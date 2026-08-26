import { useRef, useState } from "react";

import { queryDocuments } from "./api/apiClient";
import { ChatInput } from "./components/ChatInput";
import { ChatWindow } from "./components/ChatWindow";
import { UserSelector } from "./components/UserSelector";
import { ACCESS_DENIED_ANSWER, DEMO_USERS, makeSessionId, nextMessageId } from "./constants";

export function App() {
  const [identity, setIdentity] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  // One session id per page visit; consumed by Supabase integration later.
  const sessionIdRef = useRef(makeSessionId());

  const selectDemoUser = (userId) => {
    const demoUser = DEMO_USERS.find((user) => user.user_id === userId);
    if (demoUser) {
      setIdentity({ ...demoUser });
    }
  };

  const sendQuestion = async (question) => {
    if (!identity || sending) return;
    setSending(true);
    setMessages((previous) => [
      ...previous,
      { id: nextMessageId(), author: "user", text: question },
    ]);
    try {
      const response = await queryDocuments(question, identity.user_id, sessionIdRef.current);
      setMessages((previous) => [
        ...previous,
        {
          id: nextMessageId(),
          author: "assistant",
          text: response.answer,
          denied: response.answer === ACCESS_DENIED_ANSWER,
        },
      ]);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "unknown error";
      setMessages((previous) => [
        ...previous,
        {
          id: nextMessageId(),
          author: "assistant",
          text: `Request failed: ${detail}`,
          error: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <main className="app">
      <header className="app-header">
        <h1>aai-share-chat</h1>
        <p className="tagline">Secure employee RAG — answers stay inside your access tier.</p>
      </header>

      <UserSelector identity={identity} onSelectDemo={selectDemoUser} onSetCustom={setIdentity} />

      <ChatWindow messages={messages} />

      <ChatInput disabled={!identity || sending} onSend={(text) => void sendQuestion(text)} />

      <footer className="app-footer muted">
        session <code>{sessionIdRef.current}</code>
      </footer>
    </main>
  );
}
