/**
 * @typedef {{ answer: string, sources: Array<Record<string, unknown>> }} QueryResponse
 */

const QUERY_ENDPOINT = "/api/query";

/** Non-2xx response from the query API (backend detail preserved). */
export class ApiError extends Error {
  /**
   * @param {number} status
   * @param {string} message
   */
  constructor(status, message) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Pull the backend's `detail` from a (possibly non-JSON) error response.
 * @param {Response} response
 * @returns {Promise<string>}
 */
async function errorDetail(response) {
  let detail = response.statusText || "request failed";
  try {
    const body = await response.json();
    const maybeDetail = /** @type {{ detail?: unknown }} */ (body)?.detail;
    if (typeof maybeDetail === "string" && maybeDetail.length > 0) {
      detail = maybeDetail;
    }
  } catch {
    // Non-JSON error body — fall back to statusText.
  }
  return detail;
}

/**
 * The single API wrapper for the app (systemPatterns.md): every backend call
 * goes through here, never raw fetch scattered across components.
 *
 * Identity travels in the X-User-ID header exactly as the authenticated
 * route expects; session_id is required in the body and ties this exchange
 * to a (possibly shared) conversation (roadmap §3).
 *
 * @param {string} question
 * @param {string} userId
 * @param {string} sessionId
 * @param {string} [role]
 * @returns {Promise<QueryResponse>}
 */
export async function queryDocuments(question, userId, sessionId, role) {
  const headers = { "Content-Type": "application/json", "X-User-ID": userId };
  if (role) {
    headers["X-User-Role"] = role;
  }

  const response = await fetch(QUERY_ENDPOINT, {
    method: "POST",
    headers,
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response));
  }

  return /** @type {QueryResponse} */ (await response.json());
}

/**
 * @typedef {{ message_id: string, sender_user_id: string, sender_role: string,
 *   question: string, answer: string, sources: Array<Record<string, unknown>>,
 *   visible: boolean }} SessionMessageView
 * @typedef {{ session_id: string, messages: SessionMessageView[] }} SessionView
 */

/**
 * Fetch a shared session's transcript, filtered server-side to *userId*'s
 * permissions (roadmap §3). Messages the viewer may not read come back with a
 * non-leaky placeholder in `answer` and an empty `sources` list; the question
 * (the viewer's own prompt) is preserved.
 *
 * @param {string} sessionId
 * @param {string} userId
 * @returns {Promise<SessionView>}
 */
export async function getSession(sessionId, userId) {
  const response = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}`, {
    method: "GET",
    headers: { "X-User-ID": userId },
  });

  if (!response.ok) {
    throw new ApiError(response.status, await errorDetail(response));
  }

  return /** @type {SessionView} */ (await response.json());
}
