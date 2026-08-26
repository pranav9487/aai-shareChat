import { useState } from "react";

/**
 * Free-text question box; Enter or the button dispatches to the pipeline.
 *
 * @param {{ disabled: boolean, onSend: (question: string) => void }} props
 */
export function ChatInput({ disabled, onSend }) {
  const [draft, setDraft] = useState("");

  const submit = (event) => {
    event.preventDefault();
    const trimmed = draft.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setDraft("");
  };

  return (
    <form className="chat-input panel" onSubmit={submit} aria-label="Ask a question">
      <input
        placeholder="Ask about the internal documents…"
        value={draft}
        disabled={disabled}
        onChange={(e) => setDraft(e.target.value)}
        aria-label="Question"
      />
      <button type="submit" disabled={disabled || draft.trim().length === 0}>
        Ask
      </button>
    </form>
  );
}
