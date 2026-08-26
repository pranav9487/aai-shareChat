import { ApiError, queryDocuments } from "./apiClient";

const QUERY_RESPONSE = { answer: "25 days", sources: [{ source: "hr.md" }] };

function stubFetch(payload, ok = true, status = 200) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: status === 200 ? "OK" : "Rejected",
    json: async () => payload,
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("queryDocuments", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("posts to /api/query with the X-User-ID header and session body", async () => {
    const fetchMock = stubFetch(QUERY_RESPONSE);

    const result = await queryDocuments("vacation days?", "priya", "sess-123");

    expect(result).toEqual(QUERY_RESPONSE);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/query");
    expect(init.method).toBe("POST");
    expect(init.headers["X-User-ID"]).toBe("priya");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(init.body)).toEqual({
      question: "vacation days?",
      session_id: "sess-123",
    });
  });

  it("surfaces the backend detail string on non-2xx responses", async () => {
    stubFetch({ detail: "Access denied: unknown user." }, false, 403);

    await expect(queryDocuments("q", "mallory", "s")).rejects.toThrow(ApiError);
    await expect(queryDocuments("q", "mallory", "s")).rejects.toMatchObject({
      status: 403,
      message: "Access denied: unknown user.",
    });
  });

  it("falls back to status text when the error body is not JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      json: async () => {
        throw new Error("not json");
      },
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(queryDocuments("q", "alice", "s")).rejects.toMatchObject({
      status: 500,
      message: "Internal Server Error",
    });
  });
});
