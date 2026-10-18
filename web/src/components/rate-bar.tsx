import { ci, frac, pct } from "@/lib/format";
import type { Proportion } from "@/lib/types";

export function RateBar({
  row,
  label,
}: {
  row: Proportion | null | undefined;
  label: string;
}) {
  const rate = row?.rate ?? 0;
  const has = row != null && row.n > 0 && row.rate != null;
  const low = has && row.ci_low != null ? row.ci_low * 100 : rate * 100;
  const high = has && row.ci_high != null ? row.ci_high * 100 : rate * 100;
  return (
    <div className="grid grid-cols-1 gap-1 sm:grid-cols-[9rem_1fr_auto] sm:items-center sm:gap-3">
      <div className="text-sm">{label}</div>
      <div className="relative h-7 rounded-sm bg-line/70">
        {has ? (
          <>
            <div
              className="absolute inset-y-1 left-0 rounded-sm bg-ink"
              style={{ width: `${Math.max(rate * 100, rate > 0 ? 1.5 : 0)}%` }}
            />
            <div
              className="absolute top-1/2 h-0.5 -translate-y-1/2 bg-yellow"
              style={{ left: `${low}%`, width: `${Math.max(high - low, 0.6)}%` }}
            />
          </>
        ) : null}
      </div>
      <div className="num text-sm text-muted sm:text-right">
        {has ? (
          <>
            {frac(row)} · {pct(row.rate)}
            <span className="block text-xs">{ci(row) ? `CI ${ci(row)}` : ""}</span>
          </>
        ) : (
          "pending"
        )}
      </div>
    </div>
  );
}
