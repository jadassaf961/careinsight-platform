import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, TransitionTask } from "@/lib/api";
import { Card } from "@/components/core/Card";
import { SectionLabel } from "@/components/core/SectionLabel";

export function MyTasksWidget() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["my-tasks"],
    queryFn: () => api.get<TransitionTask[]>("/transitions/tasks/mine"),
  });
  const complete = useMutation({
    mutationFn: (taskId: string) => api.patch(`/transitions/tasks/${taskId}`, { status: "done" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });

  return (
    <Card>
      <SectionLabel>My Open Transition Tasks</SectionLabel>
      {isLoading && <p className="text-sm text-ink/40">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-ink/50">Nothing pending for your role.</p>
      )}
      <div className="space-y-1">
        {data?.slice(0, 8).map((t) => (
          <label key={t.id} className="flex items-start gap-2.5 p-1.5 rounded hover:bg-tint cursor-pointer">
            <input
              type="checkbox"
              className="mt-0.5 accent-ink"
              checked={false}
              onChange={() => complete.mutate(t.id)}
            />
            <span className="text-sm text-ink/80">{t.title}</span>
          </label>
        ))}
        {(data?.length ?? 0) > 8 && (
          <p className="text-xs text-ink/40 mt-1">+{data!.length - 8} more on the board</p>
        )}
      </div>
    </Card>
  );
}
