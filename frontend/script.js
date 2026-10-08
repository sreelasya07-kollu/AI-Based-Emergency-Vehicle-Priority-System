const API = "http://127.0.0.1:5050";

let currentUser = null;
let socket = null;

let ambulances = [];
let signals = [];

let hospitalMap = null;
let trafficMap = null;
let driverMap = null;

let hospitalMarkers = {};
let trafficMarkers = {};
let driverMarker = null;

const DEFAULT_CENTER = [17.3850, 78.4867];


// ============================================================
// LEAFLET CHECK
// ============================================================

function leafletReady() {
    if (typeof L === "undefined") {
        console.error("Leaflet did not load.");
        alert("Map library failed to load. Refresh the page.");
        return false;
    }

    return true;
}


// ============================================================
// AMBULANCE ICON
// ============================================================

function createAmbulanceIcon(emergency = false) {
    return L.divIcon({
        className: emergency
            ? "emergency-leaflet-icon"
            : "ambulance-leaflet-icon",

        html: `
            <div style="
                font-size:${emergency ? "40px" : "34px"};
                line-height:1;
                filter:
                    drop-shadow(0 0 3px white)
                    drop-shadow(0 0 ${emergency ? "10px red" : "4px black"});
            ">
                🚑
            </div>
        `,

        iconSize: emergency ? [45, 45] : [40, 40],
        iconAnchor: emergency ? [22, 22] : [20, 20]
    });
}


// ============================================================
// CREATE MAP
// ============================================================

function createMap(elementId) {

    if (!leafletReady()) {
        return null;
    }

    const element = document.getElementById(elementId);

    if (!element) {
        console.error("Map element not found:", elementId);
        return null;
    }

    // Remove old Leaflet instance if necessary
    if (element._leaflet_id) {
        element._leaflet_id = null;
        element.innerHTML = "";
    }

    const map = L.map(element).setView(
        DEFAULT_CENTER,
        13
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    setTimeout(() => {
        map.invalidateSize();
    }, 500);

    return map;
}


// ============================================================
// INITIALIZE MAPS
// ============================================================

function initializeMaps() {

    if (!currentUser) {
        return;
    }

    if (currentUser.role === "hospital") {

        if (!hospitalMap) {
            hospitalMap = createMap("hospitalMap");
        }

        setTimeout(() => {
            if (hospitalMap) {
                hospitalMap.invalidateSize();
                updateHospitalMap(
                    ambulances.filter(
                        ambulance =>
                            ambulance.hospital_id ===
                            currentUser.hospital_id
                    )
                );
            }
        }, 500);
    }


    if (
        currentUser.role === "traffic" ||
        currentUser.role === "admin"
    ) {

        if (!trafficMap) {
            trafficMap = createMap("trafficMap");
        }

        setTimeout(() => {
            if (trafficMap) {
                trafficMap.invalidateSize();
                updateTrafficMap(ambulances);
            }
        }, 500);
    }


    if (currentUser.role === "driver") {

        if (!driverMap) {
            driverMap = createMap("driverMap");
        }

        setTimeout(() => {

            if (!driverMap) {
                return;
            }

            driverMap.invalidateSize();

            const ambulance = ambulances.find(
                a =>
                    a.ambulance_id ===
                    currentUser.username
            );

            if (ambulance) {
                updateDriverMap(ambulance);
            }

        }, 500);
    }
}


// ============================================================
// LOGIN
// ============================================================

async function login() {

    const username =
        document.getElementById("username").value.trim();

    const password =
        document.getElementById("password").value.trim();

    const error =
        document.getElementById("loginError");

    error.textContent = "";

    if (!username || !password) {
        error.textContent =
            "Enter username and password.";
        return;
    }

    try {

        const response = await fetch(
            `${API}/api/login`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    username,
                    password
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Login failed"
            );
        }

        currentUser = data;

        localStorage.setItem(
            "rescue_user",
            JSON.stringify(data)
        );

        await loadAmbulances();

        showApplication();

    } catch (err) {

        console.error(err);

        error.textContent =
            err.message ||
            "Backend connection failed.";
    }
}


// ============================================================
// LOAD AMBULANCES DIRECTLY FROM API
// ============================================================

async function loadAmbulances() {

    try {

        const response = await fetch(
            `${API}/api/ambulances`
        );

        if (!response.ok) {
            throw new Error(
                "Could not load ambulances"
            );
        }

        const data = await response.json();

        ambulances = data.ambulances || [];

        console.log(
            "Ambulances loaded:",
            ambulances
        );

    } catch (error) {

        console.error(
            "Ambulance API error:",
            error
        );
    }
}


// ============================================================
// SHOW APPLICATION
// ============================================================

function showApplication() {

    document
        .getElementById("loginPage")
        .classList.add("hidden");

    document
        .getElementById("appPage")
        .classList.remove("hidden");

    const roleLabel =
        document.getElementById("roleLabel");

    if (roleLabel) {
        roleLabel.textContent =
            currentUser.role.toUpperCase();
    }

    hideAllDashboards();


    if (currentUser.role === "hospital") {

        document
            .getElementById("hospitalDashboard")
            .classList.remove("hidden");

        const hospitalName =
            document.getElementById("hospitalName");

        if (hospitalName) {
            hospitalName.textContent =
                `Hospital ID: ${
                    currentUser.hospital_id || "--"
                }`;
        }
    }


    else if (
        currentUser.role === "traffic" ||
        currentUser.role === "admin"
    ) {

        document
            .getElementById("trafficDashboard")
            .classList.remove("hidden");
    }


    else if (currentUser.role === "driver") {

        document
            .getElementById("driverDashboard")
            .classList.remove("hidden");
    }


    // Create map only after dashboard becomes visible
    setTimeout(() => {
        initializeMaps();
        updateDashboard();
    }, 150);


    connectWebSocket();
}


// ============================================================
// HIDE DASHBOARDS
// ============================================================

function hideAllDashboards() {

    [
        "hospitalDashboard",
        "trafficDashboard",
        "driverDashboard"
    ].forEach(id => {

        const element =
            document.getElementById(id);

        if (element) {
            element.classList.add("hidden");
        }
    });
}


// ============================================================
// LOGOUT
// ============================================================

function logout() {

    if (socket) {
        try {
            socket.close();
        } catch (error) {}

        socket = null;
    }

    localStorage.removeItem("rescue_user");

    currentUser = null;
    ambulances = [];
    signals = [];

    location.reload();
}


// ============================================================
// WEBSOCKET
// ============================================================

function connectWebSocket() {

    if (socket) {
        try {
            socket.close();
        } catch (error) {}
    }

    socket =
        new WebSocket(
            "ws://127.0.0.1:5050/ws"
        );


    socket.onopen = () => {

        console.log(
            "WebSocket connected"
        );

        updateConnectionStatus(true);
    };


    socket.onmessage = event => {

        try {

            const data =
                JSON.parse(event.data);

            if (data.type === "state") {

                ambulances =
                    data.ambulances || [];

                signals =
                    data.signals || [];

                console.log(
                    "LIVE STATE:",
                    ambulances
                );

                updateDashboard();

                // Refresh live ambulance/signal UI immediately
                if (typeof renderHospitalDashboard === "function") {
                    renderHospitalDashboard();
                }

                if (typeof renderTrafficDashboard === "function") {
                    renderTrafficDashboard();
                }

                if (typeof renderDriverDashboard === "function") {
                    renderDriverDashboard();
                }

                if (typeof updateHospitalMarkers === "function") {
                    updateHospitalMarkers();
                }

                if (typeof updateTrafficMarkers === "function") {
                    updateTrafficMarkers();
                }

                if (typeof updateDriverMap === "function") {
                    updateDriverMap();
                }
            }

        } catch (error) {

            console.error(
                "WebSocket message error:",
                error
            );
        }
    };


    socket.onclose = () => {

        updateConnectionStatus(false);

        if (currentUser) {

            setTimeout(
                connectWebSocket,
                3000
            );
        }
    };


    socket.onerror = error => {

        console.error(
            "WebSocket error:",
            error
        );

        updateConnectionStatus(false);
    };
}


// ============================================================
// CONNECTION STATUS
// ============================================================

function updateConnectionStatus(connected) {

    const element =
        document.getElementById(
            "connectionStatus"
        );

    if (!element) {
        return;
    }

    if (connected) {

        element.textContent =
            "● LIVE CONNECTED";

        element.className =
            "connection connected";

    } else {

        element.textContent =
            "● DISCONNECTED";

        element.className =
            "connection disconnected";
    }
}


// ============================================================
// UPDATE DASHBOARD
// ============================================================

function updateDashboard() {

    if (!currentUser) {
        return;
    }


    if (currentUser.role === "hospital") {
        updateHospital();
    }


    else if (
        currentUser.role === "traffic" ||
        currentUser.role === "admin"
    ) {
        updateTraffic();
    }


    else if (currentUser.role === "driver") {
        updateDriver();
    }
}


// ============================================================
// HOSPITAL DASHBOARD
// ============================================================

function updateHospital() {

    const list =
        ambulances.filter(
            ambulance =>
                ambulance.hospital_id ===
                currentUser.hospital_id
        );


    const emergency =
        list.filter(
            ambulance =>
                ambulance.emergency
        ).length;


    const count =
        document.getElementById(
            "hospitalEmergencyCount"
        );

    if (count) {
        count.textContent =
            `${emergency} EMERGENCIES`;
    }


    renderHospitalAmbulances(list);

    updateHospitalMap(list);
}


// ============================================================
// HOSPITAL CARDS
// ============================================================

function renderHospitalAmbulances(list) {

    const container =
        document.getElementById(
            "hospitalAmbulances"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";


    list.forEach(ambulance => {

        const card =
            document.createElement("div");

        card.className =
            "ambulance-card";


        if (ambulance.emergency) {
            card.classList.add("emergency");
        }


        card.innerHTML = `

            <div class="ambulance-icon">
                🚑
            </div>

            <div>

                <h3>
                    ${ambulance.ambulance_id}
                </h3>

                <p>
                    Status:
                    <strong>
                        ${ambulance.status || "--"}
                    </strong>
                </p>

                <p>
                    Destination:
                    ${ambulance.destination || "--"}
                </p>

                <p>
                    ETA:
                    ${ambulance.eta || "--"}
                </p>

            </div>

            <div>
                ${
                    ambulance.emergency
                        ? "🚨 EMERGENCY"
                        : "🟢 NORMAL"
                }
            </div>

        `;

        container.appendChild(card);
    });
}


// ============================================================
// HOSPITAL MAP
// ============================================================

function updateHospitalMap(list) {

    if (!hospitalMap) {
        return;
    }

    const activeIds = [];


    list.forEach(ambulance => {

        if (
            ambulance.lat == null ||
            ambulance.lng == null
        ) {
            return;
        }


        // IMPORTANT:
        // Backend field is ambulance_id
        const id =
            ambulance.ambulance_id;

        activeIds.push(id);


        const position = [
            Number(ambulance.lat),
            Number(ambulance.lng)
        ];


        const icon =
            createAmbulanceIcon(
                ambulance.emergency
            );


        if (hospitalMarkers[id]) {

            hospitalMarkers[id]
                .setLatLng(position);

            hospitalMarkers[id]
                .setIcon(icon);

            hospitalMarkers[id]
                .setPopupContent(
                    ambulancePopup(
                        ambulance
                    )
                );

        } else {

            hospitalMarkers[id] =
                L.marker(
                    position,
                    {
                        icon: icon
                    }
                )
                .addTo(hospitalMap)
                .bindPopup(
                    ambulancePopup(
                        ambulance
                    )
                );
        }
    });


    // Remove old markers
    Object.keys(hospitalMarkers)
        .forEach(id => {

            if (!activeIds.includes(id)) {

                hospitalMap.removeLayer(
                    hospitalMarkers[id]
                );

                delete hospitalMarkers[id];
            }
        });


    fitMap(
        hospitalMap,
        list
    );
}


// ============================================================
// TRAFFIC DASHBOARD
// ============================================================

function updateTraffic() {

    const emergency =
        ambulances.filter(
            a => a.emergency
        );


    const green =
        signals.filter(
            s => s.status === "GREEN"
        );


    const emergencyElement =
        document.getElementById(
            "trafficEmergency"
        );

    if (emergencyElement) {
        emergencyElement.textContent =
            emergency.length;
    }


    const emergencyCount =
        document.getElementById(
            "trafficEmergencyCount"
        );

    if (emergencyCount) {
        emergencyCount.textContent =
            `${emergency.length} ACTIVE`;
    }


    const greenElement =
        document.getElementById(
            "greenSignals"
        );

    if (greenElement) {
        greenElement.textContent =
            green.length;
    }


    const totalElement =
        document.getElementById(
            "totalAmbulances"
        );

    if (totalElement) {
        totalElement.textContent =
            ambulances.length;
    }


    renderTrafficAmbulances(
        ambulances
    );

    renderSignals(signals);

    updateTrafficMap(
        ambulances
    );
}


// ============================================================
// TRAFFIC AMBULANCE CARDS
// ============================================================

function renderTrafficAmbulances(list) {

    const container =
        document.getElementById(
            "trafficAmbulances"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";


    list.forEach(ambulance => {

        const div =
            document.createElement("div");

        div.className =
            "traffic-ambulance";


        if (ambulance.emergency) {
            div.classList.add("emergency");
        }


        div.innerHTML = `

            <div>

                <strong>
                    🚑 ${ambulance.ambulance_id}
                </strong>

                <span>
                    ${ambulance.status || "--"}
                </span>

            </div>

            <div>
                ${
                    ambulance.emergency
                        ? "🚨 EMERGENCY"
                        : "🟢 NORMAL"
                }
            </div>

        `;

        container.appendChild(div);
    });
}


// ============================================================
// TRAFFIC MAP
// ============================================================

function updateTrafficMap(list) {

    if (!trafficMap) {
        return;
    }

    const activeIds = [];


    list.forEach(ambulance => {

        if (
            ambulance.lat == null ||
            ambulance.lng == null
        ) {
            return;
        }


        // IMPORTANT:
        // Backend field is ambulance_id
        const id =
            ambulance.ambulance_id;

        activeIds.push(id);


        const position = [
            Number(ambulance.lat),
            Number(ambulance.lng)
        ];


        const icon =
            createAmbulanceIcon(
                ambulance.emergency
            );


        if (trafficMarkers[id]) {

            trafficMarkers[id]
                .setLatLng(position);

            trafficMarkers[id]
                .setIcon(icon);

            trafficMarkers[id]
                .setPopupContent(
                    ambulancePopup(
                        ambulance
                    )
                );

        } else {

            trafficMarkers[id] =
                L.marker(
                    position,
                    {
                        icon: icon
                    }
                )
                .addTo(trafficMap)
                .bindPopup(
                    ambulancePopup(
                        ambulance
                    )
                );
        }
    });


    Object.keys(trafficMarkers)
        .forEach(id => {

            if (!activeIds.includes(id)) {

                trafficMap.removeLayer(
                    trafficMarkers[id]
                );

                delete trafficMarkers[id];
            }
        });


    fitMap(
        trafficMap,
        list
    );
}


// ============================================================
// AMBULANCE POPUP
// ============================================================

function ambulancePopup(ambulance) {

    const confidence =
        ambulance.confidence != null
            ? (
                Number(
                    ambulance.confidence
                ) * 100
            ).toFixed(1) + "%"
            : "--";


    const distance =
        ambulance.distance_km != null
            ? `${ambulance.distance_km} km`
            : "--";


    return `

        <div style="
            min-width:250px;
            color:#111;
            font-family:Arial,sans-serif;
        ">

            <h3>
                🚑 ${ambulance.ambulance_id}
            </h3>

            <hr>

            <b>Hospital:</b>
            ${ambulance.hospital_name || "--"}

            <br><br>

            <b>Driver:</b>
            ${ambulance.driver || "--"}

            <br><br>

            <b>Status:</b>
            ${ambulance.status || "--"}

            <br><br>

            <b>Emergency:</b>
            ${
                ambulance.emergency
                    ? "🚨 YES"
                    : "NO"
            }

            <br><br>

            <b>AI Confidence:</b>
            ${confidence}

            <br><br>

            <b>Speed:</b>
            ${ambulance.speed || 0} km/h

            <br><br>

            <b>ETA:</b>
            ${ambulance.eta || "--"}

            <br><br>

            <b>Distance:</b>
            ${distance}

            <br><br>

            <b>Destination:</b>
            ${ambulance.destination || "--"}

            <br><br>

            <b>Signal Priority:</b>
            ${
                ambulance.signal_priority
                    ? "🟢 ACTIVE"
                    : "NO"
            }

        </div>
    `;
}


// ============================================================
// FIT MAP TO AMBULANCES
// ============================================================

function fitMap(map, list) {

    if (!map) {
        return;
    }


    const points =
        list
            .filter(
                ambulance =>
                    ambulance.lat != null &&
                    ambulance.lng != null
            )
            .map(
                ambulance => [
                    Number(ambulance.lat),
                    Number(ambulance.lng)
                ]
            );


    if (points.length === 0) {

        map.setView(
            DEFAULT_CENTER,
            13
        );

        return;
    }


    if (points.length === 1) {

        map.setView(
            points[0],
            14
        );

        return;
    }


    map.fitBounds(
        L.latLngBounds(points),
        {
            padding: [60, 60]
        }
    );
}


// ============================================================
// SIGNALS
// ============================================================

function renderSignals(list) {

    const container =
        document.getElementById(
            "signalList"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";


    list.forEach(signal => {

        const div =
            document.createElement("div");

        div.className =
            "signal-card";


        div.innerHTML = `

            <div>

                <strong>
                    🚦 ${signal.name}
                </strong>

                <span>
                    ${signal.status || "RED"}
                </span>

            </div>

            <div style="
                display:flex;
                gap:8px;
                margin-top:10px;
            ">

                <button
                    onclick="
                        setSignal(
                            '${signal.id}',
                            'GREEN'
                        )
                    "
                >
                    GIVE GREEN
                </button>

                <button
                    onclick="
                        setSignal(
                            '${signal.id}',
                            'RED'
                        )
                    "
                >
                    RED
                </button>

            </div>
        `;

        container.appendChild(div);
    });
}


// ============================================================
// SIGNAL API
// ============================================================

async function setSignal(
    signalId,
    status
) {

    const emergency =
        ambulances.find(
            a => a.emergency
        );


    try {

        const response =
            await fetch(
                `${API}/api/signal`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        signal_id:
                            signalId,

                        status:
                            status,

                        ambulance_id:
                            emergency
                                ? emergency.ambulance_id
                                : null
                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Signal update failed"
            );
        }


        console.log(
            "Signal updated:",
            data
        );

    } catch (error) {

        console.error(error);

        alert(
            error.message
        );
    }
}


// ============================================================
// DRIVER DASHBOARD
// ============================================================

function updateDriver() {

    const ambulance =
        ambulances.find(
            a =>
                a.ambulance_id ===
                currentUser.username
        );


    if (!ambulance) {
        return;
    }


    const name =
        document.getElementById(
            "driverAmbulanceName"
        );

    if (name) {
        name.textContent =
            `Ambulance ID: ${ambulance.ambulance_id}`;
    }


    const status =
        document.getElementById(
            "driverStatus"
        );

    if (status) {
        status.textContent =
            ambulance.status || "AVAILABLE";
    }


    const speed =
        document.getElementById(
            "driverSpeed"
        );

    if (speed) {
        speed.textContent =
            ambulance.speed || 0;
    }


    const eta =
        document.getElementById(
            "driverEta"
        );

    if (eta) {
        eta.textContent =
            ambulance.eta || "--";
    }


    const distance =
        document.getElementById(
            "driverDistance"
        );

    if (distance) {
        distance.textContent =
            ambulance.distance_km != null
                ? `${ambulance.distance_km} km`
                : "--";
    }


    const destination =
        document.getElementById(
            "driverDestination"
        );

    if (destination) {
        destination.textContent =
            ambulance.destination || "--";
    }


    const signal =
        document.getElementById(
            "driverSignal"
        );

    if (signal) {
        signal.textContent =
            ambulance.signal_priority
                ? "YES"
                : "NO";
    }


    const badge =
        document.getElementById(
            "driverEmergencyBadge"
        );


    if (badge) {

        if (ambulance.emergency) {

            badge.textContent =
                "🚨 EMERGENCY";

            badge.classList.add(
                "emergency"
            );

        } else {

            badge.textContent =
                "NORMAL";

            badge.classList.remove(
                "emergency"
            );
        }
    }


    updateDriverMap(
        ambulance
    );
}


// ============================================================
// DRIVER MAP
// ============================================================

function updateDriverMap(ambulance) {

    if (!driverMap) {
        return;
    }


    if (
        ambulance.lat == null ||
        ambulance.lng == null
    ) {
        return;
    }


    const position = [
        Number(ambulance.lat),
        Number(ambulance.lng)
    ];


    const icon =
        createAmbulanceIcon(
            ambulance.emergency
        );


    if (!driverMarker) {

        driverMarker =
            L.marker(
                position,
                {
                    icon: icon
                }
            )
            .addTo(driverMap);

    } else {

        driverMarker.setLatLng(
            position
        );

        driverMarker.setIcon(
            icon
        );
    }


    driverMarker.bindPopup(
        ambulancePopup(
            ambulance
        )
    );


    driverMap.setView(
        position,
        15
    );
}


// ============================================================
// STARTUP
// ============================================================

window.addEventListener(
    "load",
    async () => {

        console.log(
            "RescueRoute AI frontend loaded"
        );


        if (typeof L === "undefined") {

            console.error(
                "LEAFLET NOT LOADED"
            );

            return;
        }


        console.log(
            "Leaflet loaded:",
            L.version
        );


        const saved =
            localStorage.getItem(
                "rescue_user"
            );


        if (saved) {

            try {

                currentUser =
                    JSON.parse(saved);

                await loadAmbulances();

                showApplication();

            } catch (error) {

                console.error(error);

                localStorage.removeItem(
                    "rescue_user"
                );
            }
        }
    }
);