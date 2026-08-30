const statusButtons =
    document.querySelectorAll(
        ".update-status"
    );


const rejectButtons =
    document.querySelectorAll(
        ".reject-order"
    );


const driverToast =
    document.getElementById(
        "driverToast"
    );


const driverToastMessage =
    document.getElementById(
        "driverToastMessage"
    );


// =====================================================
// UPDATE STATUS
// =====================================================

// ============================================================
// PHASE 18F
// DRIVER SAFE ORDER ACTION
// ============================================================

const activeOrderRequests =
    new Set();


// ============================================================
// LOCK / UNLOCK CARD ACTIONS
// ============================================================

function setOrderCardBusy(
    card,
    busy
) {

    if (!card) {
        return;
    }


    card.classList.toggle(
        "is-processing",
        busy
    );


    const buttons =
        card.querySelectorAll(
            ".driver-actions button"
        );


    buttons.forEach(
        function (item) {

            item.disabled =
                Boolean(
                    busy
                );

        }
    );

}


// ============================================================
// CONFIRM IMPORTANT ACTION
// ============================================================

function confirmDriverAction(
    status
) {

    if (
        status === "DITOLAK"
    ) {

        return window.confirm(
            "Tolak pesanan ini?\n\n"
            +
            "Pesanan akan ditandai sebagai ditolak "
            +
            "dan tidak dapat dilanjutkan."
        );

    }


    if (
        status === "SELESAI"
    ) {

        return window.confirm(
            "Selesaikan perjalanan?\n\n"
            +
            "Pastikan penumpang sudah sampai "
            +
            "di tujuan sebelum menyelesaikan perjalanan."
        );

    }


    return true;

}


// ============================================================
// SAFE RESPONSE JSON
// ============================================================

async function readDriverResponse(
    response
) {

    try {

        return await response.json();

    }

    catch (error) {

        return {
            success: false,
            message:
                "Respons server tidak valid."
        };

    }

}


// ============================================================
// UPDATE ORDER STATUS
// ============================================================

async function updateOrderStatus(
    button
) {

    if (!button) {
        return;
    }


    const orderId =
        button.dataset.id;


    const status =
        button.dataset.status;


    if (
        !orderId
        ||
        !status
    ) {

        alert(
            "Data pesanan tidak lengkap."
        );

        return;

    }


    // --------------------------------------------------------
    // INTERNET CHECK
    // --------------------------------------------------------

    if (
        navigator.onLine
        === false
    ) {

        showDriverToast(
            "Tidak ada koneksi internet."
        );

        return;

    }


    // --------------------------------------------------------
    // DUPLICATE REQUEST PROTECTION
    // --------------------------------------------------------

    if (
        activeOrderRequests.has(
            String(
                orderId
            )
        )
    ) {

        return;

    }


    // --------------------------------------------------------
    // CONFIRM DANGEROUS ACTION
    // --------------------------------------------------------

    if (
        !confirmDriverAction(
            status
        )
    ) {

        return;

    }


    const card =
        button.closest(
            ".driver-order-card"
        );


    const originalHTML =
        button.innerHTML;


    activeOrderRequests.add(
        String(
            orderId
        )
    );


    setOrderCardBusy(
        card,
        true
    );


    button.innerHTML =
        `
        <span class="button-loading-dot"></span>
        Memproses...
        `;


    // --------------------------------------------------------
    // REQUEST TIMEOUT
    // --------------------------------------------------------

    const controller =
        new AbortController();


    const timeoutId =
        window.setTimeout(
            function () {

                controller.abort();

            },
            12000
        );


    try {

        const response =
            await fetch(
                `/api/orders/${orderId}/status`,
                {
                    method:
                        "POST",

                    cache:
                        "no-store",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {
                                status:
                                    status
                            }
                        ),

                    signal:
                        controller.signal
                }
            );


        const data =
            await readDriverResponse(
                response
            );


        // ----------------------------------------------------
        // SESSION EXPIRED
        // ----------------------------------------------------

        if (
            response.status
            === 401
        ) {

            window.location.href =
                "/driver/login?expired=1";

            return;

        }


        // ----------------------------------------------------
        // BACKEND ERROR
        // ----------------------------------------------------

        if (
            !response.ok
            ||
            !data.success
        ) {

            throw new Error(
                data.message
                ||
                "Status perjalanan belum berhasil diperbarui."
            );

        }


        // ----------------------------------------------------
        // SUCCESS
        // ----------------------------------------------------

        showDriverToast(
            data.message
            ||
            "Status perjalanan berhasil diperbarui."
        );


        if (card) {

            card.classList.add(
                "status-changing"
            );

        }


        // Reload from server so server remains source of truth.
        window.setTimeout(
            function () {

                window.location.reload();

            },
            550
        );

    }

    catch (error) {

        console.error(
            "[DRIVER ORDER STATUS]",
            error
        );


        let message =
            (
                error.message
                ||
                "Status perjalanan belum berhasil diperbarui."
            );


        if (
            error.name
            === "AbortError"
        ) {

            message =
                (
                    "Server membutuhkan waktu terlalu lama. "
                    +
                    "Periksa koneksi lalu coba lagi."
                );

        }


        showDriverToast(
            message
        );


        button.innerHTML =
            originalHTML;


        setOrderCardBusy(
            card,
            false
        );

    }

    finally {

        window.clearTimeout(
            timeoutId
        );


        activeOrderRequests.delete(
            String(
                orderId
            )
        );

    }

}

// =====================================================
// NORMAL BUTTONS
// =====================================================

statusButtons.forEach(
    function (button) {

        button.addEventListener(
            "click",
            function () {

                updateOrderStatus(
                    button
                );

            }
        );

    }
);


// =====================================================
// REJECT
// =====================================================

rejectButtons.forEach(
    function (button) {

        button.addEventListener(
            "click",
            function () {

                updateOrderStatus(
                    button
                );

            }
        );

    }
);


// =====================================================
// TOAST
// =====================================================

function showDriverToast(
    message
) {

    driverToastMessage.textContent =
        message;


    driverToast.classList.add(
        "show"
    );


    setTimeout(
        function () {

            driverToast.classList.remove(
                "show"
            );

        },
        2500
    );

}

// ============================================================
// PHASE 9
// DRIVER SERVICE CONTROL
// FIXED + SERVER SYNC
// ============================================================

const serviceControl =
    document.getElementById(
        "serviceControl"
    );


const serviceToggleButton =
    document.getElementById(
        "serviceToggleButton"
    );


const serviceStatusLabel =
    document.getElementById(
        "serviceStatusLabel"
    );


const serviceStatusDescription =
    document.getElementById(
        "serviceStatusDescription"
    );


const serviceControlMessage =
    document.getElementById(
        "serviceControlMessage"
    );


let serviceToggleBusy =
    false;


// ============================================================
// NORMALIZE BOOLEAN
// ============================================================

function normalizeServiceState(
    value
) {

    return (
        value === true
        ||
        value === "true"
        ||
        value === 1
        ||
        value === "1"
    );

}


// ============================================================
// UPDATE SERVICE UI
// ============================================================

function updateServiceControlUI(
    state
) {

    if (!serviceControl) {

        return;

    }


    const isOpen =
        normalizeServiceState(
            state
        );


    // --------------------------------------------------------
    // DATASET
    // --------------------------------------------------------

    serviceControl.dataset.serviceOpen =
        isOpen
            ? "true"
            : "false";


    // --------------------------------------------------------
    // CARD STATE
    // --------------------------------------------------------

    serviceControl.classList.toggle(
        "is-open",
        isOpen
    );


    serviceControl.classList.toggle(
        "is-closed",
        !isOpen
    );


    // --------------------------------------------------------
    // BUTTON
    // --------------------------------------------------------

    if (serviceToggleButton) {

        serviceToggleButton.setAttribute(
            "aria-pressed",
            isOpen
                ? "true"
                : "false"
        );

    }


    // --------------------------------------------------------
    // LABEL
    // --------------------------------------------------------

    if (serviceStatusLabel) {

        serviceStatusLabel.textContent =
            isOpen
                ? "MENERIMA PESANAN"
                : "SEDANG TIDAK MELAYANI";

    }


    // --------------------------------------------------------
    // DESCRIPTION
    // --------------------------------------------------------

    if (serviceStatusDescription) {

        serviceStatusDescription.textContent =
            isOpen
                ? (
                    "Pelanggan dapat membuat "
                    +
                    "pesanan baru."
                )
                : (
                    "Pesanan baru sedang "
                    +
                    "dinonaktifkan."
                );

    }

}


// ============================================================
// MESSAGE
// ============================================================

function showServiceMessage(
    message
) {

    if (!serviceControlMessage) {

        return;

    }


    serviceControlMessage.textContent =
        message || "";

}


// ============================================================
// SYNCHRONIZE WITH SERVER
// ============================================================

async function syncDriverServiceStatus() {

    if (!serviceControl) {

        return;

    }


    try {

        const response =
            await fetch(
                (
                    "/api/service-status"
                    +
                    "?t="
                    +
                    Date.now()
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
                "Status layanan tidak dapat diperiksa."
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


        updateServiceControlUI(
            data.service_open
        );


        console.log(
            "[SERVICE SYNC]",
            data.service_open
        );

    }

    catch (error) {

        console.warn(
            "[SERVICE SYNC ERROR]",
            error
        );

    }

}


// ============================================================
// TOGGLE SERVICE
// ============================================================

async function toggleDriverService() {

    if (
        !serviceControl
        ||
        !serviceToggleButton
        ||
        serviceToggleBusy
    ) {

        return;

    }


    serviceToggleBusy =
        true;


    const currentlyOpen =
        (
            serviceControl.dataset.serviceOpen
            === "true"
        );


    const nextState =
        !currentlyOpen;


    serviceToggleButton.disabled =
        true;


    showServiceMessage(
        nextState
            ? "Membuka layanan..."
            : "Menutup layanan..."
    );


    try {

        const response =
            await fetch(
                "/api/driver/service-status",
                {
                    method:
                        "POST",

                    cache:
                        "no-store",

                    credentials:
                        "same-origin",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            {
                                service_open:
                                    nextState
                            }
                        )
                }
            );


        let data =
            null;


        try {

            data =
                await response.json();

        }

        catch (error) {

            throw new Error(
                "Respons server tidak valid."
            );

        }


        // ----------------------------------------------------
        // SESSION EXPIRED
        // ----------------------------------------------------

        if (
            response.status === 401
        ) {

            window.location.href =
                "/driver/login?expired=1";

            return;

        }


        // ----------------------------------------------------
        // ERROR
        // ----------------------------------------------------

        if (
            !response.ok
            ||
            !data
            ||
            data.success !== true
        ) {

            throw new Error(
                (
                    data
                    &&
                    data.message
                )
                    ||
                    "Gagal mengubah status layanan."
            );

        }


        // ----------------------------------------------------
        // SERVER IS SOURCE OF TRUTH
        // ----------------------------------------------------

        const serverState =
            normalizeServiceState(
                data.service_open
            );


        updateServiceControlUI(
            serverState
        );


        showServiceMessage(
            data.message
            ||
            (
                serverState
                    ? "Layanan berhasil dibuka."
                    : "Layanan berhasil ditutup."
            )
        );


        console.log(
            "[SERVICE UPDATED]",
            {
                service_open:
                    serverState
            }
        );


        // ----------------------------------------------------
        // VERIFY AGAIN FROM PUBLIC API
        // ----------------------------------------------------

        window.setTimeout(
            function () {

                syncDriverServiceStatus();

            },
            300
        );


        window.setTimeout(
            function () {

                showServiceMessage(
                    ""
                );

            },
            2500
        );

    }

    catch (error) {

        console.error(
            "[SERVICE STATUS ERROR]",
            error
        );


        showServiceMessage(
            error.message
            ||
            "Status layanan belum berhasil diubah."
        );


        // Kembalikan UI berdasarkan server.
        await syncDriverServiceStatus();

    }

    finally {

        serviceToggleBusy =
            false;


        serviceToggleButton.disabled =
            false;

    }

}


// ============================================================
// CLICK EVENT
// ============================================================

if (serviceToggleButton) {

    serviceToggleButton.addEventListener(
        "click",
        toggleDriverService
    );

}


// ============================================================
// INITIAL STATE
// ============================================================

if (serviceControl) {

    // Tampilkan state dari HTML terlebih dahulu.
    updateServiceControlUI(
        serviceControl.dataset.serviceOpen
    );


    // Kemudian ambil status terbaru langsung dari server.
    syncDriverServiceStatus();

}


// ============================================================
// RE-SYNC WHEN DRIVER RETURNS TO TAB
// ============================================================

window.addEventListener(
    "focus",
    function () {

        syncDriverServiceStatus();

    }
);


document.addEventListener(
    "visibilitychange",
    function () {

        if (
            document.visibilityState
            === "visible"
        ) {

            syncDriverServiceStatus();

        }

    }
);

// ============================================================
// PHASE 12
// DRIVER NEW ORDER NOTIFICATIONS
// ============================================================


// ============================================================
// ELEMENTS
// ============================================================

const notifyControl =
    document.getElementById(
        "driverNotificationControl"
    );


const notifyEnableButton =
    document.getElementById(
        "enableDriverNotifications"
    );


const notifyStatusText =
    document.getElementById(
        "driverNotificationStatus"
    );


const notifyCountElement =
    document.getElementById(
        "driverNotificationCount"
    );


const notifyToast =
    document.getElementById(
        "driverOrderNotification"
    );


const notifyToastTitle =
    document.getElementById(
        "driverOrderNotificationTitle"
    );


const notifyToastMessage =
    document.getElementById(
        "driverOrderNotificationMessage"
    );


const notifyToastOpen =
    document.getElementById(
        "driverOrderNotificationOpen"
    );


// ============================================================
// STATE
// ============================================================

const notifyBaseTitle =
    document.title;


let notifyLastOrderId =
    notifyControl
        ? Number(
            notifyControl.dataset.latestOrderId
            || 0
        )
        : 0;


let notifyUnreadCount =
    0;


let notifyOptIn =
    (
        localStorage.getItem(
            "driverNotificationsEnabled"
        )
        === "1"
    );


let notifyAudioContext =
    null;


let notifyAudioUnlocked =
    false;


// ============================================================
// UPDATE NOTIFICATION CONTROL
// ============================================================

function updateDriverNotificationControl() {

    if (!notifyEnableButton) {
        return;
    }


    notifyEnableButton.setAttribute(
        "aria-pressed",
        notifyOptIn
            ? "true"
            : "false"
    );


    notifyEnableButton.classList.toggle(
        "is-active",
        notifyOptIn
    );


    if (!notifyOptIn) {

        notifyEnableButton.textContent =
            "Aktifkan";


        if (notifyStatusText) {

            notifyStatusText.textContent =
                "Notifikasi pesanan sedang nonaktif.";

        }


        return;

    }


    notifyEnableButton.textContent =
        "Nonaktifkan";


    if (notifyStatusText) {

        notifyStatusText.textContent =
            notifyAudioUnlocked
                ? "Notifikasi dan suara pesanan aktif."
                : "Notifikasi aktif. Suara akan aktif setelah interaksi.";

    }

}


// ============================================================
// AUDIO
// ============================================================

async function unlockDriverNotificationAudio() {

    const AudioContextClass =
        (
            window.AudioContext
            ||
            window.webkitAudioContext
        );


    if (!AudioContextClass) {

        return false;

    }


    try {

        if (!notifyAudioContext) {

            notifyAudioContext =
                new AudioContextClass();

        }


        if (
            notifyAudioContext.state
            === "suspended"
        ) {

            await notifyAudioContext.resume();

        }


        notifyAudioUnlocked =
            true;


        return true;

    }

    catch (error) {

        console.warn(
            "[NOTIFICATION AUDIO]",
            error
        );


        return false;

    }

}


// ============================================================
// PLAY ORDER SOUND
// ============================================================

function playDriverOrderSound() {

    if (
        !notifyOptIn
        ||
        !notifyAudioUnlocked
        ||
        !notifyAudioContext
    ) {

        return;

    }


    try {

        const now =
            notifyAudioContext.currentTime;


        const frequencies = [
            660,
            880
        ];


        frequencies.forEach(
            function (
                frequency,
                index
            ) {

                const oscillator =
                    notifyAudioContext
                        .createOscillator();


                const gain =
                    notifyAudioContext
                        .createGain();


                const startTime =
                    (
                        now
                        +
                        (
                            index
                            * 0.18
                        )
                    );


                oscillator.type =
                    "sine";


                oscillator.frequency.value =
                    frequency;


                gain.gain.setValueAtTime(
                    0.0001,
                    startTime
                );


                gain.gain.exponentialRampToValueAtTime(
                    0.15,
                    startTime + 0.02
                );


                gain.gain.exponentialRampToValueAtTime(
                    0.0001,
                    startTime + 0.14
                );


                oscillator.connect(
                    gain
                );


                gain.connect(
                    notifyAudioContext.destination
                );


                oscillator.start(
                    startTime
                );


                oscillator.stop(
                    startTime + 0.15
                );

            }
        );

    }

    catch (error) {

        console.warn(
            "[ORDER SOUND]",
            error
        );

    }

}


// ============================================================
// BROWSER NOTIFICATION
// ============================================================

function showDriverBrowserNotification(
    order
) {

    if (
        !notifyOptIn
        ||
        !(
            "Notification"
            in window
        )
        ||
        Notification.permission
            !== "granted"
    ) {

        return;

    }


    try {

        const notification =
            new Notification(
                "Pesanan Baru",
                {
                    body:
                        (
                            order.customer_name
                            +
                            " • "
                            +
                            order.order_code
                        ),

                    tag:
                        (
                            "ojek-order-"
                            +
                            order.id
                        ),
                }
            );


        notification.onclick =
            function () {

                window.focus();


                window.location.href =
                    "/driver";


                notification.close();

            };

    }

    catch (error) {

        console.warn(
            "[BROWSER NOTIFICATION]",
            error
        );

    }

}


// ============================================================
// ENABLE NOTIFICATIONS
// ============================================================

async function enableDriverNotifications() {

    notifyOptIn =
        true;


    localStorage.setItem(
        "driverNotificationsEnabled",
        "1"
    );


    await unlockDriverNotificationAudio();


    if (
        "Notification"
        in window
        &&
        Notification.permission
            === "default"
    ) {

        try {

            await Notification
                .requestPermission();

        }

        catch (error) {

            console.warn(
                "[NOTIFICATION PERMISSION]",
                error
            );

        }

    }


    updateDriverNotificationControl();

}


// ============================================================
// DISABLE NOTIFICATIONS
// ============================================================

async function disableDriverNotifications() {

    notifyOptIn =
        false;


    localStorage.setItem(
        "driverNotificationsEnabled",
        "0"
    );


    notifyAudioUnlocked =
        false;


    if (
        notifyAudioContext
        &&
        notifyAudioContext.state
            === "running"
    ) {

        try {

            await notifyAudioContext.suspend();

        }

        catch (error) {

            console.warn(
                "[NOTIFICATION AUDIO]",
                error
            );

        }

    }


    notifyUnreadCount =
        0;


    updateDriverNotificationCount();


    if (notifyToast) {

        notifyToast.classList.remove(
            "show"
        );


        notifyToast.hidden =
            true;

    }


    updateDriverNotificationControl();

}


// ============================================================
// TOGGLE NOTIFICATIONS
// ============================================================

async function toggleDriverNotifications() {

    if (notifyOptIn) {

        await disableDriverNotifications();

        return;

    }


    await enableDriverNotifications();

}


// ============================================================
// NOTIFICATION COUNT
// ============================================================

function updateDriverNotificationCount() {

    if (!notifyCountElement) {

        return;

    }


    if (
        notifyUnreadCount
        <= 0
    ) {

        notifyCountElement.hidden =
            true;


        notifyCountElement.textContent =
            "0";


        document.title =
            notifyBaseTitle;


        return;

    }


    notifyCountElement.hidden =
        false;


    notifyCountElement.textContent =
        String(
            notifyUnreadCount
        );


    document.title =
        (
            "("
            +
            notifyUnreadCount
            +
            ") "
            +
            notifyBaseTitle
        );

}


// ============================================================
// SHOW NEW ORDER TOAST
// ============================================================

function showDriverNewOrderToast(
    order,
    totalNewOrders
) {

    if (!notifyToast) {

        return;

    }


    if (notifyToastTitle) {

        notifyToastTitle.textContent =
            (
                totalNewOrders > 1
                    ? (
                        totalNewOrders
                        +
                        " pesanan baru"
                    )
                    : (
                        "Pesanan "
                        +
                        order.order_code
                    )
            );

    }


    if (notifyToastMessage) {

        notifyToastMessage.textContent =
            (
                order.customer_name
                +
                " • "
                +
                order.pickup
            );

    }


    notifyToast.hidden =
        false;


    notifyToast.classList.remove(
        "show"
    );


    void notifyToast.offsetWidth;


    notifyToast.classList.add(
        "show"
    );

}


// ============================================================
// MARK AS READ
// ============================================================

function markDriverNotificationsRead() {

    notifyUnreadCount =
        0;


    updateDriverNotificationCount();


    if (notifyToast) {

        notifyToast.classList.remove(
            "show"
        );


        window.setTimeout(
            function () {

                notifyToast.hidden =
                    true;

            },
            250
        );

    }

}


// ============================================================
// POLL NEW ORDERS
// ============================================================

async function pollDriverNewOrders() {

    if (!notifyControl) {

        return;

    }


    try {

        const response =
            await fetch(
                (
                    "/api/driver/new-orders"
                    +
                    "?after_id="
                    +
                    encodeURIComponent(
                        notifyLastOrderId
                    )
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


        const data =
            await response.json();


        // Session driver berakhir.
        if (
            response.status
            === 401
        ) {

            window.location.href =
                "/driver/login?expired=1";


            return;

        }


        if (
            !response.ok
            ||
            !data.success
        ) {

            throw new Error(
                data.message
                ||
                "Gagal memeriksa pesanan baru."
            );

        }


        const newOrders =
            Array.isArray(
                data.orders
            )
                ? data.orders
                : [];


        if (
    newOrders.length
    > 0
) {

    const latestNewOrder =
        newOrders[
            newOrders.length - 1
        ];


    if (notifyOptIn) {

        notifyUnreadCount +=
            newOrders.length;


        updateDriverNotificationCount();


        showDriverNewOrderToast(
            latestNewOrder,
            newOrders.length
        );


        playDriverOrderSound();


        showDriverBrowserNotification(
            latestNewOrder
        );


        if (
            "vibrate"
            in navigator
        ) {

            navigator.vibrate(
                [
                    150,
                    80,
                    150
                ]
            );

        }

    }

}


        const serverLatestId =
            Number(
                data.latest_order_id
                || 0
            );


        notifyLastOrderId =
            Math.max(
                notifyLastOrderId,
                serverLatestId
            );

    }

    catch (error) {

        console.warn(
            "[NEW ORDER POLLING]",
            error
        );

    }

}


// ============================================================
// EVENTS
// ============================================================

if (notifyEnableButton) {

    notifyEnableButton.addEventListener(
        "click",
        toggleDriverNotifications
    );

}


if (notifyToastOpen) {

    notifyToastOpen.addEventListener(
        "click",
        markDriverNotificationsRead
    );

}


// ============================================================
// INITIALIZE
// ============================================================

updateDriverNotificationControl();


// Cek setiap 4 detik.
window.setInterval(
    pollDriverNewOrders,
    4000
);

// ============================================================
// PHASE 18F
// DRIVER NETWORK STATUS
// ============================================================

const driverNetworkStatus =
    document.getElementById(
        "driverNetworkStatus"
    );


function updateDriverNetworkStatus() {

    const isOffline =
        navigator.onLine
        === false;


    if (driverNetworkStatus) {

        driverNetworkStatus.hidden =
            !isOffline;

    }


    document.body.classList.toggle(
        "driver-is-offline",
        isOffline
    );

}


window.addEventListener(
    "online",
    function () {

        updateDriverNetworkStatus();


        showDriverToast(
            "Koneksi internet kembali aktif."
        );

    }
);


window.addEventListener(
    "offline",
    function () {

        updateDriverNetworkStatus();

    }
);


updateDriverNetworkStatus();