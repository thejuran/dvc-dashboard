import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { ReservationPreview } from "../types";

interface PreviewRequest {
  contract_id: number;
  resort: string;
  room_key: string;
  check_in: string;
  check_out: string;
}

export function useBookingPreview(request: PreviewRequest | null) {
  return useQuery({
    queryKey: [
      "booking-preview",
      request?.contract_id,
      request?.resort,
      request?.room_key,
      request?.check_in,
    ],
    queryFn: () =>
      api.post<ReservationPreview>("/reservations/preview", request),
    enabled: !!request,
    staleTime: 30_000,
  });
}
