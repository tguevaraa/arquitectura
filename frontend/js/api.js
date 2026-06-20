const API_URL = "http://127.0.0.1:8000";

const api = {
    async register(email, password, full_name, role = "patient") {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password, full_name, role })
        });
        return response.json();
    },

    async login(email, password) {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });
        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem("token", data.access_token);
        }
        return data;
    },

    async getDoctors() {
        const response = await fetch(`${API_URL}/doctors/`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return response.json();
    },

    async bookAppointment(doctorId, datetime, notes) {
        const response = await fetch(`${API_URL}/appointments/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ doctor_id: doctorId, appointment_datetime: datetime, notes })
        });
        return response.json();
    },

    async bookAppointmentForPatient(doctorId, datetime, notes, patientId) {
        const body = { doctor_id: parseInt(doctorId), appointment_datetime: datetime, notes };
        if (patientId) body.patient_id = parseInt(patientId);
        const response = await fetch(`${API_URL}/appointments/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(body)
        });
        return response.json();
    },

    async getAppointments() {
        const response = await fetch(`${API_URL}/appointments/`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return response.json();
    },

    async updateAppointment(appointmentId, status, notes) {
        const body = {};
        if (status !== null && status !== undefined) body.status = status;
        if (notes  !== null && notes  !== undefined) body.notes  = notes;
        const response = await fetch(`${API_URL}/appointments/${appointmentId}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(body)
        });
        return response.json();
    },

    async patientLogin(email, password) {
        const response = await fetch(`${API_URL}/auth/patient-login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });
        return response.json();
    },

    async verifyCode(email, code) {
        const response = await fetch(`${API_URL}/auth/verify-code`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, code })
        });
        const data = await response.json();
        if (data.access_token) {
            localStorage.setItem("token", data.access_token);
        }
        return data;
    },

    async rescheduleAppointment(appointmentId, newDatetime) {
        const response = await fetch(`${API_URL}/appointments/${appointmentId}/reschedule`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ new_datetime: newDatetime })
        });
        return response.json();
    },

    // ── Admin ────────────────────────────────────
    async getUsers() {
        const r = await fetch(`${API_URL}/admin/users`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return r.json();
    },

    async updateUser(userId, data) {
        const r = await fetch(`${API_URL}/admin/users/${userId}`, {
            method: "PATCH",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(data)
        });
        return r.json();
    },

    async resetPassword(userId, newPassword) {
        const r = await fetch(`${API_URL}/admin/users/${userId}/reset-password`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ new_password: newPassword })
        });
        return r.json();
    },

    async createDoctor(data) {
        const r = await fetch(`${API_URL}/admin/doctors`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(data)
        });
        return r.json();
    },

    patientLogout() {
        localStorage.removeItem("token");
        window.location.href = "paciente.html";
    },

    logout() {
        localStorage.removeItem("token");
        window.location.href = "inicio.html";
    },

    // ── Pacientes ─────────────────────────────────
    async getPatients() {
        const r = await fetch(`${API_URL}/patients/`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return r.json();
    },

    async createPatient(data) {
        const r = await fetch(`${API_URL}/patients/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(data)
        });
        return r.json();
    },

    async getPatient(patientId) {
        const r = await fetch(`${API_URL}/patients/${patientId}`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return r.json();
    },

    async updatePatient(patientId, data) {
        const r = await fetch(`${API_URL}/patients/${patientId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(data)
        });
        return r.json();
    },

    // ── Historia Clínica ──────────────────────────
    async getConsultas(patientId) {
        const r = await fetch(`${API_URL}/patients/${patientId}/consultas`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return r.json();
    },

    async createConsulta(patientId, data) {
        const r = await fetch(`${API_URL}/patients/${patientId}/consultas`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify(data)
        });
        return r.json();
    },

    // ── Documentos ────────────────────────────────
    async getDocumentos(patientId) {
        const r = await fetch(`${API_URL}/patients/${patientId}/documentos`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return r.json();
    },

    async subirDocumento(patientId, consultaId, tipo, archivo) {
        const formData = new FormData();
        formData.append("tipo", tipo);
        formData.append("archivo", archivo);
        const r = await fetch(`${API_URL}/patients/${patientId}/consultas/${consultaId}/documentos`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` },
            body: formData
        });
        return r.json();
    }
};

