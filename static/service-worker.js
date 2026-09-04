"use strict";


// ============================================================
// PHASE 20H.7
// OJEK PRIBADI SERVICE WORKER
// ============================================================

const CACHE_PREFIX =
    "ojek-pribadi-public";

const CACHE_VERSION =
    "20h7-v1";

const CACHE_NAME =
    `${CACHE_PREFIX}-${CACHE_VERSION}`;


//
// Hanya shell publik.
//
// JANGAN masukkan:
// - /driver/...
// - /admin/...
// - /api/...
// - receipt
// - payment history
// - data transaksi
//

const PUBLIC_PRECACHE = [

    "/",

    "/manifest.webmanifest"

];


// ============================================================
// PRIVATE / SENSITIVE PATH
// ============================================================

function isPrivatePath(
    pathname
) {

    const path =
        String(
            pathname
            || ""
        )
        .toLowerCase();


    return (
        path === "/driver"
        ||
        path.startsWith(
            "/driver/"
        )
        ||
        path === "/admin"
        ||
        path.startsWith(
            "/admin/"
        )
        ||
        path === "/api"
        ||
        path.startsWith(
            "/api/"
        )
    );

}


// ============================================================
// SENSITIVE STATIC ASSET
// ============================================================

function isSensitiveStaticPath(
    pathname
) {

    const path =
        String(
            pathname
            || ""
        )
        .toLowerCase();


    return (
        path.includes(
            "payment-proof"
        )
        ||
        path.includes(
            "payment_proof"
        )
        ||
        path.includes(
            "receipt"
        )
        ||
        path.includes(
            "qris"
        )
    );

}


// ============================================================
// SAFE CACHE RESPONSE
// ============================================================

function responseCanBeCached(
    response
) {

    if (!response) {

        return false;

    }


    if (!response.ok) {

        return false;

    }


    if (
        response.type
        !== "basic"
    ) {

        return false;

    }


    const cacheControl =
        (
            response.headers.get(
                "Cache-Control"
            )
            || ""
        )
        .toLowerCase();


    if (
        cacheControl.includes(
            "no-store"
        )
    ) {

        return false;

    }


    return true;

}


// ============================================================
// INSTALL
// ============================================================

self.addEventListener(
    "install",
    function (
        event
    ) {

        event.waitUntil(

            (
                async function () {

                    const cache =
                        await caches.open(
                            CACHE_NAME
                        );


                    try {

                        await cache.addAll(
                            PUBLIC_PRECACHE
                        );

                    }
                    catch (error) {

                        console.warn(
                            "[SW] Precache tidak lengkap:",
                            error
                        );

                    }


                    await self.skipWaiting();

                }
            )()

        );

    }
);


// ============================================================
// ACTIVATE
// ============================================================

self.addEventListener(
    "activate",
    function (
        event
    ) {

        event.waitUntil(

            (
                async function () {

                    const cacheNames =
                        await caches.keys();


                    await Promise.all(

                        cacheNames.map(
                            function (
                                cacheName
                            ) {

                                if (
                                    cacheName.startsWith(
                                        CACHE_PREFIX
                                    )
                                    &&
                                    cacheName
                                    !== CACHE_NAME
                                ) {

                                    return caches.delete(
                                        cacheName
                                    );

                                }


                                return Promise.resolve();

                            }
                        )

                    );


                    await self.clients.claim();

                }
            )()

        );

    }
);


// ============================================================
// PRIVATE OFFLINE RESPONSE
// ============================================================

function privateOfflineResponse(
    request
) {

    if (
        request.mode
        === "navigate"
    ) {

        return new Response(
            `
            <!doctype html>
            <html lang="id">

            <head>

                <meta charset="utf-8">

                <meta
                    name="viewport"
                    content="
                        width=device-width,
                        initial-scale=1,
                        viewport-fit=cover
                    "
                >

                <meta
                    name="theme-color"
                    content="#07110d"
                >

                <title>
                    Koneksi Diperlukan
                </title>

                <style>

                    * {
                        box-sizing:
                            border-box;
                    }

                    html,
                    body {
                        margin:
                            0;

                        min-height:
                            100%;

                        min-height:
                            100dvh;
                    }

                    body {
                        display:
                            grid;

                        place-items:
                            center;

                        padding:
                            24px;

                        background:
                            #07110d;

                        color:
                            rgba(
                                255,
                                255,
                                255,
                                .9
                            );

                        font-family:
                            system-ui,
                            -apple-system,
                            BlinkMacSystemFont,
                            "Segoe UI",
                            sans-serif;
                    }

                    main {
                        width:
                            min(
                                100%,
                                420px
                            );

                        padding:
                            28px;

                        border:
                            1px solid
                            rgba(
                                255,
                                255,
                                255,
                                .07
                            );

                        border-radius:
                            24px;

                        background:
                            rgba(
                                255,
                                255,
                                255,
                                .025
                            );

                        text-align:
                            center;
                    }

                    .icon {
                        display:
                            grid;

                        place-items:
                            center;

                        width:
                            52px;

                        height:
                            52px;

                        margin:
                            0 auto 18px;

                        border-radius:
                            16px;

                        background:
                            rgba(
                                251,
                                191,
                                36,
                                .08
                            );

                        color:
                            #fbbf24;

                        font-size:
                            22px;
                    }

                    h1 {
                        margin:
                            0;

                        font-size:
                            22px;
                    }

                    p {
                        margin:
                            12px 0 22px;

                        color:
                            rgba(
                                255,
                                255,
                                255,
                                .42
                            );

                        font-size:
                            13px;

                        line-height:
                            1.65;
                    }

                    button {
                        width:
                            100%;

                        min-height:
                            48px;

                        border:
                            1px solid
                            rgba(
                                52,
                                211,
                                153,
                                .16
                            );

                        border-radius:
                            14px;

                        background:
                            rgba(
                                52,
                                211,
                                153,
                                .08
                            );

                        color:
                            #6ee7b7;

                        font-size:
                            13px;

                        font-weight:
                            800;

                        cursor:
                            pointer;
                    }

                </style>

            </head>

            <body>

                <main>

                    <div class="icon">
                        !
                    </div>

                    <h1>
                        Koneksi internet diperlukan
                    </h1>

                    <p>
                        Data pembayaran driver tidak disimpan
                        untuk penggunaan offline demi menjaga
                        keamanan dan memastikan informasi yang
                        ditampilkan selalu terbaru.
                    </p>

                    <button
                        type="button"
                        onclick="window.location.reload()"
                    >
                        Coba Muat Ulang
                    </button>

                </main>

            </body>

            </html>
            `,
            {
                status:
                    503,

                headers: {

                    "Content-Type":
                        "text/html; charset=utf-8",

                    "Cache-Control":
                        "no-store"
                }
            }
        );

    }


    return new Response(
        JSON.stringify(
            {
                success:
                    false,

                offline:
                    true,

                message:
                    (
                        "Koneksi internet "
                        +
                        "diperlukan."
                    )
            }
        ),
        {
            status:
                503,

            headers: {

                "Content-Type":
                    "application/json",

                "Cache-Control":
                    "no-store"
            }
        }
    );

}


// ============================================================
// PRIVATE NETWORK ONLY
// ============================================================

async function privateNetworkOnly(
    request
) {

    try {

        return await fetch(
            request
        );

    }
    catch (error) {

        return privateOfflineResponse(
            request
        );

    }

}


// ============================================================
// STATIC CACHE
// ============================================================

async function staticCacheFirst(
    request
) {

    const cache =
        await caches.open(
            CACHE_NAME
        );


    const cachedResponse =
        await cache.match(
            request
        );


    if (cachedResponse) {

        return cachedResponse;

    }


    const response =
        await fetch(
            request
        );


    if (
        responseCanBeCached(
            response
        )
    ) {

        await cache.put(
            request,
            response.clone()
        );

    }


    return response;

}


// ============================================================
// PUBLIC NAVIGATION
// ============================================================

async function publicNetworkFirst(
    request
) {

    const cache =
        await caches.open(
            CACHE_NAME
        );


    try {

        const response =
            await fetch(
                request
            );


        if (
            responseCanBeCached(
                response
            )
        ) {

            await cache.put(
                request,
                response.clone()
            );

        }


        return response;

    }
    catch (error) {

        const cachedPage =
            await cache.match(
                request
            );


        if (cachedPage) {

            return cachedPage;

        }


        const home =
            await cache.match(
                "/"
            );


        if (home) {

            return home;

        }


        throw error;

    }

}


// ============================================================
// FETCH
// ============================================================

self.addEventListener(
    "fetch",
    function (
        event
    ) {

        const request =
            event.request;


        // ----------------------------------------------------
        // GET ONLY
        // ----------------------------------------------------

        if (
            request.method
            !== "GET"
        ) {

            return;

        }


        const url =
            new URL(
                request.url
            );


        // ----------------------------------------------------
        // SAME ORIGIN ONLY
        // ----------------------------------------------------

        if (
            url.origin
            !== self.location.origin
        ) {

            return;

        }


        // ----------------------------------------------------
        // DRIVER / ADMIN / API
        //
        // NEVER CACHE.
        // ----------------------------------------------------

        if (
            isPrivatePath(
                url.pathname
            )
        ) {

            event.respondWith(
                privateNetworkOnly(
                    request
                )
            );

            return;

        }


        // ----------------------------------------------------
        // PAYMENT / RECEIPT STATIC
        //
        // NEVER CACHE.
        // ----------------------------------------------------

        if (
            isSensitiveStaticPath(
                url.pathname
            )
        ) {

            event.respondWith(
                privateNetworkOnly(
                    request
                )
            );

            return;

        }


        // ----------------------------------------------------
        // SAFE STATIC ASSETS
        // ----------------------------------------------------

        if (
            url.pathname.startsWith(
                "/static/"
            )
        ) {

            event.respondWith(
                staticCacheFirst(
                    request
                )
            );

            return;

        }


        // ----------------------------------------------------
        // PUBLIC DOCUMENT NAVIGATION
        // ----------------------------------------------------

        if (
            request.mode
            === "navigate"
        ) {

            event.respondWith(
                publicNetworkFirst(
                    request
                )
            );

        }

    }
);