/**
 * mBot IoT Gateway - Frontend Application
 * Real-time data visualization and control
 */

// Configuration
const API_BASE_URL = 'http://localhost:5000/api';
const UPDATE_INTERVAL = 1000; // 1 second
const MAX_DATA_POINTS = 100;

// Global state
let charts = {};
let updateTimer = null;
let dataBuffer = [];

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
    console.log('mBot IoT Gateway - Initializing...');
    initializeCharts();
    setupEventListeners();
    startDataUpdates();
    checkStatus();
    loadStatistics();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startExperiment);
    document.getElementById('exportBtn').addEventListener('click', exportData);
}

// Initialize all charts
function initializeCharts() {
    // PWM Chart
    charts.pwm = new Chart(document.getElementById('pwmChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'PWM Left',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'PWM Right',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: getChartOptions('PWM Value')
    });

    // Speed Chart
    charts.speed = new Chart(document.getElementById('speedChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Speed 1',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Speed 2',
                    data: [],
                    borderColor: 'rgb(153, 102, 255)',
                    backgroundColor: 'rgba(153, 102, 255, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: getChartOptions('Speed (units/s)')
    });

    // Angle Chart
    charts.angle = new Chart(document.getElementById('angleChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Angle X',
                    data: [],
                    borderColor: 'rgb(255, 159, 64)',
                    backgroundColor: 'rgba(255, 159, 64, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: getChartOptions('Angle (degrees)')
    });

    // Gyro Chart
    charts.gyro = new Chart(document.getElementById('gyroChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Gyro Y',
                    data: [],
                    borderColor: 'rgb(201, 203, 207)',
                    backgroundColor: 'rgba(201, 203, 207, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: getChartOptions('Angular Velocity (°/s)')
    });

    console.log('Charts initialized');
}

// Get common chart options
function getChartOptions(yAxisLabel) {
    return {
        responsive: true,
        maintainAspectRatio: true,
        animation: {
            duration: 0 // Disable animations for real-time updates
        },
        scales: {
            x: {
                display: true,
                title: {
                    display: true,
                    text: 'Time (s)'
                }
            },
            y: {
                display: true,
                title: {
                    display: true,
                    text: yAxisLabel
                }
            }
        },
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        }
    };
}

// Update charts with new data
function updateCharts(data) {
    const timeLabel = data.time_s.toFixed(2);

    // Update PWM chart
    updateChart(charts.pwm, timeLabel, [data.pwm_left, data.pwm_right]);

    // Update Speed chart
    updateChart(charts.speed, timeLabel, [data.speed_1, data.speed_2]);

    // Update Angle chart
    updateChart(charts.angle, timeLabel, [data.angle_x]);

    // Update Gyro chart
    updateChart(charts.gyro, timeLabel, [data.gyro_y]);
}

// Helper function to update a single chart
function updateChart(chart, label, dataPoints) {
    chart.data.labels.push(label);

    dataPoints.forEach((value, index) => {
        chart.data.datasets[index].data.push(value);
    });

    // Keep only last MAX_DATA_POINTS
    if (chart.data.labels.length > MAX_DATA_POINTS) {
        chart.data.labels.shift();
        chart.data.datasets.forEach(dataset => {
            dataset.data.shift();
        });
    }

    chart.update('none'); // Update without animation
}

// Update dashboard values
function updateDashboard(data) {
    document.getElementById('pwmLeft').textContent = data.pwm_left;
    document.getElementById('pwmRight').textContent = data.pwm_right;
    document.getElementById('speed1').textContent = data.speed_1.toFixed(2);
    document.getElementById('speed2').textContent = data.speed_2.toFixed(2);
    document.getElementById('angleX').textContent = data.angle_x.toFixed(2);
    document.getElementById('gyroY').textContent = data.gyro_y.toFixed(2);
    document.getElementById('phase').textContent = getPhaseLabel(data.phase);
    document.getElementById('timeS').textContent = data.time_s.toFixed(2);
    document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
}

// Get phase label
function getPhaseLabel(phase) {
    const phases = {
        0: 'Idle',
        1: 'Motor Test',
        2: 'Balance Test',
        3: 'Complete'
    };
    return phases[phase] || `Phase ${phase}`;
}

// Check system status
async function checkStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        const data = await response.json();

        const statusElement = document.getElementById('connectionStatus');
        if (data.serial_connected) {
            statusElement.textContent = 'Connected';
            statusElement.className = 'status-value status-connected';
        } else {
            statusElement.textContent = 'Disconnected';
            statusElement.className = 'status-value status-disconnected';
        }

        document.getElementById('dataPoints').textContent = data.buffer_size || 0;

    } catch (error) {
        console.error('Error checking status:', error);
        document.getElementById('connectionStatus').textContent = 'Error';
        document.getElementById('connectionStatus').className = 'status-value status-disconnected';
    }
}

// Start data updates
function startDataUpdates() {
    if (updateTimer) {
        clearInterval(updateTimer);
    }

    updateTimer = setInterval(async () => {
        await fetchLatestData();
        await checkStatus();
    }, UPDATE_INTERVAL);

    console.log('Data updates started');
}

// Fetch latest data from API
async function fetchLatestData() {
    try {
        const response = await fetch(`${API_BASE_URL}/data/buffer?limit=${MAX_DATA_POINTS}`);
        const result = await response.json();

        if (result.success && result.data.length > 0) {
            const newData = result.data;

            // Update only with new data points
            if (dataBuffer.length === 0 ||
                newData[newData.length - 1].time_s !== dataBuffer[dataBuffer.length - 1]?.time_s) {

                dataBuffer = newData;

                // Clear charts if this is fresh data
                if (newData[0].time_s < 1) {
                    clearCharts();
                }

                // Update with all data points
                newData.forEach(data => {
                    updateCharts(data);
                });

                // Update dashboard with latest data
                updateDashboard(newData[newData.length - 1]);
            }
        }

    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Clear all charts
function clearCharts() {
    Object.values(charts).forEach(chart => {
        chart.data.labels = [];
        chart.data.datasets.forEach(dataset => {
            dataset.data = [];
        });
        chart.update();
    });
    console.log('Charts cleared');
}

// Start experiment
async function startExperiment() {
    try {
        const response = await fetch(`${API_BASE_URL}/control/start`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('START command sent to Arduino!');
            clearCharts();
            dataBuffer = [];
        } else {
            alert('Failed to start experiment: ' + result.message);
        }

    } catch (error) {
        console.error('Error starting experiment:', error);
        alert('Error: ' + error.message);
    }
}

// Export data as CSV
async function exportData() {
    try {
        const response = await fetch(`${API_BASE_URL}/data/export`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `mbot_data_${new Date().toISOString()}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            alert('Data exported successfully!');
        } else {
            alert('Failed to export data');
        }

    } catch (error) {
        console.error('Error exporting data:', error);
        alert('Error: ' + error.message);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/statistics`);
        const result = await response.json();

        if (result.success) {
            const stats = result.statistics;
            const statsHtml = `
                <div class="stat-item">
                    <span class="stat-label">Total Measurements</span>
                    <span class="stat-value">${stats.total_measurements || 0}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">First Measurement</span>
                    <span class="stat-value">${stats.first_measurement ? new Date(stats.first_measurement).toLocaleString() : 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Last Measurement</span>
                    <span class="stat-value">${stats.last_measurement ? new Date(stats.last_measurement).toLocaleString() : 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Angle (1h)</span>
                    <span class="stat-value">${stats.avg_angle_1h ? stats.avg_angle_1h.toFixed(2) + '°' : 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Speed 1 (1h)</span>
                    <span class="stat-value">${stats.avg_speed_1_1h ? stats.avg_speed_1_1h.toFixed(2) : 'N/A'}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Speed 2 (1h)</span>
                    <span class="stat-value">${stats.avg_speed_2_1h ? stats.avg_speed_2_1h.toFixed(2) : 'N/A'}</span>
                </div>
            `;

            document.getElementById('statistics').innerHTML = statsHtml;
        }

    } catch (error) {
        console.error('Error loading statistics:', error);
        document.getElementById('statistics').innerHTML = '<p class="loading">Failed to load statistics</p>';
    }
}

// Refresh statistics every 10 seconds
setInterval(loadStatistics, 10000);

console.log('mBot IoT Gateway - Ready!');
