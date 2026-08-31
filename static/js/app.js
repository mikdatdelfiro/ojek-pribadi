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


let currentRoute =
    null;


let orderSubmitting =
    false;


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
// DESTINATION EDIT
// ============================================================

if (destinationInput) {

    destinationInput.addEventListener(
        "input",
        invalidateFare
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

if (bookingForm) {

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


                const response =
                    await fetch(
                        "/api/check-fare",
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


                if (
                    !response.ok
                    ||
                    !data.success
                ) {

                    throw new Error(
                        data.message
                        ||
                        "Tarif belum dapat dihitung. Silakan coba lagi."
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

}


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
                            .lon

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


                // ------------------------------------------------
                // SUCCESS
                // ------------------------------------------------

                showOrderSuccess(
                    data.order_code
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
    orderCode
) {

    if (
        !successOrderCode
        ||
        !successOverlay
    ) {

        return;

    }


    successOrderCode.textContent =
        orderCode;

    saveCustomerOrderToHistory(
    orderCode
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


            window.location.href =
                (
                    "/order/"
                    +
                    encodeURIComponent(
                        orderCode
                    )
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
    orderCode
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


        history.unshift(
            {
                order_code:
                    normalizedOrderCode,

                saved_at:
                    Date.now()
            }
        );


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


    link.href =
        (
            "/order/"
            +
            encodeURIComponent(
                order.order_code
            )
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
    orderCode
) {

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


        return data.order;

    }

    catch (error) {

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
                        item.order_code
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
// APP READY
// ============================================================

console.log(
    "[APP] Ojek Pribadi customer app aktif."
);
