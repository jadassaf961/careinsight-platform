import { describe, expect, it } from "vitest";
import { groupForRow } from "./board";
import type { BoardRow } from "./api";

const base: BoardRow = {
  patient_id: "p", admission_id: "a", first_name: "F", last_name: "L",
  mrn: "M", department: "Med", probability: 0.4, risk_tier: "Medium",
  plan_id: "plan", plan_status: "planning", target_discharge_date: "2026-07-02",
  open_tasks: 3, open_task_roles: ["nurse"],
};

describe("groupForRow", () => {
  it("is unplanned without a plan", () => {
    expect(groupForRow({ ...base, plan_id: null, plan_status: null }, "2026-07-02")).toBe("unplanned");
  });
  it("is blocked when target date reached and tasks open", () => {
    expect(groupForRow(base, "2026-07-02")).toBe("blocked");
    expect(groupForRow({ ...base, target_discharge_date: "2026-07-01" }, "2026-07-02")).toBe("blocked");
  });
  it("is on_track when target in future or no open tasks", () => {
    expect(groupForRow({ ...base, target_discharge_date: "2026-07-09" }, "2026-07-02")).toBe("on_track");
    expect(groupForRow({ ...base, open_tasks: 0 }, "2026-07-02")).toBe("on_track");
    expect(groupForRow({ ...base, target_discharge_date: null }, "2026-07-02")).toBe("on_track");
  });
});
