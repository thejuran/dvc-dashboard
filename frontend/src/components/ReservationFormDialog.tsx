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
import { useContracts, useResorts } from "../hooks/useContracts";
import { useChartRooms, useCalculateStayCost } from "../hooks/usePointCharts";
import { useCreateReservation, useUpdateReservation } from "../hooks/useReservations";
import type { Reservation } from "../types";

interface ReservationFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editReservation?: Reservation | null;
}

export default function ReservationFormDialog({
  open,
  onOpenChange,
  editReservation,
}: ReservationFormDialogProps) {
  const { data: contracts } = useContracts();
  const { data: resorts } = useResorts();
  const createReservation = useCreateReservation();
  const updateReservation = useUpdateReservation();

  const [contractId, setContractId] = useState("");
  const [resort, setResort] = useState("");
  const [roomKey, setRoomKey] = useState("");
  const [checkIn, setCheckIn] = useState("");
  const [checkOut, setCheckOut] = useState("");
  const [pointsCost, setPointsCost] = useState("");
  const [status, setStatus] = useState("confirmed");
  const [confirmationNumber, setConfirmationNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [calcError, setCalcError] = useState<string | null>(null);

  const isEditing = !!editReservation;

  // Get selected contract's eligible resorts
  const selectedContract = contracts?.find(
    (c) => c.id === Number(contractId)
  );
  const eligibleResorts = selectedContract?.eligible_resorts || [];
  const eligibleResortData = resorts?.filter((r) =>
    eligibleResorts.includes(r.slug)
  );

  // Get room types for selected resort
  const currentYear = new Date().getFullYear();
  const { data: chartRoomsData } = useChartRooms(resort, currentYear);
  const rooms = chartRoomsData?.rooms || [];

  const calculateCost = useCalculateStayCost();

  useEffect(() => {
    if (editReservation) {
      setContractId(String(editReservation.contract_id));
      setResort(editReservation.resort);
      setRoomKey(editReservation.room_key);
      setCheckIn(editReservation.check_in);
      setCheckOut(editReservation.check_out);
      setPointsCost(String(editReservation.points_cost));
      setStatus(editReservation.status);
      setConfirmationNumber(editReservation.confirmation_number || "");
      setNotes(editReservation.notes || "");
    } else {
      setContractId("");
      setResort("");
      setRoomKey("");
      setCheckIn("");
      setCheckOut("");
      setPointsCost("");
      setStatus("confirmed");
      setConfirmationNumber("");
      setNotes("");
    }
    setCalcError(null);
  }, [editReservation, open]);

  // Reset resort and room when contract changes
  useEffect(() => {
    if (!isEditing) {
      setResort("");
      setRoomKey("");
    }
  }, [contractId, isEditing]);

  useEffect(() => {
    if (!isEditing) {
      setRoomKey("");
    }
  }, [resort, isEditing]);

  const handleCalculateCost = () => {
    if (!resort || !roomKey || !checkIn || !checkOut) {
      setCalcError("Fill in resort, room, and dates first.");
      return;
    }
    setCalcError(null);
    calculateCost.mutate(
      { resort, room_key: roomKey, check_in: checkIn, check_out: checkOut },
      {
        onSuccess: (data) => {
          setPointsCost(String(data.total_points));
          setCalcError(null);
        },
        onError: (err) => {
          setCalcError(err.message || "Could not calculate cost.");
        },
      }
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      resort,
      room_key: roomKey,
      check_in: checkIn,
      check_out: checkOut,
      points_cost: Number(pointsCost),
      status,
      confirmation_number: confirmationNumber || undefined,
      notes: notes || undefined,
    };

    if (isEditing && editReservation) {
      await updateReservation.mutateAsync({ id: editReservation.id, data });
    } else {
      await createReservation.mutateAsync({
        contractId: Number(contractId),
        data,
      });
    }
    onOpenChange(false);
  };

  const isPending = createReservation.isPending || updateReservation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? "Edit Reservation" : "Add Reservation"}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? "Update your reservation details."
              : "Add a new DVC reservation to track."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isEditing && (
            <div className="space-y-2">
              <Label>Contract</Label>
              <Select value={contractId} onValueChange={setContractId}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select contract..." />
                </SelectTrigger>
                <SelectContent>
                  {contracts?.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name || c.home_resort} ({c.annual_points} pts)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Resort</Label>
              <Select
                value={resort}
                onValueChange={setResort}
                disabled={!isEditing && !contractId}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select resort..." />
                </SelectTrigger>
                <SelectContent>
                  {(isEditing ? resorts : eligibleResortData)?.map((r) => (
                    <SelectItem key={r.slug} value={r.slug}>
                      {r.short_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Room Type</Label>
              <Select
                value={roomKey}
                onValueChange={setRoomKey}
                disabled={!resort}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select room..." />
                </SelectTrigger>
                <SelectContent>
                  {rooms.map((room) => (
                    <SelectItem key={room.key} value={room.key}>
                      {room.room_type} - {room.view}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="res-check-in">Check-in</Label>
              <Input
                id="res-check-in"
                type="date"
                value={checkIn}
                onChange={(e) => setCheckIn(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="res-check-out">Check-out</Label>
              <Input
                id="res-check-out"
                type="date"
                min={checkIn}
                value={checkOut}
                onChange={(e) => setCheckOut(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="points-cost">Points Cost</Label>
            <div className="flex gap-2">
              <Input
                id="points-cost"
                type="number"
                min="1"
                placeholder="e.g., 85"
                value={pointsCost}
                onChange={(e) => setPointsCost(e.target.value)}
                required
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCalculateCost}
                disabled={calculateCost.isPending || !resort || !roomKey || !checkIn || !checkOut}
              >
                {calculateCost.isPending ? "..." : "Calculate"}
              </Button>
            </div>
            {calcError && (
              <p className="text-xs text-destructive">{calcError}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label>Status</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="confirmed">Confirmed</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmation-number">
              Confirmation Number (optional)
            </Label>
            <Input
              id="confirmation-number"
              placeholder="e.g., ABC123"
              value={confirmationNumber}
              onChange={(e) => setConfirmationNumber(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Input
              id="notes"
              placeholder="e.g., Spring break trip"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
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
                isPending ||
                (!isEditing && !contractId) ||
                !resort ||
                !checkIn ||
                !checkOut ||
                !pointsCost
              }
            >
              {isPending
                ? "Saving..."
                : isEditing
                ? "Update"
                : "Add Reservation"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
