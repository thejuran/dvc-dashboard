import { useState } from "react";
import { PencilIcon, TrashIcon, XCircleIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useResorts } from "../hooks/useContracts";
import { useUpdateReservation, useDeleteReservation } from "../hooks/useReservations";
import { parseRoomKey, formatDateRange, nightsBetween } from "../lib/utils";
import type { Reservation } from "../types";

interface ReservationCardProps {
  reservation: Reservation;
  contractName?: string;
  onEdit: (reservation: Reservation) => void;
}

const statusConfig: Record<
  string,
  { label: string; className: string }
> = {
  confirmed: {
    label: "Confirmed",
    className: "bg-green-100 text-green-700 border-green-200",
  },
  pending: {
    label: "Pending",
    className: "bg-amber-100 text-amber-700 border-amber-200",
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-gray-100 text-gray-500 border-gray-200",
  },
};

export default function ReservationCard({
  reservation,
  contractName,
  onEdit,
}: ReservationCardProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const { data: resorts } = useResorts();
  const updateReservation = useUpdateReservation();
  const deleteReservation = useDeleteReservation();

  const resort = resorts?.find((r) => r.slug === reservation.resort);
  const resortName = resort?.short_name || reservation.resort;
  const { roomType, view } = parseRoomKey(reservation.room_key);
  const nights = nightsBetween(reservation.check_in, reservation.check_out);
  const dateRange = formatDateRange(reservation.check_in, reservation.check_out);
  const isCancelled = reservation.status === "cancelled";
  const status = statusConfig[reservation.status] || statusConfig.confirmed;

  const handleCancel = async () => {
    await updateReservation.mutateAsync({
      id: reservation.id,
      data: { status: "cancelled" },
    });
  };

  const handleDelete = async () => {
    await deleteReservation.mutateAsync(reservation.id);
    setShowDeleteConfirm(false);
  };

  return (
    <>
      <Card className={isCancelled ? "opacity-60" : ""}>
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div>
              <CardTitle className="text-base">{resortName}</CardTitle>
              <p className="text-sm text-muted-foreground mt-0.5">
                {roomType}
                {view && ` - ${view}`}
              </p>
            </div>
            <Badge variant="secondary" className={status.className}>
              {status.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-2">
          <div className="text-sm">
            <span className="text-muted-foreground">Dates: </span>
            <span className={isCancelled ? "line-through" : ""}>
              {dateRange}
            </span>
            <span className="text-muted-foreground"> ({nights} night{nights !== 1 ? "s" : ""})</span>
          </div>

          <div className="text-sm">
            <span className="text-muted-foreground">Points: </span>
            <span className={`font-semibold ${isCancelled ? "line-through text-muted-foreground" : ""}`}>
              {reservation.points_cost}
            </span>
          </div>

          {reservation.confirmation_number && (
            <div className="text-sm">
              <span className="text-muted-foreground">Confirmation: </span>
              <span className="font-mono text-xs">
                {reservation.confirmation_number}
              </span>
            </div>
          )}

          {contractName && (
            <div className="text-xs text-muted-foreground">
              Contract: {contractName}
            </div>
          )}

          {reservation.notes && (
            <div className="text-xs text-muted-foreground italic">
              {reservation.notes}
            </div>
          )}

          <div className="flex items-center gap-2 pt-1">
            <Button
              variant="ghost"
              size="xs"
              onClick={() => onEdit(reservation)}
              disabled={isCancelled}
            >
              <PencilIcon className="size-3" />
              Edit
            </Button>
            {!isCancelled && (
              <Button
                variant="ghost"
                size="xs"
                className="text-amber-600 hover:text-amber-600"
                onClick={handleCancel}
                disabled={updateReservation.isPending}
              >
                <XCircleIcon className="size-3" />
                Cancel
              </Button>
            )}
            <Button
              variant="ghost"
              size="xs"
              className="text-destructive hover:text-destructive"
              onClick={() => setShowDeleteConfirm(true)}
            >
              <TrashIcon className="size-3" />
              Delete
            </Button>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Reservation</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this reservation at {resortName} ({dateRange})?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteConfirm(false)}
            >
              Keep
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteReservation.isPending}
            >
              {deleteReservation.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
