import { ApiError, getSession, queryDocuments } from "./apiClient";

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

describe("getSession", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("gets a shared session transcript with the viewer identity header", async () => {
    const transcript = {
      session_id: "sess-1",
      messages: [
        {
          message_id: "m1",
          sender_user_id: "priya",
          sender_role: "hr",
          question: "vacation days?",
          answer: "25 days",
          sources: [],
          visible: true,
        },
      ],
    };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => transcript,
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getSession("sess-1", "alice");

    expect(result).toEqual(transcript);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/sessions/sess-1");
    expect(init.method).toBe("GET");
    expect(init.headers["X-User-ID"]).toBe("alice");
  });

  it("encodes the session id in the path", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      statusText: "OK",
      json: async () => ({ session_id: "a/b", messages: [] }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await getSession("a/b", "alice");

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/sessions/a%2Fb",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("surfaces the backend detail on a missing session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
        json: async () => ({ detail: "Session not found." }),
      }),
    );

    await expect(getSession("nope", "alice")).rejects.toMatchObject({
      status: 404,
      message: "Session not found.",
    });
  });
});
