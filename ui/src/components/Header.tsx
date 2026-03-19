import { Sparkles, RotateCcw } from "lucide-react";
import styles from "./Header.module.css";

interface HeaderProps {
  propertyName: string;
  onReset: () => void;
}

export default function Header({ propertyName, onReset }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <div className={styles.logoWrap}>
          <Sparkles size={22} />
        </div>
        <div>
          <h1 className={styles.title}>{propertyName}</h1>
          <p className={styles.subtitle}>Virtual Concierge</p>
        </div>
      </div>
      <button
        className={styles.resetBtn}
        onClick={onReset}
        title="New conversation"
        aria-label="Start new conversation"
      >
        <RotateCcw size={18} />
      </button>
    </header>
  );
}
