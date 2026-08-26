/**
 * Mirror of the backend's v1 seed registry
 * (backend/app/services/access_control/directory.py).
 * Drift risk until a users-list endpoint or Supabase exists — see ADR-0005.
 *
 * @typedef {{ user_id: string, display_name: string, role: string }} DemoUser
 * @type {DemoUser[]}
 */
export const DEMO_USERS = [
  { user_id: "alice", display_name: "Alice", role: "employee" },
  { user_id: "priya", display_name: "Priya", role: "hr" },
  { user_id: "carlos", display_name: "Carlos", role: "manager" },
  { user_id: "dana", display_name: "Dana", role: "executive" },
  { user_id: "guest", display_name: "Guest", role: "employee" },
];

/**
 * Canonical security-decline sentence — keep in sync with
 * ACCESS_DENIED_ANSWER in backend/app/services/rag/pipeline.py.
 * @type {string}
 */
export const ACCESS_DENIED_ANSWER =
  "Access denied: you do not have permission to view this information.";

/** One session id per page visit; Supabase (roadmap Next-v2) will give it
 * real persistence semantics.
 * @returns {string} */
export function makeSessionId() {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `sess-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

let messageCounter = 0;

/** @returns {string} unique id for a chat message bubble */
export function nextMessageId() {
  messageCounter += 1;
  return `msg-${messageCounter}`;
}
