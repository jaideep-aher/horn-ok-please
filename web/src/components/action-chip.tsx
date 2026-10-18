import { cn } from "@/lib/utils";

const TONE: Record<string, string> = {
  BRAKE: "bg-signal text-white",
  SLOW: "bg-yellow text-ink",
  CONTINUE: "bg-enamel text-white",
  CHANGE_LANE: "bg-ink text-yellow",
  UNPARSEABLE: "border border-dashed border-ink/30 bg-transparent text-muted",
  PENDING: "bg-line text-muted",
};

export function actionName(action: string | undefined): string {
  if (!action) return "pending";
  if (action === "CHANGE_LANE") return "CHANGE LANE";
  if (action === "UNPARSEABLE") return "unparsed";
  return action;
}

export function ActionChip({
  action,
  className,
}: {
  action: string | undefined;
  className?: string;
}) {
  const key = action && TONE[action] ? action : action ? "PENDING" : "PENDING";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded px-2 py-0.5 font-stencil text-sm tracking-wide",
        TONE[action && TONE[action] ? action : key],
        className,
      )}
    >
      {actionName(action)}
    </span>
  );
}
