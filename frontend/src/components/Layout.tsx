import { useState, useEffect } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/trip-explorer", label: "Trip Explorer" },
  { to: "/scenarios", label: "Scenarios" },
  { to: "/contracts", label: "Contracts" },
  { to: "/availability", label: "Availability" },
  { to: "/reservations", label: "Reservations" },
  { to: "/point-charts", label: "Point Charts" },
  { to: "/settings", label: "Settings" },
];

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Close sidebar on route change
  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen">
      {/* Mobile top bar */}
      <div className="fixed top-0 left-0 right-0 h-14 border-b bg-background z-30 flex items-center justify-between px-4 md:hidden">
        <h1 className="text-lg font-bold tracking-tight">DVC Dashboard</h1>
        <button
          onClick={() => setSidebarOpen(true)}
          className="rounded-md p-2 hover:bg-accent"
          aria-label="Open menu"
        >
          <Menu className="size-5" />
        </button>
      </div>

      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar overlay */}
      <aside
        className={`fixed left-0 top-0 bottom-0 w-64 z-50 bg-background border-r p-6 flex flex-col gap-6 transition-transform duration-200 ease-in-out md:hidden ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight">DVC Dashboard</h1>
            <p className="text-sm text-muted-foreground">Point Tracker</p>
          </div>
          <button
            onClick={() => setSidebarOpen(false)}
            className="rounded-md p-1 hover:bg-accent"
            aria-label="Close menu"
          >
            <X className="size-5" />
          </button>
        </div>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent hover:text-accent-foreground"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden md:flex w-64 border-r bg-muted/40 p-6 flex-col gap-6">
        <div>
          <h1 className="text-xl font-bold tracking-tight">DVC Dashboard</h1>
          <p className="text-sm text-muted-foreground">Point Tracker</p>
        </div>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "hover:bg-accent hover:text-accent-foreground"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-4 md:p-8 pt-18 md:pt-8">
        <Outlet />
      </main>
    </div>
  );
}
