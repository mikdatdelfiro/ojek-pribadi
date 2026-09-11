"use strict";

// ============================================================
// OJEK PRIBADI
// PHASE 26B — UNIVERSAL PWA INSTALL SYSTEM
// Android + iPhone/iPad
// ============================================================

(function () {

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

    const pageInstallButton =
        document.getElementById(
            "pwaInstallButton"
        );

    const installStatus =
        document.getElementById(
            "pwaInstallStatus"
        );


    let deferredInstallPrompt =
        null;

    let floatingInstallButton =
        null;

    let installModal =
        null;


    // ========================================================
    // DEVICE DETECTION
    // ========================================================

    function isIOS() {

        const ua =
            navigator.userAgent
            || "";


        return (

            /iPhone|iPad|iPod/i.test(
                ua
            )

            ||

            (
                navigator.platform
                ===
                "MacIntel"

                &&

                navigator.maxTouchPoints
                >
                1
            )
        );

    }


    function isAndroid() {

        return /Android/i.test(
            navigator.userAgent
            || ""
        );

    }


    function isIOSSafari() {

        if (!isIOS()) {

            return false;

        }


        const ua =
            navigator.userAgent
            || "";


        return (

            /AppleWebKit/i.test(
                ua
            )

            &&

            !/CriOS|FxiOS|EdgiOS|OPiOS|DuckDuckGo/i.test(
                ua
            )
        );

    }


    // ========================================================
    // STANDALONE
    // ========================================================

    function isStandalone() {

        return (

            window.matchMedia(
                "(display-mode: standalone)"
            ).matches

            ||

            window.matchMedia(
                "(display-mode: fullscreen)"
            ).matches

            ||

            window.navigator.standalone
            ===
            true
        );

    }


    // ========================================================
    // NETWORK
    // ========================================================

    function updateNetworkState() {

        const online =
            navigator.onLine;


        document.documentElement.dataset.network =
            online
                ? "online"
                : "offline";


        if (!networkStatus) {

            return;

        }


        networkStatus.hidden =
            online;


        if (!online) {

            if (networkStatusTitle) {

                networkStatusTitle.textContent =
                    "Anda sedang offline";

            }


            if (networkStatusText) {

                networkStatusText.textContent =
                    (
                        "Data perjalanan dan pembayaran "
                        +
                        "membutuhkan koneksi ke server."
                    );

            }

        }

    }


    // ========================================================
    // INSTALL STYLE
    // ========================================================

    function ensureStyles() {

        if (
            document.getElementById(
                "pwaInstallStyles"
            )
        ) {

            return;

        }


        const style =
            document.createElement(
                "style"
            );


        style.id =
            "pwaInstallStyles";


        style.textContent = `

            .pwa-global-install-button {

                position: fixed;

                right: 16px;

                bottom:
                    calc(
                        16px
                        +
                        env(
                            safe-area-inset-bottom
                        )
                    );

                z-index: 9000;

                min-height: 46px;

                padding:
                    0
                    16px;

                border:
                    1px solid
                    rgba(
                        45,
                        212,
                        160,
                        .34
                    );

                border-radius:
                    999px;

                background:
                    rgba(
                        5,
                        18,
                        13,
                        .96
                    );

                color:
                    #ffffff;

                box-shadow:
                    0
                    16px
                    46px
                    rgba(
                        0,
                        0,
                        0,
                        .35
                    );

                font:
                    inherit;

                font-size:
                    12px;

                font-weight:
                    800;

                cursor:
                    pointer;
            }


            .pwa-global-install-button[hidden],

            .pwa-install-modal[hidden] {

                display:
                    none
                    !important;
            }


            .pwa-install-modal {

                position:
                    fixed;

                inset:
                    0;

                z-index:
                    10000;

                display:
                    grid;

                place-items:
                    end
                    center;

                padding:
                    18px;

                background:
                    rgba(
                        0,
                        0,
                        0,
                        .62
                    );

                backdrop-filter:
                    blur(
                        8px
                    );
            }


            .pwa-install-card {

                width:
                    min(
                        460px,
                        100%
                    );

                padding:
                    22px;

                border:
                    1px solid
                    rgba(
                        45,
                        212,
                        160,
                        .20
                    );

                border-radius:
                    24px;

                background:
                    #071711;

                color:
                    #ffffff;

                box-shadow:
                    0
                    24px
                    80px
                    rgba(
                        0,
                        0,
                        0,
                        .48
                    );
            }


            .pwa-install-head {

                display:
                    flex;

                justify-content:
                    space-between;

                gap:
                    14px;

                align-items:
                    flex-start;
            }


            .pwa-install-kicker {

                color:
                    #2dd4a0;

                font-size:
                    10px;

                font-weight:
                    900;

                letter-spacing:
                    .12em;
            }


            .pwa-install-title {

                margin:
                    6px
                    0
                    0;

                font-size:
                    21px;
            }


            .pwa-install-close {

                width:
                    38px;

                height:
                    38px;

                border:
                    1px solid
                    rgba(
                        255,
                        255,
                        255,
                        .10
                    );

                border-radius:
                    12px;

                background:
                    rgba(
                        255,
                        255,
                        255,
                        .05
                    );

                color:
                    #ffffff;

                font-size:
                    20px;

                cursor:
                    pointer;
            }


            .pwa-install-text {

                margin:
                    12px
                    0
                    0;

                color:
                    rgba(
                        255,
                        255,
                        255,
                        .64
                    );

                font-size:
                    13px;

                line-height:
                    1.65;
            }


            .pwa-install-steps {

                margin:
                    18px
                    0
                    0;

                padding:
                    0;

                list-style:
                    none;

                display:
                    grid;

                gap:
                    10px;
            }


            .pwa-install-step {

                padding:
                    13px;

                border:
                    1px solid
                    rgba(
                        255,
                        255,
                        255,
                        .08
                    );

                border-radius:
                    15px;

                background:
                    rgba(
                        255,
                        255,
                        255,
                        .035
                    );
            }


            .pwa-install-step strong {

                display:
                    block;

                margin-bottom:
                    4px;

                font-size:
                    12px;
            }


            .pwa-install-step span {

                color:
                    rgba(
                        255,
                        255,
                        255,
                        .58
                    );

                font-size:
                    11px;

                line-height:
                    1.55;
            }


            .pwa-install-ok {

                width:
                    100%;

                min-height:
                    48px;

                margin-top:
                    18px;

                border:
                    0;

                border-radius:
                    14px;

                background:
                    #2dd4a0;

                color:
                    #04130d;

                font:
                    inherit;

                font-size:
                    12px;

                font-weight:
                    900;

                cursor:
                    pointer;
            }


            @media (
                min-width:
                700px
            ) {

                .pwa-install-modal {

                    place-items:
                        center;
                }

            }

        `;


        document.head.appendChild(
            style
        );

    }


    // ========================================================
    // FLOATING BUTTON
    // ========================================================

    function ensureFloatingButton() {

        if (
            pageInstallButton
            ||
            floatingInstallButton
            ||
            isStandalone()
        ) {

            return;

        }


        ensureStyles();


        floatingInstallButton =
            document.createElement(
                "button"
            );


        floatingInstallButton.type =
            "button";


        floatingInstallButton.className =
            "pwa-global-install-button";


        floatingInstallButton.textContent =
            "Install OJEK PRIBADI";


        floatingInstallButton.hidden =
            true;


        floatingInstallButton.addEventListener(
            "click",
            handleInstallClick
        );


        document.body.appendChild(
            floatingInstallButton
        );

    }


    function activeInstallButton() {

        return (
            pageInstallButton
            ||
            floatingInstallButton
        );

    }


    function showInstallUI(
        message = ""
    ) {

        if (
            isStandalone()
        ) {

            hideInstallUI();

            return;

        }


        ensureFloatingButton();


        const button =
            activeInstallButton();


        if (button) {

            button.hidden =
                false;

        }


        if (
            installStatus
            &&
            message
        ) {

            installStatus.textContent =
                message;

        }

    }


    function hideInstallUI() {

        if (
            pageInstallButton
        ) {

            pageInstallButton.hidden =
                true;

        }


        if (
            floatingInstallButton
        ) {

            floatingInstallButton.hidden =
                true;

        }

    }


    // ========================================================
    // MODAL
    // ========================================================

    function ensureModal() {

        if (
            installModal
        ) {

            return installModal;

        }


        ensureStyles();


        installModal =
            document.createElement(
                "div"
            );


        installModal.className =
            "pwa-install-modal";


        installModal.hidden =
            true;


        installModal.setAttribute(
            "role",
            "dialog"
        );


        installModal.setAttribute(
            "aria-modal",
            "true"
        );


        installModal.innerHTML = `

            <div
                class="pwa-install-card"
            >

                <div
                    class="pwa-install-head"
                >

                    <div>

                        <span
                            class="pwa-install-kicker"
                        >
                            OJEK PRIBADI
                        </span>

                        <h2
                            class="pwa-install-title"
                            id="pwaGuideTitle"
                        ></h2>

                    </div>


                    <button
                        type="button"
                        class="pwa-install-close"
                        aria-label="Tutup"
                    >
                        ×
                    </button>

                </div>


                <p
                    class="pwa-install-text"
                    id="pwaGuideText"
                ></p>


                <ol
                    class="pwa-install-steps"
                    id="pwaGuideSteps"
                ></ol>


                <button
                    type="button"
                    class="pwa-install-ok"
                >
                    Mengerti
                </button>

            </div>

        `;


        document.body.appendChild(
            installModal
        );


        const close =
            function () {

                installModal.hidden =
                    true;

            };


        installModal
            .querySelector(
                ".pwa-install-close"
            )
            .addEventListener(
                "click",
                close
            );


        installModal
            .querySelector(
                ".pwa-install-ok"
            )
            .addEventListener(
                "click",
                close
            );


        installModal.addEventListener(
            "click",
            function (
                event
            ) {

                if (
                    event.target
                    ===
                    installModal
                ) {

                    close();

                }

            }
        );


        document.addEventListener(
            "keydown",
            function (
                event
            ) {

                if (
                    event.key
                    ===
                    "Escape"

                    &&

                    installModal

                    &&

                    !installModal.hidden
                ) {

                    close();

                }

            }
        );


        return installModal;

    }


    function showGuide(
        title,
        text,
        steps
    ) {

        const modal =
            ensureModal();


        modal
            .querySelector(
                "#pwaGuideTitle"
            )
            .textContent =
                title;


        modal
            .querySelector(
                "#pwaGuideText"
            )
            .textContent =
                text;


        const list =
            modal.querySelector(
                "#pwaGuideSteps"
            );


        list.replaceChildren();


        steps.forEach(
            function (
                step
            ) {

                const item =
                    document.createElement(
                        "li"
                    );


                item.className =
                    "pwa-install-step";


                const strong =
                    document.createElement(
                        "strong"
                    );


                strong.textContent =
                    step.title;


                const span =
                    document.createElement(
                        "span"
                    );


                span.textContent =
                    step.text;


                item.append(
                    strong,
                    span
                );


                list.appendChild(
                    item
                );

            }
        );


        modal.hidden =
            false;

    }


    // ========================================================
    // IOS GUIDE
    // ========================================================

    function showIOSGuide() {

        if (
            !isIOSSafari()
        ) {

            showGuide(

                "Buka melalui Safari",

                (
                    "Untuk memasang Ojek Pribadi "
                    +
                    "di iPhone/iPad, buka halaman "
                    +
                    "ini menggunakan Safari."
                ),

                [

                    {
                        title:
                            "Buka Safari",

                        text:
                            (
                                "Buka link Ojek Pribadi "
                                +
                                "menggunakan Safari."
                            )
                    },

                    {
                        title:
                            "Tekan Bagikan",

                        text:
                            (
                                "Tekan ikon Bagikan "
                                +
                                "pada toolbar Safari."
                            )
                    },

                    {
                        title:
                            "Tambah ke Layar Utama",

                        text:
                            (
                                "Pilih Tambahkan ke Layar Utama "
                                +
                                "lalu tekan Tambah."
                            )
                    }

                ]

            );


            return;

        }


        showGuide(

            "Install di iPhone / iPad",

            (
                "Apple memasang PWA "
                +
                "melalui menu Safari."
            ),

            [

                {
                    title:
                        "Tekan Bagikan",

                    text:
                        (
                            "Tekan ikon Bagikan "
                            +
                            "di toolbar Safari."
                        )
                },

                {
                    title:
                        "Tambah ke Layar Utama",

                    text:
                        (
                            "Pilih Tambahkan "
                            +
                            "ke Layar Utama."
                        )
                },

                {
                    title:
                        "Tekan Tambah",

                    text:
                        (
                            "Konfirmasi. Ikon Ojek Pribadi "
                            +
                            "akan muncul sebagai aplikasi."
                        )
                }

            ]

        );

    }


    // ========================================================
    // ANDROID GUIDE
    // ========================================================

    function showAndroidGuide() {

        showGuide(

            "Install di Android",

            (
                "Browser belum menampilkan "
                +
                "prompt otomatis. Gunakan menu "
                +
                "browser untuk memasang aplikasi."
            ),

            [

                {
                    title:
                        "Buka menu browser",

                    text:
                        (
                            "Tekan menu ⋮ di Chrome "
                            +
                            "atau menu utama browser."
                        )
                },

                {
                    title:
                        "Pilih Install app",

                    text:
                        (
                            "Pilih Install app "
                            +
                            "/ Pasang aplikasi."
                        )
                },

                {
                    title:
                        "Konfirmasi",

                    text:
                        (
                            "Tekan Install atau Pasang."
                        )
                }

            ]

        );

    }


    // ========================================================
    // NATIVE INSTALL
    // ========================================================

    async function promptNativeInstall() {

        if (
            !deferredInstallPrompt
        ) {

            return false;

        }


        const promptEvent =
            deferredInstallPrompt;


        deferredInstallPrompt =
            null;


        try {

            await promptEvent.prompt();


            const choice =
                await promptEvent.userChoice;


            if (
                choice
                &&
                choice.outcome
                ===
                "accepted"
            ) {

                if (
                    installStatus
                ) {

                    installStatus.textContent =
                        (
                            "Instalasi Ojek Pribadi "
                            +
                            "sedang diproses."
                        );

                }

            }
            else {

                showInstallUI(
                    (
                        "Anda dapat memasang "
                        +
                        "Ojek Pribadi kapan saja."
                    )
                );

            }


            return true;

        }
        catch (
            error
        ) {

            console.warn(
                "[PWA INSTALL]",
                error
            );


            showInstallUI(
                (
                    "Instalasi otomatis "
                    +
                    "belum tersedia."
                )
            );


            return false;

        }

    }


    // ========================================================
    // INSTALL CLICK
    // ========================================================

    async function handleInstallClick() {

        if (
            isStandalone()
        ) {

            hideInstallUI();

            return;

        }


        if (
            deferredInstallPrompt
        ) {

            await promptNativeInstall();

            return;

        }


        if (
            isIOS()
        ) {

            showIOSGuide();

            return;

        }


        if (
            isAndroid()
        ) {

            showAndroidGuide();

            return;

        }


        showGuide(

            "Install Ojek Pribadi",

            (
                "Gunakan menu browser "
                +
                "jika opsi Install app tersedia."
            ),

            [

                {
                    title:
                        "Buka menu browser",

                    text:
                        (
                            "Cari opsi Install app "
                            +
                            "atau Pasang aplikasi."
                        )
                },

                {
                    title:
                        "Konfirmasi",

                    text:
                        (
                            "Ikuti proses instalasi "
                            +
                            "yang ditampilkan browser."
                        )
                }

            ]

        );

    }

// ========================================================
// PHASE 26D
// STANDALONE NAVIGATION
// ========================================================

function updateStandaloneNavigation() {

    const navigation =
        document.getElementById(
            "pwaStandaloneNav"
        );


    if (!navigation) {

        return;

    }


    const pathname =
        String(
            window.location.pathname
            || "/"
        )
        .toLowerCase();


    // ====================================================
    // PHASE 26D FIX
    // TENTUKAN AREA APLIKASI
    // ====================================================

    const driverArea =
        (
            pathname.startsWith(
                "/driver"
            )

            ||

            pathname.startsWith(
                "/admin"
            )
        );


    const customerNavigationAllowed =
        (
            pathname === "/app"

            ||

            pathname === "/customer/account"

            ||

            pathname.startsWith(
                "/customer/orders"
            )
        );


    if (driverArea) {

        document.documentElement.dataset.pwaArea =
            "driver";

    }

    else if (customerNavigationAllowed) {

        document.documentElement.dataset.pwaArea =
            "customer";

    }

    else {

        document.documentElement.dataset.pwaArea =
            "other";

    }


    // ====================================================
    // DRIVER / LANDING / LOGIN
    // CUSTOMER BOTTOM NAV TIDAK BOLEH MUNCUL
    // ====================================================

    if (!customerNavigationAllowed) {

        navigation.setAttribute(
            "aria-hidden",
            "true"
        );


        navigation
            .querySelectorAll(
                ".pwa-nav-item"
            )
            .forEach(
                function (item) {

                    item.classList.remove(
                        "is-active"
                    );

                    item.removeAttribute(
                        "aria-current"
                    );

                }
            );


        return;

    }


    navigation.removeAttribute(
        "aria-hidden"
    );


    // ====================================================
    // CUSTOMER ACTIVE MENU
    // ====================================================

    const items =
        navigation.querySelectorAll(
            ".pwa-nav-item"
        );


    items.forEach(
        function (item) {

            item.classList.remove(
                "is-active"
            );

            item.removeAttribute(
                "aria-current"
            );

        }
    );


    let activeRoute =
        "home";


    if (
        pathname ===
        "/customer/account"
    ) {

        activeRoute =
            "account";

    }

    else if (
        pathname.startsWith(
            "/customer/orders"
        )
    ) {

        activeRoute =
            "orders";

    }


    const activeItem =
        navigation.querySelector(
            (
                '[data-pwa-route="'
                +
                activeRoute
                +
                '"]'
            )
        );


    if (activeItem) {

        activeItem.classList.add(
            "is-active"
        );


        activeItem.setAttribute(
            "aria-current",
            "page"
        );

    }

}

    // ========================================================
    // DISPLAY MODE UPDATE
    // ========================================================

    function updateDisplayMode() {

        const standalone =
            isStandalone();


        document.documentElement.dataset.pwa =
            standalone
                ? "standalone"
                : "browser";


        if (
            standalone
        ) {

            hideInstallUI();


            if (
                installStatus
            ) {

                installStatus.textContent =
                    (
                        "Ojek Pribadi sudah "
                        +
                        "terpasang di perangkat ini."
                    );

            }

        }

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
            ||
            !window.isSecureContext
        ) {

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


            registration.update();

        }
        catch (
            error
        ) {

            console.error(
                "[PWA] Service worker gagal:",
                error
            );

        }

    }


    // ========================================================
    // BEFOREINSTALLPROMPT
    // ========================================================

    window.addEventListener(
        "beforeinstallprompt",
        function (
            event
        ) {

            event.preventDefault();


            deferredInstallPrompt =
                event;


            showInstallUI(
                (
                    "Ojek Pribadi siap dipasang "
                    +
                    "sebagai aplikasi."
                )
            );

        }
    );


    // ========================================================
    // APP INSTALLED
    // ========================================================

    window.addEventListener(
        "appinstalled",
        function () {

            deferredInstallPrompt =
                null;


            hideInstallUI();


            document.documentElement.dataset.pwa =
                "standalone";


            if (
                installStatus
            ) {

                installStatus.textContent =
                    (
                        "Ojek Pribadi "
                        +
                        "berhasil dipasang."
                    );

            }

        }
    );


    // ========================================================
    // EXISTING BUTTON
    // ========================================================

    if (
        pageInstallButton
    ) {

        pageInstallButton.addEventListener(
            "click",
            handleInstallClick
        );

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
        function () {

            updateNetworkState();

            updateDisplayMode();

            updateStandaloneNavigation();

            updateNativeBackButton();


            document.documentElement.dataset.pwaTransition =
                "ready";

        }
    );

// ========================================================
// PHASE 26D
// DISPLAY MODE CHANGE

const standaloneMediaQuery =
    window.matchMedia(
        "(display-mode: standalone)"
    );


function handleStandaloneModeChange() {

    updateDisplayMode();

    updateStandaloneNavigation();

}


if (
    typeof
    standaloneMediaQuery.addEventListener
    ===
    "function"
) {

    standaloneMediaQuery.addEventListener(
        "change",
        handleStandaloneModeChange
    );

}
else if (
    typeof
    standaloneMediaQuery.addListener
    ===
    "function"
) {

    standaloneMediaQuery.addListener(
        handleStandaloneModeChange
    );

}

// ========================================================
// PHASE 26E
// SESSION + BACK + NATIVE EXPERIENCE
// ========================================================

const pwaNativeBack =
    document.getElementById(
        "pwaNativeBack"
    );


let pwaNavigationLocked =
    false;


let pwaHiddenAt =
    null;


// ========================================================
// PRIVATE CUSTOMER PATH
// ========================================================

function isPrivateCustomerPath() {

    const pathname =
        String(
            window.location.pathname
            || "/"
        ).toLowerCase();


    return (

        pathname === "/"

        ||

        pathname.startsWith(
            "/customer/account"
        )

        ||

        pathname.startsWith(
            "/customer/orders"
        )
    );

}


// ========================================================
// AUTH PAGE
// ========================================================

function isCustomerAuthPage() {

    const pathname =
        String(
            window.location.pathname
            || ""
        ).toLowerCase();


    return (

        pathname
        ===
        "/customer/login"

        ||

        pathname
        ===
        "/customer/register"
    );

}


// ========================================================
// DETAIL PAGE
// ========================================================

function isCustomerOrderDetailPage() {

    const pathname =
        String(
            window.location.pathname
            || ""
        ).toLowerCase();


    const parts =
        pathname
            .split("/")
            .filter(Boolean);


    return (

        parts.length === 3

        &&

        parts[0] === "customer"

        &&

        parts[1] === "orders"
    );

}


// ========================================================
// BACK BUTTON VISIBILITY
// ========================================================

function updateNativeBackButton() {

    if (!pwaNativeBack) {

        return;

    }


    const visible = (

        isStandalone()

        &&

        isCustomerOrderDetailPage()
    );


    pwaNativeBack.hidden =
        !visible;

}


// ========================================================
// SAFE BACK
// ========================================================

function handleNativeBack() {

    if (
        pwaNavigationLocked
    ) {

        return;

    }


    pwaNavigationLocked =
        true;


    document.documentElement.dataset.pwaTransition =
        "leaving";


    window.setTimeout(
        function () {

            /*
             * Detail order selalu kembali ke
             * riwayat customer.
             *
             * Jangan gunakan history.back()
             * karena history dapat berisi
             * halaman login lama setelah logout/login.
             */
            window.location.href =
                "/customer/orders";

        },
        110
    );

}


if (
    pwaNativeBack
) {

    pwaNativeBack.addEventListener(
        "click",
        handleNativeBack
    );

}


// ========================================================
// INTERNAL LINK TRANSITION
// ========================================================

document.addEventListener(
    "click",
    function (
        event
    ) {

        if (
            event.defaultPrevented
            ||
            event.button !== 0
        ) {

            return;

        }


        const link =
            event.target.closest(
                "a[href]"
            );


        if (!link) {

            return;

        }


        if (
            link.target
            &&
            link.target !== "_self"
        ) {

            return;

        }


        if (
            link.hasAttribute(
                "download"
            )
        ) {

            return;

        }


        const href =
            link.getAttribute(
                "href"
            );


        if (
            !href
            ||
            href.startsWith("#")
            ||
            href.startsWith("javascript:")
        ) {

            return;

        }


        let targetUrl;


        try {

            targetUrl =
                new URL(
                    link.href,
                    window.location.href
                );

        }
        catch (
            error
        ) {

            return;

        }


        if (
            targetUrl.origin
            !==
            window.location.origin
        ) {

            return;

        }


        if (
            pwaNavigationLocked
        ) {

            event.preventDefault();

            return;

        }


        pwaNavigationLocked =
            true;


        document.documentElement.dataset.pwaTransition =
            "leaving";

    }
);


// ========================================================
// PAGE SHOW
// BFCache SECURITY
// ========================================================

window.addEventListener(
    "pageshow",
    function (
        event
    ) {

        pwaNavigationLocked =
            false;


        document.documentElement.dataset.pwaTransition =
            "ready";


        updateNativeBackButton();


        /*
         * Safari / Chrome dapat mengembalikan halaman
         * lama dari Back-Forward Cache.
         *
         * Untuk halaman private, paksa server melakukan
         * validasi session lagi.
         */
        if (
            event.persisted

            &&

            isPrivateCustomerPath()
        ) {

            window.location.reload();

        }

    }
);


// ========================================================
// PAGE HIDE
// ========================================================

window.addEventListener(
    "pagehide",
    function () {

        pwaNavigationLocked =
            false;

    }
);


// ========================================================
// APP BACKGROUND / RESUME
// ========================================================

document.addEventListener(
    "visibilitychange",
    function () {

        if (
            document.visibilityState
            ===
            "hidden"
        ) {

            pwaHiddenAt =
                Date.now();

            return;

        }


        if (
            document.visibilityState
            !==
            "visible"
        ) {

            return;

        }


        const hiddenDuration =
            pwaHiddenAt
                ?
                (
                    Date.now()
                    -
                    pwaHiddenAt
                )
                :
                0;


        pwaHiddenAt =
            null;


        updateNetworkState();

        updateDisplayMode();

        updateStandaloneNavigation();

        updateNativeBackButton();


        /*
         * Beri tahu script halaman lain bahwa
         * aplikasi baru kembali dari background.
         */
        window.dispatchEvent(
            new CustomEvent(
                "pwa:resume",
                {
                    detail: {

                        hiddenDuration:
                            hiddenDuration

                    }
                }
            )
        );

    }
);


// ========================================================
// FOCUS
// ========================================================

window.addEventListener(
    "focus",
    function () {

        updateNetworkState();

        updateDisplayMode();

        updateStandaloneNavigation();

        updateNativeBackButton();

    }
);


// ========================================================
// FORM DOUBLE SUBMIT PROTECTION
// ========================================================

document.addEventListener(
    "submit",
    function (
        event
    ) {

        const form =
            event.target;


        if (
            !(form instanceof HTMLFormElement)
        ) {

            return;

        }


        const submitButtons =
            form.querySelectorAll(
                'button[type="submit"], input[type="submit"]'
            );


        window.setTimeout(
            function () {

                submitButtons.forEach(
                    function (
                        button
                    ) {

                        button.disabled =
                            true;

                        button.setAttribute(
                            "aria-disabled",
                            "true"
                        );

                    }
                );

            },
            0
        );

    }
);

    // ========================================================
    // INITIALIZE
    // ========================================================

    updateNetworkState();

    updateDisplayMode();


    if (
        !isStandalone()
    ) {

        if (
            isIOS()
        ) {

            showInstallUI(
                (
                    "Install Ojek Pribadi "
                    +
                    "di iPhone atau iPad."
                )
            );

        }
        else if (
            isAndroid()
        ) {

            window.setTimeout(

                function () {

                    if (
                        !isStandalone()

                        &&

                        !deferredInstallPrompt
                    ) {

                        showInstallUI(
                            (
                                "Pasang Ojek Pribadi "
                                +
                                "dari browser Android Anda."
                            )
                        );

                    }

                },

                1500

            );

        }

    }


    window.addEventListener(
        "load",
        registerServiceWorker,
        {
            once:
                true
        }
    );
})();    