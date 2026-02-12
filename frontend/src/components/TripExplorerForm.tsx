import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface TripExplorerFormProps {
  checkIn: string;
  checkOut: string;
  onCheckInChange: (v: string) => void;
  onCheckOutChange: (v: string) => void;
  isLoading: boolean;
}

export default function TripExplorerForm({
  checkIn,
  checkOut,
  onCheckInChange,
  onCheckOutChange,
  isLoading,
}: TripExplorerFormProps) {
  return (
    <div className="mb-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-4">
        <div className="w-full sm:w-auto">
          <Label htmlFor="check-in">Check-in</Label>
          <Input
            id="check-in"
            type="date"
            value={checkIn}
            onChange={(e) => onCheckInChange(e.target.value)}
            className="w-full sm:w-48 mt-1"
          />
        </div>
        <div className="w-full sm:w-auto">
          <Label htmlFor="check-out">Check-out</Label>
          <Input
            id="check-out"
            type="date"
            value={checkOut}
            onChange={(e) => onCheckOutChange(e.target.value)}
            className="w-full sm:w-48 mt-1"
          />
        </div>
      </div>
      {isLoading && (
        <p className="text-sm text-muted-foreground mt-2">Searching...</p>
      )}
    </div>
  );
}
