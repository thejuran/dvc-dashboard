import { format, parseISO, differenceInDays } from "date-fns";
import { Trash2, Loader2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useScenarioStore } from "@/store/useScenarioStore";
import type { HypotheticalBooking, ResolvedBooking } from "@/types";

interface ScenarioBookingListProps {
  bookings: HypotheticalBooking[];
  resolvedBookings: ResolvedBooking[];
  isEvaluating: boolean;
}

function findResolvedCost(
  booking: HypotheticalBooking,
  resolvedBookings: ResolvedBooking[]
): number | null {
  const match = resolvedBookings.find(
    (rb) =>
      rb.contract_id === booking.contract_id &&
      rb.resort === booking.resort &&
      rb.room_key === booking.room_key &&
      rb.check_in === booking.check_in
  );
  return match ? match.points_cost : null;
}

export default function ScenarioBookingList({
  bookings,
  resolvedBookings,
  isEvaluating,
}: ScenarioBookingListProps) {
  const removeBooking = useScenarioStore((s) => s.removeBooking);

  if (bookings.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-muted-foreground">
          {bookings.length} of 10 bookings
        </h3>
        {bookings.length >= 8 && (
          <span className="text-xs text-amber-600">
            {10 - bookings.length === 0
              ? "At capacity"
              : `${10 - bookings.length} remaining`}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {bookings.map((booking) => {
          const nights = differenceInDays(
            parseISO(booking.check_out),
            parseISO(booking.check_in)
          );
          const cost = findResolvedCost(booking, resolvedBookings);

          return (
            <Card key={booking.id} className="py-3">
              <CardContent className="flex items-center justify-between px-4 py-0">
                <div className="min-w-0 flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="font-medium truncate">
                      {booking.resort_name}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      {booking.room_key}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <span>{booking.contract_name}</span>
                    <span>|</span>
                    <span>
                      {format(parseISO(booking.check_in), "MMM d")} -{" "}
                      {format(parseISO(booking.check_out), "MMM d, yyyy")} (
                      {nights} {nights === 1 ? "night" : "nights"})
                    </span>
                    <span>|</span>
                    {cost !== null ? (
                      <span className="font-medium text-foreground">
                        {cost} pts
                      </span>
                    ) : isEvaluating ? (
                      <span className="flex items-center gap-1">
                        <Loader2 className="size-3 animate-spin" />
                        Calculating...
                      </span>
                    ) : (
                      <span>--</span>
                    )}
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  className="text-muted-foreground hover:text-destructive shrink-0 ml-2"
                  onClick={() => removeBooking(booking.id)}
                >
                  <Trash2 className="size-4" />
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
