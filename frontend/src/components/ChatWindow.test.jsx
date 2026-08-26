import { render, screen, within } from "@testing-library/react";

import { ACCESS_DENIED_ANSWER } from "../constants";
import { ChatWindow } from "./ChatWindow";

function message(overrides) {
  return { id: "m1", author: "assistant", text: "hello", ...overrides };
}

describe("ChatWindow", () => {
  it("shows a hint when there are no messages yet", () => {
    render(<ChatWindow messages={[]} />);
    expect(screen.getByText(/no messages yet/i)).toBeInTheDocument();
  });

  it("renders user and assistant turns", () => {
    render(
      <ChatWindow
        messages={[
          message({ id: "u1", author: "user", text: "how many days?" }),
          message({ id: "a1", text: "25 days" }),
        ]}
      />,
    );

    expect(screen.getByText("how many days?")).toBeInTheDocument();
    expect(screen.getByText("25 days")).toBeInTheDocument();
    expect(screen.queryByText(/security notice/i)).not.toBeInTheDocument();
  });

  it("labels security declines distinctly from normal answers", () => {
    render(
      <ChatWindow
        messages={[
          message({ id: "d1", text: ACCESS_DENIED_ANSWER, denied: true }),
          message({ id: "n1", text: "The answer was not found in the documents." }),
        ]}
      />,
    );

    const decline = screen.getByText(ACCESS_DENIED_ANSWER).closest("li");
    expect(decline).toHaveClass("denied");
    expect(within(decline).getByText(/security notice/i)).toBeInTheDocument();

    const normal = screen.getByText("The answer was not found in the documents.").closest("li");
    expect(normal).not.toHaveClass("denied");
    expect(within(normal).queryByText(/security notice/i)).not.toBeInTheDocument();
  });

  it("marks transport errors without calling them security declines", () => {
    render(<ChatWindow messages={[message({ id: "e1", text: "Request failed: boom", error: true })]} />);

    const failed = screen.getByText(/request failed: boom/i).closest("li");
    expect(failed).toHaveClass("error");
    expect(failed).not.toHaveClass("denied");
  });
});
