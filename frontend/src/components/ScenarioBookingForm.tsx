import { useState, useMemo } from "react";
import { Plus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useContracts, useResorts } from "@/hooks/useContracts";
import { useAvailableCharts, useChartRooms } from "@/hooks/usePointCharts";
import { useScenarioStore } from "@/store/useScenarioStore";

interface ScenarioBookingFormProps {
  bookingCount: number;
}

function validateField(
  name: string,
  value: string,
  extra?: { checkIn?: string }
): string {
  switch (name) {
    case "contractId":
      return value ? "" : "Contract is required";
    case "resort":
      return value ? "" : "Resort is required";
    case "roomKey":
      return value ? "" : "Room type is required";
    case "checkIn":
      return value ? "" : "Check-in date is required";
    case "checkOut": {
      if (!value) return "Check-out date is required";
      if (extra?.checkIn && value <= extra.checkIn)
        return "Check-out must be after check-in";
      if (extra?.checkIn) {
        const start = new Date(extra.checkIn + "T00:00:00");
        const end = new Date(value + "T00:00:00");
        const nights = Math.round(
          (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
        );
        if (nights > 14) return "Stay cannot exceed 14 nights";
      }
      return "";
    }
    default:
      return "";
  }
}

export default function ScenarioBookingForm({
  bookingCount,
}: ScenarioBookingFormProps) {
  const { data: contracts } = useContracts();
  const { data: resorts } = useResorts();
  const { data: availableCharts } = useAvailableCharts();

  const [selectedContractId, setSelectedContractId] = useState<string>("");
  const [selectedResort, setSelectedResort] = useState<string>("");
  const [selectedRoom, setSelectedRoom] = useState<string>("");
  const [checkIn, setCheckIn] = useState<string>("");
  const [checkOut, setCheckOut] = useState<string>("");
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const addBooking = useScenarioStore((s) => s.addBooking);

  const currentYear = new Date().getFullYear();
  const { data: chartRoomsData } = useChartRooms(selectedResort, currentYear);

  const selectedContract = useMemo(
    () => contracts?.find((c) => c.id === Number(selectedContractId)),
    [contracts, selectedContractId]
  );

  const chartsResortSet = useMemo(() => {
    if (!availableCharts) return new Set<string>();
    return new Set(availableCharts.map((c) => c.resort));
  }, [availableCharts]);

  const eligibleResorts = useMemo(() => {
    if (!selectedContract || !resorts) return [];
    return resorts.filter(
      (r) =>
        selectedContract.eligible_resorts.includes(r.slug) &&
        chartsResortSet.has(r.slug)
    );
  }, [selectedContract, resorts, chartsResortSet]);

  const roomKeys = useMemo(() => {
    if (!chartRoomsData?.rooms) return [];
    return chartRoomsData.rooms;
  }, [chartRoomsData]);

  const today = new Date().toISOString().split("T")[0];

  const maxCheckOut = useMemo(() => {
    if (!checkIn) return "";
    const d = new Date(checkIn + "T00:00:00");
    d.setDate(d.getDate() + 14);
    return d.toISOString().split("T")[0];
  }, [checkIn]);

  const isFormComplete =
    selectedContractId &&
    selectedResort &&
    selectedRoom &&
    checkIn &&
    checkOut &&
    checkOut > checkIn;

  const atCap = bookingCount >= 10;

  const handleBlur = (fieldName: string, value: string) => {
    const error = validateField(fieldName, value, { checkIn });
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const handleSelectChange = (
    fieldName: string,
    value: string,
    setter: (v: string) => void
  ) => {
    setter(value);
    const error = validateField(fieldName, value, { checkIn });
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
  };

  const handleDateChange = (
    fieldName: string,
    value: string,
    setter: (v: string) => void
  ) => {
    setter(value);
    const ci = fieldName === "checkIn" ? value : checkIn;
    const error = validateField(fieldName, value, { checkIn: ci });
    setFieldErrors((prev) => ({ ...prev, [fieldName]: error }));
    // Re-validate checkOut when checkIn changes
    if (fieldName === "checkIn" && checkOut) {
      const coError = validateField("checkOut", checkOut, { checkIn: value });
      setFieldErrors((prev) => ({ ...prev, checkOut: coError }));
    }
  };

  function handleContractChange(value: string) {
    setSelectedContractId(value);
    setSelectedResort("");
    setSelectedRoom("");
    const error = validateField("contractId", value);
    setFieldErrors((prev) => ({ ...prev, contractId: error }));
  }

  function handleResortChange(value: string) {
    setSelectedResort(value);
    setSelectedRoom("");
    const error = validateField("resort", value);
    setFieldErrors((prev) => ({ ...prev, resort: error }));
  }

  const validateAll = (): boolean => {
    const errors: Record<string, string> = {};
    errors.contractId = validateField("contractId", selectedContractId);
    errors.resort = validateField("resort", selectedResort);
    errors.roomKey = validateField("roomKey", selectedRoom);
    errors.checkIn = validateField("checkIn", checkIn);
    errors.checkOut = validateField("checkOut", checkOut, { checkIn });

    const filtered: Record<string, string> = {};
    for (const [k, v] of Object.entries(errors)) {
      if (v) filtered[k] = v;
    }
    setFieldErrors(filtered);
    return Object.keys(filtered).length === 0;
  };

  function handleSubmit() {
    if (atCap || !selectedContract) return;
    if (!validateAll()) return;

    const resort = resorts?.find((r) => r.slug === selectedResort);

    addBooking({
      contract_id: Number(selectedContractId),
      contract_name: selectedContract.name || selectedContract.home_resort,
      resort: selectedResort,
      resort_name: resort?.name || selectedResort,
      room_key: selectedRoom,
      check_in: checkIn,
      check_out: checkOut,
    });

    // Reset form except contract selection
    setSelectedResort("");
    setSelectedRoom("");
    setCheckIn("");
    setCheckOut("");
    setFieldErrors({});
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add Hypothetical Booking</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {/* Contract selector */}
          <div className="space-y-2">
            <Label>Contract</Label>
            <Select
              value={selectedContractId}
              onValueChange={handleContractChange}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select contract" />
              </SelectTrigger>
              <SelectContent>
                {contracts?.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name || c.home_resort} ({c.annual_points} pts)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fieldErrors.contractId && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.contractId}</p>
            )}
          </div>

          {/* Resort selector */}
          <div className="space-y-2">
            <Label>Resort</Label>
            <Select
              value={selectedResort}
              onValueChange={handleResortChange}
              disabled={!selectedContractId}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select resort" />
              </SelectTrigger>
              <SelectContent>
                {eligibleResorts.map((r) => (
                  <SelectItem key={r.slug} value={r.slug}>
                    {r.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fieldErrors.resort && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.resort}</p>
            )}
          </div>

          {/* Room type selector */}
          <div className="space-y-2">
            <Label>Room Type</Label>
            <Select
              value={selectedRoom}
              onValueChange={(v) => handleSelectChange("roomKey", v, setSelectedRoom)}
              disabled={!selectedResort}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select room" />
              </SelectTrigger>
              <SelectContent>
                {roomKeys.map((room) => (
                  <SelectItem key={room.key} value={room.key}>
                    {room.room_type} - {room.view}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {fieldErrors.roomKey && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.roomKey}</p>
            )}
          </div>

          {/* Check-in date */}
          <div className="space-y-2">
            <Label>Check-in</Label>
            <Input
              type="date"
              value={checkIn}
              min={today}
              onChange={(e) => {
                handleDateChange("checkIn", e.target.value, setCheckIn);
                // Reset check-out if it's before new check-in
                if (checkOut && e.target.value >= checkOut) {
                  setCheckOut("");
                }
              }}
              onBlur={() => handleBlur("checkIn", checkIn)}
            />
            {fieldErrors.checkIn && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.checkIn}</p>
            )}
          </div>

          {/* Check-out date */}
          <div className="space-y-2">
            <Label>Check-out</Label>
            <Input
              type="date"
              value={checkOut}
              min={checkIn || today}
              max={maxCheckOut}
              disabled={!checkIn}
              onChange={(e) => handleDateChange("checkOut", e.target.value, setCheckOut)}
              onBlur={() => handleBlur("checkOut", checkOut)}
            />
            {fieldErrors.checkOut && (
              <p className="text-xs text-destructive mt-1">{fieldErrors.checkOut}</p>
            )}
          </div>

          {/* Add button */}
          <div className="flex items-end">
            <Button
              onClick={handleSubmit}
              disabled={!isFormComplete || atCap}
              className="w-full"
            >
              <Plus className="size-4" />
              Add to Scenario
            </Button>
          </div>
        </div>

        {atCap && (
          <p className="mt-2 text-sm text-muted-foreground">
            Maximum of 10 bookings reached. Remove a booking to add more.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
