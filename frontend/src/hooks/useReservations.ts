import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { Reservation } from "../types";

export function useReservations(filters?: {
  contractId?: number;
  status?: string;
  upcoming?: boolean;
}) {
  const params = new URLSearchParams();
  if (filters?.contractId) params.set("contract_id", String(filters.contractId));
  if (filters?.status) params.set("status", filters.status);
  if (filters?.upcoming) params.set("upcoming", "true");
  const qs = params.toString();

  return useQuery({
    queryKey: ["reservations", filters],
    queryFn: () => api.get<Reservation[]>(`/reservations${qs ? `?${qs}` : ""}`),
  });
}

export function useContractReservations(contractId: number) {
  return useQuery({
    queryKey: ["reservations", "contract", contractId],
    queryFn: () =>
      api.get<Reservation[]>(`/contracts/${contractId}/reservations`),
    enabled: contractId > 0,
  });
}

export function useCreateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      contractId,
      data,
    }: {
      contractId: number;
      data: {
        resort: string;
        room_key: string;
        check_in: string;
        check_out: string;
        points_cost: number;
        status?: string;
        confirmation_number?: string;
        notes?: string;
      };
    }) => api.post<Reservation>(`/contracts/${contractId}/reservations`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });
}

export function useUpdateReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number;
      data: Partial<{
        resort: string;
        room_key: string;
        check_in: string;
        check_out: string;
        points_cost: number;
        status: string;
        confirmation_number: string;
        notes: string;
      }>;
    }) => api.put<Reservation>(`/reservations/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });
}

export function useDeleteReservation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.delete(`/reservations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reservations"] });
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });
}
