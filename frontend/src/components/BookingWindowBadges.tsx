import { format, parseISO } from "date-fns";
import { Badge } from "@/components/ui/badge";
import type { BookingWindowInfo } from "../types";

interface BookingWindowBadgesProps {
  windows: BookingWindowInfo;
}

export default function BookingWindowBadges({ windows }: BookingWindowBadgesProps) {
  const formatDate = (iso: string) => format(parseISO(iso), "MMM d, yyyy");

  const homeWindowSoon =
    !windows.home_resort_window_open &&
    windows.days_until_home_window >= 0 &&
    windows.days_until_home_window <= 14;

  const anyWindowSoon =
    !windows.any_resort_window_open &&
    windows.days_until_any_window >= 0 &&
    windows.days_until_any_window <= 14;

  return (
    <div className="flex gap-2 flex-wrap">
      {windows.is_home_resort && (
        <Badge
          variant="secondary"
          className={`${
            windows.home_resort_window_open
              ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
              : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
          }${homeWindowSoon ? " ring-2 ring-blue-300 animate-pulse" : ""}`}
        >
          {windows.home_resort_window_open
            ? "11-mo Home: Open"
            : `11-mo Home: Opens ${formatDate(windows.home_resort_window)}`}
        </Badge>
      )}

      <Badge
        variant="secondary"
        className={`${
          windows.any_resort_window_open
            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
            : "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        }${anyWindowSoon ? " ring-2 ring-blue-300 animate-pulse" : ""}`}
      >
        {windows.any_resort_window_open
          ? "7-mo: Open"
          : `7-mo: Opens ${formatDate(windows.any_resort_window)}`}
      </Badge>
    </div>
  );
}
