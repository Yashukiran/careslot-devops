// all calls go to a relative /api path so the same build works behind
// the vite proxy, nginx in docker compose, and the k8s ingress

async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    if (data?.detail) {
      message = Array.isArray(data.detail)
        ? data.detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(", ")
        : data.detail;
    }
    throw new Error(message);
  }
  return data;
}

const query = (params) => {
  const clean = Object.fromEntries(Object.entries(params).filter(([, v]) => v !== "" && v != null));
  const qs = new URLSearchParams(clean).toString();
  return qs ? `?${qs}` : "";
};

export const api = {
  stats: () => request("/stats"),
  info: () => request("/info"),
  activity: (limit = 8) => request(`/activity?limit=${limit}`),

  doctors: (params = {}) => request(`/doctors${query(params)}`),
  createDoctor: (body) => request("/doctors", { method: "POST", body: JSON.stringify(body) }),
  updateDoctor: (id, body) => request(`/doctors/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteDoctor: (id) => request(`/doctors/${id}`, { method: "DELETE" }),

  patients: (params = {}) => request(`/patients${query(params)}`),
  createPatient: (body) => request("/patients", { method: "POST", body: JSON.stringify(body) }),
  updatePatient: (id, body) => request(`/patients/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deletePatient: (id) => request(`/patients/${id}`, { method: "DELETE" }),

  appointments: (params = {}) => request(`/appointments${query(params)}`),
  createAppointment: (body) => request("/appointments", { method: "POST", body: JSON.stringify(body) }),
  updateAppointment: (id, body) => request(`/appointments/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteAppointment: (id) => request(`/appointments/${id}`, { method: "DELETE" }),
};
