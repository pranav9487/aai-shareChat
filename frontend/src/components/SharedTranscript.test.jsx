import { render, screen, within } from "@testing-library/react";

import { SharedTranscript } from "./SharedTranscript";

describe("SharedTranscript", () => {
  it("shows a hint when there are no messages yet", () => {
    render(<SharedTranscript messages={[]} onRefresh={() => {}} disabled={false} />);
    expect(screen.getByText(/no shared messages yet/i)).toBeInTheDocument();
  });

  it("renders visible messages with their question and answer", () => {
    render(
      <SharedTranscript
        messages={[
          {
            id: "m1",
            sender: "priya",
            question: "vacation days?",
            answer: "25 days",
            visible: true,
          },
        ]}
        onRefresh={() => {}}
        disabled={false}
      />,
    );

    expect(screen.getByText("priya")).toBeInTheDocument();
    expect(screen.getByText("vacation days?")).toBeInTheDocument();
    expect(screen.getByText("25 days")).toBeInTheDocument();
    expect(screen.queryByText(/security notice/i)).not.toBeInTheDocument();
  });

  it("styles hidden messages as security notices and keeps the question", () => {
    render(
      <SharedTranscript
        messages={[
          {
            id: "m1",
            sender: "dana",
            question: "bonus?",
            answer: "This message is not visible under your access permissions.",
            visible: false,
          },
        ]}
        onRefresh={() => {}}
        disabled={false}
      />,
    );

    const hidden = screen.getByText(/not visible under your access permissions/i);
    expect(hidden).toHaveClass("denied");
    expect(within(hidden).getByText(/security notice/i)).toBeInTheDocument();
    expect(screen.getByText("bonus?")).toBeInTheDocument();
  });

  it("disables refresh while disabled or loading", () => {
    const refresh = vi.fn();
    const { rerender } = render(
      <SharedTranscript messages={[]} onRefresh={refresh} disabled loading />,
    );
    expect(screen.getByRole("button", { name: /^Loading/i })).toBeDisabled();
    rerender(<SharedTranscript messages={[]} onRefresh={refresh} disabled={false} loading={false} />);
    expect(screen.getByRole("button", { name: /^Refresh$/ })).toBeEnabled();
  });
});