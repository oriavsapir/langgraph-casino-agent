"""Individual graph nodes — each is a pure function (state in → partial state out)."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage

from app.agent.state import AgentState, Intent
from app.knowledge.store import PropertyKnowledgeStore

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """\
You are an intent classifier for a casino resort concierge chatbot.
Classify the user's LATEST message into exactly one of the following intents:

- "property_question": the user is asking about the property, its amenities, \
restaurants, entertainment, rooms, gaming, promotions, practical info, or \
anything related to visiting the resort.
- "action_request": the user wants to perform an action such as making a \
reservation, booking a room, placing a bet, modifying an account, or any \
transactional operation.
- "off_topic": the question is unrelated to the property (e.g. politics, \
general knowledge, math, other businesses, other casinos).
- "greeting": the user is saying hello, introducing themselves, or starting \
a conversation.
- "farewell": the user is saying goodbye or ending the conversation.

Consider the FULL conversation history for context, but classify based on the \
LATEST user message.

Respond with a JSON object: {{"intent": "<intent>"}}
"""

RESPONSE_SYSTEM_PROMPT = """\
You are a warm, knowledgeable, and professional concierge for {property_name}. \
Your goal is to help guests with questions about the property so they can plan \
and enjoy their visit.

Guidelines:
- Answer ONLY based on the provided context documents. Never invent information.
- If the context does not contain the answer, say so honestly and suggest the \
guest contact the resort directly for the most up-to-date details.
- Be conversational and welcoming, but concise. Avoid walls of text.
- Use bullet points or short paragraphs for readability when listing options.
- When mentioning prices, hours, or dates, note they may be subject to change.
- Do NOT take any actions — you are informational only.
- Do NOT discuss other casino properties.

Context documents:
{context}
"""

DECLINE_ACTION_MESSAGE = (
    "I appreciate you reaching out! Unfortunately, I'm only able to provide "
    "information about {property_name} — I'm not able to make reservations, "
    "bookings, or perform any account operations. "
    "For those services, please contact the resort directly at the number on "
    "our website or use the resort's mobile app. "
    "Is there anything else about the property I can help you learn about?"
)

DECLINE_OFF_TOPIC_MESSAGE = (
    "Great question, but I'm specifically here to help with information about "
    "{property_name} — things like dining, entertainment, hotel accommodations, "
    "gaming, promotions, and practical visitor info. "
    "Feel free to ask me anything about the resort!"
)

GREETING_MESSAGE = (
    "Welcome to {property_name}! 🎰 I'm your virtual concierge and I'm here "
    "to help you with anything you'd like to know about the resort — from "
    "dining and entertainment to hotel rooms, gaming, spa services, and more. "
    "What can I help you with today?"
)

FAREWELL_MESSAGE = (
    "Thank you for chatting with me! I hope the information was helpful. "
    "If you have more questions before or during your visit to {property_name}, "
    "don't hesitate to come back. Enjoy your experience! 🎲"
)


def build_classify_node(llm: BaseChatModel):
    """Return a node function that classifies user intent via the LLM."""

    async def classify_intent(state: AgentState) -> dict[str, Any]:
        response = await llm.ainvoke(
            [SystemMessage(content=INTENT_SYSTEM_PROMPT)] + state["messages"]
        )
        try:
            parsed = json.loads(response.content)
            intent: Intent = parsed.get("intent", "property_question")
        except (json.JSONDecodeError, AttributeError):
            intent = "property_question"

        logger.info("Classified intent: %s", intent)
        return {"intent": intent}

    return classify_intent


def build_retrieve_node(store: PropertyKnowledgeStore, k: int = 6):
    """Return a node function that retrieves relevant documents."""

    async def retrieve_context(state: AgentState) -> dict[str, Any]:
        last_message = state["messages"][-1].content
        docs = store.search(str(last_message), k=k)
        logger.info("Retrieved %d documents", len(docs))
        return {"retrieved_docs": docs}

    return retrieve_context


def build_generate_node(llm: BaseChatModel):
    """Return a node function that generates an answer grounded in the
    retrieved context."""

    async def generate_response(state: AgentState) -> dict[str, Any]:
        docs = state.get("retrieved_docs", [])
        context_text = "\n\n---\n\n".join(doc.page_content for doc in docs)

        system = RESPONSE_SYSTEM_PROMPT.format(
            property_name=state["property_name"],
            context=context_text,
        )

        response = await llm.ainvoke(
            [SystemMessage(content=system)] + state["messages"]
        )
        return {"messages": [response]}

    return generate_response


def build_simple_response_node(template: str):
    """Return a node that emits a static (template-formatted) AI message."""

    async def respond(state: AgentState) -> dict[str, Any]:
        text = template.format(property_name=state["property_name"])
        return {"messages": [AIMessage(content=text)]}

    return respond


def route_by_intent(state: AgentState) -> str:
    """Conditional edge: pick the next node based on classified intent."""
    intent = state.get("intent", "property_question")
    routing: dict[str, str] = {
        "property_question": "retrieve",
        "action_request": "decline_action",
        "off_topic": "decline_off_topic",
        "greeting": "greet",
        "farewell": "farewell",
    }
    return routing.get(intent, "retrieve")
