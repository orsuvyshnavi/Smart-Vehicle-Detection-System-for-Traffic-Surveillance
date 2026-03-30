// Global variables
let isStreaming = false;
let currentSource = 'camera';
let currentWeather = 'normal';
let statsInterval;
let videoInterval;

// Chart instances
let vehicleChart = null;
let performanceChart = null;
let weatherChart = null;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    setupEventListeners();
    updateStats();
});

function setupEventListeners() {
    // Video source selection
    document.getElementById('videoSource').addEventListener('change', function(e) {
        currentSource = e.target.value;
        if (isStreaming) {
            stopStreaming();
            startStreaming();
        }
    });

    // Weather condition buttons
    document.querySelectorAll('.weather-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('.weather-btn').forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            currentWeather = this.dataset.weather;
            
            if (isStreaming) {
                stopStreaming();
                startStreaming();
            }
            
            // Update weather display
            document.getElementById('currentWeather').textContent = getWeatherDisplayName(currentWeather);
        });
    });

    // Control buttons
    document.getElementById('startBtn').addEventListener('click', startStreaming);
    document.getElementById('stopBtn').addEventListener('click', stopStreaming);
    document.getElementById('resetBtn').addEventListener('click', resetStats);

    // Export buttons
    document.getElementById('exportJSON').addEventListener('click', exportJSON);
    document.getElementById('exportCSV').addEventListener('click', exportCSV);
    document.getElementById('generateReport').addEventListener('click', generateReport);
}

function startStreaming() {
    if (isStreaming) return;
    
    isStreaming = true;
    document.getElementById('status').textContent = 'Active';
    document.getElementById('status').className = 'text-green-400';
    
    // Start video feed
    const videoFeed = document.getElementById('videoFeed');
    videoFeed.src = `/video_feed/${currentSource}/${currentWeather}`;
    
    // Start stats updates
    statsInterval = setInterval(updateStats, 1000);
}

function stopStreaming() {
    if (!isStreaming) return;
    
    isStreaming = false;
    document.getElementById('status').textContent = 'Stopped';
    document.getElementById('status').className = 'text-red-400';
    
    // Stop video feed
    document.getElementById('videoFeed').src = '';
    
    // Clear intervals
    if (statsInterval) {
        clearInterval(statsInterval);
    }
}

function resetStats() {
    fetch('/reset_stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'reset_complete') {
                // Reset UI
                document.getElementById('totalVehicles').textContent = '0';
                document.getElementById('currentFPS').textContent = '0';
                document.getElementById('avgConfidence').textContent = '0%';
                document.getElementById('processingTime').textContent = '0ms';
                
                // Reset charts
                initializeCharts();
                
                showNotification('Statistics reset successfully', 'success');
            }
        })
        .catch(error => {
            console.error('Error resetting stats:', error);
            showNotification('Error resetting statistics', 'error');
        });
}

function updateStats() {
    fetch('/stats')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'active') {
                // Update statistics display
                document.getElementById('totalVehicles').textContent = data.total_vehicles;
                document.getElementById('currentFPS').textContent = data.avg_fps.toFixed(1);
                document.getElementById('avgConfidence').textContent = (data.avg_confidence * 100).toFixed(1) + '%';
                document.getElementById('processingTime').textContent = (data.avg_processing_time * 1000).toFixed(1) + 'ms';
                
                // Update charts
                updateVehicleChart(data.vehicle_types);
                updatePerformanceChart(data.avg_fps, data.avg_processing_time);
                updateWeatherChart(data.weather_distribution);
            }
        })
        .catch(error => {
            console.error('Error fetching stats:', error);
        });
}

function initializeCharts() {
    // Vehicle Type Distribution Chart
    const vehicleCtx = document.getElementById('vehicleChart');
    if (vehicleCtx) {
        vehicleChart = Plotly.newPlot('vehicleChart', [{
            values: [0],
            labels: ['No Data'],
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#6B7280']
            },
            textinfo: 'label+percent',
            textposition: 'outside'
        }], {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: 'white' },
            showlegend: false,
            margin: { t: 0, b: 0, l: 0, r: 0 }
        }, { displayModeBar: false });
    }

    // Performance Metrics Chart
    const performanceCtx = document.getElementById('performanceChart');
    if (performanceCtx) {
        performanceChart = Plotly.newPlot('performanceChart', [
            {
                x: [],
                y: [],
                name: 'FPS',
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#10B981', width: 3 },
                marker: { size: 6 }
            },
            {
                x: [],
                y: [],
                name: 'Processing Time (ms)',
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: '#F59E0B', width: 3 },
                marker: { size: 6 },
                yaxis: 'y2'
            }
        ], {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: 'white' },
            xaxis: {
                title: 'Time',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'white'
            },
            yaxis: {
                title: 'FPS',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'white'
            },
            yaxis2: {
                title: 'Processing Time (ms)',
                overlaying: 'y',
                side: 'right',
                color: 'white'
            },
            legend: {
                x: 0.02,
                y: 0.98,
                bgcolor: 'rgba(255,255,255,0.1)',
                bordercolor: 'white',
                borderwidth: 1
            },
            margin: { t: 20, b: 50, l: 50, r: 50 }
        }, { displayModeBar: false });
    }

    // Weather Impact Chart
    const weatherCtx = document.getElementById('weatherChart');
    if (weatherCtx) {
        weatherChart = Plotly.newPlot('weatherChart', [{
            x: ['Normal', 'Rain', 'Fog', 'Night', 'Snow'],
            y: [0, 0, 0, 0, 0],
            type: 'bar',
            marker: {
                color: ['#10B981', '#3B82F6', '#6B7280', '#1F2937', '#E5E7EB'],
                line: { color: 'white', width: 1 }
            }
        }], {
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: 'white' },
            xaxis: {
                title: 'Weather Condition',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'white'
            },
            yaxis: {
                title: 'Vehicle Count',
                gridcolor: 'rgba(255,255,255,0.1)',
                color: 'white'
            },
            margin: { t: 20, b: 50, l: 50, r: 20 }
        }, { displayModeBar: false });
    }
}

function updateVehicleChart(vehicleTypes) {
    if (!vehicleChart || !vehicleTypes) return;
    
    const labels = Object.keys(vehicleTypes);
    const values = Object.values(vehicleTypes);
    const colors = ['#10B981', '#3B82F6', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316'];
    
    const data = [{
        values: values,
        labels: labels,
        type: 'pie',
        hole: 0.4,
        marker: { colors: colors.slice(0, labels.length) },
        textinfo: 'label+percent',
        textposition: 'outside'
    }];
    
    Plotly.react('vehicleChart', data, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white' },
        showlegend: false,
        margin: { t: 0, b: 0, l: 0, r: 0 }
    });
}

function updatePerformanceChart(fps, processingTime) {
    if (!performanceChart) return;
    
    const timestamp = new Date().toLocaleTimeString();
    
    // Get current data
    const fpsData = document.getElementById('performanceChart').data[0];
    const timeData = document.getElementById('performanceChart').data[1];
    
    // Limit data points to last 20
    const maxPoints = 20;
    const newFpsX = [...fpsData.x, timestamp].slice(-maxPoints);
    const newFpsY = [...fpsData.y, fps].slice(-maxPoints);
    const newTimeX = [...timeData.x, timestamp].slice(-maxPoints);
    const newTimeY = [...timeData.y, processingTime * 1000].slice(-maxPoints);
    
    const data = [
        {
            x: newFpsX,
            y: newFpsY,
            name: 'FPS',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#10B981', width: 3 },
            marker: { size: 6 }
        },
        {
            x: newTimeX,
            y: newTimeY,
            name: 'Processing Time (ms)',
            type: 'scatter',
            mode: 'lines+markers',
            line: { color: '#F59E0B', width: 3 },
            marker: { size: 6 },
            yaxis: 'y2'
        }
    ];
    
    Plotly.react('performanceChart', data, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white' },
        xaxis: {
            title: 'Time',
            gridcolor: 'rgba(255,255,255,0.1)',
            color: 'white'
        },
        yaxis: {
            title: 'FPS',
            gridcolor: 'rgba(255,255,255,0.1)',
            color: 'white'
        },
        yaxis2: {
            title: 'Processing Time (ms)',
            overlaying: 'y',
            side: 'right',
            color: 'white'
        },
        legend: {
            x: 0.02,
            y: 0.98,
            bgcolor: 'rgba(255,255,255,0.1)',
            bordercolor: 'white',
            borderwidth: 1
        },
        margin: { t: 20, b: 50, l: 50, r: 50 }
    });
}

function updateWeatherChart(weatherDistribution) {
    if (!weatherChart || !weatherDistribution) return;
    
    const weatherNames = {
        'normal': 'Normal',
        'rain': 'Rain',
        'fog': 'Fog',
        'night': 'Night',
        'snow': 'Snow'
    };
    
    const labels = Object.keys(weatherDistribution).map(key => weatherNames[key] || key);
    const values = Object.values(weatherDistribution);
    
    const data = [{
        x: labels,
        y: values,
        type: 'bar',
        marker: {
            color: ['#10B981', '#3B82F6', '#6B7280', '#1F2937', '#E5E7EB'],
            line: { color: 'white', width: 1 }
        }
    }];
    
    Plotly.react('weatherChart', data, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: 'white' },
        xaxis: {
            title: 'Weather Condition',
            gridcolor: 'rgba(255,255,255,0.1)',
            color: 'white'
        },
        yaxis: {
            title: 'Vehicle Count',
            gridcolor: 'rgba(255,255,255,0.1)',
            color: 'white'
        },
        margin: { t: 20, b: 50, l: 50, r: 20 }
    });
}

function exportJSON() {
    fetch('/export_data')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vehicle_detection_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('JSON data exported successfully', 'success');
        })
        .catch(error => {
            console.error('Error exporting JSON:', error);
            showNotification('Error exporting JSON data', 'error');
        });
}

function exportCSV() {
    fetch('/export_data')
        .then(response => response.json())
        .then(data => {
            let csvContent = 'Timestamp,Total Vehicles,Average FPS,Average Confidence,Processing Time\n';
            csvContent += `${data.timestamp},${data.total_vehicles},${data.performance_metrics.avg_fps.toFixed(2)},${data.performance_metrics.avg_confidence.toFixed(4)},${data.performance_metrics.avg_processing_time.toFixed(4)}\n`;
            
            // Add vehicle types
            csvContent += '\nVehicle Types,Count\n';
            for (const [type, count] of Object.entries(data.vehicle_types)) {
                csvContent += `${type},${count}\n`;
            }
            
            // Add weather conditions
            csvContent += '\nWeather Conditions,Count\n';
            for (const [condition, count] of Object.entries(data.weather_conditions)) {
                csvContent += `${condition},${count}\n`;
            }
            
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vehicle_detection_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('CSV data exported successfully', 'success');
        })
        .catch(error => {
            console.error('Error exporting CSV:', error);
            showNotification('Error exporting CSV data', 'error');
        });
}

function generateReport() {
    fetch('/export_data')
        .then(response => response.json())
        .then(data => {
            // Create a simple HTML report
            const reportHTML = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Vehicle Detection Report</title>
                    <style>
                        body { font-family: Arial, sans-serif; margin: 40px; }
                        .header { text-align: center; margin-bottom: 30px; }
                        .section { margin-bottom: 20px; }
                        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f0f0f0; border-radius: 5px; }
                        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                        th { background-color: #f2f2f2; }
                    </style>
                </head>
                <body>
                    <div class="header">
                        <h1>Vehicle Recognition System Report</h1>
                        <p>Generated on: ${new Date().toLocaleString()}</p>
                    </div>
                    
                    <div class="section">
                        <h2>Summary Statistics</h2>
                        <div class="metric">Total Vehicles Detected: ${data.total_vehicles}</div>
                        <div class="metric">Average FPS: ${data.performance_metrics.avg_fps.toFixed(2)}</div>
                        <div class="metric">Average Confidence: ${(data.performance_metrics.avg_confidence * 100).toFixed(2)}%</div>
                        <div class="metric">Average Processing Time: ${(data.performance_metrics.avg_processing_time * 1000).toFixed(2)}ms</div>
                    </div>
                    
                    <div class="section">
                        <h2>Vehicle Type Distribution</h2>
                        <table>
                            <tr><th>Vehicle Type</th><th>Count</th></tr>
                            ${Object.entries(data.vehicle_types).map(([type, count]) => `<tr><td>${type}</td><td>${count}</td></tr>`).join('')}
                        </table>
                    </div>
                    
                    <div class="section">
                        <h2>Weather Condition Analysis</h2>
                        <table>
                            <tr><th>Weather Condition</th><th>Vehicle Count</th></tr>
                            ${Object.entries(data.weather_conditions).map(([condition, count]) => `<tr><td>${condition}</td><td>${count}</td></tr>`).join('')}
                        </table>
                    </div>
                </body>
                </html>
            `;
            
            const blob = new Blob([reportHTML], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `vehicle_detection_report_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showNotification('Report generated successfully', 'success');
        })
        .catch(error => {
            console.error('Error generating report:', error);
            showNotification('Error generating report', 'error');
        });
}

function getWeatherDisplayName(weather) {
    const names = {
        'normal': 'Normal Conditions',
        'rain': 'Rainy Weather',
        'fog': 'Foggy Conditions',
        'night': 'Low Light/Night',
        'snow': 'Snowy Weather'
    };
    return names[weather] || weather;
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        document.body.removeChild(notification);
    }, 3000);
}