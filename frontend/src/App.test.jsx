import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "./App";
import { ApiError, queryDocuments } from "./api/apiClient";
import { ACCESS_DENIED_ANSWER } from "./constants";

vi.mock("./api/apiClient", async (importOriginal) => {
  const actual = await importOriginal();
  return { ...actual, queryDocuments: vi.fn() };
});

const mockedQuery = vi.mocked(queryDocuments);

function mockQueryResponse(answer) {
  return mockedQuery.mockResolvedValueOnce({
    answer,
    sources: [{ source: "x.md" }],
  });
}

async function selectAliceAndAsk(question) {
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: /Alice/ }));
  await userEvent.type(screen.getByLabelText("Question"), question);
  await userEvent.click(screen.getByRole("button", { name: /^Ask$/ }));
  await waitFor(() => {
    expect(mockedQuery).toHaveBeenCalled();
  });
}

describe("App integration (identity-aware chat)", () => {
  beforeEach(() => {
    mockedQuery.mockReset();
  });

  it("disables asking until an identity is chosen", () => {
    render(<App />);
    expect(screen.getByLabelText("Question")).toBeDisabled();
    expect(screen.getByRole("button", { name: /^Ask$/ })).toBeDisabled();
  });

  it("sends the question for the selected user and renders the answer", async () => {
    mockQueryResponse("Employees accrue 25 vacation days.");
    await selectAliceAndAsk("How many vacation days do we get?");

    expect(mockedQuery).toHaveBeenCalledWith(
      "How many vacation days do we get?",
      "alice",
      expect.any(String),
      "employee",
    );
    expect(await screen.findByText("Employees accrue 25 vacation days.")).toBeInTheDocument();
  });

  it("renders security declines in a distinct styled bubble", async () => {
    mockQueryResponse(ACCESS_DENIED_ANSWER);
    await selectAliceAndAsk("What is the salary band?");

    const declineBubble = (await screen.findByText(ACCESS_DENIED_ANSWER)).closest("li");
    expect(declineBubble).toHaveClass("denied");
    expect(within(declineBubble).getByText(/security notice/i)).toBeInTheDocument();
  });

  it("renders transport failures as errors, not answers", async () => {
    mockedQuery.mockRejectedValueOnce(new ApiError(502, "generation failed"));
    await selectAliceAndAsk("anything");

    expect(await screen.findByText(/request failed: generation failed/i)).toBeInTheDocument();
  });
});
