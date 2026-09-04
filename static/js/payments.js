"use strict";


// ============================================================
// PHASE 20H.2
// DRIVER PAYMENT HISTORY
// ============================================================


// ============================================================
// DOM
// ============================================================

const paymentHistoryList =
    document.getElementById(
        "paymentHistoryList"
    );

const paymentHistoryLoading =
    document.getElementById(
        "paymentHistoryLoading"
    );

const paymentHistoryEmpty =
    document.getElementById(
        "paymentHistoryEmpty"
    );

const paymentHistoryError =
    document.getElementById(
        "paymentHistoryError"
    );

const paymentHistoryErrorMessage =
    document.getElementById(
        "paymentHistoryErrorMessage"
    );

const paymentHistoryRetry =
    document.getElementById(
        "paymentHistoryRetry"
    );

const paymentHistoryPagination =
    document.getElementById(
        "paymentHistoryPagination"
    );

const paymentPreviousPage =
    document.getElementById(
        "paymentPreviousPage"
    );

const paymentNextPage =
    document.getElementById(
        "paymentNextPage"
    );

const paymentPageInfo =
    document.getElementById(
        "paymentPageInfo"
    );

const paymentResultInfo =
    document.getElementById(
        "paymentResultInfo"
    );

const paymentSearch =
    document.getElementById(
        "paymentSearch"
    );

const paymentSearchClear =
    document.getElementById(
        "paymentSearchClear"
    );

const paymentPeriodFilter =
    document.getElementById(
        "paymentPeriodFilter"
    );

const paymentMethodFilter =
    document.getElementById(
        "paymentMethodFilter"
    );

const paymentStatusFilter =
    document.getElementById(
        "paymentStatusFilter"
    );


// SUMMARY

const paymentTotalRecords =
    document.getElementById(
        "paymentTotalRecords"
    );

const paymentPaidAmount =
    document.getElementById(
        "paymentPaidAmount"
    );

const paymentPaidCount =
    document.getElementById(
        "paymentPaidCount"
    );

const paymentUnpaidCount =
    document.getElementById(
        "paymentUnpaidCount"
    );

const paymentPendingCount =
    document.getElementById(
        "paymentPendingCount"
    );


// ============================================================
// STATE
// ============================================================

let currentPage = 1;

let totalPages = 1;

let searchTimer = null;

let activeRequestController = null;


// ============================================================
// HELPERS
// ============================================================

function escapeHtml(value) {

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


function formatRupiah(value) {

    const amount =
        Number(
            value || 0
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


function formatPaymentDate(value) {

    if (!value) {

        return "Belum tercatat";

    }


    const normalized =
        String(value)
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
            day:
                "2-digit",

            month:
                "short",

            year:
                "numeric",

            hour:
                "2-digit",

            minute:
                "2-digit"
        }
    ).format(
        date
    );

}


function paymentMethodLabel(
    method
) {

    switch (method) {

        case "TUNAI":

            return "Tunai";


        case "QRIS":

            return "QRIS";


        case "TRANSFER_BANK":

            return "Transfer Bank";


        default:

            return "Belum Tercatat";

    }

}


function paymentStatusLabel(
    status
) {

    switch (status) {

        case "DIBAYAR":

            return "Dibayar";


        case "BELUM_DIBAYAR":

            return "Belum Dibayar";


        case "MENUNGGU_PEMBAYARAN":

            return "Menunggu Pembayaran";


        case "GAGAL":

            return "Gagal";


        case "KEDALUWARSA":

            return "Kedaluwarsa";


        case "DIKEMBALIKAN":

            return "Dikembalikan";


        default:

            return "Belum Tercatat";

    }

}


function paymentStatusClass(
    status
) {

    switch (status) {

        case "DIBAYAR":

            return "is-paid";


        case "BELUM_DIBAYAR":

            return "is-unpaid";


        case "MENUNGGU_PEMBAYARAN":

            return "is-pending";


        case "GAGAL":

            return "is-failed";


        case "KEDALUWARSA":

            return "is-expired";


        case "DIKEMBALIKAN":

            return "is-refunded";


        default:

            return "is-unknown";

    }

}


function paymentMethodClass(
    method
) {

    switch (method) {

        case "TUNAI":

            return "is-cash";


        case "QRIS":

            return "is-qris";


        case "TRANSFER_BANK":

            return "is-bank";


        default:

            return "is-unknown";

    }

}


// ============================================================
// URL
// ============================================================

function buildPaymentHistoryUrl() {

    const params =
        new URLSearchParams();


    params.set(
        "page",
        String(
            currentPage
        )
    );


    params.set(
        "period",
        paymentPeriodFilter?.value
        || "all"
    );


    params.set(
        "method",
        paymentMethodFilter?.value
        || "ALL"
    );


    params.set(
        "status",
        paymentStatusFilter?.value
        || "ALL"
    );


    const query =
        paymentSearch?.value
            .trim()
        || "";


    if (query) {

        params.set(
            "q",
            query
        );

    }


    return (
        "/api/driver/payments/history?"
        +
        params.toString()
    );

}


// ============================================================
// UI STATE
// ============================================================

function setPaymentHistoryLoading() {

    if (paymentHistoryLoading) {

        paymentHistoryLoading.hidden =
            false;

    }


    if (paymentHistoryList) {

        paymentHistoryList.hidden =
            true;

    }


    if (paymentHistoryEmpty) {

        paymentHistoryEmpty.hidden =
            true;

    }


    if (paymentHistoryError) {

        paymentHistoryError.hidden =
            true;

    }


    if (paymentHistoryPagination) {

        paymentHistoryPagination.hidden =
            true;

    }

}


function setPaymentHistoryError(
    message
) {

    if (paymentHistoryLoading) {

        paymentHistoryLoading.hidden =
            true;

    }


    if (paymentHistoryList) {

        paymentHistoryList.hidden =
            true;

    }


    if (paymentHistoryEmpty) {

        paymentHistoryEmpty.hidden =
            true;

    }


    if (paymentHistoryPagination) {

        paymentHistoryPagination.hidden =
            true;

    }


    if (paymentHistoryErrorMessage) {

        paymentHistoryErrorMessage.textContent =
            message
            ||
            "Riwayat pembayaran belum dapat dimuat.";

    }


    if (paymentHistoryError) {

        paymentHistoryError.hidden =
            false;

    }

}


// ============================================================
// SUMMARY
// ============================================================

function renderPaymentSummary(
    summary
) {

    if (!summary) {

        return;

    }


    if (paymentTotalRecords) {

        paymentTotalRecords.textContent =
            Number(
                summary.total_records
                || 0
            ).toLocaleString(
                "id-ID"
            );

    }


    if (paymentPaidAmount) {

        paymentPaidAmount.textContent =
            formatRupiah(
                summary.paid_amount
            );

    }


    if (paymentPaidCount) {

        paymentPaidCount.textContent =
            Number(
                summary.paid_count
                || 0
            ).toLocaleString(
                "id-ID"
            );

    }


    if (paymentUnpaidCount) {

        paymentUnpaidCount.textContent =
            Number(
                summary.unpaid_count
                || 0
            ).toLocaleString(
                "id-ID"
            );

    }


    if (paymentPendingCount) {

        paymentPendingCount.textContent =
            Number(
                summary.pending_count
                || 0
            ).toLocaleString(
                "id-ID"
            );

    }

}


// ============================================================
// PAYMENT CARD
// ============================================================

function buildPaymentCard(
    payment
) {

    const id =
        Number(
            payment.id || 0
        );


    const method =
        String(
            payment.method
            || ""
        );


    const status =
        String(
            payment.status
            || ""
        );


    const orderCode =
        escapeHtml(
            payment.order_code
            || "-"
        );


    const customerName =
        escapeHtml(
            payment.customer_name
            || "Pelanggan"
        );


    const reference =
        payment.reference
            ? escapeHtml(
                payment.reference
            )
            : "";


    const provider =
        payment.provider
            ? escapeHtml(
                payment.provider
            )
            : "";


    let extraPaymentInfo =
        "";


    if (reference) {

        extraPaymentInfo += `
            <div class="payment-history-detail-row">
                <span>REFERENSI</span>
                <strong>${reference}</strong>
            </div>
        `;

    }


    if (provider) {

        extraPaymentInfo += `
            <div class="payment-history-detail-row">
                <span>PROVIDER</span>
                <strong>${provider}</strong>
            </div>
        `;

    }


    return `
        <article class="payment-history-card">

            <div class="payment-history-card-main">

                <div class="payment-history-card-top">

                    <div>

                        <span class="payment-history-order-label">
                            ORDER
                        </span>

                        <strong class="payment-history-order-code">
                            ${orderCode}
                        </strong>

                    </div>


                    <span
                        class="
                            payment-history-status
                            ${paymentStatusClass(status)}
                        "
                    >
                        ${escapeHtml(
                            paymentStatusLabel(status)
                        )}
                    </span>

                </div>


                <div class="payment-history-customer">

                    <span>
                        ${customerName}
                    </span>

                    <small>
                        ${escapeHtml(
                            formatPaymentDate(
                                payment.payment_time
                            )
                        )}
                    </small>

                </div>


                <div class="payment-history-money">

                    <strong>
                        ${formatRupiah(
                            payment.amount
                        )}
                    </strong>

                    <span
                        class="
                            payment-history-method
                            ${paymentMethodClass(method)}
                        "
                    >
                        ${escapeHtml(
                            paymentMethodLabel(method)
                        )}
                    </span>

                </div>

            </div>


            <div class="payment-history-card-detail">

                <div class="payment-history-detail-row">

                    <span>
                        STATUS PERJALANAN
                    </span>

                    <strong>
                        ${escapeHtml(
                            payment.order_status
                            || "-"
                        )}
                    </strong>

                </div>


                ${extraPaymentInfo}


                <div class="payment-history-detail-row">

                    <span>
                        DIBAYAR
                    </span>

                    <strong>
                        ${
                            payment.paid_at
                                ? escapeHtml(
                                    formatPaymentDate(
                                        payment.paid_at
                                    )
                                )
                                : "-"
                        }
                    </strong>

                </div>

            </div>


            <div class="payment-history-card-footer">

                <a
                    href="/driver/orders/${encodeURIComponent(id)}"
                    class="payment-history-detail-button"
                >
                    Lihat Detail
                    <span>→</span>
                </a>

            </div>

        </article>
    `;

}


// ============================================================
// PAYMENT LIST
// ============================================================

function renderPayments(
    payments
) {

    if (!paymentHistoryList) {

        return;

    }


    paymentHistoryList.innerHTML =
        "";


    if (
        !Array.isArray(
            payments
        )
        ||
        payments.length === 0
    ) {

        paymentHistoryList.hidden =
            true;


        if (paymentHistoryEmpty) {

            paymentHistoryEmpty.hidden =
                false;

        }


        return;

    }


    if (paymentHistoryEmpty) {

        paymentHistoryEmpty.hidden =
            true;

    }


    paymentHistoryList.innerHTML =
        payments
            .map(
                buildPaymentCard
            )
            .join(
                ""
            );


    paymentHistoryList.hidden =
        false;

}


// ============================================================
// PAGINATION
// ============================================================

function renderPagination(
    pagination
) {

    if (!pagination) {

        return;

    }


    currentPage =
        Number(
            pagination.page
            || 1
        );


    totalPages =
        Number(
            pagination.total_pages
            || 1
        );


    if (paymentPageInfo) {

        paymentPageInfo.textContent =
            `Halaman ${currentPage} dari ${totalPages}`;

    }


    if (paymentPreviousPage) {

        paymentPreviousPage.disabled =
            !pagination.has_previous;

    }


    if (paymentNextPage) {

        paymentNextPage.disabled =
            !pagination.has_next;

    }


    if (paymentHistoryPagination) {

        paymentHistoryPagination.hidden =
            (
                Number(
                    pagination.total_records
                    || 0
                ) === 0
            );

    }

}


// ============================================================
// RESULT INFO
// ============================================================

function renderResultInfo(
    data
) {

    if (!paymentResultInfo) {

        return;

    }


    const total =
        Number(
            data?.pagination?.total_records
            || 0
        );


    const query =
        paymentSearch?.value
            .trim()
        || "";


    if (query) {

        paymentResultInfo.innerHTML =
            `
                <span>
                    Ditemukan
                    <strong>${total}</strong>
                    transaksi untuk
                    "<strong>${escapeHtml(query)}</strong>"
                </span>
            `;


        return;

    }


    paymentResultInfo.innerHTML =
        `
            <span>
                Menampilkan
                <strong>${total}</strong>
                transaksi pembayaran
            </span>
        `;

}


// ============================================================
// FETCH HISTORY
// ============================================================

async function loadPaymentHistory() {

    setPaymentHistoryLoading();


    if (activeRequestController) {

        activeRequestController.abort();

    }


    activeRequestController =
        new AbortController();


    try {

        const response =
            await fetch(
                buildPaymentHistoryUrl(),
                {
                    method:
                        "GET",

                    headers: {
                        "Accept":
                            "application/json"
                    },

                    credentials:
                        "same-origin",

                    cache:
                        "no-store",

                    signal:
                        activeRequestController
                            .signal
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
                data.debug
                ||
                data.message
                ||
                "Riwayat pembayaran gagal dimuat."
            );

        }


        if (paymentHistoryLoading) {

            paymentHistoryLoading.hidden =
                true;

        }


        renderPaymentSummary(
            data.summary
        );


        renderPayments(
            data.payments
        );


        renderPagination(
            data.pagination
        );


        renderResultInfo(
            data
        );

    }

    catch (error) {

        if (
            error.name
            === "AbortError"
        ) {

            return;

        }


        console.error(
            "[PAYMENT HISTORY]",
            error
        );


        setPaymentHistoryError(
            error.message
        );

    }

}


// ============================================================
// FILTER EVENTS
// ============================================================

function resetAndLoadPaymentHistory() {

    currentPage = 1;

    loadPaymentHistory();

}


paymentPeriodFilter?.addEventListener(
    "change",
    resetAndLoadPaymentHistory
);


paymentMethodFilter?.addEventListener(
    "change",
    resetAndLoadPaymentHistory
);


paymentStatusFilter?.addEventListener(
    "change",
    resetAndLoadPaymentHistory
);


// ============================================================
// SEARCH
// ============================================================

paymentSearch?.addEventListener(
    "input",
    () => {

        const hasValue =
            paymentSearch
                .value
                .trim()
                .length > 0;


        if (paymentSearchClear) {

            paymentSearchClear.hidden =
                !hasValue;

        }


        clearTimeout(
            searchTimer
        );


        searchTimer =
            setTimeout(
                () => {

                    resetAndLoadPaymentHistory();

                },
                350
            );

    }
);


paymentSearchClear?.addEventListener(
    "click",
    () => {

        if (!paymentSearch) {

            return;

        }


        paymentSearch.value =
            "";


        paymentSearchClear.hidden =
            true;


        paymentSearch.focus();


        resetAndLoadPaymentHistory();

    }
);


// ============================================================
// PAGINATION EVENTS
// ============================================================

paymentPreviousPage?.addEventListener(
    "click",
    () => {

        if (currentPage <= 1) {

            return;

        }


        currentPage -= 1;


        loadPaymentHistory();


        window.scrollTo(
            {
                top:
                    0,

                behavior:
                    "smooth"
            }
        );

    }
);


paymentNextPage?.addEventListener(
    "click",
    () => {

        if (
            currentPage
            >= totalPages
        ) {

            return;

        }


        currentPage += 1;


        loadPaymentHistory();


        window.scrollTo(
            {
                top:
                    0,

                behavior:
                    "smooth"
            }
        );

    }
);


// ============================================================
// RETRY
// ============================================================

paymentHistoryRetry?.addEventListener(
    "click",
    () => {

        loadPaymentHistory();

    }
);


// ============================================================
// INIT
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        loadPaymentHistory();

    }
);