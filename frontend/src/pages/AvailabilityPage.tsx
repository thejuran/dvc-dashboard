import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAvailability } from "../hooks/useAvailability";
import AvailabilityCard from "../components/AvailabilityCard";
import LoadingSkeleton from "../components/LoadingSkeleton";
import ErrorAlert from "../components/ErrorAlert";
import EmptyState from "../components/EmptyState";

function todayISO(): string {
  return new Date().toISOString().split("T")[0];
}

export default function AvailabilityPage() {
  const navigate = useNavigate();
  const [targetDate, setTargetDate] = useState(todayISO());
  const { data, isLoading, error, refetch } = useAvailability(targetDate || null);

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold tracking-tight">
          Point Availability
        </h2>
        <p className="text-sm text-muted-foreground">
          See how many points are available across all contracts for any date
        </p>
      </div>

      <div className="mb-6">
        <Label htmlFor="target-date">Target Date</Label>
        <Input
          id="target-date"
          type="date"
          value={targetDate}
          onChange={(e) => setTargetDate(e.target.value)}
          className="w-full sm:w-48 mt-1"
        />
      </div>

      {isLoading && <LoadingSkeleton variant="detail" />}

      {error && (
        <ErrorAlert message={error.message} onRetry={() => refetch()} />
      )}

      {data && (
        <div className="space-y-6">
          {/* Summary banner */}
          <Card className="bg-primary/5 border-primary/20">
            <CardHeader>
              <CardTitle className="text-sm text-muted-foreground">
                Total Available
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-4xl font-bold">
                {data.summary.total_available}{" "}
                <span className="text-lg font-normal text-muted-foreground">
                  points
                </span>
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                across {data.summary.total_contracts} contract
                {data.summary.total_contracts !== 1 ? "s" : ""} on{" "}
                {new Date(data.target_date + "T12:00:00").toLocaleDateString(
                  "en-US",
                  { month: "long", day: "numeric", year: "numeric" }
                )}
              </p>
              {data.summary.total_committed > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {data.summary.total_points} total -{" "}
                  {data.summary.total_committed} committed ={" "}
                  {data.summary.total_available} available
                </p>
              )}
            </CardContent>
          </Card>

          {/* Per-contract cards */}
          {data.contracts.length > 0 ? (
            <div className="grid gap-4 sm:grid-cols-1 md:grid-cols-2">
              {data.contracts.map((c) => (
                <AvailabilityCard key={c.contract_id} data={c} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon={BarChart3}
              title="No contracts found"
              description="Add a contract first to see point availability."
              action={{ label: "Go to Contracts", onClick: () => navigate("/contracts") }}
            />
          )}
        </div>
      )}
    </div>
  );
}
