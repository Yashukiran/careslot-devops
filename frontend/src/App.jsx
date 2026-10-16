import { useEffect, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Appointments from "./pages/Appointments.jsx";
import Patients from "./pages/Patients.jsx";
import Doctors from "./pages/Doctors.jsx";

const PAGES = {
  dashboard: { title: "Today at the clinic", component: Dashboard },
  appointments: { title: "Appointments", component: Appointments },
  patients: { title: "Patients", component: Patients },
  doctors: { title: "Doctors", component: Doctors },
};

function currentPage() {
  const key = window.location.hash.replace("#/", "");
  return PAGES[key] ? key : "dashboard";
}

export default function App() {
  const [page, setPage] = useState(currentPage);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onHash = () => {
      setPage(currentPage());
      setMenuOpen(false);
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const { title, component: Page } = PAGES[page];
  const today = new Date().toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" });

  return (
    <div className="layout">
      <Sidebar active={page} open={menuOpen} onClose={() => setMenuOpen(false)} />
      <main className="main">
        <header className="topbar">
          <button className="menu-btn" onClick={() => setMenuOpen(true)} aria-label="Open menu">
            ☰
          </button>
          <div>
            <h1>{title}</h1>
            <p className="muted">{today}</p>
          </div>
        </header>
        <Page />
      </main>
    </div>
  );
}
