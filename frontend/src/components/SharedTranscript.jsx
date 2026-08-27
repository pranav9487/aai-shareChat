/**
 * Shared-session transcript (roadmap §3), rendered exactly as the backend
 * filtered it for the current viewer. Messages the viewer may not read are
 * already a non-leaky placeholder; they are styled as security notices so a
 * "hidden" message is distinguishable from a normal answer.
 *
 * @param {{
 *   messages: Array<{ id: string, sender: string, question: string, answer: string, visible: boolean }>,
 *   onRefresh: () => void,
 *   disabled?: boolean,
 *   loading?: boolean,
 * }} props
 */
export function SharedTranscript({ messages, onRefresh, disabled, loading }) {
  return (
    <section className="panel shared-transcript" aria-label="Shared session transcript">
      <div className="section-heading">
        <h2>3 · Shared session transcript</h2>
        <button type="button" onClick={onRefresh} disabled={disabled || loading}>
          {loading ? "Loading…" : "Refresh"}
        </button>
      </div>
      {messages.length === 0 ? (
        <p className="muted empty-hint">
          No shared messages yet. Ask as one user, then switch users and hit Refresh to see
          what that user may read.
        </p>
      ) : (
        <ul className="transcript-list">
          {messages.map((message) => (
            <li key={message.id}>
              <span className="transcript-sender muted">{message.sender}</span>
              <p className="transcript-question">{message.question}</p>
              {message.visible ? (
                <p className="transcript-answer">{message.answer}</p>
              ) : (
                <p className="transcript-answer denied">
                  <strong className="notice-label">Security notice</strong>
                  {message.answer}
                </p>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}