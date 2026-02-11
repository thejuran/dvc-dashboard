import { Link } from "react-router-dom";
import { FlaskConical, RotateCcw } from "lucide-react";
import { useScenarioStore } from "@/store/useScenarioStore";
import { useScenarioEvaluation } from "@/hooks/useScenarioEvaluation";
import { useContracts } from "@/hooks/useContracts";
import { Button } from "@/components/ui/button";
import ScenarioBookingForm from "@/components/ScenarioBookingForm";
import ScenarioBookingList from "@/components/ScenarioBookingList";
import ScenarioComparison from "@/components/ScenarioComparison";

export default function ScenarioPage() {
  const bookings = useScenarioStore((s) => s.bookings);
  const clearAll = useScenarioStore((s) => s.clearAll);
  const { data: contracts, isLoading: contractsLoading } = useContracts();
  const evaluation = useScenarioEvaluation(bookings);

  // Empty state: no contracts exist
  if (!contractsLoading && contracts && contracts.length === 0) {
    return (
      <div>
        <div className="mb-6 flex items-center gap-3">
          <FlaskConical className="size-6 text-muted-foreground" />
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              What-If Scenarios
            </h2>
            <p className="text-sm text-muted-foreground">
              Model hypothetical bookings and compare point impact
            </p>
          </div>
        </div>
        <div className="rounded-md border p-8 text-center">
          <p className="text-muted-foreground">
            No contracts found. Add contracts first to model scenarios.
          </p>
          <Link
            to="/contracts"
            className="mt-2 inline-block text-sm text-primary underline underline-offset-4 hover:text-primary/80"
          >
            Go to Contracts
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Page header */}
      <div className="mb-6 flex items-start justify-between">
        <div className="flex items-center gap-3">
          <FlaskConical className="size-6 text-muted-foreground" />
          <div>
            <h2 className="text-2xl font-bold tracking-tight">
              What-If Scenarios
            </h2>
            <p className="text-sm text-muted-foreground">
              Model hypothetical bookings and compare point impact
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          size="sm"
          disabled={bookings.length === 0}
          onClick={() => clearAll()}
        >
          <RotateCcw className="size-4" />
          Clear All
        </Button>
      </div>

      <div className="space-y-6">
        {/* Booking form */}
        <ScenarioBookingForm bookingCount={bookings.length} />

        {/* Booking list */}
        <ScenarioBookingList
          bookings={bookings}
          resolvedBookings={evaluation.data?.resolved_bookings ?? []}
          isEvaluating={evaluation.isLoading}
        />

        {/* Comparison table - only when bookings exist */}
        {bookings.length > 0 ? (
          <ScenarioComparison
            data={evaluation.data}
            isLoading={evaluation.isLoading}
          />
        ) : (
          <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
            Add hypothetical bookings above to see how they affect your point
            balances.
          </div>
        )}
      </div>
    </div>
  );
}
