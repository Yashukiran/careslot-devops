const LINKS = [
  { key: "dashboard", label: "Dashboard", icon: "▦" },
  { key: "appointments", label: "Appointments", icon: "◷" },
  { key: "patients", label: "Patients", icon: "☺" },
  { key: "doctors", label: "Doctors", icon: "✚" },
];

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
          <span className="dot" /> Front desk · Reception 1
        </div>
      </aside>
      {open && <div className="backdrop" onClick={onClose} />}
    </>
  );
}
