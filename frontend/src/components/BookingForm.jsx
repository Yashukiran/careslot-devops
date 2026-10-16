import { useEffect, useState } from "react";
import { api } from "../api.js";
import { todayISO } from "../utils.js";

export default function BookingForm({ onBooked, onCancel }) {
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [form, setForm] = useState({
    patient_id: "",
    doctor_id: "",
    date: todayISO(),
    time: "10:00",
    duration_min: 20,
    reason: "",
    priority: "routine",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    Promise.all([api.doctors({ active_only: true }), api.patients()])
      .then(([d, p]) => {
        setDoctors(d);
        setPatients(p);
      })
      .catch((e) => setError(e.message));
  }, []);

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      // local date + time from the browser, sent with its offset
      const start = new Date(`${form.date}T${form.time}`);
      const appt = await api.createAppointment({
        patient_id: Number(form.patient_id),
        doctor_id: Number(form.doctor_id),
        start_time: start.toISOString(),
        duration_min: Number(form.duration_min),
        reason: form.reason,
        priority: form.priority,
      });
      onBooked(appt);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <label>
        Patient
        <select required value={form.patient_id} onChange={set("patient_id")}>
          <option value="">Select patient…</option>
          {patients.map((p) => (
            <option key={p.id} value={p.id}>
              {p.full_name} · {p.phone}
            </option>
          ))}
        </select>
      </label>
      <label>
        Doctor
        <select required value={form.doctor_id} onChange={set("doctor_id")}>
          <option value="">Select doctor…</option>
          {doctors.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} — {d.specialty}
            </option>
          ))}
        </select>
      </label>
      <div className="form-row">
        <label>
          Date
          <input type="date" required value={form.date} onChange={set("date")} />
        </label>
        <label>
          Time
          <input type="time" required step="300" value={form.time} onChange={set("time")} />
        </label>
        <label>
          Minutes
          <select value={form.duration_min} onChange={set("duration_min")}>
            {[10, 15, 20, 30, 45, 60].map((m) => (
              <option key={m}>{m}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="form-row">
        <label className="grow">
          Reason for visit
          <input placeholder="e.g. fever, follow-up" maxLength={200} value={form.reason} onChange={set("reason")} />
        </label>
        <label>
          Priority
          <select value={form.priority} onChange={set("priority")}>
            <option value="routine">Routine</option>
            <option value="urgent">Urgent</option>
          </select>
        </label>
      </div>

      {error && <p className="form-error">{error}</p>}

      <div className="form-actions">
        <button type="button" className="btn btn-light" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn" disabled={saving}>
          {saving ? "Booking…" : "Book appointment"}
        </button>
      </div>
    </form>
  );
}
