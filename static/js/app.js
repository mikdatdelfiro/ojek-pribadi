"use strict";


// ============================================================
// OJEK PRIBADI
// CUSTOMER APP
// Customer Language System - Final Copy
// ============================================================


// ============================================================
// DOM HELPER
// ============================================================

function getElement(
    id,
    required = true
) {

    const element =
        document.getElementById(id);


    if (
        required
        &&
        !element
    ) {

        console.error(
            `[APP] Element #${id} tidak ditemukan.`
        );

    }


    return element;

}


// ============================================================
// DOM ELEMENTS
// ============================================================


// ------------------------------------------------------------
// BOOKING FORM
// ------------------------------------------------------------

const bookingForm =
    getElement(
        "bookingForm"
    );

const pickupInput =
    getElement(
        "pickup"
    );

const destinationInput =
    getElement(
        "destination"
    );

const noteInput =
    getElement(
        "note"
    );


// ------------------------------------------------------------
// GPS
// ------------------------------------------------------------

const useLocationButton =
    getElement(
        "useLocationButton"
    );

const locationButtonText =
    getElement(
        "locationButtonText"
    );

// ------------------------------------------------------------
// DESTINATION MAP PICKER
// ------------------------------------------------------------

const destinationMapButton =
    getElement(
        "destinationMapButton",
        false
    );

const destinationMapStatus =
    getElement(
        "destinationMapStatus",
        false
    );

const destinationMapModal =
    getElement(
        "destinationMapModal",
        false
    );

const destinationMapClose =
    getElement(
        "destinationMapClose",
        false
    );

const destinationMapConfirm =
    getElement(
        "destinationMapConfirm",
        false
    );

const destinationMapCanvas =
    getElement(
        "destinationMapCanvas",
        false
    );

const destinationMapMessage =
    getElement(
        "destinationMapMessage",
        false
    );

    const destinationAddressDetail =
    getElement(
        "destinationAddressDetail",
        false
    );


const destinationAddressValue =
    getElement(
        "destinationAddressValue",
        false
    );


const destinationAddressCoordinates =
    getElement(
        "destinationAddressCoordinates",
        false
    );


const destinationGoogleMapsLink =
    getElement(
        "destinationGoogleMapsLink",
        false
    );

const destinationAddressDetailInput =
    getElement(
        "destinationAddressDetailInput",
        false
    );

// ------------------------------------------------------------
// CHECK FARE
// ------------------------------------------------------------

const checkFareButton =
    getElement(
        "checkFareButton"
    );

const buttonText =
    getElement(
        "buttonText"
    );

const buttonArrow =
    getElement(
        "buttonArrow"
    );

const formMessage =
    getElement(
        "formMessage"
    );


// ------------------------------------------------------------
// FARE RESULT
// ------------------------------------------------------------

const fareResult =
    getElement(
        "fareResult"
    );

const resultPickup =
    getElement(
        "resultPickup"
    );

const resultDestination =
    getElement(
        "resultDestination"
    );

const resultDistance =
    getElement(
        "resultDistance"
    );

const resultDuration =
    getElement(
        "resultDuration"
    );

const resultFare =
    getElement(
        "resultFare"
    );


// ------------------------------------------------------------
// ORDER
// ------------------------------------------------------------

const orderButton =
    getElement(
        "orderButton"
    );

const customerPanel =
    getElement(
        "customerPanel"
    );

const closeCustomerPanel =
    getElement(
        "closeCustomerPanel"
    );

const customerName =
    getElement(
        "customerName"
    );

const customerWhatsapp =
    getElement(
        "customerWhatsapp"
    );

const paymentMethodInputs =
    document.querySelectorAll(
        'input[name="paymentMethod"]'
    );

const confirmOrderButton =
    getElement(
        "confirmOrderButton"
    );

const confirmOrderText =
    getElement(
        "confirmOrderText"
    );

const orderMessage =
    getElement(
        "orderMessage"
    );


// ------------------------------------------------------------
// SUCCESS
// ------------------------------------------------------------

const successOverlay =
    getElement(
        "successOverlay"
    );

const successOrderCode =
    getElement(
        "successOrderCode"
    );

const successButton =
    getElement(
        "successButton"
    );


// ------------------------------------------------------------
// SERVICE STATUS
// ------------------------------------------------------------

const customerServiceStatus =
    getElement(
        "customerServiceStatus",
        false
    );

const customerServiceLabel =
    getElement(
        "customerServiceLabel",
        false
    );

const customerServiceDescription =
    getElement(
        "customerServiceDescription",
        false
    );


// ------------------------------------------------------------
// HEADER SERVICE BADGE
// OPTIONAL
// ------------------------------------------------------------

const headerServiceBadge =
    getElement(
        "headerServiceBadge",
        false
    );

const headerServiceText =
    getElement(
        "headerServiceText",
        false
    );


// ============================================================
// APPLICATION STATE
// ============================================================

let pickupCoordinates =
    null;


let destinationCoordinates =
    null;


let destinationMap =
    null;


let destinationMarker =
    null;


let destinationDraftCoordinates =
    null;

let destinationDraftAddress =
    "";    

let currentRoute =
    null;


let orderSubmitting =
    false;

let latestReviewToken =
    "";

let serviceOpen =
    customerServiceStatus
        ? (
            customerServiceStatus
                .dataset
                .serviceOpen
            === "true"
        )
        : true;

// ============================================================
// DESTINATION COORDINATE BRIDGE
// ============================================================

window.OjekDestination =
    window.OjekDestination
    ||
    {
        coordinates:
            null,

        address:
            ""
    };

    if (
    typeof window.OjekDestination.detail
    !== "string"
) {

    window.OjekDestination.detail =
        "";

}


// ============================================================
// FORMAT RUPIAH
// ============================================================

function formatRupiah(
    value
) {

    return new Intl.NumberFormat(
        "id-ID",
        {
            style:
                "currency",

            currency:
                "IDR",

            minimumFractionDigits:
                0,

            maximumFractionDigits:
                0
        }
    ).format(
        value
    );

}


// ============================================================
// SHORT ADDRESS
// ============================================================

function shortenLocation(
    location
) {

    if (!location) {

        return "-";

    }


    return location
        .split(",")
        .slice(
            0,
            3
        )
        .join(",")
        .trim();

}


// ============================================================
// MAIN MESSAGE
// ============================================================

function showMessage(
    message
) {

    if (!formMessage) {

        return;

    }


    formMessage.textContent =
        message;


    formMessage.classList.add(
        "show"
    );

}


function hideMessage() {

    if (!formMessage) {

        return;

    }


    formMessage.textContent =
        "";


    formMessage.classList.remove(
        "show"
    );

}


// ============================================================
// ORDER MESSAGE
// ============================================================

function showOrderMessage(
    message
) {

    if (!orderMessage) {

        return;

    }


    orderMessage.textContent =
        message;


    orderMessage.classList.add(
        "show"
    );

}


function hideOrderMessage() {

    if (!orderMessage) {

        return;

    }


    orderMessage.textContent =
        "";


    orderMessage.classList.remove(
        "show"
    );

}


// ============================================================
// SERVICE STATUS
// ============================================================

function updateOrderAvailability() {

    // Tombol buka panel order.
    if (orderButton) {

        orderButton.disabled =
            !serviceOpen;

    }


    // Tombol konfirmasi pesanan.
    if (confirmOrderButton) {

        confirmOrderButton.disabled =
            (
                !serviceOpen
                ||
                orderSubmitting
            );

    }

}


// ============================================================
// UPDATE CUSTOMER SERVICE UI
// ============================================================

function updateCustomerServiceUI(
    isOpen
) {

    serviceOpen =
        Boolean(
            isOpen
        );


    // --------------------------------------------------------
    // MAIN STATUS CARD
    // --------------------------------------------------------

    if (customerServiceStatus) {

        customerServiceStatus.dataset.serviceOpen =
            serviceOpen
                ? "true"
                : "false";


        customerServiceStatus
            .classList
            .toggle(
                "is-open",
                serviceOpen
            );


        customerServiceStatus
            .classList
            .toggle(
                "is-closed",
                !serviceOpen
            );

    }


    // --------------------------------------------------------
    // MAIN STATUS LABEL
    // --------------------------------------------------------

    if (customerServiceLabel) {

        customerServiceLabel.textContent =
            serviceOpen
                ? "Siap menerima perjalanan"
                : "Sedang tidak menerima perjalanan";

    }


    // --------------------------------------------------------
    // MAIN STATUS DESCRIPTION
    // --------------------------------------------------------

    if (customerServiceDescription) {

    customerServiceDescription.textContent =
        serviceOpen
            ? (
                "Saya siap menjemput Anda "
                +
                "sekarang."
            )
            : (
                "Layanan sedang tutup. "
                +
                "Silakan coba kembali nanti."
            );

}


    // --------------------------------------------------------
    // HEADER BADGE
    // --------------------------------------------------------

    if (headerServiceBadge) {

        headerServiceBadge
            .classList
            .toggle(
                "is-open",
                serviceOpen
            );


        headerServiceBadge
            .classList
            .toggle(
                "is-closed",
                !serviceOpen
            );

    }


    if (headerServiceText) {

        headerServiceText.textContent =
            serviceOpen
                ? "Aktif"
                : "Tutup";

    }


    // --------------------------------------------------------
    // ORDER BUTTONS
    // --------------------------------------------------------

    updateOrderAvailability();


    // Jika layanan ditutup saat panel order terbuka,
    // tampilkan informasi kepada pelanggan.
    if (
        !serviceOpen
        &&
        customerPanel
        &&
        customerPanel.classList.contains(
            "is-open"
        )        
    ) {

        showOrderMessage(
            "Layanan sedang tutup. Pesanan belum dapat dibuat saat ini."
        );

    }

}


// ============================================================
// FETCH SERVICE STATUS
// ============================================================

async function refreshServiceStatus() {

    try {

        const response =
            await fetch(
                "/api/service-status",
                {
                    method:
                        "GET",

                    cache:
                        "no-store",

                    headers: {

                        "Accept":
                            "application/json"

                    }
                }
            );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (
            !data
            ||
            data.success !== true
        ) {

            throw new Error(
                "Respons status layanan tidak valid."
            );

        }


        updateCustomerServiceUI(
            data.service_open
        );

    }

    catch (error) {

        console.warn(
            "[SERVICE STATUS]",
            error
        );

    }

}

// ============================================================
// CUSTOMER PANEL STATE
// CLEAN FIX
// ============================================================

function setCustomerPanelOpen(
    open
) {

    if (!customerPanel) {

        return;

    }


    const shouldOpen =
        Boolean(
            open
        );


    customerPanel.classList.toggle(
        "is-open",
        shouldOpen
    );


    customerPanel.setAttribute(
        "aria-hidden",
        shouldOpen
            ? "false"
            : "true"
    );

}

// ============================================================
// RESET CURRENT FARE
// ============================================================

function invalidateFare() {

    currentRoute =
        null;


    if (fareResult) {

        fareResult.classList.remove(
            "show"
        );

    }


    setCustomerPanelOpen(
            false
    );
}


// ============================================================
// GPS BUTTON STATE
// ============================================================

function setLocationLoading(
    loading
) {

    if (
        !useLocationButton
        ||
        !locationButtonText
    ) {

        return;

    }


    useLocationButton.disabled =
        loading;


    if (loading) {

        useLocationButton.classList.add(
            "location-loading"
        );


        locationButtonText.textContent =
            "Mencari lokasi Anda...";

    }

    else {

        useLocationButton.classList.remove(
            "location-loading"
        );

    }

}


// ============================================================
// GPS FALLBACK
// ============================================================

function setCoordinateFallback(
    latitude,
    longitude
) {

    if (!pickupInput) {

        return;

    }


    pickupInput.value =
        (
            "Lokasi saya "
            +
            `(${latitude.toFixed(5)}, `
            +
            `${longitude.toFixed(5)})`
        );

}


// ============================================================
// GPS SUCCESS
// ============================================================

async function handleLocationSuccess(
    position
) {

    const latitude =
        position.coords.latitude;


    const longitude =
        position.coords.longitude;


    pickupCoordinates = {

        lat:
            latitude,

        lon:
            longitude

    };


    try {

        const response =
            await fetch(
                "/api/reverse-geocode",
                {

                    method:
                        "POST",


                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },


                    body:
                        JSON.stringify(
                            {

                                lat:
                                    latitude,

                                lon:
                                    longitude

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (
            response.ok
            &&
            data.success
            &&
            data.location
        ) {

            if (pickupInput) {

                pickupInput.value =
                    data.location
                        .display_name;

            }

        }

        else {

            setCoordinateFallback(
                latitude,
                longitude
            );

        }


        if (locationButtonText) {

            locationButtonText.textContent =
                "Lokasi berhasil ditemukan";

        }


        if (useLocationButton) {

            useLocationButton.classList.add(
                "location-success"
            );

        }


        invalidateFare();

    }

    catch (error) {

        console.error(
            "[GPS] Reverse geocode gagal:",
            error
        );


        setCoordinateFallback(
            latitude,
            longitude
        );


        if (locationButtonText) {

            locationButtonText.textContent =
                "Lokasi GPS berhasil digunakan";

        }


        if (useLocationButton) {

            useLocationButton.classList.add(
                "location-success"
            );

        }

    }

    finally {

        setLocationLoading(
            false
        );

    }

}


// ============================================================
// GPS ERROR
// ============================================================

function handleLocationError(
    error
) {

    setLocationLoading(
        false
    );


    let message =
        "Lokasi belum dapat ditemukan.";


    switch (
        error.code
    ) {

        case 1:

            message =
                (
                    "Izin lokasi belum diberikan. "
                    +
                    "Anda tetap dapat memasukkan lokasi secara manual."
                );

            break;


        case 2:

            message =
                (
                    "Lokasi perangkat belum tersedia. "
                    +
                    "Pastikan layanan lokasi di perangkat Anda aktif."
                );

            break;


        case 3:

            message =
                (
                    "Pencarian lokasi membutuhkan waktu terlalu lama. "
                    +
                    "Silakan coba lagi."
                );

            break;

    }


    showMessage(
        message
    );


    console.error(
        "[GPS]",
        error
    );

}


// ============================================================
// USE CURRENT LOCATION
// ============================================================

if (useLocationButton) {

    useLocationButton.addEventListener(
        "click",
        function () {

            hideMessage();


            if (
                !navigator.geolocation
            ) {

                showMessage(
                    "Browser ini belum mendukung akses lokasi. Masukkan lokasi jemput secara manual."
                );

                return;

            }


            setLocationLoading(
                true
            );


            navigator.geolocation
                .getCurrentPosition(

                    handleLocationSuccess,

                    handleLocationError,

                    {

                        enableHighAccuracy:
                            true,

                        timeout:
                            20000,

                        maximumAge:
                            0

                    }

                );

        }
    );

}


// ============================================================
// PICKUP MANUAL EDIT
// ============================================================

if (pickupInput) {

    pickupInput.addEventListener(
        "input",
        function () {

            // Koordinat GPS tidak digunakan lagi
            // jika pengguna mengetik alamat manual.
            pickupCoordinates =
                null;


            if (locationButtonText) {

                locationButtonText.textContent =
                    "Tentukan titik jemput secara otomatis";

            }


            if (useLocationButton) {

                useLocationButton.classList.remove(
                    "location-success"
                );

            }


            invalidateFare();

        }
    );

}

// ============================================================
// DESTINATION MAP PICKER
// ============================================================

function setDestinationMapStatus(
    message,
    selected = false
) {

    if (destinationMapStatus) {

        destinationMapStatus.textContent =
            message;

    }


    if (destinationMapButton) {

        destinationMapButton
            .classList
            .toggle(
                "is-selected",
                Boolean(
                    selected
                )
            );

    }

}


function setDestinationMapMessage(
    message
) {

    if (!destinationMapMessage) {

        return;

    }


    destinationMapMessage.textContent =
        message;

}

// ============================================================
// DESTINATION ADDRESS DETAIL
// ============================================================

function renderDestinationAddressDetail(
    address,
    latitude,
    longitude
) {

    const lat =
        Number(
            latitude
        );


    const lon =
        Number(
            longitude
        );


    if (
        !Number.isFinite(
            lat
        )
        ||
        !Number.isFinite(
            lon
        )
    ) {

        return;

    }


    const cleanAddress =
        String(
            address
            || "Titik tujuan dipilih"
        ).trim();


    if (destinationAddressValue) {

        destinationAddressValue.textContent =
            cleanAddress;

    }


    if (destinationAddressCoordinates) {

        destinationAddressCoordinates.textContent =
            (
                `${lat.toFixed(6)}, `
                +
                `${lon.toFixed(6)}`
            );

    }


    if (destinationGoogleMapsLink) {

        const coordinates =
            `${lat},${lon}`;


        destinationGoogleMapsLink.href =
            (
                "https://www.google.com/maps/search/"
                +
                "?api=1&query="
                +
                encodeURIComponent(
                    coordinates
                )
            );

    }


    if (destinationAddressDetail) {

        destinationAddressDetail.hidden =
            false;

    }

}


function createDestinationMarkerIcon() {

    if (
        !window.L
        ||
        !window.L.divIcon
    ) {

        return null;

    }


    return window.L.divIcon(
        {

            className:
                "destination-selected-marker",

            html:
                "<span><i>●</i></span>",

            iconSize:
                [
                    42,
                    42
                ],

            iconAnchor:
                [
                    10,
                    38
                ]

        }
    );

}


function setDestinationDraftPoint(
    latitude,
    longitude,
    moveMap = false
) {

    if (!destinationMap) {

        return;

    }


    const lat =
        Number(
            latitude
        );


    const lon =
        Number(
            longitude
        );


    if (
        !Number.isFinite(
            lat
        )
        ||
        !Number.isFinite(
            lon
        )
        ||
        lat < -90
        ||
        lat > 90
        ||
        lon < -180
        ||
        lon > 180
    ) {

        return;

    }


    destinationDraftCoordinates = {

        lat:
            lat,

        lon:
            lon

    };


    if (destinationMarker) {

        destinationMarker.setLatLng(
            [
                lat,
                lon
            ]
        );

    }

    else {

        const markerOptions = {};


        const markerIcon =
            createDestinationMarkerIcon();


        if (markerIcon) {

            markerOptions.icon =
                markerIcon;

        }


        destinationMarker =
            window.L
                .marker(
                    [
                        lat,
                        lon
                    ],
                    markerOptions
                )
                .addTo(
                    destinationMap
                );

    }


    if (moveMap) {

        destinationMap.setView(
            [
                lat,
                lon
            ],
            Math.max(
                destinationMap.getZoom(),
                16
            )
        );

    }


    if (destinationMapConfirm) {

        destinationMapConfirm.disabled =
            false;

    }


    setDestinationMapMessage(
        (
            "Titik dipilih: "
            +
            `${lat.toFixed(6)}, `
            +
            `${lon.toFixed(6)}. `
            +
            "Tekan “Gunakan Titik Ini”."
        )
    );

}


function initializeDestinationMap() {

    if (
        destinationMap
        ||
        !destinationMapCanvas
    ) {

        return Boolean(
            destinationMap
        );

    }


    if (
        !window.L
        ||
        typeof window.L.map
        !== "function"
    ) {

        setDestinationMapMessage(
            "Peta belum dapat dimuat. Periksa koneksi internet lalu coba kembali."
        );


        return false;

    }


    const initialCoordinates =
        destinationCoordinates
        ||
        pickupCoordinates;


    const initialLat =
        initialCoordinates
            ? initialCoordinates.lat
            : -4.10;


    const initialLon =
        initialCoordinates
            ? initialCoordinates.lon
            : 104.65;


    const initialZoom =
        initialCoordinates
            ? 16
            : 11;


    destinationMap =
        window.L.map(
            destinationMapCanvas,
            {
                zoomControl:
                    true,

                attributionControl:
                    true
            }
        )
        .setView(
            [
                initialLat,
                initialLon
            ],
            initialZoom
        );


    // ============================================================
// SATELLITE HYBRID MAP
// SATELLITE + ROAD + PLACE LABELS
// ============================================================

const satelliteLayer =
    window.L.tileLayer(
        (
            "https://server.arcgisonline.com/"
            +
            "ArcGIS/rest/services/"
            +
            "World_Imagery/MapServer/"
            +
            "tile/{z}/{y}/{x}"
        ),
        {
            maxZoom:
                20,

            attribution:
                (
                    "Tiles © Esri"
                )
        }
    );


const labelLayer =
    window.L.tileLayer(
        (
            "https://services.arcgisonline.com/"
            +
            "ArcGIS/rest/services/"
            +
            "Reference/"
            +
            "World_Boundaries_and_Places/"
            +
            "MapServer/tile/{z}/{y}/{x}"
        ),
        {
            maxZoom:
                20,

            pane:
                "overlayPane"
        }
    );


satelliteLayer.addTo(
    destinationMap
);


labelLayer.addTo(
    destinationMap
);


destinationMap.on(
    "click",
    async function (
        event
    ) {

        if (
            !event
            ||
            !event.latlng
        ) {

            return;

        }


        const latitude =
            event.latlng.lat;


        const longitude =
            event.latlng.lng;


        setDestinationDraftPoint(
            latitude,
            longitude,
            false
        );


        setDestinationMapMessage(
            "Mencari detail alamat titik tujuan..."
        );


        const address =
            await reverseGeocodeDestinationPoint(
                latitude,
                longitude
            );


        destinationDraftAddress =
            address;


        renderDestinationAddressDetail(
            (
                address
                ||
                "Titik tujuan yang dipilih"
            ),
            latitude,
            longitude
        );


        setDestinationMapMessage(
            "Periksa alamat lalu tekan “Gunakan Titik Ini”."
        );

    }
);


return true;

}


// ============================================================
// SEARCH DESTINATION ADDRESS
// ============================================================

async function geocodeDestinationText(
    query
) {

    query =
        String(
            query
            || ""
        ).trim();


    if (
        query.length
        <
        3
    ) {

        return null;

    }


    try {

        const response =
            await fetch(
                "/api/geocode-location",
                {

                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {
                                query:
                                    query
                            }
                        )

                }
            );


        const data =
            await response.json();


        if (
            !response.ok
            ||
            !data
            ||
            data.success !== true
            ||
            !data.location
        ) {

            return null;

        }


        const latitude =
            Number(
                data.location.lat
            );


        const longitude =
            Number(
                data.location.lon
            );


        if (
            !Number.isFinite(
                latitude
            )
            ||
            !Number.isFinite(
                longitude
            )
        ) {

            return null;

        }


        return {

            lat:
                latitude,

            lon:
                longitude,

            display_name:
                String(
                    data.location.display_name
                    || query
                ).trim(),

        };

    }

    catch (error) {

        console.warn(
            "[DESTINATION SEARCH]",
            error
        );


        return null;

    }

}

// ============================================================
// FOCUS MAP TO DESTINATION INPUT
// ============================================================

async function focusMapToDestinationInput() {

    if (
        !destinationMap
        ||
        !destinationInput
    ) {

        return false;

    }


    // Jika sebelumnya sudah ada koordinat valid,
    // langsung gunakan.
    if (destinationCoordinates) {

        setDestinationDraftPoint(
            destinationCoordinates.lat,
            destinationCoordinates.lon,
            true
        );


        const address =
            await reverseGeocodeDestinationPoint(
                destinationCoordinates.lat,
                destinationCoordinates.lon
            );


        destinationDraftAddress =
            address;


        renderDestinationAddressDetail(
            (
                address
                ||
                destinationInput.value.trim()
            ),
            destinationCoordinates.lat,
            destinationCoordinates.lon
        );


        return true;

    }


    const query =
        destinationInput
            .value
            .trim();


    if (
        query.length
        <
        3
    ) {

        return false;

    }


    setDestinationMapMessage(
        "Mencari alamat tujuan..."
    );


    const location =
        await geocodeDestinationText(
            query
        );


    if (!location) {

        setDestinationMapMessage(
            (
                "Alamat belum ditemukan otomatis. "
                +
                "Silakan sentuh titik tujuan langsung pada peta."
            )
        );


        return false;

    }


    destinationDraftAddress =
        location.display_name;


    setDestinationDraftPoint(
        location.lat,
        location.lon,
        true
    );


    renderDestinationAddressDetail(
        location.display_name,
        location.lat,
        location.lon
    );


    setDestinationMapMessage(
        "Peta diarahkan ke alamat tujuan yang ditemukan."
    );


    return true;

}

async function openDestinationMap() {

    hideMessage();


    if (!destinationMapModal) {

        return;

    }


    destinationMapModal
        .classList
        .add(
            "is-open"
        );


    destinationMapModal.setAttribute(
        "aria-hidden",
        "false"
    );


    document.body.classList.add(
        "no-scroll"
    );


    window.setTimeout(
    async function () {

            if (!initializeDestinationMap()) {

                return;

            }


            destinationMap.invalidateSize();

            const destinationFound =
                await focusMapToDestinationInput();


            if (destinationFound) {

                return;

            }


            const preferredCoordinates =
                destinationCoordinates
                ||
                pickupCoordinates;


            if (preferredCoordinates) {

                setDestinationDraftPoint(
                    preferredCoordinates.lat,
                    preferredCoordinates.lon,
                    true
                );

            }

            else if (
                navigator.geolocation
            ) {

                setDestinationMapMessage(
                    "Mencari area Anda agar peta lebih mudah digunakan..."
                );


                navigator.geolocation
                    .getCurrentPosition(
                        function (
                            position
                        ) {

                            if (!destinationMap) {

                                return;

                            }


                            destinationMap.setView(
                                [
                                    position.coords.latitude,
                                    position.coords.longitude
                                ],
                                15
                            );


                            setDestinationMapMessage(
                                "Sentuh titik tujuan yang tepat pada peta."
                            );

                        },

                        function () {

                            setDestinationMapMessage(
                                "Sentuh titik tujuan yang tepat pada peta."
                            );

                        },

                        {
                            enableHighAccuracy:
                                true,

                            timeout:
                                8000,

                            maximumAge:
                                60000
                        }
                    );

            }

            else {

                setDestinationMapMessage(
                    "Sentuh titik tujuan yang tepat pada peta."
                );

            }

        },
        80
    );

}


function closeDestinationMap() {

    if (!destinationMapModal) {

        return;

    }


    destinationMapModal
        .classList
        .remove(
            "is-open"
        );


    destinationMapModal.setAttribute(
        "aria-hidden",
        "true"
    );


    document.body.classList.remove(
        "no-scroll"
    );

}


async function reverseGeocodeDestinationPoint(
    latitude,
    longitude
) {

    try {

        const response =
            await fetch(
                "/api/reverse-geocode",
                {

                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {

                                lat:
                                    latitude,

                                lon:
                                    longitude

                            }
                        )

                }
            );


        const data =
            await response.json();


        if (
            response.ok
            &&
            data
            &&
            data.success
            &&
            data.location
            &&
            data.location.display_name
        ) {

            return String(
                data.location.display_name
            ).trim();

        }

    }

    catch (error) {

        console.warn(
            "[DESTINATION MAP] Reverse geocode gagal:",
            error
        );

    }


    return "";

}


if (destinationMapButton) {

    destinationMapButton.addEventListener(
        "click",
        openDestinationMap
    );

}


if (destinationMapClose) {

    destinationMapClose.addEventListener(
        "click",
        closeDestinationMap
    );

}


if (destinationMapModal) {

    destinationMapModal.addEventListener(
        "click",
        function (
            event
        ) {

            if (
                event.target
                &&
                event.target.hasAttribute(
                    "data-destination-map-close"
                )
            ) {

                closeDestinationMap();

            }

        }
    );

}


document.addEventListener(
    "keydown",
    function (
        event
    ) {

        if (
            event.key
            === "Escape"
            &&
            destinationMapModal
            &&
            destinationMapModal
                .classList
                .contains(
                    "is-open"
                )
        ) {

            closeDestinationMap();

        }

    }
);


if (destinationMapConfirm) {

    destinationMapConfirm.addEventListener(
        "click",
        async function () {

            if (!destinationDraftCoordinates) {

                setDestinationMapMessage(
                    "Pilih titik tujuan pada peta terlebih dahulu."
                );


                return;

            }


            destinationMapConfirm.disabled =
                true;


            const selectedCoordinates = {

                lat:
                    destinationDraftCoordinates.lat,

                lon:
                    destinationDraftCoordinates.lon

            };


            const currentDestinationText =
                destinationInput
                    ? destinationInput.value.trim()
                    : "";


            setDestinationMapMessage(
                "Menyimpan titik tujuan..."
            );


            const reverseAddress =
                (
                    destinationDraftAddress
                    ||
                    await reverseGeocodeDestinationPoint(
                        selectedCoordinates.lat,
                        selectedCoordinates.lon
                    )
                );

            const addressDetail =
                    destinationAddressDetailInput
                        ? destinationAddressDetailInput
                            .value
                            .trim()
                        : "";


            destinationCoordinates =
                selectedCoordinates;

            window.OjekDestination.detail =
                addressDetail;


            if (destinationInput) {

    const baseAddress =
        (
            reverseAddress
            ||
            currentDestinationText
            ||
            (
                "Titik tujuan "
                +
                `(${selectedCoordinates.lat.toFixed(5)}, `
                +
                `${selectedCoordinates.lon.toFixed(5)})`
            )
        );


    destinationInput.value =
        addressDetail
            ? (
                baseAddress
                +
                " • "
                +
                addressDetail
            )
            : baseAddress;

}


            setDestinationMapStatus(
                (
                    reverseAddress
                        ? (
                            "Titik tujuan dipilih • "
                            +
                            shortenLocation(
                                reverseAddress
                            )
                        )
                        : "Titik tujuan berhasil dipilih"
                ),
                true
            );


            invalidateFare();


            closeDestinationMap();


            destinationMapConfirm.disabled =
                false;

        }
    );

}

// ============================================================
// DESTINATION EDIT
// ============================================================

if (destinationInput) {

    destinationInput.addEventListener(
        "input",
        function () {

            if (window.OjekDestination) {

                window.OjekDestination.coordinates =
                    null;


                window.OjekDestination.address =
                    "";

            }

            window.OjekDestination.detail =
                "";


            if (destinationAddressDetailInput) {

                destinationAddressDetailInput.value =
                    "";

            }


            invalidateFare();

        }
    );

}


// ============================================================
// FARE LOADING
// ============================================================

function setFareLoading(
    loading
) {

    if (
        !checkFareButton
        ||
        !buttonText
        ||
        !buttonArrow
    ) {

        return;

    }


    checkFareButton.disabled =
        loading;


    buttonText.textContent =
        loading
            ? "Menghitung tarif..."
            : "Lihat Tarif";


    buttonArrow.textContent =
        loading
            ? "•••"
            : "→";

}

// ============================================================
// CHECK FARE
// ============================================================

if (bookingForm)

    bookingForm.addEventListener(
        "submit",
        async function (
            event
        ) {

            event.preventDefault();


            hideMessage();


            if (
                !pickupInput
                ||
                !destinationInput
            ) {

                return;

            }


            const pickup =
                pickupInput
                    .value
                    .trim();


            const destination =
                destinationInput
                    .value
                    .trim();

            // ------------------------------------------------
            // VALIDATION
            // ------------------------------------------------

            if (!pickup) {

                showMessage(
                    "Masukkan lokasi penjemputan terlebih dahulu."
                );


                pickupInput.focus();


                return;

            }


            if (!destination) {

                showMessage(
                    "Masukkan lokasi tujuan terlebih dahulu."
                );


                destinationInput.focus();


                return;

            }


            setFareLoading(
                true
            );


            try {

                const payload = {

                    pickup:
                        pickup,

                    destination:
                        destination

                };


                // Gunakan GPS pickup jika tersedia.
if (pickupCoordinates) {

            payload.pickup_lat =
                pickupCoordinates.lat;


            payload.pickup_lon =
                pickupCoordinates.lon;

        }

        // ============================================================
// DESTINATION MAP COORDINATES
// ============================================================

if (
    window.OjekDestination
    &&
    window.OjekDestination.coordinates
) {

    payload.destination_lat =
        window.OjekDestination
            .coordinates
            .lat;


    payload.destination_lon =
        window.OjekDestination
            .coordinates
            .lon;

}


                    // Jika customer memilih titik tujuan di peta,
                    // kirim koordinat langsung ke backend.
                    if (destinationCoordinates) {

                        payload.destination_lat =
                            destinationCoordinates.lat;


                        payload.destination_lon =
                            destinationCoordinates.lon;

                    }


                    const response =
                        await fetch(
                            "/api/check-fare",
                            {

                                method:
                                    "POST",

                                cache:
                                    "no-store",

                                headers: {

                                    "Content-Type":
                                        "application/json",

                                    "Accept":
                                        "application/json"

                                },

                                body:
                                    JSON.stringify(
                                        payload
                                    )

                            }
                        );


                const data =
                    await response.json();


                if (
                    !response.ok
                    ||
                    !data
                    ||
                    data.success !== true
                ) {

                    throw new Error(
                        data.message
                        ||
                        "Tarif belum dapat dihitung. Silakan coba lagi."
                    );

                }

                // ============================================================
                // PHASE 20G.2
                // SAVE RECEIPT TOKEN
                // ============================================================

                if (
                    data.receipt_token
                    &&
                    data.order_code
                ) {

                    sessionStorage.setItem(
                        `receipt_token:${data.order_code}`,
                        data.receipt_token
                    );

                }


                currentRoute =
                    data;


                renderFareResult(
                    data
                );

            }

            catch (error) {

                currentRoute =
                    null;


                showMessage(
                    error.message
                    ||
                    "Terjadi kendala. Silakan coba lagi."
                );


                console.error(
                    "[FARE]",
                    error
                );

            }

            finally {

                setFareLoading(
                    false
                );

            }

        }
    );



// ============================================================
// RENDER FARE RESULT
// ============================================================

function renderFareResult(
    data
) {

    if (
        !resultPickup
        ||
        !resultDestination
        ||
        !resultDistance
        ||
        !resultDuration
        ||
        !resultFare
        ||
        !fareResult
    ) {

        return;

    }


    resultPickup.textContent =
        shortenLocation(
            data.pickup.name
        );


    resultDestination.textContent =
        shortenLocation(
            data.destination.name
        );


    resultDistance.textContent =
        `${data.distance_km} km`;


    resultDuration.textContent =
        `${data.duration_minutes} menit`;


    resultFare.textContent =
        formatRupiah(
            data.fare
        );


    fareResult.classList.add(
        "show"
    );


    window.setTimeout(
        function () {

            fareResult.scrollIntoView(
                {

                    behavior:
                        "smooth",

                    block:
                        "nearest"

                }
            );

        },
        100
    );

}


// ============================================================
// OPEN CUSTOMER PANEL
// ============================================================

if (orderButton) {

    orderButton.addEventListener(
        "click",
        function () {

            hideMessage();
            hideOrderMessage();


            // ------------------------------------------------
            // SERVICE CLOSED
            // ------------------------------------------------

            if (!serviceOpen) {

                showMessage(
                    "Layanan sedang tutup. Pesanan belum dapat dibuat saat ini."
                );

                return;

            }


            // ------------------------------------------------
            // FARE REQUIRED
            // ------------------------------------------------

            if (!currentRoute) {

                showMessage(
                    "Lihat tarif terlebih dahulu."
                );

                return;

            }


            setCustomerPanelOpen(
                true
            );


            window.setTimeout(
                function () {

                    if (customerName) {

                        customerName.focus();

                    }

                },
                180
            );

        }
    );

}


// ============================================================
// CLOSE CUSTOMER PANEL
// ============================================================

if (closeCustomerPanel) {

    closeCustomerPanel.addEventListener(
        "click",
        function () {

            hideOrderMessage();


            setCustomerPanelOpen(
                false
            );

        }
    );

}


// ============================================================
// ORDER LOADING
// ============================================================

function setOrderLoading(
    loading
) {

    orderSubmitting =
        Boolean(
            loading
        );


    if (confirmOrderText) {

        confirmOrderText.textContent =
            orderSubmitting
                ? "Mengirim pesanan..."
                : "Pesan Perjalanan";

    }


    updateOrderAvailability();

}

// ============================================================
// PHASE 20C
// SELECTED PAYMENT METHOD
// ============================================================

function getSelectedPaymentMethod() {

    const selected =
        document.querySelector(
            'input[name="paymentMethod"]:checked'
        );


    return selected
        ? selected.value
        : "TUNAI";

}

// ============================================================
// CREATE ORDER
// ============================================================

if (confirmOrderButton) {

    confirmOrderButton.addEventListener(
        "click",
        async function () {

            hideOrderMessage();


            // =================================================
            // IMPORTANT
            // Pengecekan serviceOpen harus berada DI SINI.
            // =================================================

            if (!serviceOpen) {

                showOrderMessage(
                    "Layanan sedang tutup. Pesanan belum dapat dibuat saat ini."
                );


                return;

            }


            if (!currentRoute) {

                showOrderMessage(
                    "Silakan lihat tarif kembali sebelum memesan."
                );


                return;

            }


            if (
                !customerName
                ||
                !customerWhatsapp
                ||
                !pickupInput
                ||
                !destinationInput
            ) {

                return;

            }


            const name =
                customerName
                    .value
                    .trim();


            const whatsapp =
                customerWhatsapp
                    .value
                    .trim();


            const pickup =
                pickupInput
                    .value
                    .trim();


            const destination =
                destinationInput
                    .value
                    .trim();


            const note =
                noteInput
                    ? noteInput.value.trim()
                    : "";


            // ------------------------------------------------
            // NAME VALIDATION
            // ------------------------------------------------

            if (
                name.length
                <
                2
            ) {

                showOrderMessage(
                    "Masukkan nama Anda untuk melanjutkan."
                );


                customerName.focus();


                return;

            }


            // ------------------------------------------------
            // WHATSAPP VALIDATION
            // ------------------------------------------------

            if (
                whatsapp.length
                <
                9
            ) {

                showOrderMessage(
                    "Masukkan nomor WhatsApp yang valid untuk melanjutkan."
                );


                customerWhatsapp.focus();


                return;

            }


            setOrderLoading(
                true
            );


            try {

                const payload = {

                    customer_name:
                        name,

                    whatsapp:
                        whatsapp,

                    pickup:
                        pickup,

                    destination:
                        destination,

                    note:
                        note,

                    pickup_lat:
                        currentRoute
                            .pickup
                            .lat,

                    pickup_lon:
                        currentRoute
                            .pickup
                            .lon,

                    destination_lat:
                        currentRoute
                            .destination
                            .lat,

                    destination_lon:
                        currentRoute
                            .destination
                            .lon,

                    payment_method:
                        getSelectedPaymentMethod(),

                };


                const response =
                    await fetch(
                        "/api/orders",
                        {

                            method:
                                "POST",


                            headers: {

                                "Content-Type":
                                    "application/json",

                                "Accept":
                                    "application/json"

                            },


                            body:
                                JSON.stringify(
                                    payload
                                )

                        }
                    );


                const data =
                    await response.json();


                // ------------------------------------------------
                // ORDER REJECTED
                // ------------------------------------------------

                if (
                    !response.ok
                    ||
                    !data.success
                ) {

                    // Backend memberi tahu bahwa
                    // layanan ternyata sudah ditutup.
                    if (
                        data
                        &&
                        data.service_open
                        === false
                    ) {

                        updateCustomerServiceUI(
                            false
                        );

                    }


                    throw new Error(
                        data.message
                        ||
                        "Pesanan belum berhasil dikirim. Silakan coba lagi."
                    );

                }

                // ============================================================
// PHASE 20G.3
// SAVE SECURE RECEIPT TOKEN
// ============================================================

if (
    data.order_code
    &&
    data.receipt_token
) {

    try {

        const receiptOrderCode =
            String(
                data.order_code
            )
            .trim()
            .toUpperCase();


        sessionStorage.setItem(
            `receipt_token:${receiptOrderCode}`,
            String(
                data.receipt_token
            )
        );


        console.log(
            "[RECEIPT TOKEN] Token tersimpan untuk:",
            receiptOrderCode
        );

    }

    catch (error) {

        console.warn(
            "[RECEIPT TOKEN STORAGE]",
            error
        );

    }

}


                // ------------------------------------------------
                // SUCCESS
                // ------------------------------------------------

                showOrderSuccess(
                    data.order_code,
                    data.review_token
                    || ""
                );

            }

            catch (error) {

                showOrderMessage(
                    error.message
                    ||
                    "Pesanan belum berhasil dikirim. Silakan coba lagi."
                );


                console.error(
                    "[ORDER]",
                    error
                );

            }

            finally {

                setOrderLoading(
                    false
                );

            }

        }
    );

}


// ============================================================
// ORDER SUCCESS
// ============================================================

function showOrderSuccess(
    orderCode,
    reviewToken = ""
) {

    if (
        !successOrderCode
        ||
        !successOverlay
    ) {

        return;

    }


    latestReviewToken =
        String(
            reviewToken
            || ""
        ).trim();


    successOrderCode.textContent =
        orderCode;


    saveCustomerOrderToHistory(
        orderCode,
        latestReviewToken
    );


    setCustomerPanelOpen(
        false
    );


    successOverlay.classList.add(
        "show"
    );


    document.body.classList.add(
        "no-scroll"
    );

}


// ============================================================
// OPEN LIVE ORDER STATUS
// ============================================================

if (successButton) {

    successButton.addEventListener(
        "click",
        function () {

            if (!successOrderCode) {

                return;

            }


            const orderCode =
                successOrderCode
                    .textContent
                    .trim();


            if (
                !orderCode
                ||
                orderCode === "-"
            ) {

                return;

            }


    const reviewFragment =
        latestReviewToken
            ? (
                "#review_token="
                +
                encodeURIComponent(
                    latestReviewToken
                )
            )
            : "";


    window.location.href =
        (
            "/order/"
            +
            encodeURIComponent(
                orderCode
            )
            +
            reviewFragment
        );
            }
        );

}


// ============================================================
// SERVICE STATUS INITIALIZATION
// ============================================================

// Gunakan status awal dari HTML.
updateCustomerServiceUI(
    serviceOpen
);


// Langsung sinkronkan dengan backend.
refreshServiceStatus();


// Cek status layanan setiap 2 detik.
window.setInterval(
    refreshServiceStatus,
    2000
);


// ============================================================
// REFRESH WHEN WINDOW GETS FOCUS
// ============================================================

window.addEventListener(
    "focus",
    function () {

        refreshServiceStatus();

    }
);


// ============================================================
// REFRESH WHEN TAB BECOMES VISIBLE
// ============================================================

document.addEventListener(
    "visibilitychange",
    function () {

        if (
            document.visibilityState
            === "visible"
        ) {

            refreshServiceStatus();

        }

    }
);

// ============================================================
// CUSTOMER ORDER HISTORY
// DEVICE LOCAL STORAGE
// ============================================================

const CUSTOMER_HISTORY_STORAGE_KEY =
    "ojek_pribadi_customer_history_v1";


const CUSTOMER_HISTORY_MAX_ITEMS =
    10;


// ============================================================
// HISTORY DOM
// ============================================================

const customerHistoryToggle =
    document.getElementById(
        "customerHistoryToggle"
    );


const customerHistoryPanel =
    document.getElementById(
        "customerHistoryPanel"
    );


const customerHistoryList =
    document.getElementById(
        "customerHistoryList"
    );


const customerHistoryCount =
    document.getElementById(
        "customerHistoryCount"
    );


const customerHistoryArrow =
    document.getElementById(
        "customerHistoryArrow"
    );


const clearCustomerHistoryButton =
    document.getElementById(
        "clearCustomerHistory"
    );


// ============================================================
// READ HISTORY
// ============================================================

function readCustomerOrderHistory() {

    try {

        const raw =
            localStorage.getItem(
                CUSTOMER_HISTORY_STORAGE_KEY
            );


        if (!raw) {

            return [];

        }


        const parsed =
            JSON.parse(
                raw
            );


        if (!Array.isArray(parsed)) {

            return [];

        }


        return parsed.filter(
            function (
                item
            ) {

                return (
                    item
                    &&
                    typeof item.order_code
                    === "string"
                );

            }
        );

    }

    catch (error) {

        console.warn(
            "[CUSTOMER HISTORY] Gagal membaca riwayat:",
            error
        );


        return [];

    }

}


// ============================================================
// SAVE HISTORY
// ============================================================

function saveCustomerOrderToHistory(
    orderCode,
    reviewToken = ""
) {

    const normalizedOrderCode =
        String(
            orderCode
            || ""
        )
        .trim();


    if (!normalizedOrderCode) {

        return;

    }


    try {

        const history =
            readCustomerOrderHistory()
                .filter(
                    function (
                        item
                    ) {

                        return (
                            item.order_code
                            !== normalizedOrderCode
                        );

                    }
                );


            history.unshift({

                order_code:
                    normalizedOrderCode,

                review_token:
                    String(
                        reviewToken
                        || ""
                    ).trim(),

                saved_at:
                    Date.now()
            });

        localStorage.setItem(
            CUSTOMER_HISTORY_STORAGE_KEY,

            JSON.stringify(
                history.slice(
                    0,
                    CUSTOMER_HISTORY_MAX_ITEMS
                )
            )
        );


        refreshCustomerOrderHistory();

    }

    catch (error) {

        console.warn(
            "[CUSTOMER HISTORY] Gagal menyimpan riwayat:",
            error
        );

    }

}


// ============================================================
// STATUS LABEL
// ============================================================

function customerHistoryStatusLabel(
    status
) {

    const labels = {

        MENUNGGU:
            "Menunggu",

        DITERIMA:
            "Diterima",

        MENUJU_JEMPUT:
            "Menuju Jemput",

        DIJEMPUT:
            "Dalam Perjalanan",

        SELESAI:
            "Selesai",

        DITOLAK:
            "Ditolak"

    };


    return (
        labels[
            status
        ]
        ||
        status
        ||
        "-"
    );

}


// ============================================================
// FORMAT HISTORY DATE
// ============================================================

function formatCustomerHistoryDate(
    value
) {

    if (!value) {

        return "-";

    }


    const match =
        String(
            value
        ).match(
            /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/
        );


    if (!match) {

        return value;

    }


    const monthNames = [

        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "Mei",
        "Jun",
        "Jul",
        "Agu",
        "Sep",
        "Okt",
        "Nov",
        "Des"

    ];


    return (
        `${Number(match[3])} `
        +
        `${monthNames[Number(match[2]) - 1]}`
        +
        ` • ${match[4]}:${match[5]}`
    );

}


// ============================================================
// CREATE EMPTY HISTORY
// ============================================================

function renderCustomerHistoryEmpty() {

    if (!customerHistoryList) {

        return;

    }


    customerHistoryList.innerHTML =
        "";


    const empty =
        document.createElement(
            "div"
        );


    empty.className =
        "customer-history-empty";


    const icon =
        document.createElement(
            "span"
        );


    icon.textContent =
        "↺";


    const title =
        document.createElement(
            "strong"
        );


    title.textContent =
        "Belum ada riwayat pesanan";


    const description =
        document.createElement(
            "p"
        );


    description.textContent =
        (
            "Perjalanan yang Anda buat "
            +
            "akan muncul di sini."
        );


    empty.appendChild(
        icon
    );


    empty.appendChild(
        title
    );


    empty.appendChild(
        description
    );


    customerHistoryList.appendChild(
        empty
    );

}


// ============================================================
// CREATE HISTORY ITEM
// ============================================================

function createCustomerHistoryItem(
    order
) {

    const card =
        document.createElement(
            "article"
        );


    card.className =
        (
            "customer-history-item "
            +
            `status-${String(
                order.status
                || ""
            ).toLowerCase()}`
        );


    // --------------------------------------------------------
    // TOP
    // --------------------------------------------------------

    const top =
        document.createElement(
            "div"
        );


    top.className =
        "customer-history-item-top";


    const codeWrap =
        document.createElement(
            "div"
        );


    const codeLabel =
        document.createElement(
            "small"
        );


    codeLabel.textContent =
        "KODE PESANAN";


    const code =
        document.createElement(
            "strong"
        );


    code.textContent =
        order.order_code;


    codeWrap.appendChild(
        codeLabel
    );


    codeWrap.appendChild(
        code
    );


    const status =
        document.createElement(
            "span"
        );


    status.className =
        "customer-history-status";


    status.textContent =
        customerHistoryStatusLabel(
            order.status
        );


    top.appendChild(
        codeWrap
    );


    top.appendChild(
        status
    );


    // --------------------------------------------------------
    // ROUTE
    // --------------------------------------------------------

    const route =
        document.createElement(
            "div"
        );


    route.className =
        "customer-history-route";


    const pickup =
        document.createElement(
            "div"
        );


    const pickupDot =
        document.createElement(
            "span"
        );


    pickupDot.className =
        "customer-history-route-dot pickup";


    const pickupText =
        document.createElement(
            "p"
        );


    pickupText.textContent =
        shortenLocation(
            order.pickup
        );


    pickup.appendChild(
        pickupDot
    );


    pickup.appendChild(
        pickupText
    );


    const connector =
        document.createElement(
            "span"
        );


    connector.className =
        "customer-history-route-line";


    const destination =
        document.createElement(
            "div"
        );


    const destinationDot =
        document.createElement(
            "span"
        );


    destinationDot.className =
        "customer-history-route-dot destination";


    const destinationText =
        document.createElement(
            "p"
        );


    destinationText.textContent =
        shortenLocation(
            order.destination
        );


    destination.appendChild(
        destinationDot
    );


    destination.appendChild(
        destinationText
    );


    route.appendChild(
        pickup
    );


    route.appendChild(
        connector
    );


    route.appendChild(
        destination
    );


    // --------------------------------------------------------
    // META
    // --------------------------------------------------------

    const meta =
        document.createElement(
            "div"
        );


    meta.className =
        "customer-history-meta";


    const fare =
        document.createElement(
            "strong"
        );


    fare.textContent =
        formatRupiah(
            order.fare
            || 0
        );


    const date =
        document.createElement(
            "span"
        );


    date.textContent =
        formatCustomerHistoryDate(
            order.created_at
        );


    meta.appendChild(
        fare
    );


    meta.appendChild(
        date
    );


    // --------------------------------------------------------
    // BUTTON
    // --------------------------------------------------------

    const link =
        document.createElement(
            "a"
        );


    link.className =
        "customer-history-view";


    const reviewFragment =
        order.review_token
            ? (
                "#review_token="
                +
                encodeURIComponent(
                    order.review_token
                )
            )
            : "";


    link.href =
        (
            "/order/"
            +
            encodeURIComponent(
                order.order_code
            )
            +
            reviewFragment
        );

    link.textContent =
        "Lihat Status Perjalanan";


    // --------------------------------------------------------
    // COMPLETE
    // --------------------------------------------------------

    card.appendChild(
        top
    );


    card.appendChild(
        route
    );


    card.appendChild(
        meta
    );


    card.appendChild(
        link
    );


    return card;

}


// ============================================================
// FETCH HISTORY ORDER
// ============================================================

async function fetchCustomerHistoryOrder(
    orderCode,
    reviewToken = ""
){

    try {

        const response =
            await fetch(
                (
                    "/api/orders/"
                    +
                    encodeURIComponent(
                        orderCode
                    )
                    +
                    "/status"
                ),

                {
                    method:
                        "GET",

                    cache:
                        "no-store",

                    headers: {

                        "Accept":
                            "application/json"

                    }
                }
            );


        if (!response.ok) {

            return null;

        }


        const data =
            await response.json();


        if (
            !data
            ||
            data.success !== true
            ||
            !data.order
        ) {

            return null;

        }

        data.order.review_token =
            String(
                reviewToken
                || ""
            ).trim();

        return data.order;

    } catch (error) {

        console.warn(
            "[CUSTOMER HISTORY]",
            error
        );

        return null;

    }

}


// ============================================================
// REFRESH HISTORY
// ============================================================

async function refreshCustomerOrderHistory() {

    if (
        !customerHistoryList
        ||
        !customerHistoryCount
    ) {

        return;

    }


    const history =
        readCustomerOrderHistory();


    customerHistoryCount.textContent =
        String(
            history.length
        );


    if (
        history.length
        === 0
    ) {

        renderCustomerHistoryEmpty();

        return;

    }


    customerHistoryList.innerHTML =
        "";


    const loading =
        document.createElement(
            "div"
        );


    loading.className =
        "customer-history-loading";


    loading.textContent =
        "Memuat riwayat perjalanan...";


    customerHistoryList.appendChild(
        loading
    );


    const orders =
        await Promise.all(
            history.map(
                function (
                    item
                ) {

                return fetchCustomerHistoryOrder(
                    item.order_code,
                    item.review_token
                    || ""
                );
                }
            )
        );


    customerHistoryList.innerHTML =
        "";


    const validOrders =
        orders.filter(
            Boolean
        );


    if (
        validOrders.length
        === 0
    ) {

        renderCustomerHistoryEmpty();

        return;

    }


    validOrders.forEach(
        function (
            order
        ) {

            customerHistoryList.appendChild(
                createCustomerHistoryItem(
                    order
                )
            );

        }
    );

}


// ============================================================
// TOGGLE HISTORY
// ============================================================

if (
    customerHistoryToggle
    &&
    customerHistoryPanel
) {

    customerHistoryToggle.addEventListener(
        "click",
        function () {

            const isOpen =
                !customerHistoryPanel.hidden;


            customerHistoryPanel.hidden =
                isOpen;


            customerHistoryToggle.setAttribute(
                "aria-expanded",
                String(
                    !isOpen
                )
            );


            if (customerHistoryArrow) {

                customerHistoryArrow.textContent =
                    isOpen
                        ? "↓"
                        : "↑";

            }


            if (!isOpen) {

                refreshCustomerOrderHistory();

            }

        }
    );

}


// ============================================================
// CLEAR HISTORY
// ============================================================

if (clearCustomerHistoryButton) {

    clearCustomerHistoryButton.addEventListener(
        "click",
        function () {

            const confirmed =
                window.confirm(
                    "Hapus seluruh riwayat pesanan di perangkat ini?"
                );


            if (!confirmed) {

                return;

            }


            try {

                localStorage.removeItem(
                    CUSTOMER_HISTORY_STORAGE_KEY
                );

            }

            catch (error) {

                console.warn(
                    "[CUSTOMER HISTORY]",
                    error
                );

            }


            refreshCustomerOrderHistory();

        }
    );

}


// ============================================================
// INITIAL HISTORY
// ============================================================

refreshCustomerOrderHistory();

// ============================================================
// PHASE 23
// CUSTOMER ACCOUNT MENU
// ============================================================

const customerNavMenuButton =
    document.getElementById(
        "customerNavMenuButton"
    );


const customerNavMenu =
    document.getElementById(
        "customerNavMenu"
    );


function closeCustomerNavMenu() {

    if (!customerNavMenu) {
        return;
    }


    customerNavMenu.hidden =
        true;


    if (customerNavMenuButton) {

        customerNavMenuButton.setAttribute(
            "aria-expanded",
            "false"
        );

    }

}


if (
    customerNavMenuButton
    &&
    customerNavMenu
) {

    customerNavMenuButton.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();


            const willOpen =
                customerNavMenu.hidden;


            customerNavMenu.hidden =
                !willOpen;


            customerNavMenuButton.setAttribute(
                "aria-expanded",
                willOpen
                    ? "true"
                    : "false"
            );

        }
    );


    customerNavMenu.addEventListener(
        "click",
        function(event) {

            event.stopPropagation();

        }
    );


    document.addEventListener(
        "click",
        function() {

            closeCustomerNavMenu();

        }
    );


    document.addEventListener(
        "keydown",
        function(event) {

            if (
                event.key
                ===
                "Escape"
            ) {

                closeCustomerNavMenu();

            }

        }
    );

}

// ============================================================
// APP READY
// ============================================================

console.log(
    "[APP] Ojek Pribadi customer app aktif."
);

