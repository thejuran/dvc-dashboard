import { AlertTriangleIcon } from "lucide-react";
import type { ReservationPreview } from "../types";
import { ALLOCATION_TYPE_LABELS } from "../types";

interface BookingImpactPanelProps {
  preview: ReservationPreview;
}

export default function BookingImpactPanel({ preview }: BookingImpactPanelProps) {
  return (
    <div className="space-y-4">
      {/* Before / After point balances */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">Before</p>
          <p className="text-lg font-bold">
            {preview.before.available_points} pts
          </p>
          <p className="text-xs text-muted-foreground">available</p>
          <div className="mt-1 space-y-0.5">
            {Object.entries(preview.before.balances).map(([type, points]) => (
              <p key={type} className="text-xs text-muted-foreground">
                {ALLOCATION_TYPE_LABELS[type as keyof typeof ALLOCATION_TYPE_LABELS] ?? type}:{" "}
                {points} pts
              </p>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-medium text-muted-foreground mb-1">After</p>
          <p className="text-lg font-bold">
            {preview.after.available_points} pts
          </p>
          <p className="text-xs text-muted-foreground">available</p>
          <div className="mt-1 space-y-0.5">
            {Object.entries(preview.after.balances).map(([type, points]) => (
              <p key={type} className="text-xs text-muted-foreground">
                {ALLOCATION_TYPE_LABELS[type as keyof typeof ALLOCATION_TYPE_LABELS] ?? type}:{" "}
                {points} pts
              </p>
            ))}
          </div>
        </div>
      </div>

      {/* Points delta */}
      <p className="text-sm font-semibold text-destructive">
        -{preview.points_delta} pts
      </p>

      {/* Nightly breakdown (collapsible) */}
      <details>
        <summary className="cursor-pointer text-sm text-muted-foreground hover:text-foreground transition-colors">
          {preview.num_nights} nights, {preview.total_points} pts total
        </summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-1 pr-3">Date</th>
                <th className="pb-1 pr-3">Day</th>
                <th className="pb-1 pr-3">Season</th>
                <th className="pb-1 text-right">Points</th>
              </tr>
            </thead>
            <tbody>
              {preview.nightly_breakdown.map((night) => (
                <tr
                  key={night.date}
                  className={night.is_weekend ? "bg-muted/30" : ""}
                >
                  <td className="py-0.5 pr-3">{night.date}</td>
                  <td className="py-0.5 pr-3">{night.day_of_week}</td>
                  <td className="py-0.5 pr-3">{night.season}</td>
                  <td className="py-0.5 text-right">{night.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>

      {/* Banking warning */}
      {preview.banking_warning && (
        <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700">
          <AlertTriangleIcon className="size-4 mt-0.5 shrink-0" />
          <span>{preview.banking_warning.message}</span>
        </div>
      )}
    </div>
  );
}
