/**
 * Scrollback for the conversation. Security declines and transport errors get
 * their own visual treatment so they can never be mistaken for answers.
 *
 * @param {{ messages: Array<{ id: string, author: "user"|"assistant", text: string, denied?: boolean, error?: boolean }> }} props
 */
export function ChatWindow({ messages }) {
  return (
    <section className="panel chat-window" aria-label="Conversation">

      {messages.length === 0 ? (
        <p className="muted empty-hint">
          No messages yet. Try something inside your tier — e.g. “How many vacation days do we
          get?” as Priya (hr), then the same question as Alice (employee).
        </p>
      ) : (
        <ul className="message-list">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
        </ul>
      )}
    </section>
  );
}

/** @param {{ message: { id: string, author: string, text: string, denied?: boolean, error?: boolean } }} props */
function MessageBubble({ message }) {
  if (message.author === "user") {
    return <li className="message user-message">{message.text}</li>;
  }
  if (message.denied) {
    return (
      <li className="message assistant-message denied">
        <strong className="notice-label">Security notice</strong>
        {message.text}
      </li>
    );
  }
  return (
    <li className={message.error ? "message assistant-message error" : "message assistant-message"}>
      {message.text}
    </li>
  );
}
