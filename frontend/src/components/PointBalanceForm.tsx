import { useState } from "react";
import { PlusIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  useContractPoints,
  useCreatePointBalance,
} from "../hooks/usePoints";
import type { PointAllocationType } from "../types";
import { ALLOCATION_TYPE_LABELS } from "../types";
import { ApiError } from "@/lib/api";

interface PointBalanceFormProps {
  contractId: number;
}

const ALLOCATION_TYPES: PointAllocationType[] = [
  "current",
  "banked",
  "borrowed",
  "holding",
];

function validateField(name: string, value: string): string {
  switch (name) {
    case "useYear": {
      if (!value) return "Use year is required";
      const n = Number(value);
      if (isNaN(n) || n < 2020 || n > 2035)
        return "Use year must be between 2020 and 2035";
      return "";
    }
    case "points": {
      if (value === "" || value === undefined) return "Points is required";
      const n = Number(value);
      if (isNaN(n) || n < 0) return "Points must be 0 or more";
      return "";
    }
    case "allocationType":
      return value ? "" : "Allocation type is required";
    default:
      return "";
  }
}

export default function PointBalanceForm({ contractId }: PointBalanceFormProps) {
  const { data: pointsData } = useContractPoints(contractId);
  const createBalance = useCreatePointBalance();

  const [showAddForm, setShowAddForm] = useState(false);
  const [newYear, setNewYear] = useState(new Date().getFullYear());
  const [newType, setNewType] = useState<PointAllocationType>("current");
  const [newPoints, setNewPoints] = useState(0);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleBlur = (fieldName: string, value: string) => {
    const error = validateField(fieldName, value);
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const handleSelectChange = (value: string) => {
    setNewType(value as PointAllocationType);
    const error = validateField("allocationType", value);
    setFieldErrors((prev) => ({ ...prev, allocationType: error }));
  };

  const validateAll = (): boolean => {
    const errors: Record<string, string> = {};
    errors.useYear = validateField("useYear", String(newYear));
    errors.points = validateField("points", String(newPoints));
    errors.allocationType = validateField("allocationType", newType);

    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(errors)) {
      if (v) filtered[k] = v;
    }
    setFieldErrors(filtered);
    return Object.keys(filtered).length === 0;
  };

  const handleAdd = async () => {
    if (!validateAll()) return;

    try {
      await createBalance.mutateAsync({
        contractId,
        data: {
          use_year: newYear,
          allocation_type: newType,
          points: newPoints,
        },
      });
      setShowAddForm(false);
      setNewPoints(0);
      setFieldErrors({});
    } catch (err) {
      if (err instanceof ApiError && err.fields.length > 0) {
        setFieldErrors(err.toFieldErrors());
      }
    }
  };

  if (!pointsData) return null;

  const years = Object.keys(pointsData.balances_by_year).sort();

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Point Balances</h4>
        <Button
          variant="outline"
          size="xs"
          onClick={() => {
            setShowAddForm(!showAddForm);
            setFieldErrors({});
          }}
        >
          <PlusIcon className="size-3" />
          Add
        </Button>
      </div>

      {showAddForm && (
        <div className="rounded-md border p-3 bg-muted/30 space-y-2">
          <div className="flex items-end gap-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Year</label>
              <Input
                type="number"
                value={newYear}
                onChange={(e) => setNewYear(Number(e.target.value))}
                onBlur={() => handleBlur("useYear", String(newYear))}
                className="w-20 h-8 text-sm"
                min={2020}
                max={2035}
              />
              {fieldErrors.useYear && (
                <p className="text-xs text-destructive mt-1">{fieldErrors.useYear}</p>
              )}
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Type</label>
              <Select
                value={newType}
                onValueChange={handleSelectChange}
              >
                <SelectTrigger className="w-28 h-8 text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ALLOCATION_TYPES.map((t) => (
                    <SelectItem key={t} value={t}>
                      {ALLOCATION_TYPE_LABELS[t]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {fieldErrors.allocationType && (
                <p className="text-xs text-destructive mt-1">{fieldErrors.allocationType}</p>
              )}
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Points</label>
              <Input
                type="number"
                value={newPoints}
                onChange={(e) => setNewPoints(Number(e.target.value))}
                onBlur={() => handleBlur("points", String(newPoints))}
                className="w-20 h-8 text-sm"
                min={0}
              />
              {fieldErrors.points && (
                <p className="text-xs text-destructive mt-1">{fieldErrors.points}</p>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAdd} disabled={createBalance.isPending}>
              Save
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowAddForm(false);
                setFieldErrors({});
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      )}

      {years.length > 0 ? (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Year</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Points</TableHead>
              <TableHead className="w-16"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {years.map((year) => {
              const yearData = pointsData.balances_by_year[year];
              return ALLOCATION_TYPES.filter((t) => yearData[t] > 0).map(
                (allocType) => {
                  // We need the actual balance ID for edit/delete. For now use a composite key approach.
                  // The grouped API doesn't return individual IDs, so we derive actions from contract points.
                  return (
                    <TableRow key={`${year}-${allocType}`}>
                      <TableCell className="text-sm">{year}</TableCell>
                      <TableCell className="text-sm">
                        {ALLOCATION_TYPE_LABELS[allocType]}
                      </TableCell>
                      <TableCell className="text-right text-sm font-medium">
                        {yearData[allocType]}
                      </TableCell>
                      <TableCell className="text-right">
                        {/* Edit/delete require individual balance IDs which come from the detail endpoint */}
                      </TableCell>
                    </TableRow>
                  );
                }
              );
            })}
            <TableRow className="font-semibold">
              <TableCell colSpan={2}>Total</TableCell>
              <TableCell className="text-right">
                {pointsData.grand_total}
              </TableCell>
              <TableCell></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      ) : (
        <p className="text-sm text-muted-foreground">
          No point balances entered yet.
        </p>
      )}
    </div>
  );
}
