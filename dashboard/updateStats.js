/* UPDATE THESE VALUES TO MATCH YOUR SETUP */

// Using the Nginx reverse proxy endpoints
const VM_IP = "155.248.219.72"  // Your VM IP address
const VM_PORT = "8300"
const PROCESSING_STATS_API_URL = `http://${VM_IP}:${VM_PORT}/processing/stats`
const ANALYZER_API_URL = {
    stats: `http://${VM_IP}:${VM_PORT}/analyzer/stats`,
    drone_position: `http://${VM_IP}:${VM_PORT}/analyzer/drone/position?index=2`,
    target_acquisition: `http://${VM_IP}:${VM_PORT}/analyzer/drone/target-acquisition?index=3`
}

// This function fetches and updates the general statistics
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

const updateCodeDiv = (result, elemId) => document.getElementById(elemId).innerText = JSON.stringify(result)

const getLocaleDateStr = () => (new Date()).toLocaleString()

const getStats = () => {
    document.getElementById("last-updated-value").innerText = getLocaleDateStr()

    makeReq(PROCESSING_STATS_API_URL, (result) => updateCodeDiv(result, "processing-stats"))
    makeReq(ANALYZER_API_URL.stats, (result) => updateCodeDiv(result, "analyzer-stats"))
    makeReq(ANALYZER_API_URL.drone_position, (result) => updateCodeDiv(result, "drone-position"))
    makeReq(ANALYZER_API_URL.target_acquisition, (result) => updateCodeDiv(result, "target-acquisition"))
}

const updateErrorMessages = (message) => {
    const id = Date.now()
    console.log("Creation", id)
    msg = document.createElement("div")
    msg.id = `error-${id}`
    msg.innerHTML = `<p>Something happened at ${getLocaleDateStr()}!</p><code>${message}</code>`
    document.getElementById("messages").style.display = "block"
    document.getElementById("messages").prepend(msg)
    setTimeout(() => {
        const elem = document.getElementById(`error-${id}`)
        if (elem) { elem.remove() }
    }, 7000)
}

const setup = () => {
    getStats()
    setInterval(() => getStats(), 4000) // Update every 4 seconds
}

document.addEventListener('DOMContentLoaded', setup)
