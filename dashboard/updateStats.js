// Define API URLs for our services
// Note: Using relative URLs so it works regardless of host
const PROCESSING_STATS_URL = `/processing-api/stats`;
const ANALYZER_API_URL = {
    stats: `/analyzer-api/stats`,
    dronePosition: `/analyzer-api/drone/position`,
    targetAcquisition: `/analyzer-api/drone/target-acquisition`
};

// Chart reference for updating data visualization
let dataChart = null;

// This function makes API requests with error handling
const makeRequest = (url, callback) => {
    fetch(url)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then((result) => {
        console.log(`Received data from ${url}:`, result);
        callback(result);
        updateStatusIndicator(true);
    })
    .catch((error) => {
        console.error(`Error fetching data from ${url}:`, error);
        updateErrorMessages(error.message);
        updateStatusIndicator(false);
    });
};

// Update content of an element with JSON data
const updateCodeDiv = (result, elemId) => {
    const element = document.getElementById(elemId);
    if (element) {
        element.innerText = JSON.stringify(result, null, 2);
    }
};

// Get formatted current date/time
const getLocaleDateStr = () => (new Date()).toLocaleString();

// Get a random event from the analyzer service
const getRandomEvent = () => {
    // Generate random index between 0-5 (assuming we have some events)
    const randomIndex = Math.floor(Math.random() * 5);

    // Randomly choose between drone position and target acquisition
    if (Math.random() > 0.5) {
        makeRequest(`${ANALYZER_API_URL.dronePosition}?index=${randomIndex}`, (result) => {
            updateCodeDiv(result, "event-location");
        });
    } else {
        makeRequest(`${ANALYZER_API_URL.targetAcquisition}?index=${randomIndex}`, (result) => {
            updateCodeDiv(result, "event-location");
        });
    }
};

// Main function to get all stats
const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr();

    // Get processing service stats
    makeRequest(PROCESSING_STATS_URL, (result) => {
        updateCodeDiv(result, "processing-stats");
        updateChart(result);
    });

    // Get analyzer service stats
    makeRequest(ANALYZER_API_URL.stats, (result) => {
        updateCodeDiv(result, "analyzer-stats");
    });

    // Get a random event
    getRandomEvent();
};

// Update system status indicator
const updateStatusIndicator = (isOnline) => {
    const statusCircle = document.getElementById("status-circle");
    const statusText = document.getElementById("status-text");

    if (statusCircle && statusText) {
        statusCircle.className = isOnline ? "online" : "offline";
        statusText.innerText = isOnline ? "System Online" : "System Offline";
    }
};

// Handle and display error messages
const updateErrorMessages = (message) => {
    const id = Date.now();
    console.log("Creating error message:", id);

    const messagesContainer = document.getElementById("messages");
    if (!messagesContainer) return;

    const msg = document.createElement("div");
    msg.id = `error-${id}`;
    msg.innerHTML = `<p>Error at ${getLocaleDateStr()}:</p><code>${message}</code>`;

    messagesContainer.style.display = "block";
    messagesContainer.prepend(msg);

    // Auto-remove error message after 7 seconds
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`);
        if (elem) {
            elem.remove();

            // Hide the container if no more messages
            if (messagesContainer.children.length === 0) {
                messagesContainer.style.display = "none";
            }
        }
    }, 7000);
};

// Initialize the data chart
const initializeChart = () => {
    const ctx = document.getElementById('data-chart').getContext('2d');

    dataChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Initial'],
            datasets: [
                {
                    label: 'Drone Positions',
                    data: [0],
                    borderColor: '#0056b3',
                    backgroundColor: 'rgba(0, 86, 179, 0.1)',
                          tension: 0.4,
                          fill: true
                },
                {
                    label: 'Target Acquisitions',
                    data: [0],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                          tension: 0.4,
                          fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true
                }
            },
            animation: {
                duration: 750
            }
        }
    });
};

// Update chart with new data
const updateChart = (data) => {
    if (!dataChart) return;

    // Get timestamps for labels
    const timestamp = data.last_updated ? new Date(data.last_updated).toLocaleTimeString() : getLocaleDateStr();

    // Only keep the last 10 data points for better visualization
    if (dataChart.data.labels.length > 9) {
        dataChart.data.labels.shift();
        dataChart.data.datasets[0].data.shift();
        dataChart.data.datasets[1].data.shift();
    }

    // Add new data
    dataChart.data.labels.push(timestamp);

    // Use appropriate data from the response
    const dronePositions = data.num_drone_positions || data.num_drone_position || 0;
    const targetAcquisitions = data.num_target_acquisitions || data.num_target_acquisition || 0;

    dataChart.data.datasets[0].data.push(dronePositions);
    dataChart.data.datasets[1].data.push(targetAcquisitions);

    // Update the chart
    dataChart.update();
};

// Initial setup function
const setup = () => {
    // Initialize the chart
    initializeChart();

    // Get initial stats
    getStats();

    // Set up auto-refresh every 3 seconds
    setInterval(getStats, 3000);
};

// Wait for DOM to be fully loaded before running setup
document.addEventListener('DOMContentLoaded', setup);
