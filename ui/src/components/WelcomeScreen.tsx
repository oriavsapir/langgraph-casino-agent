import { UtensilsCrossed, Bed, Gamepad2, Ticket, Sparkles, HelpCircle } from "lucide-react";
import styles from "./WelcomeScreen.module.css";

interface WelcomeScreenProps {
  onSuggestion: (text: string) => void;
}

const SUGGESTIONS = [
  { icon: UtensilsCrossed, text: "What restaurants do you have?", label: "Dining" },
  { icon: Bed, text: "Tell me about your hotel rooms", label: "Rooms" },
  { icon: Gamepad2, text: "What table games do you offer?", label: "Gaming" },
  { icon: Ticket, text: "Any upcoming shows or events?", label: "Entertainment" },
  { icon: Sparkles, text: "What spa services are available?", label: "Spa" },
  { icon: HelpCircle, text: "What are the parking options?", label: "Practical" },
];

export default function WelcomeScreen({ onSuggestion }: WelcomeScreenProps) {
  return (
    <div className={styles.welcome}>
      <div className={styles.hero}>
        <div className={styles.iconWrap}>
          <Sparkles size={32} />
        </div>
        <h2 className={styles.heading}>Welcome to Mohegan Sun</h2>
        <p className={styles.sub}>
          I'm your virtual concierge. Ask me anything about dining,
          entertainment, rooms, gaming, the spa, or planning your visit.
        </p>
      </div>

      <div className={styles.grid}>
        {SUGGESTIONS.map((s) => (
          <button
            key={s.label}
            className={styles.card}
            onClick={() => onSuggestion(s.text)}
          >
            <s.icon size={20} className={styles.cardIcon} />
            <span className={styles.cardLabel}>{s.label}</span>
            <span className={styles.cardText}>{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
