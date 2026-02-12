import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Layout from "./components/Layout";
import ErrorBoundary from "./components/ErrorBoundary";
import DashboardPage from "./pages/DashboardPage";
import ContractsPage from "./pages/ContractsPage";
import PointChartsPage from "./pages/PointChartsPage";
import ReservationsPage from "./pages/ReservationsPage";
import AvailabilityPage from "./pages/AvailabilityPage";
import TripExplorerPage from "./pages/TripExplorerPage";
import ScenarioPage from "./pages/ScenarioPage";
import SettingsPage from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<ErrorBoundary section="Dashboard"><DashboardPage /></ErrorBoundary>} />
            <Route path="/trip-explorer" element={<ErrorBoundary section="Trip Explorer"><TripExplorerPage /></ErrorBoundary>} />
            <Route path="/scenarios" element={<ErrorBoundary section="Scenarios"><ScenarioPage /></ErrorBoundary>} />
            <Route path="/contracts" element={<ErrorBoundary section="Contracts"><ContractsPage /></ErrorBoundary>} />
            <Route path="/availability" element={<ErrorBoundary section="Availability"><AvailabilityPage /></ErrorBoundary>} />
            <Route path="/reservations" element={<ErrorBoundary section="Reservations"><ReservationsPage /></ErrorBoundary>} />
            <Route path="/point-charts" element={<ErrorBoundary section="Point Charts"><PointChartsPage /></ErrorBoundary>} />
            <Route path="/settings" element={<ErrorBoundary section="Settings"><SettingsPage /></ErrorBoundary>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
