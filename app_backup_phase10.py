# ============================================================
# OJEK PRIBADI
# Clean Backend - Phase 10
# Phase 7.5 + 8A + 8B + 8C + 8D + 9 + 10
# ============================================================

from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote

import math
import os
import re
import secrets
import sqlite3
import threading
import time

import requests
from dotenv import load_dotenv

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from werkzeug.utils import secure_filename


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.abspath(
    os.path.dirname(__file__)
)

INSTANCE_DIR = os.path.join(
    BASE_DIR,
    "instance"
)

DATABASE_PATH = os.path.join(
    INSTANCE_DIR,
    "ojek.db"
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

DRIVER_UPLOAD_DIR = os.path.join(
    BASE_DIR,
    "static",
    "uploads",
    "driver"
)

ALLOWED_DRIVER_PHOTO_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv(
    ENV_PATH
)


# ============================================================
# DRIVER + SECURITY CONFIG
# ============================================================

DRIVER_USERNAME = os.getenv(
    "DRIVER_USERNAME",
    "admin"
).strip()

DRIVER_PASSWORD = os.getenv(
    "DRIVER_PASSWORD",
    ""
)

DRIVER_WHATSAPP = os.getenv(
    "DRIVER_WHATSAPP",
    ""
).strip()

DRIVER_SESSION_MINUTES = int(
    os.getenv(
        "DRIVER_SESSION_MINUTES",
        "60"
    )
)

LOGIN_MAX_ATTEMPTS = int(
    os.getenv(
        "LOGIN_MAX_ATTEMPTS",
        "5"
    )
)

LOGIN_BLOCK_MINUTES = int(
    os.getenv(
        "LOGIN_BLOCK_MINUTES",
        "5"
    )
)

COOKIE_SECURE = (
    os.getenv(
        "COOKIE_SECURE",
        "false"
    )
    .strip()
    .lower()
    == "true"
)


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.getenv(
        "SECRET_KEY",
        "development-only-secret-key"
    ),

    SESSION_COOKIE_HTTPONLY=True,

    SESSION_COOKIE_SAMESITE="Lax",

    SESSION_COOKIE_SECURE=COOKIE_SECURE,

    PERMANENT_SESSION_LIFETIME=timedelta(
        minutes=DRIVER_SESSION_MINUTES
    ),

    SESSION_REFRESH_EACH_REQUEST=True,

    MAX_CONTENT_LENGTH=
        5 * 1024 * 1024,

    JSON_SORT_KEYS=False,
)


# ============================================================
# STARTUP DIAGNOSTICS
# ============================================================

print(
    "[CONFIG] WhatsApp driver:",
    (
        "OK"
        if DRIVER_WHATSAPP
        else "BELUM DIATUR"
    )
)

print(
    "[CONFIG] Password driver:",
    (
        "OK"
        if DRIVER_PASSWORD
        else "BELUM DIATUR"
    )
)


# ============================================================
# FARE CONFIGURATION
# ============================================================

BASE_FARE = 7_000

INCLUDED_DISTANCE_KM = 2

RATE_PER_KM = 2_500

FARE_ROUNDING = 1_000


# ============================================================
# MAP SERVICES
# ============================================================

NOMINATIM_SEARCH_URL = (
    "https://nominatim.openstreetmap.org/search"
)

NOMINATIM_REVERSE_URL = (
    "https://nominatim.openstreetmap.org/reverse"
)

OSRM_URL = (
    "https://router.project-osrm.org"
)


http = requests.Session()

http.headers.update(
    {
        "User-Agent":
            "OjekPribadi/1.0 (local-development)",

        "Accept":
            "application/json",
    }
)


# ============================================================
# RUNTIME STATE
# ============================================================

geocode_cache = {}

_nominatim_lock = (
    threading.Lock()
)

_last_nominatim_request = (
    0.0
)


login_attempts = {}

login_attempts_lock = (
    threading.Lock()
)


# ============================================================
# ORDER STATUS
# ============================================================

STATUS_WAITING = (
    "MENUNGGU"
)

STATUS_ACCEPTED = (
    "DITERIMA"
)

STATUS_TO_PICKUP = (
    "MENUJU_JEMPUT"
)

STATUS_PICKED_UP = (
    "DIJEMPUT"
)

STATUS_COMPLETED = (
    "SELESAI"
)

STATUS_REJECTED = (
    "DITOLAK"
)


ACTIVE_STATUSES = (
    STATUS_ACCEPTED,
    STATUS_TO_PICKUP,
    STATUS_PICKED_UP,
)


CUSTOMER_CONTACT_STATUSES = (
    STATUS_ACCEPTED,
    STATUS_TO_PICKUP,
    STATUS_PICKED_UP,
)


DRIVER_PROFILE_VISIBLE_STATUSES = (
    STATUS_ACCEPTED,
    STATUS_TO_PICKUP,
    STATUS_PICKED_UP,
    STATUS_COMPLETED,
)


ALLOWED_TRANSITIONS = {

    STATUS_WAITING: {
        STATUS_ACCEPTED,
        STATUS_REJECTED,
    },

    STATUS_ACCEPTED: {
        STATUS_TO_PICKUP,
    },

    STATUS_TO_PICKUP: {
        STATUS_PICKED_UP,
    },

    STATUS_PICKED_UP: {
        STATUS_COMPLETED,
    },
}


STATUS_MESSAGES = {

    STATUS_ACCEPTED:
        "Pesanan berhasil diterima.",

    STATUS_TO_PICKUP:
        "Anda sedang menuju pelanggan.",

    STATUS_PICKED_UP:
        "Perjalanan dimulai.",

    STATUS_COMPLETED:
        "Perjalanan selesai.",

    STATUS_REJECTED:
        "Pesanan ditolak.",
}


# ============================================================
# SERVICE STATUS
# ============================================================

SERVICE_SETTING_KEY = (
    "service_open"
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def current_timestamp():

    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def clean_whatsapp(
    number
):

    if number is None:

        return ""


    return re.sub(
        r"[^0-9+]",
        "",
        str(number).strip()
    )


def normalize_whatsapp_number(
    number
):

    number = re.sub(
        r"\D",
        "",
        str(
            number or ""
        ).strip()
    )


    if not number:

        return ""


    if number.startswith(
        "08"
    ):

        return (
            "62"
            + number[1:]
        )


    if number.startswith(
        "8"
    ):

        return (
            "62"
            + number
        )


    return number


def generate_order_code():

    return (
        f"OJ-"
        f"{secrets.randbelow(900_000) + 100_000}"
    )


def create_unique_order_code(
    connection
):

    for _ in range(20):

        order_code = (
            generate_order_code()
        )


        existing = (
            connection.execute(
                """
                SELECT id

                FROM orders

                WHERE order_code = ?
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not existing:

            return order_code


    raise RuntimeError(
        "Gagal membuat kode order unik."
    )


# ============================================================
# DATABASE
# ============================================================

def get_db():

    connection = sqlite3.connect(
        DATABASE_PATH
    )


    connection.row_factory = (
        sqlite3.Row
    )


    return connection


def init_database():

    os.makedirs(
        INSTANCE_DIR,
        exist_ok=True
    )


    os.makedirs(
        DRIVER_UPLOAD_DIR,
        exist_ok=True
    )


    connection = get_db()


    try:

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                order_code TEXT UNIQUE NOT NULL,

                customer_name TEXT NOT NULL,

                whatsapp TEXT NOT NULL,

                pickup TEXT NOT NULL,

                destination TEXT NOT NULL,

                note TEXT,

                distance_km REAL NOT NULL,

                duration_minutes INTEGER NOT NULL,

                fare INTEGER NOT NULL,

                status TEXT NOT NULL DEFAULT 'MENUNGGU',

                created_at TEXT NOT NULL,

                pickup_lat REAL,

                pickup_lon REAL,

                destination_lat REAL,

                destination_lon REAL
            )
            """
        )


        # ----------------------------------------------------
        # SETTINGS
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (

                setting_key TEXT PRIMARY KEY,

                setting_value TEXT NOT NULL,

                updated_at TEXT NOT NULL
            )
            """
        )


        # ----------------------------------------------------
        # DRIVER PROFILE
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS driver_profile (

                id INTEGER PRIMARY KEY,

                driver_name TEXT NOT NULL,

                short_bio TEXT,

                vehicle_name TEXT NOT NULL,

                vehicle_color TEXT,

                vehicle_plate TEXT NOT NULL,

                photo_filename TEXT,

                updated_at TEXT NOT NULL
            )
            """
        )


        # ----------------------------------------------------
        # MIGRATION OLD ORDERS
        # ----------------------------------------------------

        existing_columns = {

            row["name"]

            for row in connection.execute(
                "PRAGMA table_info(orders)"
            ).fetchall()
        }


        required_columns = {

            "pickup_lat":
                "REAL",

            "pickup_lon":
                "REAL",

            "destination_lat":
                "REAL",

            "destination_lon":
                "REAL",
        }


        for (
            column_name,
            column_type
        ) in required_columns.items():

            if (
                column_name
                not in existing_columns
            ):

                connection.execute(
                    f"""
                    ALTER TABLE orders

                    ADD COLUMN
                    {column_name}
                    {column_type}
                    """
                )


        # ----------------------------------------------------
        # DEFAULT SERVICE STATUS
        # ----------------------------------------------------

        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (

                setting_key,

                setting_value,

                updated_at
            )

            VALUES (?, ?, ?)
            """,
            (
                SERVICE_SETTING_KEY,

                "1",

                current_timestamp(),
            )
        )


        # ----------------------------------------------------
        # DEFAULT DRIVER PROFILE
        # ----------------------------------------------------

        connection.execute(
            """
            INSERT OR IGNORE INTO driver_profile (

                id,

                driver_name,

                short_bio,

                vehicle_name,

                vehicle_color,

                vehicle_plate,

                photo_filename,

                updated_at
            )

            VALUES (
                1,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                "Pengemudi",

                "Pengemudi Ojek Pribadi",

                "Motor",

                "",

                "-",

                None,

                current_timestamp(),
            )
        )


        # ----------------------------------------------------
        # INDEXES
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_status

            ON orders(status)
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_created_at

            ON orders(created_at)
            """
        )


        connection.commit()


    finally:

        connection.close()


# ============================================================
# SERVICE STATUS HELPERS
# ============================================================

def get_service_open(
    connection=None
):

    own_connection = (
        connection is None
    )


    if own_connection:

        connection = (
            get_db()
        )


    try:

        row = (
            connection.execute(
                """
                SELECT setting_value

                FROM app_settings

                WHERE setting_key = ?
                """,
                (
                    SERVICE_SETTING_KEY,
                )
            )
            .fetchone()
        )


        if not row:

            return True


        return (
            row[
                "setting_value"
            ]
            == "1"
        )


    finally:

        if own_connection:

            connection.close()


def set_service_open(
    is_open
):

    value = (
        "1"
        if is_open
        else "0"
    )


    connection = get_db()


    try:

        connection.execute(
            """
            INSERT INTO app_settings (

                setting_key,

                setting_value,

                updated_at
            )

            VALUES (?, ?, ?)

            ON CONFLICT(setting_key)

            DO UPDATE SET

                setting_value =
                    excluded.setting_value,

                updated_at =
                    excluded.updated_at
            """,
            (
                SERVICE_SETTING_KEY,

                value,

                current_timestamp(),
            )
        )


        connection.commit()


    finally:

        connection.close()


# ============================================================
# DRIVER PROFILE HELPERS
# ============================================================

def get_driver_profile(
    connection=None
):

    own_connection = (
        connection is None
    )


    if own_connection:

        connection = (
            get_db()
        )


    try:

        return (
            connection.execute(
                """
                SELECT *

                FROM driver_profile

                WHERE id = 1
                """
            )
            .fetchone()
        )


    finally:

        if own_connection:

            connection.close()


def allowed_driver_photo(
    filename
):

    if (
        not filename
        or "." not in filename
    ):

        return False


    extension = (
        filename
        .rsplit(
            ".",
            1
        )[1]
        .lower()
    )


    return (
        extension
        in ALLOWED_DRIVER_PHOTO_EXTENSIONS
    )


def driver_photo_url(
    filename
):

    if not filename:

        return None


    safe_filename = (
        os.path.basename(
            filename
        )
    )


    return url_for(
        "static",

        filename=(
            "uploads/driver/"
            + safe_filename
        )
    )


def driver_profile_payload(
    profile
):

    if not profile:

        return None


    return {

        "driver_name":
            profile[
                "driver_name"
            ],

        "short_bio":
            profile[
                "short_bio"
            ],

        "vehicle_name":
            profile[
                "vehicle_name"
            ],

        "vehicle_color":
            profile[
                "vehicle_color"
            ],

        "vehicle_plate":
            profile[
                "vehicle_plate"
            ],

        "photo_url":
            driver_photo_url(
                profile[
                    "photo_filename"
                ]
            ),
    }


# ============================================================
# LOGIN SECURITY
# ============================================================

def get_client_ip():

    return (
        request.remote_addr
        or "unknown"
    )


def get_login_state(
    client_ip
):

    with login_attempts_lock:

        return login_attempts.get(
            client_ip,
            {
                "attempts": 0,

                "blocked_until": 0,
            }
        ).copy()


def clear_login_attempts(
    client_ip
):

    with login_attempts_lock:

        login_attempts.pop(
            client_ip,
            None
        )


def login_is_blocked(
    client_ip
):

    state = (
        get_login_state(
            client_ip
        )
    )


    blocked_until = (
        state.get(
            "blocked_until",
            0
        )
    )


    now = (
        time.time()
    )


    if now < blocked_until:

        return (
            True,

            max(
                1,
                int(
                    blocked_until
                    - now
                )
            )
        )


    if blocked_until:

        clear_login_attempts(
            client_ip
        )


    return (
        False,
        0
    )


def register_failed_login(
    client_ip
):

    with login_attempts_lock:

        state = login_attempts.get(
            client_ip,
            {
                "attempts": 0,

                "blocked_until": 0,
            }
        )


        attempts = (
            state.get(
                "attempts",
                0
            )
            + 1
        )


        blocked_until = (
            0
        )


        if (
            attempts
            >= LOGIN_MAX_ATTEMPTS
        ):

            blocked_until = (
                time.time()
                +
                (
                    LOGIN_BLOCK_MINUTES
                    * 60
                )
            )


        login_attempts[
            client_ip
        ] = {

            "attempts":
                attempts,

            "blocked_until":
                blocked_until,
        }


        return (
            attempts,
            blocked_until
        )


# ============================================================
# WHATSAPP DRIVER -> CUSTOMER
# ============================================================

def build_whatsapp_link(
    number,
    customer_name,
    order_code,
    status=None
):

    whatsapp_number = (
        normalize_whatsapp_number(
            number
        )
    )


    if (
        len(
            whatsapp_number
        )
        < 10
    ):

        return None


    if (
        status
        == STATUS_ACCEPTED
    ):

        message = (
            f"Halo {customer_name}, "
            f"pesanan {order_code} "
            f"sudah saya terima.\n\n"
            f"Saya akan segera menuju "
            f"lokasi penjemputan."
        )


    elif (
        status
        == STATUS_TO_PICKUP
    ):

        message = (
            f"Halo {customer_name}, "
            f"saya sedang menuju "
            f"lokasi penjemputan untuk "
            f"pesanan {order_code}."
        )


    elif (
        status
        == STATUS_PICKED_UP
    ):

        message = (
            f"Halo {customer_name}, "
            f"ini terkait perjalanan "
            f"{order_code}."
        )


    else:

        message = (
            f"Halo {customer_name}, "
            f"saya dari Ojek Pribadi.\n\n"
            f"Saya menghubungi Anda "
            f"terkait pesanan "
            f"{order_code}."
        )


    return (
        f"https://wa.me/"
        f"{whatsapp_number}"
        f"?text={quote(message)}"
    )


@app.template_global()
def whatsapp_link(
    number,
    customer_name,
    order_code,
    status=None
):

    return build_whatsapp_link(
        number,
        customer_name,
        order_code,
        status
    )


# ============================================================
# WHATSAPP CUSTOMER -> DRIVER
# ============================================================

def build_driver_whatsapp_link(
    order_code,
    customer_name
):

    driver_number = (
        normalize_whatsapp_number(
            DRIVER_WHATSAPP
        )
    )


    if (
        len(
            driver_number
        )
        < 10
    ):

        print(
            "[WHATSAPP] "
            "Nomor driver belum valid."
        )

        return None


    message = (
        f"Halo, saya {customer_name}.\n\n"
        f"Saya pelanggan untuk pesanan "
        f"{order_code}.\n"
        f"Saya ingin menghubungi pengemudi "
        f"terkait perjalanan saya."
    )


    return (
        f"https://wa.me/"
        f"{driver_number}"
        f"?text={quote(message)}"
    )


# ============================================================
# NOMINATIM RATE LIMIT
# ============================================================

def wait_for_nominatim():

    global _last_nominatim_request


    with _nominatim_lock:

        now = (
            time.monotonic()
        )


        elapsed = (
            now
            - _last_nominatim_request
        )


        minimum_interval = (
            1.1
        )


        if (
            elapsed
            < minimum_interval
        ):

            time.sleep(
                minimum_interval
                - elapsed
            )


        _last_nominatim_request = (
            time.monotonic()
        )


# ============================================================
# GEOCODING
# ============================================================

def geocode_location(
    location_text
):

    location_text = (
        location_text.strip()
    )


    cache_key = (
        location_text.lower()
    )


    if (
        cache_key
        in geocode_cache
    ):

        return (
            geocode_cache[
                cache_key
            ]
        )


    wait_for_nominatim()


    response = http.get(
        NOMINATIM_SEARCH_URL,

        params={
            "q":
                location_text,

            "format":
                "jsonv2",

            "limit":
                1,

            "countrycodes":
                "id",
        },

        timeout=20
    )


    response.raise_for_status()


    data = (
        response.json()
    )


    if not data:

        return None


    result = {

        "lat":
            float(
                data[0][
                    "lat"
                ]
            ),

        "lon":
            float(
                data[0][
                    "lon"
                ]
            ),

        "display_name":
            data[0][
                "display_name"
            ],
    }


    geocode_cache[
        cache_key
    ] = result


    return result


def reverse_geocode(
    latitude,
    longitude
):

    wait_for_nominatim()


    response = http.get(
        NOMINATIM_REVERSE_URL,

        params={
            "lat":
                latitude,

            "lon":
                longitude,

            "format":
                "jsonv2",

            "zoom":
                18,

            "addressdetails":
                1,
        },

        timeout=20
    )


    response.raise_for_status()


    data = (
        response.json()
    )


    return {

        "lat":
            float(
                latitude
            ),

        "lon":
            float(
                longitude
            ),

        "display_name":
            data.get(
                "display_name",
                "Lokasi saya"
            ),
    }


def resolve_location(
    data,
    prefix,
    location_text
):

    latitude = data.get(
        f"{prefix}_lat"
    )


    longitude = data.get(
        f"{prefix}_lon"
    )


    if (
        latitude is not None
        and
        longitude is not None
    ):

        try:

            latitude = float(
                latitude
            )


            longitude = float(
                longitude
            )


            if not (
                -90
                <= latitude
                <= 90
            ):

                raise ValueError


            if not (
                -180
                <= longitude
                <= 180
            ):

                raise ValueError


            return {

                "lat":
                    latitude,

                "lon":
                    longitude,

                "display_name":
                    location_text,
            }


        except (
            TypeError,
            ValueError
        ):

            pass


    return geocode_location(
        location_text
    )


# ============================================================
# ROUTING
# ============================================================

def calculate_route(
    pickup,
    destination
):

    coordinates = (
        f'{pickup["lon"]},'
        f'{pickup["lat"]};'
        f'{destination["lon"]},'
        f'{destination["lat"]}'
    )


    response = http.get(
        (
            f"{OSRM_URL}"
            f"/route/v1/driving/"
            f"{coordinates}"
        ),

        params={
            "overview":
                "false",

            "steps":
                "false",
        },

        timeout=20
    )


    response.raise_for_status()


    data = (
        response.json()
    )


    if (
        data.get(
            "code"
        )
        != "Ok"
    ):

        return None


    routes = (
        data.get(
            "routes",
            []
        )
    )


    if not routes:

        return None


    route = (
        routes[0]
    )


    return {

        "distance_km":
            route[
                "distance"
            ]
            / 1000,

        "duration_minutes":
            route[
                "duration"
            ]
            / 60,
    }


# ============================================================
# FARE
# ============================================================

def calculate_fare(
    distance_km
):

    if (
        distance_km
        <= INCLUDED_DISTANCE_KM
    ):

        fare = (
            BASE_FARE
        )


    else:

        extra_distance = (
            distance_km
            - INCLUDED_DISTANCE_KM
        )


        fare = (
            BASE_FARE
            +
            (
                extra_distance
                * RATE_PER_KM
            )
        )


    return int(
        math.ceil(
            fare
            / FARE_ROUNDING
        )
        * FARE_ROUNDING
    )


def build_trip(
    data,
    pickup_text,
    destination_text
):

    pickup = (
        resolve_location(
            data,
            "pickup",
            pickup_text
        )
    )


    if not pickup:

        raise ValueError(
            "Lokasi jemput tidak ditemukan."
        )


    destination = (
        resolve_location(
            data,
            "destination",
            destination_text
        )
    )


    if not destination:

        raise ValueError(
            "Lokasi tujuan tidak ditemukan."
        )


    route = (
        calculate_route(
            pickup,
            destination
        )
    )


    if not route:

        raise ValueError(
            "Rute perjalanan tidak ditemukan."
        )


    return {

        "pickup":
            pickup,

        "destination":
            destination,

        "distance_km":
            round(
                route[
                    "distance_km"
                ],
                1
            ),

        "duration_minutes":
            max(
                1,
                round(
                    route[
                        "duration_minutes"
                    ]
                )
            ),

        "fare":
            calculate_fare(
                route[
                    "distance_km"
                ]
            ),
    }


# ============================================================
# DRIVER AUTHENTICATION
# ============================================================

def driver_is_authenticated():

    return (
        session.get(
            "driver_authenticated"
        )
        is True
    )


def driver_session_expired():

    last_activity = (
        session.get(
            "driver_last_activity"
        )
    )


    if (
        last_activity
        is None
    ):

        return False


    try:

        last_activity = (
            float(
                last_activity
            )
        )


    except (
        TypeError,
        ValueError
    ):

        return True


    idle_seconds = (
        time.time()
        - last_activity
    )


    return (
        idle_seconds
        >
        (
            DRIVER_SESSION_MINUTES
            * 60
        )
    )


def refresh_driver_activity():

    session[
        "driver_last_activity"
    ] = time.time()


def driver_login_required(
    view_function
):

    @wraps(
        view_function
    )
    def wrapped_view(
        *args,
        **kwargs
    ):

        if not driver_is_authenticated():

            return redirect(
                url_for(
                    "driver_login"
                )
            )


        if driver_session_expired():

            session.clear()


            return redirect(
                url_for(
                    "driver_login",
                    expired="1"
                )
            )


        refresh_driver_activity()


        return view_function(
            *args,
            **kwargs
        )


    return wrapped_view


def driver_api_required(
    view_function
):

    @wraps(
        view_function
    )
    def wrapped_view(
        *args,
        **kwargs
    ):

        if not driver_is_authenticated():

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Anda belum login "
                            "sebagai driver."
                        ),

                    "session_expired":
                        False,
                }
            ), 401


        if driver_session_expired():

            session.clear()


            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Session driver telah "
                            "berakhir. Silakan login kembali."
                        ),

                    "session_expired":
                        True,
                }
            ), 401


        refresh_driver_activity()


        return view_function(
            *args,
            **kwargs
        )


    return wrapped_view


# ============================================================
# CUSTOMER PAGE
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html",

        service_open=
            get_service_open()
    )


# ============================================================
# PUBLIC SERVICE STATUS
# ============================================================

@app.route(
    "/api/service-status",
    methods=["GET"]
)
def get_service_status():

    service_open = (
        get_service_open()
    )


    return jsonify(
        {
            "success":
                True,

            "service_open":
                service_open,

            "status":
                (
                    "OPEN"
                    if service_open
                    else "CLOSED"
                ),

            "label":
                (
                    "MENERIMA PESANAN"
                    if service_open
                    else "SEDANG TIDAK MELAYANI"
                ),
        }
    )


# ============================================================
# REVERSE GEOCODE API
# ============================================================

@app.route(
    "/api/reverse-geocode",
    methods=["POST"]
)
def api_reverse_geocode():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    latitude = (
        data.get(
            "lat"
        )
    )


    longitude = (
        data.get(
            "lon"
        )
    )


    if (
        latitude is None
        or
        longitude is None
    ):

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Koordinat tidak tersedia.",
            }
        ), 400


    try:

        latitude = float(
            latitude
        )


        longitude = float(
            longitude
        )


        if not (
            -90
            <= latitude
            <= 90
        ):

            raise ValueError


        if not (
            -180
            <= longitude
            <= 180
        ):

            raise ValueError


        return jsonify(
            {
                "success":
                    True,

                "location":
                    reverse_geocode(
                        latitude,
                        longitude
                    ),
            }
        )


    except requests.RequestException as error:

        print(
            "[REVERSE GEOCODE ERROR]",
            repr(error)
        )


        return jsonify(
            {
                "success":
                    True,

                "location": {

                    "lat":
                        latitude,

                    "lon":
                        longitude,

                    "display_name":
                        (
                            f"Lokasi saya "
                            f"({latitude:.5f}, "
                            f"{longitude:.5f})"
                        ),
                },
            }
        )


    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Koordinat tidak valid.",
            }
        ), 400


# ============================================================
# CHECK FARE API
# ============================================================

@app.route(
    "/api/check-fare",
    methods=["POST"]
)
def check_fare():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    pickup_text = (
        data.get(
            "pickup",
            ""
        )
        .strip()
    )


    destination_text = (
        data.get(
            "destination",
            ""
        )
        .strip()
    )


    if not pickup_text:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Lokasi jemput harus diisi.",
            }
        ), 400


    if not destination_text:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Tujuan harus diisi.",
            }
        ), 400


    try:

        trip = (
            build_trip(
                data,
                pickup_text,
                destination_text
            )
        )


        return jsonify(
            {
                "success":
                    True,

                "pickup": {

                    "name":
                        trip[
                            "pickup"
                        ][
                            "display_name"
                        ],

                    "lat":
                        trip[
                            "pickup"
                        ][
                            "lat"
                        ],

                    "lon":
                        trip[
                            "pickup"
                        ][
                            "lon"
                        ],
                },

                "destination": {

                    "name":
                        trip[
                            "destination"
                        ][
                            "display_name"
                        ],

                    "lat":
                        trip[
                            "destination"
                        ][
                            "lat"
                        ],

                    "lon":
                        trip[
                            "destination"
                        ][
                            "lon"
                        ],
                },

                "distance_km":
                    trip[
                        "distance_km"
                    ],

                "duration_minutes":
                    trip[
                        "duration_minutes"
                    ],

                "fare":
                    trip[
                        "fare"
                    ],
            }
        )


    except ValueError as error:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 400


    except requests.RequestException as error:

        print(
            "[CHECK FARE MAP ERROR]",
            repr(error)
        )


        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Layanan lokasi sedang "
                        "tidak dapat dihubungi."
                    ),
            }
        ), 503


    except Exception as error:

        print(
            "[CHECK FARE ERROR]",
            repr(error)
        )


        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Terjadi kesalahan saat "
                        "menghitung tarif."
                    ),
            }
        ), 500


# ============================================================
# CREATE ORDER
# ============================================================

@app.route(
    "/api/orders",
    methods=["POST"]
)
def create_order():

    if not get_service_open():

        return jsonify(
            {
                "success":
                    False,

                "service_open":
                    False,

                "message":
                    (
                        "Maaf, layanan sedang "
                        "tidak menerima pesanan."
                    ),
            }
        ), 503


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    customer_name = (
        data.get(
            "customer_name",
            ""
        )
        .strip()
    )


    whatsapp = clean_whatsapp(
        data.get(
            "whatsapp",
            ""
        )
    )


    pickup_text = (
        data.get(
            "pickup",
            ""
        )
        .strip()
    )


    destination_text = (
        data.get(
            "destination",
            ""
        )
        .strip()
    )


    note = (
        data.get(
            "note",
            ""
        )
        .strip()
    )


    if (
        len(
            customer_name
        )
        < 2
    ):

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Masukkan nama Anda.",
            }
        ), 400


    if (
        len(
            normalize_whatsapp_number(
                whatsapp
            )
        )
        < 10
    ):

        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Nomor WhatsApp "
                        "tidak valid."
                    ),
            }
        ), 400


    if not pickup_text:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Lokasi jemput belum diisi.",
            }
        ), 400


    if not destination_text:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Tujuan belum diisi.",
            }
        ), 400


    try:

        trip = (
            build_trip(
                data,
                pickup_text,
                destination_text
            )
        )


        connection = (
            get_db()
        )


        try:

            order_code = (
                create_unique_order_code(
                    connection
                )
            )


            connection.execute(
                """
                INSERT INTO orders (

                    order_code,

                    customer_name,

                    whatsapp,

                    pickup,

                    destination,

                    note,

                    distance_km,

                    duration_minutes,

                    fare,

                    status,

                    created_at,

                    pickup_lat,

                    pickup_lon,

                    destination_lat,

                    destination_lon
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
                """,
                (
                    order_code,

                    customer_name,

                    whatsapp,

                    pickup_text,

                    destination_text,

                    note,

                    trip[
                        "distance_km"
                    ],

                    trip[
                        "duration_minutes"
                    ],

                    trip[
                        "fare"
                    ],

                    STATUS_WAITING,

                    current_timestamp(),

                    trip[
                        "pickup"
                    ][
                        "lat"
                    ],

                    trip[
                        "pickup"
                    ][
                        "lon"
                    ],

                    trip[
                        "destination"
                    ][
                        "lat"
                    ],

                    trip[
                        "destination"
                    ][
                        "lon"
                    ],
                )
            )


            connection.commit()


        finally:

            connection.close()


        return jsonify(
            {
                "success":
                    True,

                "order_code":
                    order_code,

                "fare":
                    trip[
                        "fare"
                    ],

                "status":
                    STATUS_WAITING,

                "message":
                    "Pesanan berhasil dibuat.",
            }
        )


    except ValueError as error:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(error),
            }
        ), 400


    except requests.RequestException as error:

        print(
            "[CREATE ORDER MAP ERROR]",
            repr(error)
        )


        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Layanan lokasi sedang "
                        "tidak tersedia."
                    ),
            }
        ), 503


    except Exception as error:

        print(
            "[CREATE ORDER ERROR]",
            repr(error)
        )


        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Pesanan gagal dibuat.",
            }
        ), 500


# ============================================================
# CUSTOMER ORDER STATUS PAGE
# ============================================================

@app.route(
    "/order/<string:order_code>"
)
def customer_order_status(
    order_code
):

    connection = get_db()


    try:

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


    finally:

        connection.close()


    if not order:

        abort(404)


    return render_template(
        "order_status.html",
        order=order
    )


# ============================================================
# CUSTOMER LIVE STATUS API
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/status",
    methods=["GET"]
)
def get_customer_order_status(
    order_code
):

    connection = get_db()


    try:

        order = (
            connection.execute(
                """
                SELECT

                    order_code,

                    customer_name,

                    pickup,

                    destination,

                    note,

                    distance_km,

                    duration_minutes,

                    fare,

                    status,

                    created_at

                FROM orders

                WHERE order_code = ?
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        profile = None


        if (
            order
            and
            order[
                "status"
            ]
            in DRIVER_PROFILE_VISIBLE_STATUSES
        ):

            profile = (
                get_driver_profile(
                    connection
                )
            )


    finally:

        connection.close()


    if not order:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Pesanan tidak ditemukan.",
            }
        ), 404


    return jsonify(
        {
            "success":
                True,

            "order": {

                "order_code":
                    order[
                        "order_code"
                    ],

                "customer_name":
                    order[
                        "customer_name"
                    ],

                "pickup":
                    order[
                        "pickup"
                    ],

                "destination":
                    order[
                        "destination"
                    ],

                "note":
                    order[
                        "note"
                    ],

                "distance_km":
                    order[
                        "distance_km"
                    ],

                "duration_minutes":
                    order[
                        "duration_minutes"
                    ],

                "fare":
                    order[
                        "fare"
                    ],

                "status":
                    order[
                        "status"
                    ],

                "created_at":
                    order[
                        "created_at"
                    ],

                "driver_profile":
                    driver_profile_payload(
                        profile
                    ),
            },
        }
    )


# ============================================================
# CUSTOMER CONTACT DRIVER
# ============================================================

@app.route(
    "/order/<string:order_code>/contact-driver"
)
def customer_contact_driver(
    order_code
):

    connection = get_db()


    try:

        order = (
            connection.execute(
                """
                SELECT

                    order_code,

                    customer_name,

                    status

                FROM orders

                WHERE order_code = ?
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


    finally:

        connection.close()


    if not order:

        abort(404)


    if (
        order[
            "status"
        ]
        not in CUSTOMER_CONTACT_STATUSES
    ):

        return (
            "Pengemudi belum dapat "
            "dihubungi untuk status "
            "perjalanan ini.",
            403
        )


    whatsapp_url = (
        build_driver_whatsapp_link(
            order[
                "order_code"
            ],

            order[
                "customer_name"
            ]
        )
    )


    if not whatsapp_url:

        return (
            "Nomor WhatsApp pengemudi "
            "belum dikonfigurasi.",
            503
        )


    return redirect(
        whatsapp_url
    )


# ============================================================
# DRIVER LOGIN
# ============================================================

@app.route(
    "/driver/login",
    methods=[
        "GET",
        "POST"
    ]
)
def driver_login():

    if driver_is_authenticated():

        if not driver_session_expired():

            return redirect(
                url_for(
                    "driver_dashboard"
                )
            )


        session.clear()


    error = None

    blocked_seconds = 0


    if (
        request.args.get(
            "expired"
        )
        == "1"
    ):

        error = (
            "Session Anda telah berakhir. "
            "Silakan login kembali."
        )


    client_ip = (
        get_client_ip()
    )


    blocked, blocked_seconds = (
        login_is_blocked(
            client_ip
        )
    )


    if (
        request.method
        == "POST"
    ):

        if blocked:

            return render_template(
                "admin/login.html",

                error=(
                    "Terlalu banyak percobaan "
                    "login. Silakan tunggu "
                    "beberapa saat."
                ),

                blocked_seconds=
                    blocked_seconds

            ), 429


        username = (
            request.form
            .get(
                "username",
                ""
            )
            .strip()
        )


        password = (
            request.form.get(
                "password",
                ""
            )
        )


        username_valid = (
            secrets.compare_digest(
                username,
                DRIVER_USERNAME
            )
        )


        password_valid = (
            bool(
                DRIVER_PASSWORD
            )
            and
            secrets.compare_digest(
                password,
                DRIVER_PASSWORD
            )
        )


        if (
            username_valid
            and
            password_valid
        ):

            clear_login_attempts(
                client_ip
            )


            session.clear()


            session.permanent = (
                True
            )


            session[
                "driver_authenticated"
            ] = True


            session[
                "driver_username"
            ] = DRIVER_USERNAME


            refresh_driver_activity()


            return redirect(
                url_for(
                    "driver_dashboard"
                )
            )


        attempts, blocked_until = (
            register_failed_login(
                client_ip
            )
        )


        if blocked_until:

            error = (
                "Terlalu banyak percobaan "
                "login. "
                f"Akses dikunci selama "
                f"{LOGIN_BLOCK_MINUTES} menit."
            )


        else:

            attempts_left = max(
                0,

                LOGIN_MAX_ATTEMPTS
                - attempts
            )


            error = (
                "Username atau password "
                "tidak benar. "
                f"Sisa percobaan: "
                f"{attempts_left}."
            )


    return render_template(
        "admin/login.html",

        error=
            error,

        blocked_seconds=
            blocked_seconds
    )


# ============================================================
# DRIVER LOGOUT
# ============================================================

@app.route(
    "/driver/logout",
    methods=["POST"]
)
@driver_login_required
def driver_logout():

    session.clear()


    return redirect(
        url_for(
            "driver_login"
        )
    )


# ============================================================
# DRIVER PROFILE
# ============================================================

@app.route(
    "/driver/profile",
    methods=[
        "GET",
        "POST"
    ]
)
@driver_login_required
def driver_profile():

    error = None


    if (
        request.method
        == "POST"
    ):

        driver_name = (
            request.form
            .get(
                "driver_name",
                ""
            )
            .strip()
        )


        short_bio = (
            request.form
            .get(
                "short_bio",
                ""
            )
            .strip()
        )


        vehicle_name = (
            request.form
            .get(
                "vehicle_name",
                ""
            )
            .strip()
        )


        vehicle_color = (
            request.form
            .get(
                "vehicle_color",
                ""
            )
            .strip()
        )


        vehicle_plate = (
            request.form
            .get(
                "vehicle_plate",
                ""
            )
            .strip()
            .upper()
        )


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if (
            len(
                driver_name
            )
            < 2
        ):

            error = (
                "Nama driver minimal "
                "2 karakter."
            )


        elif (
            len(
                short_bio
            )
            > 140
        ):

            error = (
                "Bio maksimal "
                "140 karakter."
            )


        elif (
            len(
                vehicle_name
            )
            < 2
        ):

            error = (
                "Nama kendaraan harus diisi."
            )


        elif (
            len(
                vehicle_plate
            )
            < 2
        ):

            error = (
                "Plat nomor harus diisi."
            )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        if not error:

            connection = (
                get_db()
            )


            try:

                old_profile = (
                    get_driver_profile(
                        connection
                    )
                )


                photo_filename = (
                    old_profile[
                        "photo_filename"
                    ]
                    if old_profile
                    else None
                )


                photo = (
                    request.files.get(
                        "driver_photo"
                    )
                )


                if (
                    photo
                    and
                    photo.filename
                ):

                    if not allowed_driver_photo(
                        photo.filename
                    ):

                        error = (
                            "Format foto harus "
                            "JPG, JPEG, PNG, "
                            "atau WEBP."
                        )


                    else:

                        safe_name = (
                            secure_filename(
                                photo.filename
                            )
                        )


                        if (
                            "."
                            not in safe_name
                        ):

                            error = (
                                "Nama file foto "
                                "tidak valid."
                            )


                        else:

                            extension = (
                                safe_name
                                .rsplit(
                                    ".",
                                    1
                                )[1]
                                .lower()
                            )


                            new_filename = (
                                "driver_"
                                + secrets.token_hex(
                                    12
                                )
                                + "."
                                + extension
                            )


                            new_path = (
                                os.path.join(
                                    DRIVER_UPLOAD_DIR,
                                    new_filename
                                )
                            )


                            photo.save(
                                new_path
                            )


                            if (
                                old_profile
                                and
                                old_profile[
                                    "photo_filename"
                                ]
                            ):

                                old_path = (
                                    os.path.join(
                                        DRIVER_UPLOAD_DIR,

                                        os.path.basename(
                                            old_profile[
                                                "photo_filename"
                                            ]
                                        )
                                    )
                                )


                                if (
                                    os.path.isfile(
                                        old_path
                                    )
                                ):

                                    try:

                                        os.remove(
                                            old_path
                                        )

                                    except OSError:

                                        pass


                            photo_filename = (
                                new_filename
                            )


                if not error:

                    connection.execute(
                        """
                        UPDATE driver_profile

                        SET
                            driver_name = ?,

                            short_bio = ?,

                            vehicle_name = ?,

                            vehicle_color = ?,

                            vehicle_plate = ?,

                            photo_filename = ?,

                            updated_at = ?

                        WHERE id = 1
                        """,
                        (
                            driver_name,

                            short_bio,

                            vehicle_name,

                            vehicle_color,

                            vehicle_plate,

                            photo_filename,

                            current_timestamp(),
                        )
                    )


                    connection.commit()


            finally:

                connection.close()


        if not error:

            return redirect(
                url_for(
                    "driver_profile",
                    saved="1"
                )
            )


    profile = (
        get_driver_profile()
    )


    return render_template(
        "admin/profile.html",

        profile=
            profile,

        photo_url=(
            driver_photo_url(
                profile[
                    "photo_filename"
                ]
            )
            if profile
            else None
        ),

        error=
            error,

        saved=(
            request.args.get(
                "saved"
            )
            == "1"
        )
    )


# ============================================================
# DRIVER DASHBOARD
# ============================================================

@app.route(
    "/driver"
)
@driver_login_required
def driver_dashboard():

    connection = (
        get_db()
    )


    try:

        orders = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE status NOT IN (
                    'SELESAI',
                    'DITOLAK'
                )

                ORDER BY id DESC
                """
            )
            .fetchall()
        )


        waiting_count = (
            connection.execute(
                """
                SELECT
                    COUNT(*) AS total

                FROM orders

                WHERE status = ?
                """,
                (
                    STATUS_WAITING,
                )
            )
            .fetchone()[
                "total"
            ]
        )


        active_count = (
            connection.execute(
                """
                SELECT
                    COUNT(*) AS total

                FROM orders

                WHERE status IN (
                    ?, ?, ?
                )
                """,
                ACTIVE_STATUSES
            )
            .fetchone()[
                "total"
            ]
        )


        today = (
            datetime.now()
            .strftime(
                "%Y-%m-%d"
            )
        )


        completed_today = (
            connection.execute(
                """
                SELECT
                    COUNT(*) AS total

                FROM orders

                WHERE status = ?

                AND created_at LIKE ?
                """,
                (
                    STATUS_COMPLETED,

                    f"{today}%"
                )
            )
            .fetchone()[
                "total"
            ]
        )


        income_today = (
            connection.execute(
                """
                SELECT
                    COALESCE(
                        SUM(fare),
                        0
                    ) AS total

                FROM orders

                WHERE status = ?

                AND created_at LIKE ?
                """,
                (
                    STATUS_COMPLETED,

                    f"{today}%"
                )
            )
            .fetchone()[
                "total"
            ]
        )


        service_open = (
            get_service_open(
                connection
            )
        )


        profile = (
            get_driver_profile(
                connection
            )
        )


    finally:

        connection.close()


    return render_template(
        "admin/dashboard.html",

        orders=
            orders,

        waiting_count=
            waiting_count,

        active_count=
            active_count,

        completed_today=
            completed_today,

        income_today=
            income_today,

        service_open=
            service_open,

        driver_profile=
            profile
    )


# ============================================================
# DRIVER SERVICE STATUS API
# ============================================================

@app.route(
    "/api/driver/service-status",
    methods=["POST"]
)
@driver_api_required
def update_driver_service_status():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    service_open = (
        data.get(
            "service_open"
        )
    )


    if not isinstance(
        service_open,
        bool
    ):

        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Status layanan "
                        "tidak valid."
                    ),
            }
        ), 400


    set_service_open(
        service_open
    )


    return jsonify(
        {
            "success":
                True,

            "service_open":
                service_open,

            "label":
                (
                    "MENERIMA PESANAN"
                    if service_open
                    else "SEDANG TIDAK MELAYANI"
                ),

            "message":
                (
                    "Layanan berhasil dibuka."
                    if service_open
                    else "Layanan berhasil ditutup."
                ),
        }
    )


# ============================================================
# DRIVER UPDATE ORDER STATUS
# ============================================================

@app.route(
    "/api/orders/<int:order_id>/status",
    methods=["POST"]
)
@driver_api_required
def update_order_status(
    order_id
):

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    new_status = (
        data.get(
            "status",
            ""
        )
        .strip()
        .upper()
    )


    connection = (
        get_db()
    )


    try:

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE id = ?
                """,
                (
                    order_id,
                )
            )
            .fetchone()
        )


        if not order:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Pesanan tidak ditemukan.",
                }
            ), 404


        allowed_next_statuses = (
            ALLOWED_TRANSITIONS.get(
                order[
                    "status"
                ],
                set()
            )
        )


        if (
            new_status
            not in allowed_next_statuses
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Perubahan status "
                            "tidak diperbolehkan."
                        ),
                }
            ), 400


        connection.execute(
            """
            UPDATE orders

            SET status = ?

            WHERE id = ?
            """,
            (
                new_status,
                order_id
            )
        )


        connection.commit()


    finally:

        connection.close()


    return jsonify(
        {
            "success":
                True,

            "status":
                new_status,

            "message":
                STATUS_MESSAGES.get(
                    new_status,
                    "Status berhasil diperbarui."
                ),
        }
    )


# ============================================================
# SECURITY HEADERS
# ============================================================

@app.after_request
def add_security_headers(
    response
):

    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"


    response.headers[
        "X-Frame-Options"
    ] = "DENY"


    response.headers[
        "Referrer-Policy"
    ] = (
        "strict-origin-when-cross-origin"
    )


    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=(self)"
    )


    if (
        request.path.startswith(
            "/driver"
        )
        or
        request.path.startswith(
            "/api/driver/"
        )
    ):

        response.headers[
            "Cache-Control"
        ] = (
            "no-store, "
            "no-cache, "
            "must-revalidate, "
            "max-age=0"
        )


    return response


# ============================================================
# ERROR - FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def file_too_large(
    error
):

    if request.path.startswith(
        "/driver/profile"
    ):

        profile = (
            get_driver_profile()
        )


        return render_template(
            "admin/profile.html",

            profile=
                profile,

            photo_url=(
                driver_photo_url(
                    profile[
                        "photo_filename"
                    ]
                )
                if profile
                else None
            ),

            error=(
                "Ukuran foto terlalu besar. "
                "Maksimal 5 MB."
            ),

            saved=False

        ), 413


    return (
        "File terlalu besar.",
        413
    )


# ============================================================
# INITIALIZE DATABASE
# ============================================================

init_database()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )