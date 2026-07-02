import type { BoardRow } from "./api";

export type BoardGroup = "blocked" | "on_track" | "unplanned";

/** `today` is an ISO date string (YYYY-MM-DD) so string comparison works. */
export function groupForRow(row: BoardRow, today: string): BoardGroup {
  if (!row.plan_id) return "unplanned";
  if (
    row.open_tasks > 0 &&
    row.target_discharge_date !== null &&
    row.target_discharge_date <= today
  ) {
    return "blocked";
  }
  return "on_track";
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
