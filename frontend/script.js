const API_URL =
    "http://127.0.0.1:5050/api/status";


let currentRole = null;


/* =====================================================
   LOGIN
===================================================== */

function login() {

    const role =
        document.getElementById(
            "roleSelect"
        ).value;

    const username =
        document.getElementById(
            "username"
        ).value.trim();

    const password =
        document.getElementById(
            "password"
        ).value.trim();

    const error =
        document.getElementById(
            "loginError"
        );


    /*
     * Demo credentials
     *
     * Admin:
     * admin / admin123
     *
     * Traffic Police:
     * traffic / traffic123
     *
     * Hospital:
     * hospital / hospital123
     */

    const credentials = {

        admin: {
            username: "admin",
            password: "admin123"
        },

        traffic: {
            username: "traffic",
            password: "traffic123"
        },

        hospital: {
            username: "hospital",
            password: "hospital123"
        }
    };


    if (
        username !==
        credentials[role].username
        ||
        password !==
        credentials[role].password
    ) {

        error.textContent =
            "Invalid username or password.";

        return;
    }


    currentRole = role;

    sessionStorage.setItem(
        "rescueRole",
        role
    );


    error.textContent = "";


    document
        .getElementById("loginPage")
        .classList.add("hidden");


    document
        .getElementById("appPage")
        .classList.remove("hidden");


    setupDashboard();
}


/* =====================================================
   LOGOUT
===================================================== */

function logout() {

    sessionStorage.removeItem(
        "rescueRole"
    );

    currentRole = null;


    document
        .getElementById("appPage")
        .classList.add("hidden");


    document
        .getElementById("loginPage")
        .classList.remove("hidden");


    document.getElementById(
        "username"
    ).value = "";

    document.getElementById(
        "password"
    ).value = "";
}


/* =====================================================
   DASHBOARD SETUP
===================================================== */

function setupDashboard() {

    const admin =
        document.getElementById(
            "adminDashboard"
        );

    const traffic =
        document.getElementById(
            "trafficDashboard"
        );

    const hospital =
        document.getElementById(
            "hospitalDashboard"
        );


    admin.classList.add("hidden");

    traffic.classList.add("hidden");

    hospital.classList.add("hidden");


    const nav =
        document.getElementById(
            "sidebarNav"
        );


    nav.innerHTML = "";


    const roleText = {

        admin:
            "Administrator",

        traffic:
            "Traffic Police",

        hospital:
            "Hospital"
    };


    document.getElementById(
        "currentRole"
    ).textContent =
        roleText[currentRole];


    if (currentRole === "admin") {

        admin.classList.remove(
            "hidden"
        );

        document.getElementById(
            "pageTitle"
        ).textContent =
            "Emergency Control Center";


        createNav(
            [
                "Dashboard",
                "AI Detection",
                "Real Route",
                "Traffic Analysis",
                "Signal Priority"
            ]
        );

    }


    if (currentRole === "traffic") {

        traffic.classList.remove(
            "hidden"
        );

        document.getElementById(
            "pageTitle"
        ).textContent =
            "Traffic Police Control Center";


        createNav(
            [
                "Traffic Dashboard",
                "Vehicle Monitoring",
                "Signal Priority",
                "Emergency Alerts"
            ]
        );

    }


    if (currentRole === "hospital") {

        hospital.classList.remove(
            "hidden"
        );

        document.getElementById(
            "pageTitle"
        ).textContent =
            "Hospital Emergency Desk";


        createNav(
            [
                "Emergency Dashboard",
                "Incoming Ambulance",
                "Route & ETA",
                "Arrival Status"
            ]
        );

    }
}


/* =====================================================
   SIDEBAR NAV
===================================================== */

function createNav(items) {

    const nav =
        document.getElementById(
            "sidebarNav"
        );


    items.forEach(
        (item, index) => {

            const button =
                document.createElement(
                    "button"
                );

            button.textContent =
                item;

            if (index === 0) {

                button.classList.add(
                    "active"
                );
            }

            nav.appendChild(
                button
            );
        }
    );
}


/* =====================================================
   FETCH LIVE DATA
===================================================== */

async function updateDashboard() {

    if (!currentRole) {
        return;
    }


    try {

        const response =
            await fetch(API_URL);


        if (!response.ok) {
            throw new Error(
                "API unavailable"
            );
        }


        const data =
            await response.json();


        if (currentRole === "admin") {

            updateAdmin(
                data
            );

        }


        if (currentRole === "traffic") {

            updateTraffic(
                data
            );

        }


        if (currentRole === "hospital") {

            updateHospital(
                data
            );
        }

    }

    catch (error) {

        console.error(
            "Dashboard API error:",
            error
        );
    }
}


/* =====================================================
   ADMIN
===================================================== */

function updateAdmin(data) {

    const emergency =
        Boolean(
            data.emergency_mode
        );


    document.getElementById(
        "adminAmbulance"
    ).textContent =
        emergency
            ? "DETECTED"
            : "NOT DETECTED";


    document.getElementById(
        "adminConfidence"
    ).textContent =
        Math.round(
            Number(
                data.confidence || 0
            ) * 100
        ) + "%";


    document.getElementById(
        "adminTraffic"
    ).textContent =
        data.traffic_level ||
        "LOW";


    document.getElementById(
        "adminTrafficScore"
    ).textContent =
        "Score: " +
        (
            data.traffic_score || 0
        );


    document.getElementById(
        "adminSignal"
    ).textContent =
        data.signal_priority
            ? "ACTIVE"
            : "INACTIVE";


    const badge =
        document.getElementById(
            "adminEmergencyBadge"
        );


    if (emergency) {

        badge.textContent =
            "EMERGENCY ACTIVE";

        badge.className =
            "status-badge emergency";

    }

    else {

        badge.textContent =
            "NORMAL";

        badge.className =
            "status-badge normal";
    }


    const vehicles =
        data.vehicle_counts || {};


    document.getElementById(
        "adminCars"
    ).textContent =
        vehicles.Car || 0;


    document.getElementById(
        "adminMotorcycles"
    ).textContent =
        vehicles.Motorcycle || 0;


    document.getElementById(
        "adminBuses"
    ).textContent =
        vehicles.Bus || 0;


    document.getElementById(
        "adminTrucks"
    ).textContent =
        vehicles.Truck || 0;


    document.getElementById(
        "adminTotalVehicles"
    ).textContent =
        (
            data.total_vehicles || 0
        )
        + " vehicles";


    document.getElementById(
        "adminRoute"
    ).textContent =
        data.route ||
        "Waiting for route...";


    document.getElementById(
        "adminDistance"
    ).textContent =
        Number(
            data.distance || 0
        ).toFixed(2)
        + " km";


    document.getElementById(
        "adminEta"
    ).textContent =
        data.eta || "--";


    document.getElementById(
        "adminDestination"
    ).textContent =
        data.destination || "--";
}


/* =====================================================
   TRAFFIC POLICE
===================================================== */

function updateTraffic(data) {

    const vehicles =
        data.vehicle_counts || {};


    const emergency =
        Boolean(
            data.emergency_mode
        );


    document.getElementById(
        "policeTraffic"
    ).textContent =
        data.traffic_level ||
        "LOW";


    document.getElementById(
        "policeTotal"
    ).textContent =
        data.total_vehicles || 0;


    document.getElementById(
        "policeAmbulance"
    ).textContent =
        emergency
            ? "DETECTED"
            : "NOT DETECTED";


    document.getElementById(
        "policeSignal"
    ).textContent =
        data.signal_priority
            ? "ACTIVE"
            : "INACTIVE";


    document.getElementById(
        "policeCars"
    ).textContent =
        vehicles.Car || 0;


    document.getElementById(
        "policeMotorcycles"
    ).textContent =
        vehicles.Motorcycle || 0;


    document.getElementById(
        "policeBuses"
    ).textContent =
        vehicles.Bus || 0;


    document.getElementById(
        "policeTrucks"
    ).textContent =
        vehicles.Truck || 0;


    updateBar(
        "carBar",
        vehicles.Car || 0
    );


    updateBar(
        "motorcycleBar",
        vehicles.Motorcycle || 0
    );


    updateBar(
        "busBar",
        vehicles.Bus || 0
    );


    updateBar(
        "truckBar",
        vehicles.Truck || 0
    );


    document.getElementById(
        "policeScore"
    ).textContent =
        (
            data.traffic_score || 0
        )
        + " / 100";


    document.getElementById(
        "policeSignalLarge"
    ).textContent =
        data.signal_priority
            ? "SIGNAL PRIORITY ACTIVE"
            : "SIGNAL PRIORITY INACTIVE";


    const badge =
        document.getElementById(
            "trafficEmergencyBadge"
        );


    if (emergency) {

        badge.textContent =
            "AMBULANCE DETECTED";

        badge.className =
            "status-badge emergency";

    }

    else {

        badge.textContent =
            "NORMAL";

        badge.className =
            "status-badge normal";
    }
}


/* =====================================================
   BAR
===================================================== */

function updateBar(
    id,
    value
) {

    const max =
        20;

    const percentage =
        Math.min(
            100,
            (value / max) * 100
        );


    document.getElementById(
        id
    ).style.width =
        percentage + "%";
}


/* =====================================================
   HOSPITAL
===================================================== */

function updateHospital(data) {

    const emergency =
        Boolean(
            data.emergency_mode
        );


    document.getElementById(
        "hospitalAmbulance"
    ).textContent =
        emergency
            ? "DETECTED"
            : "NOT DETECTED";


    document.getElementById(
        "hospitalEta"
    ).textContent =
        data.eta || "--";


    document.getElementById(
        "hospitalDistance"
    ).textContent =
        Number(
            data.distance || 0
        ).toFixed(2)
        + " km";


    document.getElementById(
        "hospitalConfidence"
    ).textContent =
        Math.round(
            Number(
                data.confidence || 0
            ) * 100
        ) + "%";


    document.getElementById(
        "hospitalDestination"
    ).textContent =
        data.destination ||
        "Waiting for ambulance...";


    document.getElementById(
        "hospitalRoute"
    ).textContent =
        data.route ||
        "Waiting for ambulance route...";


    document.getElementById(
        "arrivalStatus"
    ).textContent =
        emergency
            ? "AMBULANCE EN ROUTE"
            : "No incoming ambulance";


    const badge =
        document.getElementById(
            "hospitalEmergencyBadge"
        );


    if (emergency) {

        badge.textContent =
            "AMBULANCE EN ROUTE";

        badge.className =
            "status-badge emergency";

    }

    else {

        badge.textContent =
            "NO AMBULANCE";

        badge.className =
            "status-badge normal";
    }
}


/* =====================================================
   CLOCK
===================================================== */

function updateClock() {

    const now =
        new Date();


    document.getElementById(
        "dateTime"
    ).textContent =
        now.toLocaleString(
            "en-IN",
            {
                day: "2-digit",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        );
}


/* =====================================================
   SESSION RESTORE
===================================================== */

window.addEventListener(
    "DOMContentLoaded",
    () => {

        const savedRole =
            sessionStorage.getItem(
                "rescueRole"
            );


        if (savedRole) {

            currentRole =
                savedRole;


            document
                .getElementById(
                    "loginPage"
                )
                .classList.add(
                    "hidden"
                );


            document
                .getElementById(
                    "appPage"
                )
                .classList.remove(
                    "hidden"
                );


            setupDashboard();
        }


        updateClock();

        setInterval(
            updateClock,
            1000
        );

        setInterval(
            updateDashboard,
            1000
        );

    }
);