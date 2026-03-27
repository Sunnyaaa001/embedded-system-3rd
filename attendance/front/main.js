const API_URL = '/attendance/show'; 
async function refreshAttendanceDashboard() {
    const displayContainer = document.getElementById('attendance-display');
    try {
        const response = await fetch(API_URL);
        const result = await response.json();
        if (result.code !== 200) return;

        displayContainer.innerHTML = '';
        result.data.forEach(user => {
            const fullName = `${user.first_name} ${user.middle_name || ''} ${user.last_name}`.replace(/\s+/g, ' ').trim();
            const userCard = document.createElement('div');
            userCard.className = 'card mb-4 shadow-sm';
            
            const attendanceHtml = user.attendance
                .sort((a, b) => new Date(b.time) - new Date(a.time)) 
                .map(record => {
                    const isCheckIn = record.type === "0";
                    return `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge ${isCheckIn ? 'bg-success' : 'bg-danger'} me-2">${isCheckIn ? 'In' : 'Out'}</span>
                                <span class="text-muted small">${record.current_time}</span>
                            </div>
                        </li>`;
                }).join('');

            userCard.innerHTML = `
                <div class="card-header bg-primary text-white"><h5 class="mb-0">${fullName}</h5></div>
                <ul class="list-group list-group-flush">${attendanceHtml || '<li class="list-group-item">No records</li>'}</ul>`;
            displayContainer.appendChild(userCard);
        });
    } catch (e) { console.error(e); }
}

// Handler for Pico scan
document.getElementById('btn-scan').addEventListener('click', async () => {
    const btn = document.getElementById('btn-scan');
    const status = document.getElementById('scan-status');
    const uidInput = document.getElementById('reg-uid');
    const submitBtn = document.getElementById('btn-submit-user');

    btn.disabled = true;
    status.innerText = "Waiting for card swipe...";
    status.className = "form-text text-primary fw-bold";

    try {
        const response = await fetch(`/uid/info`);
        const result = await response.json();

        if (result.code === 200) {
            uidInput.value = result.data;
            status.innerText = "Success: Card detected";
            status.className = "form-text text-success";
            submitBtn.disabled = false;
        } else {
            status.innerText = "Error: Timeout";
            status.className = "form-text text-danger";
        }
    } catch (error) {
        status.innerText = "Error: Connection to Pico failed";
        status.className = "form-text text-danger";
    } finally {
        btn.disabled = false;
    }
});

// Post new user to PC Backend
document.getElementById('addUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const userData = {
        uid: document.getElementById('reg-uid').value,
        first_name: document.getElementById('reg-first-name').value,
        last_name: document.getElementById('reg-last-name').value
    };

    try {
        const response = await fetch('/insert/user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });
        if (response.ok) {
            alert("Registered successfully");
            location.reload();
        }
    } catch (error) {
        alert("Server error");
    }
});

document.addEventListener('DOMContentLoaded', refreshAttendanceDashboard);
setInterval(refreshAttendanceDashboard, 15000);