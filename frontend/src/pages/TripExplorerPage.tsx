import { useState } from "react";
import { Search } from "lucide-react";
import { useTripExplorer } from "../hooks/useTripExplorer";
import TripExplorerForm from "../components/TripExplorerForm";
import TripExplorerResults from "../components/TripExplorerResults";
import ErrorAlert from "../components/ErrorAlert";
import EmptyState from "../components/EmptyState";

export default function TripExplorerPage() {
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");

  const { data, isLoading, error, refetch } = useTripExplorer(
    checkIn || null,
    checkOut || null
  );

  const showPrompt = !checkIn && !checkOut && !data;

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight">Trip Explorer</h2>
        <p className="text-sm text-muted-foreground">
          Find what you can afford for a date range
        </p>
      </div>

      <TripExplorerForm
        checkIn={checkIn}
        checkOut={checkOut}
        onCheckInChange={setCheckIn}
        onCheckOutChange={setCheckOut}
        isLoading={isLoading}
      />

      {error && (
        <ErrorAlert message={error.message} onRetry={() => refetch()} />
      )}

      {data && <TripExplorerResults data={data} checkIn={checkIn} checkOut={checkOut} />}

      {showPrompt && (
        <EmptyState
          icon={Search}
          title="Ready to explore"
          description="Select check-in and check-out dates above to see what you can book."
        />
      )}
    </div>
  );
}
