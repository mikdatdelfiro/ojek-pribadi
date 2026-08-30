"use strict";


// ============================================================
// OJEK PRIBADI
// CUSTOMER LIVE ORDER STATUS
// Phase 16 - Customer Tracking Dark Premium Final
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
            `[ORDER STATUS] Element #${id} tidak ditemukan.`
        );

    }


    return element;

}


// ============================================================
// MAIN PAGE DATA
// ============================================================

const trackingPage =
    getElement(
        "trackingPage"
    );


const orderCode =
    trackingPage
        ? trackingPage.dataset.orderCode
        : "";


const initialStatus =
    trackingPage
        ? trackingPage.dataset.initialStatus
        : "MENUNGGU";


// ============================================================
// LIVE STATUS ELEMENTS
// ============================================================

const liveStatusCard =
    getElement(
        "liveStatusCard"
    );


const liveIcon =
    getElement(
        "liveIcon"
    );


const liveStatusTitle =
    getElement(
        "liveStatusTitle"
    );


const liveStatusDescription =
    getElement(
        "liveStatusDescription"
    );


const lastUpdate =
    getElement(
        "lastUpdate"
    );


const rejectedCard =
    getElement(
        "rejectedCard",
        false
    );


// ============================================================
// DRIVER CONTACT
// ============================================================

const customerDriverContact =
    getElement(
        "customerDriverContact",
        false
    );


// ============================================================
// PROGRESS
// ============================================================

const progressSteps =
    document.querySelectorAll(
        ".progress-step"
    );

    // =====================================================
// TIMELINE TIMESTAMP CONFIG
// =====================================================

const timelineTimestampKeys = {

    0:
        "created_at",

    1:
        "accepted_at",

    2:
        "to_pickup_at",

    3:
        "picked_up_at",

    4:
        "completed_at"

};


const statusTimestampKeys = {

    MENUNGGU:
        "created_at",

    DITERIMA:
        "accepted_at",

    MENUJU_JEMPUT:
        "to_pickup_at",

    DIJEMPUT:
        "picked_up_at",

    SELESAI:
        "completed_at",

    DITOLAK:
        "rejected_at"

};

// ============================================================
// DRIVER PROFILE
// ============================================================

const driverProfileCard =
    getElement(
        "driverProfileCard",
        false
    );


const driverProfilePhoto =
    getElement(
        "driverProfilePhoto",
        false
    );


const driverProfileInitial =
    getElement(
        "driverProfileInitial",
        false
    );


const driverProfileName =
    getElement(
        "driverProfileName",
        false
    );


const driverProfileBio =
    getElement(
        "driverProfileBio",
        false
    );


const driverVehicleName =
    getElement(
        "driverVehicleName",
        false
    );


const driverVehicleColor =
    getElement(
        "driverVehicleColor",
        false
    );


const driverVehiclePlate =
    getElement(
        "driverVehiclePlate",
        false
    );


// ============================================================
// STATUS CONFIGURATION
// ============================================================

const statusConfig = {

    MENUNGGU: {

        step:
            0,

        icon:
            "⌛",

        title:
            "Menunggu konfirmasi driver",

        description:
            (
                "Pesanan Anda sudah dikirim. "
                +
                "Mohon tunggu pengemudi "
                +
                "mengonfirmasi perjalanan."
            )

    },


    DITERIMA: {

        step:
            1,

        icon:
            "✓",

        title:
            "Perjalanan dikonfirmasi",

        description:
            (
                "Driver telah menerima "
                +
                "pesanan Anda dan akan "
                +
                "segera menuju lokasi jemput."
            )

    },


    MENUJU_JEMPUT: {

        step:
            2,

        icon:
            "🛵",

        title:
            "Driver menuju lokasi Anda",

        description:
            (
                "Driver sedang dalam "
                +
                "perjalanan menuju lokasi jemput."
            )

    },


    DIJEMPUT: {

        step:
            3,

        icon:
            "→",

        title:
            "Perjalanan sedang berlangsung",

        description:
            (
                "Anda sudah dijemput. "
                +
                "Perjalanan menuju tujuan "
                +
                "sedang berlangsung."
            )

    },


    SELESAI: {

        step:
            4,

        icon:
            "✓",

        title:
            "Perjalanan selesai",

        description:
            (
                "Perjalanan telah selesai. "
                +
                "Terima kasih telah menggunakan "
                +
                "layanan Ojek Pribadi."
            )

    }

};


// ============================================================
// APPLICATION STATE
// ============================================================

let currentStatus =
    null;


let statusInterval =
    null;


// ============================================================
// DRIVER PROFILE
// ============================================================

function updateDriverProfile(
    profile
) {

    if (!driverProfileCard) {

        return;

    }


    // --------------------------------------------------------
    // HIDE PROFILE
    // --------------------------------------------------------

    if (!profile) {

        driverProfileCard.hidden =
            true;


        return;

    }


    // --------------------------------------------------------
    // SHOW PROFILE
    // --------------------------------------------------------

    driverProfileCard.hidden =
        false;


    // --------------------------------------------------------
    // DRIVER NAME
    // --------------------------------------------------------

    const driverName =
        (
            profile.driver_name
            ||
            "Driver"
        );


    if (driverProfileName) {

        driverProfileName.textContent =
            driverName;

    }


    // --------------------------------------------------------
    // BIO
    // --------------------------------------------------------

    if (driverProfileBio) {

        driverProfileBio.textContent =
            (
                profile.short_bio
                ||
                ""
            );

    }


    // --------------------------------------------------------
    // VEHICLE
    // --------------------------------------------------------

    if (driverVehicleName) {

        driverVehicleName.textContent =
            (
                profile.vehicle_name
                ||
                "-"
            );

    }


    if (driverVehicleColor) {

        driverVehicleColor.textContent =
            (
                profile.vehicle_color
                ||
                "-"
            );

    }


    if (driverVehiclePlate) {

        driverVehiclePlate.textContent =
            (
                profile.vehicle_plate
                ||
                "-"
            );

    }


    // --------------------------------------------------------
    // INITIAL
    // --------------------------------------------------------

    const initial =
        driverName
            .charAt(0)
            .toUpperCase();


    if (driverProfileInitial) {

        driverProfileInitial.textContent =
            initial;

    }


    // --------------------------------------------------------
    // PHOTO
    // --------------------------------------------------------

    if (
        driverProfilePhoto
        &&
        profile.photo_url
    ) {

        driverProfilePhoto.src =
            profile.photo_url;


        driverProfilePhoto.hidden =
            false;


        if (driverProfileInitial) {

            driverProfileInitial.hidden =
                true;

        }


        // Jika foto gagal dimuat,
        // tampilkan initial sebagai fallback.

        driverProfilePhoto.onerror =
            function () {

                driverProfilePhoto.hidden =
                    true;


                if (driverProfileInitial) {

                    driverProfileInitial.hidden =
                        false;

                }

            };

    }

    else {

        if (driverProfilePhoto) {

            driverProfilePhoto.removeAttribute(
                "src"
            );


            driverProfilePhoto.hidden =
                true;

        }


        if (driverProfileInitial) {

            driverProfileInitial.hidden =
                false;

        }

    }

}


// ============================================================
// DRIVER CONTACT
// ============================================================

function updateDriverContact(
    status
) {

    if (!customerDriverContact) {

        return;

    }


    const allowedStatuses = [

        "DITERIMA",

        "MENUJU_JEMPUT",

        "DIJEMPUT"

    ];


    const canContact =
        allowedStatuses.includes(
            status
        );


    customerDriverContact
        .classList
        .toggle(
            "show",
            canContact
        );


    // Tambahan proteksi agar tombol benar-benar
    // tidak tampil ketika status belum diizinkan.

    customerDriverContact.hidden =
        !canContact;

}

// =====================================================
// JOURNEY TIMESTAMP FORMAT
// =====================================================

function formatJourneyTimestamp(
    value
) {

    if (!value) {

        return "--:--";

    }


    const timestamp =
        String(
            value
        ).trim();


    /*
        Backend:

        2026-08-27 21:33:20

        Tampilan:

        21:33
    */

    const match =
        timestamp.match(
            /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/
        );


    if (!match) {

        return timestamp;

    }


    return (
        `${match[4]}:${match[5]}`
    );

}

// =====================================================
// CREATE PROGRESS TIMESTAMP
// =====================================================

function getProgressTimestampElement(
    step
) {

    let timestampElement =
        step.querySelector(
            ".progress-timestamp"
        );


    if (timestampElement) {

        return timestampElement;

    }


    timestampElement =
        document.createElement(
            "span"
        );


    timestampElement.className =
        "progress-timestamp";


    timestampElement.textContent =
        "--:--";


    // Cari deskripsi di dalam progress step.
    const description =
        step.querySelector(
            "p"
        );


    if (description) {

        description.insertAdjacentElement(
            "afterend",
            timestampElement
        );

    }

    else {

        step.appendChild(
            timestampElement
        );

    }


    return timestampElement;

}

// =====================================================
// UPDATE JOURNEY TIMELINE TIMESTAMPS
// =====================================================

function updateTimelineTimestamps(
    timestamps
) {

    if (!timestamps) {

        return;

    }


    progressSteps.forEach(
        function (
            step
        ) {

            const stepNumber =
                Number(
                    step.dataset.step
                );


            const timestampKey =
                timelineTimestampKeys[
                    stepNumber
                ];


            if (!timestampKey) {

                return;

            }


            const timestampElement =
                getProgressTimestampElement(
                    step
                );


            const timestampValue =
                timestamps[
                    timestampKey
                ];


            if (timestampValue) {

                timestampElement.textContent =
                    formatJourneyTimestamp(
                        timestampValue
                    );


                timestampElement.classList.add(
                    "is-set"
                );


                timestampElement.title =
                    timestampValue;

            }

            else {

                timestampElement.textContent =
                    "--:--";


                timestampElement.classList.remove(
                    "is-set"
                );


                timestampElement.removeAttribute(
                    "title"
                );

            }

        }
    );

}

// =====================================================
// CURRENT STATUS TIMESTAMP
// =====================================================

function updateCurrentStatusTimestamp(
    status,
    timestamps
) {

    if (
        !liveStatusDescription
        ||
        !timestamps
    ) {

        return;

    }


    let timestampElement =
        document.getElementById(
            "liveStatusTimestamp"
        );


    if (!timestampElement) {

        timestampElement =
            document.createElement(
                "div"
            );


        timestampElement.id =
            "liveStatusTimestamp";


        timestampElement.className =
            "live-status-timestamp";


        liveStatusDescription
            .insertAdjacentElement(
                "afterend",
                timestampElement
            );

    }


    const timestampKey =
        statusTimestampKeys[
            status
        ];


    const timestampValue =
        timestampKey
            ? timestamps[
                timestampKey
            ]
            : null;


    if (!timestampValue) {

        timestampElement.hidden =
            true;


        return;

    }


    timestampElement.hidden =
        false;


    timestampElement.innerHTML =
        (
            "<span>TERJADI PUKUL</span>"
            +
            "<strong>"
            +
            formatJourneyTimestamp(
                timestampValue
            )
            +
            "</strong>"
        );

}

// =====================================================
// REJECTED TIMESTAMP
// =====================================================

function updateRejectedTimestamp(
    timestamps
) {

    if (
        !rejectedCard
        ||
        !timestamps
    ) {

        return;

    }


    let element =
        rejectedCard.querySelector(
            ".rejected-timestamp"
        );


    if (!element) {

        element =
            document.createElement(
                "div"
            );


        element.className =
            "rejected-timestamp";


        rejectedCard.appendChild(
            element
        );

    }


    const rejectedAt =
        timestamps.rejected_at;


    if (!rejectedAt) {

        element.hidden =
            true;


        return;

    }


    element.hidden =
        false;


    element.textContent =
        (
            "Ditolak pukul "
            +
            formatJourneyTimestamp(
                rejectedAt
            )
        );

}

// =====================================================
// UPDATE ALL JOURNEY TIMESTAMPS
// =====================================================

function updateJourneyTimestamps(
    status,
    timestamps
) {

    if (!timestamps) {

        return;

    }


    updateTimelineTimestamps(
        timestamps
    );


    updateCurrentStatusTimestamp(
        status,
        timestamps
    );


    updateRejectedTimestamp(
        timestamps
    );

}

// ============================================================
// LAST UPDATE
// ============================================================

function updateLastUpdate() {

    if (!lastUpdate) {

        return;

    }


    const now =
        new Date();


    lastUpdate.textContent =
        now.toLocaleTimeString(
            "id-ID",
            {

                hour:
                    "2-digit",

                minute:
                    "2-digit",

                second:
                    "2-digit"

            }
        );

}


// ============================================================
// UPDATE PROGRESS
// ============================================================

function updateProgress(
    stepNumber,
    status
) {

    progressSteps.forEach(
        function (
            step
        ) {

            const currentStep =
                Number(
                    step.dataset.step
                );


            step.classList.remove(
                "done",
                "current"
            );


            if (
                currentStep
                <
                stepNumber
            ) {

                step.classList.add(
                    "done"
                );

            }


            if (
                currentStep
                ===
                stepNumber
            ) {

                step.classList.add(
                    "current"
                );

            }

        }
    );


    // --------------------------------------------------------
    // COMPLETED
    // --------------------------------------------------------

    if (
        status
        === "SELESAI"
    ) {

        progressSteps.forEach(
            function (
                step
            ) {

                step.classList.remove(
                    "current"
                );


                step.classList.add(
                    "done"
                );

            }
        );

    }

}

// ============================================================
// PHASE 12
// CUSTOMER STATUS NOTIFICATION
// ============================================================

const customerStatusNotificationConfig = {

    DITERIMA: {
        title:
            "Perjalanan dikonfirmasi",

        message:
            (
                "Driver telah menerima "
                +
                "perjalanan Anda."
            )
    },


    MENUJU_JEMPUT: {
        title:
            "Driver menuju Anda",

        message:
            (
                "Pengemudi sedang menuju "
                +
                "lokasi penjemputan."
            )
    },


    DIJEMPUT: {
        title:
            "Perjalanan dimulai",

        message:
            (
                "Perjalanan menuju tujuan "
                +
                "sedang berlangsung."
            )
    },


    SELESAI: {
        title:
            "Perjalanan selesai",

        message:
            (
                "Anda telah sampai di tujuan. "
                +
                "Terima kasih."
            )
    },


    DITOLAK: {
        title:
            "Perjalanan belum dapat diterima",

        message:
            (
                "Maaf, perjalanan Anda belum "
                +
                "dapat diterima oleh driver."
            )
    }

};


const customerStatusBaseTitle =
    document.title;


let customerStatusToastTimer =
    null;


// ============================================================
// CREATE CUSTOMER TOAST
// ============================================================

function getCustomerStatusToast() {

    let toast =
        document.getElementById(
            "customerStatusToast"
        );


    if (toast) {

        return toast;

    }


    toast =
        document.createElement(
            "div"
        );


    toast.id =
        "customerStatusToast";


    toast.className =
        "customer-status-toast";


    const label =
        document.createElement(
            "span"
        );


    label.className =
        "customer-status-toast-label";


    label.textContent =
        "UPDATE PERJALANAN";


    const title =
        document.createElement(
            "strong"
        );


    title.id =
        "customerStatusToastTitle";


    const message =
        document.createElement(
            "p"
        );


    message.id =
        "customerStatusToastMessage";


    toast.appendChild(
        label
    );


    toast.appendChild(
        title
    );


    toast.appendChild(
        message
    );


    document.body.appendChild(
        toast
    );


    return toast;

}


// ============================================================
// SHOW CUSTOMER STATUS NOTIFICATION
// ============================================================

function showCustomerStatusNotification(
    status
) {

    const config =
        customerStatusNotificationConfig[
            status
        ];


    if (!config) {

        return;

    }


    const toast =
        getCustomerStatusToast();


    const title =
        document.getElementById(
            "customerStatusToastTitle"
        );


    const message =
        document.getElementById(
            "customerStatusToastMessage"
        );


    if (title) {

        title.textContent =
            config.title;

    }


    if (message) {

        message.textContent =
            config.message;

    }


    toast.classList.remove(
        "show"
    );


    void toast.offsetWidth;


    toast.classList.add(
        "show"
    );


    if (customerStatusToastTimer) {

        window.clearTimeout(
            customerStatusToastTimer
        );

    }


    customerStatusToastTimer =
        window.setTimeout(
            function () {

                toast.classList.remove(
                    "show"
                );

            },
            5000
        );


    // --------------------------------------------------------
    // TAB TITLE
    // --------------------------------------------------------

    document.title =
        (
            config.title
            +
            " • Ojek Pribadi"
        );


    // --------------------------------------------------------
    // MOBILE VIBRATION
    // --------------------------------------------------------

    if (
        "vibrate"
        in navigator
    ) {

        navigator.vibrate(
            150
        );

    }

}


// ============================================================
// RESTORE TITLE
// ============================================================

window.addEventListener(
    "focus",
    function () {

        document.title =
            customerStatusBaseTitle;

    }
);

// ============================================================
// UPDATE STATUS UI
// ============================================================

function updateStatusUI(
    status,
    driverProfile = null
) {

    if (!status) {

        return;

    }


    // ========================================================
    // ALWAYS UPDATE THESE
    // ========================================================

    updateDriverContact(
        status
    );


    updateDriverProfile(
        driverProfile
    );


    updateLastUpdate();


    // Tidak perlu menjalankan animasi ulang
    // jika status masih sama.
    if (
    status
    === currentStatus
) {

    return;

}


const previousStatus =
    currentStatus;


currentStatus =
    status;


// ========================================================
// PHASE 12
// NOTIFY CUSTOMER
// ========================================================

if (
    previousStatus
    !== null
) {

    showCustomerStatusNotification(
        status
    );

}


    // ========================================================
    // REJECTED
    // ========================================================

    if (
        status
        === "DITOLAK"
    ) {

        if (rejectedCard) {

            rejectedCard.classList.add(
                "show"
            );

        }


        if (liveStatusCard) {

            liveStatusCard.classList.add(
                "rejected"
            );

        }


        if (liveIcon) {

            liveIcon.textContent =
                "×";

        }


        if (liveStatusTitle) {

            liveStatusTitle.textContent =
                "Perjalanan belum dapat diterima";

        }


        if (liveStatusDescription) {

            liveStatusDescription.textContent =
                (
                    "Maaf, perjalanan ini belum "
                    +
                    "dapat diterima oleh driver."
                );

        }


        progressSteps.forEach(
            function (
                step
            ) {

                step.classList.remove(
                    "done",
                    "current"
                );

            }
        );


        stopPolling();


        return;

    }


    // ========================================================
    // REMOVE REJECTED STATE
    // ========================================================

    if (rejectedCard) {

        rejectedCard.classList.remove(
            "show"
        );

    }


    if (liveStatusCard) {

        liveStatusCard.classList.remove(
            "rejected"
        );

    }


    // ========================================================
    // GET CONFIG
    // ========================================================

    const config =
        statusConfig[
            status
        ];


    if (!config) {

        console.warn(
            "[ORDER STATUS] Status tidak dikenal:",
            status
        );


        return;

    }


    // ========================================================
    // STATUS CHANGE ANIMATION
    // ========================================================

    if (liveStatusCard) {

        liveStatusCard.classList.remove(
            "status-change"
        );


        // Force browser reflow.
        void liveStatusCard.offsetWidth;


        liveStatusCard.classList.add(
            "status-change"
        );

    }


    // ========================================================
    // ICON
    // ========================================================

    if (liveIcon) {

        liveIcon.textContent =
            config.icon;

    }


    // ========================================================
    // TITLE
    // ========================================================

    if (liveStatusTitle) {

        liveStatusTitle.textContent =
            config.title;

    }


    // ========================================================
    // DESCRIPTION
    // ========================================================

    if (liveStatusDescription) {

        liveStatusDescription.textContent =
            config.description;

    }


    // ========================================================
    // PROGRESS
    // ========================================================

    updateProgress(
        config.step,
        status
    );


    // ========================================================
    // COMPLETED
    // ========================================================

    if (
        status
        === "SELESAI"
    ) {

        stopPolling();

    }

}


// ============================================================
// FETCH ORDER STATUS
// ============================================================

async function fetchOrderStatus() {

    if (!orderCode) {

        console.error(
            "[ORDER STATUS] Kode pesanan tidak tersedia."
        );


        return;

    }


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
            ||
            !data.order
        ) {

            throw new Error(
                (
                    data
                    &&
                    data.message
                )
                ||
                "Status tidak dapat diperbarui."
            );

        }


        // ====================================================
        // STATUS + DRIVER PROFILE
        // ====================================================

        // ====================================================
        // LIVE STATUS
        // ====================================================

        updateStatusUI(
            data.order.status,
            data.order.driver_profile
            || null
        );


        // ====================================================
        // LIVE TIMESTAMPS
        // ====================================================

        updateJourneyTimestamps(
            data.order.status,
            data.order.timestamps
            || null
        );

            }

    catch (error) {

        console.error(
            "[ORDER STATUS]",
            error
        );

    }

}


// ============================================================
// POLLING CONTROL
// ============================================================

function startPolling() {

    if (statusInterval) {

        return;

    }


    statusInterval =
        window.setInterval(
            fetchOrderStatus,
            3000
        );

}


function stopPolling() {

    if (!statusInterval) {

        return;

    }


    window.clearInterval(
        statusInterval
    );


    statusInterval =
        null;

}


// ============================================================
// INITIAL STATUS
// ============================================================

// Status HTML awal.
// Driver profile belum perlu dipaksakan dari HTML;
// fetch API berikutnya akan mengambil data terbaru.

updateStatusUI(
    initialStatus,
    null
);


// ============================================================
// FIRST API CHECK
// ============================================================

fetchOrderStatus();


// ============================================================
// START LIVE POLLING
// ============================================================

if (
    initialStatus !== "SELESAI"
    &&
    initialStatus !== "DITOLAK"
) {

    startPolling();

}


// ============================================================
// WINDOW FOCUS
// ============================================================

window.addEventListener(
    "focus",
    function () {

        fetchOrderStatus();

    }
);


// ============================================================
// VISIBILITY CHANGE
// ============================================================

document.addEventListener(
    "visibilitychange",
    function () {

        if (
            document.visibilityState
            === "visible"
        ) {

            fetchOrderStatus();


            if (
                currentStatus !== "SELESAI"
                &&
                currentStatus !== "DITOLAK"
            ) {

                startPolling();

            }

        }

    }
);


// ============================================================
// PAGE CLEANUP
// ============================================================

window.addEventListener(
    "beforeunload",
    function () {

        stopPolling();

    }
);


// ============================================================
// APP READY
// ============================================================

console.log(
    "[ORDER STATUS] Live tracking aktif."
);
