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
 * The single API wrapper for the app (systemPatterns.md): every backend call
 * goes through here, never raw fetch scattered across components.
 *
 * Identity travels in the X-User-ID header exactly as the authenticated
 * route expects; session_id rides along in the body already (the backend
 * schema ignores extra fields today, the Supabase integration will use it).
 *
 * @param {string} question
 * @param {string} userId
 * @param {string} sessionId
 * @returns {Promise<QueryResponse>}
 */
export async function queryDocuments(question, userId, sessionId) {
  const response = await fetch(QUERY_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-User-ID": userId },
    body: JSON.stringify({ question, session_id: sessionId }),
  });

  if (!response.ok) {
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
    throw new ApiError(response.status, detail);
  }

  return /** @type {QueryResponse} */ (await response.json());
}
