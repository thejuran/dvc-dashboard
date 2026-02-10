import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { parseRoomKey, formatDateRange } from "../lib/utils";
import { useResorts } from "../hooks/useContracts";
import type { Reservation } from "../types";

interface UpcomingReservationsProps {
  reservations: Reservation[] | undefined;
}

export default function UpcomingReservations({
  reservations,
}: UpcomingReservationsProps) {
  const { data: resorts } = useResorts();
  const displayed = reservations?.slice(0, 5) ?? [];
  const hasMore = (reservations?.length ?? 0) > 5;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upcoming Reservations</CardTitle>
      </CardHeader>
      <CardContent>
        {displayed.length === 0 ? (
          <p className="text-muted-foreground">No upcoming reservations</p>
        ) : (
          <div className="space-y-3">
            {displayed.map((r) => {
              const resort = resorts?.find((res) => res.slug === r.resort);
              const resortName = resort?.short_name || r.resort;
              const { roomType, view } = parseRoomKey(r.room_key);
              const dateRange = formatDateRange(r.check_in, r.check_out);

              return (
                <div
                  key={r.id}
                  className="flex items-center justify-between text-sm border-b last:border-b-0 pb-2 last:pb-0"
                >
                  <div>
                    <p className="font-medium">{resortName}</p>
                    <p className="text-muted-foreground text-xs">
                      {roomType}
                      {view && ` - ${view}`} | {dateRange}
                    </p>
                  </div>
                  <span className="font-semibold tabular-nums">
                    {r.points_cost} pts
                  </span>
                </div>
              );
            })}
            {hasMore && (
              <a
                href="/reservations"
                className="text-sm text-primary hover:underline"
              >
                View all reservations
              </a>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
