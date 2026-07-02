import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, TransitionTask } from "@/lib/api";
import { Card } from "@/components/core/Card";

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
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
        My Open Transition Tasks
      </div>
      {isLoading && <p className="text-sm text-slate-400">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-slate-500">Nothing pending for your role. 🎉</p>
      )}
      <div className="space-y-1">
        {data?.slice(0, 8).map((t) => (
          <label key={t.id} className="flex items-start gap-2.5 p-1.5 rounded hover:bg-slate-50 cursor-pointer">
            <input
              type="checkbox"
              className="mt-0.5 accent-brand-600"
              checked={false}
              onChange={() => complete.mutate(t.id)}
            />
            <span className="text-sm text-slate-700">{t.title}</span>
          </label>
        ))}
        {(data?.length ?? 0) > 8 && (
          <p className="text-xs text-slate-400 mt-1">+{data!.length - 8} more on the board</p>
        )}
      </div>
    </Card>
  );
}
