import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const VIEW_CATEGORIES = [
  "standard",
  "standard_view",
  "preferred",
  "preferred_view",
  "lake",
  "lake_view",
  "theme_park",
  "theme_park_view",
  "pool",
  "pool_view",
  "garden",
  "garden_view",
  "ocean",
  "ocean_view",
  "lagoon",
  "lagoon_view",
  "savanna",
  "savanna_view",
  "value",
  "woods",
  "near_pool",
  "courtyard",
];

export function parseRoomKey(roomKey: string): { roomType: string; view: string } {
  // Try longest-match view category suffix
  for (const vc of VIEW_CATEGORIES.sort((a, b) => b.length - a.length)) {
    if (roomKey.endsWith(`_${vc}`)) {
      const roomPart = roomKey.slice(0, roomKey.length - vc.length - 1);
      return {
        roomType: roomPart.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        view: vc.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
      };
    }
  }
  // Fallback: no view suffix found
  return {
    roomType: roomKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
    view: "",
  };
}

export function formatDateRange(checkIn: string, checkOut: string): string {
  const ci = new Date(checkIn + "T12:00:00");
  const co = new Date(checkOut + "T12:00:00");
  const ciMonth = ci.toLocaleDateString("en-US", { month: "short" });
  const coMonth = co.toLocaleDateString("en-US", { month: "short" });
  const year = ci.getFullYear();

  if (ciMonth === coMonth) {
    return `${ciMonth} ${ci.getDate()} - ${co.getDate()}, ${year}`;
  }
  return `${ciMonth} ${ci.getDate()} - ${coMonth} ${co.getDate()}, ${year}`;
}

export function nightsBetween(checkIn: string, checkOut: string): number {
  const ci = new Date(checkIn);
  const co = new Date(checkOut);
  return Math.round((co.getTime() - ci.getTime()) / (1000 * 60 * 60 * 24));
}

/** Map a point value to a heat-map background class (green=low, yellow=mid, red=high). */
export function heatColor(value: number, min: number, max: number): string {
  if (max === min) return "bg-green-100 dark:bg-green-900/30";
  const ratio = (value - min) / (max - min);
  if (ratio < 0.2) return "bg-green-100 dark:bg-green-900/30";
  if (ratio < 0.4) return "bg-lime-100 dark:bg-lime-900/30";
  if (ratio < 0.6) return "bg-yellow-100 dark:bg-yellow-900/30";
  if (ratio < 0.8) return "bg-orange-100 dark:bg-orange-900/30";
  return "bg-red-100 dark:bg-red-900/30";
}
