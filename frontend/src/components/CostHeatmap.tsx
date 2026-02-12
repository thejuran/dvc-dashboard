import { useState, useMemo, useEffect } from "react";
import { format, parseISO } from "date-fns";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { heatColor } from "@/lib/utils";
import type { PointChart, RoomInfo, Season } from "../types";

interface CostHeatmapProps {
  chart: PointChart;
  rooms: RoomInfo[];
}

interface DayCost {
  date: string;       // "2026-01-15"
  day: number;        // 15
  points: number;     // e.g. 14
  season: string;     // "Adventure"
  isWeekend: boolean; // true for Fri(5) and Sat(6) per DVC definition
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const DAY_LABELS = ["S", "M", "T", "W", "T", "F", "S"];

const COST_TIERS = [
  { label: "Low", className: "bg-green-400" },
  { label: "Below Avg", className: "bg-lime-400" },
  { label: "Average", className: "bg-yellow-400" },
  { label: "Above Avg", className: "bg-orange-400" },
  { label: "High", className: "bg-red-400" },
];

export default function CostHeatmap({ chart, rooms }: CostHeatmapProps) {
  const [roomKey, setRoomKey] = useState("");
  const [tooltip, setTooltip] = useState<{ x: number; y: number; data: DayCost } | null>(null);

  // Auto-reset room key when rooms change (resort switch)
  useEffect(() => {
    if (rooms.length > 0) {
      setRoomKey(rooms[0].key);
    } else {
      setRoomKey("");
    }
  }, [rooms]);

  // Build daily costs from chart data
  const dailyCosts = useMemo(() => {
    if (!roomKey) return [];

    // Build date-to-season lookup
    const dateSeasonMap: Record<string, Season> = {};
    for (const season of chart.seasons) {
      for (const [startStr, endStr] of season.date_ranges) {
        const start = new Date(startStr + "T00:00:00");
        const end = new Date(endStr + "T00:00:00");
        const current = new Date(start);
        while (current <= end) {
          const key = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}-${String(current.getDate()).padStart(2, "0")}`;
          dateSeasonMap[key] = season;
          current.setDate(current.getDate() + 1);
        }
      }
    }

    // Walk every day of the year
    const result: DayCost[] = [];
    const year = chart.year;
    const startDate = new Date(year, 0, 1);
    const endDate = new Date(year, 11, 31);
    const current = new Date(startDate);

    while (current <= endDate) {
      const dateStr = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, "0")}-${String(current.getDate()).padStart(2, "0")}`;
      const day = current.getDate();
      const dow = current.getDay();
      const isWeekend = dow === 5 || dow === 6; // DVC: Fri=5, Sat=6

      const season = dateSeasonMap[dateStr];
      let points = 0;
      let seasonName = "";

      if (season) {
        seasonName = season.name;
        const roomData = season.rooms[roomKey];
        if (roomData) {
          points = isWeekend ? roomData.weekend : roomData.weekday;
        }
      }

      result.push({ date: dateStr, day, points, season: seasonName, isWeekend });
      current.setDate(current.getDate() + 1);
    }

    return result;
  }, [chart, roomKey]);

  // Compute min/max from valid point costs
  const { min, max } = useMemo(() => {
    const validPoints = dailyCosts.filter((d) => d.points > 0).map((d) => d.points);
    if (validPoints.length === 0) return { min: 0, max: 0 };
    return {
      min: Math.min(...validPoints),
      max: Math.max(...validPoints),
    };
  }, [dailyCosts]);

  if (!roomKey) {
    return (
      <div className="text-center py-12 border rounded-lg bg-muted/30">
        <p className="text-muted-foreground">Select a room type to view the cost heatmap.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Room selector */}
      <div className="max-w-sm space-y-1">
        <label className="text-sm font-medium">Room Type</label>
        <Select value={roomKey} onValueChange={setRoomKey}>
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

      {/* 12-month grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {MONTH_NAMES.map((monthName, monthIndex) => (
          <HeatmapMonthGrid
            key={monthName}
            year={chart.year}
            month={monthIndex}
            monthName={monthName}
            dailyCosts={dailyCosts.filter(
              (d) => parseInt(d.date.split("-")[1], 10) === monthIndex + 1
            )}
            min={min}
            max={max}
            onHover={(x, y, data) => setTooltip({ x, y, data })}
            onLeave={() => setTooltip(null)}
          />
        ))}
      </div>

      {/* Tooltip */}
      {tooltip && (
        <div
          className="fixed z-50 bg-popover text-popover-foreground border rounded-lg shadow-lg px-3 py-2 text-sm pointer-events-none"
          style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
        >
          <div className="font-semibold">{format(parseISO(tooltip.data.date), "EEEE, MMM d, yyyy")}</div>
          <div className="text-muted-foreground">Season: {tooltip.data.season}</div>
          <div>
            <span className="font-medium">{tooltip.data.points} points</span>
            <span className="text-muted-foreground ml-1">({tooltip.data.isWeekend ? "Weekend" : "Weekday"})</span>
          </div>
        </div>
      )}

      {/* Color legend */}
      <div className="mt-6 flex flex-wrap gap-4 justify-center">
        {COST_TIERS.map((tier) => (
          <div key={tier.label} className="flex items-center gap-2">
            <div className={`w-4 h-4 rounded ${tier.className}`} />
            <span className="text-sm">{tier.label}</span>
          </div>
        ))}
      </div>

      {/* Weekend indicator legend */}
      <div className="mt-3 flex gap-4 justify-center text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-foreground/60" />
          Weekend (Fri/Sat)
        </div>
      </div>
    </div>
  );
}

interface HeatmapMonthGridProps {
  year: number;
  month: number;
  monthName: string;
  dailyCosts: DayCost[];
  min: number;
  max: number;
  onHover: (x: number, y: number, data: DayCost) => void;
  onLeave: () => void;
}

function HeatmapMonthGrid({
  year,
  month,
  monthName,
  dailyCosts,
  min,
  max,
  onHover,
  onLeave,
}: HeatmapMonthGridProps) {
  const firstDay = new Date(year, month, 1);
  const startDow = firstDay.getDay(); // 0=Sun
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  // Build a lookup map for this month's costs
  const costMap = useMemo(() => {
    const map: Record<number, DayCost> = {};
    for (const dc of dailyCosts) {
      map[dc.day] = dc;
    }
    return map;
  }, [dailyCosts]);

  const cells: (number | null)[] = [];
  // Pad start
  for (let i = 0; i < startDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);
  // Pad end to fill last row
  while (cells.length % 7 !== 0) cells.push(null);

  return (
    <div className="border rounded-lg p-3">
      <h3 className="text-sm font-semibold text-center mb-2">{monthName}</h3>
      <div className="grid grid-cols-7 gap-0.5 text-center">
        {DAY_LABELS.map((label, i) => (
          <div key={i} className="text-xs font-medium text-muted-foreground py-1">
            {label}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day === null) {
            return <div key={i} className="h-7" />;
          }
          const dayCost = costMap[day];
          const hasPoints = dayCost && dayCost.points > 0;

          return (
            <div
              key={i}
              className={`h-7 flex items-center justify-center text-xs rounded relative cursor-default ${
                hasPoints ? heatColor(dayCost.points, min, max) : "text-muted-foreground"
              }`}
              onMouseEnter={(e) => {
                if (dayCost) {
                  onHover(e.clientX, e.clientY, dayCost);
                }
              }}
              onMouseLeave={onLeave}
            >
              {day}
              {dayCost?.isWeekend && (
                <span className="absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full bg-foreground/60" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
