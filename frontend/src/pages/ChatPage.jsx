import { useRef, useState } from "react";

import { getSession, queryDocuments } from "../api/apiClient";
import { ChatInput } from "../components/ChatInput";
import { ChatWindow } from "../components/ChatWindow";
import { SharedTranscript } from "../components/SharedTranscript";
import { ACCESS_DENIED_ANSWER, makeSessionId, nextMessageId } from "../constants";

/**
 * Chat page — messaging + shared transcript, shown after login.
 *
 * @param {{
 *   identity: { user_id: string, display_name: string, role: string },
 *   onLogout: () => void,
 * }} props
 */
export function ChatPage({ identity, onLogout }) {
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [shared, setShared] = useState([]);
  const [loadingShared, setLoadingShared] = useState(false);
  const sessionIdRef = useRef(makeSessionId());

  const sendQuestion = async (question) => {
    if (sending) return;
    setSending(true);
    setMessages((prev) => [
      ...prev,
      { id: nextMessageId(), author: "user", text: question },
    ]);
    try {
      const res = await queryDocuments(question, identity.user_id, sessionIdRef.current, identity.role);
      setMessages((prev) => [
        ...prev,
        {
          id: nextMessageId(),
          author: "assistant",
          text: res.answer,
          denied: res.answer === ACCESS_DENIED_ANSWER,
        },
      ]);
    } catch (err) {
      const detail = err instanceof Error ? err.message : "unknown error";
      setMessages((prev) => [
        ...prev,
        { id: nextMessageId(), author: "assistant", text: `Request failed: ${detail}`, error: true },
      ]);
    } finally {
      setSending(false);
    }
  };

  const refreshShared = async () => {
    setLoadingShared(true);
    try {
      const session = await getSession(sessionIdRef.current, identity.user_id);
      setShared(
        session.messages.map((m) => ({
          id: m.message_id,
          sender: m.sender_user_id,
          question: m.question,
          answer: m.answer,
          visible: m.visible,
        })),
      );
    } catch {
      setShared([]);
    } finally {
      setLoadingShared(false);
    }
  };

  return (
    <div className="chat-page">
      <header className="chat-topbar">
        <div className="chat-topbar-left">
          <h1 className="chat-brand">ShareChat</h1>
          <span className="chat-user-badge">
            {identity.display_name}
            <span className="chat-role-tag">{identity.role}</span>
          </span>
        </div>
        <button type="button" className="chat-logout" onClick={onLogout}>
          Sign out
        </button>
      </header>

      <div className="chat-body">
        <div className="chat-main">
          <ChatWindow messages={messages} />
          <ChatInput disabled={sending} onSend={(t) => void sendQuestion(t)} />
        </div>

        <aside className="chat-sidebar">
          <SharedTranscript
            messages={shared}
            onRefresh={() => void refreshShared()}
            disabled={false}
            loading={loadingShared}
          />
        </aside>
      </div>

      <footer className="chat-footer muted">
        session <code>{sessionIdRef.current}</code>
      </footer>
    </div>
  );
}
