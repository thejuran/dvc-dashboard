import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { BookingWindowAlert } from "../types";

export function useUpcomingBookingWindows() {
  return useQuery({
    queryKey: ["booking-windows", "upcoming"],
    queryFn: () => api.get<BookingWindowAlert[]>("/booking-windows/upcoming"),
  });
}
