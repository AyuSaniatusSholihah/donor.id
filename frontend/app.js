// Global Variables
let map;
let nodesData = {};
let edgesData = [];
let markers = {};
let pathLines = [];
let connectionLines = [];
let animatedMarkers = [];
let animationTimers = [];
let routeLegend = null;
let initialBounds = null;
let showGraphEdges = false;
let explorationMaps = { astar: null, bfs: null };
let explorationMapLayers = { astar: [], bfs: [] };
let explorationConnectionLayers = { astar: [], bfs: [] };

const API_BASE = getApiBase();
const ASTAR_COLOR       = "#2196F3";   // warna node eksplorasi A*
const BFS_COLOR         = "#FF9800";   // warna node eksplorasi BFS
const ASTAR_ROUTE_COLOR = "#00E5FF";   // warna jalur rute A* (cyan)
const BFS_ROUTE_COLOR   = "#FF4081";   // warna jalur rute BFS (pink)
const START_COLOR = "#94a3b8";
const GOAL_COLOR  = "#22c55e";

// Initialize Map and Load Graph
document.addEventListener("DOMContentLoaded", () => {
    initMap();
    initDateTime();
    fetchGraphData();

    const form = document.getElementById("search-form");
    form.addEventListener("submit", handleSearchSubmit);

    const resetButton = document.getElementById("reset-map");
    resetButton.addEventListener("click", resetMapView);

    const edgeToggle = document.getElementById("show-graph-edges");
    edgeToggle.addEventListener("change", handleGraphEdgeToggle);

    const closeSingleTreeButton = document.getElementById("close-single-tree");
    closeSingleTreeButton.addEventListener("click", () => {
        document.getElementById("single-tree-panel").classList.add("hidden");
    });
});

function getApiBase() {
    const isBackendOrigin = window.location.hostname === "localhost" && window.location.port === "8000";
    const isBackendIpOrigin = window.location.hostname === "127.0.0.1" && window.location.port === "8000";

    if (window.location.protocol === "file:" || (!isBackendOrigin && !isBackendIpOrigin)) {
        return "http://localhost:8000";
    }

    return "";
}

// Initialize Leaflet Map
function initMap() {
    // Center of Surakarta
    map = L.map("map").setView([-7.5666, 110.8283], 14);

    // CartoDB Dark Matter tile layer
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20
    }).addTo(map);
}

// Pre-fill time input with local time
function initDateTime() {
    const timeInput = document.getElementById("current-time");
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    timeInput.value = `${hours}:${minutes}`;
}

// Fetch Graph Nodes and Edges from API
async function fetchGraphData() {
    try {
        const response = await fetch(`${API_BASE}/api/nodes`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status} saat memuat node`);
        }
        const data = await response.json();

        edgesData = Array.isArray(data.edges) ? data.edges : [];

        const startSelect = document.getElementById("start-node");
        startSelect.innerHTML = '<option value="" disabled selected>Pilih Lokasi Awal...</option>';

        data.nodes.forEach(node => {
            nodesData[node.id] = node;

            const option = document.createElement("option");
            option.value = node.id;
            option.textContent = `${node.name} (${node.type})`;
            startSelect.appendChild(option);

            createNodeMarker(node);
        });

        if (Object.keys(markers).length > 0) {
            const markerGroup = L.featureGroup(Object.values(markers));
            initialBounds = markerGroup.getBounds();
            map.fitBounds(initialBounds, { padding: [30, 30] });
        }

        if (showGraphEdges) {
            drawConnections();
        }
    } catch (error) {
        console.error("Error fetching graph data:", error);
        showGraphLoadError();
    }
}

function showGraphLoadError() {
    const startSelect = document.getElementById("start-node");
    startSelect.innerHTML = '<option value="" disabled selected>Gagal memuat lokasi dari API</option>';

    const panel = document.getElementById("comparison-panel");
    const results = document.getElementById("comparison-results");
    const summary = document.getElementById("comparison-summary");
    panel.classList.remove("hidden");
    results.classList.remove("hidden");
    summary.classList.add("warning");
    summary.textContent = `Tidak bisa memuat data node. Pastikan backend FastAPI berjalan di ${API_BASE || "http://localhost:8000"}.`;
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
        className: "custom-div-icon",
        html: `<div class="marker-pin ${typeClass}" id="pin-${node.id}"><i class="fa-solid ${iconClass}"></i></div>`,
        iconSize: [30, 42],
        iconAnchor: [15, 42]
    });

    const marker = L.marker([node.lat, node.lon], { icon: customIcon }).addTo(map);

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

function handleGraphEdgeToggle(e) {
    showGraphEdges = e.target.checked;
    if (showGraphEdges) {
        drawConnections();
        drawAllExplorationConnections();
    } else {
        clearConnections();
        clearAllExplorationConnections();
    }
}

function clearConnections() {
    connectionLines.forEach(line => map.removeLayer(line));
    connectionLines = [];
}

// Draw standard graph connection lines.
function drawConnections() {
    clearConnections();

    edgesData.forEach(edge => {
        const fromNode = nodesData[edge.from];
        const toNode = nodesData[edge.to];
        if (!fromNode || !toNode) return;

        const line = L.polyline(
            [
                [fromNode.lat, fromNode.lon],
                [toNode.lat, toNode.lon]
            ],
            getGraphEdgeStyle()
        ).addTo(map);

        line.bringToBack();
        connectionLines.push(line);
    });
}

function getGraphEdgeStyle(weight = 1.4, opacity = 0.65) {
    return {
        color: "rgba(148, 163, 184, 0.55)",
        weight,
        opacity,
        dashArray: "4 6",
        interactive: false
    };
}

// Handle Form Submit and Search Request
async function handleSearchSubmit(e) {
    e.preventDefault();

    const startId = document.getElementById("start-node").value;
    const bloodType = document.getElementById("blood-type").value;
    const qty = document.getElementById("quantity").value;
    const time = document.getElementById("current-time").value;
    const mode = document.getElementById("search-mode").value;

    if (!startId) {
        showValidationMessage("Pilih titik awal pencarian terlebih dahulu.");
        return;
    }

    resetVisualizations();
    setLoadingState(true, mode);

    try {
        const params = new URLSearchParams({
            start_id: startId,
            blood_type: bloodType,
            qty,
            current_time: time
        });

        if (mode === "compare") {
            await runComparisonSearch(params, bloodType, startId);
        } else {
            await runSingleAlgorithmSearch(params, bloodType, startId, mode);
        }
    } catch (error) {
        console.error("Error performing search:", error);
        showSearchError();
    } finally {
        setLoadingState(false);
    }
}

async function runComparisonSearch(params, bloodType, startId) {
    const [astarResponse, bfsResponse] = await Promise.all([
        fetch(`${API_BASE}/api/search?${params.toString()}&algorithm=astar`),
        fetch(`${API_BASE}/api/search?${params.toString()}&algorithm=bfs`)
    ]);

    if (!astarResponse.ok || !bfsResponse.ok) {
        throw new Error(`API search gagal: A* ${astarResponse.status}, BFS ${bfsResponse.status}`);
    }

    const [astarResult, bfsResult] = await Promise.all([
        astarResponse.json(),
        bfsResponse.json()
    ]);

    prepareExplorationPanel();
    fillComparisonData(astarResult, bfsResult, bloodType, startId);

    const mapDuration = animateMapComparison(astarResult, bfsResult);
    const treeDuration = renderTraversalTrees(astarResult, bfsResult, startId);
    const revealDelay = Math.max(mapDuration, treeDuration) + 350;

    const revealTimer = setTimeout(() => {
        revealComparisonResults(astarResult, bfsResult);
    }, revealDelay);
    animationTimers.push(revealTimer);
}

async function runSingleAlgorithmSearch(params, bloodType, startId, algorithm) {
    const response = await fetch(`${API_BASE}/api/search?${params.toString()}&algorithm=${algorithm}`);
    if (!response.ok) {
        throw new Error(`API search ${algorithm} gagal: ${response.status}`);
    }

    const result = await response.json();
    const nodeColor  = algorithm === "astar" ? ASTAR_COLOR       : BFS_COLOR;
    const routeColor = algorithm === "astar" ? ASTAR_ROUTE_COLOR : BFS_ROUTE_COLOR;
    const dashArray = null;

    document.getElementById("comparison-panel").classList.add("hidden");
    prepareSingleTreePanel(result, bloodType, algorithm);

    const mapDuration = animateSingleGlobalMap(result, nodeColor, routeColor, dashArray);
    const treeDuration = renderSingleTraversalTree(result, startId, algorithm);
    const doneDelay = Math.max(mapDuration, treeDuration) + 150;

    const doneTimer = setTimeout(() => {
        document.getElementById("single-tree-status").textContent = "Eksplorasi selesai";
    }, doneDelay);
    animationTimers.push(doneTimer);
}

function showValidationMessage(message) {
    const panel = document.getElementById("comparison-panel");
    const results = document.getElementById("comparison-results");
    const summary = document.getElementById("comparison-summary");
    panel.classList.remove("hidden");
    results.classList.remove("hidden");
    summary.classList.add("warning");
    summary.textContent = message;
}

function setLoadingState(isLoading, mode = "compare") {
    const button = document.querySelector(".btn-search");
    button.disabled = isLoading;
    const loadingText = mode === "compare" ? "Membandingkan..." : "Mencari...";
    button.innerHTML = isLoading
        ? `<i class="fa-solid fa-spinner fa-spin"></i> ${loadingText}`
        : '<i class="fa-solid fa-magnifying-glass"></i> Cari Fasilitas';
}

function showSearchError() {
    const panel = document.getElementById("comparison-panel");
    const results = document.getElementById("comparison-results");
    const summary = document.getElementById("comparison-summary");
    panel.classList.remove("hidden");
    results.classList.remove("hidden");
    summary.classList.add("warning");
    summary.textContent = "Terjadi kesalahan saat menghubungi API pencarian.";
}

function prepareExplorationPanel() {
    const panel = document.getElementById("comparison-panel");
    const results = document.getElementById("comparison-results");
    const mapSection = document.getElementById("map-section");
    const status = document.getElementById("exploration-status");

    panel.classList.remove("hidden");
    mapSection.classList.remove("hidden");
    results.classList.add("hidden");
    status.textContent = "Animasi eksplorasi berjalan";

    ensureExplorationMaps();
    setTimeout(() => {
        Object.values(explorationMaps).forEach(item => {
            if (item) item.invalidateSize();
        });
        fitExplorationMapsToNodes();
    }, 80);
}

function fillComparisonData(astarResult, bfsResult, bloodType, startId) {
    const summary = document.getElementById("comparison-summary");

    summary.classList.remove("warning");

    fillAlgorithmCard("astar", astarResult, bloodType);
    fillAlgorithmCard("bfs", bfsResult, bloodType);
    fillComparisonTable(astarResult, bfsResult);
    summary.textContent = buildEfficiencySummary(astarResult, bfsResult);

    if (!astarResult.success && !bfsResult.success) {
        summary.classList.add("warning");
    }

    const startNode = nodesData[startId];
    if (startNode) {
        highlightPin(startNode.id, "0 0 18px 4px rgba(148, 163, 184, 0.8)");
    }
}

function revealComparisonResults(astarResult, bfsResult) {
    const results = document.getElementById("comparison-results");
    const summary = document.getElementById("comparison-summary");
    const status = document.getElementById("exploration-status");

    results.classList.remove("hidden");
    status.textContent = "Perbandingan selesai";

    if (!astarResult.success && !bfsResult.success) {
        summary.classList.add("warning");
    }
}

function prepareSingleTreePanel(result, bloodType, algorithm) {
    const panel = document.getElementById("single-tree-panel");
    const title = document.getElementById("single-tree-title");
    const status = document.getElementById("single-tree-status");
    const facility = document.getElementById("single-facility");
    const distance = document.getElementById("single-distance");
    const visited = document.getElementById("single-visited");
    const time = document.getElementById("single-time");
    const target = result.recommended_node;
    const label = algorithm === "astar" ? "A*" : "BFS";

    panel.classList.remove("hidden");
    title.textContent = `Tree ${label}`;
    status.textContent = "Eksplorasi berjalan";
    facility.textContent = target ? `${target.name} (stok ${bloodType}: ${target.stock?.[bloodType] ?? 0})` : "Tidak ditemukan";
    distance.textContent = result.success ? `Jarak: ${formatNumber(result.distance, 2)} km` : "Jarak: -";
    visited.textContent = `Node: ${getVisitedCount(result)}`;
    time.textContent = result.success ? `Waktu: ${formatNumber(result.execution_time_ms, 3)} ms` : "Waktu: -";
}

function fillAlgorithmCard(prefix, result, bloodType) {
    const facility = document.getElementById(`${prefix}-facility`);
    const distance = document.getElementById(`${prefix}-distance`);
    const visited = document.getElementById(`${prefix}-visited`);
    const time = document.getElementById(`${prefix}-time`);
    const message = document.getElementById(`${prefix}-message`);

    const target = result.recommended_node;
    facility.textContent = target ? `${target.name} (stok ${bloodType}: ${target.stock?.[bloodType] ?? 0})` : "Tidak ditemukan";
    distance.textContent = result.success ? `${formatNumber(result.distance, 2)} km` : "-";
    visited.textContent = result.visited_count ?? (result.visited_nodes || []).length;
    time.textContent = result.success ? `${formatNumber(result.execution_time_ms, 3)} ms` : "-";
    message.textContent = result.message || (result.success ? "Berhasil menemukan fasilitas." : "Tidak ada fasilitas yang cocok.");
}

function fillComparisonTable(astarResult, bfsResult) {
    const tbody = document.getElementById("comparison-table-body");
    tbody.innerHTML = "";

    const rows = [
        {
            label: "Jarak (km)",
            astar: astarResult.success ? astarResult.distance : null,
            bfs: bfsResult.success ? bfsResult.distance : null,
            astarText: astarResult.success ? formatNumber(astarResult.distance, 2) : "-",
            bfsText: bfsResult.success ? formatNumber(bfsResult.distance, 2) : "-",
            type: "lower"
        },
        {
            label: "Node dikunjungi",
            astar: getVisitedCount(astarResult),
            bfs: getVisitedCount(bfsResult),
            astarText: String(getVisitedCount(astarResult)),
            bfsText: String(getVisitedCount(bfsResult)),
            type: "lower"
        },
        {
            label: "Waktu (ms)",
            astar: astarResult.success ? astarResult.execution_time_ms : null,
            bfs: bfsResult.success ? bfsResult.execution_time_ms : null,
            astarText: astarResult.success ? formatNumber(astarResult.execution_time_ms, 3) : "-",
            bfsText: bfsResult.success ? formatNumber(bfsResult.execution_time_ms, 3) : "-",
            type: "lower"
        },
        {
            label: "Fasilitas",
            astarText: astarResult.recommended_node?.name || "-",
            bfsText: bfsResult.recommended_node?.name || "-",
            type: "facility"
        }
    ];

    rows.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.label}</td>
            <td>${row.astarText}</td>
            <td>${row.bfsText}</td>
            <td>${getWinnerText(row, astarResult, bfsResult)}</td>
        `;
        tbody.appendChild(tr);
    });
}

function getWinnerText(row, astarResult, bfsResult) {
    if (row.type === "facility") {
        const astarId = astarResult.recommended_node?.id;
        const bfsId = bfsResult.recommended_node?.id;
        if (!astarId && !bfsId) return "-";
        return astarId === bfsId ? "sama" : "beda";
    }

    if (row.astar == null && row.bfs == null) return "-";
    if (row.astar == null) return '<span class="winner-mark">BFS</span>';
    if (row.bfs == null) return '<span class="winner-mark">A*</span>';
    if (Number(row.astar) === Number(row.bfs)) return "-";
    return Number(row.astar) < Number(row.bfs)
        ? '<span class="winner-mark">A* ✓</span>'
        : '<span class="winner-mark">BFS ✓</span>';
}

function buildEfficiencySummary(astarResult, bfsResult) {
    const astarCount = getVisitedCount(astarResult);
    const bfsCount = getVisitedCount(bfsResult);

    if (!astarResult.success && !bfsResult.success) {
        return `Keduanya belum menemukan fasilitas yang cocok. A* mengunjungi ${astarCount} node, BFS ${bfsCount} node.`;
    }

    if (astarCount === bfsCount) {
        return `A* dan BFS sama efisien dari jumlah node: masing-masing mengunjungi ${astarCount} node.`;
    }

    const winner = astarCount < bfsCount ? "A*" : "BFS";
    const loser = winner === "A*" ? "BFS" : "A*";
    const winnerCount = Math.min(astarCount, bfsCount);
    const loserCount = Math.max(astarCount, bfsCount);
    const percent = loserCount === 0 ? 0 : Math.round(((loserCount - winnerCount) / loserCount) * 100);

    return `${winner} lebih efisien: mengunjungi ${winnerCount} node vs ${loser} ${loserCount} node (${percent}% lebih sedikit).`;
}

function animateMapComparison(astarResult, bfsResult) {
    ensureExplorationMaps();

    const astarDuration = animateAlgorithmMap("astar", astarResult, ASTAR_COLOR, ASTAR_ROUTE_COLOR, null);
    const bfsDuration   = animateAlgorithmMap("bfs",   bfsResult,   BFS_COLOR,   BFS_ROUTE_COLOR,   null);

    return Math.max(astarDuration, bfsDuration);
}

function animateSingleGlobalMap(result, nodeColor, routeColor, dashArray) {
    const visitedNodes = result.visited_nodes || [];
    const targetId = result.recommended_node?.id;
    const routeDelay = visitedNodes.length * 300 + 180;

    // Kumpulkan semua koordinat untuk fitBounds:
    // selalu sertakan semua node yang dikunjungi agar zoom mencakup area eksplorasi penuh
    const boundsCoords = visitedNodes.map(node => [node.lat, node.lon]);

    let latlngs = null;
    if (result.success && Array.isArray(result.path) && result.path.length > 1) {
        latlngs = (result.path_geometry && result.path_geometry.length >= 2)
            ? result.path_geometry
            : result.path.map(node => [node.lat, node.lon]);

        // Tambahkan koordinat rute ke bounds
        boundsCoords.push(...latlngs);
    }

    // Zoom peta mencakup seluruh area eksplorasi + rute
    if (boundsCoords.length > 0) {
        map.fitBounds(L.latLngBounds(boundsCoords), getSingleMapFitOptions());
    }

    if (latlngs) {
        const routeTimer = setTimeout(() => {
            const pathLine = L.polyline(latlngs, {
                color: routeColor,
                weight: 5,
                opacity: 0.95,
                dashArray
            }).addTo(map);
            pathLines.push(pathLine);
            pathLine.bringToBack();

            if (targetId) {
                const targetPin = document.getElementById(`pin-${targetId}`);
                if (targetPin) {
                    targetPin.classList.add("highlighted");
                    targetPin.style.boxShadow = "0 0 24px 6px rgba(34, 197, 94, 0.95)";
                }
            }
        }, routeDelay);
        animationTimers.push(routeTimer);
    }

    visitedNodes.forEach((node, index) => {
        const timer = setTimeout(() => {
            if (!node || node.id === targetId) return;

            const marker = L.circleMarker([node.lat, node.lon], {
                radius: 7,
                color: nodeColor,
                fillColor: nodeColor,
                fillOpacity: 0.9,
                weight: 2,
                opacity: 1
            }).addTo(map);
            marker.bindTooltip(node.name, { direction: "top", offset: [0, -6] });
            animatedMarkers.push(marker);
        }, index * 300);
        animationTimers.push(timer);
    });

    return routeDelay + 350;
}

function getSingleMapFitOptions() {
    const panel = document.getElementById("single-tree-panel");
    const panelWidth = panel && !panel.classList.contains("hidden") ? panel.offsetWidth : 0;

    return {
        paddingTopLeft: [70, 70],
        paddingBottomRight: [panelWidth + 90, 70]
    };
}

function ensureExplorationMaps() {
    createExplorationMap("astar", "astar-mini-map");
    createExplorationMap("bfs", "bfs-mini-map");
}

function createExplorationMap(key, elementId) {
    if (explorationMaps[key]) return;

    const mapInstance = L.map(elementId, {
        zoomControl: false,
        attributionControl: false
    }).setView([-7.5666, 110.8283], 13);

    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        subdomains: "abcd",
        maxZoom: 20
    }).addTo(mapInstance);

    explorationMaps[key] = mapInstance;
}

function fitExplorationMapsToNodes() {
    const allNodes = Object.values(nodesData);
    if (!allNodes.length) return;

    const bounds = L.latLngBounds(allNodes.map(node => [node.lat, node.lon]));
    Object.values(explorationMaps).forEach(item => {
        if (item) item.fitBounds(bounds, { padding: [18, 18] });
    });
}

function animateAlgorithmMap(key, result, nodeColor, routeColor, dashArray) {
    const targetMap = explorationMaps[key];
    if (!targetMap) return 0;

    clearExplorationMapLayers(key);
    clearExplorationConnections(key);
    if (showGraphEdges) {
        drawExplorationConnections(key);
    }
    drawExplorationBaseNodes(key);

    const visitedNodes = result.visited_nodes || [];
    const targetId = result.recommended_node?.id;
    const routeDelay = visitedNodes.length * 300 + 180;

    // Kumpulkan bounds dari semua node yang dikunjungi + rute
    const boundsCoords = visitedNodes.map(node => [node.lat, node.lon]);

    let latlngs = null;
    if (result.success && Array.isArray(result.path) && result.path.length > 1) {
        latlngs = (result.path_geometry && result.path_geometry.length >= 2)
            ? result.path_geometry
            : result.path.map(node => [node.lat, node.lon]);

        boundsCoords.push(...latlngs);
    }

    // Zoom mini map mencakup seluruh area eksplorasi + rute
    if (boundsCoords.length > 0) {
        targetMap.fitBounds(L.latLngBounds(boundsCoords), { padding: [28, 28] });
    }

    if (latlngs) {
        const routeTimer = setTimeout(() => {
            const route = L.polyline(latlngs, {
                color: routeColor,
                weight: 4,
                opacity: 0.96,
                dashArray
            }).addTo(targetMap);
            explorationMapLayers[key].push(route);
            route.bringToBack();
        }, routeDelay);
        animationTimers.push(routeTimer);
    }

    visitedNodes.forEach((node, index) => {
        const timer = setTimeout(() => {
            if (!node) return;

            const marker = L.circleMarker([node.lat, node.lon], {
                radius: node.id === targetId ? 8 : 6,
                color: node.id === targetId ? GOAL_COLOR : nodeColor,
                fillColor: node.id === targetId ? GOAL_COLOR : nodeColor,
                fillOpacity: 0.9,
                weight: node.id === targetId ? 3 : 2,
                opacity: 1
            }).addTo(targetMap);

            marker.bindTooltip(node.name, { direction: "top", offset: [0, -6] });
            explorationMapLayers[key].push(marker);
        }, index * 300);
        animationTimers.push(timer);
    });

    return routeDelay + 350;
}

function drawExplorationBaseNodes(key) {
    const targetMap = explorationMaps[key];
    if (!targetMap) return;

    Object.values(nodesData).forEach(node => {
        const marker = L.circleMarker([node.lat, node.lon], {
            radius: 4,
            color: "rgba(226, 232, 240, 0.58)",
            fillColor: "rgba(148, 163, 184, 0.42)",
            fillOpacity: 0.5,
            weight: 1
        }).addTo(targetMap);
        marker.bindTooltip(node.name, { direction: "top", offset: [0, -6] });
        explorationMapLayers[key].push(marker);
    });
}

function drawAllExplorationConnections() {
    Object.keys(explorationMaps).forEach(key => drawExplorationConnections(key));
}

function clearAllExplorationConnections() {
    Object.keys(explorationMaps).forEach(key => clearExplorationConnections(key));
}

function drawExplorationConnections(key) {
    const targetMap = explorationMaps[key];
    if (!targetMap) return;

    clearExplorationConnections(key);

    edgesData.forEach(edge => {
        const fromNode = nodesData[edge.from];
        const toNode = nodesData[edge.to];
        if (!fromNode || !toNode) return;

        const line = L.polyline(
            [
                [fromNode.lat, fromNode.lon],
                [toNode.lat, toNode.lon]
            ],
            getGraphEdgeStyle(1, 0.5)
        ).addTo(targetMap);

        line.bringToBack();
        explorationConnectionLayers[key].push(line);
    });
}

function clearExplorationConnections(key) {
    explorationConnectionLayers[key].forEach(layer => {
        if (explorationMaps[key]) {
            explorationMaps[key].removeLayer(layer);
        }
    });
    explorationConnectionLayers[key] = [];
}

function clearExplorationMapLayers(key) {
    explorationMapLayers[key].forEach(layer => {
        if (explorationMaps[key]) {
            explorationMaps[key].removeLayer(layer);
        }
    });
    explorationMapLayers[key] = [];
}

function highlightPin(nodeId, boxShadow) {
    const pin = document.getElementById(`pin-${nodeId}`);
    if (pin) {
        pin.style.boxShadow = boxShadow;
        pin.style.transition = "box-shadow 0.3s ease";
    }
}

function addRouteLegend() {
    if (routeLegend) {
        map.removeControl(routeLegend);
    }

    routeLegend = L.control({ position: "bottomright" });
    routeLegend.onAdd = function onAddLegend() {
        const div = L.DomUtil.create("div", "map-route-legend");
        div.innerHTML = `
            <h4>Legenda Peta</h4>
            <div><span class="legend-line astar-route"></span> Jalur Rute A*</div>
            <div><span class="legend-line bfs-route"></span> Jalur Rute BFS</div>
            <div><span class="legend-dot astar-node"></span> Node Eksplorasi A*</div>
            <div><span class="legend-dot bfs-node"></span> Node Eksplorasi BFS</div>
            <div><span class="legend-dot goal-node"></span> Fasilitas Tujuan</div>
        `;
        return div;
    };
    routeLegend.addTo(map);
}

function renderTraversalTrees(astarResult, bfsResult, startId) {
    if (typeof d3 === "undefined") {
        console.error("D3.js belum dimuat, tree traversal tidak dapat dirender.");
        const status = document.getElementById("exploration-status");
        status.textContent = "D3 gagal dimuat";
        return 0;
    }

    const section = document.getElementById("tree-section");
    section.classList.remove("hidden");

    const astarTreeDuration = renderTree("#astar-tree", astarResult, startId, "astar", 0, 300, { compact: true });
    const bfsTreeDuration = renderTree("#bfs-tree", bfsResult, startId, "bfs", 0, 300, { compact: true });

    return Math.max(astarTreeDuration, bfsTreeDuration);
}

function renderSingleTraversalTree(result, startId, algorithm) {
    if (typeof d3 === "undefined") {
        console.error("D3.js belum dimuat, tree traversal tidak dapat dirender.");
        document.getElementById("single-tree-status").textContent = "D3 gagal dimuat";
        return 0;
    }

    return renderTree("#single-tree", result, startId, algorithm, 0, 300, { compact: true });
}

function renderTree(containerSelector, result, startId, algorithm, startDelay = 0, stepDelay = 200, options = {}) {
    const container = d3.select(containerSelector);
    container.selectAll("*").remove();

    const visitedNodes = result.visited_nodes || [];
    if (!visitedNodes.length) {
        container.append("div")
            .style("color", "#94a3b8")
            .style("font-size", "12px")
            .text("Belum ada node yang dikunjungi.");
        return startDelay;
    }

    const treeData = buildTreeData(visitedNodes, startId, result.recommended_node?.id, result.heuristic_details || {});
    const nodeCount = visitedNodes.length;
    const containerWidth = container.node()?.clientWidth || 320;
    const compact = Boolean(options.compact);
    const width = compact ? Math.max(260, containerWidth - 16) : Math.max(280, nodeCount * 58);
    const height = compact ? Math.max(320, getTreeDepth(treeData) * 86) : Math.max(220, getTreeDepth(treeData) * 92);
    const margin = compact
        ? { top: 28, right: 14, bottom: 34, left: 14 }
        : { top: 28, right: 24, bottom: 34, left: 24 };

    const svg = container.append("svg")
        .attr("width", width)
        .attr("height", height);

    const tooltip = getTreeTooltip();
    const root = d3.hierarchy(treeData);
    const layout = d3.tree().size([
        width - margin.left - margin.right,
        height - margin.top - margin.bottom
    ]);
    layout(root);

    const group = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    group.selectAll(".tree-link")
        .data(root.links())
        .enter()
        .append("path")
        .attr("class", "tree-link")
        .attr("d", d3.linkVertical().x(d => d.x).y(d => d.y))
        .style("opacity", 0)
        .transition()
        .delay((d, index) => startDelay + ((index + 1) * stepDelay))
        .duration(220)
        .style("opacity", 1);

    const node = group.selectAll(".tree-node")
        .data(root.descendants())
        .enter()
        .append("g")
        .attr("class", "tree-node")
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .style("opacity", 0);

    node.transition()
        .delay(d => startDelay + (d.data.order * stepDelay))
        .duration(250)
        .style("opacity", 1);

    node.append("circle")
        .attr("r", 13)
        .attr("fill", d => getTreeNodeColor(d.data, algorithm))
        .attr("stroke", d => d.data.isGoal ? "#bbf7d0" : "rgba(255, 255, 255, 0.75)")
        .attr("stroke-width", d => d.data.isGoal ? 4 : 1.5)
        .on("mousemove", (event, d) => showTreeTooltip(event, d.data, result.heuristic_details || {}, algorithm, tooltip))
        .on("mouseleave", () => tooltip.classed("hidden", true));

    node.append("text")
        .attr("class", "tree-label")
        .attr("dy", 30)
        .text(d => truncateLabel(d.data.name, compact ? 9 : 12));

    return startDelay + (visitedNodes.length * stepDelay) + 260;
}

function buildTreeData(visitedNodes, startId, goalId, heuristicDetails) {
    const rootNode = visitedNodes[0] || nodesData[startId];
    const root = createTreeNode(rootNode, 0, startId, goalId);
    const treeNodeById = { [root.id]: root };

    visitedNodes.slice(1).forEach((node, index) => {
        const treeNode = createTreeNode(node, index + 1, startId, goalId);
        // Gunakan parent yang dikirim backend (came_from), bukan koneksi graph asli
        const detail = (heuristicDetails || {})[node.id] || {};
        const parentId = detail.parent;
        const parent = (parentId && treeNodeById[parentId]) ? treeNodeById[parentId] : root;
        parent.children.push(treeNode);
        treeNodeById[node.id] = treeNode;
    });

    return root;
}

function createTreeNode(node, order, startId, goalId) {
    return {
        id: node.id,
        name: node.name,
        type: node.type,
        order,
        isStart: node.id === startId || order === 0,
        isGoal: node.id === goalId,
        children: []
    };
}



function getTreeDepth(node) {
    if (!node.children || node.children.length === 0) return 2;
    return 1 + Math.max(...node.children.map(getTreeDepth));
}

function getTreeNodeColor(data, algorithm) {
    if (data.isGoal) return GOAL_COLOR;
    if (data.isStart) return START_COLOR;
    return algorithm === "astar" ? ASTAR_COLOR : BFS_COLOR;
}

function getTreeTooltip() {
    let tooltip = d3.select(".tree-tooltip");
    if (tooltip.empty()) {
        tooltip = d3.select("body").append("div").attr("class", "tree-tooltip hidden");
    }
    return tooltip;
}

function showTreeTooltip(event, data, details, algorithm, tooltip) {
    const detail = details[data.id] || {};
    const g = detail.g ?? "-";
    const metricLines = algorithm === "astar"
        ? `<br>g: ${g}<br>f: ${detail.f ?? "-"}`
        : `<br>g: ${g}`;

    tooltip
        .classed("hidden", false)
        .style("left", `${event.clientX + 14}px`)
        .style("top", `${event.clientY + 14}px`)
        .html(`
            <strong>${data.name}</strong><br>
            Tipe: ${data.type}${metricLines}
        `);
}

function truncateLabel(text, maxLength) {
    if (!text) return "-";
    return text.length > maxLength ? `${text.slice(0, maxLength - 1)}...` : text;
}

// Reset Highlights, routes, animations, and tree diagrams.
function resetVisualizations() {
    animationTimers.forEach(timer => clearTimeout(timer));
    animationTimers = [];

    pathLines.forEach(line => map.removeLayer(line));
    pathLines = [];

    animatedMarkers.forEach(marker => map.removeLayer(marker));
    animatedMarkers = [];

    if (routeLegend) {
        map.removeControl(routeLegend);
        routeLegend = null;
    }

    clearExplorationMapLayers("astar");
    clearExplorationMapLayers("bfs");
    clearAllExplorationConnections();

    Object.keys(markers).forEach(nodeId => {
        const pin = document.getElementById(`pin-${nodeId}`);
        if (pin) {
            pin.classList.remove("highlighted");
            pin.style.boxShadow = "";
        }
    });

    if (typeof d3 !== "undefined") {
        d3.select("#astar-tree").selectAll("*").remove();
        d3.select("#bfs-tree").selectAll("*").remove();
        d3.select("#single-tree").selectAll("*").remove();
        d3.select(".tree-tooltip").classed("hidden", true);
    }
    document.getElementById("map-section").classList.add("hidden");
    document.getElementById("tree-section").classList.add("hidden");
    document.getElementById("comparison-results").classList.add("hidden");
    document.getElementById("single-tree-panel").classList.add("hidden");
    document.getElementById("exploration-status").textContent = "Menunggu pencarian";
}

function resetMapView() {
    resetVisualizations();
    document.getElementById("comparison-panel").classList.add("hidden");
    document.getElementById("comparison-table-body").innerHTML = "";

    if (initialBounds) {
        map.fitBounds(initialBounds, { padding: [30, 30] });
    }
}

function getVisitedCount(result) {
    return result.visited_count ?? (result.visited_nodes || []).length;
}

function formatNumber(value, digits) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return "-";
    return numeric.toFixed(digits);
}
