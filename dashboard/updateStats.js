
const VM_IP = "155.248.219.72"
const VM_PORT = "8300"
const PROCESSING_STATS_API_URL = `http://${VM_IP}:${VM_PORT}/processing/stats`
const ANALYZER_API_URL = {
    stats: `http://${VM_IP}:${VM_PORT}/analyzer/stats`,
    drone_position: `http://${VM_IP}:${VM_PORT}/analyzer/drone/position`,
    target_acquisition: `http://${VM_IP}:${VM_PORT}/analyzer/drone/target-acquisition`
}


let currentEventIndexes = {
    drone_position: 1,
    target_acquisition: 1
}


const makeReq = (url, cb) => {
    fetch(url)
    .then(res => res.json())
    .then((result) => {
        console.log("Received data: ", result)
        cb(result);
    }).catch((error) => {
        updateErrorMessages(error.message)
    })
}

const updateCodeDiv = (result, elemId) => {
    document.getElementById(elemId).innerText = JSON.stringify(result, null, 2)


    if (elemId === "processing-stats") {
        updateProcessingStats(result)
    } else if (elemId === "analyzer-stats") {
        updateAnalyzerStats(result)
    } else if (elemId === "drone-position") {
        updateDronePositionDetails(result)
    } else if (elemId === "target-acquisition") {
        updateTargetAcquisitionDetails(result)
    }
}

const updateProcessingStats = (data) => {
    if (!data) return


        if (data.last_updated) {
            document.getElementById("last-updated-value").innerText = data.last_updated
        }
        if (data.max_certainty) {
            document.getElementById("max-certainty").innerText = data.max_certainty
        }
        if (data.max_signal_strength) {
            document.getElementById("max-signal").innerText = data.max_signal_strength
        }
        if (data.num_drone_positions) {
            document.getElementById("num-drone-positions").innerText = data.num_drone_positions
        }
        if (data.num_target_acquisitions) {
            document.getElementById("num-target-acquisitions").innerText = data.num_target_acquisitions
        }
}

const updateAnalyzerStats = (data) => {
    if (!data) return


        if (data.num_drone_position) {
            document.getElementById("num-drone-position").innerText = data.num_drone_position
        }
        if (data.num_target_acquisition) {
            document.getElementById("num-target-acquisition").innerText = data.num_target_acquisition
        }

        updateEventSelectors(data)
}

const updateDronePositionDetails = (data) => {
    if (!data) return

        if (data.altitude) {
            document.getElementById("drone-altitude").innerText = data.altitude
        }
        if (data.latitude) {
            document.getElementById("drone-latitude").innerText = data.latitude.toFixed(6)
        }
        if (data.longitude) {
            document.getElementById("drone-longitude").innerText = data.longitude.toFixed(4)
        }
        if (data.drone_id) {
            document.getElementById("drone-id").innerText = data.drone_id
        }
        if (data.signal_strength) {
            document.getElementById("drone-signal").innerText = data.signal_strength
        }
        if (data.timestamp) {
            document.getElementById("drone-timestamp").innerText = formatTimestamp(data.timestamp)
        }
}

const updateTargetAcquisitionDetails = (data) => {
    if (!data) return


        if (data.acquisition_type) {
            document.getElementById("acquisition-type").innerText = data.acquisition_type
        }
        if (data.altitude) {
            document.getElementById("target-altitude").innerText = data.altitude
        }
        if (data.certainty) {
            document.getElementById("target-certainty").innerText = data.certainty
        }
        if (data.drone_id) {
            document.getElementById("target-drone-id").innerText = data.drone_id
        }
        if (data.latitude) {
            document.getElementById("target-latitude").innerText = data.latitude.toFixed(6)
        }
        if (data.longitude) {
            document.getElementById("target-longitude").innerText = data.longitude.toFixed(6)
        }
        if (data.target_id) {
            document.getElementById("target-id").innerText = data.target_id
        }
        if (data.target_type) {
            document.getElementById("target-type").innerText = data.target_type
        }
        if (data.timestamp) {
            document.getElementById("target-timestamp").innerText = formatTimestamp(data.timestamp)
        }
}


const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleString()
}


const updateEventSelectors = (analyzerStats) => {
    if (!analyzerStats) return;

    const dronePositionCount = analyzerStats.num_drone_position || 0;
    const targetAcquisitionCount = analyzerStats.num_target_acquisition || 0;

    // Update drone position selector
    const dronePositionSelector = document.getElementById('drone-position-selector');
    dronePositionSelector.innerHTML = '';
    for (let i = 1; i <= dronePositionCount; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        if (i === currentEventIndexes.drone_position) {
            option.selected = true;
        }
        dronePositionSelector.appendChild(option);
    }


    const targetAcquisitionSelector = document.getElementById('target-acquisition-selector');
    targetAcquisitionSelector.innerHTML = '';
    for (let i = 1; i <= targetAcquisitionCount; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        if (i === currentEventIndexes.target_acquisition) {
            option.selected = true;
        }
        targetAcquisitionSelector.appendChild(option);
    }
}


const updateSelectedEvent = (eventType, userIndex) => {

    const apiIndex = parseInt(userIndex) - 1;
    currentEventIndexes[eventType] = parseInt(userIndex);


    const url = `${ANALYZER_API_URL[eventType]}?index=${apiIndex}`;
    const elemId = eventType === 'drone_position' ? 'drone-position' : 'target-acquisition';

    makeReq(url, (result) => updateCodeDiv(result, elemId));
}

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    makeReq(PROCESSING_STATS_API_URL, (result) => {
        updateCodeDiv(result, "processing-stats");
    });


    makeReq(ANALYZER_API_URL.stats, (result) => {
        updateCodeDiv(result, "analyzer-stats");
    });


    makeReq(`${ANALYZER_API_URL.drone_position}?index=${currentEventIndexes.drone_position - 1}`,
            (result) => updateCodeDiv(result, "drone-position"));

    makeReq(`${ANALYZER_API_URL.target_acquisition}?index=${currentEventIndexes.target_acquisition - 1}`,
            (result) => updateCodeDiv(result, "target-acquisition"));
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `
    <p><i class="fas fa-exclamation-triangle"></i> Error at ${getLocaleDateStr()}</p>
    <code>${message}</code>
    `
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) {
            elem.style.opacity = "0"
            setTimeout(() => elem.remove(), 300)
        }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000)
}

document.addEventListener('DOMContentLoaded', setup)
