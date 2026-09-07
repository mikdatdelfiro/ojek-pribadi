"use strict";


// ============================================================
// OJEK PRIBADI
// DESTINATION MAP
// ISOLATED SAFE SCRIPT
// ============================================================

(function () {

    const button =
        document.getElementById(
            "destinationMapButton"
        );


    const status =
        document.getElementById(
            "destinationMapStatus"
        );


    const modal =
        document.getElementById(
            "destinationMapModal"
        );


    const closeButton =
        document.getElementById(
            "destinationMapClose"
        );


    const confirmButton =
        document.getElementById(
            "destinationMapConfirm"
        );


    const canvas =
        document.getElementById(
            "destinationMapCanvas"
        );


    const message =
        document.getElementById(
            "destinationMapMessage"
        );


    const destinationInput =
        document.getElementById(
            "destination"
        );


    const detail =
        document.getElementById(
            "destinationAddressDetail"
        );


    const addressValue =
        document.getElementById(
            "destinationAddressValue"
        );


    const coordinatesValue =
        document.getElementById(
            "destinationAddressCoordinates"
        );


    const googleMapsLink =
        document.getElementById(
            "destinationGoogleMapsLink"
        );


    // ========================================================
    // SAFETY
    // ========================================================

    if (
        !button
        ||
        !modal
        ||
        !canvas
        ||
        !confirmButton
        ||
        !destinationInput
    ) {

        console.warn(
            "[DESTINATION MAP] Elemen HTML belum lengkap."
        );


        return;

    }


    window.OjekDestination =
        window.OjekDestination
        ||
        {
            coordinates:
                null,

            address:
                ""
        };


    let map =
        null;


    let marker =
        null;


    let draftCoordinates =
        null;


    let draftAddress =
        "";


    // ========================================================
    // MESSAGE
    // ========================================================

    function setMessage(
        value
    ) {

        if (message) {

            message.textContent =
                value;

        }

    }


    // ========================================================
    // STATUS
    // ========================================================

    function setStatus(
        value,
        selected = false
    ) {

        if (status) {

            status.textContent =
                value;

        }


        button.classList.toggle(
            "is-selected",
            Boolean(
                selected
            )
        );

    }


    // ========================================================
    // ADDRESS DETAIL
    // ========================================================

    function renderAddress(
        address,
        latitude,
        longitude
    ) {

        const lat =
            Number(
                latitude
            );


        const lon =
            Number(
                longitude
            );


        if (
            !Number.isFinite(
                lat
            )
            ||
            !Number.isFinite(
                lon
            )
        ) {

            return;

        }


        const cleanAddress =
            String(
                address
                ||
                "Titik tujuan yang dipilih"
            ).trim();


        if (addressValue) {

            addressValue.textContent =
                cleanAddress;

        }


        if (coordinatesValue) {

            coordinatesValue.textContent =
                (
                    `${lat.toFixed(6)}, `
                    +
                    `${lon.toFixed(6)}`
                );

        }


        if (googleMapsLink) {

            googleMapsLink.href =
                (
                    "https://www.google.com/maps/search/"
                    +
                    "?api=1&query="
                    +
                    encodeURIComponent(
                        `${lat},${lon}`
                    )
                );

        }


        if (detail) {

            detail.hidden =
                false;

        }

    }


    // ========================================================
    // REVERSE GEOCODE
    // ========================================================

    async function reverseGeocode(
        latitude,
        longitude
    ) {

        try {

            const response =
                await fetch(
                    "/api/reverse-geocode",
                    {

                        method:
                            "POST",

                        cache:
                            "no-store",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                {

                                    lat:
                                        latitude,

                                    lon:
                                        longitude

                                }
                            )

                    }
                );


            const data =
                await response.json();


            if (
                response.ok
                &&
                data
                &&
                data.success === true
                &&
                data.location
            ) {

                return String(
                    data.location.display_name
                    || ""
                ).trim();

            }

        }

        catch (error) {

            console.warn(
                "[DESTINATION MAP] Reverse geocode gagal:",
                error
            );

        }


        return "";

    }


    // ========================================================
    // FORWARD GEOCODE
    // ========================================================

    async function forwardGeocode(
        query
    ) {

        query =
            String(
                query
                || ""
            ).trim();


        if (
            query.length
            <
            3
        ) {

            return null;

        }


        try {

            const response =
                await fetch(
                    "/api/geocode-location",
                    {

                        method:
                            "POST",

                        cache:
                            "no-store",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"

                        },

                        body:
                            JSON.stringify(
                                {

                                    query:
                                        query

                                }
                            )

                    }
                );


            const data =
                await response.json();


            if (
                !response.ok
                ||
                !data
                ||
                data.success !== true
                ||
                !data.location
            ) {

                return null;

            }


            const lat =
                Number(
                    data.location.lat
                );


            const lon =
                Number(
                    data.location.lon
                );


            if (
                !Number.isFinite(
                    lat
                )
                ||
                !Number.isFinite(
                    lon
                )
            ) {

                return null;

            }


            return {

                lat:
                    lat,

                lon:
                    lon,

                display_name:
                    String(
                        data.location.display_name
                        ||
                        query
                    ).trim()

            };

        }

        catch (error) {

            console.warn(
                "[DESTINATION MAP] Forward geocode gagal:",
                error
            );


            return null;

        }

    }


    // ========================================================
    // CREATE MAP
    // ========================================================

    function initializeMap() {

        if (map) {

            return true;

        }


        if (
            !window.L
            ||
            typeof window.L.map
            !== "function"
        ) {

            setMessage(
                (
                    "Peta gagal dimuat. "
                    +
                    "Periksa koneksi internet."
                )
            );


            return false;

        }


        map =
            window.L.map(
                canvas
            )
            .setView(
                [
                    -4.10,
                    104.65
                ],
                11
            );


        window.L
            .tileLayer(
                "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                {

                    maxZoom:
                        19,

                    attribution:
                        "&copy; OpenStreetMap"

                }
            )
            .addTo(
                map
            );


        // ====================================================
        // CLICK MAP
        // ====================================================

        map.on(
            "click",
            async function (
                event
            ) {

                if (
                    !event
                    ||
                    !event.latlng
                ) {

                    return;

                }


                const latitude =
                    event.latlng.lat;


                const longitude =
                    event.latlng.lng;


                setDraftPoint(
                    latitude,
                    longitude,
                    false
                );


                setMessage(
                    "Mencari detail alamat..."
                );


                draftAddress =
                    await reverseGeocode(
                        latitude,
                        longitude
                    );


                renderAddress(
                    draftAddress
                    ||
                    "Titik tujuan yang dipilih",
                    latitude,
                    longitude
                );


                setMessage(
                    (
                        "Periksa alamat lalu tekan "
                        +
                        "“Gunakan Titik Ini”."
                    )
                );

            }
        );


        return true;

    }


    // ========================================================
    // MARKER
    // ========================================================

    function setDraftPoint(
        latitude,
        longitude,
        moveMap
    ) {

        const lat =
            Number(
                latitude
            );


        const lon =
            Number(
                longitude
            );


        if (
            !Number.isFinite(
                lat
            )
            ||
            !Number.isFinite(
                lon
            )
        ) {

            return;

        }


        draftCoordinates = {

            lat:
                lat,

            lon:
                lon

        };


        if (marker) {

            marker.setLatLng(
                [
                    lat,
                    lon
                ]
            );

        }

        else {

            marker =
                window.L
                    .marker(
                        [
                            lat,
                            lon
                        ]
                    )
                    .addTo(
                        map
                    );

        }


        if (moveMap) {

            map.setView(
                [
                    lat,
                    lon
                ],
                17
            );

        }


        confirmButton.disabled =
            false;

    }


    // ========================================================
    // OPEN
    // ========================================================

    function openMap() {

        modal.classList.add(
            "is-open"
        );


        modal.setAttribute(
            "aria-hidden",
            "false"
        );


        document.body.classList.add(
            "no-scroll"
        );


        window.setTimeout(
            async function () {

                if (!initializeMap()) {

                    return;

                }


                map.invalidateSize();


                const query =
                    destinationInput
                        .value
                        .trim();


                // ============================================
                // EXISTING SELECTED LOCATION
                // ============================================

                if (
                    window.OjekDestination.coordinates
                ) {

                    const saved =
                        window.OjekDestination
                            .coordinates;


                    setDraftPoint(
                        saved.lat,
                        saved.lon,
                        true
                    );


                    draftAddress =
                        window.OjekDestination.address
                        ||
                        await reverseGeocode(
                            saved.lat,
                            saved.lon
                        );


                    renderAddress(
                        draftAddress
                        ||
                        query,
                        saved.lat,
                        saved.lon
                    );


                    return;

                }


                // ============================================
                // SEARCH TYPED DESTINATION
                // ============================================

                if (
                    query.length
                    >= 3
                ) {

                    setMessage(
                        "Mencari alamat tujuan..."
                    );


                    const found =
                        await forwardGeocode(
                            query
                        );


                    if (found) {

                        draftAddress =
                            found.display_name;


                        setDraftPoint(
                            found.lat,
                            found.lon,
                            true
                        );


                        renderAddress(
                            found.display_name,
                            found.lat,
                            found.lon
                        );


                        setMessage(
                            (
                                "Peta diarahkan ke alamat yang ditemukan. "
                                +
                                "Klik lokasi lain jika titik belum tepat."
                            )
                        );


                        return;

                    }


                    setMessage(
                        (
                            "Alamat belum ditemukan otomatis. "
                            +
                            "Silakan klik titik tujuan pada peta."
                        )
                    );

                }


                // ============================================
                // CURRENT CUSTOMER LOCATION FALLBACK
                // ============================================

                if (
                    navigator.geolocation
                ) {

                    navigator.geolocation
                        .getCurrentPosition(
                            function (
                                position
                            ) {

                                if (!map) {

                                    return;

                                }


                                map.setView(
                                    [
                                        position.coords.latitude,
                                        position.coords.longitude
                                    ],
                                    14
                                );

                            },

                            function () {

                                // Peta menggunakan posisi default.

                            },

                            {

                                enableHighAccuracy:
                                    true,

                                timeout:
                                    7000,

                                maximumAge:
                                    60000

                            }
                        );

                }

            },
            80
        );

    }


    // ========================================================
    // CLOSE
    // ========================================================

    function closeMap() {

        modal.classList.remove(
            "is-open"
        );


        modal.setAttribute(
            "aria-hidden",
            "true"
        );


        document.body.classList.remove(
            "no-scroll"
        );

    }


    // ========================================================
    // BUTTON OPEN
    // ========================================================

    button.addEventListener(
        "click",
        function (
            event
        ) {

            event.preventDefault();


            openMap();

        }
    );


    // ========================================================
    // CLOSE BUTTON
    // ========================================================

    if (closeButton) {

        closeButton.addEventListener(
            "click",
            closeMap
        );

    }


    // ========================================================
    // BACKDROP
    // ========================================================

    modal.addEventListener(
        "click",
        function (
            event
        ) {

            if (
                event.target
                &&
                event.target.hasAttribute(
                    "data-destination-map-close"
                )
            ) {

                closeMap();

            }

        }
    );


    // ========================================================
    // CONFIRM
    // ========================================================

    confirmButton.addEventListener(
        "click",
        async function () {

            if (!draftCoordinates) {

                setMessage(
                    "Pilih titik tujuan terlebih dahulu."
                );


                return;

            }


            confirmButton.disabled =
                true;


            if (!draftAddress) {

                setMessage(
                    "Membaca detail alamat..."
                );


                draftAddress =
                    await reverseGeocode(
                        draftCoordinates.lat,
                        draftCoordinates.lon
                    );

            }


            window.OjekDestination.coordinates = {

                lat:
                    draftCoordinates.lat,

                lon:
                    draftCoordinates.lon

            };


            window.OjekDestination.address =
                draftAddress;


            destinationInput.value =
                (
                    draftAddress
                    ||
                    destinationInput.value.trim()
                    ||
                    (
                        "Titik tujuan "
                        +
                        `(${draftCoordinates.lat.toFixed(5)}, `
                        +
                        `${draftCoordinates.lon.toFixed(5)})`
                    )
                );


            setStatus(
                "Titik tujuan berhasil dipilih",
                true
            );


            // ================================================
            // INVALIDATE OLD FARE
            // ================================================

            try {

                if (
                    typeof currentRoute
                    !== "undefined"
                ) {

                    currentRoute =
                        null;

                }

            }

            catch (error) {

                console.warn(
                    "[DESTINATION MAP]",
                    error
                );

            }


            const fareResult =
                document.getElementById(
                    "fareResult"
                );


            if (fareResult) {

                fareResult.classList.remove(
                    "show"
                );

            }


            closeMap();


            confirmButton.disabled =
                false;

        }
    );


    // ========================================================
    // ESCAPE
    // ========================================================

    document.addEventListener(
        "keydown",
        function (
            event
        ) {

            if (
                event.key
                === "Escape"
                &&
                modal.classList.contains(
                    "is-open"
                )
            ) {

                closeMap();

            }

        }
    );


    console.log(
        "[DESTINATION MAP] Aktif."
    );

})();