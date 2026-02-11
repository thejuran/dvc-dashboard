import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { HypotheticalBooking, ScenarioEvaluateResponse } from "../types";

export function useScenarioEvaluation(bookings: HypotheticalBooking[]) {
  return useQuery({
    queryKey: ["scenario-evaluate", ...bookings.map((b) => b.id)],
    queryFn: () =>
      api.post<ScenarioEvaluateResponse>("/scenarios/evaluate", {
        hypothetical_bookings: bookings.map((b) => ({
          contract_id: b.contract_id,
          resort: b.resort,
          room_key: b.room_key,
          check_in: b.check_in,
          check_out: b.check_out,
        })),
      }),
    enabled: bookings.length > 0,
    staleTime: 30_000,
  });
}
