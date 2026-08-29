import { useState } from "react";

import { ChatPage } from "./pages/ChatPage";
import { LoginPage } from "./pages/LoginPage";

export function App() {
  const [identity, setIdentity] = useState(null);

  if (!identity) {
    return <LoginPage onLogin={setIdentity} />;
  }

  return (
    <ChatPage
      identity={identity}
      onLogout={() => setIdentity(null)}
    />
  );
}
