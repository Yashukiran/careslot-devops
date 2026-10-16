import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import Modal from "../components/Modal.jsx";
import { Empty, ErrorBox, Loading } from "../components/States.jsx";
import { initials } from "../utils.js";

export default function Doctors() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      setDoctors(await api.doctors());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function toggle(d) {
    await api.updateDoctor(d.id, { active: !d.active });
    load();
  }

  async function remove(d) {
    if (!confirm(`Remove ${d.name}? All their appointments will be deleted.`)) return;
    await api.deleteDoctor(d.id);
    load();
  }

  if (loading) return <Loading />;
  if (error) return <ErrorBox error={error} onRetry={load} />;

  return (
    <div className="stack">
      <div className="panel-head">
        <p className="muted">{doctors.filter((d) => d.active).length} of {doctors.length} doctors taking appointments</p>
        <button className="btn" onClick={() => setAdding(true)}>
          + Add doctor
        </button>
      </div>

      {doctors.length === 0 ? (
        <Empty text="No doctors added yet." />
      ) : (
        <section className="doc-grid">
          {doctors.map((d) => (
            <div key={d.id} className={`card doc-card ${d.active ? "" : "inactive"}`}>
              <span className="avatar large">{initials(d.name)}</span>
              <strong>{d.name}</strong>
              <span className="muted">{d.specialty}</span>
              <span className="pill pill-grey">Room {d.room || "—"}</span>
              <div className="doc-actions">
                <button className="btn btn-light btn-small" onClick={() => toggle(d)}>
                  {d.active ? "Mark off duty" : "Mark on duty"}
                </button>
                <button className="icon-btn danger" onClick={() => remove(d)} aria-label="Delete">
                  🗑
                </button>
              </div>
            </div>
          ))}
        </section>
      )}

      {adding && (
        <Modal title="Add doctor" onClose={() => setAdding(false)}>
          <DoctorForm
            onCancel={() => setAdding(false)}
            onSaved={() => {
              setAdding(false);
              load();
            }}
          />
        </Modal>
      )}
    </div>
  );
}

function DoctorForm({ onSaved, onCancel }) {
  const [form, setForm] = useState({ name: "Dr. ", specialty: "", room: "" });
  const [error, setError] = useState("");
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    try {
      await api.createDoctor(form);
      onSaved();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <label>
        Name
        <input required minLength={2} value={form.name} onChange={set("name")} />
      </label>
      <div className="form-row">
        <label>
          Specialty
          <input required placeholder="e.g. Cardiology" value={form.specialty} onChange={set("specialty")} />
        </label>
        <label>
          Room
          <input placeholder="101" value={form.room} onChange={set("room")} />
        </label>
      </div>
      {error && <p className="form-error">{error}</p>}
      <div className="form-actions">
        <button type="button" className="btn btn-light" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn">Add doctor</button>
      </div>
    </form>
  );
}
