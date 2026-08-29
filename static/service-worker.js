"use strict";


// ============================================================
// OJEK PRIBADI
// SERVICE WORKER
// PHASE 13
// ============================================================

const CACHE_NAME =
    "ojek-pribadi-v4";


// ============================================================
// STATIC FILES
// ============================================================

const STATIC_ASSETS = [

    "/static/css/style.css",

    "/static/js/app.js",

    "/static/js/driver.js",

    "/static/js/order_status.js",

    "/static/js/pwa.js",

    "/static/icons/icon-192.png",

    "/static/icons/icon-512.png",

    "/static/icons/apple-touch-icon.png"

];


// ============================================================
// INSTALL
// ============================================================

self.addEventListener(
    "install",
    function (
        event
    ) {

        event.waitUntil(

            caches
                .open(
                    CACHE_NAME
                )
                .then(
                    async function (
                        cache
                    ) {

                        /*
                            addAll() bisa gagal total
                            jika satu file tidak ditemukan.

                            Karena itu setiap asset
                            kita cache satu per satu.
                        */

                        await Promise.allSettled(

                            STATIC_ASSETS.map(
                                function (
                                    asset
                                ) {

                                    return cache.add(
                                        asset
                                    );

                                }
                            )

                        );

                    }
                )

        );


        self.skipWaiting();

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

            caches
                .keys()
                .then(
                    function (
                        cacheNames
                    ) {

                        return Promise.all(

                            cacheNames
                                .filter(
                                    function (
                                        cacheName
                                    ) {

                                        return (
                                            cacheName
                                            !== CACHE_NAME
                                        );

                                    }
                                )
                                .map(
                                    function (
                                        cacheName
                                    ) {

                                        return caches.delete(
                                            cacheName
                                        );

                                    }
                                )

                        );

                    }
                )

        );


        self.clients.claim();

    }
);


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


        // Hanya tangani resource
        // dari domain aplikasi sendiri.

        if (
            url.origin
            !== self.location.origin
        ) {

            return;

        }


        // ====================================================
        // NEVER CACHE API
        // ====================================================

        if (
            url.pathname.startsWith(
                "/api/"
            )
        ) {

            return;

        }


        // ====================================================
        // NEVER CACHE DYNAMIC ORDER / DRIVER PAGES
        // ====================================================

        if (
            url.pathname.startsWith(
                "/order/"
            )
            ||
            url.pathname.startsWith(
                "/driver"
            )
        ) {

            return;

        }


        // ====================================================
        // STATIC ASSETS
        // NETWORK FIRST
        // ====================================================

        if (
            url.pathname.startsWith(
                "/static/"
            )
        ) {

            event.respondWith(

                fetch(
                    request
                )
                .then(
                    function (
                        response
                    ) {

                        if (
                            !response
                            ||
                            response.status
                                !== 200
                        ) {

                            return response;

                        }


                        const copy =
                            response.clone();


                        caches
                            .open(
                                CACHE_NAME
                            )
                            .then(
                                function (
                                    cache
                                ) {

                                    cache.put(
                                        request,
                                        copy
                                    );

                                }
                            );


                        return response;

                    }
                )
                .catch(
                    function () {

                        return caches.match(
                            request
                        );

                    }
                )

            );

        }

    }
);