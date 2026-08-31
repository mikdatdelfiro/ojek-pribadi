# ============================================================
# OJEK PRIBADI
# Production Backend - Phase 14C
# Neon PostgreSQL + Cloudinary + PWA
# ============================================================

from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote, urlparse, unquote
from zoneinfo import ZoneInfo

import math
import os
import re
import secrets
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
    send_from_directory,
)

from werkzeug.middleware.proxy_fix import ProxyFix


# ============================================================
# PATHS + ENVIRONMENT
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(
        __file__
    )
)

ENV_PATH = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(
    ENV_PATH
)


# Import konektor production setelah .env dimuat.
import psycopg
from psycopg.rows import dict_row

import cloudinary
import cloudinary.api
import cloudinary.uploader


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    ""
).strip()

CLOUDINARY_URL = os.getenv(
    "CLOUDINARY_URL",
    ""
).strip()

CLOUDINARY_CLOUD_NAME = os.getenv(
    "CLOUDINARY_CLOUD_NAME",
    ""
).strip()

CLOUDINARY_API_KEY = os.getenv(
    "CLOUDINARY_API_KEY",
    ""
).strip()

CLOUDINARY_API_SECRET = os.getenv(
    "CLOUDINARY_API_SECRET",
    ""
).strip()

APP_ENV = os.getenv(
    "APP_ENV",
    "development"
).strip().lower()

APP_TIMEZONE = os.getenv(
    "APP_TIMEZONE",
    "Asia/Jakarta"
).strip()

try:
    APP_TZ = ZoneInfo(
        APP_TIMEZONE
    )
except Exception:
    APP_TIMEZONE = "Asia/Jakarta"
    APP_TZ = ZoneInfo(
        APP_TIMEZONE
    )


# ============================================================
# CLOUDINARY CONFIGURATION
# ============================================================

def _cloudinary_value_is_placeholder(value):

    value = str(value or "").strip().lower()

    placeholder_markers = (
        "<your_api_key>",
        "<your_api_secret>",
        "<your_cloud_name>",
        "your_api_key",
        "your_api_secret",
        "your_cloud_name",
    )

    return any(
        marker in value
        for marker in placeholder_markers
    )


def _valid_cloudinary_value(value):

    value = str(value or "").strip()

    return bool(
        value
        and not _cloudinary_value_is_placeholder(value)
    )


def configure_cloudinary():
    """
    Konfigurasi Cloudinary secara eksplisit.

    Prioritas:
    1. CLOUDINARY_CLOUD_NAME + CLOUDINARY_API_KEY + CLOUDINARY_API_SECRET
    2. CLOUDINARY_URL

    CLOUDINARY_URL diparse sendiri supaya konfigurasi tidak bergantung
    pada kapan SDK Cloudinary membaca environment variable.
    """

    if all(
        _valid_cloudinary_value(value)
        for value in (
            CLOUDINARY_CLOUD_NAME,
            CLOUDINARY_API_KEY,
            CLOUDINARY_API_SECRET,
        )
    ):

        cloudinary.config(
            cloud_name=CLOUDINARY_CLOUD_NAME,
            api_key=CLOUDINARY_API_KEY,
            api_secret=CLOUDINARY_API_SECRET,
            secure=True,
        )

        return "separate"


    if _valid_cloudinary_value(CLOUDINARY_URL):

        try:

            parsed = urlparse(
                CLOUDINARY_URL
            )

            if parsed.scheme != "cloudinary":
                raise ValueError(
                    "CLOUDINARY_URL harus diawali cloudinary://"
                )

            api_key = unquote(
                parsed.username or ""
            ).strip()

            api_secret = unquote(
                parsed.password or ""
            ).strip()

            cloud_name = unquote(
                parsed.hostname or ""
            ).strip()

            if not all(
                _valid_cloudinary_value(value)
                for value in (
                    cloud_name,
                    api_key,
                    api_secret,
                )
            ):
                raise ValueError(
                    "CLOUDINARY_URL belum berisi credential lengkap."
                )

            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True,
            )

            return "url"

        except Exception as error:

            print(
                "[CONFIG] CLOUDINARY_URL tidak valid:",
                type(error).__name__,
                str(error),
            )

            return "invalid_url"


    return "none"


CLOUDINARY_CONFIG_SOURCE = (
    configure_cloudinary()
)

_cloudinary_config = (
    cloudinary.config()
)

CLOUDINARY_CONFIGURED = bool(
    _valid_cloudinary_value(
        getattr(
            _cloudinary_config,
            "cloud_name",
            ""
        )
    )
    and _valid_cloudinary_value(
        getattr(
            _cloudinary_config,
            "api_key",
            ""
        )
    )
    and _valid_cloudinary_value(
        getattr(
            _cloudinary_config,
            "api_secret",
            ""
        )
    )
)


ALLOWED_DRIVER_PHOTO_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
}


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

app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1
)


# ============================================================
# STARTUP DIAGNOSTICS
# ============================================================

print(
    "[CONFIG] Environment:",
    APP_ENV
)

print(
    "[CONFIG] Timezone:",
    APP_TIMEZONE
)

print(
    "[CONFIG] Neon PostgreSQL:",
    (
        "OK"
        if DATABASE_URL
        else "BELUM DIATUR"
    )
)

print(
    "[CONFIG] Cloudinary:",
    (
        "OK"
        if CLOUDINARY_CONFIGURED
        else "BELUM DIATUR / KREDENSIAL TIDAK LENGKAP"
    )
)

print(
    "[CONFIG] Cloudinary source:",
    CLOUDINARY_CONFIG_SOURCE
)

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
# STATUS TIMESTAMP MAPPING
# ============================================================

STATUS_TIMESTAMP_COLUMNS = {

    STATUS_ACCEPTED:
        "accepted_at",

    STATUS_TO_PICKUP:
        "to_pickup_at",

    STATUS_PICKED_UP:
        "picked_up_at",

    STATUS_COMPLETED:
        "completed_at",

    STATUS_REJECTED:
        "rejected_at",
}

# ============================================================
# PHASE 19B
# CUSTOMER REVIEW CONFIG
# ============================================================

REVIEW_FEEDBACK_MAX_LENGTH = 300


REVIEW_ALLOWED_TAGS = {
    "ramah",
    "tepat_waktu",
    "aman",
    "nyaman",
    "komunikatif",
    "berkendara_baik",
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

    return datetime.now(
        APP_TZ
    ).strftime(
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
# TEMPLATE FILTERS
# ============================================================

@app.template_filter(
    "rupiah"
)
def rupiah_filter(
    value
):
    """
    Format:
    222000 -> Rp222.000
    """

    try:

        value = int(
            value or 0
        )

    except (
        TypeError,
        ValueError
    ):

        value = 0


    formatted = (
        f"{value:,}"
        .replace(
            ",",
            "."
        )
    )


    return (
        f"Rp{formatted}"
    )

# ============================================================
# DATABASE
# NEON POSTGRESQL
# ============================================================

def _convert_qmark_sql(
    query
):
    """
    Mempertahankan query lama aplikasi yang memakai
    placeholder SQLite "?" dan mengubahnya menjadi
    placeholder Psycopg "%s".
    """

    return str(
        query
    ).replace(
        "?",
        "%s"
    )


class DatabaseConnection:
    """
    Compatibility wrapper agar sebagian besar kode lama
    connection.execute(...).fetchone()/fetchall() tetap bekerja.
    """

    def __init__(
        self,
        connection
    ):

        self._connection = (
            connection
        )


    def execute(
        self,
        query,
        parameters=None
    ):

        sql = (
            _convert_qmark_sql(
                query
            )
        )

        if parameters is None:

            return (
                self._connection.execute(
                    sql
                )
            )

        return (
            self._connection.execute(
                sql,
                parameters
            )
        )


    def commit(
        self
    ):

        return (
            self._connection.commit()
        )


    def rollback(
        self
    ):

        return (
            self._connection.rollback()
        )


    def close(
        self
    ):

        return (
            self._connection.close()
        )


def get_db():

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL Neon belum dikonfigurasi."
        )


    raw_connection = (
        psycopg.connect(
            DATABASE_URL,

            row_factory=
                dict_row,

            connect_timeout=
                15,
        )
    )


    return DatabaseConnection(
        raw_connection
    )


def init_database():

    connection = get_db()


    try:

        # ----------------------------------------------------
        # ORDERS
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (

                id BIGSERIAL PRIMARY KEY,

                order_code TEXT UNIQUE NOT NULL,

                customer_name TEXT NOT NULL,

                whatsapp TEXT NOT NULL,

                pickup TEXT NOT NULL,

                destination TEXT NOT NULL,

                note TEXT,

                distance_km DOUBLE PRECISION NOT NULL,

                duration_minutes INTEGER NOT NULL,

                fare INTEGER NOT NULL,

                status TEXT NOT NULL
                    DEFAULT 'MENUNGGU',

                created_at TEXT NOT NULL,

                pickup_lat DOUBLE PRECISION,

                pickup_lon DOUBLE PRECISION,

                destination_lat DOUBLE PRECISION,

                destination_lon DOUBLE PRECISION,

                accepted_at TEXT,

                to_pickup_at TEXT,

                picked_up_at TEXT,

                completed_at TEXT,

                rejected_at TEXT
            )
            """
        )


        # ----------------------------------------------------
        # SAFE COLUMN MIGRATIONS
        # ----------------------------------------------------

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            pickup_lat DOUBLE PRECISION
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            pickup_lon DOUBLE PRECISION
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            destination_lat DOUBLE PRECISION
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            destination_lon DOUBLE PRECISION
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            accepted_at TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            to_pickup_at TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            picked_up_at TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            completed_at TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            rejected_at TEXT
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

                photo_url TEXT,

                photo_public_id TEXT,

                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            ALTER TABLE driver_profile
            ADD COLUMN IF NOT EXISTS
            photo_url TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE driver_profile
            ADD COLUMN IF NOT EXISTS
            photo_public_id TEXT
            """
        )


        # ----------------------------------------------------
        # DEFAULT SERVICE STATUS
        # ----------------------------------------------------

        connection.execute(
            """
            INSERT INTO app_settings (

                setting_key,

                setting_value,

                updated_at
            )

            VALUES (?, ?, ?)

            ON CONFLICT (setting_key)
            DO NOTHING
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
            INSERT INTO driver_profile (

                id,

                driver_name,

                short_bio,

                vehicle_name,

                vehicle_color,

                vehicle_plate,

                photo_url,

                photo_public_id,

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
                ?,
                ?
            )

            ON CONFLICT (id)
            DO NOTHING
            """,
            (
                "Pengemudi",

                "Pengemudi Ojek Pribadi",

                "Motor",

                "",

                "-",

                None,

                None,

                current_timestamp(),
            )
        )

        # ----------------------------------------------------
        # PHASE 19A + 19B
        # CUSTOMER REVIEWS
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS order_reviews (

                id BIGSERIAL PRIMARY KEY,

                order_id BIGINT NOT NULL UNIQUE,

                rating INTEGER NOT NULL
                    CHECK (
                        rating >= 1
                        AND rating <= 5
                    ),

                feedback TEXT,

                tags TEXT,

                created_at TEXT NOT NULL,

                CONSTRAINT fk_order_review_order
                    FOREIGN KEY (order_id)
                    REFERENCES orders(id)
                    ON DELETE CASCADE
            )
            """
        )


        # ----------------------------------------------------
        # SAFE REVIEW MIGRATIONS
        # ----------------------------------------------------

        connection.execute(
            """
            ALTER TABLE order_reviews
            ADD COLUMN IF NOT EXISTS
            feedback TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE order_reviews
            ADD COLUMN IF NOT EXISTS
            tags TEXT
            """
        )


        # ----------------------------------------------------
        # REVIEW INDEXES
        # ----------------------------------------------------

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_order_reviews_rating

            ON order_reviews(rating)
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_order_reviews_created_at

            ON order_reviews(created_at)
            """
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

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_completed_at

            ON orders(completed_at)
            """
        )


        connection.commit()


    except Exception:

        connection.rollback()

        raise


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
# CLOUDINARY
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
    value
):

    if not value:

        return None


    return str(
        value
    ).strip() or None


def cloudinary_upload_error_message(error):

    raw_message = str(
        error or ""
    ).strip()

    message = raw_message.lower()

    if (
        "invalid signature" in message
        or "unknown api key" in message
        or "invalid api key" in message
        or "authentication" in message
        or "authorization" in message
        or "unauthorized" in message
        or "401" in message
        or "403" in message
    ):

        return (
            "Kredensial Cloudinary ditolak. "
            "Periksa Cloud Name, API Key, dan API Secret."
        )

    if (
        "cloud name" in message
        or "cloud_name" in message
        or "must supply cloud" in message
    ):

        return (
            "Cloud Name Cloudinary tidak valid atau belum terbaca."
        )

    if (
        "api key" in message
        or "api_key" in message
        or "api secret" in message
        or "api_secret" in message
    ):

        return (
            "API Key atau API Secret Cloudinary belum benar."
        )

    if (
        "timed out" in message
        or "timeout" in message
        or "connection" in message
        or "network" in message
        or "name resolution" in message
    ):

        return (
            "Cloudinary tidak dapat dihubungi. "
            "Periksa koneksi internet lalu coba lagi."
        )

    return (
        "Cloudinary mengembalikan error: "
        + (
            raw_message[:220]
            if raw_message
            else type(error).__name__
        )
    )


def upload_driver_photo(
    photo
):

    if not CLOUDINARY_CONFIGURED:

        raise RuntimeError(
            "Cloudinary belum dikonfigurasi."
        )


    if (
        not photo
        or not photo.filename
    ):

        raise ValueError(
            "Foto tidak tersedia."
        )


    if not allowed_driver_photo(
        photo.filename
    ):

        raise ValueError(
            "Format foto harus JPG, JPEG, PNG, atau WEBP."
        )


    # Pastikan stream mulai dari awal.
    try:

        photo.stream.seek(
            0
        )

    except Exception:

        pass


    upload_result = (
        cloudinary.uploader.upload(
            photo.stream,

            folder=
                "ojek-pribadi/driver",

            public_id=(
                "driver_"
                + secrets.token_hex(
                    12
                )
            ),

            resource_type=
                "image",

            overwrite=
                False,

            timeout=
                30,
        )
    )


    secure_url = (
        upload_result.get(
            "secure_url"
        )
    )

    public_id = (
        upload_result.get(
            "public_id"
        )
    )


    if (
        not secure_url
        or not public_id
    ):

        raise RuntimeError(
            "Cloudinary tidak mengembalikan URL foto."
        )


    return {
        "photo_url":
            secure_url,

        "photo_public_id":
            public_id,
    }


def delete_cloudinary_photo(
    public_id
):

    if (
        not CLOUDINARY_CONFIGURED
        or not public_id
    ):

        return


    try:

        cloudinary.uploader.destroy(
            public_id,

            resource_type=
                "image",

            invalidate=
                True,
        )


    except Exception as error:

        # Gagal menghapus foto lama tidak boleh
        # menggagalkan penyimpanan profil baru.
        print(
            "[CLOUDINARY DELETE ERROR]",
            repr(error)
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
                profile.get(
                    "photo_url"
                )
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
# PHASE 13
# PWA FILES
# ============================================================

@app.route(
    "/manifest.webmanifest"
)
def pwa_manifest():

    return send_from_directory(
        os.path.join(
            BASE_DIR,
            "static"
        ),
        "manifest.webmanifest",
        mimetype=(
            "application/manifest+json"
        )
    )


@app.route(
    "/service-worker.js"
)
def pwa_service_worker():

    response = (
        send_from_directory(
            os.path.join(
                BASE_DIR,
                "static"
            ),
            "service-worker.js",
            mimetype=(
                "application/javascript"
            )
        )
    )


    # Service worker boleh mengontrol
    # seluruh website mulai dari "/".
    response.headers[
        "Service-Worker-Allowed"
    ] = "/"


    # Hindari browser menyimpan SW lama
    # terlalu agresif saat development.
    response.headers[
        "Cache-Control"
    ] = (
        "no-cache, "
        "no-store, "
        "must-revalidate"
    )


    return response

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
# PHASE 10 + PHASE 11.5
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/status",
    methods=["GET"]
)
def get_customer_order_status(
    order_code
):

    connection = (
        get_db()
    )


    try:

        # ----------------------------------------------------
        # ORDER
        # ----------------------------------------------------

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

                    created_at,

                    accepted_at,

                    to_pickup_at,

                    picked_up_at,

                    completed_at,

                    rejected_at

                FROM orders

                WHERE order_code = ?
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        # ----------------------------------------------------
        # DRIVER PROFILE
        # ----------------------------------------------------

        profile = None


        if (
            order
            and
            order["status"]
            in DRIVER_PROFILE_VISIBLE_STATUSES
        ):

            profile = (
                get_driver_profile(
                    connection
                )
            )


    finally:

        connection.close()


    # --------------------------------------------------------
    # ORDER NOT FOUND
    # --------------------------------------------------------

    if not order:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    "Pesanan tidak ditemukan.",
            }
        ), 404


    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

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


                # ============================================
                # PHASE 10
                # DRIVER PROFILE
                # ============================================

                "driver_profile":
                    driver_profile_payload(
                        profile
                    ),


                # ============================================
                # PHASE 11.5
                # JOURNEY TIMESTAMPS
                # ============================================

                "timestamps": {

                    "created_at":
                        order[
                            "created_at"
                        ],


                    "accepted_at":
                        order[
                            "accepted_at"
                        ],


                    "to_pickup_at":
                        order[
                            "to_pickup_at"
                        ],


                    "picked_up_at":
                        order[
                            "picked_up_at"
                        ],


                    "completed_at":
                        order[
                            "completed_at"
                        ],


                    "rejected_at":
                        order[
                            "rejected_at"
                        ],
                },
            },
        }
    )

# ============================================================
# PHASE 19B
# CUSTOMER REVIEW HELPERS
# ============================================================

def normalize_review_tags(
    value
):

    if not isinstance(
        value,
        list
    ):

        return []


    normalized = []


    for item in value:

        tag = (
            str(
                item or ""
            )
            .strip()
            .lower()
        )


        if (
            tag
            in REVIEW_ALLOWED_TAGS
            and
            tag not in normalized
        ):

            normalized.append(
                tag
            )


    return normalized


def encode_review_tags(
    tags
):

    return ",".join(
        tags
    )


def decode_review_tags(
    value
):

    if not value:

        return []


    tags = []


    for item in str(
        value
    ).split(","):

        tag = (
            item
            .strip()
            .lower()
        )


        if (
            tag
            and
            tag in REVIEW_ALLOWED_TAGS
            and
            tag not in tags
        ):

            tags.append(
                tag
            )


    return tags


def customer_review_payload(
    review
):

    if not review:

        return None


    return {

        "rating":
            int(
                review[
                    "rating"
                ]
            ),

        "feedback":
            (
                review[
                    "feedback"
                ]
                or ""
            ),

        "tags":
            decode_review_tags(
                review[
                    "tags"
                ]
            ),

        "created_at":
            review[
                "created_at"
            ],
    }


# ============================================================
# PHASE 19A + 19B
# CUSTOMER ORDER REVIEW API
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/review",
    methods=[
        "GET",
        "POST",
    ]
)
def customer_order_review(
    order_code
):

    connection = (
        get_db()
    )


    try:

        # ====================================================
        # ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT
                    id,
                    order_code,
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


        if not order:

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Pesanan tidak ditemukan.",
                }
            ), 404


        # ====================================================
        # EXISTING REVIEW
        # ====================================================

        existing_review = (
            connection.execute(
                """
                SELECT
                    id,
                    rating,
                    feedback,
                    tags,
                    created_at

                FROM order_reviews

                WHERE order_id = ?
                """,
                (
                    order[
                        "id"
                    ],
                )
            )
            .fetchone()
        )


        # ====================================================
        # GET REVIEW
        # ====================================================

        if (
            request.method
            == "GET"
        ):

            return jsonify(
                {
                    "success":
                        True,

                    "eligible":
                        (
                            order[
                                "status"
                            ]
                            == STATUS_COMPLETED
                        ),

                    "review":
                        customer_review_payload(
                            existing_review
                        ),
                }
            )


        # ====================================================
        # REVIEW ONLY AFTER COMPLETION
        # ====================================================

        if (
            order[
                "status"
            ]
            != STATUS_COMPLETED
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Penilaian hanya dapat "
                            "diberikan setelah "
                            "perjalanan selesai."
                        ),
                }
            ), 403


        # ====================================================
        # ALREADY REVIEWED
        # ====================================================

        if existing_review:

            return jsonify(
                {
                    "success":
                        True,

                    "already_reviewed":
                        True,

                    "message":
                        (
                            "Perjalanan ini "
                            "sudah dinilai."
                        ),

                    "review":
                        customer_review_payload(
                            existing_review
                        ),
                }
            )


        # ====================================================
        # REQUEST DATA
        # ====================================================

        data = (
            request.get_json(
                silent=True
            )
            or {}
        )


        raw_rating = (
            data.get(
                "rating"
            )
        )


        feedback = (
            str(
                data.get(
                    "feedback",
                    ""
                )
                or ""
            )
            .strip()
        )


        tags = (
            normalize_review_tags(
                data.get(
                    "tags",
                    []
                )
            )
        )


        # ====================================================
        # RATING VALIDATION
        # ====================================================

        if isinstance(
            raw_rating,
            bool
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        "Pilih rating 1 sampai 5.",
                }
            ), 400


        try:

            rating = int(
                raw_rating
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
                        "Pilih rating 1 sampai 5.",
                }
            ), 400


        if (
            rating < 1
            or rating > 5
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Rating harus "
                            "antara 1 sampai 5."
                        ),
                }
            ), 400


        # ====================================================
        # FEEDBACK VALIDATION
        # ====================================================

        if (
            len(
                feedback
            )
            >
            REVIEW_FEEDBACK_MAX_LENGTH
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Feedback maksimal "
                            f"{REVIEW_FEEDBACK_MAX_LENGTH} "
                            "karakter."
                        ),
                }
            ), 400


        # ====================================================
        # SAVE REVIEW
        # ====================================================

        created_at = (
            current_timestamp()
        )


        encoded_tags = (
            encode_review_tags(
                tags
            )
        )


        try:

            connection.execute(
                """
                INSERT INTO order_reviews (

                    order_id,

                    rating,

                    feedback,

                    tags,

                    created_at
                )

                VALUES (
                    ?, ?, ?, ?, ?
                )
                """,
                (
                    order[
                        "id"
                    ],

                    rating,

                    feedback,

                    encode_review_tags(
                        tags
                    ),

                    created_at,
                )
            )


            connection.commit()


        # ====================================================
        # DATABASE DUPLICATE PROTECTION
        # ====================================================

        except psycopg.errors.UniqueViolation:

            connection.rollback()


            existing_review = (
                connection.execute(
                    """
                    SELECT
                        id,
                        rating,
                        feedback,
                        tags,
                        created_at

                    FROM order_reviews

                    WHERE order_id = ?
                    """,
                    (
                        order[
                            "id"
                        ],
                    )
                )
                .fetchone()
            )


            return jsonify(
                {
                    "success":
                        True,

                    "already_reviewed":
                        True,

                    "message":
                        (
                            "Perjalanan ini "
                            "sudah dinilai."
                        ),

                    "review":
                        customer_review_payload(
                            existing_review
                        ),
                }
            )


        # ====================================================
        # SUCCESS
        # ====================================================

        return jsonify(
            {
                "success":
                    True,

                "already_reviewed":
                    False,

                "message":
                    (
                        "Terima kasih atas "
                        "penilaian Anda."
                    ),

                "review": {

                    "rating":
                        rating,

                    "feedback":
                        feedback,

                    "tags":
                        tags,

                    "created_at":
                        created_at,
                },
            }
        )


    except Exception as error:

        connection.rollback()


        print(
            "[CUSTOMER REVIEW ERROR]",
            type(
                error
            ).__name__,
            repr(
                error
            )
        )


        return jsonify(
            {
                "success":
                    False,

                "message":
                    (
                        "Penilaian belum berhasil "
                        "disimpan."
                    ),
            }
        ), 500


    finally:

        connection.close()

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
# NEON + CLOUDINARY
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


        photo = (
            request.files.get(
                "driver_photo"
            )
        )


        if (
            not error
            and photo
            and photo.filename
            and not allowed_driver_photo(
                photo.filename
            )
        ):

            error = (
                "Format foto harus "
                "JPG, JPEG, PNG, atau WEBP."
            )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        if not error:

            connection = (
                get_db()
            )

            uploaded_public_id = (
                None
            )

            old_public_id = (
                None
            )


            try:

                old_profile = (
                    get_driver_profile(
                        connection
                    )
                )


                photo_url = (
                    old_profile.get(
                        "photo_url"
                    )
                    if old_profile
                    else None
                )


                photo_public_id = (
                    old_profile.get(
                        "photo_public_id"
                    )
                    if old_profile
                    else None
                )


                old_public_id = (
                    photo_public_id
                )


                if (
                    photo
                    and photo.filename
                ):

                    try:

                        uploaded = (
                            upload_driver_photo(
                                photo
                            )
                        )


                        photo_url = (
                            uploaded[
                                "photo_url"
                            ]
                        )


                        photo_public_id = (
                            uploaded[
                                "photo_public_id"
                            ]
                        )


                        uploaded_public_id = (
                            photo_public_id
                        )


                    except Exception as upload_error:

                        print(
                            "[CLOUDINARY UPLOAD ERROR]",
                            repr(upload_error)
                        )


                        error = (
                            cloudinary_upload_error_message(
                                upload_error
                            )
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

                            photo_url = ?,

                            photo_public_id = ?,

                            updated_at = ?

                        WHERE id = 1
                        """,
                        (
                            driver_name,

                            short_bio,

                            vehicle_name,

                            vehicle_color,

                            vehicle_plate,

                            photo_url,

                            photo_public_id,

                            current_timestamp(),
                        )
                    )


                    connection.commit()


            except Exception:

                connection.rollback()


                if uploaded_public_id:

                    delete_cloudinary_photo(
                        uploaded_public_id
                    )


                raise


            finally:

                connection.close()


            if (
                not error
                and uploaded_public_id
                and old_public_id
                and old_public_id
                    != uploaded_public_id
            ):

                delete_cloudinary_photo(
                    old_public_id
                )


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
                profile.get(
                    "photo_url"
                )
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
            datetime.now(APP_TZ)
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

                AND COALESCE(
                    completed_at,
                    created_at
                ) LIKE ?
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

                AND COALESCE(
                    completed_at,
                    created_at
                ) LIKE ?
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

        # ----------------------------------------------------
        # LATEST ORDER ID
        # PHASE 12
        # ----------------------------------------------------

        latest_order_id = (
            connection.execute(
                """
                SELECT
                    COALESCE(
                        MAX(id),
                        0
                    ) AS latest_order_id

                FROM orders
                """
            )
            .fetchone()[
                "latest_order_id"
            ]
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
            profile,
            
        latest_order_id=
            latest_order_id,    
    )

# ============================================================
# PHASE 18E
# PREMIUM DRIVER HISTORY + INCOME
# ============================================================

@app.route(
    "/driver/history"
)
@driver_login_required
def driver_history():

    # ========================================================
    # FILTER INPUT
    # ========================================================

    period = (
        request.args.get(
            "period",
            "all"
        )
        .strip()
        .lower()
    )

    status_filter = (
        request.args.get(
            "status",
            "all"
        )
        .strip()
        .upper()
    )

    search_query = (
        request.args.get(
            "q",
            ""
        )
        .strip()
    )


    # ========================================================
    # VALIDATION
    # ========================================================

    valid_periods = {
        "all",
        "today",
        "7days",
        "30days",
    }

    if period not in valid_periods:
        period = "all"


    valid_statuses = {
        "ALL",
        STATUS_COMPLETED,
        STATUS_REJECTED,
    }

    if status_filter not in valid_statuses:
        status_filter = "ALL"


    # ========================================================
    # TIME
    # ========================================================

    now = datetime.now(
        APP_TZ
    )

    today = now.strftime(
        "%Y-%m-%d"
    )

    seven_days_start = (
        now
        - timedelta(days=6)
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )

    thirty_days_start = (
        now
        - timedelta(days=29)
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )


    # ========================================================
    # BASE QUERY
    # ========================================================

    query = """
        SELECT *

        FROM orders

        WHERE status IN (?, ?)
    """

    parameters = [
        STATUS_COMPLETED,
        STATUS_REJECTED,
    ]


    # ========================================================
    # PERIOD FILTER
    # ========================================================

    history_time_column = """
        (
            CASE

                WHEN status = 'SELESAI'

                THEN COALESCE(
                    completed_at,
                    created_at
                )

                WHEN status = 'DITOLAK'

                THEN COALESCE(
                    rejected_at,
                    created_at
                )

                ELSE created_at

            END
        )
    """


    if period == "today":

        query += (
            " AND "
            + history_time_column
            + " LIKE ?"
        )

        parameters.append(
            f"{today}%"
        )


    elif period == "7days":

        query += (
            " AND "
            + history_time_column
            + " >= ?"
        )

        parameters.append(
            seven_days_start
        )


    elif period == "30days":

        query += (
            " AND "
            + history_time_column
            + " >= ?"
        )

        parameters.append(
            thirty_days_start
        )


    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status_filter != "ALL":

        query += """
            AND status = ?
        """

        parameters.append(
            status_filter
        )


    # ========================================================
    # SEARCH
    # ========================================================

    if search_query:

        search_value = (
            f"%{search_query.lower()}%"
        )

        query += """
            AND (
                LOWER(order_code) LIKE ?
                OR LOWER(customer_name) LIKE ?
                OR LOWER(whatsapp) LIKE ?
                OR LOWER(pickup) LIKE ?
                OR LOWER(destination) LIKE ?
            )
        """

        parameters.extend(
            [
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
            ]
        )


    # ========================================================
    # ORDER
    # ========================================================

    query += """
        ORDER BY id DESC
    """


    connection = get_db()


    try:

        # ====================================================
        # FILTERED ORDERS
        # ====================================================

        orders = (
            connection.execute(
                query,
                parameters
            )
            .fetchall()
        )


        # ====================================================
        # FILTERED SUMMARY
        # ====================================================

        total_orders = len(
            orders
        )


        completed_count = sum(
            1
            for order in orders
            if order["status"]
            == STATUS_COMPLETED
        )


        rejected_count = sum(
            1
            for order in orders
            if order["status"]
            == STATUS_REJECTED
        )


        total_income = sum(
            int(
                order["fare"]
                or 0
            )
            for order in orders
            if order["status"]
            == STATUS_COMPLETED
        )


        average_income = (
            int(
                total_income
                / completed_count
            )
            if completed_count > 0
            else 0
        )


        # ====================================================
        # GLOBAL INCOME OVERVIEW
        # Only completed trips count as income.
        # ====================================================

        income_overview = (
            connection.execute(
                """
                SELECT

                    COALESCE(
                        SUM(
                            CASE
                                WHEN
                                    status = ?
                                    AND COALESCE(
                                        completed_at,
                                        created_at
                                    ) LIKE ?
                                THEN fare
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income_today,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN
                                    status = ?
                                    AND COALESCE(
                                        completed_at,
                                        created_at
                                    ) >= ?
                                THEN fare
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income_7_days,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN
                                    status = ?
                                    AND COALESCE(
                                        completed_at,
                                        created_at
                                    ) >= ?
                                THEN fare
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income_30_days

                FROM orders
                """,
                (
                    STATUS_COMPLETED,
                    f"{today}%",

                    STATUS_COMPLETED,
                    seven_days_start,

                    STATUS_COMPLETED,
                    thirty_days_start,
                )
            )
            .fetchone()
        )


        income_today = int(
            income_overview[
                "income_today"
            ]
            or 0
        )

        income_7_days = int(
            income_overview[
                "income_7_days"
            ]
            or 0
        )

        income_30_days = int(
            income_overview[
                "income_30_days"
            ]
            or 0
        )
        # ====================================================
        # PHASE 18E.4
        # PERFORMANCE ANALYTICS
        # ====================================================

        performance_row = (
            connection.execute(
                """
                SELECT

                    COUNT(
                        CASE
                            WHEN status = ?
                            THEN 1
                        END
                    ) AS completed_total,

                    COUNT(
                        CASE
                            WHEN status = ?
                            THEN 1
                        END
                    ) AS rejected_total,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN status = ?
                                THEN fare
                            END
                        ),
                        0
                    ) AS average_fare,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN status = ?
                                THEN distance_km
                            END
                        ),
                        0
                    ) AS average_distance,

                    COALESCE(
                        AVG(
                            CASE
                                WHEN status = ?
                                THEN duration_minutes
                            END
                        ),
                        0
                    ) AS average_duration,

                    COALESCE(
                        MAX(
                            CASE
                                WHEN status = ?
                                THEN fare
                            END
                        ),
                        0
                    ) AS highest_fare,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN status = ?
                                THEN distance_km
                                ELSE 0
                            END
                        ),
                        0
                    ) AS total_distance

                FROM orders

                WHERE status IN (?, ?)
                """,
                (
                    STATUS_COMPLETED,
                    STATUS_REJECTED,

                    STATUS_COMPLETED,
                    STATUS_COMPLETED,
                    STATUS_COMPLETED,
                    STATUS_COMPLETED,
                    STATUS_COMPLETED,

                    STATUS_COMPLETED,
                    STATUS_REJECTED,
                )
            )
            .fetchone()
        )


        analytics_completed = int(
            performance_row[
                "completed_total"
            ]
            or 0
        )


        analytics_rejected = int(
            performance_row[
                "rejected_total"
            ]
            or 0
        )


        finalized_orders = (
            analytics_completed
            +
            analytics_rejected
        )


        completion_rate = (
            round(
                (
                    analytics_completed
                    /
                    finalized_orders
                )
                * 100
            )
            if finalized_orders > 0
            else 0
        )


        average_fare_analytics = int(
            performance_row[
                "average_fare"
            ]
            or 0
        )


        average_distance = round(
            float(
                performance_row[
                    "average_distance"
                ]
                or 0
            ),
            1
        )


        average_duration = round(
            float(
                performance_row[
                    "average_duration"
                ]
                or 0
            )
        )


        highest_fare = int(
            performance_row[
                "highest_fare"
            ]
            or 0
        )


        total_distance = round(
            float(
                performance_row[
                    "total_distance"
                ]
                or 0
            ),
            1
        )


        # ====================================================
        # PERFORMANCE LABEL
        # ====================================================

        if finalized_orders == 0:

            performance_label = (
                "Belum ada data"
            )

            performance_message = (
                "Selesaikan beberapa perjalanan "
                "untuk melihat insight performa."
            )


        elif completion_rate >= 90:

            performance_label = (
                "Sangat Baik"
            )

            performance_message = (
                "Sebagian besar pesanan berhasil "
                "diselesaikan."
            )


        elif completion_rate >= 75:

            performance_label = (
                "Stabil"
            )

            performance_message = (
                "Performa perjalanan berada "
                "pada tingkat yang stabil."
            )


        else:

            performance_label = (
                "Perlu Perhatian"
            )

            performance_message = (
                "Rasio perjalanan selesai masih "
                "dapat ditingkatkan."
            )


        # ====================================================
        # 7 DAY INCOME CHART
        # ====================================================

        weekday_names = [
            "Sen",
            "Sel",
            "Rab",
            "Kam",
            "Jum",
            "Sab",
            "Min",
        ]


        income_chart = []


        for days_ago in range(
            6,
            -1,
            -1
        ):

            chart_date = (
                now
                -
                timedelta(
                    days=days_ago
                )
            )


            chart_date_string = (
                chart_date.strftime(
                    "%Y-%m-%d"
                )
            )


            chart_row = (
                connection.execute(
                    """
                    SELECT
                        COALESCE(
                            SUM(fare),
                            0
                        ) AS income,

                        COUNT(*) AS trips

                    FROM orders

                    WHERE status = ?

                    AND COALESCE(
                        completed_at,
                        created_at
                    ) LIKE ?
                    """,
                    (
                        STATUS_COMPLETED,
                        f"{chart_date_string}%"
                    )
                )
                .fetchone()
            )


            income_chart.append(
                {
                    "label":
                        weekday_names[
                            chart_date.weekday()
                        ],

                    "date":
                        chart_date.strftime(
                            "%d/%m"
                        ),

                    "income":
                        int(
                            chart_row[
                                "income"
                            ]
                            or 0
                        ),

                    "trips":
                        int(
                            chart_row[
                                "trips"
                            ]
                            or 0
                        ),
                }
            )


        # ====================================================
        # NORMALIZE BAR WIDTH
        # ====================================================

        chart_max_income = max(
            (
                item[
                    "income"
                ]
                for item
                in income_chart
            ),
            default=0
        )


        for item in income_chart:

            if chart_max_income > 0:

                item[
                    "percentage"
                ] = max(
                    3,
                    round(
                        (
                            item[
                                "income"
                            ]
                            /
                            chart_max_income
                        )
                        * 100
                    )
                )

            else:

                item[
                    "percentage"
                ] = 0


    finally:

        connection.close()

    return render_template(
        "admin/history.html",

        orders=
            orders,

        total_orders=
            total_orders,

        completed_count=
            completed_count,

        rejected_count=
            rejected_count,

        total_income=
            total_income,

        average_income=
            average_income,

        income_today=
            income_today,

        income_7_days=
            income_7_days,

        income_30_days=
            income_30_days,

        period=
            period,

        status_filter=
            status_filter,

        search_query=
            search_query,

        completion_rate=
            completion_rate,

        average_fare_analytics=
            average_fare_analytics,

        average_distance=
            average_distance,

        average_duration=
            average_duration,

        highest_fare=
            highest_fare,

        total_distance=
            total_distance,

        analytics_completed=
            analytics_completed,

        analytics_rejected=
            analytics_rejected,

        performance_label=
            performance_label,

        performance_message=
            performance_message,

        income_chart=
            income_chart,
    )
    
# ============================================================
# DRIVER ORDER DETAIL
# ============================================================

@app.route(
    "/driver/orders/<int:order_id>"
)
@driver_login_required
def driver_order_detail(
    order_id
):

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


    finally:

        connection.close()


    if not order:

        abort(
            404
        )


    # --------------------------------------------------------
    # GOOGLE MAPS LINKS
    # --------------------------------------------------------

    pickup_map_url = (
        None
    )


    destination_map_url = (
        None
    )


    if (
        order[
            "pickup_lat"
        ]
        is not None
        and
        order[
            "pickup_lon"
        ]
        is not None
    ):

        pickup_map_url = (
            "https://www.google.com/maps/search/"
            "?api=1"
            "&query="
            f"{order['pickup_lat']},"
            f"{order['pickup_lon']}"
        )


    if (
        order[
            "destination_lat"
        ]
        is not None
        and
        order[
            "destination_lon"
        ]
        is not None
    ):

        destination_map_url = (
            "https://www.google.com/maps/search/"
            "?api=1"
            "&query="
            f"{order['destination_lat']},"
            f"{order['destination_lon']}"
        )


    return render_template(
        "admin/order_detail.html",

        order=
            order,

        pickup_map_url=
            pickup_map_url,

        destination_map_url=
            destination_map_url,
    )    

# ============================================================
# API - DRIVER NEW ORDER NOTIFICATION
# PHASE 12
# ============================================================

@app.route(
    "/api/driver/new-orders",
    methods=["GET"]
)
@driver_api_required
def driver_new_orders():

    # --------------------------------------------------------
    # AFTER ID
    # --------------------------------------------------------

    raw_after_id = (
        request.args.get(
            "after_id",
            "0"
        )
        .strip()
    )


    try:

        after_id = int(
            raw_after_id
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
                    "after_id tidak valid.",
            }
        ), 400


    after_id = max(
        0,
        after_id
    )


    connection = (
        get_db()
    )


    try:

        # ----------------------------------------------------
        # GLOBAL LATEST ID
        # ----------------------------------------------------

        latest_order_id = (
            connection.execute(
                """
                SELECT
                    COALESCE(
                        MAX(id),
                        0
                    ) AS latest_order_id

                FROM orders
                """
            )
            .fetchone()[
                "latest_order_id"
            ]
        )


        # ----------------------------------------------------
        # NEW WAITING ORDERS
        # ----------------------------------------------------

        new_orders = (
            connection.execute(
                """
                SELECT

                    id,

                    order_code,

                    customer_name,

                    pickup,

                    destination,

                    fare,

                    created_at

                FROM orders

                WHERE
                    id > ?

                    AND status = ?

                ORDER BY id ASC

                LIMIT 20
                """,
                (
                    after_id,

                    STATUS_WAITING,
                )
            )
            .fetchall()
        )


    finally:

        connection.close()


    return jsonify(
        {
            "success":
                True,

            "latest_order_id":
                latest_order_id,

            "count":
                len(
                    new_orders
                ),

            "orders": [

                {
                    "id":
                        order[
                            "id"
                        ],

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

                    "fare":
                        order[
                            "fare"
                        ],

                    "created_at":
                        order[
                            "created_at"
                        ],
                }

                for order
                in new_orders

            ],
        }
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


                # ----------------------------------------------------
        # STATUS TIMESTAMP
        # ----------------------------------------------------

        status_timestamp_column = (
            STATUS_TIMESTAMP_COLUMNS.get(
                new_status
            )
        )


        status_timestamp = (
            current_timestamp()
        )


        if status_timestamp_column:

            connection.execute(
                f"""
                UPDATE orders

                SET
                    status = ?,

                    {status_timestamp_column} = ?

                WHERE id = ?
                """,
                (
                    new_status,

                    status_timestamp,

                    order_id,
                )
            )


        else:

            connection.execute(
                """
                UPDATE orders

                SET status = ?

                WHERE id = ?
                """,
                (
                    new_status,

                    order_id,
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

            "timestamp":
                status_timestamp,

            "message":
                STATUS_MESSAGES.get(
                    new_status,
                    "Status berhasil diperbarui."
                ),
        }
    )


# ============================================================
# SECURITY HEADERS
# PHASE 14E
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


    response.headers[
        "X-Permitted-Cross-Domain-Policies"
    ] = "none"


    if (
        APP_ENV
        == "production"
    ):

        response.headers[
            "Strict-Transport-Security"
        ] = (
            "max-age=31536000"
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


        response.headers[
            "Pragma"
        ] = "no-cache"


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
                    profile.get(
                        "photo_url"
                    )
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
# CLOUDINARY HEALTH CHECK
# DRIVER ONLY
# ============================================================

@app.route(
    "/api/driver/cloudinary-health",
    methods=["GET"]
)
@driver_api_required
def cloudinary_health():
    """
    Tes jalur upload yang benar-benar digunakan aplikasi.

    Kita tidak lagi memakai Admin API ping sebagai tes utama.
    Endpoint ini mengunggah gambar 1x1 yang sangat kecil lalu
    menghapusnya kembali. Dengan demikian yang diuji sama dengan
    fitur upload foto profil driver.
    """

    config = cloudinary.config()

    safe_config = {
        "config_source": CLOUDINARY_CONFIG_SOURCE,
        "cloud_name": getattr(
            config,
            "cloud_name",
            None
        ),
        "api_key_present": bool(
            getattr(
                config,
                "api_key",
                None
            )
        ),
        "api_secret_present": bool(
            getattr(
                config,
                "api_secret",
                None
            )
        ),
    }

    if not CLOUDINARY_CONFIGURED:

        return jsonify(
            {
                "success": False,
                "status": "not_configured",
                "message": (
                    "Konfigurasi Cloudinary belum lengkap."
                ),
                "config": safe_config,
            }
        ), 503


    # GIF transparan 1x1.
    health_asset = (
        "data:image/gif;base64,"
        "R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw=="
    )

    public_id = (
        "health_"
        + secrets.token_hex(8)
    )

    uploaded_public_id = None

    try:

        result = cloudinary.uploader.upload(
            health_asset,
            folder="ojek-pribadi/health",
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            timeout=30,
        )

        uploaded_public_id = result.get(
            "public_id"
        )

        secure_url = result.get(
            "secure_url"
        )

        if not uploaded_public_id or not secure_url:
            raise RuntimeError(
                "Cloudinary tidak mengembalikan public_id/secure_url."
            )

        return jsonify(
            {
                "success": True,
                "status": "ok",
                "message": (
                    "Cloudinary upload berhasil dan credential valid."
                ),
                "config": safe_config,
            }
        ), 200

    except Exception as error:

        print(
            "[CLOUDINARY HEALTH ERROR]",
            type(error).__name__,
            repr(error)
        )

        return jsonify(
            {
                "success": False,
                "status": "error",
                "error_type": type(error).__name__,
                "message": (
                    cloudinary_upload_error_message(
                        error
                    )
                ),
                "config": safe_config,
            }
        ), 503

    finally:

        if uploaded_public_id:

            try:
                cloudinary.uploader.destroy(
                    uploaded_public_id,
                    resource_type="image",
                    invalidate=False,
                )
            except Exception as cleanup_error:
                print(
                    "[CLOUDINARY HEALTH CLEANUP ERROR]",
                    repr(cleanup_error)
                )


# ============================================================
# PRODUCTION HEALTH CHECK
# ============================================================

@app.route(
    "/healthz",
    methods=["GET"]
)
def healthz():

    connection = None


    try:

        connection = (
            get_db()
        )


        connection.execute(
            "SELECT 1"
        ).fetchone()


        return jsonify(
            {
                "status":
                    "ok"
            }
        ), 200


    except Exception:

        return jsonify(
            {
                "status":
                    "error"
            }
        ), 503


    finally:

        if connection:

            connection.close()

# ============================================================
# BOOT DIAGNOSTICS
# ============================================================

_registered_routes = {
    rule.rule
    for rule in app.url_map.iter_rules()
}

print(
    "[BOOT] File aktif:",
    os.path.abspath(
        __file__
    )
)

print(
    "[BOOT] /healthz:",
    (
        "OK"
        if "/healthz"
        in _registered_routes
        else "TIDAK ADA"
    )
)

print(
    "[BOOT] /manifest.webmanifest:",
    (
        "OK"
        if "/manifest.webmanifest"
        in _registered_routes
        else "TIDAK ADA"
    )
)

print(
    "[BOOT] /service-worker.js:",
    (
        "OK"
        if "/service-worker.js"
        in _registered_routes
        else "TIDAK ADA"
    )
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
        host="127.0.0.1",
        port=5000,
        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "false"
            )
            .strip()
            .lower()
            == "true"
        )
    )