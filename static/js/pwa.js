"use strict";


// ============================================================
// PHASE 20H.7
// MOBILE & PWA POLISH
// ============================================================

(function () {

    // ========================================================
    // DOM
    // ========================================================

    const networkStatus =
        document.getElementById(
            "pwaNetworkStatus"
        );

    const networkStatusTitle =
        document.getElementById(
            "pwaNetworkStatusTitle"
        );

    const networkStatusText =
        document.getElementById(
            "pwaNetworkStatusText"
        );


    // ========================================================
    // NETWORK STATE
    // ========================================================

    function updateNetworkState() {

        const isOnline =
            navigator.onLine;


        document.documentElement.dataset.network =
            isOnline
                ? "online"
                : "offline";


        if (!networkStatus) {

            return;

        }


        if (isOnline) {

            networkStatus.hidden =
                true;

            return;

        }


        networkStatus.hidden =
            false;


        if (networkStatusTitle) {

            networkStatusTitle.textContent =
                "Anda sedang offline";

        }


        if (networkStatusText) {

            networkStatusText.textContent =
                (
                    "Data pembayaran tidak disimpan "
                    +
                    "untuk penggunaan offline."
                );

        }

    }


    // ========================================================
    // DISPLAY MODE
    // ========================================================

    function updateDisplayMode() {

        const standalone =
            (
                window.matchMedia(
                    "(display-mode: standalone)"
                ).matches
                ||
                window.navigator.standalone
                === true
            );


        document.documentElement.dataset.pwa =
            standalone
                ? "standalone"
                : "browser";

    }


    // ========================================================
    // SERVICE WORKER
    // ========================================================

    async function registerServiceWorker() {

        if (
            !(
                "serviceWorker"
                in navigator
            )
        ) {

            return;

        }


        if (!window.isSecureContext) {

            return;

        }


        try {

            const registration =
                await navigator
                    .serviceWorker
                    .register(
                        "/service-worker.js",
                        {
                            scope:
                                "/",

                            updateViaCache:
                                "none"
                        }
                    );


            // Minta browser memeriksa
            // versi service worker baru.
            registration.update();


        }
        catch (error) {

            console.error(
                "[PWA] Service worker gagal:",
                error
            );

        }

    }


    // ========================================================
    // EVENTS
    // ========================================================

    window.addEventListener(
        "online",
        updateNetworkState
    );


    window.addEventListener(
        "offline",
        updateNetworkState
    );


    window.addEventListener(
        "pageshow",
        updateNetworkState
    );


    // ========================================================
    // INITIALIZE
    // ========================================================

    updateNetworkState();

    updateDisplayMode();


    window.addEventListener(
        "load",
        registerServiceWorker,
        {
            once:
                true
        }
    );

})();