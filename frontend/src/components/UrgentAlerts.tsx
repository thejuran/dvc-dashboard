import {
  AlertTriangleIcon,
  ClockIcon,
  CalendarCheckIcon,
  CalendarClockIcon,
} from "lucide-react";
import { format, parseISO } from "date-fns";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import type { AvailabilityContractResult, BookingWindowAlert } from "../types";

interface UrgentAlertsProps {
  items: AvailabilityContractResult[];
  bookingWindowAlerts?: BookingWindowAlert[];
}

export default function UrgentAlerts({
  items,
  bookingWindowAlerts,
}: UrgentAlertsProps) {
  return (
    <Card className="border-amber-200 bg-amber-50">
      <CardHeader>
        <div className="flex items-center gap-2 font-semibold text-amber-800">
          <AlertTriangleIcon className="size-4" />
          Action Needed
        </div>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          {items.map((item) => {
            if (
              !item.banking_deadline_passed &&
              item.days_until_banking_deadline <= 60
            ) {
              return (
                <li
                  key={`banking-${item.contract_id}`}
                  className="flex items-start gap-2 text-sm text-amber-700"
                >
                  <ClockIcon className="size-4 mt-0.5 shrink-0" />
                  <span>
                    {item.contract_name}: Banking deadline in{" "}
                    {item.days_until_banking_deadline} days (
                    {item.available_points} pts available)
                  </span>
                </li>
              );
            }

            if (item.days_until_expiration <= 90) {
              return (
                <li
                  key={`expiry-${item.contract_id}`}
                  className="flex items-start gap-2 text-sm text-red-700"
                >
                  <AlertTriangleIcon className="size-4 mt-0.5 shrink-0" />
                  <span>
                    {item.contract_name}: Points expire in{" "}
                    {item.days_until_expiration} days
                  </span>
                </li>
              );
            }

            return null;
          })}
          {bookingWindowAlerts?.map((alert, idx) => (
            <li
              key={`bw-${alert.window_type}-${alert.resort}-${idx}`}
              className="flex items-start gap-2 text-sm text-blue-700"
            >
              {alert.window_type === "home_resort" ? (
                <CalendarCheckIcon className="size-4 mt-0.5 shrink-0" />
              ) : (
                <CalendarClockIcon className="size-4 mt-0.5 shrink-0" />
              )}
              <span>
                {alert.contract_name} @ {alert.resort_name}:{" "}
                {alert.window_type === "home_resort" ? "11-month" : "7-month"}{" "}
                window opens in {alert.days_until_open} day
                {alert.days_until_open !== 1 ? "s" : ""} (
                {format(parseISO(alert.window_date), "MMM d")}) -- check-in{" "}
                {format(parseISO(alert.check_in), "MMM d, yyyy")}
              </span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
