import { useCallback, useEffect, useState } from "react";
import { api } from "../api.js";
import Modal from "../components/Modal.jsx";
import { Empty, ErrorBox, Loading } from "../components/States.jsx";
import { initials } from "../utils.js";

const EMPTY = { full_name: "", phone: "", age: "", notes: "" };

export default function Patients() {
  const [search, setSearch] = useState("");
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null); // null = closed, {} = new, patient = edit

  const load = useCallback(async () => {
    setError("");
    try {
      setRows(await api.patients({ q: search }));
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search]);

  useEffect(() => {
    const t = setTimeout(load, 250); // small debounce while typing
    return () => clearTimeout(t);
  }, [load]);

  async function remove(p) {
    if (!confirm(`Remove ${p.full_name}? Their appointments will be deleted too.`)) return;
    await api.deletePatient(p.id);
    load();
  }

  return (
    <section className="panel">
      <div className="panel-head wrap">
        <input
          className="search"
          placeholder="Search by name or phone…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button className="btn" onClick={() => setEditing({})}>
          + Add patient
        </button>
      </div>

      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorBox error={error} onRetry={load} />
      ) : rows.length === 0 ? (
        <Empty text={search ? "No patients match that search." : "No patients registered yet."} />
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Phone</th>
                <th>Age</th>
                <th>Notes</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td data-label="Name">
                    <span className="person">
                      <span className="avatar small">{initials(p.full_name)}</span>
                      {p.full_name}
                    </span>
                  </td>
                  <td data-label="Phone">{p.phone}</td>
                  <td data-label="Age">{p.age ?? "—"}</td>
                  <td data-label="Notes" className="muted">
                    {p.notes || "—"}
                  </td>
                  <td className="row-actions">
                    <button className="icon-btn" onClick={() => setEditing(p)} aria-label="Edit">
                      ✎
                    </button>
                    <button className="icon-btn danger" onClick={() => remove(p)} aria-label="Delete">
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editing && (
        <Modal title={editing.id ? "Edit patient" : "Add patient"} onClose={() => setEditing(null)}>
          <PatientForm
            patient={editing}
            onCancel={() => setEditing(null)}
            onSaved={() => {
              setEditing(null);
              load();
            }}
          />
        </Modal>
      )}
    </section>
  );
}

function PatientForm({ patient, onSaved, onCancel }) {
  const [form, setForm] = useState({ ...EMPTY, ...patient, age: patient.age ?? "" });
  const [error, setError] = useState("");
  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    const body = {
      full_name: form.full_name,
      phone: form.phone,
      age: form.age === "" ? null : Number(form.age),
      notes: form.notes,
    };
    try {
      if (patient.id) await api.updatePatient(patient.id, body);
      else await api.createPatient(body);
      onSaved();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <form className="form" onSubmit={submit}>
      <label>
        Full name
        <input required minLength={2} value={form.full_name} onChange={set("full_name")} />
      </label>
      <div className="form-row">
        <label>
          Phone
          <input required placeholder="+91 98450 11223" value={form.phone} onChange={set("phone")} />
        </label>
        <label>
          Age
          <input type="number" min="0" max="120" value={form.age} onChange={set("age")} />
        </label>
      </div>
      <label>
        Notes
        <textarea rows="3" placeholder="Allergies, conditions…" value={form.notes} onChange={set("notes")} />
      </label>
      {error && <p className="form-error">{error}</p>}
      <div className="form-actions">
        <button type="button" className="btn btn-light" onClick={onCancel}>
          Cancel
        </button>
        <button className="btn">Save</button>
      </div>
    </form>
  );
}
