"use strict";


// ============================================================
// PHASE 20G
// DIGITAL RECEIPT
// ============================================================


const receiptPage =
    document.querySelector(
        ".digital-receipt-page"
    );


const orderCode =
    String(
        receiptPage?.dataset.orderCode
        || ""
    )
    .trim()
    .toUpperCase();


const loadingElement =
    document.getElementById(
        "digitalReceiptLoading"
    );


const errorElement =
    document.getElementById(
        "digitalReceiptError"
    );


const errorMessageElement =
    document.getElementById(
        "digitalReceiptErrorMessage"
    );


const receiptElement =
    document.getElementById(
        "digitalReceipt"
    );


const printButton =
    document.getElementById(
        "digitalReceiptPrintButton"
    );


const backButton =
    document.getElementById(
        "digitalReceiptBackButton"
    );


const backErrorButton =
    document.getElementById(
        "digitalReceiptBackError"
    );


// ============================================================
// TOKEN
// ============================================================

function getReceiptTokenFromHash() {

    const hash =
        String(
            window.location.hash
            || ""
        );


    if (!hash) {

        return "";

    }


    const raw =
        hash.startsWith("#")
            ? hash.slice(1)
            : hash;


    const params =
        new URLSearchParams(
            raw
        );


    return String(
        params.get(
            "token"
        )
        || ""
    ).trim();

}


const receiptToken =
    getReceiptTokenFromHash();


// ============================================================
// REMOVE TOKEN FROM ADDRESS BAR
// ============================================================

function cleanReceiptHash() {

    if (!window.location.hash) {

        return;

    }


    window.history.replaceState(
        null,
        "",
        (
            window.location.pathname
            +
            window.location.search
        )
    );

}


// ============================================================
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
// FORMAT DATE
// ============================================================

function formatReceiptDate(
    value
) {

    const text =
        String(
            value
            || ""
        ).trim();


    if (!text) {

        return "-";

    }


    /*
     * Database menggunakan:
     * YYYY-MM-DD HH:MM:SS
     */

    const normalized =
        text.replace(
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

        return text;

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
// SET TEXT
// ============================================================

function setReceiptText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        return;

    }


    element.textContent =
        String(
            value
            ?? "-"
        );

}


// ============================================================
// SHOW ERROR
// ============================================================

function showReceiptError(
    message
) {

    if (loadingElement) {

        loadingElement.hidden =
            true;

    }


    if (receiptElement) {

        receiptElement.hidden =
            true;

    }


    if (errorElement) {

        errorElement.hidden =
            false;

    }


    if (errorMessageElement) {

        errorMessageElement.textContent =
            (
                message
                ||
                "Struk belum dapat dimuat."
            );

    }

}


// ============================================================
// RENDER RECEIPT
// ============================================================

function renderDigitalReceipt(
    receipt
) {

    if (!receipt) {

        showReceiptError(
            "Data struk tidak tersedia."
        );


        return;

    }


    const payment =
        receipt.payment
        || {};


    setReceiptText(
        "receiptAmount",
        formatReceiptRupiah(
            payment.amount
        )
    );


    setReceiptText(
        "receiptPaymentMethod",
        payment.method_label
        || "-"
    );


    setReceiptText(
        "receiptNumber",
        receipt.receipt_number
        || "-"
    );


    setReceiptText(
        "receiptOrderCode",
        receipt.order_code
        || "-"
    );


    setReceiptText(
        "receiptCustomerName",
        receipt.customer_name
        || "-"
    );


    setReceiptText(
        "receiptPaidAt",
        formatReceiptDate(
            payment.paid_at
        )
    );


    setReceiptText(
        "receiptPickup",
        receipt.pickup
        || "-"
    );


    setReceiptText(
        "receiptDestination",
        receipt.destination
        || "-"
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
        "receiptFare",
        formatReceiptRupiah(
            receipt.fare
        )
    );


    setReceiptText(
        "receiptMethod",
        payment.method_label
        || "-"
    );


    const referenceRow =
        document.getElementById(
            "receiptReferenceRow"
        );


    const reference =
        String(
            payment.reference
            || ""
        ).trim();


    if (
        referenceRow
        &&
        reference
    ) {

        referenceRow.hidden =
            false;


        setReceiptText(
            "receiptReference",
            reference
        );

    }


    if (loadingElement) {

        loadingElement.hidden =
            true;

    }


    if (errorElement) {

        errorElement.hidden =
            true;

    }


    if (receiptElement) {

        receiptElement.hidden =
            false;

    }

}


// ============================================================
// LOAD RECEIPT
// ============================================================

async function loadDigitalReceipt() {

    if (!orderCode) {

        showReceiptError(
            "Kode pesanan tidak tersedia."
        );


        return;

    }


    if (!receiptToken) {

        showReceiptError(
            (
                "Akses struk tidak tersedia. "
                +
                "Buka struk dari halaman "
                +
                "status pesanan Anda."
            )
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

                        "X-Review-Token":
                            receiptToken

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
                "Struk belum dapat dimuat."
            );

        }


        /*
         * Token sudah diterima JS.
         * Hilangkan dari address bar.
         */

        cleanReceiptHash();


        renderDigitalReceipt(
            data.receipt
        );

    }

    catch (error) {

        console.error(
            "[DIGITAL RECEIPT]",
            error
        );


        showReceiptError(
            error.message
            ||
            "Struk belum dapat dimuat."
        );

    }

}


// ============================================================
// PRINT
// ============================================================

if (printButton) {

    printButton.addEventListener(
        "click",
        function () {

            window.print();

        }
    );

}


// ============================================================
// BACK
// ============================================================

function backToTracking() {

    if (
        window.history.length
        > 1
    ) {

        window.history.back();


        return;

    }


    window.location.href =
        "/";

}


if (backButton) {

    backButton.addEventListener(
        "click",
        backToTracking
    );

}


if (backErrorButton) {

    backErrorButton.addEventListener(
        "click",
        backToTracking
    );

}


// ============================================================
// INIT
// ============================================================

loadDigitalReceipt();