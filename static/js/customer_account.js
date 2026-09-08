"use strict";


// ============================================================
// PHASE 24
// CUSTOMER ACTIVE ORDER DASHBOARD
// ============================================================

const customerActiveOrders =
    document.getElementById(
        "customerActiveOrders"
    );


const customerActiveRefresh =
    document.getElementById(
        "customerActiveRefresh"
    );


function escapeCustomerHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


function formatCustomerRupiah(
    value
) {

    const amount =
        Number(
            value
            || 0
        );


    return (
        "Rp"
        +
        Math.round(
            amount
        )
        .toLocaleString(
            "id-ID"
        )
    );

}


function renderCustomerActiveOrders(
    orders
) {

    if (!customerActiveOrders) {
        return;
    }


    if (
        !Array.isArray(
            orders
        )
        ||
        orders.length === 0
    ) {

        customerActiveOrders.innerHTML = `
            <div class="customer-active-empty">

                <strong>
                    Tidak ada pesanan aktif.
                </strong>

                <p>
                    Pesanan baru Anda akan muncul di sini.
                </p>

                <a href="/">
                    Pesan Perjalanan
                </a>

            </div>
        `;


        return;

    }


    customerActiveOrders.innerHTML =
        orders
        .map(
            function(order) {

                return `
                    <a
                        href="${escapeCustomerHtml(order.detail_url)}"
                        class="customer-active-order"
                    >

                        <div class="customer-active-top">

                            <strong>
                                ${escapeCustomerHtml(order.order_code)}
                            </strong>

                            <span>
                                ${escapeCustomerHtml(order.status)}
                            </span>

                        </div>


                        <div class="customer-active-route">

                            <div>

                                <small>
                                    JEMPUT
                                </small>

                                <p>
                                    ${escapeCustomerHtml(order.pickup)}
                                </p>

                            </div>


                            <div>

                                <small>
                                    TUJUAN
                                </small>

                                <p>
                                    ${escapeCustomerHtml(order.destination)}
                                </p>

                            </div>

                        </div>


                        <div class="customer-active-bottom">

                            <span>
                                ${escapeCustomerHtml(order.distance_km)} km
                            </span>

                            <strong>
                                ${formatCustomerRupiah(order.fare)}
                            </strong>

                        </div>

                    </a>
                `;

            }
        )
        .join("");

}


async function refreshCustomerActiveOrders() {

    if (!customerActiveOrders) {
        return;
    }


    try {

        if (customerActiveRefresh) {

            customerActiveRefresh.textContent =
                "MEMUAT";

        }


        const response =
            await fetch(
                "/api/customer/active-orders",
                {
                    method:
                        "GET",

                    credentials:
                        "same-origin",

                    cache:
                        "no-store",
                }
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        if (
            !data
            ||
            data.success !== true
        ) {

            return;

        }


        renderCustomerActiveOrders(
            data.orders
        );


    }

    catch (error) {

        console.warn(
            "[CUSTOMER ACTIVE ORDERS]",
            error
        );

    }

    finally {

        if (customerActiveRefresh) {

            customerActiveRefresh.textContent =
                "LIVE";

        }

    }

}


if (customerActiveOrders) {

    window.setInterval(
        refreshCustomerActiveOrders,
        15000
    );

}

// ============================================================
// PHASE 25
// CUSTOMER NOTIFICATION SYSTEM
// ============================================================

const customerNotificationCenter =
    document.getElementById(
        "customerNotificationCenter"
    );


const customerNotificationToggle =
    document.getElementById(
        "customerNotificationToggle"
    );


const customerNotificationPanel =
    document.getElementById(
        "customerNotificationPanel"
    );


const customerNotificationCount =
    document.getElementById(
        "customerNotificationCount"
    );


const customerNotificationList =
    document.getElementById(
        "customerNotificationList"
    );


const customerNotificationReadAll =
    document.getElementById(
        "customerNotificationReadAll"
    );


const customerNotificationCsrf =
    customerNotificationCenter
        ? String(
            customerNotificationCenter
                .dataset
                .csrfToken
            || ""
        )
        : "";


let customerNotificationInitialized =
    false;


const knownCustomerNotificationIds =
    new Set();


// ============================================================
// ESCAPE
// ============================================================

function escapeCustomerNotificationHtml(
    value
) {

    return String(
        value ?? ""
    )
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


// ============================================================
// TOAST
// ============================================================

function showCustomerNotificationToast(
    notification
) {

    const toast =
        document.createElement(
            "div"
        );


    toast.className =
        "customer-notification-toast";


    const title =
        document.createElement(
            "strong"
        );


    title.textContent =
        notification.title
        || "Notifikasi";


    const message =
        document.createElement(
            "span"
        );


    message.textContent =
        notification.message
        || "";


    toast.append(
        title,
        message
    );


    document.body.appendChild(
        toast
    );


    window.setTimeout(
        function() {

            toast.classList.add(
                "show"
            );

        },
        50
    );


    window.setTimeout(
        function() {

            toast.remove();

        },
        5000
    );

}


// ============================================================
// RENDER
// ============================================================

function renderCustomerNotifications(
    notifications,
    unreadCount
) {

    if (
        customerNotificationCount
    ) {

        customerNotificationCount.textContent =
            String(
                unreadCount
                || 0
            );


        customerNotificationCount.hidden =
            !unreadCount;

    }


    if (!customerNotificationList) {
        return;
    }


    if (
        !Array.isArray(
            notifications
        )
        ||
        notifications.length === 0
    ) {

        customerNotificationList.innerHTML =
            `
                <p class="customer-notification-empty">
                    Belum ada notifikasi.
                </p>
            `;


        return;

    }


    customerNotificationList.innerHTML =
        notifications
            .map(
                function(notification) {

                    return `
                        <a
                            href="${escapeCustomerNotificationHtml(
                                notification.detail_url
                            )}"
                            class="customer-notification-item ${
                                notification.is_read
                                    ? ""
                                    : "is-unread"
                            }"
                            data-notification-id="${
                                Number(notification.id)
                            }"
                        >

                            <strong>
                                ${escapeCustomerNotificationHtml(
                                    notification.title
                                )}
                            </strong>

                            <p>
                                ${escapeCustomerNotificationHtml(
                                    notification.message
                                )}
                            </p>

                            <small>
                                ${escapeCustomerNotificationHtml(
                                    notification.created_at
                                )}
                            </small>

                        </a>
                    `;

                }
            )
            .join("");

}


// ============================================================
// FETCH
// ============================================================

async function refreshCustomerNotifications() {

    if (!customerNotificationCenter) {
        return;
    }


    try {

        const response =
            await fetch(
                "/api/customer/notifications",
                {
                    method:
                        "GET",

                    credentials:
                        "same-origin",

                    cache:
                        "no-store",

                    headers: {
                        "Accept":
                            "application/json"
                    }
                }
            );


        if (!response.ok) {
            return;
        }


        const data =
            await response.json();


        if (
            !data
            ||
            data.success !== true
        ) {

            return;

        }


        const notifications =
            Array.isArray(
                data.notifications
            )
                ? data.notifications
                : [];


        if (
            customerNotificationInitialized
        ) {

            notifications.forEach(
                function(notification) {

                    const id =
                        Number(
                            notification.id
                        );


                    if (
                        !notification.is_read
                        &&
                        !knownCustomerNotificationIds.has(
                            id
                        )
                    ) {

                        showCustomerNotificationToast(
                            notification
                        );

                    }

                }
            );

        }


        notifications.forEach(
            function(notification) {

                knownCustomerNotificationIds.add(
                    Number(
                        notification.id
                    )
                );

            }
        );


        customerNotificationInitialized =
            true;


        renderCustomerNotifications(
            notifications,
            data.unread_count
        );


    }

    catch (error) {

        console.warn(
            "[CUSTOMER NOTIFICATIONS]",
            error
        );

    }

}


// ============================================================
// MARK READ
// ============================================================

async function markCustomerNotificationRead(
    notificationId = null,
    markAll = false
) {

    const response =
        await fetch(
            "/api/customer/notifications/read",
            {
                method:
                    "POST",

                credentials:
                    "same-origin",

                cache:
                    "no-store",

                headers: {

                    "Content-Type":
                        "application/json",

                    "Accept":
                        "application/json",

                    "X-CSRF-Token":
                        customerNotificationCsrf

                },

                body:
                    JSON.stringify(
                        markAll
                            ? {
                                all:
                                    true
                            }
                            : {
                                notification_id:
                                    notificationId
                            }
                    )
            }
        );


    if (response.ok) {

        await refreshCustomerNotifications();

    }

}


// ============================================================
// OPEN / CLOSE
// ============================================================

if (
    customerNotificationToggle
    &&
    customerNotificationPanel
) {

    customerNotificationToggle.addEventListener(
        "click",
        function() {

            const opening =
                customerNotificationPanel.hidden;


            customerNotificationPanel.hidden =
                !opening;


            customerNotificationToggle.setAttribute(
                "aria-expanded",
                opening
                    ? "true"
                    : "false"
            );

        }
    );

}


// ============================================================
// MARK ALL
// ============================================================

if (
    customerNotificationReadAll
) {

    customerNotificationReadAll.addEventListener(
        "click",
        function() {

            markCustomerNotificationRead(
                null,
                true
            );

        }
    );

}


// ============================================================
// NOTIFICATION CLICK
// ============================================================

if (
    customerNotificationList
) {

    customerNotificationList.addEventListener(
        "click",
        async function(event) {

            const item =
                event.target.closest(
                    ".customer-notification-item"
                );


            if (!item) {
                return;
            }


            const notificationId =
                Number(
                    item.dataset.notificationId
                );


            if (!notificationId) {
                return;
            }


            event.preventDefault();


            await markCustomerNotificationRead(
                notificationId,
                false
            );


            window.location.href =
                item.href;

        }
    );

}


// ============================================================
// INITIAL + POLLING
// ============================================================

refreshCustomerNotifications();


window.setInterval(
    refreshCustomerNotifications,
    10000
);