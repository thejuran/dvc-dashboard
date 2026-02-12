import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useResorts, useCreateContract, useUpdateContract } from "../hooks/useContracts";
import {
  USE_YEAR_MONTHS,
  USE_YEAR_MONTH_NAMES,
} from "../types";
import type {
  ContractWithDetails,
  PurchaseType,
} from "../types";
import { ApiError } from "@/lib/api";

interface ContractFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editContract?: ContractWithDetails | null;
}

function validateField(name: string, value: string): string {
  switch (name) {
    case "homeResort":
      return value ? "" : "Home resort is required";
    case "useYearMonth":
      return value ? "" : "Use year month is required";
    case "annualPoints": {
      if (!value) return "Annual points is required";
      const n = Number(value);
      if (isNaN(n) || n < 1 || n > 2000)
        return "Annual points must be between 1 and 2,000";
      return "";
    }
    case "name":
      return value.length > 100 ? "Name must be 100 characters or less" : "";
    default:
      return "";
  }
}

export default function ContractFormDialog({
  open,
  onOpenChange,
  editContract,
}: ContractFormDialogProps) {
  const { data: resorts } = useResorts();
  const createContract = useCreateContract();
  const updateContract = useUpdateContract();

  const [name, setName] = useState("");
  const [homeResort, setHomeResort] = useState("");
  const [useYearMonth, setUseYearMonth] = useState<string>("");
  const [annualPoints, setAnnualPoints] = useState("");
  const [purchaseType, setPurchaseType] = useState<PurchaseType>("resale");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const isEditing = !!editContract;

  // Sync form state from props when dialog opens
  useEffect(() => {
    if (editContract) {
      setName(editContract.name || "");
      setHomeResort(editContract.home_resort);
      setUseYearMonth(String(editContract.use_year_month));
      setAnnualPoints(String(editContract.annual_points));
      setPurchaseType(editContract.purchase_type);
    } else {
      setName("");
      setHomeResort("");
      setUseYearMonth("");
      setAnnualPoints("");
      setPurchaseType("resale");
    }
    setFieldErrors({});
  }, [editContract, open]);

  const handleBlur = (fieldName: string, value: string) => {
    const error = validateField(fieldName, value);
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const handleSelectChange = (fieldName: string, value: string, setter: (v: string) => void) => {
    setter(value);
    const error = validateField(fieldName, value);
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const validateAll = (): boolean => {
    const errors: Record<string, string> = {};
    errors.name = validateField("name", name);
    errors.homeResort = validateField("homeResort", homeResort);
    errors.useYearMonth = validateField("useYearMonth", useYearMonth);
    errors.annualPoints = validateField("annualPoints", annualPoints);

    // Remove empty errors
    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(errors)) {
      if (v) filtered[k] = v;
    }
    setFieldErrors(filtered);
    return Object.keys(filtered).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateAll()) return;

    const data = {
      name: name || undefined,
      home_resort: homeResort,
      use_year_month: Number(useYearMonth),
      annual_points: Number(annualPoints),
      purchase_type: purchaseType,
    };

    try {
      if (isEditing && editContract) {
        await updateContract.mutateAsync({ id: editContract.id, data });
      } else {
        await createContract.mutateAsync(data);
      }
      onOpenChange(false);
    } catch (err) {
      if (err instanceof ApiError && err.fields.length > 0) {
        setFieldErrors(err.toFieldErrors());
      }
    }
  };

  const isPending = createContract.isPending || updateContract.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Contract" : "Add Contract"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update your DVC contract details."
              : "Add a new DVC contract to track."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nickname (optional)</Label>
            <Input
              id="name"
              placeholder="e.g., Our Poly contract"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => handleBlur("name", name)}
            />
            {fieldErrors.name && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.name}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="home_resort">Home Resort</Label>
            <Select
              value={homeResort}
              onValueChange={(v) => handleSelectChange("homeResort", v, setHomeResort)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select a resort" />
              </SelectTrigger>
              <SelectContent>
                {resorts?.map((r) => (
                  <SelectItem key={r.slug} value={r.slug}>
                    {r.short_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fieldErrors.homeResort && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.homeResort}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="use_year_month">Use Year Month</Label>
            <Select
              value={useYearMonth}
              onValueChange={(v) => handleSelectChange("useYearMonth", v, setUseYearMonth)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select month" />
              </SelectTrigger>
              <SelectContent>
                {USE_YEAR_MONTHS.map((m) => (
                  <SelectItem key={m} value={String(m)}>
                    {USE_YEAR_MONTH_NAMES[m]}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fieldErrors.useYearMonth && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.useYearMonth}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="annual_points">Annual Points</Label>
            <Input
              id="annual_points"
              type="number"
              min="1"
              max="2000"
              placeholder="e.g., 160"
              value={annualPoints}
              onChange={(e) => setAnnualPoints(e.target.value)}
              onBlur={() => handleBlur("annualPoints", annualPoints)}
              required
            />
            {fieldErrors.annualPoints && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.annualPoints}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="purchase_type">Purchase Type</Label>
            <Select
              value={purchaseType}
              onValueChange={(v) => setPurchaseType(v as PurchaseType)}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="resale">Resale</SelectItem>
                <SelectItem value="direct">Direct</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                isPending || !homeResort || !useYearMonth || !annualPoints
              }
            >
              {isPending
                ? "Saving..."
                : isEditing
                ? "Update"
                : "Add Contract"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
