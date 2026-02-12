import { AlertTriangleIcon } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import type { ScenarioEvaluateResponse } from "@/types";

interface ScenarioComparisonProps {
  data: ScenarioEvaluateResponse | undefined;
  isLoading: boolean;
}

function formatImpact(impact: number): string {
  if (impact === 0) return "0 pts";
  return `${impact > 0 ? "-" : "+"}${Math.abs(impact)} pts`;
}

export default function ScenarioComparison({
  data,
  isLoading,
}: ScenarioComparisonProps) {
  if (isLoading || !data) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-medium">Baseline vs Scenario</h3>
        <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
          {isLoading
            ? "Calculating scenario impact..."
            : "Add bookings to see comparison"}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium">Baseline vs Scenario</h3>

      <div className="rounded-md border overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Contract</TableHead>
              <TableHead className="text-right">Baseline</TableHead>
              <TableHead className="text-right">Scenario</TableHead>
              <TableHead className="text-right">Impact</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.contracts.map((contract) => (
              <TableRow key={contract.contract_id}>
                <TableCell>
                  <div>
                    <span className="font-medium">
                      {contract.contract_name}
                    </span>
                    {contract.home_resort !== contract.contract_name && (
                      <span className="ml-1 text-muted-foreground text-xs">
                        ({contract.home_resort})
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  {contract.baseline_available} pts
                </TableCell>
                <TableCell className="text-right">
                  {contract.scenario_available} pts
                </TableCell>
                <TableCell
                  className={`text-right font-medium ${
                    contract.impact > 0
                      ? "text-destructive"
                      : contract.impact === 0
                        ? "text-muted-foreground"
                        : "text-muted-foreground"
                  }`}
                >
                  {formatImpact(contract.impact)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableFooter>
            <TableRow>
              <TableCell className="font-semibold">Total</TableCell>
              <TableCell className="text-right font-semibold">
                {data.summary.baseline_available} pts
              </TableCell>
              <TableCell className="text-right font-semibold">
                {data.summary.scenario_available} pts
              </TableCell>
              <TableCell
                className={`text-right font-semibold ${
                  data.summary.total_impact > 0
                    ? "text-destructive"
                    : "text-muted-foreground"
                }`}
              >
                {formatImpact(data.summary.total_impact)}
              </TableCell>
            </TableRow>
          </TableFooter>
        </Table>
      </div>

      {data.errors.length > 0 && (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-3 dark:border-amber-900 dark:bg-amber-950">
          <div className="flex items-center gap-2 text-sm font-medium text-amber-800 dark:text-amber-200">
            <AlertTriangleIcon className="size-4" />
            Some bookings could not be evaluated
          </div>
          <ul className="mt-2 space-y-1 text-sm text-amber-700 dark:text-amber-300">
            {data.errors.map((err, i) => (
              <li key={i}>
                {err.resort} / {err.room_key}: {err.error}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
