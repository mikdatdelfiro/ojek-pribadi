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

async function updateOrderStatus(
    button
) {

    const orderId =
        button.dataset.id;


    const status =
        button.dataset.status;


    // Konfirmasi khusus penolakan.
    if (status === "DITOLAK") {

        const confirmed =
            window.confirm(
                "Tolak pesanan ini?"
            );


        if (!confirmed) {
            return;
        }

    }


    const originalText =
        button.innerHTML;


    button.disabled = true;


    button.innerHTML =
        `
        <span class="button-loading-dot"></span>
        Memproses...
        `;


    try {

        const response =
            await fetch(
                `/api/orders/${orderId}/status`,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                status:
                                    status
                            }
                        )
                }
            );


        const data =
            await response.json();

        if (
            response.status === 401
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
                "Gagal memperbarui pesanan."
            );

        }


        showDriverToast(
            data.message
        );


        const card =
            button.closest(
                ".driver-order-card"
            );


        if (card) {

            card.classList.add(
                "status-changing"
            );

        }


        setTimeout(
            function () {

                window.location.reload();

            },
            650
        );

    }

    catch (error) {

        alert(
            error.message
        );


        button.disabled = false;

        button.innerHTML =
            originalText;

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

// =====================================================
// PHASE 9
// DRIVER SERVICE CONTROL
// =====================================================

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


// =====================================================
// UPDATE SERVICE UI
// =====================================================

function updateServiceControlUI(
    isOpen
) {

    if (!serviceControl) {
        return;
    }


    serviceControl.dataset.serviceOpen =
        isOpen
            ? "true"
            : "false";


    serviceControl.classList.toggle(
        "is-open",
        isOpen
    );


    serviceControl.classList.toggle(
        "is-closed",
        !isOpen
    );


    if (serviceToggleButton) {

        serviceToggleButton.setAttribute(
            "aria-pressed",
            isOpen
                ? "true"
                : "false"
        );

    }


    if (serviceStatusLabel) {

        serviceStatusLabel.textContent =
            isOpen
                ? "MENERIMA PESANAN"
                : "SEDANG TIDAK MELAYANI";

    }


    if (serviceStatusDescription) {

        serviceStatusDescription.textContent =
            isOpen
                ? (
                    "Pelanggan dapat membuat "
                    + "pesanan baru."
                )
                : (
                    "Pesanan baru sedang "
                    + "dinonaktifkan."
                );

    }

}


// =====================================================
// TOGGLE SERVICE
// =====================================================

async function toggleDriverService() {

    if (
        !serviceControl
        ||
        !serviceToggleButton
    ) {
        return;
    }


    const currentlyOpen =
        serviceControl.dataset.serviceOpen
        === "true";


    const nextState =
        !currentlyOpen;


    serviceToggleButton.disabled =
        true;


    if (serviceControlMessage) {

        serviceControlMessage.textContent =
            "Memperbarui status...";

    }


    try {

        const response = await fetch(
            "/api/driver/service-status",
            {
                method:
                    "POST",

                headers: {
                    "Content-Type":
                        "application/json",
                },

                body:
                    JSON.stringify(
                        {
                            service_open:
                                nextState,
                        }
                    ),
            }
        );


        const data =
            await response.json();


        // Session expired.
        if (
            response.status === 401
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
                "Gagal mengubah status layanan."
            );

        }


        updateServiceControlUI(
            data.service_open
        );


        if (serviceControlMessage) {

            serviceControlMessage.textContent =
                data.message;

        }


        window.setTimeout(
            function () {

                if (
                    serviceControlMessage
                ) {

                    serviceControlMessage.textContent =
                        "";

                }

            },
            2500
        );

    }

    catch (error) {

        console.error(
            "[SERVICE STATUS]",
            error
        );


        if (serviceControlMessage) {

            serviceControlMessage.textContent =
                error.message;

        }

    }

    finally {

        serviceToggleButton.disabled =
            false;

    }

}


// =====================================================
// EVENT
// =====================================================

if (serviceToggleButton) {

    serviceToggleButton.addEventListener(
        "click",
        toggleDriverService
    );

}

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


    if (!notifyOptIn) {

        notifyEnableButton.textContent =
            "Aktifkan";


        if (notifyStatusText) {

            notifyStatusText.textContent =
                (
                    "Aktifkan suara dan "
                    +
                    "notifikasi browser."
                );

        }


        return;

    }


    if (
        notifyOptIn
        &&
        !notifyAudioUnlocked
    ) {

        notifyEnableButton.textContent =
            "Aktifkan Suara";


        if (notifyStatusText) {

            notifyStatusText.textContent =
                (
                    "Notifikasi aktif. "
                    +
                    "Klik untuk mengaktifkan suara."
                );

        }


        return;

    }


    notifyEnableButton.textContent =
        "Notifikasi Aktif";


    if (notifyStatusText) {

        notifyStatusText.textContent =
            (
                "Siap memberi tahu "
                +
                "ketika pesanan baru masuk."
            );

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
    ) {

        if (
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

    }


    updateDriverNotificationControl();

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
        enableDriverNotifications
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