import { useRef, useState } from "react";

import { getSession, queryDocuments } from "./api/apiClient";
import { ChatInput } from "./components/ChatInput";
import { ChatWindow } from "./components/ChatWindow";
import { SharedTranscript } from "./components/SharedTranscript";
import { UserSelector } from "./components/UserSelector";
import { ACCESS_DENIED_ANSWER, DEMO_USERS, makeSessionId, nextMessageId } from "./constants";

export function App() {
  const [identity, setIdentity] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [shared, setShared] = useState([]);
  const [loadingShared, setLoadingShared] = useState(false);
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
      const response = await queryDocuments(question, identity.user_id, sessionIdRef.current, identity.role);
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

  const refreshShared = async () => {
    if (!identity) return;
    setLoadingShared(true);
    try {
      const session = await getSession(sessionIdRef.current, identity.user_id);
      setShared(
        session.messages.map((message) => ({
          id: message.message_id,
          sender: message.sender_user_id,
          question: message.question,
          answer: message.answer,
          visible: message.visible,
        })),
      );
    } catch {
      setShared([]);
    } finally {
      setLoadingShared(false);
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

      <SharedTranscript
        messages={shared}
        onRefresh={() => void refreshShared()}
        disabled={!identity}
        loading={loadingShared}
      />

      <ChatInput disabled={!identity || sending} onSend={(text) => void sendQuestion(text)} />

      <footer className="app-footer muted">
        session <code>{sessionIdRef.current}</code>
      </footer>
    </main>
  );
}
