import { useState } from "react";

import { DEMO_USERS } from "../constants";

/**
 * Full-screen login page — pick a demo identity or enter a custom one.
 *
 * @param {{ onLogin: (identity: { user_id: string, display_name: string, role: string }) => void }} props
 */
export function LoginPage({ onLogin }) {
  const [selected, setSelected] = useState(null);
  const [customId, setCustomId] = useState("");
  const [customRole, setCustomRole] = useState("employee");

  const handleDemoSelect = (user) => {
    setSelected(user);
    setCustomId("");
  };

  const handleContinue = () => {
    if (selected) {
      onLogin({ ...selected });
    }
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    const id = customId.trim();
    if (!id) return;
    onLogin({ user_id: id, display_name: id, role: customRole });
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">ShareChat</h1>
        <p className="login-subtitle">Secure employee RAG</p>

        <div className="login-section">
          <span className="login-label">Pick a user</span>
          <div className="login-user-grid">
            {DEMO_USERS.map((user) => (
              <button
                key={user.user_id}
                type="button"
                className={
                  selected?.user_id === user.user_id
                    ? "login-chip login-chip--active"
                    : "login-chip"
                }
                onClick={() => handleDemoSelect(user)}
              >
                <span className="login-chip-name">{user.display_name}</span>
                <span className="login-chip-role">{user.role}</span>
              </button>
            ))}
          </div>

          {selected && (
            <button
              type="button"
              className="login-continue"
              onClick={handleContinue}
            >
              Continue as {selected.display_name} →
            </button>
          )}
        </div>

        <div className="login-divider">
          <span>or</span>
        </div>

        <form className="login-custom" onSubmit={handleCustomSubmit}>
          <input
            className="login-input"
            placeholder="user id"
            value={customId}
            onChange={(e) => setCustomId(e.target.value)}
            aria-label="Custom user ID"
          />
          <select
            className="login-select"
            value={customRole}
            onChange={(e) => setCustomRole(e.target.value)}
            aria-label="Role"
          >
            {["employee", "hr", "manager", "executive"].map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
          <button
            type="submit"
            className="login-continue"
            disabled={!customId.trim()}
          >
            Enter →
          </button>
        </form>
      </div>
    </div>
  );
}
