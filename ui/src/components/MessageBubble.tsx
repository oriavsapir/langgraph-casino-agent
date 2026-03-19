import ReactMarkdown from "react-markdown";
import { Bot, User } from "lucide-react";
import styles from "./MessageBubble.module.css";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={`${styles.row} ${isUser ? styles.userRow : styles.botRow}`}
    >
      {!isUser && (
        <div className={styles.avatar}>
          <Bot size={18} />
        </div>
      )}

      <div
        className={`${styles.bubble} ${isUser ? styles.userBubble : styles.botBubble}`}
      >
        <div className={styles.text}>
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
        </div>
        <span className={styles.time}>
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      {isUser && (
        <div className={styles.avatarUser}>
          <User size={18} />
        </div>
      )}
    </div>
  );
}
