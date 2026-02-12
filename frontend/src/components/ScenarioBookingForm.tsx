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

  function handleContractChange(value: string) {
    setSelectedContractId(value);
    setSelectedResort("");
    setSelectedRoom("");
  }

  function handleResortChange(value: string) {
    setSelectedResort(value);
    setSelectedRoom("");
  }

  function handleSubmit() {
    if (!isFormComplete || atCap || !selectedContract) return;

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
          </div>

          {/* Room type selector */}
          <div className="space-y-2">
            <Label>Room Type</Label>
            <Select
              value={selectedRoom}
              onValueChange={setSelectedRoom}
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
          </div>

          {/* Check-in date */}
          <div className="space-y-2">
            <Label>Check-in</Label>
            <Input
              type="date"
              value={checkIn}
              min={today}
              onChange={(e) => {
                setCheckIn(e.target.value);
                // Reset check-out if it's before new check-in
                if (checkOut && e.target.value >= checkOut) {
                  setCheckOut("");
                }
              }}
            />
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
              onChange={(e) => setCheckOut(e.target.value)}
            />
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
