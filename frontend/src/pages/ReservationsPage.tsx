import { useState } from "react";
import { PlusIcon, CalendarDays } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useReservations } from "../hooks/useReservations";
import { useContracts } from "../hooks/useContracts";
import ReservationCard from "../components/ReservationCard";
import ReservationFormDialog from "../components/ReservationFormDialog";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorAlert from "../components/ErrorAlert";
import EmptyState from "../components/EmptyState";
import type { Reservation } from "../types";

export default function ReservationsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [upcomingOnly, setUpcomingOnly] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [editReservation, setEditReservation] = useState<Reservation | null>(
    null
  );

  const filters = {
    status: statusFilter !== "all" ? statusFilter : undefined,
    upcoming: upcomingOnly || undefined,
  };

  const { data: reservations, isLoading, error, refetch } = useReservations(filters);
  const { data: contracts } = useContracts();

  const contractNameMap = new Map(
    contracts?.map((c) => [c.id, c.name || c.home_resort]) || []
  );

  const handleEdit = (reservation: Reservation) => {
    setEditReservation(reservation);
    setFormOpen(true);
  };

  const handleOpenChange = (open: boolean) => {
    setFormOpen(open);
    if (!open) setEditReservation(null);
  };

  return (
    <div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Reservations</h2>
          <p className="text-sm text-muted-foreground">
            Track your DVC resort reservations
          </p>
        </div>
        <Button onClick={() => setFormOpen(true)}>
          <PlusIcon className="size-4" />
          Add Reservation
        </Button>
      </div>

      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="confirmed">Confirmed</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant={upcomingOnly ? "default" : "outline"}
          size="sm"
          onClick={() => setUpcomingOnly(!upcomingOnly)}
        >
          Upcoming Only
        </Button>
      </div>

      {isLoading && <LoadingSkeleton variant="cards" />}

      {error && (
        <ErrorAlert message={error.message} onRetry={() => refetch()} />
      )}

      {reservations && reservations.length === 0 && (
        <EmptyState
          icon={CalendarDays}
          title="No reservations yet"
          description="Add your first reservation to track your DVC bookings."
          action={{ label: "Add Reservation", onClick: () => setFormOpen(true) }}
        />
      )}

      {reservations && reservations.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2">
          {reservations.map((reservation) => (
            <ReservationCard
              key={reservation.id}
              reservation={reservation}
              contractName={contractNameMap.get(reservation.contract_id)}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}

      <ReservationFormDialog
        open={formOpen}
        onOpenChange={handleOpenChange}
        editReservation={editReservation}
      />
    </div>
  );
}
