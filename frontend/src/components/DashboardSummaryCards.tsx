import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AvailabilityResponse, ContractWithDetails } from "../types";

interface DashboardSummaryCardsProps {
  availability: AvailabilityResponse | undefined;
  contracts: ContractWithDetails[] | undefined;
}

export default function DashboardSummaryCards({
  availability,
  contracts,
}: DashboardSummaryCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            Contracts
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">{contracts?.length ?? "--"}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            Total Points
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold">
            {availability?.summary.total_points ?? "--"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            Available Points
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-green-600">
            {availability?.summary.total_available ?? "--"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm text-muted-foreground">
            Committed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-3xl font-bold text-amber-600">
            {availability?.summary.total_committed ?? "--"}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
