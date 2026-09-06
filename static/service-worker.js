"use strict";


// ============================================================
// OJEK PRIBADI
// SERVICE WORKER
//
// STRATEGY:
//
// HTML / NAVIGATION
// → NETWORK ONLY
// → NO OFFLINE FALLBACK
// → NEVER SERVE STALE CUSTOMER PAGE
//
// API / PRIVATE ROUTES
// → NETWORK ONLY
// → NO CACHE
//
// STATIC ASSETS
// → STALE WHILE REVALIDATE
// → CSS / JS / IMAGES / FONTS tetap cepat
// ============================================================


// ============================================================
// CACHE CONFIGURATION
// ============================================================

const CACHE_PREFIX =
    "ojek-pribadi-";


const STATIC_CACHE_NAME =
    "ojek-pribadi-static-v20i5-1";


// ============================================================
// STATIC FILE EXTENSIONS
// ============================================================

const STATIC_FILE_EXTENSIONS = [

    ".css",
    ".js",

    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".svg",
    ".ico",

    ".woff",
    ".woff2",
    ".ttf",
    ".otf"

];


// ============================================================
// INSTALL
// ============================================================

self.addEventListener(
    "install",
    () => {

        console.log(
            "[SERVICE WORKER] Installing..."
        );


        // Aktifkan versi baru secepat mungkin.
        self.skipWaiting();

    }
);


// ============================================================
// ACTIVATE
//
// Hapus cache lama.
// Ini sangat penting agar HTML lama dari service worker
// sebelumnya tidak terus tersedia.
// ============================================================

self.addEventListener(
    "activate",
    (event) => {

        console.log(
            "[SERVICE WORKER] Activating..."
        );


        event.waitUntil(

            Promise.all([

                // =================================================
                // DELETE OLD OJEK PRIBADI CACHES
                // =================================================

                caches.keys()
                    .then(
                        (cacheNames) => {

                            return Promise.all(

                                cacheNames.map(
                                    (cacheName) => {

                                        const isOjekCache =
                                            cacheName.startsWith(
                                                CACHE_PREFIX
                                            );


                                        const isCurrentCache =
                                            (
                                                cacheName
                                                ===
                                                STATIC_CACHE_NAME
                                            );


                                        if (
                                            isOjekCache
                                            &&
                                            !isCurrentCache
                                        ) {

                                            console.log(
                                                (
                                                    "[SERVICE WORKER] "
                                                    +
                                                    "Deleting old cache:"
                                                ),
                                                cacheName
                                            );


                                            return caches.delete(
                                                cacheName
                                            );

                                        }


                                        return Promise.resolve(
                                            false
                                        );

                                    }
                                )

                            );

                        }
                    ),


                // =================================================
                // CONTROL OPEN CLIENTS
                // =================================================

                self.clients.claim()

            ])

        );

    }
);


// ============================================================
// HELPERS
// ============================================================

function isSameOrigin(
    url
) {

    return (
        url.origin
        ===
        self.location.origin
    );

}


// ============================================================
// NAVIGATION / HTML REQUEST
//
// Semua dokumen HTML wajib ke server.
// Tidak pernah dibaca dari CacheStorage.
// ============================================================

function isNavigationRequest(
    request
) {

    if (
        request.mode
        ===
        "navigate"
    ) {

        return true;

    }


    const acceptHeader =
        request.headers.get(
            "accept"
        )
        ||
        "";


    return (
        acceptHeader.includes(
            "text/html"
        )
    );

}


// ============================================================
// PRIVATE / DYNAMIC ROUTES
// ============================================================

function isDynamicRoute(
    url
) {

    const pathname =
        url.pathname.toLowerCase();


    return (

        // API
        pathname.startsWith(
            "/api/"
        )

        ||

        // DRIVER / ADMIN
        pathname.startsWith(
            "/driver"
        )

        ||

        pathname.startsWith(
            "/admin"
        )

        ||

        // CUSTOMER ORDER
        pathname.startsWith(
            "/order"
        )

        ||

        pathname.includes(
            "/receipt"
        )

        ||

        pathname.includes(
            "/refund"
        )

        ||

        pathname.includes(
            "/review"
        )

        ||

        pathname.includes(
            "/payment"
        )

    );

}


// ============================================================
// STATIC ASSET
// ============================================================

function isStaticAsset(
    url
) {

    const pathname =
        url.pathname.toLowerCase();


    // ========================================================
    // /static/*
    // ========================================================

    if (
        pathname.startsWith(
            "/static/"
        )
    ) {

        return true;

    }


    // ========================================================
    // Manifest boleh dicache.
    // ========================================================

    if (
        pathname
        ===
        "/manifest.webmanifest"
    ) {

        return true;

    }


    // ========================================================
    // Root-level image/font/static file
    // jika suatu saat logo/icon tidak berada di /static/.
    // ========================================================

    return STATIC_FILE_EXTENSIONS.some(
        (extension) => {

            return pathname.endsWith(
                extension
            );

        }
    );

}


// ============================================================
// NETWORK ONLY
//
// Dipakai untuk:
// - HTML
// - customer pages
// - API
// - driver
// - payment
// - refund
// - receipt
//
// cache:"no-store" juga meminta browser tidak memakai
// HTTP cache lama untuk request tersebut.
// ============================================================

async function networkOnly(
    request
) {

    const networkRequest =
        new Request(
            request,
            {
                cache:
                    "no-store"
            }
        );


    try {

        return await fetch(
            networkRequest
        );

    }
    catch (error) {

        console.warn(
            (
                "[SERVICE WORKER] "
                +
                "Network unavailable:"
            ),
            request.url
        );


        // ====================================================
        // JANGAN return caches.match(request)
        //
        // Customer tidak boleh melihat halaman stale.
        // ====================================================

        if (
            isNavigationRequest(
                request
            )
        ) {

            return new Response(
                `
                <!doctype html>

                <html lang="id">

                <head>

                    <meta charset="utf-8">

                    <meta
                        name="viewport"
                        content="width=device-width, initial-scale=1"
                    >

                    <title>
                        OJEK PRIBADI — Server Tidak Tersedia
                    </title>

                    <style>

                        * {
                            box-sizing: border-box;
                        }


                        body {
                            margin: 0;

                            min-height: 100vh;

                            display: grid;

                            place-items: center;

                            padding: 24px;

                            background:
                                #050807;

                            color:
                                #ffffff;

                            font-family:
                                Arial,
                                sans-serif;
                        }


                        main {
                            width: 100%;

                            max-width: 420px;

                            padding: 24px;

                            border:
                                1px solid
                                rgba(
                                    255,
                                    255,
                                    255,
                                    .08
                                );

                            border-radius:
                                18px;

                            background:
                                rgba(
                                    255,
                                    255,
                                    255,
                                    .025
                                );
                        }


                        span {
                            color:
                                #34d399;

                            font-size:
                                11px;

                            font-weight:
                                800;

                            letter-spacing:
                                .08em;
                        }


                        h1 {
                            margin:
                                10px
                                0
                                8px;

                            font-size:
                                22px;
                        }


                        p {
                            margin: 0;

                            color:
                                rgba(
                                    255,
                                    255,
                                    255,
                                    .55
                                );

                            font-size:
                                14px;

                            line-height:
                                1.6;
                        }

                    </style>

                </head>

                <body>

                    <main>

                        <span>
                            OJEK PRIBADI
                        </span>

                        <h1>
                            Server sedang tidak tersedia
                        </h1>

                        <p>
                            Halaman ini membutuhkan koneksi
                            langsung ke server.
                            Silakan coba kembali setelah
                            layanan aktif.
                        </p>

                    </main>

                </body>

                </html>
                `,
                {
                    status:
                        503,

                    statusText:
                        "Service Unavailable",

                    headers: {

                        "Content-Type":
                            "text/html; charset=utf-8",

                        "Cache-Control":
                            "no-store, no-cache, must-revalidate"

                    }
                }
            );

        }


        // API / dynamic non-navigation.
        return new Response(
            JSON.stringify(
                {
                    ok:
                        false,

                    error:
                        "SERVER_UNAVAILABLE"
                }
            ),
            {
                status:
                    503,

                statusText:
                    "Service Unavailable",

                headers: {

                    "Content-Type":
                        "application/json; charset=utf-8",

                    "Cache-Control":
                        "no-store, no-cache, must-revalidate"

                }
            }
        );

    }

}


// ============================================================
// STATIC ASSET
// STALE WHILE REVALIDATE
//
// Aset cached langsung digunakan agar cepat,
// sementara browser mengambil versi terbaru di background.
// ============================================================

async function staleWhileRevalidate(
    request
) {

    const cache =
        await caches.open(
            STATIC_CACHE_NAME
        );


    const cachedResponse =
        await cache.match(
            request
        );


    const networkPromise =
        fetch(
            request
        )
        .then(
            async (response) => {

                // =================================================
                // Hanya cache response valid.
                // =================================================

                if (
                    response
                    &&
                    response.ok
                    &&
                    response.type
                    !==
                    "opaque"
                ) {

                    await cache.put(
                        request,
                        response.clone()
                    );

                }


                return response;

            }
        )
        .catch(
            (error) => {

                console.warn(
                    (
                        "[SERVICE WORKER] "
                        +
                        "Static asset update failed:"
                    ),
                    request.url,
                    error
                );


                return null;

            }
        );


    // ========================================================
    // Cached asset tersedia → langsung gunakan.
    // ========================================================

    if (
        cachedResponse
    ) {

        // Background refresh.
        networkPromise.catch(
            () => {}
        );


        return cachedResponse;

    }


    // ========================================================
    // Belum ada cache → tunggu network.
    // ========================================================

    const networkResponse =
        await networkPromise;


    if (
        networkResponse
    ) {

        return networkResponse;

    }


    return new Response(
        "",
        {
            status:
                503,

            statusText:
                "Static Asset Unavailable"
        }
    );

}


// ============================================================
// FETCH
// ============================================================

self.addEventListener(
    "fetch",
    (event) => {

        const request =
            event.request;


        // ====================================================
        // NON-GET
        //
        // POST payment/refund/order/etc
        // tidak boleh dicache.
        // ====================================================

        if (
            request.method
            !==
            "GET"
        ) {

            return;

        }


        const url =
            new URL(
                request.url
            );


        // ====================================================
        // CROSS ORIGIN
        //
        // Jangan masukkan Cloudinary / external API
        // ke CacheStorage aplikasi.
        // ====================================================

        if (
            !isSameOrigin(
                url
            )
        ) {

            return;

        }


        // ====================================================
        // RULE 1
        //
        // SEMUA HTML / NAVIGATION = NETWORK ONLY.
        //
        // Ini rule terpenting.
        // Bahkan kalau route customer baru ditambahkan
        // di masa depan, halaman HTML tetap tidak dicache.
        // ====================================================

        if (
            isNavigationRequest(
                request
            )
        ) {

            event.respondWith(
                networkOnly(
                    request
                )
            );


            return;

        }


        // ====================================================
        // RULE 2
        //
        // API / DRIVER / PAYMENT / REFUND / RECEIPT
        // = NETWORK ONLY.
        // ====================================================

        if (
            isDynamicRoute(
                url
            )
        ) {

            event.respondWith(
                networkOnly(
                    request
                )
            );


            return;

        }


        // ====================================================
        // RULE 3
        //
        // CSS / JS / LOGO / ICON / FONT
        // = CACHE.
        // ====================================================

        if (
            isStaticAsset(
                url
            )
        ) {

            event.respondWith(
                staleWhileRevalidate(
                    request
                )
            );


            return;

        }


        // ====================================================
        // RULE 4
        //
        // Request lain yang tidak dikenal:
        // network saja.
        //
        // Jangan cache secara otomatis.
        // ====================================================

        event.respondWith(
            networkOnly(
                request
            )
        );

    }
);