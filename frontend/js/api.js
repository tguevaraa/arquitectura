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

    async getAppointments() {
        const response = await fetch(`${API_URL}/appointments/`, {
            headers: { "Authorization": `Bearer ${localStorage.getItem("token")}` }
        });
        return response.json();
    },

    logout() {
        localStorage.removeItem("token");
        window.location.href = "index.html";
    }
};

