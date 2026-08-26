import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { DEMO_USERS } from "../constants";
import { UserSelector } from "./UserSelector";

describe("UserSelector", () => {
  it("renders every demo user with their role", () => {
    render(<UserSelector identity={null} onSelectDemo={() => {}} onSetCustom={() => {}} />);

    for (const user of DEMO_USERS) {
      expect(screen.getByRole("button", { name: new RegExp(user.display_name) })).toHaveTextContent(
        user.role,
      );
    }
  });

  it("marks the selected demo user", () => {
    render(
      <UserSelector
        identity={{ user_id: "priya", display_name: "Priya", role: "hr" }}
        onSelectDemo={() => {}}
        onSetCustom={() => {}}
      />,
    );

    expect(screen.getByRole("button", { name: /Priya/ })).toHaveClass("selected");
    expect(screen.getByRole("button", { name: /Alice/ })).not.toHaveClass("selected");
  });

  it("reports the clicked demo user", async () => {
    const onSelectDemo = vi.fn();
    render(<UserSelector identity={null} onSelectDemo={onSelectDemo} onSetCustom={() => {}} />);

    await userEvent.click(screen.getByRole("button", { name: /Carlos/ }));

    expect(onSelectDemo).toHaveBeenCalledWith("carlos");
  });

  it("accepts a custom id and role via the override form", async () => {
    const onSetCustom = vi.fn();
    render(<UserSelector identity={null} onSelectDemo={() => {}} onSetCustom={onSetCustom} />);

    await userEvent.type(screen.getByLabelText("Custom user ID"), "mallory");
    await userEvent.selectOptions(screen.getByLabelText("Custom role"), "manager");
    await userEvent.click(screen.getByRole("button", { name: /Use this identity/i }));

    expect(onSetCustom).toHaveBeenCalledWith({
      user_id: "mallory",
      display_name: "mallory",
      role: "manager",
    });
  });

  it("ignores a blank custom id", async () => {
    const onSetCustom = vi.fn();
    render(<UserSelector identity={null} onSelectDemo={() => {}} onSetCustom={onSetCustom} />);

    await userEvent.click(screen.getByRole("button", { name: /Use this identity/i }));

    expect(onSetCustom).not.toHaveBeenCalled();
  });
});
