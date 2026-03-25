// Configuration: Point this to your actual PC backend URL
const API_URL = 'http://127.0.0.1:8080/attendance/show'; 

/**
 * Main function to fetch and render data
 */
async function refreshAttendanceDashboard() {
    const displayContainer = document.getElementById('attendance-display');
    
    try {
        const response = await fetch(API_URL);
        const result = await response.json();

        if (result.code !== 200) {
            console.error("Backend returned error code:", result.code);
            return;
        }

        // Clear existing content before re-rendering
        displayContainer.innerHTML = '';

        // Iterate through users
        result.data.forEach(user => {
            // Construct Full Name (handling potential null middle_name)
            const fullName = `${user.first_name} ${user.middle_name || ''} ${user.last_name}`.replace(/\s+/g, ' ').trim();
            
            // Create the card for the user
            const userCard = document.createElement('div');
            userCard.className = 'card mb-4 shadow-sm';

            // Generate HTML for the attendance list
            // Sorting by time descending (newest first) is recommended
            const attendanceHtml = user.attendance
                .sort((a, b) => new Date(b.time) - new Date(a.time)) 
                .map(record => {
                    const isCheckIn = record.type === "0";
                    const badgeClass = isCheckIn ? 'bg-success' : 'bg-danger';
                    const statusLabel = isCheckIn ? 'Check-in' : 'Check-out';
                    
                    return `
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <span class="badge ${badgeClass} me-2">${statusLabel}</span>
                                <span class="text-muted small">${record.time}</span>
                            </div>
                        </li>`;
                }).join('');

            userCard.innerHTML = `
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0">User: ${fullName}</h5>
                </div>
                <ul class="list-group list-group-flush">
                    ${attendanceHtml || '<li class="list-group-item text-center text-muted">No records found</li>'}
                </ul>
            `;

            displayContainer.appendChild(userCard);
        });

    } catch (error) {
        console.error("Connection failed:", error);
        displayContainer.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> Could not connect to the backend server at ${API_URL}.
            </div>`;
    }
}

// Initial load
document.addEventListener('DOMContentLoaded', refreshAttendanceDashboard);

// Auto-refresh every 15 seconds to keep data live
setInterval(refreshAttendanceDashboard, 15000);