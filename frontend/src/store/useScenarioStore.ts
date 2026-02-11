import { create } from "zustand";
import type { HypotheticalBooking } from "../types";

interface ScenarioState {
  bookings: HypotheticalBooking[];
  addBooking: (booking: Omit<HypotheticalBooking, "id">) => void;
  removeBooking: (id: string) => void;
  clearAll: () => void;
}

export const useScenarioStore = create<ScenarioState>()((set) => ({
  bookings: [],
  addBooking: (booking) =>
    set((state) => ({
      bookings: [
        ...state.bookings,
        { ...booking, id: crypto.randomUUID() },
      ],
    })),
  removeBooking: (id) =>
    set((state) => ({
      bookings: state.bookings.filter((b) => b.id !== id),
    })),
  clearAll: () => set({ bookings: [] }),
}));
