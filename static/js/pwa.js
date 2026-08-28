"use strict";


// ============================================================
// OJEK PRIBADI
// PWA INSTALL MANAGER
// PHASE 13
// ============================================================


// ============================================================
// STATE
// ============================================================

let deferredInstallPrompt =
    null;


// ============================================================
// ELEMENTS
// ============================================================

const pwaInstallButton =
    document.getElementById(
        "pwaInstallButton"
    );


const pwaInstallStatus =
    document.getElementById(
        "pwaInstallStatus"
    );


// ============================================================
// SERVICE WORKER
// ============================================================

async function registerServiceWorker() {

    if (
        !(
            "serviceWorker"
            in navigator
        )
    ) {

        console.warn(
            "[PWA] Service Worker tidak didukung."
        );

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
                            "/"
                    }
                );


        console.log(
            "[PWA] Service Worker aktif:",
            registration.scope
        );

    }

    catch (error) {

        console.error(
            "[PWA] Service Worker gagal:",
            error
        );

    }

}


// ============================================================
// CHECK STANDALONE
// ============================================================

function isRunningStandalone() {

    return (

        window.matchMedia(
            "(display-mode: standalone)"
        ).matches

        ||

        window.navigator
            .standalone
        === true

    );

}


// ============================================================
// UPDATE INSTALL UI
// ============================================================

function updateInstallUI() {

    if (
        !pwaInstallButton
    ) {

        return;

    }


    if (
        isRunningStandalone()
    ) {

        pwaInstallButton.hidden =
            true;


        if (
            pwaInstallStatus
        ) {

            pwaInstallStatus.textContent =
                "Aplikasi sudah terpasang.";

        }


        return;

    }


    if (
        deferredInstallPrompt
    ) {

        pwaInstallButton.hidden =
            false;


        if (
            pwaInstallStatus
        ) {

            pwaInstallStatus.textContent =
                (
                    "Pasang Ojek Pribadi "
                    +
                    "ke perangkat Anda."
                );

        }

    }

}


// ============================================================
// BEFORE INSTALL PROMPT
// ============================================================

window.addEventListener(
    "beforeinstallprompt",
    function (
        event
    ) {

        event.preventDefault();


        deferredInstallPrompt =
            event;


        updateInstallUI();

    }
);


// ============================================================
// INSTALL BUTTON
// ============================================================

if (
    pwaInstallButton
) {

    pwaInstallButton.addEventListener(
        "click",
        async function () {

            if (
                !deferredInstallPrompt
            ) {

                return;

            }


            pwaInstallButton.disabled =
                true;


            try {

                deferredInstallPrompt
                    .prompt();


                const result =
                    await deferredInstallPrompt
                        .userChoice;


                console.log(
                    "[PWA] Install:",
                    result.outcome
                );


                deferredInstallPrompt =
                    null;


                if (
                    result.outcome
                    === "accepted"
                ) {

                    pwaInstallButton.hidden =
                        true;


                    if (
                        pwaInstallStatus
                    ) {

                        pwaInstallStatus.textContent =
                            (
                                "Ojek Pribadi "
                                +
                                "berhasil dipasang."
                            );

                    }

                }

            }

            catch (error) {

                console.error(
                    "[PWA INSTALL]",
                    error
                );

            }

            finally {

                pwaInstallButton.disabled =
                    false;

            }

        }
    );

}


// ============================================================
// APP INSTALLED
// ============================================================

window.addEventListener(
    "appinstalled",
    function () {

        deferredInstallPrompt =
            null;


        if (
            pwaInstallButton
        ) {

            pwaInstallButton.hidden =
                true;

        }


        if (
            pwaInstallStatus
        ) {

            pwaInstallStatus.textContent =
                "Aplikasi sudah terpasang.";

        }


        console.log(
            "[PWA] Aplikasi berhasil diinstall."
        );

    }
);


// ============================================================
// START
// ============================================================

registerServiceWorker();


updateInstallUI();