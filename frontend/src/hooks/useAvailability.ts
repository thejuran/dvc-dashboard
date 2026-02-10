import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { AvailabilityResponse } from "../types";

export function useAvailability(targetDate: string | null) {
  return useQuery({
    queryKey: ["availability", targetDate],
    queryFn: () =>
      api.get<AvailabilityResponse>(`/availability?target_date=${targetDate}`),
    enabled: !!targetDate,
  });
}
