import { useEffect, useState } from "react";
import { api } from "../api.js";

const LINKS = [
  { key: "dashboard", label: "Dashboard", icon: "▦" },
  { key: "appointments", label: "Appointments", icon: "◷" },
  { key: "patients", label: "Patients", icon: "☺" },
  { key: "doctors", label: "Doctors", icon: "✚" },
];

// small "which build is running" indicator, handy right after a pipeline deploy
function BuildStatus() {
  const [info, setInfo] = useState(null);
  const [down, setDown] = useState(false);

  useEffect(() => {
    const check = () =>
      api
        .info()
        .then((i) => {
          setInfo(i);
          setDown(i.database !== "ok");
        })
        .catch(() => setDown(true));
    check();
    const t = setInterval(check, 30000);
    return () => clearInterval(t);
  }, []);

  return (
    <div className="build">
      <div className="build-row">
        <span className={`dot ${down ? "dot-red" : ""}`} />
        {down ? "API unreachable" : "All systems running"}
      </div>
      {info && (
        <div className="build-meta">
          build <code>{info.version.slice(0, 7)}</code> · {info.environment}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ active, open, onClose }) {
  return (
    <>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-mark">+</span>
          <div>
            <strong>CareSlot</strong>
            <small>Sunrise Family Clinic</small>
          </div>
        </div>
        <nav>
          {LINKS.map((link) => (
            <a key={link.key} href={`#/${link.key}`} className={active === link.key ? "active" : ""}>
              <span className="icon">{link.icon}</span>
              {link.label}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="muted-light">Front desk · Reception 1</span>
          <BuildStatus />
        </div>
      </aside>
      {open && <div className="backdrop" onClick={onClose} />}
    </>
  );
}
