import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AvailabilityContractResult } from "../types";

interface AvailabilityCardProps {
  data: AvailabilityContractResult;
}

const ALLOC_LABELS: Record<string, string> = {
  current: "Current",
  banked: "Banked",
  borrowed: "Borrowed",
  holding: "Holding",
};

export default function AvailabilityCard({ data }: AvailabilityCardProps) {
  const uyStart = new Date(data.use_year_start + "T12:00:00").toLocaleDateString(
    "en-US",
    { month: "short", year: "numeric" }
  );
  const uyEnd = new Date(data.use_year_end + "T12:00:00").toLocaleDateString(
    "en-US",
    { month: "short", year: "numeric" }
  );

  const bankingDate = new Date(
    data.banking_deadline + "T12:00:00"
  ).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const expirationDate = new Date(
    data.use_year_end + "T12:00:00"
  ).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const bankingUrgent =
    !data.banking_deadline_passed && data.days_until_banking_deadline <= 30;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <CardTitle className="text-base">{data.contract_name}</CardTitle>
            <p className="text-sm text-muted-foreground mt-0.5">
              {data.use_year} Use Year ({uyStart} - {uyEnd})
            </p>
          </div>
          <Badge
            variant="secondary"
            className={
              data.use_year_status === "active"
                ? "bg-green-100 text-green-700 border-green-200"
                : data.use_year_status === "upcoming"
                ? "bg-blue-100 text-blue-700 border-blue-200"
                : "bg-gray-100 text-gray-500 border-gray-200"
            }
          >
            {data.use_year_status}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Balance breakdown */}
        <div className="space-y-1">
          {Object.entries(data.balances).map(([type, points]) => (
            <div key={type} className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                {ALLOC_LABELS[type] || type}
              </span>
              <span className="tabular-nums">{points} pts</span>
            </div>
          ))}
          <div className="flex justify-between text-sm font-medium border-t pt-1">
            <span>Total</span>
            <span className="tabular-nums">{data.total_points} pts</span>
          </div>
        </div>

        {/* Committed */}
        {data.committed_points > 0 && (
          <div className="flex justify-between text-sm text-amber-600">
            <span>
              Committed ({data.committed_reservation_count} reservation
              {data.committed_reservation_count !== 1 ? "s" : ""})
            </span>
            <span className="tabular-nums">-{data.committed_points} pts</span>
          </div>
        )}

        {/* Available */}
        <div className="flex justify-between items-center pt-1 border-t">
          <span className="font-semibold">Available</span>
          <span className="text-xl font-bold text-green-600 tabular-nums">
            {data.available_points} pts
          </span>
        </div>

        {/* Banking deadline */}
        <div className="space-y-1 pt-2 border-t text-xs">
          <div
            className={
              data.banking_deadline_passed
                ? "text-red-600"
                : bankingUrgent
                ? "text-amber-600"
                : "text-muted-foreground"
            }
          >
            {data.banking_deadline_passed
              ? `Banking deadline passed (${Math.abs(data.days_until_banking_deadline)} days ago)`
              : `Banking deadline: ${bankingDate} (in ${data.days_until_banking_deadline} days)`}
          </div>
          <div className="text-muted-foreground">
            Points expire: {expirationDate} (in {data.days_until_expiration}{" "}
            days)
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
