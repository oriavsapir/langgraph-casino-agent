import { useState, useRef, useEffect, useCallback } from "react";
import Header from "./components/Header";
import MessageBubble, { type Message } from "./components/MessageBubble";
import TypingIndicator from "./components/TypingIndicator";
import InputBar from "./components/InputBar";
import WelcomeScreen from "./components/WelcomeScreen";
import { sendMessage } from "./api";
import styles from "./App.module.css";

const PROPERTY_NAME = "Mohegan Sun";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setError(null);

    try {
      const res = await sendMessage(text, sessionId);
      if (!sessionId) setSessionId(res.session_id);

      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.reply,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Something went wrong";
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setSessionId(undefined);
    setError(null);
  };

  return (
    <div className={styles.layout}>
      <Header propertyName={PROPERTY_NAME} onReset={handleReset} />

      <div className={styles.messages} ref={scrollRef}>
        {messages.length === 0 && !loading ? (
          <WelcomeScreen onSuggestion={handleSend} />
        ) : (
          <div className={styles.messageList}>
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {loading && <TypingIndicator />}
            {error && (
              <div className={styles.error}>
                <p>{error}</p>
              </div>
            )}
          </div>
        )}
      </div>

      <InputBar onSend={handleSend} disabled={loading} />
    </div>
  );
}
