import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Modal from "../components/Modal.jsx";
import BookingForm from "../components/BookingForm.jsx";
import { Empty, ErrorBox, Loading } from "../components/States.jsx";
import { formatTime, initials, todayISO } from "../utils.js";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [today, setToday] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [s, appts, docs] = await Promise.all([api.stats(), api.appointments({ day: todayISO() }), api.doctors()]);
      setStats(s);
      setToday(appts);
      setDoctors(docs);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function setStatus(appt, status) {
    try {
      await api.updateAppointment(appt.id, { status });
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={load} />;

  const s = stats.by_status;
  const waiting = today.filter((a) => a.status === "checked_in");
  const cards = [
    { label: "Appointments today", value: stats.appointments_today, hint: `${s.scheduled} still to come` },
    { label: "In waiting room", value: s.checked_in, hint: waiting[0] ? `Next: ${waiting[0].patient_name}` : "Nobody waiting" },
    { label: "Seen today", value: s.completed, hint: `${s.cancelled + s.no_show} cancelled / no-show` },
    { label: "Doctors on duty", value: stats.doctors, hint: stats.busiest_doctor ? `Busiest: ${stats.busiest_doctor}` : "—" },
  ];

  const perDoctor = doctors.map((d) => ({
    ...d,
    count: today.filter((a) => a.doctor_id === d.id && a.status !== "cancelled").length,
  }));

  return (
    <div className="stack">
      <section className="cards">
        {cards.map((c) => (
          <div className="card stat" key={c.label}>
            <span className="muted">{c.label}</span>
            <strong>{c.value}</strong>
            <small>{c.hint}</small>
          </div>
        ))}
      </section>

      <div className="split">
        <section className="panel">
          <div className="panel-head">
            <h2>Today's schedule</h2>
            <button className="btn" onClick={() => setBooking(true)}>
              + Book
            </button>
          </div>
          {today.length === 0 ? (
            <Empty text="No appointments booked for today yet." />
          ) : (
            <ul className="timeline">
              {today.map((a) => (
                <li key={a.id} className={`tl-item tl-${a.status}`}>
                  <time>{formatTime(a.start_time)}</time>
                  <div className="tl-body">
                    <div className="tl-title">
                      <strong>{a.patient_name}</strong>
                      <StatusBadge status={a.status} />
                    </div>
                    <span className="muted">
                      {a.doctor_name} · {a.reason || "General consultation"}
                    </span>
                  </div>
                  <div className="tl-actions">
                    {a.status === "scheduled" && (
                      <button className="btn btn-small" onClick={() => setStatus(a, "checked_in")}>
                        Check in
                      </button>
                    )}
                    {a.status === "checked_in" && (
                      <button className="btn btn-small" onClick={() => setStatus(a, "completed")}>
                        Done
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Doctors</h2>
          </div>
          <ul className="doc-list">
            {perDoctor.map((d) => (
              <li key={d.id}>
                <span className="avatar">{initials(d.name)}</span>
                <div>
                  <strong>{d.name}</strong>
                  <span className="muted">
                    {d.specialty} · Room {d.room || "—"}
                  </span>
                </div>
                <span className={`pill ${d.active ? "pill-green" : "pill-grey"}`}>
                  {d.active ? `${d.count} today` : "Off"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {booking && (
        <Modal title="Book appointment" onClose={() => setBooking(false)}>
          <BookingForm
            onCancel={() => setBooking(false)}
            onBooked={() => {
              setBooking(false);
              load();
            }}
          />
        </Modal>
      )}
    </div>
  );
}
