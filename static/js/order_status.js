"use strict";


// ============================================================
// OJEK PRIBADI
// CUSTOMER LIVE ORDER STATUS
// PHASE 20I.3F - CUSTOMER REFUND STATUS + SECURE RECEIPT
//
// FULL REPLACEMENT
// ------------------------------------------------------------
// Dipertahankan:
// - Live tracking
// - Driver profile
// - Driver trust
// - Journey timeline
// - Customer review
// - Payment confirmation QRIS / Transfer
// - Payment experience
// - Payment copy
// - Payment toast
// - Customer notifications
// - Customer contact driver
// - Polling
//
// Diperbaiki:
// - Receipt tidak lagi membuka /order/.../receipt#token=...
// - Receipt memakai secure API + X-Receipt-Token
// - Receipt token dibaca dari sessionStorage
// - Cash payment tetap dipantau setelah status SELESAI
// - Receipt muncul setelah SELESAI + DIBAYAR
// ============================================================


// ============================================================
// DOM HELPER
// ============================================================

function getElement(
    id,
    required = true
) {

    const element =
        document.getElementById(
            id
        );


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
        ? String(
            trackingPage.dataset.orderCode
            || ""
        )
            .trim()
            .toUpperCase()
        : "";


const initialStatus =
    trackingPage
        ? String(
            trackingPage.dataset.initialStatus
            || "MENUNGGU"
        )
            .trim()
            .toUpperCase()
        : "MENUNGGU";


// ============================================================
// PHASE 19E
// PRIVATE REVIEW ACCESS TOKEN
// ============================================================

const reviewTokenStorageKey =
    (
        "ojek_pribadi_review_token_"
        +
        orderCode
    );


function getReviewTokenFromHash() {

    const rawHash =
        window.location.hash
            .replace(
                /^#/,
                ""
            );


    if (!rawHash) {

        return "";

    }


    const params =
        new URLSearchParams(
            rawHash
        );


    return String(
        params.get(
            "review_token"
        )
        || ""
    ).trim();

}


function resolveCustomerReviewToken() {

    const hashToken =
        getReviewTokenFromHash();


    if (hashToken) {

        try {

            sessionStorage.setItem(
                reviewTokenStorageKey,
                hashToken
            );

        }

        catch (error) {

            console.warn(
                "[REVIEW TOKEN]",
                error
            );

        }


        // Hilangkan review_token dari address bar
        // setelah berhasil dibaca.
        window.history.replaceState(
            null,
            "",
            (
                window.location.pathname
                +
                window.location.search
            )
        );


        return hashToken;

    }


    try {

        return String(
            sessionStorage.getItem(
                reviewTokenStorageKey
            )
            || ""
        ).trim();

    }

    catch (error) {

        console.warn(
            "[REVIEW TOKEN STORAGE]",
            error
        );


        return "";

    }

}


const customerReviewToken =
    resolveCustomerReviewToken();


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
// PHASE 20D
// PAYMENT CONFIRMATION DOM
// ============================================================

const customerPaymentConfirmButton =
    document.getElementById(
        "customerPaymentConfirmButton"
    );


const customerPaymentConfirmArea =
    document.getElementById(
        "customerPaymentConfirmArea"
    );


const customerPaymentConfirmMessage =
    document.getElementById(
        "customerPaymentConfirmMessage"
    );

// ============================================================
// PHASE 20I.3B
// CUSTOMER REFUND REQUEST DOM
// ============================================================

const customerRefundRequestArea =
    document.getElementById(
        "customerRefundRequestArea"
    );


const customerRefundRequestReason =
    document.getElementById(
        "customerRefundRequestReason"
    );


const customerRefundRequestButton =
    document.getElementById(
        "customerRefundRequestButton"
    );


const customerRefundRequestMessage =
    document.getElementById(
        "customerRefundRequestMessage"
    );


// ============================================================
// PHASE 20I.3F
// CUSTOMER REFUND STATUS DOM
// ============================================================

const customerRefundStatusCard =
    document.getElementById(
        "customerRefundStatusCard"
    );


const customerRefundStatusIcon =
    document.getElementById(
        "customerRefundStatusIcon"
    );


const customerRefundStatusTitle =
    document.getElementById(
        "customerRefundStatusTitle"
    );


const customerRefundStatusDescription =
    document.getElementById(
        "customerRefundStatusDescription"
    );


const customerRefundStatusBadge =
    document.getElementById(
        "customerRefundStatusBadge"
    );


const customerRefundRequestReasonBlock =
    document.getElementById(
        "customerRefundRequestReasonBlock"
    );


const customerRefundRequestReasonText =
    document.getElementById(
        "customerRefundRequestReasonText"
    );


const customerRefundRejectionBlock =
    document.getElementById(
        "customerRefundRejectionBlock"
    );


const customerRefundRejectionReasonText =
    document.getElementById(
        "customerRefundRejectionReasonText"
    );


const customerRefundAmountBlock =
    document.getElementById(
        "customerRefundAmountBlock"
    );


const customerRefundAmountText =
    document.getElementById(
        "customerRefundAmountText"
    );


const customerRefundRequestedAtBlock =
    document.getElementById(
        "customerRefundRequestedAtBlock"
    );


const customerRefundRequestedAtText =
    document.getElementById(
        "customerRefundRequestedAtText"
    );


const customerRefundReviewedAtBlock =
    document.getElementById(
        "customerRefundReviewedAtBlock"
    );


const customerRefundReviewedAtText =
    document.getElementById(
        "customerRefundReviewedAtText"
    );


const customerRefundedAtBlock =
    document.getElementById(
        "customerRefundedAtBlock"
    );


const customerRefundedAtText =
    document.getElementById(
        "customerRefundedAtText"
    );


const customerRefundStatusNotice =
    document.getElementById(
        "customerRefundStatusNotice"
    );

// ============================================================
// PHASE 20F
// CUSTOMER PAYMENT EXPERIENCE DOM
// ============================================================

const customerPaymentStatusBadge =
    document.getElementById(
        "customerPaymentStatusBadge"
    );


const customerPaymentLiveStatus =
    document.getElementById(
        "customerPaymentLiveStatus"
    );


const customerPaymentProgress =
    document.getElementById(
        "customerPaymentProgress"
    );


const customerPaymentToast =
    document.getElementById(
        "customerPaymentToast"
    );


const customerPaymentCopyButtons =
    document.querySelectorAll(
        ".customer-payment-copy-button"
    );


// ============================================================
// PHASE 20G
// LEGACY DIGITAL RECEIPT DOM
// ============================================================

const customerDigitalReceiptArea =
    document.getElementById(
        "customerDigitalReceiptArea"
    );


const customerDigitalReceiptButton =
    document.getElementById(
        "customerDigitalReceiptButton"
    );


// ============================================================
// PHASE 20G.3
// CUSTOMER DIGITAL RECEIPT DOM
// ============================================================

const customerReceiptConfig =
    document.getElementById(
        "customerReceiptConfig"
    );


const customerReceiptCard =
    document.getElementById(
        "customerReceiptCard"
    );


const customerReceiptMessage =
    document.getElementById(
        "customerReceiptMessage"
    );


const openCustomerReceiptButton =
    document.getElementById(
        "openCustomerReceiptButton"
    );


const customerReceiptModal =
    document.getElementById(
        "customerReceiptModal"
    );


const customerReceiptBackdrop =
    document.getElementById(
        "customerReceiptBackdrop"
    );


const closeCustomerReceiptButton =
    document.getElementById(
        "closeCustomerReceiptButton"
    );


const customerReceiptLoading =
    document.getElementById(
        "customerReceiptLoading"
    );


const customerReceiptError =
    document.getElementById(
        "customerReceiptError"
    );


const customerReceiptContent =
    document.getElementById(
        "customerReceiptContent"
    );

const customerReceiptPrintButton =
    document.getElementById(
        "customerReceiptPrintButton"
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
// PHASE 19D
// DRIVER TRUST
// ============================================================

const driverTrustArea =
    getElement(
        "driverTrustArea",
        false
    );


const driverTrustRating =
    getElement(
        "driverTrustRating",
        false
    );


const driverTrustLabel =
    getElement(
        "driverTrustLabel",
        false
    );


const driverTrustReviewCount =
    getElement(
        "driverTrustReviewCount",
        false
    );


const driverTrustCompleted =
    getElement(
        "driverTrustCompleted",
        false
    );


const driverTrustVehicle =
    getElement(
        "driverTrustVehicle",
        false
    );


const driverTrustContact =
    getElement(
        "driverTrustContact",
        false
    );


// ============================================================
// PHASE 19A
// CUSTOMER REVIEW ELEMENTS
// ============================================================

const customerReviewCard =
    getElement(
        "customerReviewCard",
        false
    );


const customerReviewForm =
    getElement(
        "customerReviewForm",
        false
    );


const customerReviewStars =
    document.querySelectorAll(
        ".customer-review-star"
    );


const customerReviewLabel =
    getElement(
        "customerReviewLabel",
        false
    );


const customerReviewMessage =
    getElement(
        "customerReviewMessage",
        false
    );


const customerReviewSubmit =
    getElement(
        "customerReviewSubmit",
        false
    );


const customerReviewSubmitText =
    getElement(
        "customerReviewSubmitText",
        false
    );


const customerReviewSuccess =
    getElement(
        "customerReviewSuccess",
        false
    );


const customerReviewResultStars =
    getElement(
        "customerReviewResultStars",
        false
    );


const customerReviewTagButtons =
    document.querySelectorAll(
        ".customer-review-tag"
    );


const customerReviewFeedback =
    getElement(
        "customerReviewFeedback",
        false
    );


const customerReviewFeedbackCount =
    getElement(
        "customerReviewFeedbackCount",
        false
    );


const customerReviewResultTags =
    getElement(
        "customerReviewResultTags",
        false
    );


const customerReviewResultFeedback =
    getElement(
        "customerReviewResultFeedback",
        false
    );


// ============================================================
// APPLICATION STATE
// ============================================================

let currentStatus =
    null;


let statusInterval =
    null;


let latestOrderData =
    null;


let selectedReviewTags =
    [];


let selectedReviewRating =
    0;


let reviewLoaded =
    false;


let reviewSubmitting =
    false;


let customerStatusToastTimer =
    null;


let customerPaymentToastTimer =
    null;


// ============================================================
// STATUS TIMESTAMP CONFIG
// ============================================================

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


// ============================================================
// PHASE 19A
// CUSTOMER RATING LABELS
// ============================================================

const reviewLabels = {

    1:
        "Kurang",

    2:
        "Cukup",

    3:
        "Baik",

    4:
        "Sangat Baik",

    5:
        "Luar Biasa"

};


// ============================================================
// PHASE 20F
// PAYMENT STATUS LABEL
// ============================================================

function getCustomerPaymentStatusLabel(
    paymentStatus
) {

    switch (
        String(
            paymentStatus
            || ""
        )
            .trim()
            .toUpperCase()
    ) {

        case "DIBAYAR":

            return "DIBAYAR";


        case "DIKEMBALIKAN":

            return "DIKEMBALIKAN";


        case "MENUNGGU_KONFIRMASI":

            return "MENUNGGU KONFIRMASI";


        case "MENUNGGU_PEMBAYARAN":

            return "MENUNGGU PEMBAYARAN";


        case "GAGAL":

            return "GAGAL";


        case "KEDALUWARSA":

            return "KEDALUWARSA";


        default:

            return "BELUM DIBAYAR";

    }

}


// ============================================================
// PHASE 20D
// CUSTOMER SUBMIT PAYMENT CONFIRMATION
//
// Hanya QRIS / Transfer.
// TUNAI dikonfirmasi oleh driver.
// ============================================================

async function submitCustomerPaymentConfirmation() {

    if (
        !orderCode
        ||
        !customerPaymentConfirmButton
    ) {

        return;

    }


    const customerConfirmed =
        window.confirm(
            (
                "Pastikan pembayaran benar-benar "
                +
                "sudah berhasil.\n\n"
                +
                "Kirim konfirmasi pembayaran sekarang?"
            )
        );


    if (!customerConfirmed) {

        return;

    }


    if (!customerReviewToken) {

                console.warn(
            "[PAYMENT] Token customer tidak tersedia."
        );


        if (
            customerPaymentConfirmMessage
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                (
                    "Akses pembayaran tidak tersedia. "
                    +
                    "Buka status dari perangkat "
                    +
                    "yang digunakan untuk memesan."
                );

        }


        return;

    }


    customerPaymentConfirmButton.disabled =
        true;


    const originalText =
        customerPaymentConfirmButton
            .textContent;


    customerPaymentConfirmButton.textContent =
        "Mengirim konfirmasi...";


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
                    "/payment/confirm"
                ),
                {

                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {

                        "Accept":
                            "application/json",

                        "Content-Type":
                            "application/json",

                        "X-Review-Token":
                            customerReviewToken

                    },

                    body:
                        JSON.stringify(
                            {}
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
                "Konfirmasi pembayaran gagal."
            );

        }


        if (
            customerPaymentConfirmArea
        ) {

            customerPaymentConfirmArea.hidden =
                true;

        }


        if (
            customerPaymentConfirmMessage
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                data.message
                ||
                "Konfirmasi pembayaran berhasil dikirim.";

        }


        window.setTimeout(
            function () {

                fetchOrderStatus();

            },
            300
        );

    }

    catch (error) {

        console.error(
            "[CUSTOMER PAYMENT CONFIRM]",
            error
        );


        customerPaymentConfirmButton.disabled =
            false;


        customerPaymentConfirmButton.textContent =
            originalText;


        if (
            customerPaymentConfirmMessage
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                (
                    error.message
                    ||
                    "Konfirmasi pembayaran gagal."
                );

        }

    }

}

// ============================================================
// PHASE 20I.3F
// REFUND FORMATTERS
// ============================================================

function formatCustomerRefundAmount(
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
        Math.max(
            0,
            amount
        ).toLocaleString(
            "id-ID"
        )
    );

}


function formatCustomerRefundTimestamp(
    value
) {

    const raw =
        String(
            value
            || ""
        ).trim();


    if (!raw) {

        return "-";

    }


    const match =
        raw.match(
            /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/
        );


    if (!match) {

        return raw;

    }


    return (
        match[3]
        +
        "/"
        +
        match[2]
        +
        "/"
        +
        match[1]
        +
        " • "
        +
        match[4]
        +
        ":"
        +
        match[5]
    );

}

// ============================================================
// PHASE 20I.3F
// LIVE CUSTOMER REFUND STATUS
// ============================================================

function renderCustomerRefundStatus(
    payment
) {

    if (!payment) {

        return;

    }


    const refundRequest =
        payment.refund_request
        || {};


    const status =
        String(
            refundRequest.status
            || "NONE"
        )
            .trim()
            .toUpperCase();


    // ========================================================
    // CUSTOMER REQUEST FORM
    // ========================================================

    if (
        customerRefundRequestArea
    ) {

        customerRefundRequestArea.hidden =
            !Boolean(
                refundRequest.can_customer_request
            );

    }


    // ========================================================
    // NONE
    // ========================================================

    if (
        status
        === "NONE"
    ) {

        if (
            customerRefundStatusCard
        ) {

            customerRefundStatusCard.hidden =
                true;

        }


        return;

    }


    if (
        !customerRefundStatusCard
    ) {

        return;

    }


    customerRefundStatusCard.hidden =
        false;


    customerRefundStatusCard.classList.remove(
        "is-pending",
        "is-rejected",
        "is-approved"
    );


    // ========================================================
    // COMMON DATA
    // ========================================================

    const requestReason =
        String(
            refundRequest.request_reason
            || ""
        ).trim();


    const rejectionReason =
        String(
            refundRequest.rejection_reason
            || ""
        ).trim();


    if (
        customerRefundRequestReasonBlock
    ) {

        customerRefundRequestReasonBlock.hidden =
            !requestReason;

    }


    if (
        customerRefundRequestReasonText
    ) {

        customerRefundRequestReasonText.textContent =
            requestReason;

    }


    if (
        customerRefundRequestedAtBlock
    ) {

        customerRefundRequestedAtBlock.hidden =
            !refundRequest.requested_at;

    }


    if (
        customerRefundRequestedAtText
    ) {

        customerRefundRequestedAtText.textContent =
            formatCustomerRefundTimestamp(
                refundRequest.requested_at
            );

    }


    // ========================================================
    // RESET FINAL/REJECTION ELEMENTS
    // ========================================================

    if (
        customerRefundRejectionBlock
    ) {

        customerRefundRejectionBlock.hidden =
            true;

    }


    if (
        customerRefundAmountBlock
    ) {

        customerRefundAmountBlock.hidden =
            true;

    }


    if (
        customerRefundReviewedAtBlock
    ) {

        customerRefundReviewedAtBlock.hidden =
            true;

    }


    if (
        customerRefundedAtBlock
    ) {

        customerRefundedAtBlock.hidden =
            true;

    }


    // ========================================================
    // PENDING
    // ========================================================

    if (
        status
        === "PENDING"
    ) {

        customerRefundStatusCard.classList.add(
            "is-pending"
        );


        if (
            customerRefundStatusIcon
        ) {

            customerRefundStatusIcon.textContent =
                "⏳";

        }


        if (
            customerRefundStatusBadge
        ) {

            customerRefundStatusBadge.textContent =
                "PENDING";

        }


        if (
            customerRefundStatusTitle
        ) {

            customerRefundStatusTitle.textContent =
                "Menunggu review driver";

        }


        if (
            customerRefundStatusDescription
        ) {

            customerRefundStatusDescription.textContent =
                (
                    "Permintaan pengembalian dana "
                    +
                    "Anda sedang diperiksa oleh driver."
                );

        }


        if (
            customerRefundStatusNotice
        ) {

            customerRefundStatusNotice.textContent =
                (
                    "Pembayaran tetap berstatus DIBAYAR "
                    +
                    "sampai driver benar-benar "
                    +
                    "memproses pengembalian dana."
                );

        }


        return;

    }


    // ========================================================
    // REJECTED
    // ========================================================

    if (
        status
        === "REJECTED"
    ) {

        customerRefundStatusCard.classList.add(
            "is-rejected"
        );


        if (
            customerRefundStatusIcon
        ) {

            customerRefundStatusIcon.textContent =
                "!";

        }


        if (
            customerRefundStatusBadge
        ) {

            customerRefundStatusBadge.textContent =
                "DITOLAK";

        }


        if (
            customerRefundStatusTitle
        ) {

            customerRefundStatusTitle.textContent =
                "Permintaan refund ditolak";

        }


        if (
            customerRefundStatusDescription
        ) {

            customerRefundStatusDescription.textContent =
                (
                    "Driver sudah meninjau "
                    +
                    "permintaan pengembalian dana Anda."
                );

        }


        if (
            customerRefundRejectionBlock
        ) {

            customerRefundRejectionBlock.hidden =
                !rejectionReason;
                }


        if (
            customerRefundRejectionReasonText
        ) {

            customerRefundRejectionReasonText.textContent =
                rejectionReason;

        }


        if (
            customerRefundReviewedAtBlock
        ) {

            customerRefundReviewedAtBlock.hidden =
                !refundRequest.reviewed_at;

        }


        if (
            customerRefundReviewedAtText
        ) {

            customerRefundReviewedAtText.textContent =
                formatCustomerRefundTimestamp(
                    refundRequest.reviewed_at
                );

        }


        if (
            customerRefundStatusNotice
        ) {

            customerRefundStatusNotice.textContent =
                (
                    "Dana tidak dikembalikan. "
                    +
                    "Pembayaran tetap tercatat DIBAYAR."
                );

        }


        return;

    }


    // ========================================================
    // APPROVED
    // ========================================================

    if (
        status
        === "APPROVED"
    ) {

        customerRefundStatusCard.classList.add(
            "is-approved"
        );


        if (
            customerRefundStatusIcon
        ) {

            customerRefundStatusIcon.textContent =
                "✓";

        }


        if (
            customerRefundStatusBadge
        ) {

            customerRefundStatusBadge.textContent =
                "DIKEMBALIKAN";

        }


        if (
            customerRefundStatusTitle
        ) {

            customerRefundStatusTitle.textContent =
                "Dana sudah dikembalikan";

        }


        if (
            customerRefundStatusDescription
        ) {

            customerRefundStatusDescription.textContent =
                (
                    "Driver telah mengonfirmasi "
                    +
                    "pengembalian dana Anda."
                );

        }


        if (
            customerRefundAmountBlock
        ) {

            customerRefundAmountBlock.hidden =
                false;

        }


        if (
            customerRefundAmountText
        ) {

            customerRefundAmountText.textContent =
                formatCustomerRefundAmount(
                    payment.refund_amount
                );

        }


        if (
            customerRefundReviewedAtBlock
        ) {

            customerRefundReviewedAtBlock.hidden =
                !refundRequest.reviewed_at;

        }


        if (
            customerRefundReviewedAtText
        ) {

            customerRefundReviewedAtText.textContent =
                formatCustomerRefundTimestamp(
                    refundRequest.reviewed_at
                );

        }


        if (
            customerRefundedAtBlock
        ) {

            customerRefundedAtBlock.hidden =
                !payment.refunded_at;

        }


        if (
            customerRefundedAtText
        ) {

            customerRefundedAtText.textContent =
                formatCustomerRefundTimestamp(
                    payment.refunded_at
                );

        }


        if (
            customerRefundStatusNotice
        ) {

            customerRefundStatusNotice.textContent =
                (
                    "Pembayaran sudah berstatus "
                    +
                    "DIKEMBALIKAN."
                );

        }

    }

}

// ============================================================
// PHASE 20F
// RENDER CUSTOMER PAYMENT EXPERIENCE
// ============================================================

function renderCustomerPaymentExperience(
    payment
) {

    if (!payment) {

        return;

    }


    const status =
        String(
            payment.status
            || ""
        )
            .trim()
            .toUpperCase();


    const method =
        String(
            payment.method
            || "TUNAI"
        )
            .trim()
            .toUpperCase();


    // ========================================================
    // STATUS BADGE
    // ========================================================

    if (
        customerPaymentStatusBadge
    ) {

        customerPaymentStatusBadge.textContent =
            getCustomerPaymentStatusLabel(
                status
            );


        customerPaymentStatusBadge.classList.remove(
            "is-paid",
            "is-review",
            "is-pending",
            "is-refunded"
        );


        if (
            status
            === "DIKEMBALIKAN"
        ) {

            customerPaymentStatusBadge.classList.add(
                "is-refunded"
            );

        }

        else if (
            status
            === "DIBAYAR"
        ) {

            customerPaymentStatusBadge.classList.add(
                "is-paid"
            );

        }

        else if (
            status
            === "MENUNGGU_KONFIRMASI"
        ) {

            customerPaymentStatusBadge.classList.add(
                "is-review"
            );

        }

        else {

            customerPaymentStatusBadge.classList.add(
                "is-pending"
            );

        }

    }


    // ========================================================
    // LIVE MESSAGE
    // ========================================================

    if (
        customerPaymentLiveStatus
    ) {

        if (
            status
            === "DIKEMBALIKAN"
        ) {

            customerPaymentLiveStatus.innerHTML =
                `
                    <span class="customer-payment-live-icon">
                        ↩
                    </span>

                    <div>
                        <strong>
                            Dana sudah dikembalikan
                        </strong>

                        <p>
                            Pengembalian dana telah
                            dikonfirmasi oleh driver.
                        </p>
                    </div>
                `;

        }

        else if (
            status
            === "DIBAYAR"
        ) {

            customerPaymentLiveStatus.innerHTML =
                `
                    <span class="customer-payment-live-icon">
                        ✓
                    </span>

                    <div>
                        <strong>
                            Pembayaran berhasil
                        </strong>

                        <p>
                            Pembayaran Anda sudah
                            dikonfirmasi oleh driver.
                        </p>
                    </div>
                `;

        }

        else if (
            status
            === "MENUNGGU_KONFIRMASI"
        ) {

            customerPaymentLiveStatus.innerHTML =
                `
                    <span class="customer-payment-live-icon">
                        ⏳
                    </span>

                    <div>
                        <strong>
                            Sedang diverifikasi
                        </strong>

                        <p>
                            Konfirmasi pembayaran sudah
                            dikirim. Tunggu driver
                            melakukan verifikasi.
                        </p>
                    </div>
                `;

        }

        else if (
            method
            === "TUNAI"
        ) {

            customerPaymentLiveStatus.innerHTML =
                `
                    <span class="customer-payment-live-icon">
                        Rp
                    </span>

                    <div>
                        <strong>
                            Pembayaran tunai
                        </strong>

                        <p>
                            Bayarkan tarif langsung
                            kepada driver.
                            Setelah perjalanan selesai,
                            driver akan mengonfirmasi
                            pembayaran tunai Anda.
                        </p>
                    </div>
                `;

        }

        else {

            customerPaymentLiveStatus.innerHTML =
                `
                    <span class="customer-payment-live-icon">
                        !
                    </span>

                    <div>
                        <strong>
                            Pembayaran belum selesai
                        </strong>

                        <p>
                            Selesaikan pembayaran
                            kemudian kirim konfirmasi.
                        </p>
                    </div>
                `;

        }

    }


    // ========================================================
    // CONFIRM BUTTON
    // ========================================================

    if (
        customerPaymentConfirmArea
    ) {

        customerPaymentConfirmArea.hidden =
            !payment.can_customer_confirm;

    }


    // ========================================================
    // CONFIRM MESSAGE
    // ========================================================

    if (
        customerPaymentConfirmMessage
    ) {

        if (
            status
            === "DIKEMBALIKAN"
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                "↩ Dana sudah dikembalikan.";

        }

        else if (
            status
            === "DIBAYAR"
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                "✓ Pembayaran sudah dikonfirmasi.";

        }

        else if (
            status
            === "MENUNGGU_KONFIRMASI"
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                (
                    "Konfirmasi sudah dikirim. "
                    +
                    "Menunggu verifikasi driver."
                );

        }

        else if (
            method
            === "TUNAI"
            &&
            latestOrderData
            &&
            latestOrderData.status
            === "SELESAI"
        ) {

            customerPaymentConfirmMessage.hidden =
                false;


            customerPaymentConfirmMessage.textContent =
                (
                    "Menunggu driver mengonfirmasi "
                    +
                    "pembayaran tunai."
                );

        }

        else {

            customerPaymentConfirmMessage.hidden =
                true;

        }

    }


    // ========================================================
    // PHASE 20I.3F
    // CUSTOMER REFUND LIVE STATUS
    // ========================================================

    renderCustomerRefundStatus(
        payment
    );


    updateCustomerPaymentProgress(
        payment
    );

}

// ============================================================
// PHASE 20I.3B
// SUBMIT CUSTOMER REFUND REQUEST
// ============================================================

async function submitCustomerRefundRequest() {

    if (
        !orderCode
        ||
        !customerRefundRequestButton
        ||
        !customerRefundRequestReason
    ) {

        return;

    }


    const reason =
        String(
            customerRefundRequestReason.value
            || ""
        ).trim();


    if (
        reason.length < 3
    ) {

        if (
            customerRefundRequestMessage
        ) {

            customerRefundRequestMessage.hidden =
                false;


            customerRefundRequestMessage.textContent =
                (
                    "Masukkan alasan pengembalian "
                    +
                    "dana minimal 3 karakter."
                );

        }


        customerRefundRequestReason.focus();

                return;

    }


    if (
        !customerReviewToken
    ) {

        if (
            customerRefundRequestMessage
        ) {

            customerRefundRequestMessage.hidden =
                false;


            customerRefundRequestMessage.textContent =
                (
                    "Akses pesanan tidak tersedia. "
                    +
                    "Buka status dari perangkat "
                    +
                    "yang digunakan untuk memesan."
                );

        }


        return;

    }


    const confirmed =
        window.confirm(
            (
                "Ajukan pengembalian dana?\n\n"
                +
                "Permintaan akan dikirim "
                +
                "kepada driver untuk diperiksa."
            )
        );


    if (!confirmed) {

        return;

    }


    const originalText =
        customerRefundRequestButton
            .textContent;


    customerRefundRequestButton.disabled =
        true;


    customerRefundRequestButton.textContent =
        "Mengirim permintaan...";


    if (
        customerRefundRequestMessage
    ) {

        customerRefundRequestMessage.hidden =
            true;


        customerRefundRequestMessage.textContent =
            "";

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
                    "/refund-request"
                ),
                {

                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {

                        "Accept":
                            "application/json",

                        "Content-Type":
                            "application/json",

                        "X-Review-Token":
                            customerReviewToken

                    },

                    body:
                        JSON.stringify(
                            {
                                reason:
                                    reason
                            }
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
                "Permintaan refund gagal."
            );

        }


        // ====================================================
        // Setelah request berhasil, form langsung ditutup.
        // Sumber state final tetap Live Status API.
        // ====================================================

        if (
            customerRefundRequestArea
        ) {

            customerRefundRequestArea.hidden =
                true;

        }


        if (
            customerRefundRequestMessage
        ) {

            customerRefundRequestMessage.hidden =
                false;


            customerRefundRequestMessage.textContent =
                data.message
                ||
                "Permintaan pengembalian dana berhasil dikirim.";

        }


        // ====================================================
        // Order sebelumnya mungkin SELESAI + DIBAYAR sehingga
        // polling sudah berhenti. Hidupkan lagi untuk PENDING.
        // ====================================================

        startPolling();


        window.setTimeout(
            function () {

                fetchOrderStatus();

            },
            150
        );

    }

    catch (error) {

        console.error(
            "[CUSTOMER REFUND REQUEST]",
            error
        );


        customerRefundRequestButton.disabled =
            false;


        customerRefundRequestButton.textContent =
            originalText;


        if (
            customerRefundRequestMessage
        ) {

            customerRefundRequestMessage.hidden =
                false;


            customerRefundRequestMessage.textContent =
                (
                    error.message
                    ||
                    "Permintaan refund gagal."
                );

        }

    }

}

// ============================================================
// PHASE 20F
// PAYMENT PROGRESS
// ============================================================

function updateCustomerPaymentProgress(
    payment
) {

    if (
        !customerPaymentProgress
        ||
        !payment
    ) {

        return;

    }


    const method =
        String(
            payment.method
            || "TUNAI"
        )
            .trim()
            .toUpperCase();


    const status =
        String(
            payment.status
            || ""
        )
            .trim()
            .toUpperCase();


    const steps =
        customerPaymentProgress
            .querySelectorAll(
                ".customer-payment-step"
            );


    if (
        !steps.length
    ) {

        return;

    }


    const paymentFinalized =
        (
            status
            === "DIBAYAR"
            ||
            status
            === "DIKEMBALIKAN"
        );


    steps.forEach(
        function (
            step
        ) {

            step.classList.remove(
                "is-active"
            );

        }
    );


    // ========================================================
    // CASH
    // ========================================================

    if (
        method
        === "TUNAI"
    ) {

        steps[
            0
        ]?.classList.add(
            "is-active"
        );


        if (
            paymentFinalized
        ) {

            steps[
                1
            ]?.classList.add(
                "is-active"
            );


            steps[
                2
            ]?.classList.add(
                "is-active"
            );

        }


        return;

    }


    // ========================================================
    // QRIS / BANK TRANSFER
    // ========================================================

    steps[
        0
    ]?.classList.add(
        "is-active"
    );


    if (
        status
        === "MENUNGGU_KONFIRMASI"
        ||
        paymentFinalized
    ) {

        steps[
            1
        ]?.classList.add(
            "is-active"
        );

    }


    if (
        paymentFinalized
    ) {

        steps[
            2
        ]?.classList.add(
            "is-active"
        );

    }

}


// ============================================================
// PHASE 20D
// UPDATE CUSTOMER PAYMENT STATUS
// ============================================================

function updateCustomerPaymentStatus(
    payment
) {

    if (!payment) {

        return;

    }


    if (
        customerPaymentConfirmArea
    ) {

        customerPaymentConfirmArea.hidden =
            !payment.can_customer_confirm;

    }


    if (
        !customerPaymentConfirmMessage
    ) {

        return;

    }


    const status =
        String(
            payment.status
            || ""
        )
            .trim()
            .toUpperCase();


    const method =
        String(
            payment.method
            || "TUNAI"
        )
            .trim()
            .toUpperCase();


    if (
        status
        === "DIKEMBALIKAN"
    ) {

        customerPaymentConfirmMessage.hidden =
            false;


        customerPaymentConfirmMessage.textContent =
            "↩ Dana sudah dikembalikan.";


        return;

    }


    if (
        status
        === "DIBAYAR"
    ) {

        customerPaymentConfirmMessage.hidden =
            false;


        customerPaymentConfirmMessage.textContent =
            "✓ Pembayaran sudah dikonfirmasi.";


        return;

    }


    if (
        status
        === "MENUNGGU_KONFIRMASI"
    ) {

        customerPaymentConfirmMessage.hidden =
            false;


        customerPaymentConfirmMessage.textContent =
            (
                "Pembayaran sedang menunggu "
                +
                "konfirmasi driver."
            );


        return;

    }


    if (
        method
        === "TUNAI"
        &&
        latestOrderData
        &&
        latestOrderData.status
        === "SELESAI"
    ) {

        customerPaymentConfirmMessage.hidden =
            false;


        customerPaymentConfirmMessage.textContent =
            (
                "Pembayaran tunai belum dikonfirmasi. "
                +
                "Menunggu driver."
            );


        return;

    }


    customerPaymentConfirmMessage.hidden =
        true;

}


// ============================================================
// PHASE 20F
// PAYMENT COPY
// ============================================================

async function copyCustomerPaymentValue(
    value
) {

    const text =
        String(
            value
            || ""
        ).trim();


    if (!text) {

        return false;

    }


    try {

        if (
            navigator.clipboard
            &&
            window.isSecureContext
        ) {

            await navigator.clipboard.writeText(
                text
            );


            return true;

        }


        const textarea =
            document.createElement(
                "textarea"
            );


        textarea.value =
            text;


        textarea.style.position =
            "fixed";


        textarea.style.opacity =
            "0";


        document.body.appendChild(
            textarea
        );

                textarea.focus();

        textarea.select();


        const copied =
            document.execCommand(
                "copy"
            );


        textarea.remove();


        return copied;

    }

    catch (error) {

        console.error(
            "[PAYMENT COPY]",
            error
        );


        return false;

    }

}


// ============================================================
// PHASE 20F
// PAYMENT TOAST
// ============================================================

function showCustomerPaymentToast(
    message
) {

    if (
        !customerPaymentToast
    ) {

        return;

    }


    customerPaymentToast.textContent =
        message;


    customerPaymentToast.hidden =
        false;


    customerPaymentToast.classList.add(
        "is-visible"
    );


    if (
        customerPaymentToastTimer
    ) {

        window.clearTimeout(
            customerPaymentToastTimer
        );

    }


    customerPaymentToastTimer =
        window.setTimeout(
            function () {

                customerPaymentToast.classList.remove(
                    "is-visible"
                );


                window.setTimeout(
                    function () {

                        customerPaymentToast.hidden =
                            true;

                    },
                    220
                );

            },
            1800
        );

}


// ============================================================
// PHASE 20F
// PAYMENT COPY EVENTS
// ============================================================

customerPaymentCopyButtons.forEach(
    function (
        button
    ) {

        button.addEventListener(
            "click",
            async function () {

                const value =
                    button.dataset.copyValue
                    || "";


                const label =
                    button.dataset.copyLabel
                    || "Data";


                const copied =
                    await copyCustomerPaymentValue(
                        value
                    );


                if (
                    copied
                ) {

                    showCustomerPaymentToast(
                        (
                            label
                            +
                            " berhasil disalin"
                        )
                    );

                }

                else {

                    showCustomerPaymentToast(
                        (
                            label
                            +
                            " tidak dapat disalin"
                        )
                    );

                }

            }
        );

    }
);


// ============================================================
// DRIVER PROFILE
// ============================================================

function updateDriverProfile(
    profile
) {

    if (
        !driverProfileCard
    ) {

        return;

    }


    if (!profile) {

        driverProfileCard.hidden =
            true;


        return;

    }


    driverProfileCard.hidden =
        false;


    const driverName =
        (
            profile.driver_name
            ||
            "Driver"
        );


    if (
        driverProfileName
    ) {

        driverProfileName.textContent =
            driverName;

    }


    if (
        driverProfileBio
    ) {

        driverProfileBio.textContent =
            (
                profile.short_bio
                ||
                ""
            );

    }


    if (
        driverVehicleName
    ) {

        driverVehicleName.textContent =
            (
                profile.vehicle_name
                ||
                "-"
            );

    }


    if (
        driverVehicleColor
    ) {

        driverVehicleColor.textContent =
            (
                profile.vehicle_color
                ||
                "-"
            );

    }


    if (
        driverVehiclePlate
    ) {

        driverVehiclePlate.textContent =
            (
                profile.vehicle_plate
                ||
                "-"
            );

    }


    const initial =
        driverName
            .charAt(
                0
            )
            .toUpperCase();


    if (
        driverProfileInitial
    ) {

        driverProfileInitial.textContent =
            initial;

    }


    if (
        driverProfilePhoto
        &&
        profile.photo_url
    ) {

        driverProfilePhoto.src =
            profile.photo_url;


        driverProfilePhoto.hidden =
            false;


        if (
            driverProfileInitial
        ) {

            driverProfileInitial.hidden =
                true;

        }


        driverProfilePhoto.onerror =
            function () {

                driverProfilePhoto.hidden =
                    true;


                if (
                    driverProfileInitial
                ) {

                    driverProfileInitial.hidden =
                        false;

                }

            };

    }

    else {

        if (
            driverProfilePhoto
        ) {

            driverProfilePhoto.removeAttribute(
                "src"
            );


            driverProfilePhoto.hidden =
                true;

        }


        if (
            driverProfileInitial
        ) {

            driverProfileInitial.hidden =
                false;

        }

    }

}


// ============================================================
// PHASE 19D
// UPDATE DRIVER TRUST
// ============================================================

function updateDriverTrust(
    trust
) {

    if (
        !driverTrustArea
    ) {

        return;

    }


    if (!trust) {

        driverTrustArea.hidden =
            true;


        return;

    }


    driverTrustArea.hidden =
        false;


    const reviewCount =
        Number(
            trust.review_count
        )
        || 0;


    const averageRating =
        Number(
            trust.average_rating
        )
        || 0;


    const completedTrips =
        Number(
            trust.completed_trips
        )
        || 0;


    if (
        driverTrustRating
    ) {

        driverTrustRating.textContent =
            (
                reviewCount > 0
                ? averageRating.toFixed(
                    1
                )
                : "—"
            );

    }


    if (
        driverTrustLabel
    ) {

        driverTrustLabel.textContent =
            (
                trust.reputation_label
                ||
                "Reputasi driver"
            );

    }


    if (
        driverTrustReviewCount
    ) {

        if (
            reviewCount
            === 0
        ) {

            driverTrustReviewCount.textContent =
                "Belum ada ulasan";

        }

        else if (
            reviewCount
            === 1
        ) {

            driverTrustReviewCount.textContent =
                "Berdasarkan 1 ulasan";

        }

        else {

            driverTrustReviewCount.textContent =
                (
                    "Berdasarkan "
                    +
                    reviewCount
                    +
                    " ulasan"
                );

        }

    }


    if (
        driverTrustCompleted
    ) {

        driverTrustCompleted.textContent =
            (
                completedTrips
                +
                " perjalanan selesai"
            );

    }


    if (
        driverTrustVehicle
    ) {

        driverTrustVehicle.hidden =
            (
                trust.vehicle_data_available
                !== true
            );

    }


    if (
        driverTrustContact
    ) {

        driverTrustContact.hidden =
            (
                trust.contact_available
                !== true
            );

    }

}


// ============================================================
// DRIVER CONTACT
// ============================================================

function updateDriverContact(
    status
) {

    if (
        !customerDriverContact
    ) {

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


    customerDriverContact.hidden =
        !canContact;

}


// ============================================================
// JOURNEY TIMESTAMP FORMAT
// ============================================================

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


// ============================================================
// CREATE PROGRESS TIMESTAMP
// ============================================================

function getProgressTimestampElement(
    step
) {

    let timestampElement =
        step.querySelector(
            ".progress-timestamp"
        );


    if (
        timestampElement
    ) {

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


    const description =
        step.querySelector(
            "p"
        );


    if (
        description
    ) {

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


// ============================================================
// UPDATE JOURNEY TIMELINE TIMESTAMPS
// ============================================================

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


            if (
                !timestampKey
            ) {

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


            if (
                timestampValue
            ) {

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


// ============================================================
// CURRENT STATUS TIMESTAMP
// ============================================================

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


    if (
        !timestampElement
    ) {

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


    if (
        !timestampValue
    ) {

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


// ============================================================
// REJECTED TIMESTAMP
// ============================================================

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


    if (
        !element
    ) {

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


    if (
        !rejectedAt
    ) {

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


// ============================================================
// UPDATE ALL JOURNEY TIMESTAMPS
// ============================================================

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

    if (
        !lastUpdate
    ) {

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
// CREATE CUSTOMER STATUS TOAST
// ============================================================

function getCustomerStatusToast() {

    let toast =
        document.getElementById(
            "customerStatusToast"
        );


    if (
        toast
    ) {

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


    if (
        !config
    ) {

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


    if (
        title
    ) {

        title.textContent =
            config.title;

    }


    if (
        message
    ) {

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


    if (
        customerStatusToastTimer
    ) {

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


    document.title =
        (
            config.title
            +
            " • Ojek Pribadi"
        );


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
// PHASE 19B
// QUICK TAGS
// ============================================================

function toggleCustomerReviewTag(
    button
) {

    const tag =
        button.dataset.reviewTag;


    if (!tag) {

        return;

    }


    const selected =
        selectedReviewTags.includes(
            tag
        );


    if (
        selected
    ) {

        selectedReviewTags =
            selectedReviewTags.filter(
                function (
                    item
                ) {

                    return (
                        item
                        !== tag
                    );

                }
            );

    }

    else {

        selectedReviewTags.push(
            tag
        );

    }


    const nowSelected =
        !selected;


    button.classList.toggle(
        "is-active",
        nowSelected
    );


    button.setAttribute(
        "aria-pressed",
        nowSelected
            ? "true"
            : "false"
    );

}


// ============================================================
// REVIEW TAG EVENTS
// ============================================================

customerReviewTagButtons.forEach(
    function (
        button
    ) {

        button.addEventListener(
            "click",
            function () {

                toggleCustomerReviewTag(
                    button
                );

            }
        );

    }
);


// ============================================================
// REVIEW FEEDBACK COUNTER
// ============================================================

if (
    customerReviewFeedback
) {

    customerReviewFeedback.addEventListener(
        "input",
        function () {

            const length =
                customerReviewFeedback
                    .value
                    .length;


            if (
                customerReviewFeedbackCount
            ) {

                customerReviewFeedbackCount.textContent =
                    String(
                        length
                    );

            }

        }
    );

}


// ============================================================
// UPDATE STAR UI
// ============================================================

function updateCustomerReviewStars(
    rating
) {

    selectedReviewRating =
        Number(
            rating
        )
        || 0;


    customerReviewStars.forEach(
        function (
            star
        ) {

            const starRating =
                Number(
                    star.dataset.rating
                );


            const active =
                (
                    starRating
                    <= selectedReviewRating
                );


            star.classList.toggle(
                "is-active",
                active
            );


            star.setAttribute(
                "aria-checked",
                (
                    starRating
                    === selectedReviewRating
                )
                    ? "true"
                    : "false"
            );

        }
    );


    if (
        customerReviewLabel
    ) {

        customerReviewLabel.textContent =
            selectedReviewRating
                ? reviewLabels[
                    selectedReviewRating
                ]
                : "Pilih rating";

    }


    if (
        customerReviewSubmit
    ) {

        customerReviewSubmit.disabled =
            (
                selectedReviewRating
                < 1

                ||

                reviewSubmitting
            );

    }

}


// ============================================================
// RENDER EXISTING REVIEW
// ============================================================

function showCustomerReviewSuccess(
    review
) {

    if (!review) {

        return;

    }


    if (
        customerReviewForm
    ) {

        customerReviewForm.hidden =
            true;

    }


    if (
        customerReviewSuccess
    ) {

        customerReviewSuccess.hidden =
            false;

    }


    if (
        customerReviewResultStars
    ) {

        const rating =
            Number(
                review.rating
            )
            || 0;


        customerReviewResultStars.textContent =
            (
                "★".repeat(
                    rating
                )
                +
                "☆".repeat(
                    Math.max(
                        0,
                        5 - rating
                    )
                )
            );

    }


    if (
        customerReviewResultTags
    ) {

        customerReviewResultTags.innerHTML =
            "";


        const tags =
            Array.isArray(
                review.tags
            )
                ? review.tags
                : [];


        const tagLabels = {

            ramah:
                "Ramah",

            tepat_waktu:
                "Tepat Waktu",

            aman:
                "Aman",

            nyaman:
                "Nyaman",

            komunikatif:
                "Komunikatif",

            berkendara_baik:
                "Berkendara Baik"

        };


        tags.forEach(
            function (
                tag
            ) {

                const element =
                    document.createElement(
                        "span"
                    );


                element.textContent =
                    (
                        tagLabels[
                            tag
                        ]
                        ||
                        tag
                    );


                customerReviewResultTags
                    .appendChild(
                        element
                    );

            }
        );


        customerReviewResultTags.hidden =
            (
                tags.length
                === 0
            );

    }


    if (
        customerReviewResultFeedback
    ) {

        const feedback =
            String(
                review.feedback
                || ""
            ).trim();


        customerReviewResultFeedback.textContent =
            feedback;


        customerReviewResultFeedback.hidden =
            !feedback;

    }

}


// ============================================================
// LOAD REVIEW
// ============================================================

async function loadCustomerReview() {

    if (
        !orderCode
        ||
        reviewLoaded
    ) {

        return;

    }


    if (
        !customerReviewToken
    ) {

        console.warn(
            "[REVIEW] Token akses tidak tersedia."
        );


        return;

    }


    reviewLoaded =
        true;


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
                    "/review"
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
                            "application/json",

                        "X-Review-Token":
                            customerReviewToken

                    }

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
                "Penilaian belum dapat dimuat."
            );

        }


        if (
            data.review
        ) {

            if (
                customerReviewCard
            ) {

                customerReviewCard.hidden =
                    false;

            }


            showCustomerReviewSuccess(
                data.review
            );


            return;

        }


        if (
            !data.eligible
        ) {

            if (
                customerReviewCard
            ) {

                customerReviewCard.hidden =
                    true;

            }


            return;

        }


        if (
            customerReviewCard
        ) {

            customerReviewCard.hidden =
                false;

        }

    }

    catch (error) {

        reviewLoaded =
            false;


        console.warn(
            "[CUSTOMER REVIEW LOAD]",
            error
        );

    }

}


// ============================================================
// REVIEW VISIBILITY
// ============================================================

function updateCustomerReviewVisibility(
    status
) {

    if (
        !customerReviewCard
    ) {

        return;

    }


    const completed =
        (
            status
            === "SELESAI"
        );


    customerReviewCard.hidden =
        !completed;


    if (
        completed
    ) {

        loadCustomerReview();

    }

}


// ============================================================
// SUBMIT REVIEW
// ============================================================

async function submitCustomerReview() {

    if (
        reviewSubmitting
        ||
        selectedReviewRating < 1
        ||
        !orderCode
    ) {

        return;

    }


    reviewSubmitting =
        true;


    if (
        customerReviewSubmit
    ) {

        customerReviewSubmit.disabled =
            true;

    }


    if (
        customerReviewSubmitText
    ) {

        customerReviewSubmitText.textContent =
            "Menyimpan...";

    }


    if (
        customerReviewMessage
    ) {

        customerReviewMessage.textContent =
            "";

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
                    "/review"
                ),
                {

                    method:
                        "POST",

                    cache:
                        "no-store",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json",

                        "X-Review-Token":
                            customerReviewToken

                    },

                    body:
                        JSON.stringify(
                            {

                                rating:
                                    selectedReviewRating,

                                feedback:
                                    customerReviewFeedback
                                        ? customerReviewFeedback
                                            .value
                                            .trim()
                                        : "",

                                tags:
                                    selectedReviewTags

                            }
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
                "Penilaian belum berhasil disimpan."
            );

        }


        showCustomerReviewSuccess(
            data.review
        );

    }

    catch (error) {

        console.error(
            "[CUSTOMER REVIEW SUBMIT]",
            error
        );


        if (
            customerReviewMessage
        ) {

            customerReviewMessage.textContent =
                (
                    error.message
                    ||
                    "Penilaian belum berhasil disimpan."
                );

        }

    }

    finally {

        reviewSubmitting =
            false;


        if (
            customerReviewSubmitText
        ) {

            customerReviewSubmitText.textContent =
                "Kirim Penilaian";

        }


        if (
            customerReviewSubmit
            &&
            customerReviewForm
            &&
            !customerReviewForm.hidden
        ) {

            customerReviewSubmit.disabled =
                (
                    selectedReviewRating
                    < 1
                );

        }

    }

}


// ============================================================
// REVIEW EVENTS
// ============================================================

customerReviewStars.forEach(
    function (
        star
    ) {

        star.addEventListener(
            "click",
            function () {

                updateCustomerReviewStars(
                    star.dataset.rating
                );

            }
        );

    }
);


if (
    customerReviewSubmit
) {

    customerReviewSubmit.addEventListener(
        "click",
        submitCustomerReview
    );

}


// ============================================================
// PHASE 20G.3
// RECEIPT ORDER CODE
// ============================================================

function getCustomerReceiptOrderCode() {

    const configuredOrderCode =
        (
            customerReceiptConfig
            &&
            customerReceiptConfig.dataset
        )
            ? customerReceiptConfig.dataset.orderCode
            : "";


    return String(
        configuredOrderCode
        ||
        orderCode
        ||
        ""
    )
        .trim()
        .toUpperCase();

}


// ============================================================
// PHASE 20G.3
// RECEIPT TOKEN
// ============================================================

function getCustomerReceiptToken(
    receiptOrderCode
) {

    receiptOrderCode =
        String(
            receiptOrderCode
            || ""
        )
            .trim()
            .toUpperCase();


    if (
        !receiptOrderCode
    ) {

        return "";

    }


    try {

        return String(
            sessionStorage.getItem(
                `receipt_token:${receiptOrderCode}`
            )
            || ""
        ).trim();

    }

    catch (error) {

        console.warn(
            "[RECEIPT TOKEN]",
            error
        );


        return "";

    }

}


// ============================================================
// PHASE 20G.3
// FORMAT RUPIAH
// ============================================================

function formatReceiptRupiah(
    value
) {

    const amount =
        Number(
            value
            || 0
        );


    return new Intl.NumberFormat(
        "id-ID",
        {

            style:
                "currency",

            currency:
                "IDR",

            maximumFractionDigits:
                0

        }
    ).format(
        amount
    );

}


// ============================================================
// PHASE 20G.3
// FORMAT DATE TIME
// ============================================================

function formatReceiptDateTime(
    value
) {

    if (!value) {

        return "-";

    }


    const normalized =
        String(
            value
        )
            .trim()
            .replace(
                " ",
                "T"
            );


    const date =
        new Date(
            normalized
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(
            value
        );

    }


    return new Intl.DateTimeFormat(
        "id-ID",
        {

            dateStyle:
                "medium",

            timeStyle:
                "short"

        }
    ).format(
        date
    );

}


// ============================================================
// PHASE 20G.3
// SAFE TEXT
// ============================================================

function setReceiptText(
    elementId,
    value
) {

    const element =
        document.getElementById(
            elementId
        );


    if (
        !element
    ) {

        return;

    }


    element.textContent =
        (
            value === null
            ||
            value === undefined
            ||
            value === ""
        )
            ? "-"
            : String(
                value
            );

}


// ============================================================
// PHASE 20G.6.5
// RESET CUSTOMER RECEIPT CONTENT
// ============================================================

function resetCustomerReceiptContent() {

    setReceiptText("receiptOrderCode", "-");
    setReceiptText("receiptCustomerName", "-");
    setReceiptText("receiptPickup", "-");
    setReceiptText("receiptDestination", "-");
    setReceiptText("receiptDistance", "-");

        setReceiptText("receiptDuration", "-");
    setReceiptText("receiptPaymentMethod", "-");
    setReceiptText("receiptPaymentStatus", "-");
    setReceiptText("receiptPaidAt", "-");
    setReceiptText("receiptTotal", "Rp0");


    if (
        customerReceiptContent
    ) {

        customerReceiptContent.hidden =
            true;


        customerReceiptContent.setAttribute(
            "aria-busy",
            "true"
        );

    }


    if (
        customerReceiptPrintButton
    ) {

        customerReceiptPrintButton.disabled =
            true;

    }

}


// ============================================================
// PHASE 20G.3
// RECEIPT AVAILABILITY
// ============================================================

function updateCustomerReceiptAvailability(
    order
) {

    if (!order) {

        return;

    }


    const receiptOrderCode =
        String(
            order.order_code
            ||
            getCustomerReceiptOrderCode()
        )
            .trim()
            .toUpperCase();


    const orderStatus =
        String(
            order.status
            || ""
        )
            .trim()
            .toUpperCase();


    const payment =
        order.payment
        || {};


    const paymentStatus =
        String(
            payment.status
            || ""
        )
            .trim()
            .toUpperCase();


    const paymentMethod =
        String(
            payment.method
            || ""
        )
            .trim()
            .toUpperCase();


    const paymentAmount =
        Number(
            payment.amount
            || 0
        );


    const fare =
        Number(
            order.fare
            || 0
        );


    const paidAt =
        String(
            payment.paid_at
            || ""
        ).trim();


    const receiptToken =
        getCustomerReceiptToken(
            receiptOrderCode
        );


    const validPaymentMethod =
        [
            "TUNAI",
            "QRIS",
            "TRANSFER_BANK"
        ].includes(
            paymentMethod
        );


    const completedAndPaid =
        (
            orderStatus
            === "SELESAI"

            &&

            paymentStatus
            === "DIBAYAR"
        );


    const receiptEligible =
        (
            completedAndPaid

            &&

            Boolean(
                paidAt
            )

            &&

            Number.isFinite(
                fare
            )

            &&

            Number.isFinite(
                paymentAmount
            )

            &&

            fare > 0

            &&

            paymentAmount > 0

            &&

            paymentAmount
            === fare

            &&

            validPaymentMethod
        );


    const canOpenReceipt =
        (
            receiptEligible

            &&

            Boolean(
                receiptToken
            )
        );


    if (
        customerReceiptCard
    ) {

        customerReceiptCard.hidden =
            !canOpenReceipt;

    }


    if (
        customerDigitalReceiptArea
    ) {

        customerDigitalReceiptArea.hidden =
            (
                customerReceiptCard
                    ? true
                    : !canOpenReceipt
            );

    }


    if (
        !customerReceiptMessage
    ) {

        return;

    }


    if (
        completedAndPaid
        &&
        !receiptEligible
    ) {

        customerReceiptMessage.textContent =
            (
                "Pembayaran sudah dikonfirmasi. "
                +
                "Struk digital sedang disiapkan."
            );


        customerReceiptMessage.hidden =
            false;


        return;

    }


    if (
        receiptEligible
        &&
        !receiptToken
    ) {

        customerReceiptMessage.textContent =
            (
                "Struk pembayaran sudah siap, tetapi "
                +
                "akses aman tidak ditemukan pada sesi "
                +
                "browser ini."
            );


        customerReceiptMessage.hidden =
            false;


        return;

    }


    customerReceiptMessage.hidden =
        true;

}


// ============================================================
// PHASE 20G.3
// RECEIPT MODAL
// ============================================================

function openCustomerReceiptModal() {

    if (
        !customerReceiptModal
    ) {

        return;

    }


    customerReceiptModal.hidden =
        false;


    document.body.classList.add(
        "receipt-modal-open"
    );

}


function closeCustomerReceiptModal() {

    if (
        !customerReceiptModal
    ) {

        return;

    }


    customerReceiptModal.hidden =
        true;


    document.body.classList.remove(
        "receipt-modal-open"
    );

}


// ============================================================
// PHASE 20G.3
// RENDER RECEIPT
// ============================================================

function renderCustomerReceipt(
    receipt
) {

    if (!receipt) {

        return;

    }


    setReceiptText(
        "receiptOrderCode",
        receipt.order_code
    );


    setReceiptText(
        "receiptCustomerName",
        receipt.customer_name
    );


    setReceiptText(
        "receiptPickup",
        receipt.pickup
    );


    setReceiptText(
        "receiptDestination",
        receipt.destination
    );


    setReceiptText(
        "receiptDistance",
        (
            Number(
                receipt.distance_km
                || 0
            ).toFixed(
                1
            )
            +
            " km"
        )
    );


    setReceiptText(
        "receiptDuration",
        (
            Number(
                receipt.duration_minutes
                || 0
            )
            +
            " menit"
        )
    );


    setReceiptText(
        "receiptPaymentMethod",
        receipt.payment_method_label
    );


    setReceiptText(
        "receiptPaymentStatus",
        (
            receipt.payment_status
            === "DIBAYAR"
                ? "Dibayar"
                : receipt.payment_status
        )
    );


    setReceiptText(
        "receiptPaidAt",
        formatReceiptDateTime(
            receipt.paid_at
        )
    );


    setReceiptText(
        "receiptTotal",
        formatReceiptRupiah(
            receipt.fare
        )
    );

}


// ============================================================
// PHASE 20G.3
// FALLBACK RECEIPT DISPLAY
//
// Jika modal baru belum ada di template,
// data receipt tetap bisa dilihat tanpa membuka URL baru.
// ============================================================

function showReceiptFallback(
    receipt
) {

    if (
        customerReceiptModal
    ) {

        return;

    }


    const lines = [

        "OJEK PRIBADI",

        "Struk Pembayaran",

        "",

        `Kode: ${receipt.order_code || "-"}`,

        `Pelanggan: ${receipt.customer_name || "-"}`,

        `Jemput: ${receipt.pickup || "-"}`,

        `Tujuan: ${receipt.destination || "-"}`,

        `Metode: ${receipt.payment_method_label || "-"}`,

        `Status: ${receipt.payment_status || "-"}`,

        `Total: ${formatReceiptRupiah(receipt.fare)}`,

        `Dibayar: ${formatReceiptDateTime(receipt.paid_at)}`

    ];


    window.alert(
        lines.join(
            "\n"
        )
    );

}


// ============================================================
// PHASE 20G.3
// LOAD SECURE DIGITAL RECEIPT
// ============================================================

async function loadCustomerDigitalReceipt() {

    const receiptOrderCode =
        getCustomerReceiptOrderCode();


    if (
        !receiptOrderCode
    ) {

        console.warn(
            "[RECEIPT] Kode pesanan tidak tersedia."
        );


        return;

    }


    const receiptToken =
        getCustomerReceiptToken(
            receiptOrderCode
        );


    if (
        !receiptToken
    ) {

        if (
            customerReceiptMessage
        ) {

            customerReceiptMessage.textContent =
                (
                    "Akses aman struk tidak tersedia "
                    +
                    "pada sesi browser ini."
                );


            customerReceiptMessage.hidden =
                false;

        }


        window.alert(
            (
                "Akses struk tidak tersedia. "
                +
                "Gunakan tab atau sesi browser "
                +
                "yang sama dengan saat membuat pesanan."
            )
        );


        return;

    }


    if (
        customerReceiptModal
    ) {

        openCustomerReceiptModal();

    }


    resetCustomerReceiptContent();


    if (
        customerReceiptLoading
    ) {

        customerReceiptLoading.hidden =
            false;

    }


    if (
        customerReceiptContent
    ) {

        customerReceiptContent.hidden =
            true;

    }


    if (
        customerReceiptError
    ) {

        customerReceiptError.hidden =
            true;

                    customerReceiptError.textContent =
            "";

    }


    if (
        openCustomerReceiptButton
    ) {

        openCustomerReceiptButton.disabled =
            true;

    }


    if (
        customerDigitalReceiptButton
    ) {

        customerDigitalReceiptButton.disabled =
            true;

    }


    try {

        const response =
            await fetch(
                (
                    "/api/orders/"
                    +
                    encodeURIComponent(
                        receiptOrderCode
                    )
                    +
                    "/receipt"
                ),
                {

                    method:
                        "GET",

                    cache:
                        "no-store",

                    headers: {

                        "Accept":
                            "application/json",

                        "X-Receipt-Token":
                            receiptToken

                    }

                }
            );


        const data =
            await response.json();


        if (
            response.status
            === 409
        ) {

            throw new Error(
                data.message
                ||
                "Struk pembayaran belum tersedia."
            );

        }


        if (
            response.status
            === 404
        ) {

            throw new Error(
                (
                    data.message
                    ||
                    "Akses struk tidak valid atau tidak tersedia."
                )
            );

        }


        if (
            !response.ok
            ||
            !data.success
            ||
            !data.receipt
        ) {

            throw new Error(
                data.message
                ||
                "Struk pembayaran belum dapat dimuat."
            );

        }


        renderCustomerReceipt(
            data.receipt
        );


        if (
            customerReceiptContent
        ) {

            customerReceiptContent.hidden =
                false;


            customerReceiptContent.setAttribute(
                "aria-busy",
                "false"
            );

        }


        if (
            customerReceiptPrintButton
        ) {

            customerReceiptPrintButton.disabled =
                false;

        }


        showReceiptFallback(
            data.receipt
        );

    }

    catch (error) {

        console.error(
            "[CUSTOMER RECEIPT ERROR]",
            error
        );


        if (
            customerReceiptContent
        ) {

            customerReceiptContent.hidden =
                true;


            customerReceiptContent.setAttribute(
                "aria-busy",
                "false"
            );

        }


        if (
            customerReceiptPrintButton
        ) {

            customerReceiptPrintButton.disabled =
                true;

        }


        if (
            customerReceiptError
        ) {

            customerReceiptError.textContent =
                (
                    error.message
                    ||
                    "Struk pembayaran belum dapat dimuat."
                );


            customerReceiptError.hidden =
                false;

        }

        else {

            window.alert(
                (
                    error.message
                    ||
                    "Struk pembayaran belum dapat dimuat."
                )
            );

        }

    }

    finally {

        if (
            customerReceiptLoading
        ) {

            customerReceiptLoading.hidden =
                true;

        }


        if (
            openCustomerReceiptButton
        ) {

            openCustomerReceiptButton.disabled =
                false;

        }


        if (
            customerDigitalReceiptButton
        ) {

            customerDigitalReceiptButton.disabled =
                false;

        }

    }

}


// ============================================================
// UPDATE STATUS UI
// ============================================================

function updateStatusUI(
    status,
    driverProfile = null,
    driverTrust = null
) {

    if (!status) {

        return;

    }


    status =
        String(
            status
        )
            .trim()
            .toUpperCase();


    updateDriverContact(
        status
    );


    updateDriverProfile(
        driverProfile
    );


    updateDriverTrust(
        driverTrust
    );


    updateLastUpdate();


    updateCustomerReviewVisibility(
        status
    );


    // Tidak perlu menjalankan animasi ulang
    // bila status masih sama.
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

        if (
            rejectedCard
        ) {

            rejectedCard.classList.add(
                "show"
            );

        }


        if (
            liveStatusCard
        ) {

            liveStatusCard.classList.add(
                "rejected"
            );

        }


        if (
            liveIcon
        ) {

            liveIcon.textContent =
                "×";

        }


        if (
            liveStatusTitle
        ) {

            liveStatusTitle.textContent =
                "Perjalanan belum dapat diterima";

        }


        if (
            liveStatusDescription
        ) {

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


    if (
        rejectedCard
    ) {

        rejectedCard.classList.remove(
            "show"
        );

    }


    if (
        liveStatusCard
    ) {

        liveStatusCard.classList.remove(
            "rejected"
        );

    }


    const config =
        statusConfig[
            status
        ];


    if (
        !config
    ) {

        console.warn(
            "[ORDER STATUS] Status tidak dikenal:",
            status
        );


        return;

    }


    if (
        liveStatusCard
    ) {

        liveStatusCard.classList.remove(
            "status-change"
        );


        void liveStatusCard.offsetWidth;


        liveStatusCard.classList.add(
            "status-change"
        );

    }


    if (
        liveIcon
    ) {

        liveIcon.textContent =
            config.icon;

    }


    if (
        liveStatusTitle
    ) {

        liveStatusTitle.textContent =
            config.title;

    }


    if (
        liveStatusDescription
    ) {

        liveStatusDescription.textContent =
            config.description;

    }


    updateProgress(
        config.step,
        status
    );


    // Penting:
    // Jangan stop polling hanya karena status = SELESAI.
    // Untuk TUNAI, payment_status masih bisa berubah dari
    // BELUM_DIBAYAR -> DIBAYAR setelah driver konfirmasi.

}



// ============================================================
// PHASE 20I.3F
// REFUND-AWARE POLLING DECISION
// ============================================================

function shouldContinueCustomerPolling(
    order
) {

    if (!order) {

        return (
            initialStatus
            !== "DITOLAK"
        );

    }


    const orderStatus =
        String(
            order.status
            || ""
        )
            .trim()
            .toUpperCase();


    const payment =
        order.payment
        || {};


    const paymentStatus =
        String(
            payment.status
            || ""
        )
            .trim()
            .toUpperCase();


    const refundRequestStatus =
        String(
            (
                payment.refund_request
                &&
                payment.refund_request.status
            )
            ||
            "NONE"
        )
            .trim()
            .toUpperCase();


    // Perjalanan ditolak adalah final.
    if (
        orderStatus
        === "DITOLAK"
    ) {

        return false;

    }


    // Customer sedang menunggu keputusan driver.
    // Tetap polling walaupun perjalanan sudah SELESAI
    // dan payment masih DIBAYAR.
    if (
        refundRequestStatus
        === "PENDING"
    ) {

        return true;

            }


    // SELESAI + state payment/refund final.
    if (
        orderStatus
        === "SELESAI"

        &&

        (
            paymentStatus
            === "DIBAYAR"

            ||

            paymentStatus
            === "DIKEMBALIKAN"
        )

        &&

        (
            refundRequestStatus
            === "NONE"

            ||

            refundRequestStatus
            === "APPROVED"

            ||

            refundRequestStatus
            === "REJECTED"
        )
    ) {

        return false;

    }


    return true;

}

// ============================================================
// FETCH ORDER STATUS
// ============================================================

async function fetchOrderStatus() {

    if (
        !orderCode
    ) {

        console.error(
            "[ORDER STATUS] Kode pesanan tidak tersedia."
        );


        return;

    }


    try {

        const statusUrl =
            (
                "/api/orders/"
                +
                encodeURIComponent(
                    orderCode
                )
                +
                "/status"
                +
                "?_="
                +
                Date.now()
            );


        const response =
            await fetch(
                statusUrl,
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


        if (
            !response.ok
        ) {

            throw new Error(
                `HTTP ${response.status}`
            );

        }


        const data =
            await response.json();


        if (
            !data
            ||
            data.success
            !== true
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


        latestOrderData =
            data.order;


        updateCustomerPaymentStatus(
            data.order.payment
            || null
        );


        renderCustomerPaymentExperience(
            data.order.payment
            || null
        );


        updateCustomerReceiptAvailability(
            data.order
        );


        updateStatusUI(
            data.order.status,

            data.order.driver_profile
            || null,

            data.order.driver_trust
            || null
        );


        updateJourneyTimestamps(
            data.order.status,

            data.order.timestamps
            || null
        );


        // ====================================================
        // PHASE 20I.3F
        // REFUND-AWARE POLLING
        // ====================================================

        if (
            shouldContinueCustomerPolling(
                data.order
            )
        ) {

            startPolling();

        }

        else {

            stopPolling();

        }

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

    if (
        statusInterval
    ) {

        return;

    }


    console.log(
        "[ORDER STATUS] Live polling dimulai."
    );


    statusInterval =
        window.setInterval(
            function () {

                fetchOrderStatus();

            },
            3000
        );

}


function stopPolling() {

    if (
        !statusInterval
    ) {

        return;

    }


    window.clearInterval(
        statusInterval
    );


    statusInterval =
        null;


    console.log(
        "[ORDER STATUS] Live polling dihentikan."
    );

}


// ============================================================
// INITIAL STATUS
// ============================================================

updateStatusUI(
    initialStatus,
    null,
    null
);


// ============================================================
// FIRST API CHECK
// ============================================================

fetchOrderStatus();


// ============================================================
// START LIVE POLLING
//
// Status SELESAI tetap polling,
// karena pembayaran tunai mungkin belum dikonfirmasi.
// ============================================================

if (
    initialStatus
    !== "DITOLAK"
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
                shouldContinueCustomerPolling(
                    latestOrderData
                )
            ) {

                startPolling();

            }

            else {

                stopPolling();

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
// PHASE 20D
// PAYMENT CONFIRM BUTTON EVENT
// ============================================================

if (
    customerPaymentConfirmButton
) {

    customerPaymentConfirmButton.addEventListener(
        "click",
        function () {

            submitCustomerPaymentConfirmation();

        }
    );

}


// ============================================================
// PHASE 20G.3
// LEGACY RECEIPT BUTTON EVENT
//
// Tidak lagi menggunakan:
// /order/<code>/receipt#token=...
// ============================================================

if (
    customerDigitalReceiptButton
) {

    customerDigitalReceiptButton.addEventListener(
        "click",
        function (
            event
        ) {

            event.preventDefault();


            loadCustomerDigitalReceipt();

        }
    );

}


// ============================================================
// PHASE 20G.3
// NEW RECEIPT BUTTON EVENT
// ============================================================

if (
    openCustomerReceiptButton
) {

    openCustomerReceiptButton.addEventListener(
        "click",
        function (
            event
        ) {

            event.preventDefault();


            loadCustomerDigitalReceipt();

        }
    );

}


// ============================================================
// PHASE 20G.3
// CLOSE RECEIPT
// ============================================================

if (
    closeCustomerReceiptButton
) {

    closeCustomerReceiptButton.addEventListener(
        "click",
        closeCustomerReceiptModal
    );

}


if (
    customerReceiptBackdrop
) {

    customerReceiptBackdrop.addEventListener(
        "click",
        closeCustomerReceiptModal
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
            customerReceiptModal

            &&
            !customerReceiptModal.hidden
        ) {

            closeCustomerReceiptModal();

        }

    }
);

// ============================================================
// PHASE 20G.6
// CUSTOMER RECEIPT PRINT / SAVE PDF
// ============================================================

if (
    customerReceiptPrintButton
) {

    customerReceiptPrintButton.addEventListener(
        "click",
        function () {

            if (
                !customerReceiptContent

                ||

                customerReceiptContent.hidden

                ||

                customerReceiptPrintButton.disabled
            ) {

                return;

            }


            document.body.classList.add(
                "customer-receipt-print-mode"
            );


            window.print();

        }
    );

}


window.addEventListener(
    "afterprint",
    function () {

        document.body.classList.remove(
            "customer-receipt-print-mode"
        );

    }
);

if (
    customerRefundRequestButton
) {

    customerRefundRequestButton.addEventListener(
        "click",
        submitCustomerRefundRequest
    );

}

// ============================================================
// APP READY
// ============================================================

console.log(
    "[ORDER STATUS] Live tracking + refund status + secure receipt aktif."
);
