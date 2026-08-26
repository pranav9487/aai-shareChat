import { useState } from "react";

import { DEMO_USERS } from "../constants";

/**
 * Identity picker: one-click demo users plus a free-text override
 * (roadmap Next-v1: "select or provide their user_id and role").
 *
 * @param {{
 *   identity: { user_id: string, display_name: string, role: string } | null,
 *   onSelectDemo: (userId: string) => void,
 *   onSetCustom: (identity: { user_id: string, display_name: string, role: string }) => void,
 * }} props
 */
export function UserSelector({ identity, onSelectDemo, onSetCustom }) {
  const [draftUserId, setDraftUserId] = useState("");
  const [draftRole, setDraftRole] = useState("employee");

  const submitCustom = (event) => {
    event.preventDefault();
    const trimmedId = draftUserId.trim();
    if (!trimmedId) return;
    onSetCustom({ user_id: trimmedId, display_name: trimmedId, role: draftRole });
  };

  return (
    <section className="panel" aria-label="Identity selection">
      <h2>1 · Who are you?</h2>
      <div className="user-grid">
        {DEMO_USERS.map((user) => (
          <button
            key={user.user_id}
            type="button"
            className={identity?.user_id === user.user_id ? "user-chip selected" : "user-chip"}
            onClick={() => onSelectDemo(user.user_id)}
          >
            <strong>{user.display_name}</strong>
            <span className="role-badge">{user.role}</span>
          </button>
        ))}
      </div>

      <form className="custom-identity" onSubmit={submitCustom}>
        <input
          aria-label="Custom user ID"
          placeholder="custom user id…"
          value={draftUserId}
          onChange={(e) => setDraftUserId(e.target.value)}
        />
        <select
          aria-label="Custom role"
          value={draftRole}
          onChange={(e) => setDraftRole(e.target.value)}
        >
          {["employee", "hr", "manager", "executive"].map((role) => (
            <option key={role} value={role}>
              {role}
            </option>
          ))}
        </select>
        <button type="submit">Use this identity</button>
      </form>

      {identity ? (
        <p className="identity-status">
          Querying as <strong>{identity.display_name}</strong>{" "}
          <span className="role-badge">{identity.role}</span>
        </p>
      ) : (
        <p className="identity-status muted">Pick a test user to start asking questions.</p>
      )}
    </section>
  );
}
