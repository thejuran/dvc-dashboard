import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { LayoutDashboard } from "lucide-react";
import { useContracts } from "../hooks/useContracts";
import { useAvailability } from "../hooks/useAvailability";
import { useReservations } from "../hooks/useReservations";
import { useUpcomingBookingWindows } from "../hooks/useBookingWindows";
import DashboardSummaryCards from "../components/DashboardSummaryCards";
import UrgentAlerts from "../components/UrgentAlerts";
import UpcomingReservations from "../components/UpcomingReservations";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorAlert from "../components/ErrorAlert";
import EmptyState from "../components/EmptyState";

function todayISO(): string {
  return new Date().toISOString().split("T")[0];
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const {
    data: contracts,
    isLoading: contractsLoading,
    error: contractsError,
    refetch: refetchContracts,
  } = useContracts();

  const {
    data: availability,
    isLoading: availabilityLoading,
    error: availabilityError,
    refetch: refetchAvailability,
  } = useAvailability(todayISO());

  const {
    data: reservations,
    isLoading: reservationsLoading,
    error: reservationsError,
    refetch: refetchReservations,
  } = useReservations({ upcoming: true });

  const { data: bookingWindowAlerts } = useUpcomingBookingWindows();

  const isLoading = contractsLoading || availabilityLoading || reservationsLoading;
  const error = contractsError || availabilityError || reservationsError;
  const refetchAll = () => {
    refetchContracts();
    refetchAvailability();
    refetchReservations();
  };

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

      {isLoading && <LoadingSkeleton variant="cards" />}

      {error && (
        <ErrorAlert message={error.message} onRetry={refetchAll} />
      )}

      {!isLoading && !error && contracts && contracts.length === 0 && (
        <EmptyState
          icon={LayoutDashboard}
          title="No contracts yet"
          description="Add your first DVC contract to see your dashboard overview."
          action={{ label: "Add Contract", onClick: () => navigate("/contracts") }}
        />
      )}

      {!isLoading && !error && contracts && contracts.length > 0 && (
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
