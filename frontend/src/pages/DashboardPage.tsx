import { useMemo } from "react";
import { useContracts } from "../hooks/useContracts";
import { useAvailability } from "../hooks/useAvailability";
import { useReservations } from "../hooks/useReservations";
import { useUpcomingBookingWindows } from "../hooks/useBookingWindows";
import DashboardSummaryCards from "../components/DashboardSummaryCards";
import UrgentAlerts from "../components/UrgentAlerts";
import UpcomingReservations from "../components/UpcomingReservations";

function todayISO(): string {
  return new Date().toISOString().split("T")[0];
}

export default function DashboardPage() {
  const {
    data: contracts,
    isLoading: contractsLoading,
    error: contractsError,
  } = useContracts();

  const {
    data: availability,
    isLoading: availabilityLoading,
    error: availabilityError,
  } = useAvailability(todayISO());

  const {
    data: reservations,
    isLoading: reservationsLoading,
    error: reservationsError,
  } = useReservations({ upcoming: true });

  const { data: bookingWindowAlerts } = useUpcomingBookingWindows();

  const isLoading = contractsLoading || availabilityLoading || reservationsLoading;
  const error = contractsError || availabilityError || reservationsError;

  const urgentItems = useMemo(() => {
    if (!availability?.contracts) return [];
    return availability.contracts.filter(
      (c) =>
        (!c.banking_deadline_passed && c.days_until_banking_deadline <= 60) ||
        c.days_until_expiration <= 90
    );
  }, [availability]);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Overview of your DVC points and upcoming reservations
        </p>
      </div>

      {isLoading && (
        <p className="text-muted-foreground">Loading dashboard...</p>
      )}

      {error && (
        <p className="text-destructive">
          Failed to load dashboard: {error.message}
        </p>
      )}

      {!isLoading && !error && (
        <div className="space-y-6">
          <DashboardSummaryCards
            availability={availability}
            contracts={contracts}
          />

          {(urgentItems.length > 0 ||
            (bookingWindowAlerts && bookingWindowAlerts.length > 0)) && (
            <UrgentAlerts
              items={urgentItems}
              bookingWindowAlerts={bookingWindowAlerts ?? []}
            />
          )}

          <UpcomingReservations reservations={reservations} />
        </div>
      )}
    </div>
  );
}
