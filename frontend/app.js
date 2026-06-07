// Global Variables
let map;
let nodesData = {};
let edgesData = [];
let markers = {};
let pathLines = [];
let connectionLines = [];

// Initialize Map and Load Graph
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initDateTime();
    fetchGraphData();

    // Form submission
    const form = document.getElementById("search-form");
    form.addEventListener("submit", handleSearchSubmit);
});

// Initialize Leaflet Map
function initMap() {
    // Center of Surakarta
    map = L.map('map').setView([-7.5666, 110.8283], 14);

    // CartoDB Dark Matter tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);
}

// Pre-fill time input with local time
function initDateTime() {
    const timeInput = document.getElementById("current-time");
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    timeInput.value = `${hours}:${minutes}`;
}

// Fetch Graph Nodes and Edges from API
async function fetchGraphData() {
    try {
        const response = await fetch("/api/nodes");
        const data = await response.json();
        
        edgesData = data.edges;
        
        // Populate select option & markers
        const startSelect = document.getElementById("start-node");
        startSelect.innerHTML = '<option value="" disabled selected>Pilih Lokasi Awal...</option>';

        data.nodes.forEach(node => {
            nodesData[node.id] = node;
            
            // Add option to dropdown
            const option = document.createElement("option");
            option.value = node.id;
            option.textContent = `${node.name} (${node.type})`;
            startSelect.appendChild(option);

            // Add marker to map
            createNodeMarker(node);
        });

        // Draw connections
        drawConnections();

    } catch (error) {
        console.error("Error fetching graph data:", error);
    }
}

// Create Custom Markers
function createNodeMarker(node) {
    let iconClass = "fa-hospital";
    let typeClass = "rs";

    if (node.type === "UTD_PMI") {
        iconClass = "fa-hand-holding-droplet";
        typeClass = "pmi";
    } else if (node.type === "DonorSukarela") {
        iconClass = "fa-user-nurse";
        typeClass = "volunteer";
    }

    const customIcon = L.divIcon({
        className: 'custom-div-icon',
        html: `<div class="marker-pin ${typeClass}" id="pin-${node.id}"><i class="fa-solid ${iconClass}"></i></div>`,
        iconSize: [30, 42],
        iconAnchor: [15, 42]
    });

    const marker = L.marker([node.lat, node.lon], { icon: customIcon }).addTo(map);
    
    // Popup content with details
    const popupContent = `
        <div style="color: #333; font-family: sans-serif;">
            <strong style="font-size: 14px;">${node.name}</strong><br>
            <span style="font-size: 11px; color: #666;">Tipe: ${node.type}</span><br>
            <hr style="margin: 8px 0; border: none; border-top: 1px solid #eee;">
            <strong>Stok Darah:</strong><br>
            A: ${node.stock.A} | B: ${node.stock.B} | AB: ${node.stock.AB} | O: ${node.stock.O}<br>
            <strong>Jam Operasional:</strong><br>
            ${node.operational_hours.is_24h ? "24 Jam" : `${node.operational_hours.open} - ${node.operational_hours.close}`}
        </div>
    `;
    marker.bindPopup(popupContent);
    markers[node.id] = marker;
}

// Draw standard connection lines
function drawConnections() {
    // Clear old lines
    connectionLines.forEach(line => map.removeLayer(line));
    connectionLines = [];

    edgesData.forEach(edge => {
        const fromNode = nodesData[edge.from];
        const toNode = nodesData[edge.to];
        if (fromNode && toNode) {
            const line = L.polyline(
                [[fromNode.lat, fromNode.lon], [toNode.lat, toNode.lon]],
                {
                    color: 'rgba(255, 255, 255, 0.15)',
                    weight: 2,
                    dashArray: '5, 5'
                }
            ).addTo(map);
            connectionLines.push(line);
        }
    });
}

// Handle Form Submit and Search Request
async function handleSearchSubmit(e) {
    e.preventDefault();

    const startId = document.getElementById("start-node").value;
    const bloodType = document.getElementById("blood-type").value;
    const qty = document.getElementById("quantity").value;
    const time = document.getElementById("current-time").value;
    const algorithm = document.getElementById("algorithm").value;

    if (!startId) return;

    // Reset markers and path lines
    resetPathHighlighting();

    try {
        const response = await fetch(`/api/search?start_id=${startId}&blood_type=${bloodType}&qty=${qty}&current_time=${time}&algorithm=${algorithm}`);
        const result = await response.json();

        displayResults(result, bloodType);

    } catch (error) {
        console.error("Error performing search:", error);
    }
}

// Reset Highlights
function resetPathHighlighting() {
    pathLines.forEach(line => map.removeLayer(line));
    pathLines = [];

    // Remove highlighted class from all pins
    Object.keys(markers).forEach(nodeId => {
        const pin = document.getElementById(`pin-${nodeId}`);
        if (pin) {
            pin.classList.remove("highlighted");
            pin.style.boxShadow = "";
        }
    });
}

// Display Path and Visited Nodes on map & UI
function displayResults(result, bloodType) {
    const resultCard = document.getElementById("result-card");
    const statusDiv = document.getElementById("result-status");
    const distSpan = document.getElementById("metric-distance");
    const visitedSpan = document.getElementById("metric-visited");
    const stepsOl = document.getElementById("path-steps");

    resultCard.classList.remove("hidden");
    stepsOl.innerHTML = "";

    // Set Status Text
    statusDiv.textContent = result.message;
    if (result.success) {
        statusDiv.className = "result-status success";
        distSpan.textContent = `${result.total_distance} km`;
        visitedSpan.textContent = result.visited.length;
    } else {
        statusDiv.className = "result-status fail";
        distSpan.textContent = "-";
        visitedSpan.textContent = result.visited.length;
    }

    // Visualize Visited Nodes (e.g. coloring or pulsing them temporarily)
    result.visited.forEach((node, index) => {
        setTimeout(() => {
            const pin = document.getElementById(`pin-${node.id}`);
            if (pin && node.id !== result.target_id) {
                // Flash visited nodes to visualize the search space
                pin.style.boxShadow = "0 0 15px rgba(56, 189, 248, 0.8)";
            }
        }, index * 150); // Animated delay to show expansion order
    });

    if (result.success && result.path) {
        // Draw the path lines after visited animation finishes or directly
        const latlngs = result.path.map(node => [node.lat, node.lon]);
        
        // Highlight path with a solid colored polyline
        const pathLine = L.polyline(latlngs, {
            color: '#fbbf24', // Yellow/Gold path
            weight: 5,
            opacity: 0.9
        }).addTo(map);
        pathLines.push(pathLine);

        // Zoom/fit map bounds to the path
        map.fitBounds(pathLine.getBounds(), { padding: [50, 50] });

        // Highlight target node
        setTimeout(() => {
            const targetPin = document.getElementById(`pin-${result.target_id}`);
            if (targetPin) {
                targetPin.classList.add("highlighted");
            }
        }, result.visited.length * 150);

        // Populate steps in the sidebar
        result.path.forEach((node, idx) => {
            const li = document.createElement("li");
            let nodeDetails = `${node.name}`;
            if (idx === 0) {
                nodeDetails += " (Mulai)";
            } else if (node.id === result.target_id) {
                nodeDetails += ` (Tujuan - Stok ${bloodType}: ${node.stock[bloodType] || 0})`;
            }
            li.textContent = nodeDetails;
            stepsOl.appendChild(li);
        });
    }
}
