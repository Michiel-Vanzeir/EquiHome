PICO_IP = "http://10.122.133.119:5000";

// --- Window Control Logic ---
let isWindowOpen = false;

document.getElementById('btn-open').addEventListener('click', () => {
    isWindowOpen = false;
    document.getElementById('window-status').textContent = 'Open';
    document.getElementById('window-status').classList.replace('bg-success', 'bg-warning');
    sendControlData({ windows_open: true });
});

document.getElementById('btn-close').addEventListener('click', () => {
    isWindowOpen = true;
    document.getElementById('window-status').textContent = 'Closed';
    document.getElementById('window-status').classList.replace('bg-warning', 'bg-success');
    sendControlData({ windows_open: false });
});

// --- Peltier Power Slider Control Logic ---
document.getElementById('peltier1').addEventListener('change', function() {
    const val = parseInt(this.value);
    document.getElementById('peltier1-val').textContent = val + '%';
    sendControlData({ peltier1: val });
});

document.getElementById('peltier2').addEventListener('change', function() {
    const val = parseInt(this.value);
    document.getElementById('peltier2-val').textContent = val + '%';
    sendControlData({ peltier2: val });
});

// --- Status & Setpoint Logic ---
// Change to PID mode
document.getElementById('mode-pid').addEventListener('change', () => {
    if(document.getElementById('mode-pid').checked) {
        sendControlData({ status: "PID" });
    }
});

// Change to Manual mode
document.getElementById('mode-manual').addEventListener('change', () => {
    if(document.getElementById('mode-manual').checked) {
        sendControlData({ status: "MANUAL" });
    }
});

// Change the setpoint
document.getElementById('btn-setpoint').addEventListener('click', () => {
    const val = parseFloat(document.getElementById('setpoint-input').value);
    
    // Check if setpoint is a valid value 
    if(!isNaN(val)) {
        sendControlData({ setpoint: val });
        const btn = document.getElementById('btn-setpoint');
        const originalText = btn.innerText;
        btn.innerText = "Saved!";
        btn.classList.replace('btn-primary', 'btn-success');
        setTimeout(() => {
            btn.innerText = originalText;
            btn.classList.replace('btn-success', 'btn-primary');
        }, 1500);
    }
});

// Send Control Data to Pico
function sendControlData(payload) {
    fetch(`${PICO_IP}/api/control`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
    }).catch(err => console.error("Error sending to Pico:", err));
}

// --- Chart.js Initialization (Starts Empty) ---
const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 },
    scales: {
        x: { display: true, title: { display: true, text: 'Time' } },
        y: { display: true, title: { display: true, text: 'Temperature (°C)' } }
    },
    elements: { point: { radius: 2 } }
};

const ctx1 = document.getElementById('chartHouse1').getContext('2d');
const chartHouse1 = new Chart(ctx1, {
    type: 'line',
    data: {
        labels: [], 
        datasets: [
            { label: 'Average indoor temperature', borderColor: '#0d6efd', data: [], fill: false, tension: 0.3 },
       ]
    },
    options: commonOptions
});

const ctx2 = document.getElementById('chartHouse2').getContext('2d');
const chartHouse2 = new Chart(ctx2, {
    type: 'line',
    data: {
        labels: [], 
        datasets: [
            { label: 'Average indoor temperature', borderColor: '#0d6efd', data: [], fill: false, tension: 0.3 },
            { label: 'Outdoor temperature', borderColor: '#198754', data: [], fill: false, tension: 0.3 },        ]
    },
    options: commonOptions
});

function updateHouseData(houseNum, t1, t2, t3, avg) {
    const timeStr = new Date().toLocaleTimeString();
    let targetChart;
    
    if (houseNum === 1) {
        targetChart = chartHouse1;
        document.getElementById('val-h1-1').innerText = t1.toFixed(1) + ' °C';
        document.getElementById('val-h1-2').innerText = t2.toFixed(1) + ' °C';
        document.getElementById('val-h1-3').innerText = t3.toFixed(1) + ' °C';
    } else {
        return;
    }

    if (targetChart.data.labels.length >= 600) {
        targetChart.data.labels.shift();
        targetChart.data.datasets.forEach(dataset => dataset.data.shift());
    }

    targetChart.data.labels.push(timeStr);
    
    if (targetChart.data.datasets[0]) {
        targetChart.data.datasets[0].data.push(avg);
    }
    
    targetChart.update();
}

// --- Polling the Pico for new data every 2 seconds ---
setInterval(() => {
    fetch(`${PICO_IP}/api/data`)
        .then(response => response.json())
        .then(data => {
            // Update de grafiek en temperaturen
            updateHouseData(1, data.house1.t1, data.house1.t2, data.house1.t3, data.house1.t4);
            
            // Update de sliders ALLEEN als het systeem in PID mode staat. 
            // Als het op Manual staat, wil je zelf de slider kunnen slepen zonder dat hij terugspringt.
            if (data.status === "PID") {
                // Update Slider 1
                document.getElementById('peltier1').value = data.peltiers.p1;
                document.getElementById('peltier1-val').textContent = Math.round(data.peltiers.p1) + '%';
                
                // Update Slider 2
                document.getElementById('peltier2').value = data.peltiers.p2;
                document.getElementById('peltier2-val').textContent = Math.round(data.peltiers.p2) + '%';
            }
        })
        .catch(err => console.error("Error fetching data:", err));
}, 1000);