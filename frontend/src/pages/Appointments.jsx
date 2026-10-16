import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import StatusBadge from "../components/StatusBadge.jsx";
import Modal from "../components/Modal.jsx";
import BookingForm from "../components/BookingForm.jsx";
import { Empty, ErrorBox, Loading } from "../components/States.jsx";
import { STATUS_LABELS, formatDate, formatTime, todayISO } from "../utils.js";

export default function Appointments() {
  const [filters, setFilters] = useState({ day: todayISO(), doctor_id: "", status_filter: "" });
  const [rows, setRows] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [booking, setBooking] = useState(false);

  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      setRows(await api.appointments(filters));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    api.doctors().then(setDoctors).catch(() => {});
  }, []);

  const set = (field) => (e) => setFilters({ ...filters, [field]: e.target.value });

  async function changeStatus(appt, status) {
    try {
      await api.updateAppointment(appt.id, { status });
      load();
    } catch (e) {
      alert(e.message);
    }
  }

  async function remove(appt) {
    if (!confirm(`Delete appointment for ${appt.patient_name}?`)) return;
    await api.deleteAppointment(appt.id);
    load();
  }

  return (
    <section className="panel">
      <div className="panel-head wrap">
        <div className="filters">
          <input type="date" value={filters.day} onChange={set("day")} aria-label="Day" />
          <select value={filters.doctor_id} onChange={set("doctor_id")} aria-label="Doctor">
            <option value="">All doctors</option>
            {doctors.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
          <select value={filters.status_filter} onChange={set("status_filter")} aria-label="Status">
            <option value="">Any status</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
          {filters.day && (
            <button className="btn btn-light" onClick={() => setFilters({ ...filters, day: "" })}>
              All dates
            </button>
          )}
        </div>
        <button className="btn" onClick={() => setBooking(true)}>
          + New appointment
        </button>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox error={error} onRetry={load} />
      ) : rows.length === 0 ? (
        <Empty text="No appointments match these filters." />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>When</th>
                <th>Patient</th>
                <th>Doctor</th>
                <th>Reason</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((a) => (
                <tr key={a.id}>
                  <td data-label="When">
                    <strong>{formatTime(a.start_time)}</strong>
                    <span className="muted"> {formatDate(a.start_time)} · {a.duration_min}m</span>
                  </td>
                  <td data-label="Patient">{a.patient_name}</td>
                  <td data-label="Doctor">
                    {a.doctor_name}
                    <span className="muted block">{a.specialty}</span>
                  </td>
                  <td data-label="Reason">{a.reason || "—"}</td>
                  <td data-label="Status">
                    <select
                      className={`status-select badge-${a.status}`}
                      value={a.status}
                      onChange={(e) => changeStatus(a, e.target.value)}
                    >
                      {Object.entries(STATUS_LABELS).map(([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="row-actions">
                    <button className="icon-btn danger" onClick={() => remove(a)} aria-label="Delete">
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {booking && (
        <Modal title="New appointment" onClose={() => setBooking(false)}>
          <BookingForm
            onCancel={() => setBooking(false)}
            onBooked={() => {
              setBooking(false);
              load();
            }}
          />
        </Modal>
      )}
    </section>
  );
}
