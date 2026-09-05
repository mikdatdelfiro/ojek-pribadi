# ============================================================
# OJEK PRIBADI
# Production Backend - Phase 14C
# Neon PostgreSQL + Cloudinary + PWA
# ============================================================

from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import quote, urlparse, unquote
from zoneinfo import ZoneInfo

import hashlib
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
    flash,
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
# PHASE 20C
# PAYMENT CONFIGURATION
# ============================================================

PAYMENT_BANK_NAME = os.getenv(
    "PAYMENT_BANK_NAME",
    ""
).strip()


PAYMENT_BANK_ACCOUNT_NUMBER = os.getenv(
    "PAYMENT_BANK_ACCOUNT_NUMBER",
    ""
).strip()


PAYMENT_BANK_ACCOUNT_NAME = os.getenv(
    "PAYMENT_BANK_ACCOUNT_NAME",
    ""
).strip()


PAYMENT_QRIS_IMAGE = os.getenv(
    "PAYMENT_QRIS_IMAGE",
    "images/payment/qris.png"
).strip()

# ============================================================
# PHASE 20I.4
# FAILED & EXPIRED PAYMENT CONFIGURATION
# ============================================================

try:

    PAYMENT_EXPIRY_MINUTES = int(
        os.getenv(
            "PAYMENT_EXPIRY_MINUTES",
            "30"
        )
    )

except (
    TypeError,
    ValueError
):

    PAYMENT_EXPIRY_MINUTES = 30


# Hindari konfigurasi yang terlalu pendek
# atau tidak masuk akal di production.
PAYMENT_EXPIRY_MINUTES = max(
    5,
    min(
        PAYMENT_EXPIRY_MINUTES,
        24 * 60
    )
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
# PHASE 19E
# REVIEW RATE LIMIT STATE
# ============================================================

review_attempts = {}

review_attempts_lock = (
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
# PHASE 20
# PAYMENT & TRANSACTION SYSTEM
# ============================================================

PAYMENT_METHOD_CASH = (
    "TUNAI"
)

PAYMENT_METHOD_QRIS = (
    "QRIS"
)

PAYMENT_METHOD_BANK_TRANSFER = (
    "TRANSFER_BANK"
)

PAYMENT_STATUS_UNPAID = (
    "BELUM_DIBAYAR"
)

PAYMENT_STATUS_PENDING = (
    "MENUNGGU_PEMBAYARAN"
)

PAYMENT_STATUS_AWAITING_CONFIRMATION = (
    "MENUNGGU_KONFIRMASI"
)

PAYMENT_STATUS_PAID = (
    "DIBAYAR"
)

PAYMENT_STATUS_FAILED = (
    "GAGAL"
)

PAYMENT_STATUS_EXPIRED = (
    "KEDALUWARSA"
)

PAYMENT_STATUS_REFUNDED = (
    "DIKEMBALIKAN"
)


PAYMENT_ALLOWED_METHODS = {

    PAYMENT_METHOD_CASH,

    PAYMENT_METHOD_QRIS,

    PAYMENT_METHOD_BANK_TRANSFER,
}

PAYMENT_ALLOWED_STATUSES = {

    PAYMENT_STATUS_UNPAID,

    PAYMENT_STATUS_PENDING,

    PAYMENT_STATUS_AWAITING_CONFIRMATION,

    PAYMENT_STATUS_PAID,

    PAYMENT_STATUS_FAILED,

    PAYMENT_STATUS_EXPIRED,

    PAYMENT_STATUS_REFUNDED,

}

# ============================================================
# PHASE 20I.1
# PAYMENT CORRECTION FOUNDATION
# ============================================================

PAYMENT_AUDIT_REASON_MAX_LENGTH = 500

PAYMENT_AUDIT_EVENT_CODE_BYTES = 12


PAYMENT_AUDIT_ACTOR_DRIVER = (
    "DRIVER"
)

PAYMENT_AUDIT_ACTOR_CUSTOMER = (
    "CUSTOMER"
)

PAYMENT_AUDIT_ACTOR_SYSTEM = (
    "SYSTEM"
)


PAYMENT_AUDIT_ALLOWED_ACTORS = {
    PAYMENT_AUDIT_ACTOR_DRIVER,
    PAYMENT_AUDIT_ACTOR_CUSTOMER,
    PAYMENT_AUDIT_ACTOR_SYSTEM,
}


# ============================================================
# PAYMENT AUDIT ACTIONS
# ============================================================

PAYMENT_AUDIT_ACTION_CREATED = (
    "PAYMENT_CREATED"
)

PAYMENT_AUDIT_ACTION_CONFIRMED_CASH = (
    "PAYMENT_CONFIRMED_CASH"
)

PAYMENT_AUDIT_ACTION_CUSTOMER_SUBMITTED = (
    "PAYMENT_CUSTOMER_SUBMITTED"
)

PAYMENT_AUDIT_ACTION_CONFIRMED_MANUAL = (
    "PAYMENT_CONFIRMED_MANUAL"
)

PAYMENT_AUDIT_ACTION_CORRECTION = (
    "PAYMENT_CORRECTED"
)

PAYMENT_AUDIT_ACTION_REFUND_REJECTED = (
    "PAYMENT_REFUND_REJECTED"
)

PAYMENT_AUDIT_ACTION_REFUND = (
    "PAYMENT_REFUNDED"
)

PAYMENT_AUDIT_ACTION_REFUND_REQUESTED = (
    "PAYMENT_REFUND_REQUESTED"
)

PAYMENT_AUDIT_ACTION_FAILED = (
    "PAYMENT_FAILED"
)

PAYMENT_AUDIT_ACTION_EXPIRED = (
    "PAYMENT_EXPIRED"
)


PAYMENT_AUDIT_ALLOWED_ACTIONS = {
    PAYMENT_AUDIT_ACTION_CREATED,
    PAYMENT_AUDIT_ACTION_CUSTOMER_SUBMITTED,
    PAYMENT_AUDIT_ACTION_CONFIRMED_CASH,
    PAYMENT_AUDIT_ACTION_CONFIRMED_MANUAL,
    PAYMENT_AUDIT_ACTION_CORRECTION,
    PAYMENT_AUDIT_ACTION_REFUND,
    PAYMENT_AUDIT_ACTION_FAILED,
    PAYMENT_AUDIT_ACTION_EXPIRED,
    PAYMENT_AUDIT_ACTION_REFUND_REQUESTED,
    PAYMENT_AUDIT_ACTION_REFUND_REJECTED,
}

# ============================================================
# PHASE 20I.2
# PAYMENT STATUS TRANSITION SECURITY
# ============================================================

PAYMENT_STATUS_TRANSITIONS = {

    PAYMENT_STATUS_UNPAID: {
        PAYMENT_STATUS_PAID,
        PAYMENT_STATUS_FAILED,
    },

    PAYMENT_STATUS_PENDING: {
        PAYMENT_STATUS_AWAITING_CONFIRMATION,
        PAYMENT_STATUS_FAILED,
        PAYMENT_STATUS_EXPIRED,
    },

    PAYMENT_STATUS_AWAITING_CONFIRMATION: {
        PAYMENT_STATUS_PAID,
        PAYMENT_STATUS_FAILED,
        PAYMENT_STATUS_EXPIRED,
    },

    PAYMENT_STATUS_PAID: {
        PAYMENT_STATUS_REFUNDED,
    },

    PAYMENT_STATUS_FAILED: set(),

    PAYMENT_STATUS_EXPIRED: set(),

    PAYMENT_STATUS_REFUNDED: set(),
}


# ============================================================
# ACTOR-SPECIFIC TRANSITIONS
# ============================================================

PAYMENT_ACTOR_TRANSITIONS = {

    PAYMENT_AUDIT_ACTOR_CUSTOMER: {

        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
        ),
    },


    PAYMENT_AUDIT_ACTOR_DRIVER: {

        (
            PAYMENT_STATUS_UNPAID,
            PAYMENT_STATUS_PAID,
        ),

        (
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
            PAYMENT_STATUS_PAID,
        ),

        # Digunakan PHASE 20I.3 nanti.
        (
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_REFUNDED,
        ),
    },


    PAYMENT_AUDIT_ACTOR_SYSTEM: {

        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_EXPIRED,
        ),

        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_FAILED,
        ),

        (
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
            PAYMENT_STATUS_FAILED,
        ),

        (
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
            PAYMENT_STATUS_EXPIRED,
        ),
    },
}

# ============================================================
# PHASE 20I.3
# PAYMENT REFUND CONFIGURATION
# ============================================================

PAYMENT_REFUND_REASON_MIN_LENGTH = 3

PAYMENT_REFUND_REASON_MAX_LENGTH = 300

PAYMENT_REFUND_REFERENCE_MAX_LENGTH = 100

# ============================================================
# PHASE 20I.3A
# REFUND REQUEST FOUNDATION
# CUSTOMER <-> DRIVER
# ============================================================

PAYMENT_REFUND_REQUEST_NONE = "NONE"

PAYMENT_REFUND_REQUEST_PENDING = "PENDING"

PAYMENT_REFUND_REQUEST_APPROVED = "APPROVED"

PAYMENT_REFUND_REQUEST_REJECTED = "REJECTED"


PAYMENT_REFUND_REQUEST_ALLOWED_STATUSES = {
    PAYMENT_REFUND_REQUEST_NONE,
    PAYMENT_REFUND_REQUEST_PENDING,
    PAYMENT_REFUND_REQUEST_APPROVED,
    PAYMENT_REFUND_REQUEST_REJECTED,
}


PAYMENT_REFUND_REQUEST_REASON_MIN_LENGTH = 3

PAYMENT_REFUND_REQUEST_REASON_MAX_LENGTH = 300

PAYMENT_REFUND_REJECTION_REASON_MIN_LENGTH = 3

PAYMENT_REFUND_REJECTION_REASON_MAX_LENGTH = 300

# ============================================================
# PHASE 20H.1
# PAYMENT HISTORY FOUNDATION
# ============================================================

PAYMENT_HISTORY_PAGE_SIZE = 20

PAYMENT_HISTORY_MAX_PAGE_SIZE = 50

PAYMENT_HISTORY_SEARCH_MAX_LENGTH = 100


# ============================================================
# PHASE 20G.2
# RECEIPT SECURITY
# ============================================================

RECEIPT_TOKEN_BYTES = 32

RECEIPT_ACCESS_WINDOW_SECONDS = (
    10 * 60
)

RECEIPT_ACCESS_MAX_ATTEMPTS = 12


_receipt_access_attempts = {}

_receipt_access_lock = (
    threading.Lock()
)

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

REVIEW_ALLOWED_TAGS_LABELS = {

    "ramah":
        "Ramah",

    "tepat_waktu":
        "Tepat Waktu",

    "aman":
        "Aman",

    "nyaman":
        "Nyaman",

    "komunikatif":
        "Komunikatif",

    "berkendara_baik":
        "Berkendara Baik",
}

# ============================================================
# PHASE 19F
# REVIEW HISTORY CONFIG
# ============================================================

REVIEW_HISTORY_PAGE_SIZE = 20

REVIEW_HISTORY_MAX_PAGE_SIZE = 50

# ============================================================
# PHASE 19F.3
# REVIEW SEARCH CONFIG
# ============================================================

REVIEW_HISTORY_SEARCH_MAX_LENGTH = 100

# ============================================================
# PHASE 19E
# REVIEW SAFETY CONFIG
# ============================================================

REVIEW_TOKEN_BYTES = 32

REVIEW_WINDOW_DAYS = 7

REVIEW_POST_LIMIT = 8

REVIEW_RATE_WINDOW_SECONDS = 10 * 60

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

        # ============================================================
        # PHASE 20G.2
        # RECEIPT SECURITY MIGRATION
        # ============================================================

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS receipt_token_hash TEXT
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
        # PHASE 19E
        # REVIEW SECURITY TOKEN
        # ----------------------------------------------------

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            review_token_hash TEXT
            """
        )
        
        # ============================================================
        # PHASE 20A
        # PAYMENT FOUNDATION
        # ============================================================

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_method TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_status TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_amount INTEGER
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_reference TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_provider TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_expires_at TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            paid_at TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_updated_at TEXT
            """
        )
        
        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_customer_confirmed_at TEXT
            """
        )


        # ====================================================
        # PHASE 20H.1
        # DRIVER PAYMENT CONFIRMATION TIMESTAMP
        # ====================================================

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_driver_confirmed_at TEXT
            """
        )
        
        # ====================================================
        # PHASE 20I.3
        # PAYMENT REFUND MIGRATION
        # ====================================================

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refunded_at TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_amount INTEGER
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_reason TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_reference TEXT
            """
        )
        
        # ====================================================
        # PHASE 20I.3A
        # REFUND REQUEST FOUNDATION
        # CUSTOMER <-> DRIVER
        # ====================================================

        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_request_status TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_requested_at TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_request_reason TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_reviewed_at TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE orders
            ADD COLUMN IF NOT EXISTS
            payment_refund_rejection_reason TEXT
            """
        )
        
        # ====================================================
        # PHASE 20I.3A.4
        # NORMALIZE REFUND REQUEST STATUS
        # ====================================================

        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status = ?

            WHERE
                payment_refund_request_status IS NULL

                OR TRIM(
                    payment_refund_request_status
                ) = ''
            """,
            (
                PAYMENT_REFUND_REQUEST_NONE,
            )
        )
        
        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status =
                    UPPER(
                        TRIM(
                            payment_refund_request_status
                        )
                    )

            WHERE
                payment_refund_request_status IS NOT NULL
            """
        )
        
        
        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status = ?

            WHERE
                payment_refund_request_status
                NOT IN (
                    ?,
                    ?,
                    ?,
                    ?
                )
            """,
            (
                PAYMENT_REFUND_REQUEST_NONE,

                PAYMENT_REFUND_REQUEST_NONE,
                PAYMENT_REFUND_REQUEST_PENDING,
                PAYMENT_REFUND_REQUEST_APPROVED,
                PAYMENT_REFUND_REQUEST_REJECTED,
            )
        )
        
        # ====================================================
        # DEFAULT STATUS FOR NEW ORDERS
        # ====================================================

        connection.execute(
            """
            ALTER TABLE orders

            ALTER COLUMN
            payment_refund_request_status

            SET DEFAULT 'NONE'
            """
        )
        
        # ====================================================
        # REFUND REQUEST STATUS MUST ALWAYS EXIST
        # ====================================================

        connection.execute(
            """
            ALTER TABLE orders

            ALTER COLUMN
            payment_refund_request_status

            SET NOT NULL
            """
        )
        
        # ====================================================
        # PHASE 20I.3A.7
        # REFUND REQUEST STATUS DATABASE CONSTRAINT
        # ====================================================

        refund_status_constraint = (
            connection.execute(
                """
                SELECT
                    1

                FROM pg_constraint

                WHERE
                    conname = ?
                    AND conrelid =
                        'orders'::regclass

                LIMIT 1
                """,
                (
                    "chk_orders_refund_request_status",
                )
            )
            .fetchone()
        )


        if not refund_status_constraint:

            connection.execute(
                """
                ALTER TABLE orders

                ADD CONSTRAINT
                chk_orders_refund_request_status

                CHECK (
                    payment_refund_request_status
                    IN (
                        'NONE',
                        'PENDING',
                        'APPROVED',
                        'REJECTED'
                    )
                )
                """
            )
        
        # ====================================================
        # PHASE 20I.1
        # PAYMENT AUDIT LOG FOUNDATION
        # ====================================================

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS payment_audit_logs (

                id BIGSERIAL PRIMARY KEY,

                event_code TEXT
                    UNIQUE
                    NOT NULL,

                order_id BIGINT
                    NOT NULL,

                order_code TEXT
                    NOT NULL,

                action TEXT
                    NOT NULL,

                actor_type TEXT
                    NOT NULL,

                old_payment_method TEXT,

                new_payment_method TEXT,

                old_payment_status TEXT,

                new_payment_status TEXT,

                old_payment_amount INTEGER,

                new_payment_amount INTEGER,

                old_payment_reference TEXT,

                new_payment_reference TEXT,

                reason TEXT,

                created_at TEXT
                    NOT NULL,

                CONSTRAINT fk_payment_audit_order

                    FOREIGN KEY (
                        order_id
                    )

                    REFERENCES orders(
                        id
                    )

                    ON DELETE RESTRICT
            )
            """
        )
        
        # ====================================================
        # PHASE 20I.3G
        # REFUND AUDIT INTEGRATION MIGRATION
        # ====================================================

        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            old_refund_request_status TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            new_refund_request_status TEXT
            """
        )

        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            old_refund_amount INTEGER
            """
        )


        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            new_refund_amount INTEGER
            """
        )


        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            old_refund_reference TEXT
            """
        )


        connection.execute(
            """
            ALTER TABLE payment_audit_logs
            ADD COLUMN IF NOT EXISTS
            new_refund_reference TEXT
            """
        )

        # ====================================================
        # PAYMENT AUDIT INDEXES
        # ====================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payment_audit_order

            ON payment_audit_logs(
                order_id,
                id DESC
            )
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payment_audit_created_at

            ON payment_audit_logs(
                created_at DESC
            )
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_payment_audit_action

            ON payment_audit_logs(
                action
            )
            """
        )
        
        # ----------------------------------------------------
        # BACKFILL HISTORICAL PAID TRANSACTIONS
        # ----------------------------------------------------

        connection.execute(
            """
            UPDATE orders

            SET
                payment_driver_confirmed_at = paid_at

            WHERE
                payment_status = ?
                AND paid_at IS NOT NULL
                AND payment_driver_confirmed_at IS NULL
            """,
            (
                PAYMENT_STATUS_PAID,
            )
        )
        
        # ====================================================
        # PHASE 20I.3
        # REFUND INDEX
        # ====================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_payment_refunded_at

            ON orders(
                payment_refunded_at DESC
            )

            WHERE payment_refunded_at IS NOT NULL
            """
        )
        
        # ====================================================
        # PHASE 20I.3A.5
        # REFUND REQUEST INDEXES
        # ====================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_refund_request_status

            ON orders(
                payment_refund_request_status
            )
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_refund_requested_at

            ON orders(
                payment_refund_requested_at DESC
            )

            WHERE
                payment_refund_requested_at IS NOT NULL
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
        
        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_orders_review_token_hash

            ON orders(review_token_hash)

            WHERE review_token_hash IS NOT NULL
            """
        )


        # ====================================================
        # PHASE 20G.2
        # RECEIPT TOKEN INDEX
        # ====================================================

        connection.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
            idx_orders_receipt_token_hash

            ON orders(receipt_token_hash)

            WHERE receipt_token_hash IS NOT NULL
            """
        )
        
        # ============================================================
        # PHASE 20A
        # PAYMENT INDEXES
        # ============================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_payment_status

            ON orders(payment_status)
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_payment_method

            ON orders(payment_method)
            """
        )


        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_paid_at

            ON orders(paid_at)
            """
        )
        
        # ====================================================
        # PHASE 20I.4A
        # ACTIVE PAYMENT EXPIRY INDEX
        # ====================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_payment_expiry_active

            ON orders(
                payment_expires_at,
                id
            )

            WHERE
                payment_expires_at IS NOT NULL

                AND payment_status IN (
                    'MENUNGGU_PEMBAYARAN',
                    'MENUNGGU_KONFIRMASI'
                )
            """
        )


        # ====================================================
        # PHASE 20H.1
        # CANONICAL PAID PAYMENT HISTORY INDEX
        # ====================================================

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_orders_paid_payment_history

            ON orders(
                paid_at DESC,
                id DESC
            )

            WHERE
                status = 'SELESAI'
                AND payment_status = 'DIBAYAR'
                AND payment_amount IS NOT NULL
                AND payment_amount > 0
                AND paid_at IS NOT NULL
                AND payment_method IN (
                    'TUNAI',
                    'QRIS',
                    'TRANSFER_BANK'
                )
            """
        )


        connection.commit()


    except Exception:

        connection.rollback()

        raise


    finally:

        connection.close()

# ============================================================
# PHASE 20I.1
# PAYMENT AUDIT HELPERS
# ============================================================

def payment_audit_safe_integer(
    value
):

    if value is None:

        return None


    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return None


def build_payment_audit_snapshot(
    order
):

    if not order:

        return {
            "payment_method":
                None,

            "payment_status":
                None,

            "payment_amount":
                None,

            "payment_reference":
                None,

            "refund_request_status":
                None,

            "refund_amount":
                None,

            "refund_reference":
                None,
        }


    refund_request_status = str(
        order.get(
            "payment_refund_request_status"
        )
        or
        PAYMENT_REFUND_REQUEST_NONE
    ).strip().upper()


    return {
        "payment_method":
            order.get(
                "payment_method"
            ),

        "payment_status":
            order.get(
                "payment_status"
            ),

        "payment_amount":
            payment_audit_safe_integer(
                order.get(
                    "payment_amount"
                )
            ),

        "payment_reference":
            order.get(
                "payment_reference"
            ),

        "refund_request_status":
            refund_request_status,

        "refund_amount":
            payment_audit_safe_integer(
                order.get(
                    "payment_refund_amount"
                )
            ),

        "refund_reference":
            order.get(
                "payment_refund_reference"
            ),
    }
    
def normalize_payment_audit_reason(
    value
):

    reason = str(
        value
        or ""
    )


    # Hilangkan karakter kontrol.
    reason = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        reason
    )


    reason = (
        " ".join(
            reason
            .strip()
            .split()
        )
    )


    return reason[
        :PAYMENT_AUDIT_REASON_MAX_LENGTH
    ]
    
def generate_payment_audit_event_code(
    connection
):

    for _ in range(
        20
    ):

        event_code = (
            "PA-"
            +
            secrets.token_hex(
                PAYMENT_AUDIT_EVENT_CODE_BYTES
            ).upper()
        )


        existing = (
            connection.execute(
                """
                SELECT id

                FROM payment_audit_logs

                WHERE event_code = ?

                LIMIT 1
                """,
                (
                    event_code,
                )
            )
            .fetchone()
        )


        if not existing:

            return event_code


    raise RuntimeError(
        (
            "Gagal membuat "
            "payment audit event code."
        )
    )
 
def record_payment_audit_event(
    connection,
    order,
    action,
    actor_type,
    old_snapshot=None,
    new_snapshot=None,
    reason=""
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # ORDER
    # ========================================================

    try:

        order_id = int(
            order[
                "id"
            ]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):

        raise ValueError(
            "ID pesanan tidak valid."
        )


    order_code = str(
        order.get(
            "order_code"
        )
        or ""
    ).strip().upper()


    if not order_code:

        raise ValueError(
            "Kode pesanan tidak valid."
        )


    # ========================================================
    # ACTION
    # ========================================================

    action = str(
        action
        or ""
    ).strip().upper()


    if (
        action
        not in PAYMENT_AUDIT_ALLOWED_ACTIONS
    ):

        raise ValueError(
            "Jenis payment audit tidak valid."
        )


    # ========================================================
    # ACTOR
    # ========================================================

    actor_type = str(
        actor_type
        or ""
    ).strip().upper()


    if (
        actor_type
        not in PAYMENT_AUDIT_ALLOWED_ACTORS
    ):

        raise ValueError(
            "Actor payment audit tidak valid."
        )


    # ========================================================
    # SNAPSHOTS
    # ========================================================

    if old_snapshot is None:

        old_snapshot = (
            build_payment_audit_snapshot(
                order
            )
        )


    if new_snapshot is None:

        new_snapshot = dict(
            old_snapshot
        )


    # ========================================================
    # REASON
    # ========================================================

    reason = (
        normalize_payment_audit_reason(
            reason
        )
    )


    # ========================================================
    # EVENT
    # ========================================================

    event_code = (
        generate_payment_audit_event_code(
            connection
        )
    )


    created_at = (
        current_timestamp()
    )


    # ========================================================
    # INSERT
    #
    # Tidak melakukan commit di helper.
    #
    # Caller yang melakukan commit supaya perubahan payment
    # dan audit log berada di transaction yang sama.
    # ========================================================

    connection.execute(
    """
    INSERT INTO payment_audit_logs (

        event_code,

        order_id,

        order_code,

        action,

        actor_type,

        old_payment_method,

        new_payment_method,

        old_payment_status,

        new_payment_status,

        old_payment_amount,

        new_payment_amount,

        old_payment_reference,

        new_payment_reference,

        old_refund_request_status,

        new_refund_request_status,

        old_refund_amount,

        new_refund_amount,

        old_refund_reference,

        new_refund_reference,

        reason,

        created_at
    )

    VALUES (
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?
    )
    """,
    (
        event_code,

        order_id,

        order_code,

        action,

        actor_type,

        old_snapshot.get(
            "payment_method"
        ),

        new_snapshot.get(
            "payment_method"
        ),

        old_snapshot.get(
            "payment_status"
        ),

        new_snapshot.get(
            "payment_status"
        ),

        payment_audit_safe_integer(
            old_snapshot.get(
                "payment_amount"
            )
        ),

        payment_audit_safe_integer(
            new_snapshot.get(
                "payment_amount"
            )
        ),

        old_snapshot.get(
            "payment_reference"
        ),

        new_snapshot.get(
            "payment_reference"
        ),

        old_snapshot.get(
            "refund_request_status"
        ),

        new_snapshot.get(
            "refund_request_status"
        ),

        payment_audit_safe_integer(
            old_snapshot.get(
                "refund_amount"
            )
        ),

        payment_audit_safe_integer(
            new_snapshot.get(
                "refund_amount"
            )
        ),

        old_snapshot.get(
            "refund_reference"
        ),

        new_snapshot.get(
            "refund_reference"
        ),

        reason or None,

        created_at,
    )
)


    return {
        "event_code":
            event_code,

        "order_id":
            order_id,

        "order_code":
            order_code,

        "action":
            action,

        "actor_type":
            actor_type,

        "reason":
            reason,

        "created_at":
            created_at,
    }
    
def get_payment_audit_events(
    connection,
    order_id,
    limit=50
):

    try:

        order_id = int(
            order_id
        )

    except (
        TypeError,
        ValueError
    ):

        return []


    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 50


    limit = max(
        1,
        min(
            limit,
            100
        )
    )


    rows = (
        connection.execute(
            """
            SELECT

                id,

                event_code,

                order_id,

                order_code,

                action,

                actor_type,

                old_payment_method,

                new_payment_method,

                old_payment_status,

                new_payment_status,

                old_payment_amount,

                new_payment_amount,

                old_payment_reference,

                new_payment_reference,

                old_refund_request_status,

                new_refund_request_status,

                old_refund_amount,

                new_refund_amount,

                old_refund_reference,

                new_refund_reference,

                reason,

                created_at

            FROM payment_audit_logs

            WHERE order_id = ?

            ORDER BY
                id DESC

            LIMIT ?
            """,
            (
                order_id,
                limit,
            )
        )
        .fetchall()
    )


    return [
        {
            "id":
                int(
                    row[
                        "id"
                    ]
                ),

            "event_code":
                row[
                    "event_code"
                ],

            "order_id":
                int(
                    row[
                        "order_id"
                    ]
                ),

            "order_code":
                row[
                    "order_code"
                ],

            "action":
                row[
                    "action"
                ],

            "actor_type":
                row[
                    "actor_type"
                ],

            "old_payment_method":
                row[
                    "old_payment_method"
                ],

            "new_payment_method":
                row[
                    "new_payment_method"
                ],

            "old_payment_status":
                row[
                    "old_payment_status"
                ],

            "new_payment_status":
                row[
                    "new_payment_status"
                ],

            "old_payment_amount":
                payment_audit_safe_integer(
                    row[
                        "old_payment_amount"
                    ]
                ),

            "new_payment_amount":
                payment_audit_safe_integer(
                    row[
                        "new_payment_amount"
                    ]
                ),

            "old_payment_reference":
                row[
                    "old_payment_reference"
                ],

            "new_payment_reference":
                row[
                    "new_payment_reference"
                ],

            "reason":
                row[
                    "reason"
                ],
                
            "old_refund_request_status":
                row[
                    "old_refund_request_status"
                ],

            "new_refund_request_status":
                row[
                    "new_refund_request_status"
                ],

            "old_refund_amount":
                payment_audit_safe_integer(
                    row[
                        "old_refund_amount"
                    ]
                ),

            "new_refund_amount":
                payment_audit_safe_integer(
                    row[
                        "new_refund_amount"
                    ]
                ),

            "old_refund_reference":
                row[
                    "old_refund_reference"
                ],

            "new_refund_reference":
                row[
                    "new_refund_reference"
                ],

            "created_at":
                row[
                    "created_at"
                ],
        }

        for row
        in rows
    ]
    
# ============================================================
# PHASE 20I.3
# PAYMENT REFUND HELPERS
# ============================================================

def normalize_payment_refund_reason(
    value
):

    reason = str(
        value
        or ""
    )


    reason = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        reason
    )


    reason = " ".join(
        reason
        .strip()
        .split()
    )


    if (
        len(
            reason
        )
        <
        PAYMENT_REFUND_REASON_MIN_LENGTH
    ):

        raise ValueError(
            (
                "Alasan pengembalian pembayaran "
                f"minimal "
                f"{PAYMENT_REFUND_REASON_MIN_LENGTH} "
                "karakter."
            )
        )


    return reason[
        :PAYMENT_REFUND_REASON_MAX_LENGTH
    ]
    
def normalize_payment_refund_reference(
    value
):

    reference = str(
        value
        or ""
    )


    reference = re.sub(
        r"[\x00-\x1F\x7F]",
        "",
        reference
    )


    reference = " ".join(
        reference
        .strip()
        .split()
    )


    return reference[
        :PAYMENT_REFUND_REFERENCE_MAX_LENGTH
    ]
    
def refund_paid_payment(
    connection,
    order,
    reason,
    refund_reference="",
    audit_new_refund_request_status=None
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # ORDER MUST BE COMPLETED
    # ========================================================

    order_status = str(
        order.get(
            "status"
        )
        or ""
    ).strip().upper()


    if (
        order_status
        != STATUS_COMPLETED
    ):

        raise ValueError(
            (
                "Pengembalian pembayaran "
                "hanya dapat dilakukan untuk "
                "perjalanan yang sudah selesai."
            )
        )


    # ========================================================
    # CURRENT PAYMENT STATUS
    # ========================================================

    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        payment_status
        ==
        PAYMENT_STATUS_REFUNDED
    ):

        return {
            "already_refunded":
                True,

            "refund": {
                "status":
                    PAYMENT_STATUS_REFUNDED,

                "amount":
                    payment_audit_safe_integer(
                        order.get(
                            "payment_refund_amount"
                        )
                    )
                    or
                    payment_audit_safe_integer(
                        order.get(
                            "payment_amount"
                        )
                    )
                    or 0,

                "reason":
                    order.get(
                        "payment_refund_reason"
                    ),

                "reference":
                    order.get(
                        "payment_refund_reference"
                    ),

                "refunded_at":
                    order.get(
                        "payment_refunded_at"
                    ),
            },
        }


    # ========================================================
    # MUST CURRENTLY BE PAID
    # ========================================================

    if (
        payment_status
        != PAYMENT_STATUS_PAID
    ):

        raise ValueError(
            (
                "Hanya pembayaran dengan status "
                "DIBAYAR yang dapat dikembalikan."
            )
        )


    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    payment_method = str(
        order.get(
            "payment_method"
        )
        or ""
    ).strip().upper()


    if (
        payment_method
        not in PAYMENT_ALLOWED_METHODS
    ):

        raise ValueError(
            "Metode pembayaran tidak valid."
        )


    # ========================================================
    # PAID TIMESTAMP
    # ========================================================

    if not order.get(
        "paid_at"
    ):

        raise ValueError(
            (
                "Pembayaran tidak memiliki "
                "waktu pembayaran yang valid."
            )
        )


    # ========================================================
    # FULL REFUND AMOUNT
    # ========================================================

    payment_amount = (
        get_verified_payment_amount(
            order
        )
    )


    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    reason = (
        normalize_payment_refund_reason(
            reason
        )
    )


    refund_reference = (
        normalize_payment_refund_reference(
            refund_reference
        )
    )


    # ========================================================
    # OPTIONAL REFUND REQUEST AUDIT TARGET
    # ========================================================

    if (
        audit_new_refund_request_status
        is not None
    ):

        audit_new_refund_request_status = str(
            audit_new_refund_request_status
        ).strip().upper()


        if (
            audit_new_refund_request_status
            not in
            PAYMENT_REFUND_REQUEST_ALLOWED_STATUSES
        ):

            raise ValueError(
                (
                    "Status refund request tujuan "
                    "untuk audit tidak valid."
                )
            )


    # ========================================================
    # PAYMENT TRANSITION
    # DIBAYAR -> DIKEMBALIKAN
    # ========================================================

    transition = (
        validate_payment_status_transition(
            order,
            PAYMENT_STATUS_REFUNDED,
            PAYMENT_AUDIT_ACTOR_DRIVER
        )
    )


    # ========================================================
    # OLD AUDIT SNAPSHOT
    # ========================================================

    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )


    refunded_at = (
        current_timestamp()
    )


    # ========================================================
    # ATOMIC UPDATE
    # ========================================================

    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_status = ?,

                payment_refunded_at = ?,

                payment_refund_amount = ?,

                payment_refund_reason = ?,

                payment_refund_reference = ?,

                payment_updated_at = ?

            WHERE
                id = ?

                AND payment_status = ?
            """,
            (
                PAYMENT_STATUS_REFUNDED,

                refunded_at,

                payment_amount,

                reason,

                (
                    refund_reference
                    or None
                ),

                refunded_at,

                order[
                    "id"
                ],

                transition[
                    "old_status"
                ],
            )
        )
    )


    ensure_payment_transition_updated(
        update_cursor,
        order.get(
            "order_code"
        )
    )


    # ========================================================
    # PHASE 20I.3G
    # NEW AUDIT SNAPSHOT
    # ========================================================

    new_snapshot = dict(
        old_snapshot
    )


    new_snapshot[
        "payment_status"
    ] = (
        PAYMENT_STATUS_REFUNDED
    )


    new_snapshot[
        "refund_amount"
    ] = (
        payment_amount
    )


    new_snapshot[
        "refund_reference"
    ] = (
        refund_reference
        or None
    )


    if (
        audit_new_refund_request_status
        is not None
    ):

        new_snapshot[
            "refund_request_status"
        ] = (
            audit_new_refund_request_status
        )


    # ========================================================
    # AUDIT
    # ========================================================

    record_payment_audit_event(
        connection,
        order,

        action=
            PAYMENT_AUDIT_ACTION_REFUND,

        actor_type=
            PAYMENT_AUDIT_ACTOR_DRIVER,

        old_snapshot=
            old_snapshot,

        new_snapshot=
            new_snapshot,

        reason=
            reason
    )


    # ========================================================
    # RESULT
    #
    # WAJIB RETURN DICTIONARY.
    # Jangan hapus bagian ini.
    # ========================================================

    return {
        "already_refunded":
            False,

        "refund": {
            "status":
                PAYMENT_STATUS_REFUNDED,

            "amount":
                payment_amount,

            "reason":
                reason,

            "reference":
                (
                    refund_reference
                    or None
                ),

            "refunded_at":
                refunded_at,
        },
    }
    
# ============================================================
# PHASE 20I.3A
# REFUND REQUEST HELPERS
# ============================================================

def normalize_payment_refund_request_status(
    value
):

    status = str(
        value
        or
        PAYMENT_REFUND_REQUEST_NONE
    ).strip().upper()


    if (
        status
        not in PAYMENT_REFUND_REQUEST_ALLOWED_STATUSES
    ):

        return (
            PAYMENT_REFUND_REQUEST_NONE
        )


    return status

def normalize_payment_refund_request_reason(
    value
):

    reason = str(
        value
        or ""
    )


    reason = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        reason
    )


    reason = " ".join(
        reason
        .strip()
        .split()
    )


    if (
        len(reason)
        <
        PAYMENT_REFUND_REQUEST_REASON_MIN_LENGTH
    ):

        raise ValueError(
            (
                "Alasan pengembalian dana minimal "
                f"{PAYMENT_REFUND_REQUEST_REASON_MIN_LENGTH} "
                "karakter."
            )
        )


    return reason[
        :PAYMENT_REFUND_REQUEST_REASON_MAX_LENGTH
    ]
    
def normalize_payment_refund_rejection_reason(
    value
):

    reason = str(
        value
        or ""
    )


    reason = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        reason
    )


    reason = " ".join(
        reason
        .strip()
        .split()
    )


    if (
        len(reason)
        <
        PAYMENT_REFUND_REJECTION_REASON_MIN_LENGTH
    ):

        raise ValueError(
            (
                "Alasan penolakan refund minimal "
                f"{PAYMENT_REFUND_REJECTION_REASON_MIN_LENGTH} "
                "karakter."
            )
        )


    return reason[
        :PAYMENT_REFUND_REJECTION_REASON_MAX_LENGTH
    ]
    
def get_payment_refund_request_state(
    order
):

    if not order:

        return {
            "status":
                PAYMENT_REFUND_REQUEST_NONE,

            "requested_at":
                None,

            "request_reason":
                None,

            "reviewed_at":
                None,

            "rejection_reason":
                None,
        }


    return {
        "status":
            normalize_payment_refund_request_status(
                order.get(
                    "payment_refund_request_status"
                )
            ),

        "requested_at":
            order.get(
                "payment_refund_requested_at"
            ),

        "request_reason":
            order.get(
                "payment_refund_request_reason"
            ),

        "reviewed_at":
            order.get(
                "payment_refund_reviewed_at"
            ),

        "rejection_reason":
            order.get(
                "payment_refund_rejection_reason"
            ),
    }
    
def get_payment_refund_capabilities(
    order
):

    if not order:

        return {
            "can_customer_request":
                False,

            "can_driver_review":
                False,

            "is_pending":
                False,

            "is_approved":
                False,

            "is_rejected":
                False,

            "is_refunded":
                False,
        }


    # ========================================================
    # ORDER STATUS
    # ========================================================

    order_status = str(
        order.get(
            "status"
        )
        or ""
    ).strip().upper()


    # ========================================================
    # PAYMENT STATUS
    # ========================================================

    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # REFUND REQUEST STATUS
    # ========================================================

    request_status = (
        normalize_payment_refund_request_status(
            order.get(
                "payment_refund_request_status"
            )
        )
    )


    # ========================================================
    # STATE FLAGS
    # ========================================================

    is_completed = (
        order_status
        ==
        STATUS_COMPLETED
    )


    is_paid = (
        payment_status
        ==
        PAYMENT_STATUS_PAID
    )


    is_refunded = (
        payment_status
        ==
        PAYMENT_STATUS_REFUNDED
    )


    is_pending = (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_PENDING
    )


    is_approved = (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_APPROVED
    )


    is_rejected = (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_REJECTED
    )


    # ========================================================
    # CUSTOMER
    #
    # Customer hanya dapat mengajukan refund jika:
    #
    # - perjalanan SELESAI
    # - pembayaran DIBAYAR
    # - belum pernah membuat refund request
    # ========================================================

    can_customer_request = (
        is_completed
        and
        is_paid
        and
        request_status
        ==
        PAYMENT_REFUND_REQUEST_NONE
    )


    # ========================================================
    # DRIVER
    #
    # Driver hanya review jika:
    #
    # - perjalanan SELESAI
    # - pembayaran masih DIBAYAR
    # - refund request PENDING
    # ========================================================

    can_driver_review = (
        is_completed
        and
        is_paid
        and
        is_pending
    )


    return {
        "can_customer_request":
            can_customer_request,

        "can_driver_review":
            can_driver_review,

        "is_pending":
            is_pending,

        "is_approved":
            is_approved,

        "is_rejected":
            is_rejected,

        "is_refunded":
            is_refunded,
    }
    
def payment_refund_request_payload(
    order
):

    state = (
        get_payment_refund_request_state(
            order
        )
    )


    capabilities = (
        get_payment_refund_capabilities(
            order
        )
    )


    return {
        "status":
            state[
                "status"
            ],

        "requested_at":
            state[
                "requested_at"
            ],

        "request_reason":
            state[
                "request_reason"
            ],

        "reviewed_at":
            state[
                "reviewed_at"
            ],

        "rejection_reason":
            state[
                "rejection_reason"
            ],

        "can_customer_request":
            capabilities[
                "can_customer_request"
            ],

        "can_driver_review":
            capabilities[
                "can_driver_review"
            ],

        "is_pending":
            capabilities[
                "is_pending"
            ],

        "is_approved":
            capabilities[
                "is_approved"
            ],

        "is_rejected":
            capabilities[
                "is_rejected"
            ],

        "is_refunded":
            capabilities[
                "is_refunded"
            ],
    }
    
def validate_payment_refund_request_state(
    order
):

    if not order:

        raise ValueError(
            "Data pesanan tidak ditemukan."
        )


    # ========================================================
    # ORDER STATUS
    # ========================================================

    order_status = str(
        order.get(
            "status"
        )
        or ""
    ).strip().upper()


    # ========================================================
    # PAYMENT STATUS
    # ========================================================

    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # REFUND REQUEST STATUS
    # Strict: nilai ilegal tidak boleh diam-diam menjadi NONE.
    # ========================================================

    request_status = str(
        order.get(
            "payment_refund_request_status"
        )
        or PAYMENT_REFUND_REQUEST_NONE
    ).strip().upper()


    if (
        request_status
        not in PAYMENT_REFUND_REQUEST_ALLOWED_STATUSES
    ):

        raise ValueError(
            (
                "Status refund request tidak valid: "
                f"{request_status}."
            )
        )


    # ========================================================
    # REQUEST METADATA
    # ========================================================

    requested_at = (
        order.get(
            "payment_refund_requested_at"
        )
    )


    request_reason = str(
        order.get(
            "payment_refund_request_reason"
        )
        or ""
    ).strip()


    reviewed_at = (
        order.get(
            "payment_refund_reviewed_at"
        )
    )


    rejection_reason = str(
        order.get(
            "payment_refund_rejection_reason"
        )
        or ""
    ).strip()


    # ========================================================
    # ACTUAL REFUND DATA
    # ========================================================

    refunded_at = (
        order.get(
            "payment_refunded_at"
        )
    )


    refund_amount = (
        payment_audit_safe_integer(
            order.get(
                "payment_refund_amount"
            )
        )
    )


    payment_amount = (
        payment_audit_safe_integer(
            order.get(
                "payment_amount"
            )
        )
    )


    # ========================================================
    # NONE
    #
    # Tidak ada customer refund request. Refund manual/legacy
    # tetap boleh ada, tetapi metadata REQUEST tidak boleh ada.
    # ========================================================

    if (
        request_status
        == PAYMENT_REFUND_REQUEST_NONE
    ):

        if (
            requested_at
            or request_reason
            or reviewed_at
            or rejection_reason
        ):

            raise ValueError(
                (
                    "Refund request NONE tidak boleh "
                    "memiliki metadata permintaan refund."
                )
            )


        return {
            "valid":
                True,

            "order_status":
                order_status,

            "payment_status":
                payment_status,

            "refund_request_status":
                request_status,
        }


    # ========================================================
    # CUSTOMER REFUND REQUEST HANYA SETELAH TRIP SELESAI
    # ========================================================

    if (
        order_status
        != STATUS_COMPLETED
    ):

        raise ValueError(
            (
                "Refund request tidak valid: "
                "perjalanan belum selesai."
            )
        )


    # ========================================================
    # REQUEST DATA WAJIB
    # ========================================================

    if not requested_at:

        raise ValueError(
            (
                "Refund request tidak memiliki "
                "waktu pengajuan."
            )
        )


    if (
        len(
            request_reason
        )
        < PAYMENT_REFUND_REQUEST_REASON_MIN_LENGTH
    ):

        raise ValueError(
            (
                "Refund request tidak memiliki "
                "alasan pengajuan yang valid."
            )
        )


    # ========================================================
    # PENDING
    # ========================================================

    if (
        request_status
        == PAYMENT_REFUND_REQUEST_PENDING
    ):

        if (
            payment_status
            != PAYMENT_STATUS_PAID
        ):

            raise ValueError(
                (
                    "Refund request PENDING hanya valid "
                    "untuk pembayaran DIBAYAR."
                )
            )


        if reviewed_at:

            raise ValueError(
                (
                    "Refund request PENDING tidak boleh "
                    "sudah memiliki waktu review."
                )
            )


        if rejection_reason:

            raise ValueError(
                (
                    "Refund request PENDING tidak boleh "
                    "memiliki alasan penolakan."
                )
            )


        if refunded_at:

            raise ValueError(
                (
                    "Refund request PENDING tidak boleh "
                    "sudah memiliki waktu refund."
                )
            )


        if refund_amount is not None:

            raise ValueError(
                (
                    "Refund request PENDING tidak boleh "
                    "sudah memiliki nominal refund."
                )
            )


    # ========================================================
    # REJECTED
    # ========================================================

    elif (
        request_status
        == PAYMENT_REFUND_REQUEST_REJECTED
    ):

        if (
            payment_status
            != PAYMENT_STATUS_PAID
        ):

            raise ValueError(
                (
                    "Refund request REJECTED hanya valid "
                    "jika pembayaran tetap DIBAYAR."
                )
            )


        if not reviewed_at:

            raise ValueError(
                (
                    "Refund request REJECTED tidak memiliki "
                    "waktu review driver."
                )
            )


        if (
            len(
                rejection_reason
            )
            < PAYMENT_REFUND_REJECTION_REASON_MIN_LENGTH
        ):

            raise ValueError(
                (
                    "Refund request REJECTED tidak memiliki "
                    "alasan penolakan yang valid."
                )
            )


        if refunded_at:

            raise ValueError(
                (
                    "Refund request REJECTED tidak boleh "
                    "memiliki waktu refund."
                )
            )


        if refund_amount is not None:

            raise ValueError(
                (
                    "Refund request REJECTED tidak boleh "
                    "memiliki nominal refund."
                )
            )


    # ========================================================
    # APPROVED
    # ========================================================

    elif (
        request_status
        == PAYMENT_REFUND_REQUEST_APPROVED
    ):

        if (
            payment_status
            != PAYMENT_STATUS_REFUNDED
        ):

            raise ValueError(
                (
                    "Refund request APPROVED hanya valid "
                    "jika payment_status DIKEMBALIKAN."
                )
            )


        if not reviewed_at:

            raise ValueError(
                (
                    "Refund APPROVED tidak memiliki "
                    "waktu review driver."
                )
            )


        if rejection_reason:

            raise ValueError(
                (
                    "Refund APPROVED tidak boleh "
                    "memiliki alasan penolakan."
                )
            )


        if not refunded_at:

            raise ValueError(
                (
                    "Refund APPROVED tidak memiliki "
                    "waktu pengembalian dana."
                )
            )


        if (
            refund_amount is None
            or refund_amount <= 0
        ):

            raise ValueError(
                (
                    "Refund APPROVED tidak memiliki "
                    "nominal refund yang valid."
                )
            )


        if (
            payment_amount is None
            or payment_amount <= 0
        ):

            raise ValueError(
                (
                    "Refund APPROVED tidak memiliki "
                    "nominal pembayaran asli yang valid."
                )
            )


        if (
            refund_amount
            != payment_amount
        ):

            raise ValueError(
                (
                    "Nominal refund harus sama dengan "
                    "nominal pembayaran untuk full refund."
                )
            )


    else:

        raise ValueError(
            "Status refund request tidak dikenali."
        )


    return {
        "valid":
            True,

        "order_status":
            order_status,

        "payment_status":
            payment_status,

        "refund_request_status":
            request_status,
    }

# ============================================================
# PHASE 20I.3B
# CUSTOMER REFUND REQUEST
# ============================================================

def submit_customer_refund_request(
    connection,
    order,
    reason
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # CURRENT REFUND REQUEST STATE
    # ========================================================

    request_status = (
        normalize_payment_refund_request_status(
            order.get(
                "payment_refund_request_status"
            )
        )
    )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_PENDING
    ):

        return {
            "already_requested":
                True,

            "refund_request":
                payment_refund_request_payload(
                    order
                ),
        }


    # ========================================================
    # APPROVED
    # ========================================================

    if (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_APPROVED
    ):

        raise ValueError(
            "Pengembalian dana sudah diproses."
        )


    # ========================================================
    # REJECTED
    #
    # Untuk sekarang tidak boleh mengajukan ulang.
    # ========================================================

    if (
        request_status
        ==
        PAYMENT_REFUND_REQUEST_REJECTED
    ):

        raise ValueError(
            (
                "Permintaan pengembalian dana "
                "sebelumnya sudah ditolak."
            )
        )


    # ========================================================
    # CAPABILITY
    # ========================================================

    capabilities = (
        get_payment_refund_capabilities(
            order
        )
    )


    if not capabilities[
        "can_customer_request"
    ]:

        raise ValueError(
            (
                "Pesanan ini belum memenuhi syarat "
                "untuk pengembalian dana."
            )
        )


    # ========================================================
    # PAYMENT MUST REALLY HAVE BEEN PAID
    # ========================================================

    if not order.get(
        "paid_at"
    ):

        raise ValueError(
            (
                "Pembayaran belum memiliki "
                "konfirmasi pembayaran yang valid."
            )
        )


    # ========================================================
    # PAYMENT AMOUNT INTEGRITY
    # ========================================================

    get_verified_payment_amount(
        order
    )


    # ========================================================
    # REASON
    # ========================================================

    reason = (
        normalize_payment_refund_request_reason(
            reason
        )
    )


    # ========================================================
    # OLD PAYMENT SNAPSHOT
    # ========================================================

    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )


    requested_at = (
        current_timestamp()
    )


    # ========================================================
    # ATOMIC UPDATE
    #
    # payment_status TIDAK berubah.
    # ========================================================

    cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status = ?,

                payment_refund_requested_at = ?,

                payment_refund_request_reason = ?,

                payment_refund_reviewed_at = NULL,

                payment_refund_rejection_reason = NULL

            WHERE
                id = ?

                AND status = ?

                AND payment_status = ?

                AND payment_refund_request_status = ?
            """,
            (
                PAYMENT_REFUND_REQUEST_PENDING,

                requested_at,

                reason,

                order[
                    "id"
                ],

                STATUS_COMPLETED,

                PAYMENT_STATUS_PAID,

                PAYMENT_REFUND_REQUEST_NONE,
            )
        )
    )


    # ========================================================
    # CONCURRENT / DOUBLE REQUEST PROTECTION
    # ========================================================

    affected_rows = int(
        cursor.rowcount
        or 0
    )


    if affected_rows != 1:

        latest_order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE id = ?

                LIMIT 1
                """,
                (
                    order[
                        "id"
                    ],
                )
            )
            .fetchone()
        )


        if (
            latest_order
            and
            normalize_payment_refund_request_status(
                latest_order.get(
                    "payment_refund_request_status"
                )
            )
            ==
            PAYMENT_REFUND_REQUEST_PENDING
        ):

            return {
                "already_requested":
                    True,

                "refund_request":
                    payment_refund_request_payload(
                        latest_order
                    ),
            }


        raise RuntimeError(
            (
                "Status pesanan berubah saat "
                "permintaan refund diproses. "
                "Silakan muat ulang halaman."
            )
        )


    # ========================================================
    # BUILD UPDATED ORDER FOR VALIDATION
    # ========================================================

    updated_order = dict(
        order
    )


    updated_order[
        "payment_refund_request_status"
    ] = PAYMENT_REFUND_REQUEST_PENDING


    updated_order[
        "payment_refund_requested_at"
    ] = requested_at


    updated_order[
        "payment_refund_request_reason"
    ] = reason


    updated_order[
        "payment_refund_reviewed_at"
    ] = None


    updated_order[
        "payment_refund_rejection_reason"
    ] = None


    # ========================================================
    # STATE VALIDATION
    # ========================================================

    validate_payment_refund_request_state(
        updated_order
    )


    # ========================================================
    # PHASE 20I.3G
    # REFUND REQUEST AUDIT SNAPSHOT
    #
    # Customer refund request:
    # NONE -> PENDING
    #
    # Payment tetap:
    # DIBAYAR -> DIBAYAR
    # ========================================================

    new_snapshot = (
        build_payment_audit_snapshot(
            updated_order
        )
    )


    record_payment_audit_event(
        connection,
        order,

        action=
            PAYMENT_AUDIT_ACTION_REFUND_REQUESTED,

        actor_type=
            PAYMENT_AUDIT_ACTOR_CUSTOMER,

        old_snapshot=
            old_snapshot,

        new_snapshot=
            new_snapshot,

        reason=
            reason
    )


    return {
        "already_requested":
            False,

        "refund_request":
            payment_refund_request_payload(
                updated_order
            ),
    }
    
# ============================================================
# PHASE 20I.3D
# DRIVER CONFIRM CUSTOMER REFUND
# ============================================================

def confirm_customer_refund_request(
    connection,
    order,
    refund_reference=""
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    request_status = (
        normalize_payment_refund_request_status(
            order.get(
                "payment_refund_request_status"
            )
        )
    )


    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        request_status
        == PAYMENT_REFUND_REQUEST_APPROVED
        and payment_status
        == PAYMENT_STATUS_REFUNDED
    ):

        return {
            "already_confirmed":
                True,

            "refund_request":
                payment_refund_request_payload(
                    order
                ),

            "refund": {
                "status":
                    PAYMENT_STATUS_REFUNDED,

                "amount":
                    payment_audit_safe_integer(
                        order.get(
                            "payment_refund_amount"
                        )
                    )
                    or 0,

                "reason":
                    order.get(
                        "payment_refund_reason"
                    ),

                "reference":
                    order.get(
                        "payment_refund_reference"
                    ),

                "refunded_at":
                    order.get(
                        "payment_refunded_at"
                    ),
            },
        }


    if (
        request_status
        != PAYMENT_REFUND_REQUEST_PENDING
    ):

        raise ValueError(
            (
                "Permintaan pengembalian dana "
                "tidak sedang menunggu review."
            )
        )


    validate_payment_refund_request_state(
        order
    )


    capabilities = (
        get_payment_refund_capabilities(
            order
        )
    )


    if not capabilities[
        "can_driver_review"
    ]:

        raise ValueError(
            (
                "Permintaan refund ini tidak dapat "
                "diproses pada kondisi sekarang."
            )
        )


    refund_reason = (
        normalize_payment_refund_request_reason(
            order.get(
                "payment_refund_request_reason"
            )
        )
    )


    refund_reference = (
        normalize_payment_refund_reference(
            refund_reference
        )
    )


    payment_amount = (
        get_verified_payment_amount(
            order
        )
    )


    # ========================================================
    # ACTUAL REFUND
    # DIBAYAR -> DIKEMBALIKAN + PAYMENT_REFUNDED AUDIT
    # Belum commit.
    # ========================================================

    refund_result = (
        refund_paid_payment(
            connection,
            order,

            reason=
                refund_reason,

            refund_reference=
                refund_reference,

            audit_new_refund_request_status=
                PAYMENT_REFUND_REQUEST_APPROVED
        )
    )


    if not isinstance(
        refund_result,
        dict
    ):

        raise RuntimeError(
            (
                "Hasil proses pengembalian dana "
                "tidak valid. Transaksi dibatalkan."
            )
        )


    if refund_result.get(
        "already_refunded"
    ):

        raise RuntimeError(
            (
                "Pembayaran sudah berubah menjadi "
                "dikembalikan. Muat ulang halaman."
            )
        )


    refunded_at = (
        refund_result[
            "refund"
        ][
            "refunded_at"
        ]
    )


    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status = ?,
                payment_refund_reviewed_at = ?,
                payment_refund_rejection_reason = NULL

            WHERE
                id = ?
                AND payment_status = ?
                AND payment_refund_request_status = ?
            """,
            (
                PAYMENT_REFUND_REQUEST_APPROVED,
                refunded_at,
                order[
                    "id"
                ],
                PAYMENT_STATUS_REFUNDED,
                PAYMENT_REFUND_REQUEST_PENDING,
            )
        )
    )


    affected_rows = int(
        update_cursor.rowcount
        or 0
    )


    if affected_rows != 1:

        raise RuntimeError(
            (
                "Status refund request berubah "
                "saat proses pengembalian dana. "
                "Silakan muat ulang halaman."
            )
        )


    updated_order = (
        connection.execute(
            """
            SELECT *

            FROM orders

            WHERE id = ?

            LIMIT 1
            """,
            (
                order[
                    "id"
                ],
            )
        )
        .fetchone()
    )


    if not updated_order:

        raise RuntimeError(
            (
                "Data pesanan tidak ditemukan "
                "setelah refund diproses."
            )
        )


    validate_payment_refund_request_state(
        updated_order
    )


    final_refund_amount = (
        payment_audit_safe_integer(
            updated_order.get(
                "payment_refund_amount"
            )
        )
    )


    if (
        final_refund_amount
        != payment_amount
    ):

        raise RuntimeError(
            (
                "Nominal refund akhir tidak sesuai "
                "dengan pembayaran."
            )
        )


    return {
        "already_confirmed":
            False,

        "refund_request":
            payment_refund_request_payload(
                updated_order
            ),

        "refund":
            refund_result[
                "refund"
            ],
    }


# ============================================================
# PHASE 20I.3E
# DRIVER REJECT CUSTOMER REFUND
# ============================================================

def reject_customer_refund_request(
    connection,
    order,
    rejection_reason
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    request_status = (
        normalize_payment_refund_request_status(
            order.get(
                "payment_refund_request_status"
            )
        )
    )


    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        request_status
        == PAYMENT_REFUND_REQUEST_REJECTED
        and payment_status
        == PAYMENT_STATUS_PAID
    ):

        return {
            "already_rejected":
                True,

            "refund_request":
                payment_refund_request_payload(
                    order
                ),
        }


    if (
        request_status
        != PAYMENT_REFUND_REQUEST_PENDING
    ):

        raise ValueError(
            (
                "Permintaan pengembalian dana "
                "tidak sedang menunggu review."
            )
        )


    if (
        payment_status
        != PAYMENT_STATUS_PAID
    ):

        raise ValueError(
            (
                "Permintaan refund hanya dapat ditolak "
                "ketika pembayaran masih berstatus DIBAYAR."
            )
        )


    validate_payment_refund_request_state(
        order
    )


    capabilities = (
        get_payment_refund_capabilities(
            order
        )
    )


    if not capabilities[
        "can_driver_review"
    ]:

        raise ValueError(
            (
                "Permintaan refund ini tidak dapat "
                "diproses pada kondisi sekarang."
            )
        )


    rejection_reason = (
        normalize_payment_refund_rejection_reason(
            rejection_reason
        )
    )


    reviewed_at = (
        current_timestamp()
    )


    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )


    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_refund_request_status = ?,
                payment_refund_reviewed_at = ?,
                payment_refund_rejection_reason = ?

            WHERE
                id = ?
                AND status = ?
                AND payment_status = ?
                AND payment_refund_request_status = ?
            """,
            (
                PAYMENT_REFUND_REQUEST_REJECTED,
                reviewed_at,
                rejection_reason,
                order[
                    "id"
                ],
                STATUS_COMPLETED,
                PAYMENT_STATUS_PAID,
                PAYMENT_REFUND_REQUEST_PENDING,
            )
        )
    )


    affected_rows = int(
        update_cursor.rowcount
        or 0
    )


    if affected_rows != 1:

        latest_order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE id = ?

                LIMIT 1
                """,
                (
                    order[
                        "id"
                    ],
                )
            )
            .fetchone()
        )


        if (
            latest_order
            and normalize_payment_refund_request_status(
                latest_order.get(
                    "payment_refund_request_status"
                )
            )
            == PAYMENT_REFUND_REQUEST_REJECTED
            and get_effective_payment_status(
                latest_order
            )
            == PAYMENT_STATUS_PAID
        ):

            return {
                "already_rejected":
                    True,

                "refund_request":
                    payment_refund_request_payload(
                        latest_order
                    ),
            }


        raise RuntimeError(
            (
                "Status refund request berubah saat "
                "penolakan diproses. "
                "Silakan muat ulang halaman."
            )
        )


    updated_order = (
        connection.execute(
            """
            SELECT *

            FROM orders

            WHERE id = ?

            LIMIT 1
            """,
            (
                order[
                    "id"
                ],
            )
        )
        .fetchone()
    )


    if not updated_order:

        raise RuntimeError(
            (
                "Data pesanan tidak ditemukan "
                "setelah permintaan ditolak."
            )
        )


    validate_payment_refund_request_state(
        updated_order
    )


    new_snapshot = (
        build_payment_audit_snapshot(
            updated_order
        )
    )


    record_payment_audit_event(
        connection,
        updated_order,
        action=PAYMENT_AUDIT_ACTION_REFUND_REJECTED,
        actor_type=PAYMENT_AUDIT_ACTOR_DRIVER,
        old_snapshot=old_snapshot,
        new_snapshot=new_snapshot,
        reason=rejection_reason
    )


    return {
        "already_rejected":
            False,

        "refund_request":
            payment_refund_request_payload(
                updated_order
            ),
    }

def get_invalid_payment_refund_request_states(
    connection,
    limit=100
):

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 100


    limit = max(
        1,
        min(
            limit,
            500
        )
    )


    # ========================================================
    # Ambil semua order yang mempunyai refund-request state
    # atau refund-request metadata.
    #
    # NONE murni tidak perlu diperiksa.
    # ========================================================

    rows = (
        connection.execute(
            """
            SELECT *

            FROM orders

            WHERE
                payment_refund_request_status
                <> ?

                OR payment_refund_requested_at
                IS NOT NULL

                OR NULLIF(
                    TRIM(
                        COALESCE(
                            payment_refund_request_reason,
                            ''
                        )
                    ),
                    ''
                )
                IS NOT NULL

                OR payment_refund_reviewed_at
                IS NOT NULL

                OR NULLIF(
                    TRIM(
                        COALESCE(
                            payment_refund_rejection_reason,
                            ''
                        )
                    ),
                    ''
                )
                IS NOT NULL

            ORDER BY id DESC

            LIMIT ?
            """,
            (
                PAYMENT_REFUND_REQUEST_NONE,
                limit,
            )
        )
        .fetchall()
    )


    invalid_rows = []


    for order in rows:

        try:

            validate_payment_refund_request_state(
                order
            )


        except ValueError as error:

            invalid_rows.append(
                {
                    "id":
                        int(
                            order[
                                "id"
                            ]
                        ),

                    "order_code":
                        order[
                            "order_code"
                        ],

                    "status":
                        order.get(
                            "status"
                        ),

                    "payment_status":
                        order.get(
                            "payment_status"
                        ),

                    "refund_request_status":
                        order.get(
                            "payment_refund_request_status"
                        ),

                    "error":
                        str(
                            error
                        ),
                }
            )


    return invalid_rows    

# ============================================================
# PHASE 20I.3C
# DRIVER REFUND REQUEST REVIEW
# ============================================================

def get_driver_pending_refund_requests(
    connection,
    limit=50
):

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 50


    limit = max(
        1,
        min(
            limit,
            100
        )
    )


    rows = (
        connection.execute(
            """
            SELECT

                id,
                order_code,

                customer_name,
                whatsapp,

                pickup,
                destination,

                fare,
                status,

                payment_method,
                payment_status,
                payment_amount,
                paid_at,

                payment_refund_request_status,
                payment_refund_requested_at,
                payment_refund_request_reason,
                payment_refund_reviewed_at,
                payment_refund_rejection_reason,

                created_at

            FROM orders

            WHERE
                status = ?

                AND payment_status = ?

                AND payment_refund_request_status = ?

            ORDER BY
                payment_refund_requested_at DESC,
                id DESC

            LIMIT ?
            """,
            (
                STATUS_COMPLETED,

                PAYMENT_STATUS_PAID,

                PAYMENT_REFUND_REQUEST_PENDING,

                limit,
            )
        )
        .fetchall()
    )


    refund_requests = []


    for row in rows:

        refund_requests.append(
            {
                "id":
                    int(
                        row[
                            "id"
                        ]
                    ),

                "order_code":
                    row[
                        "order_code"
                    ],

                "customer_name":
                    row[
                        "customer_name"
                    ],

                "whatsapp":
                    row[
                        "whatsapp"
                    ],

                "pickup":
                    row[
                        "pickup"
                    ],

                "destination":
                    row[
                        "destination"
                    ],

                "fare":
                    payment_audit_safe_integer(
                        row[
                            "fare"
                        ]
                    )
                    or 0,

                "status":
                    row[
                        "status"
                    ],

                "payment_method":
                    row[
                        "payment_method"
                    ],

                "payment_status":
                    row[
                        "payment_status"
                    ],

                "payment_amount":
                    payment_audit_safe_integer(
                        row[
                            "payment_amount"
                        ]
                    )
                    or 0,

                "paid_at":
                    row[
                        "paid_at"
                    ],

                "refund_request_status":
                    row[
                        "payment_refund_request_status"
                    ],

                "refund_requested_at":
                    row[
                        "payment_refund_requested_at"
                    ],

                "refund_request_reason":
                    row[
                        "payment_refund_request_reason"
                    ],

                "created_at":
                    row[
                        "created_at"
                    ],
            }
        )


    return refund_requests
    
# ============================================================
# PHASE 20I.2
# PAYMENT TRANSITION HELPERS
# ============================================================

def get_effective_payment_status(
    order
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    payment_status = str(
        order.get(
            "payment_status"
        )
        or ""
    ).strip().upper()


    if (
        payment_status
        in PAYMENT_ALLOWED_STATUSES
    ):

        return payment_status


    # ========================================================
    # LEGACY FALLBACK
    # ========================================================

    payment_method = str(
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    ).strip().upper()


    if (
        payment_method
        == PAYMENT_METHOD_CASH
    ):

        return (
            PAYMENT_STATUS_UNPAID
        )


    return (
        PAYMENT_STATUS_PENDING
    )


def validate_payment_status_transition(
    order,
    new_status,
    actor_type
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # CURRENT STATUS
    # ========================================================

    current_status = (
        get_effective_payment_status(
            order
        )
    )


    # ========================================================
    # NEW STATUS
    # ========================================================

    new_status = str(
        new_status
        or ""
    ).strip().upper()


    if (
        new_status
        not in PAYMENT_ALLOWED_STATUSES
    ):

        raise ValueError(
            "Status pembayaran tujuan tidak valid."
        )


    # ========================================================
    # ACTOR
    # ========================================================

    actor_type = str(
        actor_type
        or ""
    ).strip().upper()


    if (
        actor_type
        not in PAYMENT_AUDIT_ALLOWED_ACTORS
    ):

        raise ValueError(
            "Actor perubahan pembayaran tidak valid."
        )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        current_status
        == new_status
    ):

        return {
            "allowed":
                True,

            "idempotent":
                True,

            "old_status":
                current_status,

            "new_status":
                new_status,

            "actor_type":
                actor_type,
        }


    # ========================================================
    # GLOBAL TRANSITION
    # ========================================================

    allowed_next_statuses = (
        PAYMENT_STATUS_TRANSITIONS.get(
            current_status,
            set()
        )
    )


    if (
        new_status
        not in allowed_next_statuses
    ):

        raise ValueError(
            (
                "Perubahan status pembayaran "
                f"{current_status} → {new_status} "
                "tidak diperbolehkan."
            )
        )


    # ========================================================
    # ACTOR TRANSITION
    # ========================================================

    transition_pair = (
        current_status,
        new_status,
    )


    allowed_actor_transitions = (
        PAYMENT_ACTOR_TRANSITIONS.get(
            actor_type,
            set()
        )
    )


    if (
        transition_pair
        not in allowed_actor_transitions
    ):

        raise ValueError(
            (
                "Aktor ini tidak memiliki izin "
                "melakukan perubahan status "
                "pembayaran tersebut."
            )
        )


    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    payment_method = str(
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    ).strip().upper()


    if (
        payment_method
        not in PAYMENT_ALLOWED_METHODS
    ):

        raise ValueError(
            "Metode pembayaran tidak valid."
        )


    # ========================================================
    # CASH:
    # BELUM_DIBAYAR -> DIBAYAR
    # ========================================================

    if (
        transition_pair
        ==
        (
            PAYMENT_STATUS_UNPAID,
            PAYMENT_STATUS_PAID,
        )
        and
        payment_method
        != PAYMENT_METHOD_CASH
    ):

        raise ValueError(
            (
                "Transisi pembayaran langsung "
                "BELUM_DIBAYAR → DIBAYAR "
                "hanya diperbolehkan untuk Tunai."
            )
        )


    # ========================================================
    # DIGITAL:
    # PENDING -> CUSTOMER SUBMITTED
    # ========================================================

    if (
        transition_pair
        ==
        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
        )
        and
        payment_method
        not in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )
    ):

        raise ValueError(
            (
                "Konfirmasi pelanggan hanya berlaku "
                "untuk QRIS atau Transfer Bank."
            )
        )


    # ========================================================
    # DIGITAL:
    # AWAITING -> PAID
    # ========================================================

    if (
        transition_pair
        ==
        (
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
            PAYMENT_STATUS_PAID,
        )
        and
        payment_method
        not in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )
    ):

        raise ValueError(
            (
                "Konfirmasi pembayaran digital "
                "hanya berlaku untuk QRIS "
                "atau Transfer Bank."
            )
        )


    return {
        "allowed":
            True,

        "idempotent":
            False,

        "old_status":
            current_status,

        "new_status":
            new_status,

        "actor_type":
            actor_type,
    }
    
def ensure_payment_transition_updated(
    cursor,
    order_code
):

    affected_rows = int(
        cursor.rowcount
        or 0
    )


    if affected_rows == 1:

        return


    app.logger.warning(
        (
            "[PAYMENT TRANSITION CONFLICT] "
            f"order={order_code}"
        )
    )


    raise RuntimeError(
        (
            "Status pembayaran berubah "
            "saat transaksi sedang diproses. "
            "Silakan muat ulang data."
        )
    )        

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
# PHASE 19D
# PUBLIC DRIVER TRUST
# ============================================================

def get_public_driver_trust(
    connection,
    profile=None
):

    if profile is None:

        profile = (
            get_driver_profile(
                connection
            )
        )


    # ========================================================
    # PUBLIC REPUTATION STATS
    # ========================================================

    trust_row = (
        connection.execute(
            """
            SELECT

                (
                    SELECT
                        COUNT(*)

                    FROM orders

                    WHERE status = ?
                ) AS completed_trips,


                (
                    SELECT
                        COUNT(*)

                    FROM order_reviews r

                    INNER JOIN orders o
                        ON o.id = r.order_id

                    WHERE o.status = ?
                ) AS review_count,


                (
                    SELECT
                        COALESCE(
                            AVG(r.rating),
                            0
                        )

                    FROM order_reviews r

                    INNER JOIN orders o
                        ON o.id = r.order_id

                    WHERE o.status = ?
                ) AS average_rating
            """,
            (
                STATUS_COMPLETED,

                STATUS_COMPLETED,

                STATUS_COMPLETED,
            )
        )
        .fetchone()
    )


    completed_trips = int(
        trust_row[
            "completed_trips"
        ]
        or 0
    )


    review_count = int(
        trust_row[
            "review_count"
        ]
        or 0
    )


    average_rating = round(
        float(
            trust_row[
                "average_rating"
            ]
            or 0
        ),
        1
    )


    # ========================================================
    # PROFILE AVAILABILITY
    # ========================================================

    profile_available = bool(
        profile
        and
        str(
            profile.get(
                "driver_name"
            )
            or ""
        ).strip()
    )


    vehicle_name = (
        str(
            profile.get(
                "vehicle_name"
            )
            or ""
        ).strip()
        if profile
        else ""
    )


    vehicle_plate = (
        str(
            profile.get(
                "vehicle_plate"
            )
            or ""
        ).strip()
        if profile
        else ""
    )


    vehicle_data_available = bool(
        vehicle_name
        and
        vehicle_plate
        and
        vehicle_plate != "-"
    )


    contact_available = (
        len(
            normalize_whatsapp_number(
                DRIVER_WHATSAPP
            )
        )
        >= 10
    )


    # ========================================================
    # PUBLIC REPUTATION LABEL
    # ========================================================

    if review_count == 0:

        reputation_label = (
            "Belum ada ulasan"
        )


    elif review_count < 3:

        reputation_label = (
            "Rating mulai terbentuk"
        )


    elif average_rating >= 4.8:

        reputation_label = (
            "Pelayanan Istimewa"
        )


    elif average_rating >= 4.5:

        reputation_label = (
            "Sangat Baik"
        )


    elif average_rating >= 4.0:

        reputation_label = (
            "Pelayanan Baik"
        )


    else:

        reputation_label = (
            "Terus Ditingkatkan"
        )


    return {

        "average_rating":
            average_rating,

        "review_count":
            review_count,

        "completed_trips":
            completed_trips,

        "reputation_label":
            reputation_label,

        "profile_available":
            profile_available,

        "vehicle_data_available":
            vehicle_data_available,

        "contact_available":
            contact_available,
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
# PHASE 20H.8
# DRIVER PAYMENT CSRF SECURITY
# ============================================================

DRIVER_CSRF_SESSION_KEY = (
    "driver_csrf_token"
)


def get_driver_csrf_token():

    token = (
        session.get(
            DRIVER_CSRF_SESSION_KEY
        )
    )


    if not token:

        token = (
            secrets.token_urlsafe(
                32
            )
        )


        session[
            DRIVER_CSRF_SESSION_KEY
        ] = token


    return token


@app.template_global(
    "driver_csrf_token"
)
def driver_csrf_token_template():

    return (
        get_driver_csrf_token()
    )


def driver_csrf_token_is_valid():

    expected_token = str(
        session.get(
            DRIVER_CSRF_SESSION_KEY,
            ""
        )
        or ""
    ).strip()


    supplied_token = str(
        request.form.get(
            "_csrf_token",
            ""
        )
        or
        request.headers.get(
            "X-CSRF-Token",
            ""
        )
        or ""
    ).strip()


    if (
        not expected_token
        or
        not supplied_token
    ):

        return False


    return secrets.compare_digest(
        expected_token,
        supplied_token
    )


def driver_csrf_required(
    view_function
):

    @wraps(
        view_function
    )
    def wrapped_view(
        *args,
        **kwargs
    ):

        if not driver_csrf_token_is_valid():

            app.logger.warning(
                (
                    "[DRIVER CSRF BLOCKED] "
                    f"path={request.path} "
                    f"ip={request.remote_addr}"
                )
            )


            if request.path.startswith(
                "/api/"
            ):

                return jsonify(
                    {
                        "success":
                            False,

                        "message":
                            (
                                "Permintaan keamanan "
                                "tidak valid."
                            ),
                    }
                ), 403


            abort(
                403
            )


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
# PHASE 19D
# ============================================================

@app.route("/")
def index():

    connection = (
        get_db()
    )


    try:

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


        driver_trust = (
            get_public_driver_trust(
                connection,
                profile
            )
        )


    finally:

        connection.close()


    return render_template(
        "index.html",

        service_open=
            service_open,

        driver_profile=
            profile,

        driver_trust=
            driver_trust,
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
# PHASE 20C
# PAYMENT METHOD AVAILABILITY
# ============================================================

def payment_method_is_available(
    payment_method
):

    if (
        payment_method
        == PAYMENT_METHOD_CASH
    ):

        return True


    if (
        payment_method
        == PAYMENT_METHOD_QRIS
    ):

        qris_path = os.path.join(
            BASE_DIR,
            "static",
            PAYMENT_QRIS_IMAGE
        )


        return bool(
            PAYMENT_QRIS_IMAGE
            and os.path.isfile(
                qris_path
            )
        )


    if (
        payment_method
        == PAYMENT_METHOD_BANK_TRANSFER
    ):

        return bool(
            PAYMENT_BANK_NAME
            and
            PAYMENT_BANK_ACCOUNT_NUMBER
            and
            PAYMENT_BANK_ACCOUNT_NAME
        )


    return False

# ============================================================
# PHASE 20I.4A
# DIGITAL PAYMENT HELPERS
# ============================================================

def payment_method_is_digital(
    payment_method
):

    payment_method = str(
        payment_method
        or ""
    ).strip().upper()


    return (
        payment_method
        in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )
    )
    
def parse_payment_timestamp(
    value
):

    if not value:

        return None


    try:

        parsed = datetime.strptime(
            str(
                value
            ).strip(),
            "%Y-%m-%d %H:%M:%S"
        )


        return parsed.replace(
            tzinfo=APP_TZ
        )


    except (
        TypeError,
        ValueError
    ):

        return None
    
def build_payment_expiry_timestamp(
    minutes=None
):

    if minutes is None:

        minutes = (
            PAYMENT_EXPIRY_MINUTES
        )


    try:

        minutes = int(
            minutes
        )

    except (
        TypeError,
        ValueError
    ):

        minutes = (
            PAYMENT_EXPIRY_MINUTES
        )


    minutes = max(
        1,
        minutes
    )


    expires_at = (
        datetime.now(
            APP_TZ
        )
        +
        timedelta(
            minutes=minutes
        )
    )


    return expires_at.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    
def get_payment_expiry_state(
    order
):

    if not order:

        return {
            "enabled":
                False,

            "active":
                False,

            "expired":
                False,

            "expires_at":
                None,

            "seconds_remaining":
                None,
        }


    payment_method = str(
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    ).strip().upper()


    payment_status = (
        get_effective_payment_status(
            order
        )
    )


    expires_at_raw = (
        order.get(
            "payment_expires_at"
        )
    )


    # ========================================================
    # CASH NEVER USES DIGITAL EXPIRATION
    # ========================================================

    if not payment_method_is_digital(
        payment_method
    ):

        return {
            "enabled":
                False,

            "active":
                False,

            "expired":
                False,

            "expires_at":
                None,

            "seconds_remaining":
                None,
        }


    # ========================================================
    # ONLY TRANSIENT DIGITAL STATES USE EXPIRY
    # ========================================================

    if (
        payment_status
        not in (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
        )
    ):

        return {
            "enabled":
                True,

            "active":
                False,

            "expired":
                (
                    payment_status
                    ==
                    PAYMENT_STATUS_EXPIRED
                ),

            "expires_at":
                expires_at_raw,

            "seconds_remaining":
                0
                if (
                    payment_status
                    ==
                    PAYMENT_STATUS_EXPIRED
                )
                else None,
        }


    expires_at = (
        parse_payment_timestamp(
            expires_at_raw
        )
    )


    # Window belum dimulai.
    if expires_at is None:

        return {
            "enabled":
                True,

            "active":
                False,

            "expired":
                False,

            "expires_at":
                None,

            "seconds_remaining":
                None,
        }


    now = datetime.now(
        APP_TZ
    )


    seconds_remaining = int(
        (
            expires_at
            - now
        ).total_seconds()
    )


    expired = (
        seconds_remaining
        <= 0
    )


    return {
        "enabled":
            True,

        "active":
            True,

        "expired":
            expired,

        "expires_at":
            expires_at_raw,

        "seconds_remaining":
            max(
                0,
                seconds_remaining
            ),
    }    

# ============================================================
# PHASE 20A
# PAYMENT METHOD NORMALIZER
# ============================================================

def normalize_payment_method(
    value,
    default=PAYMENT_METHOD_CASH
):

    value = str(
        value
        or ""
    ).strip().upper()


    if (
        value
        in PAYMENT_ALLOWED_METHODS
    ):

        return value


    return default

# ============================================================
# PHASE 20C
# PARSE CUSTOMER PAYMENT METHOD
# ============================================================

def parse_payment_method(
    value
):

    value = str(
        value
        or PAYMENT_METHOD_CASH
    ).strip().upper()


    if (
        value
        not in PAYMENT_ALLOWED_METHODS
    ):

        raise ValueError(
            "Metode pembayaran tidak valid."
        )


    if not payment_method_is_available(
        value
    ):

        raise ValueError(
            (
                "Metode pembayaran yang dipilih "
                "belum tersedia."
            )
        )


    return value

# ============================================================
# PHASE 20C
# PAYMENT INSTRUCTIONS
# ============================================================

def get_payment_instructions(
    payment_method,
    amount,
    order_code
):

    payment_method = (
        normalize_payment_method(
            payment_method
        )
    )


    amount = int(
        amount
        or 0
    )


    # ========================================================
    # CASH
    # ========================================================

    if (
        payment_method
        == PAYMENT_METHOD_CASH
    ):

        return {

            "type":
                "cash",

            "title":
                "Pembayaran Tunai",

            "description":
                (
                    "Bayarkan tarif langsung "
                    "kepada driver."
                ),
        }


    # ========================================================
    # QRIS
    # ========================================================

    if (
        payment_method
        == PAYMENT_METHOD_QRIS
    ):

        return {

            "type":
                "qris",

            "title":
                "Pembayaran QRIS",

            "image_url":
                url_for(
                    "static",
                    filename=
                        PAYMENT_QRIS_IMAGE
                ),

            "amount":
                amount,

            "reference":
                order_code,

            "description":
                (
                    "Scan QRIS dan bayarkan "
                    "sesuai nominal perjalanan."
                ),
        }


    # ========================================================
    # BANK TRANSFER
    # ========================================================

    if (
        payment_method
        == PAYMENT_METHOD_BANK_TRANSFER
    ):

        return {

            "type":
                "bank_transfer",

            "title":
                "Transfer Bank",

            "bank_name":
                PAYMENT_BANK_NAME,

            "account_number":
                PAYMENT_BANK_ACCOUNT_NUMBER,

            "account_name":
                PAYMENT_BANK_ACCOUNT_NAME,

            "amount":
                amount,

            "reference":
                order_code,

            "description":
                (
                    "Transfer sesuai nominal "
                    "perjalanan ke rekening berikut."
                ),
        }


    return None

# ============================================================
# PHASE 20C
# INITIALIZE ORDER PAYMENT
# ============================================================

def initialize_order_payment(
    connection,
    order_code,
    fare,
    payment_method=PAYMENT_METHOD_CASH
):

    payment_method = (
        parse_payment_method(
            payment_method
        )
    )


    payment_amount = int(
        fare
        or 0
    )


    # ========================================================
    # INITIAL STATUS
    # ========================================================

    if (
        payment_method
        == PAYMENT_METHOD_CASH
    ):

        payment_status = (
            PAYMENT_STATUS_UNPAID
        )

        payment_provider = (
            None
        )

        payment_reference = (
            None
        )


    else:

        payment_status = (
            PAYMENT_STATUS_PENDING
        )

        payment_provider = (
            "MANUAL"
        )

        payment_reference = (
            order_code
        )


    timestamp = (
        current_timestamp()
    )


    connection.execute(
        """
        UPDATE orders

        SET
            payment_method = ?,

            payment_status = ?,

            payment_amount = ?,

            payment_reference = ?,

            payment_provider = ?,

            payment_expires_at = NULL,

            paid_at = NULL,

            payment_customer_confirmed_at = NULL,

            payment_driver_confirmed_at = NULL,

            payment_updated_at = ?

        WHERE order_code = ?
        """,
        (
            payment_method,

            payment_status,

            payment_amount,

            payment_reference,

            payment_provider,

            timestamp,

            order_code,
        )
    )
    
        # ========================================================
    # PHASE 20I.2
    # INITIAL PAYMENT AUDIT
    # ========================================================

    audit_order = (
        connection.execute(
            """
            SELECT

                id,

                order_code,

                payment_method,

                payment_status,

                payment_amount,

                payment_reference,
                
                payment_refund_request_status,

                payment_refund_amount,

                payment_refund_reference

            FROM orders

            WHERE order_code = ?

            LIMIT 1
            """,
            (
                order_code,
            )
        )
        .fetchone()
    )


    if not audit_order:

        raise RuntimeError(
            (
                "Order payment tidak ditemukan "
                "setelah initialization."
            )
        )


    empty_snapshot = {
        "payment_method":
            None,

        "payment_status":
            None,

        "payment_amount":
            None,

        "payment_reference":
            None,

        "refund_request_status":
            None,

        "refund_amount":
            None,

        "refund_reference":
            None,
    }


    new_snapshot = (
        build_payment_audit_snapshot(
            audit_order
        )
    )


    record_payment_audit_event(
        connection,
        audit_order,

        action=
            PAYMENT_AUDIT_ACTION_CREATED,

        actor_type=
            PAYMENT_AUDIT_ACTOR_SYSTEM,

        old_snapshot=
            empty_snapshot,

        new_snapshot=
            new_snapshot,

        reason=(
            "Payment dibuat bersamaan "
            "dengan pesanan."
        )
    )


    return {

        "method":
            payment_method,

        "status":
            payment_status,

        "amount":
            payment_amount,

        "reference":
            payment_reference,

        "provider":
            payment_provider,

        "paid_at":
            None,

        "instructions":
            get_payment_instructions(
                payment_method,
                payment_amount,
                order_code
            ),
    }
    
# ============================================================
# PHASE 20D
# ORDER PAYMENT PAYLOAD
# ============================================================

def order_payment_payload(
    order
):

    if not order:

        return None


    payment_method = (
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    )


    payment_status = (
        order.get(
            "payment_status"
        )
        or PAYMENT_STATUS_UNPAID
    )


    payment_amount = int(
        order.get(
            "payment_amount"
        )
        or order.get(
            "fare"
        )
        or 0
    )


    order_code = (
        order.get(
            "order_code"
        )
        or ""
    )


    trip_status = (
        order.get(
            "status"
        )
        or ""
    )


    # ========================================================
    # CUSTOMER MAY SUBMIT PAYMENT CONFIRMATION
    # ========================================================

    can_customer_confirm = (

        payment_method
        in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )

        and

        payment_status
        == PAYMENT_STATUS_PENDING

        and

        trip_status
        in (
            STATUS_ACCEPTED,
            STATUS_TO_PICKUP,
            STATUS_PICKED_UP,
            STATUS_COMPLETED,
        )
    )


    # ========================================================
    # DRIVER MAY CONFIRM PAYMENT RECEIVED
    # ========================================================

    can_driver_confirm = (

        payment_method
        in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )

        and

        payment_status
        == PAYMENT_STATUS_AWAITING_CONFIRMATION
    )


    return {

        "method":
            payment_method,

        "status":
            payment_status,

        "amount":
            payment_amount,

        "reference":
            order.get(
                "payment_reference"
            ),
            
        "refunded_at":
            order.get(
                "payment_refunded_at"
            ),

        "refund_amount":
            int(
                order.get(
                    "payment_refund_amount"
                )
                or 0
            ),

        "refund_reason":
            order.get(
                "payment_refund_reason"
            ),

        "provider":
            order.get(
                "payment_provider"
            ),

        "paid_at":
            order.get(
                "paid_at"
            ),

        "customer_confirmed_at":
            order.get(
                "payment_customer_confirmed_at"
            ),

        "driver_confirmed_at":
            order.get(
                "payment_driver_confirmed_at"
            ),

        "updated_at":
            order.get(
                "payment_updated_at"
            ),
            
        "expires_at":
            order.get(
                "payment_expires_at"
            ),

        "expiry":
            get_payment_expiry_state(
                order
            ),

        "can_customer_confirm":
            can_customer_confirm,

        "can_driver_confirm":
            can_driver_confirm,
            
        "refund_request":
            payment_refund_request_payload(
                order
            ),

        "instructions":
            get_payment_instructions(
                payment_method,
                payment_amount,
                order_code
            ),
    }
     
     # ============================================================
# PHASE 20G.2
# RECEIPT TOKEN HELPERS
# ============================================================

def generate_receipt_token():

    return secrets.token_urlsafe(
        RECEIPT_TOKEN_BYTES
    )


def hash_receipt_token(
    token
):

    token = str(
        token
        or ""
    ).strip()


    if not token:

        return None


    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def verify_receipt_token(
    raw_token,
    stored_hash
):

    raw_token = str(
        raw_token
        or ""
    ).strip()


    stored_hash = str(
        stored_hash
        or ""
    ).strip()


    if (
        not raw_token
        or
        not stored_hash
    ):

        return False


    calculated_hash = (
        hash_receipt_token(
            raw_token
        )
    )


    if not calculated_hash:

        return False


    return secrets.compare_digest(
        calculated_hash,
        stored_hash
    )


# ============================================================
# PHASE 20G.2
# INITIALIZE RECEIPT ACCESS
# ============================================================

def initialize_receipt_access(
    connection,
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    if not order_code:

        raise ValueError(
            "Kode pesanan receipt tidak valid."
        )


    receipt_token = (
        generate_receipt_token()
    )


    receipt_token_hash = (
        hash_receipt_token(
            receipt_token
        )
    )


    if not receipt_token_hash:

        raise RuntimeError(
            "Receipt token gagal dibuat."
        )


    connection.execute(
        """
        UPDATE orders

        SET
            receipt_token_hash = ?

        WHERE order_code = ?
        """,
        (
            receipt_token_hash,
            order_code,
        )
    )


    return receipt_token


# ============================================================
# PHASE 20G.2
# RECEIPT ELIGIBILITY
# ============================================================

def get_receipt_eligibility(
    order
):

    if not order:

        return {
            "eligible":
                False,

            "reason":
                "ORDER_NOT_FOUND",
        }


    # ========================================================
    # ORDER MUST BE COMPLETED
    # ========================================================

    order_status = str(
        order.get(
            "status"
        )
        or ""
    ).strip().upper()


    if (
        order_status
        != STATUS_COMPLETED
    ):

        return {
            "eligible":
                False,

            "reason":
                "ORDER_NOT_COMPLETED",
        }


    # ========================================================
    # PAYMENT MUST BE PAID
    # ========================================================

    payment_status = str(
        order.get(
            "payment_status"
        )
        or ""
    ).strip().upper()


    if (
        payment_status
        != PAYMENT_STATUS_PAID
    ):

        return {
            "eligible":
                False,

            "reason":
                "PAYMENT_NOT_PAID",
        }


    # ========================================================
    # PAID TIMESTAMP MUST EXIST
    # ========================================================

    paid_at = (
        order.get(
            "paid_at"
        )
    )


    if not paid_at:

        return {
            "eligible":
                False,

            "reason":
                "PAID_AT_MISSING",
        }


    # ========================================================
    # PAYMENT AMOUNT MUST BE VALID
    # ========================================================

    try:

        fare = int(
            order.get(
                "fare"
            )
            or 0
        )


        payment_amount = int(
            order.get(
                "payment_amount"
            )
            or 0
        )


    except (
        TypeError,
        ValueError
    ):

        return {
            "eligible":
                False,

            "reason":
                "INVALID_AMOUNT",
        }


    if (
        fare <= 0
        or
        payment_amount <= 0
    ):

        return {
            "eligible":
                False,

            "reason":
                "INVALID_AMOUNT",
        }


    if (
        payment_amount
        != fare
    ):

        return {
            "eligible":
                False,

            "reason":
                "PAYMENT_AMOUNT_MISMATCH",
        }


    # ========================================================
    # PAYMENT METHOD MUST BE KNOWN
    # ========================================================

    payment_method = str(
        order.get(
            "payment_method"
        )
        or ""
    ).strip().upper()


    if (
        payment_method
        not in PAYMENT_ALLOWED_METHODS
    ):

        return {
            "eligible":
                False,

            "reason":
                "INVALID_PAYMENT_METHOD",
        }


    return {
        "eligible":
            True,

        "reason":
            None,
    }


# ============================================================
# PHASE 20G
# DIGITAL RECEIPT PAYLOAD
# ============================================================

def build_payment_receipt(
    order
):

    if not order:

        return None


    eligibility = (
        get_receipt_eligibility(
            order
        )
    )


    order_code = str(
        order.get(
            "order_code"
        )
        or ""
    ).strip().upper()


    customer_name = str(
        order.get(
            "customer_name"
        )
        or "Pelanggan"
    ).strip()


    pickup = str(
        order.get(
            "pickup"
        )
        or ""
    ).strip()


    destination = str(
        order.get(
            "destination"
        )
        or ""
    ).strip()


    payment_method = str(
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    ).strip().upper()


    payment_status = str(
        order.get(
            "payment_status"
        )
        or PAYMENT_STATUS_UNPAID
    ).strip().upper()


    payment_amount = int(
        order.get(
            "payment_amount"
        )
        or order.get(
            "fare"
        )
        or 0
    )


    if (
        payment_method
        == PAYMENT_METHOD_QRIS
    ):

        payment_method_label = (
            "QRIS"
        )


    elif (
        payment_method
        == PAYMENT_METHOD_BANK_TRANSFER
    ):

        payment_method_label = (
            "Transfer Bank"
        )


    else:

        payment_method_label = (
            "Tunai"
        )


    return {

        "available":
            bool(
                eligibility[
                    "eligible"
                ]
            ),

        "eligibility_reason":
            eligibility[
                "reason"
            ],

        "order_code":
            order_code,

        "customer_name":
            customer_name,

        "pickup":
            pickup,

        "destination":
            destination,

        "distance_km":
            float(
                order.get(
                    "distance_km"
                )
                or 0
            ),

        "duration_minutes":
            int(
                order.get(
                    "duration_minutes"
                )
                or 0
            ),

        "fare":
            payment_amount,

        "order_status":
            (
                order.get(
                    "status"
                )
                or ""
            ),

        "payment_method":
            payment_method,

        "payment_method_label":
            payment_method_label,

        "payment_status":
            payment_status,

        "payment_reference":
            order.get(
                "payment_reference"
            ),

        "payment_provider":
            order.get(
                "payment_provider"
            ),

        "created_at":
            order.get(
                "created_at"
            ),

        "completed_at":
            order.get(
                "completed_at"
            ),

        "paid_at":
            order.get(
                "paid_at"
            ),
    }


# ============================================================
# PHASE 20G.2
# RECEIPT ACCESS RATE LIMIT
# ============================================================

def get_receipt_client_key(
    order_code
):

    client_ip = str(
        request.remote_addr
        or "unknown"
    ).strip()


    order_code = str(
        order_code
        or ""
    ).strip().upper()


    return (
        f"{client_ip}:{order_code}"
    )


def receipt_access_is_limited(
    order_code
):

    now = time.time()


    key = (
        get_receipt_client_key(
            order_code
        )
    )


    with _receipt_access_lock:

        attempts = (
            _receipt_access_attempts.get(
                key,
                []
            )
        )


        attempts = [

            attempt_time

            for attempt_time
            in attempts

            if (
                now
                - attempt_time
            )
            <
            RECEIPT_ACCESS_WINDOW_SECONDS
        ]


        _receipt_access_attempts[
            key
        ] = attempts


        return (
            len(
                attempts
            )
            >=
            RECEIPT_ACCESS_MAX_ATTEMPTS
        )


def record_receipt_access_failure(
    order_code
):

    now = time.time()


    key = (
        get_receipt_client_key(
            order_code
        )
    )


    with _receipt_access_lock:

        attempts = (
            _receipt_access_attempts.get(
                key,
                []
            )
        )


        attempts.append(
            now
        )


        _receipt_access_attempts[
            key
        ] = attempts


def clear_receipt_access_failures(
    order_code
):

    key = (
        get_receipt_client_key(
            order_code
        )
    )


    with _receipt_access_lock:

        _receipt_access_attempts.pop(
            key,
            None
        )


def receipt_json_response(
    payload,
    status_code=200
):

    response = jsonify(
        payload
    )


    response.status_code = (
        status_code
    )


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
# PHASE 20D
# CUSTOMER SUBMITTED PAYMENT
# ============================================================

def mark_customer_payment_submitted(
    connection,
    order
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    payment_method = (
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    )


    # ========================================================
    # CASH DOES NOT USE CUSTOMER CONFIRMATION
    # ========================================================

    if (
        payment_method
        == PAYMENT_METHOD_CASH
    ):

        raise ValueError(
            (
                "Pembayaran tunai dikonfirmasi "
                "langsung oleh driver."
            )
        )


    if (
        payment_method
        not in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )
    ):

        raise ValueError(
            "Metode pembayaran tidak didukung."
        )


    # ========================================================
    # DRIVER MUST ACCEPT ORDER FIRST
    # ========================================================

    trip_status = (
        order.get(
            "status"
        )
        or ""
    )


    if (
        trip_status
        == STATUS_WAITING
    ):

        raise ValueError(
            (
                "Tunggu driver menerima pesanan "
                "sebelum melakukan pembayaran."
            )
        )


    if (
        trip_status
        == STATUS_REJECTED
    ):

        raise ValueError(
            (
                "Pembayaran tidak dapat dikonfirmasi "
                "karena pesanan ditolak."
            )
        )


    # ========================================================
    # CURRENT PAYMENT STATUS
    # ========================================================

    payment_status = (
        order.get(
            "payment_status"
        )
        or PAYMENT_STATUS_PENDING
    )


    # Sudah dibayar.
    if (
        payment_status
        == PAYMENT_STATUS_PAID
    ):

        return {

            "already_paid":
                True,

            "already_submitted":
                True,

            "payment":
                order_payment_payload(
                    order
                ),
        }


    # Sudah pernah dikirim customer.
    if (
        payment_status
        == PAYMENT_STATUS_AWAITING_CONFIRMATION
    ):

        return {

            "already_paid":
                False,

            "already_submitted":
                True,

            "payment":
                order_payment_payload(
                    order
                ),
        }


    if (
        payment_status
        != PAYMENT_STATUS_PENDING
    ):

        raise ValueError(
            (
                "Pembayaran dengan status ini "
                "belum dapat dikonfirmasi."
            )
        )


    timestamp = (
        current_timestamp()
    )
    
        # ========================================================
    # PHASE 20I.2
    # TRANSITION SECURITY
    # ========================================================

    transition = (
        validate_payment_status_transition(
            order,
            PAYMENT_STATUS_AWAITING_CONFIRMATION,
            PAYMENT_AUDIT_ACTOR_CUSTOMER
        )
    )


    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )


    # ========================================================
    # UPDATE
    # ========================================================

    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_status = ?,

                payment_customer_confirmed_at = ?,

                payment_updated_at = ?

            WHERE
                id = ?
                AND payment_status = ?
            """,
            (
                PAYMENT_STATUS_AWAITING_CONFIRMATION,

                timestamp,

                timestamp,

                order[
                    "id"
                ],

                transition[
                    "old_status"
                ],
            )
        )
    )


    ensure_payment_transition_updated(
        update_cursor,
        order.get(
            "order_code"
        )
    )

    updated_order = dict(order)
    updated_order["payment_status"] = PAYMENT_STATUS_AWAITING_CONFIRMATION
    updated_order["payment_customer_confirmed_at"] = timestamp
    updated_order["payment_updated_at"] = timestamp

    # ========================================================
    # PHASE 20I.3G
    # PAYMENT SUBMISSION AUDIT SNAPSHOT
    #
    # Snapshot baru dibangun dari updated_order agar
    # perubahan status pembayaran tercatat dengan benar.
    # Refund request status tidak berubah pada proses ini.
    # ========================================================

    new_snapshot = (
        build_payment_audit_snapshot(
            updated_order
        )
    )


    new_snapshot[
        "payment_status"
    ] = (
        PAYMENT_STATUS_AWAITING_CONFIRMATION
    )


    record_payment_audit_event(
        connection,
        order,

        action=
            PAYMENT_AUDIT_ACTION_CUSTOMER_SUBMITTED,

        actor_type=
            PAYMENT_AUDIT_ACTOR_CUSTOMER,

        old_snapshot=
            old_snapshot,

        new_snapshot=
            new_snapshot,

        reason=(
            "Pelanggan mengirim "
            "konfirmasi pembayaran."
        )
    )


    return {

        "already_paid":
            False,

        "already_submitted":
            False,

        "payment": {

            "method":
                payment_method,

            "status":
                PAYMENT_STATUS_AWAITING_CONFIRMATION,

            "amount":
                int(
                    order.get(
                        "payment_amount"
                    )
                    or order.get(
                        "fare"
                    )
                    or 0
                ),

            "reference":
                order.get(
                    "payment_reference"
                ),

            "provider":
                order.get(
                    "payment_provider"
                ),

            "paid_at":
                None,

            "customer_confirmed_at":
                timestamp,

            "driver_confirmed_at":
                None,

            "updated_at":
                timestamp,

            "can_customer_confirm":
                False,

            "can_driver_confirm":
                True,
        },
    }
    
    
# ============================================================
# PHASE 20H.8
# PAYMENT AMOUNT INTEGRITY
# ============================================================

def get_verified_payment_amount(
    order
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # FARE
    # ========================================================

    try:

        fare = int(
            order.get(
                "fare"
            )
            or 0
        )

    except (
        TypeError,
        ValueError
    ):

        raise ValueError(
            "Tarif perjalanan tidak valid."
        )


    if fare <= 0:

        raise ValueError(
            "Tarif perjalanan tidak valid."
        )


    # ========================================================
    # PAYMENT AMOUNT
    # ========================================================

    raw_payment_amount = (
        order.get(
            "payment_amount"
        )
    )


    # Untuk data lama yang belum memiliki payment_amount,
    # aman untuk memakai fare resmi sebagai nominal.
    if (
        raw_payment_amount
        is None
        or
        str(
            raw_payment_amount
        ).strip()
        == ""
    ):

        payment_amount = (
            fare
        )


    else:

        try:

            payment_amount = int(
                raw_payment_amount
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "Nominal pembayaran tidak valid."
            )


    if payment_amount <= 0:

        raise ValueError(
            "Nominal pembayaran tidak valid."
        )


    # ========================================================
    # PAYMENT MUST MATCH TRIP FARE
    # ========================================================

    if payment_amount != fare:

        app.logger.warning(
            (
                "[PAYMENT AMOUNT MISMATCH] "
                f"order={order.get('order_code')} "
                f"fare={fare} "
                f"payment={payment_amount}"
            )
        )


        raise ValueError(
            (
                "Nominal pembayaran berbeda "
                "dari tarif perjalanan. "
                "Periksa transaksi sebelum "
                "mengonfirmasi pembayaran."
            )
        )


    return payment_amount
# ============================================================
# PHASE 20B
# CONFIRM CASH PAYMENT
# ============================================================

def confirm_cash_payment(
    connection,
    order
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    payment_method = (
        order[
            "payment_method"
        ]
        or PAYMENT_METHOD_CASH
    )


    if (
        payment_method
        != PAYMENT_METHOD_CASH
    ):

        raise ValueError(
            "Pesanan ini bukan pembayaran tunai."
        )


    # ========================================================
    # TRIP MUST BE COMPLETED
    # ========================================================

    if (
        order[
            "status"
        ]
        != STATUS_COMPLETED
    ):

        raise ValueError(
            (
                "Pembayaran tunai hanya dapat "
                "dikonfirmasi setelah perjalanan selesai."
            )
        )


    # ========================================================
    # CURRENT PAYMENT STATUS
    # ========================================================

    payment_status = (
        order[
            "payment_status"
        ]
        or PAYMENT_STATUS_UNPAID
    )


    # Sudah dibayar -> idempotent.
    if (
        payment_status
        == PAYMENT_STATUS_PAID
    ):

        return {

            "already_paid":
                True,

            "payment":
                order_payment_payload(
                    order
                ),
        }


    # ========================================================
    # ONLY UNPAID CASH CAN BE CONFIRMED
    # ========================================================

    if (
        payment_status
        != PAYMENT_STATUS_UNPAID
    ):

        raise ValueError(
            (
                "Status pembayaran ini tidak dapat "
                "dikonfirmasi sebagai pembayaran tunai."
            )
        )

    # ========================================================
    # PHASE 20I.2
    # TRANSITION SECURITY
    # ========================================================

    transition = (
        validate_payment_status_transition(
            order,
            PAYMENT_STATUS_PAID,
            PAYMENT_AUDIT_ACTOR_DRIVER
        )
    )


    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )

    # ========================================================
    # PHASE 20H.8
    # PAYMENT AMOUNT INTEGRITY
    # ========================================================

    payment_amount = (
        get_verified_payment_amount(
            order
        )
    )


    # ========================================================
    # TIMESTAMP
    # ========================================================

    paid_at = (
        current_timestamp()
    )


    # ========================================================
    # UPDATE PAYMENT
    # ========================================================

    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_method = ?,

                payment_status = ?,

                payment_amount = ?,

                paid_at = ?,

                payment_driver_confirmed_at = ?,

                payment_updated_at = ?

            WHERE
                id = ?
                AND payment_status = ?
            """,
            (
                PAYMENT_METHOD_CASH,

                PAYMENT_STATUS_PAID,

                payment_amount,

                paid_at,

                paid_at,

                paid_at,

                order[
                    "id"
                ],

                transition[
                    "old_status"
                ],
            )
        )
    )
    
        # ========================================================
    # PAYMENT AUDIT
    # ========================================================

    new_snapshot = dict(
        old_snapshot
    )


    new_snapshot[
        "payment_method"
    ] = (
        PAYMENT_METHOD_CASH
    )


    new_snapshot[
        "payment_status"
    ] = (
        PAYMENT_STATUS_PAID
    )


    new_snapshot[
        "payment_amount"
    ] = (
        payment_amount
    )


    record_payment_audit_event(
        connection,
        order,

        action=
            PAYMENT_AUDIT_ACTION_CONFIRMED_CASH,

        actor_type=
            PAYMENT_AUDIT_ACTOR_DRIVER,

        old_snapshot=
            old_snapshot,

        new_snapshot=
            new_snapshot,

        reason=(
            "Driver mengonfirmasi "
            "pembayaran tunai diterima."
        )
    )

    ensure_payment_transition_updated(
        update_cursor,
        order.get(
            "order_code"
        )
    )


    return {

        "already_paid":
            False,

        "payment": {

            "method":
                PAYMENT_METHOD_CASH,

            "status":
                PAYMENT_STATUS_PAID,

            "amount":
                payment_amount,

            "paid_at":
                paid_at,

            "driver_confirmed_at":
                paid_at,

            "updated_at":
                paid_at,
        },
    }

# ============================================================
# PHASE 20D
# DRIVER CONFIRM MANUAL DIGITAL PAYMENT
# ============================================================

def confirm_manual_payment(
    connection,
    order
):

    if not order:

        raise ValueError(
            "Pesanan tidak ditemukan."
        )


    payment_method = (
        order.get(
            "payment_method"
        )
        or PAYMENT_METHOD_CASH
    )


    # ========================================================
    # ONLY QRIS / BANK TRANSFER
    # ========================================================

    if (
        payment_method
        not in (
            PAYMENT_METHOD_QRIS,
            PAYMENT_METHOD_BANK_TRANSFER,
        )
    ):

        raise ValueError(
            (
                "Pesanan ini bukan pembayaran "
                "QRIS atau Transfer Bank."
            )
        )


    payment_status = (
        order.get(
            "payment_status"
        )
        or PAYMENT_STATUS_PENDING
    )


    # ========================================================
    # IDEMPOTENT
    # ========================================================

    if (
        payment_status
        == PAYMENT_STATUS_PAID
    ):

        return {

            "already_paid":
                True,

            "payment":
                order_payment_payload(
                    order
                ),
        }


    # ========================================================
    # CUSTOMER MUST SUBMIT FIRST
    # ========================================================

    if (
        payment_status
        != PAYMENT_STATUS_AWAITING_CONFIRMATION
    ):

        raise ValueError(
            (
                "Pelanggan belum mengirim "
                "konfirmasi pembayaran."
            )
        )
        
    # ========================================================
    # PHASE 20I.2
    # TRANSITION SECURITY
    # ========================================================

    transition = (
        validate_payment_status_transition(
            order,
            PAYMENT_STATUS_PAID,
            PAYMENT_AUDIT_ACTOR_DRIVER
        )
    )


    old_snapshot = (
        build_payment_audit_snapshot(
            order
        )
    )


    payment_amount = int(
        order.get(
            "payment_amount"
        )
        or order.get(
            "fare"
        )
        or 0
    )


    if payment_amount <= 0:

        raise ValueError(
            "Nominal pembayaran tidak valid."
        )


    paid_at = (
        current_timestamp()
    )


    update_cursor = (
        connection.execute(
            """
            UPDATE orders

            SET
                payment_status = ?,

                payment_amount = ?,

                paid_at = ?,

                payment_driver_confirmed_at = ?,

                payment_updated_at = ?

            WHERE
                id = ?
                AND payment_status = ?
            """,
            (
                PAYMENT_STATUS_PAID,

                payment_amount,

                paid_at,

                paid_at,

                paid_at,

                order[
                    "id"
                ],

                transition[
                    "old_status"
                ],
            )
        )
    )
    
        # ========================================================
    # PAYMENT AUDIT
    # ========================================================

    new_snapshot = dict(
        old_snapshot
    )


    new_snapshot[
        "payment_status"
    ] = (
        PAYMENT_STATUS_PAID
    )


    new_snapshot[
        "payment_amount"
    ] = (
        payment_amount
    )


    record_payment_audit_event(
        connection,
        order,

        action=
            PAYMENT_AUDIT_ACTION_CONFIRMED_MANUAL,

        actor_type=
            PAYMENT_AUDIT_ACTOR_DRIVER,

        old_snapshot=
            old_snapshot,

        new_snapshot=
            new_snapshot,

        reason=(
            "Driver mengonfirmasi "
            "pembayaran digital diterima."
        )
    )


    ensure_payment_transition_updated(
        update_cursor,
        order.get(
            "order_code"
        )
    )


    return {

        "already_paid":
            False,

        "payment": {

            "method":
                payment_method,

            "status":
                PAYMENT_STATUS_PAID,

            "amount":
                payment_amount,

            "paid_at":
                paid_at,

            "driver_confirmed_at":
                paid_at,

            "updated_at":
                paid_at,
        },
    }

# ============================================================
# PHASE 20E
# DRIVER PAYMENT CONTROL SUMMARY
# ============================================================

def get_driver_payment_control_summary():

    connection = None

    try:

        connection = get_db()


        row = (
            connection.execute(
                """
                SELECT

                    SUM(
                        CASE
                            WHEN payment_status = ?
                            THEN 1
                            ELSE 0
                        END
                    ) AS needs_confirmation,

                    SUM(
                        CASE
                            WHEN
                                COALESCE(
                                    payment_status,
                                    ?
                                )
                                IN (?, ?)
                            THEN 1
                            ELSE 0
                        END
                    ) AS waiting_payment,

                    SUM(
                        CASE
                            WHEN payment_status = ?
                            THEN 1
                            ELSE 0
                        END
                    ) AS paid

                FROM orders

                WHERE status != ?
                """,
                (
                    PAYMENT_STATUS_AWAITING_CONFIRMATION,

                    PAYMENT_STATUS_UNPAID,

                    PAYMENT_STATUS_UNPAID,
                    PAYMENT_STATUS_PENDING,

                    PAYMENT_STATUS_PAID,

                    STATUS_REJECTED,
                )
            )
            .fetchone()
        )


        return {

            "needs_confirmation":
                int(
                    row[
                        "needs_confirmation"
                    ]
                    or 0
                ),

            "waiting_payment":
                int(
                    row[
                        "waiting_payment"
                    ]
                    or 0
                ),

            "paid":
                int(
                    row[
                        "paid"
                    ]
                    or 0
                ),
        }


    except Exception:

        app.logger.exception(
            "[DRIVER PAYMENT SUMMARY ERROR]"
        )


        return {

            "needs_confirmation":
                0,

            "waiting_payment":
                0,

            "paid":
                0,
        }


    finally:

        if connection is not None:

            connection.close()
            
# ============================================================
# PHASE 20E
# DRIVER PAYMENT ORDERS
# ============================================================

def get_driver_payment_orders(
    payment_filter="all",
    payment_method="all"
):

    payment_filter = str(
        payment_filter
        or "all"
    ).strip().lower()


    payment_method = str(
        payment_method
        or "all"
    ).strip().upper()


    allowed_filters = {

        "all",

        "needs_confirmation",

        "waiting",

        "paid",
    }


    if payment_filter not in allowed_filters:

        payment_filter = "all"


    allowed_methods = {

        "ALL",

        PAYMENT_METHOD_CASH,

        PAYMENT_METHOD_QRIS,

        PAYMENT_METHOD_BANK_TRANSFER,
    }


    if payment_method not in allowed_methods:

        payment_method = "ALL"


    conditions = [

        "status != ?"

    ]


    parameters = [

        STATUS_REJECTED

    ]


    # ========================================================
    # PAYMENT STATUS FILTER
    # ========================================================

    if (
        payment_filter
        == "needs_confirmation"
    ):

        conditions.append(
            "payment_status = ?"
        )


        parameters.append(
            PAYMENT_STATUS_AWAITING_CONFIRMATION
        )


    elif (
        payment_filter
        == "waiting"
    ):

        conditions.append(
            """
            COALESCE(
                payment_status,
                ?
            )
            IN (?, ?)
            """
        )


        parameters.extend(
            [
                PAYMENT_STATUS_UNPAID,

                PAYMENT_STATUS_UNPAID,

                PAYMENT_STATUS_PENDING,
            ]
        )


    elif (
        payment_filter
        == "paid"
    ):

        conditions.append(
            "payment_status = ?"
        )


        parameters.append(
            PAYMENT_STATUS_PAID
        )


    # ========================================================
    # PAYMENT METHOD FILTER
    # ========================================================

    if (
        payment_method
        != "ALL"
    ):

        conditions.append(
            """
            COALESCE(
                payment_method,
                ?
            ) = ?
            """
        )


        parameters.extend(
            [
                PAYMENT_METHOD_CASH,

                payment_method,
            ]
        )


    where_sql = (
        " AND ".join(
            conditions
        )
    )


    sql = f"""
        SELECT

            id,

            order_code,

            customer_name,

            pickup,

            destination,

            fare,

            status,

            created_at,

            payment_method,

            payment_status,

            payment_amount,

            payment_customer_confirmed_at,

            payment_driver_confirmed_at,

            paid_at,

            payment_updated_at

        FROM orders

        WHERE
            {where_sql}

        ORDER BY id DESC

        LIMIT 100
    """


    connection = None


    try:

        connection = get_db()


        return (
            connection.execute(
                sql,
                tuple(
                    parameters
                )
            )
            .fetchall()
        )


    finally:

        if connection is not None:

            connection.close()
            
# ============================================================
# PHASE 20H.1
# CANONICAL PAYMENT HISTORY HELPERS
# ============================================================

def normalize_payment_history_period(
    value
):

    value = str(
        value
        or "all"
    ).strip().lower()


    if value not in {
        "all",
        "today",
        "7days",
        "30days",
    }:

        return "all"


    return value


def normalize_payment_history_method(
    value
):

    value = str(
        value
        or "ALL"
    ).strip().upper()


    if value not in {
        "ALL",
        PAYMENT_METHOD_CASH,
        PAYMENT_METHOD_QRIS,
        PAYMENT_METHOD_BANK_TRANSFER,
    }:

        return "ALL"


    return value


def normalize_payment_history_search(
    value
):

    value = " ".join(
        str(
            value
            or ""
        )
        .strip()
        .split()
    )


    return value[
        :PAYMENT_HISTORY_SEARCH_MAX_LENGTH
    ]


def get_driver_payment_history_page(
    connection,
    page=1,
    page_size=PAYMENT_HISTORY_PAGE_SIZE,
    period="all",
    payment_method="ALL",
    search=""
):
    """
    Canonical Payment History.

    Hanya transaksi valid yang masuk riwayat:
    - perjalanan SELESAI
    - pembayaran DIBAYAR
    - payment_amount > 0
    - paid_at tersedia
    - metode pembayaran dikenali

    Payment Control tetap terpisah dan dapat menampilkan
    pembayaran yang masih pending/belum dibayar.
    """

    try:

        page = int(
            page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1


    page = max(
        1,
        page
    )


    try:

        page_size = int(
            page_size
        )

    except (
        TypeError,
        ValueError
    ):

        page_size = (
            PAYMENT_HISTORY_PAGE_SIZE
        )


    page_size = max(
        1,
        min(
            page_size,
            PAYMENT_HISTORY_MAX_PAGE_SIZE
        )
    )


    period = (
        normalize_payment_history_period(
            period
        )
    )


    payment_method = (
        normalize_payment_history_method(
            payment_method
        )
    )


    search = (
        normalize_payment_history_search(
            search
        )
    )


    # ========================================================
    # CANONICAL CONDITIONS
    # ========================================================

    conditions = [
        "status = ?",
        "payment_status = ?",
        "payment_amount IS NOT NULL",
        "payment_amount > 0",
        "paid_at IS NOT NULL",
        """
        payment_method IN (
            ?, ?, ?
        )
        """,
    ]


    parameters = [
        STATUS_COMPLETED,
        PAYMENT_STATUS_PAID,
        PAYMENT_METHOD_CASH,
        PAYMENT_METHOD_QRIS,
        PAYMENT_METHOD_BANK_TRANSFER,
    ]


    # ========================================================
    # PERIOD
    # ========================================================

    now = datetime.now(
        APP_TZ
    )


    if period == "today":

        conditions.append(
            "paid_at LIKE ?"
        )


        parameters.append(
            now.strftime(
                "%Y-%m-%d"
            )
            + "%"
        )


    elif period == "7days":

        conditions.append(
            "paid_at >= ?"
        )


        parameters.append(
            (
                now
                -
                timedelta(
                    days=6
                )
            ).strftime(
                "%Y-%m-%d 00:00:00"
            )
        )


    elif period == "30days":

        conditions.append(
            "paid_at >= ?"
        )


        parameters.append(
            (
                now
                -
                timedelta(
                    days=29
                )
            ).strftime(
                "%Y-%m-%d 00:00:00"
            )
        )


    # ========================================================
    # PAYMENT METHOD
    # ========================================================

    if payment_method != "ALL":

        conditions.append(
            "payment_method = ?"
        )


        parameters.append(
            payment_method
        )


    # ========================================================
    # SEARCH
    # ========================================================

    if search:

        search_pattern = (
            "%"
            +
            search
            +
            "%"
        )


        conditions.append(
            """
            (
                order_code ILIKE ?
                OR customer_name ILIKE ?
                OR COALESCE(
                    payment_reference,
                    ''
                ) ILIKE ?
            )
            """
        )


        parameters.extend(
            [
                search_pattern,
                search_pattern,
                search_pattern,
            ]
        )


    where_sql = (
        " AND ".join(
            conditions
        )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    summary_row = (
        connection.execute(
            f"""
            SELECT

                COUNT(*) AS total_records,

                COALESCE(
                    SUM(payment_amount),
                    0
                ) AS paid_amount

            FROM orders

            WHERE {where_sql}
            """,
            tuple(
                parameters
            )
        )
        .fetchone()
    )


    total_records = int(
        summary_row[
            "total_records"
        ]
        or 0
    )


    paid_amount = int(
        summary_row[
            "paid_amount"
        ]
        or 0
    )


    # ========================================================
    # PAGINATION
    # ========================================================

    total_pages = (

        math.ceil(
            total_records
            /
            page_size
        )

        if total_records > 0

        else 0

    )


    if (
        total_pages > 0
        and
        page > total_pages
    ):

        page = (
            total_pages
        )


    offset = (
        (page - 1)
        *
        page_size
    )


    query_parameters = (
        list(
            parameters
        )
        +
        [
            page_size,
            offset,
        ]
    )


    # ========================================================
    # PAYMENT RECORDS
    # ========================================================

    rows = (
        connection.execute(
            f"""
            SELECT

                id,

                order_code,

                customer_name,

                whatsapp,

                fare,

                status,

                created_at,

                completed_at,

                payment_method,

                payment_status,

                payment_amount,

                payment_reference,

                payment_provider,

                payment_customer_confirmed_at,

                payment_driver_confirmed_at,

                paid_at,

                payment_updated_at

            FROM orders

            WHERE {where_sql}

            ORDER BY
                paid_at DESC,
                id DESC

            LIMIT ?

            OFFSET ?
            """,
            tuple(
                query_parameters
            )
        )
        .fetchall()
    )

    # ========================================================
    # PHASE 20H.4
    # PAYMENT DETAIL + RECEIPT INTEGRATION
    # ========================================================

    payments = []


    for row in rows:

        # ====================================================
        # RECEIPT ELIGIBILITY
        # ====================================================

        receipt_eligibility = (
            get_receipt_eligibility(
                row
            )
        )


        receipt_available = bool(
            receipt_eligibility[
                "eligible"
            ]
        )


        # ====================================================
        # PAYMENT METHOD LABEL
        # ====================================================

        row_payment_method = (
            row[
                "payment_method"
            ]
        )


        if (
            row_payment_method
            == PAYMENT_METHOD_QRIS
        ):

            payment_method_label = (
                "QRIS"
            )


        elif (
            row_payment_method
            == PAYMENT_METHOD_BANK_TRANSFER
        ):

            payment_method_label = (
                "Transfer Bank"
            )


        else:

            payment_method_label = (
                "Tunai"
            )


        # ====================================================
        # DRIVER URLS
        # ====================================================

        detail_url = (
            url_for(
                "driver_order_detail",
                order_id=
                    row[
                        "id"
                    ]
            )
        )


        receipt_url = (
            url_for(
                "driver_order_receipt",
                order_id=
                    row[
                        "id"
                    ]
            )

            if receipt_available

            else None
        )


        # ====================================================
        # PAYLOAD
        # ====================================================

        payments.append(
            {
                "id":
                    int(
                        row[
                            "id"
                        ]
                    ),

                "order_code":
                    row[
                        "order_code"
                    ],

                "customer_name":
                    row[
                        "customer_name"
                    ],

                "whatsapp":
                    row[
                        "whatsapp"
                    ],

                "order_status":
                    row[
                        "status"
                    ],

                "method":
                    row_payment_method,

                "method_label":
                    payment_method_label,

                "status":
                    row[
                        "payment_status"
                    ],

                # =============================================
                # CANONICAL PAYMENT AMOUNT
                # Tidak fallback ke fare.
                # =============================================

                "amount":
                    int(
                        row[
                            "payment_amount"
                        ]
                        or 0
                    ),

                "fare":
                    int(
                        row[
                            "fare"
                        ]
                        or 0
                    ),

                "reference":
                    row[
                        "payment_reference"
                    ],

                "provider":
                    row[
                        "payment_provider"
                    ],

                "customer_confirmed_at":
                    row[
                        "payment_customer_confirmed_at"
                    ],

                "driver_confirmed_at":
                    row[
                        "payment_driver_confirmed_at"
                    ],

                "paid_at":
                    row[
                        "paid_at"
                    ],

                "updated_at":
                    row[
                        "payment_updated_at"
                    ],

                "payment_time":
                    row[
                        "paid_at"
                    ],

                "created_at":
                    row[
                        "created_at"
                    ],

                "completed_at":
                    row[
                        "completed_at"
                    ],

                # =============================================
                # PHASE 20H.4
                # DETAIL INTEGRATION
                # =============================================

                "detail_url":
                    detail_url,

                # =============================================
                # PHASE 20H.4
                # RECEIPT INTEGRATION
                # =============================================

                "receipt_available":
                    receipt_available,

                "receipt_reason":
                    receipt_eligibility[
                        "reason"
                    ],

                "receipt_url":
                    receipt_url,
            }
        )


    # ========================================================
    # RESPONSE
    # ========================================================

    return {

        "payments":
            payments,

        "filters": {
            "period":
                period,

            # Gunakan filter yang dipilih, bukan metode row terakhir.
            "method":
                payment_method,

            "status":
                PAYMENT_STATUS_PAID,

            "q":
                search,
        },

        "summary": {
            "total_records":
                total_records,

            "paid_count":
                total_records,

            "unpaid_count":
                0,

            "pending_count":
                0,

            "paid_amount":
                paid_amount,
        },

        "pagination": {
            "page":
                page,

            "per_page":
                page_size,

            "total_pages":
                total_pages,

            "total_records":
                total_records,

            "has_previous":
                page > 1,

            "has_next":
                (
                    total_pages > 0
                    and
                    page < total_pages
                ),

            "result_start":
                (
                    offset + 1
                    if total_records > 0
                    else 0
                ),

            "result_end":
                (
                    min(
                        offset + len(
                            payments
                        ),
                        total_records
                    )
                    if total_records > 0
                    else 0
                ),

            "page_numbers":
                (
                    list(
                        range(
                            max(
                                1,
                                page - 2
                            ),
                            min(
                                total_pages,
                                page + 2
                            )
                            + 1
                        )
                    )
                    if total_pages > 0
                    else []
                ),
        },
    }


# ============================================================
# PHASE 20H.6
# DRIVER PAYMENT STATISTICS
# SAFE VERSION
# ============================================================

def get_driver_payment_statistics(
    connection,
    period="all"
):
    """
    Statistik pembayaran driver.

    Hanya menghitung transaksi:

    status = SELESAI
    payment_status = DIBAYAR
    payment_amount > 0
    paid_at != NULL
    """

    # ========================================================
    # NORMALIZE PERIOD
    # ========================================================

    period = (
        normalize_payment_history_period(
            period
        )
    )


    # ========================================================
    # BASE CONDITIONS
    # ========================================================

    conditions = [
        "status = ?",
        "payment_status = ?",
        "payment_amount IS NOT NULL",
        "payment_amount > 0",
        "paid_at IS NOT NULL",
    ]


    parameters = [
        STATUS_COMPLETED,
        PAYMENT_STATUS_PAID,
    ]


    # ========================================================
    # PERIOD
    # ========================================================

    now = datetime.now(
        APP_TZ
    )


    if period == "today":

        conditions.append(
            "paid_at LIKE ?"
        )

        parameters.append(
            now.strftime(
                "%Y-%m-%d"
            )
            + "%"
        )


    elif period == "7days":

        conditions.append(
            "paid_at >= ?"
        )

        parameters.append(
            (
                now
                -
                timedelta(
                    days=6
                )
            ).strftime(
                "%Y-%m-%d 00:00:00"
            )
        )


    elif period == "30days":

        conditions.append(
            "paid_at >= ?"
        )

        parameters.append(
            (
                now
                -
                timedelta(
                    days=29
                )
            ).strftime(
                "%Y-%m-%d 00:00:00"
            )
        )


    where_sql = (
        " AND ".join(
            conditions
        )
    )


    # ========================================================
    # QUERY
    #
    # Metode dibuat literal agar parameter SQL lebih sederhana
    # dan menghindari mismatch placeholder.
    # ========================================================

    row = (
        connection.execute(
            f"""
            SELECT

                COUNT(*) AS total_transactions,


                COALESCE(
                    SUM(payment_amount),
                    0
                ) AS total_received,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'TUNAI'
                            THEN payment_amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS cash_amount,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'QRIS'
                            THEN payment_amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS qris_amount,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'TRANSFER_BANK'
                            THEN payment_amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS transfer_amount,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'TUNAI'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS cash_transactions,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'QRIS'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS qris_transactions,


                COALESCE(
                    SUM(
                        CASE
                            WHEN payment_method = 'TRANSFER_BANK'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS transfer_transactions


            FROM orders

            WHERE {where_sql}
            """,
            tuple(
                parameters
            )
        )
        .fetchone()
    )


    # ========================================================
    # EMPTY PROTECTION
    # ========================================================

    if not row:

        return {
            "period":
                period,

            "total_received":
                0,

            "total_transactions":
                0,

            "average_transaction":
                0,

            "cash": {
                "amount":
                    0,

                "transactions":
                    0,
            },

            "qris": {
                "amount":
                    0,

                "transactions":
                    0,
            },

            "transfer": {
                "amount":
                    0,

                "transactions":
                    0,
            },

            "unclassified_amount":
                0,
        }


    # ========================================================
    # VALUES
    # ========================================================

    total_transactions = int(
        row.get(
            "total_transactions"
        )
        or 0
    )


    total_received = int(
        row.get(
            "total_received"
        )
        or 0
    )


    cash_amount = int(
        row.get(
            "cash_amount"
        )
        or 0
    )


    qris_amount = int(
        row.get(
            "qris_amount"
        )
        or 0
    )


    transfer_amount = int(
        row.get(
            "transfer_amount"
        )
        or 0
    )


    cash_transactions = int(
        row.get(
            "cash_transactions"
        )
        or 0
    )


    qris_transactions = int(
        row.get(
            "qris_transactions"
        )
        or 0
    )


    transfer_transactions = int(
        row.get(
            "transfer_transactions"
        )
        or 0
    )


    # ========================================================
    # CALCULATIONS
    # ========================================================

    if total_transactions > 0:

        average_transaction = int(
            round(
                total_received
                /
                total_transactions
            )
        )

    else:

        average_transaction = 0


    classified_amount = (
        cash_amount
        +
        qris_amount
        +
        transfer_amount
    )


    unclassified_amount = max(
        0,
        total_received
        -
        classified_amount
    )


    # ========================================================
    # RETURN
    # ========================================================

    return {
        "period":
            period,

        "total_received":
            total_received,

        "total_transactions":
            total_transactions,

        "average_transaction":
            average_transaction,

        "cash": {
            "amount":
                cash_amount,

            "transactions":
                cash_transactions,
        },

        "qris": {
            "amount":
                qris_amount,

            "transactions":
                qris_transactions,
        },

        "transfer": {
            "amount":
                transfer_amount,

            "transactions":
                transfer_transactions,
        },

        "unclassified_amount":
            unclassified_amount,
    }


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
    
    try:

        payment_method = (
            parse_payment_method(
                data.get(
                    "payment_method",
                    PAYMENT_METHOD_CASH
                )
            )
        )

    except ValueError as error:

        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(
                        error
                    ),
            }
        ), 400


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

            # ================================================
            # PHASE 19E
            # PRIVATE REVIEW TOKEN
            # ================================================

            review_token = (
                generate_review_token()
            )


            review_token_hash = (
                hash_review_token(
                    review_token
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

                    destination_lon,

                    review_token_hash
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
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

                    review_token_hash,
                )
            )

            # ========================================================
            # PHASE 20A
            # INITIAL PAYMENT
            # ========================================================

            payment = (
                initialize_order_payment(
                    connection,
                    order_code,
                    trip[
                        "fare"
                    ],
                    payment_method
                )
            )


            # ========================================================
            # PHASE 20G.2
            # INITIALIZE RECEIPT SECURITY
            # ========================================================

            receipt_token = (
                initialize_receipt_access(
                    connection,
                    order_code
                )
            )

            connection.commit()

        except Exception:

            connection.rollback()

            raise

        finally:

            connection.close()


        return jsonify(
            {
                "success":
                    True,
                    
                "receipt_token":
                    receipt_token,

                "order_code":
                    order_code,

                "review_token":
                    review_token,
                    
                "payment":
                    payment,

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

        app.logger.exception(
            "[CREATE ORDER ERROR]"
        )


        response_data = {
            "success":
                False,

            "message":
                "Pesanan gagal dibuat.",
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
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

    order=
        order,

    payment=
        order_payment_payload(
            order
        )
)
    
# ============================================================
# PHASE 20G.2
# SECURE CUSTOMER DIGITAL RECEIPT API
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/receipt",
    methods=["GET"]
)
def customer_payment_receipt_api(
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    generic_denied_message = (
        "Struk tidak ditemukan "
        "atau akses tidak valid."
    )


    # ========================================================
    # INVALID ORDER CODE
    # ========================================================

    if not order_code:

        return receipt_json_response(
            {
                "success":
                    False,

                "message":
                    generic_denied_message,
            },
            404
        )


    # ========================================================
    # RATE LIMIT
    # ========================================================

    if receipt_access_is_limited(
        order_code
    ):

        return receipt_json_response(
            {
                "success":
                    False,

                "message":
                    (
                        "Terlalu banyak percobaan. "
                        "Silakan coba kembali nanti."
                    ),
            },
            429
        )


    # ========================================================
    # RECEIPT TOKEN
    # ========================================================

    receipt_token = str(
        request.headers.get(
            "X-Receipt-Token",
            ""
        )
        or ""
    ).strip()


    if not receipt_token:

        record_receipt_access_failure(
            order_code
        )


        return receipt_json_response(
            {
                "success":
                    False,

                "message":
                    generic_denied_message,
            },
            404
        )


    connection = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        # ====================================================
        # DO NOT LEAK ORDER EXISTENCE
        # ====================================================

        if not order:

            record_receipt_access_failure(
                order_code
            )


            return receipt_json_response(
                {
                    "success":
                        False,

                    "message":
                        generic_denied_message,
                },
                404
            )


        # ====================================================
        # TOKEN VERIFICATION
        # ====================================================

        token_valid = (
            verify_receipt_token(
                receipt_token,

                order.get(
                    "receipt_token_hash"
                )
            )
        )


        if not token_valid:

            record_receipt_access_failure(
                order_code
            )


            return receipt_json_response(
                {
                    "success":
                        False,

                    "message":
                        generic_denied_message,
                },
                404
            )


        clear_receipt_access_failures(
            order_code
        )


        # ====================================================
        # ELIGIBILITY
        # ====================================================

        eligibility = (
            get_receipt_eligibility(
                order
            )
        )


        if not eligibility[
            "eligible"
        ]:

            return receipt_json_response(
                {
                    "success":
                        False,

                    "available":
                        False,

                    "message":
                        (
                            "Struk pembayaran "
                            "belum tersedia."
                        ),
                },
                409
            )


        # ====================================================
        # RECEIPT
        # ====================================================

        receipt = (
            build_payment_receipt(
                order
            )
        )


        return receipt_json_response(
            {
                "success":
                    True,

                "available":
                    True,

                "receipt":
                    receipt,
            },
            200
        )


    except Exception as error:

        app.logger.exception(
            "[SECURE RECEIPT ERROR]"
        )


        response_data = {
            "success":
                False,

            "message":
                (
                    "Struk pembayaran belum "
                    "dapat dimuat."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return receipt_json_response(
            response_data,
            500
        )


    finally:

        if connection is not None:

            connection.close()


# ============================================================
# PHASE 20D
# CUSTOMER PAYMENT CONFIRMATION
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/payment/confirm",
    methods=["POST"]
)
def customer_confirm_payment(
    order_code
):

    connection = (
        get_db()
    )


    try:

        # ====================================================
        # FIND ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT
                    *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
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
        # CUSTOMER SECRET TOKEN
        # PHASE 19E
        # ====================================================

        supplied_token = (
            get_supplied_review_token()
        )


        if not review_token_is_valid(
            order[
                "review_token_hash"
            ],
            supplied_token
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "access_denied":
                        True,

                    "message":
                        (
                            "Akses pembayaran untuk "
                            "pesanan ini tidak valid."
                        ),
                }
            ), 403


        # ====================================================
        # MARK PAYMENT SUBMITTED
        # ====================================================

        result = (
            mark_customer_payment_submitted(
                connection,
                order
            )
        )


        connection.commit()


        if result[
            "already_paid"
        ]:

            message = (
                "Pembayaran sudah dikonfirmasi."
            )


        elif result[
            "already_submitted"
        ]:

            message = (
                "Pembayaran sudah menunggu "
                "konfirmasi driver."
            )


        else:

            message = (
                "Konfirmasi pembayaran berhasil "
                "dikirim ke driver."
            )


        return jsonify(
            {
                "success":
                    True,

                "already_paid":
                    result[
                        "already_paid"
                    ],

                "already_submitted":
                    result[
                        "already_submitted"
                    ],

                "payment":
                    result[
                        "payment"
                    ],

                "message":
                    message,
            }
        )


    except ValueError as error:

        connection.rollback()


        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(
                        error
                    ),
            }
        ), 400


    except Exception as error:

        connection.rollback()


        app.logger.exception(
            "[CUSTOMER PAYMENT CONFIRM ERROR]"
        )


        response_data = {

            "success":
                False,

            "message":
                (
                    "Konfirmasi pembayaran "
                    "belum berhasil."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
        ), 500


    finally:

        connection.close()
        
        # ============================================================
# PHASE 20I.3B
# CUSTOMER REFUND REQUEST API
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/refund-request",
    methods=["POST"]
)
def customer_request_payment_refund(
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    reason = (
        data.get(
            "reason",
            ""
        )
    )


    connection = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
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
                        (
                            "Pesanan tidak ditemukan "
                            "atau akses tidak valid."
                        ),
                }
            ), 404


        # ====================================================
        # CUSTOMER PRIVATE TOKEN
        #
        # Menggunakan security mechanism yang sudah dipakai
        # untuk payment confirmation / review.
        # ====================================================

        supplied_token = (
            get_supplied_review_token()
        )


        if not review_token_is_valid(
            order.get(
                "review_token_hash"
            ),
            supplied_token
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "access_denied":
                        True,

                    "message":
                        (
                            "Akses pengembalian dana "
                            "untuk pesanan ini tidak valid."
                        ),
                }
            ), 403


        # ====================================================
        # SUBMIT
        # ====================================================

        result = (
            submit_customer_refund_request(
                connection,
                order,
                reason
            )
        )


        # ====================================================
        # UPDATE + AUDIT COMMIT TOGETHER
        # ====================================================

        connection.commit()


        if result[
            "already_requested"
        ]:

            message = (
                "Permintaan pengembalian dana "
                "sudah dikirim sebelumnya."
            )

        else:

            message = (
                "Permintaan pengembalian dana "
                "berhasil dikirim ke driver."
            )


        response = jsonify(
            {
                "success":
                    True,

                "already_requested":
                    result[
                        "already_requested"
                    ],

                "refund_request":
                    result[
                        "refund_request"
                    ],

                "message":
                    message,
            }
        )


        response.headers[
            "Cache-Control"
        ] = (
            "no-store, no-cache, "
            "must-revalidate, max-age=0"
        )


        return response


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(
                        error
                    ),
            }
        ), 400


    except RuntimeError as error:

        if connection is not None:

            connection.rollback()


        return jsonify(
            {
                "success":
                    False,

                "message":
                    str(
                        error
                    ),
            }
        ), 409


    except Exception as error:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[CUSTOMER REFUND REQUEST ERROR]"
        )


        response_data = {
            "success":
                False,

            "message":
                (
                    "Permintaan pengembalian dana "
                    "belum dapat diproses."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
        ), 500


    finally:

        if connection is not None:

            connection.close()

# ============================================================
# CUSTOMER LIVE STATUS API
# PHASE 10 + PHASE 11.5 + PAYMENT / REFUND SAFE
# ============================================================

@app.route(
    "/api/orders/<string:order_code>/status",
    methods=["GET"]
)
def get_customer_order_status(
    order_code
):

    connection = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # ORDER
        #
        # Gunakan SELECT * karena payment/refund terus
        # berkembang dan live status membutuhkan payload
        # order terbaru secara lengkap.
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        # ====================================================
        # ORDER NOT FOUND
        # ====================================================

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
        # DRIVER PROFILE
        # ====================================================

        profile = None

        driver_trust = None


        if (
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


            driver_trust = (
                get_public_driver_trust(
                    connection,
                    profile
                )
            )


        # ====================================================
        # PAYMENT
        # ====================================================

        payment_payload = (
            order_payment_payload(
                order
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        response = jsonify(
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


                    # =========================================
                    # LIVE JOURNEY STATUS
                    # =========================================

                    "status":
                        order[
                            "status"
                        ],


                    # =========================================
                    # PAYMENT
                    # =========================================

                    "payment":
                        payment_payload,


                    "created_at":
                        order[
                            "created_at"
                        ],


                    # =========================================
                    # DRIVER PROFILE
                    # =========================================

                    "driver_profile":
                        driver_profile_payload(
                            profile
                        ),


                    # =========================================
                    # DRIVER TRUST
                    # =========================================

                    "driver_trust":
                        driver_trust,


                    # =========================================
                    # JOURNEY TIMESTAMPS
                    # =========================================

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


        # ====================================================
        # LIVE STATUS MUST NEVER BE CACHED
        # ====================================================

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


        response.headers[
            "Expires"
        ] = "0"


        return response


    except Exception as error:

        app.logger.exception(
            "[CUSTOMER LIVE STATUS ERROR]"
        )


        response_data = {

            "success":
                False,

            "message":
                (
                    "Status perjalanan belum "
                    "dapat diperbarui."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        response = jsonify(
            response_data
        )


        response.status_code = 500


        response.headers[
            "Cache-Control"
        ] = (
            "no-store, "
            "no-cache, "
            "must-revalidate, "
            "max-age=0"
        )


        return response


    finally:

        if connection is not None:

            connection.close()

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
# PHASE 19F.1
# DRIVER REVIEW HISTORY PAYLOAD
# ============================================================

def driver_review_history_payload(
    review
):

    if not review:

        return None


    return {

        "review_id":
            int(
                review[
                    "review_id"
                ]
            ),

        "order_id":
            int(
                review[
                    "order_id"
                ]
            ),

        "order_code":
            review[
                "order_code"
            ],

        "customer_name":
            review[
                "customer_name"
            ],

        "rating":
            int(
                review[
                    "rating"
                ]
                or 0
            ),

        "feedback":
            (
                review[
                    "feedback"
                ]
                or ""
            ).strip(),

        "tags":
            decode_review_tags(
                review[
                    "tags"
                ]
            ),

        "review_created_at":
            review[
                "review_created_at"
            ],

        "completed_at":
            review[
                "completed_at"
            ],

        "pickup":
            review[
                "pickup"
            ],

        "destination":
            review[
                "destination"
            ],

        "distance_km":
            float(
                review[
                    "distance_km"
                ]
                or 0
            ),

        "duration_minutes":
            int(
                review[
                    "duration_minutes"
                ]
                or 0
            ),

        "fare":
            int(
                review[
                    "fare"
                ]
                or 0
            ),
    }
    
    # ============================================================
# PHASE 19F.2
# REVIEW RATING FILTER
# ============================================================

def normalize_review_rating_filter(
    value
):

    if value is None:

        return None


    value = str(
        value
    ).strip().lower()


    if value in (
        "",
        "all",
        "semua"
    ):

        return None


    try:

        rating = int(
            value
        )

    except (
        TypeError,
        ValueError
    ):

        return None


    if rating not in (
        1,
        2,
        3,
        4,
        5
    ):

        return None


    return rating

# ============================================================
# PHASE 19F.3
# NORMALIZE REVIEW SEARCH
# ============================================================

def normalize_review_search(
    value
):

    if value is None:

        return ""


    value = str(
        value
    )


    # Hilangkan spasi berlebihan.
    value = " ".join(
        value
        .strip()
        .split()
    )


    return value
    
# ============================================================
# PHASE 19F.4
# DRIVER REVIEW STATISTICS
# ============================================================

def get_driver_review_statistics(
    connection
):

    # ========================================================
    # DATABASE STATISTICS
    # ========================================================

    row = (
        connection.execute(
            """
            SELECT

                COUNT(*)
                    AS total_reviews,

                COALESCE(
                    AVG(r.rating),
                    0
                )
                    AS average_rating,


                SUM(
                    CASE
                        WHEN r.rating = 5
                        THEN 1
                        ELSE 0
                    END
                )
                    AS rating_5,

                SUM(
                    CASE
                        WHEN r.rating = 4
                        THEN 1
                        ELSE 0
                    END
                )
                    AS rating_4,

                SUM(
                    CASE
                        WHEN r.rating = 3
                        THEN 1
                        ELSE 0
                    END
                )
                    AS rating_3,

                SUM(
                    CASE
                        WHEN r.rating = 2
                        THEN 1
                        ELSE 0
                    END
                )
                    AS rating_2,

                SUM(
                    CASE
                        WHEN r.rating = 1
                        THEN 1
                        ELSE 0
                    END
                )
                    AS rating_1,


                SUM(
                    CASE
                        WHEN r.rating >= 4
                        THEN 1
                        ELSE 0
                    END
                )
                    AS positive_reviews,


                SUM(
                    CASE
                        WHEN
                            NULLIF(
                                TRIM(
                                    COALESCE(
                                        r.feedback,
                                        ''
                                    )
                                ),
                                ''
                            )
                            IS NOT NULL

                        THEN 1
                        ELSE 0
                    END
                )
                    AS feedback_count

            FROM order_reviews r

            INNER JOIN orders o
                ON o.id = r.order_id

            WHERE o.status = ?
            """,
            (
                STATUS_COMPLETED,
            )
        )
        .fetchone()
    )


    # ========================================================
    # TOTAL REVIEWS
    # ========================================================

    total_reviews = int(
        row[
            "total_reviews"
        ]
        or 0
    )


    # ========================================================
    # AVERAGE RATING
    # ========================================================

    average_rating = round(
        float(
            row[
                "average_rating"
            ]
            or 0
        ),
        1
    )


    # ========================================================
    # RATING COUNTS
    # ========================================================

    rating_counts = {

        5:
            int(
                row[
                    "rating_5"
                ]
                or 0
            ),

        4:
            int(
                row[
                    "rating_4"
                ]
                or 0
            ),

        3:
            int(
                row[
                    "rating_3"
                ]
                or 0
            ),

        2:
            int(
                row[
                    "rating_2"
                ]
                or 0
            ),

        1:
            int(
                row[
                    "rating_1"
                ]
                or 0
            ),
    }


    # ========================================================
    # RATING DISTRIBUTION
    # ========================================================

    distribution = {}


    for rating in (
        5,
        4,
        3,
        2,
        1
    ):

        count = (
            rating_counts[
                rating
            ]
        )


        percentage = (

            round(
                (
                    count
                    /
                    total_reviews
                )
                * 100,
                1
            )

            if total_reviews > 0

            else 0.0

        )


        distribution[
            str(
                rating
            )
        ] = {

            "count":
                count,

            "percentage":
                percentage,
        }


    # ========================================================
    # POSITIVE RATING
    # ========================================================

    positive_reviews = int(
        row[
            "positive_reviews"
        ]
        or 0
    )


    positive_percentage = (

        round(
            (
                positive_reviews
                /
                total_reviews
            )
            * 100,
            1
        )

        if total_reviews > 0

        else 0.0

    )


    # ========================================================
    # FEEDBACK COUNT
    # ========================================================

    feedback_count = int(
        row[
            "feedback_count"
        ]
        or 0
    )


    # ========================================================
    # REPUTATION LABEL
    # ========================================================

    if total_reviews == 0:

        reputation_label = (
            "Belum Ada Ulasan"
        )


    elif total_reviews < 3:

        reputation_label = (
            "Mulai Terbentuk"
        )


    elif average_rating >= 4.8:

        reputation_label = (
            "Pelayanan Istimewa"
        )


    elif average_rating >= 4.5:

        reputation_label = (
            "Sangat Baik"
        )


    elif average_rating >= 4.0:

        reputation_label = (
            "Pelayanan Baik"
        )


    elif average_rating >= 3.0:

        reputation_label = (
            "Cukup Baik"
        )


    else:

        reputation_label = (
            "Terus Tingkatkan"
        )


    # ========================================================
    # RESULT
    # ========================================================

    return {

        "total_reviews":
            total_reviews,

        "average_rating":
            average_rating,

        "positive_reviews":
            positive_reviews,

        "positive_percentage":
            positive_percentage,

        "feedback_count":
            feedback_count,

        "reputation_label":
            reputation_label,

        "distribution":
            distribution,
    }

# ============================================================
# PHASE 19F.3
# DRIVER REVIEW HISTORY
# RATING FILTER + SEARCH + PAGINATION
# ============================================================

def get_driver_review_history_page(
    connection,
    page=1,
    page_size=REVIEW_HISTORY_PAGE_SIZE,
    rating=None,
    search=""
):

    # ========================================================
    # SAFE PAGE
    # ========================================================

    try:

        page = int(
            page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1


    page = max(
        1,
        page
    )


    # ========================================================
    # SAFE PAGE SIZE
    # ========================================================

    try:

        page_size = int(
            page_size
        )

    except (
        TypeError,
        ValueError
    ):

        page_size = (
            REVIEW_HISTORY_PAGE_SIZE
        )


    page_size = max(
        1,
        min(
            page_size,
            REVIEW_HISTORY_MAX_PAGE_SIZE
        )
    )


    # ========================================================
    # RATING
    # ========================================================

    rating = (
        normalize_review_rating_filter(
            rating
        )
    )


    # ========================================================
    # SEARCH
    # ========================================================

    search = (
        normalize_review_search(
            search
        )
    )


    # ========================================================
    # WHERE
    # ========================================================

    where_parts = [

        "o.status = ?"

    ]


    where_params = [

        STATUS_COMPLETED

    ]


    # ========================================================
    # RATING FILTER
    # ========================================================

    if rating is not None:

        where_parts.append(
            "r.rating = ?"
        )


        where_params.append(
            rating
        )


    # ========================================================
    # SEARCH FILTER
    # ========================================================

    if search:

        search_pattern = (
            "%"
            +
            search
            +
            "%"
        )


        where_parts.append(
            """
            (
                o.order_code ILIKE ?
                OR
                o.customer_name ILIKE ?
                OR
                COALESCE(
                    r.feedback,
                    ''
                ) ILIKE ?
                OR
                o.pickup ILIKE ?
                OR
                o.destination ILIKE ?
            )
            """
        )


        where_params.extend(
            [
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
                search_pattern,
            ]
        )


    # ========================================================
    # BUILD WHERE SQL
    # ========================================================

    where_sql = (
        " AND ".join(
            where_parts
        )
    )


    # ========================================================
    # TOTAL FILTERED REVIEWS
    # ========================================================

    total_row = (
        connection.execute(
            f"""
            SELECT
                COUNT(*) AS total

            FROM order_reviews r

            INNER JOIN orders o
                ON o.id = r.order_id

            WHERE {where_sql}
            """,
            tuple(
                where_params
            )
        )
        .fetchone()
    )


    total = int(
        total_row[
            "total"
        ]
        or 0
    )


    # ========================================================
    # TOTAL PAGES
    # ========================================================

    total_pages = (

        math.ceil(
            total
            /
            page_size
        )

        if total > 0

        else 0

    )


    # ========================================================
    # NORMALIZE CURRENT PAGE
    # ========================================================

    if (
        total_pages > 0
        and
        page > total_pages
    ):

        page = (
            total_pages
        )


    offset = (
        (page - 1)
        *
        page_size
    )


    # ========================================================
    # FINAL QUERY PARAMS
    # ========================================================

    query_params = (

        where_params
        +
        [
            page_size,
            offset,
        ]

    )


    # ========================================================
    # REVIEW DATA
    # ========================================================

    rows = (
        connection.execute(
            f"""
            SELECT

                r.id
                    AS review_id,

                r.order_id
                    AS order_id,

                r.rating
                    AS rating,

                r.feedback
                    AS feedback,

                r.tags
                    AS tags,

                r.created_at
                    AS review_created_at,


                o.order_code
                    AS order_code,

                o.customer_name
                    AS customer_name,

                o.pickup
                    AS pickup,

                o.destination
                    AS destination,

                o.distance_km
                    AS distance_km,

                o.duration_minutes
                    AS duration_minutes,

                o.fare
                    AS fare,

                o.completed_at
                    AS completed_at

            FROM order_reviews r

            INNER JOIN orders o
                ON o.id = r.order_id

            WHERE {where_sql}

            ORDER BY
                r.id DESC

            LIMIT ?

            OFFSET ?
            """,
            tuple(
                query_params
            )
        )
        .fetchall()
    )


    # ========================================================
    # PAYLOAD
    # ========================================================

    reviews = [

        driver_review_history_payload(
            row
        )

        for row
        in rows

    ]


    # ========================================================
    # RESPONSE DATA
    # ========================================================

    return {

        "reviews":
            reviews,

        "filters": {

            "rating":
                rating,

            "search":
                search,

        },

        "pagination": {

            "page":
                page,

            "page_size":
                page_size,

            "total":
                total,

            "total_pages":
                total_pages,

            "has_previous":
                page > 1,

            "has_next":
                (
                    total_pages > 0
                    and
                    page < total_pages
                ),

        },

    }
# ============================================================
# PHASE 19E
# REVIEW SECURITY HELPERS
# ============================================================

def generate_review_token():

    return secrets.token_urlsafe(
        REVIEW_TOKEN_BYTES
    )


def hash_review_token(
    token
):

    token = str(
        token or ""
    ).strip()


    if not token:

        return ""


    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def review_token_is_valid(
    stored_hash,
    supplied_token
):

    stored_hash = str(
        stored_hash or ""
    ).strip()


    supplied_hash = (
        hash_review_token(
            supplied_token
        )
    )


    if (
        not stored_hash
        or not supplied_hash
    ):

        return False


    return secrets.compare_digest(
        stored_hash,
        supplied_hash
    )


def get_supplied_review_token():

    return (
        request.headers.get(
            "X-Review-Token",
            ""
        )
        .strip()
    )


def sanitize_review_feedback(
    value
):

    feedback = str(
        value or ""
    )


    # Hilangkan karakter kontrol yang
    # tidak diperlukan.
    feedback = re.sub(
        r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]",
        "",
        feedback
    )


    # Rapikan spasi horizontal.
    feedback = re.sub(
        r"[ \t]+",
        " ",
        feedback
    )


    # Maksimal dua newline berturut-turut.
    feedback = re.sub(
        r"\n{3,}",
        "\n\n",
        feedback
    )


    return feedback.strip()


def parse_app_timestamp(
    value
):

    if not value:

        return None


    try:

        parsed = datetime.strptime(
            str(
                value
            ).strip(),
            "%Y-%m-%d %H:%M:%S"
        )


        return parsed.replace(
            tzinfo=APP_TZ
        )


    except (
        TypeError,
        ValueError
    ):

        return None


def review_window_is_open(
    completed_at,
    created_at=None
):

    completed_time = (
        parse_app_timestamp(
            completed_at
        )
        or
        parse_app_timestamp(
            created_at
        )
    )


    if not completed_time:

        return False


    deadline = (
        completed_time
        +
        timedelta(
            days=REVIEW_WINDOW_DAYS
        )
    )


    return (
        datetime.now(
            APP_TZ
        )
        <= deadline
    )


def review_rate_limit_allowed(
    client_ip
):

    now = time.time()


    cutoff = (
        now
        -
        REVIEW_RATE_WINDOW_SECONDS
    )


    with review_attempts_lock:

        attempts = [

            attempt_time

            for attempt_time
            in review_attempts.get(
                client_ip,
                []
            )

            if attempt_time >= cutoff
        ]


        if (
            len(
                attempts
            )
            >= REVIEW_POST_LIMIT
        ):

            review_attempts[
                client_ip
            ] = attempts


            return False


        attempts.append(
            now
        )


        review_attempts[
            client_ip
        ] = attempts


    return True

# ============================================================
# PHASE 19A + 19B + 19E
# SECURE CUSTOMER ORDER REVIEW
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

    # ========================================================
    # POST RATE LIMIT
    # ========================================================

    if (
        request.method
        == "POST"
    ):

        client_ip = (
            get_client_ip()
        )


        if not review_rate_limit_allowed(
            client_ip
        ):

            response = jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Terlalu banyak percobaan. "
                            "Silakan tunggu beberapa menit."
                        ),
                }
            )


            response.status_code = 429


            response.headers[
                "Retry-After"
            ] = str(
                REVIEW_RATE_WINDOW_SECONDS
            )


            return response


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

                    status,

                    created_at,

                    completed_at,

                    review_token_hash

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
        # PRIVATE REVIEW TOKEN
        # ====================================================

        supplied_token = (
            get_supplied_review_token()
        )


        if not review_token_is_valid(
            order[
                "review_token_hash"
            ],
            supplied_token
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "eligible":
                        False,

                    "access_denied":
                        True,

                    "message":
                        (
                            "Akses penilaian untuk "
                            "perjalanan ini tidak valid."
                        ),
                }
            ), 403


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
        # REVIEW WINDOW
        # ====================================================

        window_open = (
            review_window_is_open(
                order[
                    "completed_at"
                ],

                order[
                    "created_at"
                ]
            )
        )


        # ====================================================
        # GET
        # ====================================================

        if (
            request.method
            == "GET"
        ):

            eligible = (
                order[
                    "status"
                ]
                == STATUS_COMPLETED

                and

                window_open

                and

                existing_review
                is None
            )


            return jsonify(
                {
                    "success":
                        True,

                    "eligible":
                        eligible,

                    "window_open":
                        window_open,

                    "review_window_days":
                        REVIEW_WINDOW_DAYS,

                    "review":
                        customer_review_payload(
                            existing_review
                        ),
                }
            )


        # ====================================================
        # COMPLETED ONLY
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
        # IDEMPOTENT DUPLICATE PROTECTION
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
        # REVIEW WINDOW CLOSED
        # ====================================================

        if not window_open:

            return jsonify(
                {
                    "success":
                        False,

                    "window_closed":
                        True,

                    "message":
                        (
                            "Waktu untuk memberikan "
                            "penilaian perjalanan ini "
                            "sudah berakhir."
                        ),
                }
            ), 403


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
            sanitize_review_feedback(
                data.get(
                    "feedback",
                    ""
                )
            )
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
        # RATING
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
        # FEEDBACK
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


        created_at = (
            current_timestamp()
        )


        encoded_tags = (
            encode_review_tags(
                tags
            )
        )


        # ====================================================
        # SAVE
        # ====================================================

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

                    encoded_tags,

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
            "[SECURE REVIEW ERROR]",
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
                        "diproses."
                    ),
            }
        ), 500


    finally:

        connection.close()
        
# ============================================================
# PHASE 19F.4
# DRIVER REVIEW HISTORY API
# FILTER + SEARCH + STATISTICS
# ============================================================

@app.route(
    "/api/driver/reviews",
    methods=["GET"]
)
@driver_api_required
def driver_review_history_api():

    connection = None


    try:

        # ====================================================
        # PAGE
        # ====================================================

        raw_page = str(
            request.args.get(
                "page",
                "1"
            )
            or "1"
        ).strip()


        try:

            page = int(
                raw_page
            )

        except (
            TypeError,
            ValueError
        ):

            page = 1


        page = max(
            1,
            page
        )


        # ====================================================
        # RATING
        # ====================================================

        raw_rating = str(
            request.args.get(
                "rating",
                ""
            )
            or ""
        ).strip()


        rating = (
            normalize_review_rating_filter(
                raw_rating
            )
        )


        if (
            raw_rating
            and
            raw_rating.lower()
            not in (
                "all",
                "semua"
            )
            and
            rating is None
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Filter rating harus "
                            "bernilai 1 sampai 5."
                        ),
                }
            ), 400


        # ====================================================
        # SEARCH
        # ====================================================

        raw_search = str(
            request.args.get(
                "search",
                ""
            )
            or ""
        )


        search = (
            normalize_review_search(
                raw_search
            )
        )


        if (
            len(
                search
            )
            >
            REVIEW_HISTORY_SEARCH_MAX_LENGTH
        ):

            return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Pencarian maksimal "
                            f"{REVIEW_HISTORY_SEARCH_MAX_LENGTH} "
                            "karakter."
                        ),
                }
            ), 400


        # ====================================================
        # DATABASE
        # ====================================================

        connection = (
            get_db()
        )


        # ====================================================
        # REVIEW HISTORY
        # ====================================================

        result = (
            get_driver_review_history_page(
                connection,
                page=page,
                rating=rating,
                search=search
            )
        )


        # ====================================================
        # REVIEW STATISTICS
        # ====================================================

        statistics = (
            get_driver_review_statistics(
                connection
            )
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify(
            {
                "success":
                    True,

                "statistics":
                    statistics,

                "reviews":
                    result[
                        "reviews"
                    ],

                "filters":
                    result[
                        "filters"
                    ],

                "pagination":
                    result[
                        "pagination"
                    ],
            }
        )


    except Exception as error:

        app.logger.exception(
            "[DRIVER REVIEW HISTORY ERROR]"
        )


        response_data = {

            "success":
                False,

            "message":
                (
                    "Riwayat ulasan belum "
                    "dapat dimuat."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
        ), 500


    finally:

        if connection is not None:

            connection.close()

# ============================================================
# PHASE 19F.5
# DRIVER REVIEW HISTORY
# ============================================================

@app.route(
    '/api/driver/review-history',
    methods=[
        'GET'
    ]
)
@driver_api_required
def driver_review_history():

    # ========================================================
    # PARAMETERS
    # ========================================================

    page = (
        request.args.get(
            'page',
            1,
            type=int
        )
    )

    rating = (
        request.args.get(
            'rating',
            '',
            type=str
        )
    )

    search = (
        request.args.get(
            'search',
            '',
            type=str
        )
    )

    # ========================================================
    # DATABASE
    # ========================================================

    connection = (
        get_db()
    )


    try:

        # ========================================================
        # REVIEW HISTORY
        # ========================================================

        result = (
            get_driver_review_history_page(
                connection,
                page=page,
                rating=rating,
                search=search
                
                )
            )


        # ========================================================
        # REVIEW STATISTICS
        # ========================================================

        statistics = (
            get_driver_review_statistics(
                 connection
                
                )
            )

    except Exception:

        app.logger.exception(
                "[DRIVER REVIEW HISTORY ERROR]"
            )


        return jsonify(
                {
                    "success":
                        False,

                    "message":
                        (
                            "Riwayat ulasan belum "
                            "dapat dimuat."
                        ),
                }
            ), 500

    finally:

        connection.close()


    # ========================================================
    # RESPONSE
    # ========================================================

    return jsonify(
        {
            "success":
                True,


            # ====================================================
            # STATISTICS
            # ====================================================

            "statistics":
                statistics,


            # ====================================================
            # REVIEW HISTORY
            # ====================================================

            "reviews":
                result[
                    "reviews"
                ],


            # ====================================================
            # ACTIVE FILTERS
            # ====================================================

            "filters":
                result[
                    "filters"
                ],


            # ====================================================
            # PAGINATION
            # ====================================================

            "pagination":
                result[
                    "pagination"
                ],

        }
    )

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

        # ====================================================
        # PHASE 19C
        # DRIVER REPUTATION
        # ====================================================

        reputation_row = (
            connection.execute(
                """
                SELECT

                    COUNT(*) AS review_count,

                    COALESCE(
                        AVG(r.rating),
                        0
                    ) AS average_rating,

                    COUNT(
                        CASE
                            WHEN r.rating = 5
                            THEN 1
                        END
                    ) AS rating_5,

                    COUNT(
                        CASE
                            WHEN r.rating = 4
                            THEN 1
                        END
                    ) AS rating_4,

                    COUNT(
                        CASE
                            WHEN r.rating = 3
                            THEN 1
                        END
                    ) AS rating_3,

                    COUNT(
                        CASE
                            WHEN r.rating = 2
                            THEN 1
                        END
                    ) AS rating_2,

                    COUNT(
                        CASE
                            WHEN r.rating = 1
                            THEN 1
                        END
                    ) AS rating_1

                FROM order_reviews r

                INNER JOIN orders o
                    ON o.id = r.order_id

                WHERE o.status = ?
                """,
                (
                    STATUS_COMPLETED,
                )
            )
            .fetchone()
        )


        review_count = int(
            reputation_row[
                "review_count"
            ]
            or 0
        )


        average_rating = round(
            float(
                reputation_row[
                    "average_rating"
                ]
                or 0
            ),
            1
        )


        # ====================================================
        # RATING DISTRIBUTION
        # ====================================================

        rating_distribution = {}


        for star in range(
            5,
            0,
            -1
        ):

            count = int(
                reputation_row[
                    f"rating_{star}"
                ]
                or 0
            )


            percentage = (
                round(
                    (
                        count
                        /
                        review_count
                    )
                    * 100
                )
                if review_count > 0
                else 0
            )


            rating_distribution[
                star
            ] = {

                "count":
                    count,

                "percentage":
                    percentage,
            }


        # ====================================================
        # REPUTATION BADGE
        # ====================================================

        if review_count == 0:

            reputation_label = (
                "Reputasi Baru"
            )

            reputation_message = (
                "Belum ada penilaian pelanggan."
            )


        elif review_count < 3:

            reputation_label = (
                "Mulai Terbentuk"
            )

            reputation_message = (
                f"Berdasarkan {review_count} "
                "ulasan pelanggan."
            )


        elif average_rating >= 4.8:

            reputation_label = (
                "Pelayanan Istimewa"
            )

            reputation_message = (
                "Pelanggan memberikan "
                "penilaian yang sangat tinggi."
            )


        elif average_rating >= 4.5:

            reputation_label = (
                "Sangat Baik"
            )

            reputation_message = (
                "Kualitas pelayanan dinilai "
                "sangat baik oleh pelanggan."
            )


        elif average_rating >= 4.0:

            reputation_label = (
                "Pelayanan Baik"
            )

            reputation_message = (
                "Pelanggan memberikan "
                "penilaian positif."
            )


        else:

            reputation_label = (
                "Terus Tingkatkan"
            )

            reputation_message = (
                "Masukan pelanggan dapat digunakan "
                "untuk meningkatkan pelayanan."
            )


        # ====================================================
        # LATEST REVIEWS
        # ====================================================

        recent_review_rows = (
            connection.execute(
                """
                SELECT

                    r.rating,

                    r.feedback,

                    r.tags,

                    r.created_at,

                    o.order_code,

                    o.customer_name

                FROM order_reviews r

                INNER JOIN orders o
                    ON o.id = r.order_id

                WHERE o.status = ?

                ORDER BY r.id DESC

                LIMIT 5
                """,
                (
                    STATUS_COMPLETED,
                )
            )
            .fetchall()
        )
        
        # ============================================================
        # PHASE 20G.4
        # RECENT DRIVER RECEIPTS
        # ============================================================

        recent_receipts = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE status = ?

                AND payment_status = ?

                AND paid_at IS NOT NULL

                AND payment_amount IS NOT NULL

                AND payment_amount > 0

                AND payment_amount = fare

                AND payment_method IN (
                    ?, ?, ?
                )

                ORDER BY
                    COALESCE(
                        paid_at,
                        completed_at,
                        created_at
                    ) DESC

                LIMIT 5
                """,
                (
                    STATUS_COMPLETED,
                    PAYMENT_STATUS_PAID,
                    PAYMENT_METHOD_CASH,
                    PAYMENT_METHOD_QRIS,
                    PAYMENT_METHOD_BANK_TRANSFER,
                )
            )
            .fetchall()
        )


        recent_reviews = []


        for review in recent_review_rows:

            decoded_tags = (
                decode_review_tags(
                    review[
                        "tags"
                    ]
                )
            )


            tag_labels = [

                REVIEW_ALLOWED_TAGS_LABELS.get(
                    tag,
                    tag.replace(
                        "_",
                        " "
                    ).title()
                )

                for tag
                in decoded_tags
            ]


            recent_reviews.append(
                {
                    "rating":
                        int(
                            review[
                                "rating"
                            ]
                            or 0
                        ),

                    "feedback":
                        (
                            review[
                                "feedback"
                            ]
                            or ""
                        ).strip(),

                    "tags":
                        tag_labels,

                    "created_at":
                        review[
                            "created_at"
                        ],

                    "order_code":
                        review[
                            "order_code"
                        ],

                    "customer_name":
                        review[
                            "customer_name"
                        ],
                }
            )

    finally:

        connection.close()


    return render_template(
        "admin/dashboard.html",

        orders=
            orders,
            
        recent_receipts=
            recent_receipts,

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
            
        payment_control=
            get_driver_payment_control_summary(),

        latest_order_id=
            latest_order_id,

        # ====================================================
        # PHASE 19C
        # DRIVER REPUTATION
        # ====================================================

        review_count=
            review_count,

        average_rating=
            average_rating,

        rating_distribution=
            rating_distribution,

        reputation_label=
            reputation_label,

        reputation_message=
            reputation_message,

        recent_reviews=
            recent_reviews,
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
# PHASE 19F.6
# PREMIUM DRIVER REVIEW HISTORY PAGE
# ============================================================

@app.route(
    "/driver/reviews"
)
@driver_login_required
def driver_reviews():

    # ========================================================
    # PAGE
    # ========================================================

    raw_page = str(
        request.args.get(
            "page",
            "1"
        )
        or "1"
    ).strip()


    try:

        page = int(
            raw_page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1


    page = max(
        1,
        page
    )


    # ========================================================
    # RATING FILTER
    # ========================================================

    raw_rating = str(
        request.args.get(
            "rating",
            ""
        )
        or ""
    ).strip()


    rating = (
        normalize_review_rating_filter(
            raw_rating
        )
    )


    # ========================================================
    # SEARCH
    # ========================================================

    search = (
        normalize_review_search(
            request.args.get(
                "search",
                ""
            )
        )
    )


    if (
        len(
            search
        )
        >
        REVIEW_HISTORY_SEARCH_MAX_LENGTH
    ):

        search = search[
            :REVIEW_HISTORY_SEARCH_MAX_LENGTH
        ]


    # ========================================================
    # DATABASE
    # ========================================================

    connection = (
        get_db()
    )


    try:

        result = (
            get_driver_review_history_page(
                connection,
                page=page,
                rating=rating,
                search=search
            )
        )


        statistics = (
            get_driver_review_statistics(
                connection
            )
        )


    finally:

        connection.close()


    # ========================================================
    # TEMPLATE
    # ========================================================

    return render_template(
        "admin/reviews.html",

        reviews=
            result[
                "reviews"
            ],

        pagination=
            result[
                "pagination"
            ],

        filters=
            result[
                "filters"
            ],

        statistics=
            statistics,
    )
    
    # ============================================================
# PHASE 20H.5
# INCOME / PAYMENT RECONCILIATION
# ============================================================

def get_driver_payment_reconciliation(
    connection,
    period="all"
):

    # ========================================================
    # NORMALIZE PERIOD
    # ========================================================

    period = (
        normalize_payment_history_period(
            period
        )
    )


    now = datetime.now(
        APP_TZ
    )


    today = now.strftime(
        "%Y-%m-%d"
    )


    seven_days_start = (
        now
        -
        timedelta(
            days=6
        )
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )


    thirty_days_start = (
        now
        -
        timedelta(
            days=29
        )
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )


    # ========================================================
    # COMPLETED TRIP TIME
    # ========================================================

    completed_time_column = """
        COALESCE(
            completed_at,
            created_at
        )
    """


    conditions = [
        "status = ?"
    ]


    parameters = [
        STATUS_COMPLETED
    ]


    # ========================================================
    # PERIOD FILTER
    # ========================================================

    if period == "today":

        conditions.append(
            completed_time_column
            +
            " LIKE ?"
        )


        parameters.append(
            f"{today}%"
        )


    elif period == "7days":

        conditions.append(
            completed_time_column
            +
            " >= ?"
        )


        parameters.append(
            seven_days_start
        )


    elif period == "30days":

        conditions.append(
            completed_time_column
            +
            " >= ?"
        )


        parameters.append(
            thirty_days_start
        )


    where_sql = (
        " AND ".join(
            conditions
        )
    )


    # ========================================================
    # MAIN RECONCILIATION QUERY
    # ========================================================

    row = (
        connection.execute(
            f"""
            SELECT

                COUNT(*)
                    AS completed_trips,


                COALESCE(
                    SUM(
                        fare
                    ),
                    0
                )
                    AS trip_income,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status = ?
                                AND payment_amount IS NOT NULL
                                AND payment_amount > 0
                                AND paid_at IS NOT NULL
                                AND payment_method IN (
                                    ?,
                                    ?,
                                    ?
                                )

                            THEN 1

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS paid_trips,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status = ?
                                AND payment_amount IS NOT NULL
                                AND payment_amount > 0
                                AND paid_at IS NOT NULL
                                AND payment_method IN (
                                    ?,
                                    ?,
                                    ?
                                )

                            THEN payment_amount

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS paid_income,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status != ?

                                OR payment_status IS NULL

                                OR payment_amount IS NULL

                                OR payment_amount <= 0

                                OR paid_at IS NULL

                                OR payment_method NOT IN (
                                    ?,
                                    ?,
                                    ?
                                )

                            THEN 1

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS unresolved_trips,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status != ?

                                OR payment_status IS NULL

                                OR payment_amount IS NULL

                                OR payment_amount <= 0

                                OR paid_at IS NULL

                                OR payment_method NOT IN (
                                    ?,
                                    ?,
                                    ?
                                )

                            THEN fare

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS unresolved_amount,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status = ?
                                AND payment_amount IS NOT NULL
                                AND payment_amount > 0
                                AND payment_amount != fare

                            THEN 1

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS mismatch_count,


                COALESCE(
                    SUM(
                        CASE

                            WHEN
                                payment_status = ?
                                AND payment_amount IS NOT NULL
                                AND payment_amount > 0
                                AND payment_amount != fare

                            THEN ABS(
                                payment_amount
                                -
                                fare
                            )

                            ELSE 0

                        END
                    ),
                    0
                )
                    AS mismatch_amount


            FROM orders

            WHERE
                {where_sql}
            """,
            (
                # paid_trips
                PAYMENT_STATUS_PAID,
                PAYMENT_METHOD_CASH,
                PAYMENT_METHOD_QRIS,
                PAYMENT_METHOD_BANK_TRANSFER,

                # paid_income
                PAYMENT_STATUS_PAID,
                PAYMENT_METHOD_CASH,
                PAYMENT_METHOD_QRIS,
                PAYMENT_METHOD_BANK_TRANSFER,

                # unresolved_trips
                PAYMENT_STATUS_PAID,
                PAYMENT_METHOD_CASH,
                PAYMENT_METHOD_QRIS,
                PAYMENT_METHOD_BANK_TRANSFER,

                # unresolved_amount
                PAYMENT_STATUS_PAID,
                PAYMENT_METHOD_CASH,
                PAYMENT_METHOD_QRIS,
                PAYMENT_METHOD_BANK_TRANSFER,

                # mismatch_count
                PAYMENT_STATUS_PAID,

                # mismatch_amount
                PAYMENT_STATUS_PAID,

                *parameters,
            )
        )
        .fetchone()
    )


    completed_trips = int(
        row[
            "completed_trips"
        ]
        or 0
    )


    trip_income = int(
        row[
            "trip_income"
        ]
        or 0
    )


    paid_trips = int(
        row[
            "paid_trips"
        ]
        or 0
    )


    paid_income = int(
        row[
            "paid_income"
        ]
        or 0
    )


    unresolved_trips = int(
        row[
            "unresolved_trips"
        ]
        or 0
    )


    unresolved_amount = int(
        row[
            "unresolved_amount"
        ]
        or 0
    )


    mismatch_count = int(
        row[
            "mismatch_count"
        ]
        or 0
    )


    mismatch_amount = int(
        row[
            "mismatch_amount"
        ]
        or 0
    )


    # ========================================================
    # DIFFERENCE
    # ========================================================

    difference = (
        trip_income
        -
        paid_income
    )


    if difference < 0:

        difference = 0


    # ========================================================
    # PAYMENT COMPLETION RATE
    # ========================================================

    payment_rate = (

        round(
            (
                paid_trips
                /
                completed_trips
            )
            * 100
        )

        if completed_trips > 0

        else 0

    )


    # ========================================================
    # STATUS LABEL
    # ========================================================

    if completed_trips == 0:

        status = (
            "EMPTY"
        )

        status_label = (
            "Belum Ada Data"
        )

        status_message = (
            "Belum ada perjalanan selesai "
            "pada periode ini."
        )


    elif (
        unresolved_trips == 0
        and
        mismatch_count == 0
        and
        difference == 0
    ):

        status = (
            "BALANCED"
        )

        status_label = (
            "Seimbang"
        )

        status_message = (
            "Nilai perjalanan dan pembayaran "
            "yang diterima sudah sesuai."
        )


    elif mismatch_count > 0:

        status = (
            "MISMATCH"
        )

        status_label = (
            "Perlu Pemeriksaan"
        )

        status_message = (
            "Ada pembayaran dengan nominal "
            "yang berbeda dari tarif perjalanan."
        )


    else:

        status = (
            "PENDING"
        )

        status_label = (
            "Belum Sepenuhnya Dibayar"
        )

        status_message = (
            "Masih ada perjalanan selesai "
            "yang pembayarannya belum terkonfirmasi."
        )


    return {

        "period":
            period,

        "completed_trips":
            completed_trips,

        "trip_income":
            trip_income,

        "paid_trips":
            paid_trips,

        "paid_income":
            paid_income,

        "unresolved_trips":
            unresolved_trips,

        "unresolved_amount":
            unresolved_amount,

        "difference":
            difference,

        "mismatch_count":
            mismatch_count,

        "mismatch_amount":
            mismatch_amount,

        "payment_rate":
            payment_rate,

        "status":
            status,

        "status_label":
            status_label,

        "status_message":
            status_message,
    }
    
    # ============================================================
# PHASE 20H.5
# UNRESOLVED PAYMENT RECONCILIATION
# ============================================================

def get_driver_unresolved_payments(
    connection,
    period="all",
    limit=10
):

    period = (
        normalize_payment_history_period(
            period
        )
    )


    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 10


    limit = max(
        1,
        min(
            limit,
            50
        )
    )


    now = datetime.now(
        APP_TZ
    )


    today = now.strftime(
        "%Y-%m-%d"
    )


    seven_days_start = (
        now
        -
        timedelta(
            days=6
        )
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )


    thirty_days_start = (
        now
        -
        timedelta(
            days=29
        )
    ).strftime(
        "%Y-%m-%d 00:00:00"
    )


    completed_time_column = """
        COALESCE(
            completed_at,
            created_at
        )
    """


    conditions = [

        "status = ?",

        """
        (
            payment_status != ?

            OR payment_status IS NULL

            OR payment_amount IS NULL

            OR payment_amount <= 0

            OR paid_at IS NULL

            OR payment_method NOT IN (
                ?,
                ?,
                ?
            )

            OR payment_amount != fare
        )
        """
    ]


    parameters = [

        STATUS_COMPLETED,

        PAYMENT_STATUS_PAID,

        PAYMENT_METHOD_CASH,

        PAYMENT_METHOD_QRIS,

        PAYMENT_METHOD_BANK_TRANSFER,
    ]


    if period == "today":

        conditions.append(
            completed_time_column
            +
            " LIKE ?"
        )


        parameters.append(
            f"{today}%"
        )


    elif period == "7days":

        conditions.append(
            completed_time_column
            +
            " >= ?"
        )


        parameters.append(
            seven_days_start
        )


    elif period == "30days":

        conditions.append(
            completed_time_column
            +
            " >= ?"
        )


        parameters.append(
            thirty_days_start
        )


    where_sql = (
        " AND ".join(
            conditions
        )
    )


    parameters.append(
        limit
    )


    rows = (
        connection.execute(
            f"""
            SELECT

                id,

                order_code,

                customer_name,

                fare,

                status,

                completed_at,

                payment_method,

                payment_status,

                payment_amount,

                payment_customer_confirmed_at,

                payment_driver_confirmed_at,

                paid_at


            FROM orders


            WHERE
                {where_sql}


            ORDER BY

                COALESCE(
                    completed_at,
                    created_at
                )
                DESC,

                id DESC


            LIMIT ?
            """,
            tuple(
                parameters
            )
        )
        .fetchall()
    )


    results = []


    for row in rows:

        fare = int(
            row[
                "fare"
            ]
            or 0
        )


        payment_amount = int(
            row[
                "payment_amount"
            ]
            or 0
        )


        # ====================================================
        # REASON
        # ====================================================

        if (
            row[
                "payment_status"
            ]
            != PAYMENT_STATUS_PAID
        ):

            reason = (
                "PAYMENT_NOT_PAID"
            )

            reason_label = (
                "Pembayaran belum dikonfirmasi"
            )


        elif not row[
            "paid_at"
        ]:

            reason = (
                "PAID_AT_MISSING"
            )

            reason_label = (
                "Waktu pembayaran belum tercatat"
            )


        elif (
            row[
                "payment_method"
            ]
            not in PAYMENT_ALLOWED_METHODS
        ):

            reason = (
                "INVALID_METHOD"
            )

            reason_label = (
                "Metode pembayaran tidak valid"
            )


        elif payment_amount <= 0:

            reason = (
                "INVALID_AMOUNT"
            )

            reason_label = (
                "Nominal pembayaran tidak valid"
            )


        elif (
            payment_amount
            != fare
        ):

            reason = (
                "AMOUNT_MISMATCH"
            )

            reason_label = (
                "Nominal pembayaran berbeda"
            )


        else:

            reason = (
                "UNKNOWN"
            )

            reason_label = (
                "Perlu diperiksa"
            )


        results.append(
            {
                "id":
                    int(
                        row[
                            "id"
                        ]
                    ),

                "order_code":
                    row[
                        "order_code"
                    ],

                "customer_name":
                    row[
                        "customer_name"
                    ],

                "fare":
                    fare,

                "payment_method":
                    row[
                        "payment_method"
                    ],

                "payment_status":
                    (
                        row[
                            "payment_status"
                        ]
                        or
                        PAYMENT_STATUS_UNPAID
                    ),

                "payment_amount":
                    payment_amount,

                "completed_at":
                    row[
                        "completed_at"
                    ],

                "customer_confirmed_at":
                    row[
                        "payment_customer_confirmed_at"
                    ],

                "driver_confirmed_at":
                    row[
                        "payment_driver_confirmed_at"
                    ],

                "paid_at":
                    row[
                        "paid_at"
                    ],

                "reason":
                    reason,

                "reason_label":
                    reason_label,

                "difference":
                    abs(
                        fare
                        -
                        payment_amount
                    ),
            }
        )


    return results
    
# ============================================================
# PHASE 20H.1
# DRIVER CANONICAL PAYMENT HISTORY API
# ============================================================

@app.route(
    "/api/driver/payments/history",
    methods=["GET"]
)
@driver_api_required
def driver_payment_history_api():

    raw_page = str(
        request.args.get(
            "page",
            "1"
        )
        or "1"
    ).strip()


    try:

        page = int(
            raw_page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1


    page = max(
        1,
        page
    )


    period = (
        normalize_payment_history_period(
            request.args.get(
                "period",
                "all"
            )
        )
    )


    method_filter = (
        normalize_payment_history_method(
            request.args.get(
                "method",
                "ALL"
            )
        )
    )


    search_query = (
        normalize_payment_history_search(
            request.args.get(
                "q",
                ""
            )
        )
    )


    connection = None


    try:

        connection = (
            get_db()
        )


        result = (
            get_driver_payment_history_page(
                connection,
                page=page,
                page_size=
                    PAYMENT_HISTORY_PAGE_SIZE,
                period=period,
                payment_method=
                    method_filter,
                search=
                    search_query
            )
        )
        
        reconciliation = (
            get_driver_payment_reconciliation(
                connection,
                period=period
            )
        )


        return jsonify(
            {
                "success":
                    True,

                "canonical":
                    True,

                "filters":
                    result[
                        "filters"
                    ],

                "summary":
                    result[
                        "summary"
                    ],

                "pagination":
                    result[
                        "pagination"
                    ],

                "payments":
                    result[
                        "payments"
                    ],
                "reconciliation":
                    reconciliation,
                
            }
        )


    except Exception as error:

        app.logger.exception(
            "[PAYMENT HISTORY API ERROR]"
        )


        response_data = {
            "success":
                False,

            "message":
                (
                    "Riwayat pembayaran "
                    "belum dapat dimuat."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
        ), 500


    finally:

        if connection is not None:

            connection.close()

# ============================================================
# PHASE 20H.7 FIX
# DRIVER PAYMENT HISTORY PAGE
# SAFE HISTORY + RECONCILIATION + STATISTICS
# ============================================================

@app.route(
    "/driver/payments/history",
    methods=["GET"]
)
@driver_login_required
def driver_payment_history_page():

    # ========================================================
    # PAGE
    # ========================================================

    raw_page = str(
        request.args.get(
            "page",
            "1"
        )
        or "1"
    ).strip()


    try:

        page = int(
            raw_page
        )

    except (
        TypeError,
        ValueError
    ):

        page = 1


    page = max(
        1,
        page
    )


    # ========================================================
    # FILTERS
    # ========================================================

    period = (
        normalize_payment_history_period(
            request.args.get(
                "period",
                "all"
            )
        )
    )


    method_filter = (
        normalize_payment_history_method(
            request.args.get(
                "method",
                "ALL"
            )
        )
    )


    search_query = (
        normalize_payment_history_search(
            request.args.get(
                "q",
                ""
            )
        )
    )


    # ========================================================
    # SAFE DEFAULTS
    # ========================================================

    result = {
        "payments":
            [],

        "summary": {
            "total_records":
                0,

            "paid_count":
                0,

            "unpaid_count":
                0,

            "pending_count":
                0,

            "paid_amount":
                0,
        },

        "pagination": {
            "page":
                page,

            "per_page":
                PAYMENT_HISTORY_PAGE_SIZE,

            "total_pages":
                0,

            "total_records":
                0,

            "has_previous":
                False,

            "has_next":
                False,

            "result_start":
                0,

            "result_end":
                0,

            "page_numbers":
                [],
        },

        "filters": {
            "period":
                period,

            "method":
                method_filter,

            "status":
                PAYMENT_STATUS_PAID,

            "q":
                search_query,
        },
    }


    statistics = {
        "period":
            period,

        "total_received":
            0,

        "total_transactions":
            0,

        "average_transaction":
            0,

        "cash": {
            "amount":
                0,

            "transactions":
                0,
        },

        "qris": {
            "amount":
                0,

            "transactions":
                0,
        },

        "transfer": {
            "amount":
                0,

            "transactions":
                0,
        },

        "unclassified_amount":
            0,
    }


    reconciliation = {
        "period":
            period,

        "completed_trips":
            0,

        "trip_income":
            0,

        "paid_trips":
            0,

        "paid_income":
            0,

        "unresolved_trips":
            0,

        "unresolved_amount":
            0,

        "difference":
            0,

        "mismatch_count":
            0,

        "mismatch_amount":
            0,

        "payment_rate":
            0,

        "status":
            "EMPTY",

        "status_label":
            "Belum Ada Data",

        "status_message":
            "Belum ada data rekonsiliasi.",
    }


    unresolved_payments = []


    connection = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # PHASE 20H.1 - 20H.4
        # CANONICAL PAYMENT HISTORY
        # ====================================================

        result = (
            get_driver_payment_history_page(
                connection,

                page=
                    page,

                page_size=
                    PAYMENT_HISTORY_PAGE_SIZE,

                period=
                    period,

                payment_method=
                    method_filter,

                search=
                    search_query
            )
        )


        if not isinstance(
            result,
            dict
        ):

            raise RuntimeError(
                (
                    "get_driver_payment_history_page() "
                    "tidak mengembalikan dictionary."
                )
            )


        # ====================================================
        # PHASE 20H.5
        # PAYMENT RECONCILIATION
        # ====================================================

        try:

            reconciliation = (
                get_driver_payment_reconciliation(
                    connection,
                    period=period
                )
            )


            unresolved_payments = (
                get_driver_unresolved_payments(
                    connection,
                    period=period,
                    limit=10
                )
            )


        except Exception:

            app.logger.exception(
                "[PAYMENT RECONCILIATION ERROR]"
            )


        # ====================================================
        # PHASE 20H.6
        # PAYMENT STATISTICS
        # ====================================================

        try:

            statistics = (
                get_driver_payment_statistics(
                    connection,
                    period=period
                )
            )


        except Exception:

            app.logger.exception(
                "[PAYMENT STATISTICS ERROR]"
            )


    except Exception:

        app.logger.exception(
            "[PAYMENT HISTORY PAGE ERROR]"
        )

        raise


    finally:

        if connection is not None:

            connection.close()


    # ========================================================
    # TEMPLATE
    # ========================================================

    return render_template(
        "admin/payment_history.html",

        payments=
            result.get(
                "payments",
                []
            ),

        summary=
            result.get(
                "summary",
                {}
            ),

        pagination=
            result.get(
                "pagination",
                {}
            ),

        filters=
            result.get(
                "filters",
                {}
            ),

        reconciliation=
            reconciliation,

        unresolved_payments=
            unresolved_payments,

        statistics=
            statistics,
    )


# ============================================================
# PHASE 20G.4
# DRIVER DIGITAL RECEIPT VIEW
# ============================================================

@app.route(
    "/driver/orders/<int:order_id>/receipt",
    methods=["GET"]
)
@driver_login_required
def driver_order_receipt(
    order_id
):

    connection = None


    try:

        connection = get_db()


        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE id = ?

                LIMIT 1
                """,
                (
                    order_id,
                )
            )
            .fetchone()
        )


        if not order:

            abort(
                404
            )


        # ====================================================
        # RECEIPT ELIGIBILITY
        # ====================================================

        eligibility = (
            get_receipt_eligibility(
                order
            )
        )


        if not eligibility[
            "eligible"
        ]:

            return render_template(
                "admin/receipt.html",

                receipt=None,

                order=order,

                receipt_available=False,

                receipt_reason=eligibility[
                    "reason"
                ]
            )


        # ====================================================
        # BUILD RECEIPT
        # ====================================================

        receipt = (
            build_payment_receipt(
                order
            )
        )


        return render_template(
            "admin/receipt.html",

            receipt=receipt,

            order=order,

            receipt_available=True,

            receipt_reason=None
        )


    except Exception:

        app.logger.exception(
            "[DRIVER RECEIPT ERROR]"
        )


        abort(
            500
        )


    finally:

        if connection is not None:

            connection.close()
    
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
        
    # ========================================================
    # PHASE 20I.3C
    # DRIVER REFUND REQUEST STATE
    # ========================================================

    refund_request = (
        payment_refund_request_payload(
            order
        )
    )


    return render_template(
        "admin/order_detail.html",

        order=
            order,

        pickup_map_url=
            pickup_map_url,

        destination_map_url=
            destination_map_url,
            
        refund_request=
            refund_request,
    )    
    
# ============================================================
# PHASE 20B
# CONFIRM DRIVER CASH PAYMENT
# ============================================================

@app.route(
    "/driver/orders/<string:order_code>/payment/cash/confirm",
    methods=["POST"]
)
@driver_csrf_required
@driver_login_required
def driver_confirm_cash_payment(
    order_code
):

    order_code = (
        str(
            order_code
            or ""
        )
        .strip()
        .upper()
    )


    # ========================================================
    # INVALID ORDER CODE
    # ========================================================

    if not order_code:

        flash(
            "Kode pesanan tidak valid.",
            "error"
        )


        return redirect(
            url_for(
                "driver_dashboard"
            )
        )


    connection = None

    order = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # FIND ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT
                    *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not order:

            flash(
                "Pesanan tidak ditemukan.",
                "error"
            )


            return redirect(
                url_for(
                    "driver_dashboard"
                )
            )


        # ====================================================
        # CONFIRM CASH PAYMENT
        # ====================================================

        result = (
            confirm_cash_payment(
                connection,
                order
            )
        )


        connection.commit()


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        if result[
            "already_paid"
        ]:

            flash(
                (
                    "Pembayaran tunai pesanan ini "
                    "sudah dikonfirmasi sebelumnya."
                ),
                "info"
            )


        else:

            flash(
                (
                    "Pembayaran tunai berhasil "
                    "dikonfirmasi."
                ),
                "success"
            )


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except Exception:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[CASH PAYMENT CONFIRM ERROR]"
        )


        flash(
            (
                "Pembayaran tunai belum dapat "
                "dikonfirmasi."
            ),
            "error"
        )


    finally:

        if connection is not None:

            connection.close()


    # ========================================================
    # RETURN TO ORDER DETAIL
    # ========================================================

    if order:

        return redirect(
            url_for(
                "driver_order_detail",
                order_id=order[
                    "id"
                ]
            )
        )


    return redirect(
        url_for(
            "driver_dashboard"
        )
    )

# ============================================================
# PHASE 20D
# DRIVER CONFIRM QRIS / BANK PAYMENT
# ============================================================

@app.route(
    "/driver/orders/<string:order_code>/payment/manual/confirm",
    methods=["POST"]
)
@driver_login_required
@driver_csrf_required
def driver_confirm_manual_payment(
    order_code
):

    order_code = (
        str(
            order_code
            or ""
        )
        .strip()
        .upper()
    )


    connection = None

    order = None


    try:

        connection = (
            get_db()
        )


        order = (
            connection.execute(
                """
                SELECT
                    *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not order:

            flash(
                "Pesanan tidak ditemukan.",
                "error"
            )


            return redirect(
                url_for(
                    "driver_dashboard"
                )
            )


        result = (
            confirm_manual_payment(
                connection,
                order
            )
        )
        



        connection.commit()


        if result[
            "already_paid"
        ]:

            flash(
                (
                    "Pembayaran sudah "
                    "dikonfirmasi sebelumnya."
                ),
                "info"
            )


        else:

            flash(
                (
                    "Pembayaran berhasil "
                    "dikonfirmasi."
                ),
                "success"
            )


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except Exception:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[MANUAL PAYMENT CONFIRM ERROR]"
        )


        flash(
            (
                "Pembayaran belum dapat "
                "dikonfirmasi."
            ),
            "error"
        )


    finally:

        if connection is not None:

            connection.close()


    if order:

        return redirect(
            url_for(
                "driver_order_detail",
                order_id=order[
                    "id"
                ]
            )
        )


    return redirect(
        url_for(
            "driver_dashboard"
        )
    )
    
    # ============================================================
# PHASE 20I.3
# DRIVER REFUND PAYMENT
# ============================================================

@app.route(
    "/driver/orders/<string:order_code>/payment/refund",
    methods=["POST"]
)
@driver_login_required
@driver_csrf_required
def driver_refund_payment(
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    if not order_code:

        flash(
            "Kode pesanan tidak valid.",
            "error"
        )


        return redirect(
            url_for(
                "driver_dashboard"
            )
        )


    # ========================================================
    # INPUT
    # ========================================================

    reason = (
        request.form.get(
            "refund_reason",
            ""
        )
    )


    refund_reference = (
        request.form.get(
            "refund_reference",
            ""
        )
    )


    connection = None

    order = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not order:

            flash(
                "Pesanan tidak ditemukan.",
                "error"
            )


            return redirect(
                url_for(
                    "driver_dashboard"
                )
            )


        # ====================================================
        # PHASE 20I.3B
        # MANUAL REFUND MUST NOT BYPASS CUSTOMER REQUEST
        # ====================================================

        refund_request_status = (
            normalize_payment_refund_request_status(
                order.get(
                    "payment_refund_request_status"
                )
            )
        )


        if (
            refund_request_status
            != PAYMENT_REFUND_REQUEST_NONE
        ):

            raise ValueError(
                (
                    "Pesanan ini memiliki proses refund "
                    "customer. Gunakan proses review "
                    "permintaan refund."
                )
            )


        # ====================================================
        # REFUND
        # ====================================================

        result = (
            refund_paid_payment(
                connection,
                order,
                reason=reason,
                refund_reference=
                    refund_reference
            )
        )


        # ====================================================
        # PAYMENT + AUDIT COMMIT TOGETHER
        # ====================================================

        connection.commit()


        if result[
            "already_refunded"
        ]:

            flash(
                (
                    "Pembayaran pesanan ini "
                    "sudah dikembalikan sebelumnya."
                ),
                "info"
            )


        else:

            flash(
                (
                    "Pembayaran berhasil "
                    "ditandai sebagai dikembalikan."
                ),
                "success"
            )


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except Exception:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[PAYMENT REFUND ERROR]"
        )


        flash(
            (
                "Pengembalian pembayaran "
                "belum dapat diproses."
            ),
            "error"
        )


    finally:

        if connection is not None:

            connection.close()


    # ========================================================
    # BACK TO DETAIL
    # ========================================================

    if order:

        return redirect(
            url_for(
                "driver_order_detail",
                order_id=
                    order[
                        "id"
                    ]
            )
        )


    return redirect(
        url_for(
            "driver_dashboard"
        )
    )

# ============================================================
# PHASE 20I.3D
# DRIVER CONFIRM CUSTOMER REFUND
# ============================================================

@app.route(
    "/driver/orders/<string:order_code>/refund-request/confirm",
    methods=["POST"]
)
@driver_login_required
@driver_csrf_required
def driver_confirm_customer_refund(
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    if not order_code:

        flash(
            "Kode pesanan tidak valid.",
            "error"
        )


        return redirect(
            url_for(
                "driver_refund_requests"
            )
        )


    # ========================================================
    # OPTIONAL REFERENCE
    # ========================================================

    refund_reference = (
        request.form.get(
            "refund_reference",
            ""
        )
    )


    connection = None

    order = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # LOAD ORDER
        # ====================================================

        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not order:

            flash(
                "Pesanan tidak ditemukan.",
                "error"
            )


            return redirect(
                url_for(
                    "driver_refund_requests"
                )
            )


        # ====================================================
        # CONFIRM
        # ====================================================

        result = (
            confirm_customer_refund_request(
                connection,
                order,

                refund_reference=
                    refund_reference
            )
        )


        # ====================================================
        # PAYMENT REFUND + REQUEST APPROVAL + AUDIT
        # COMMIT TOGETHER
        # ====================================================

        connection.commit()


        if result[
            "already_confirmed"
        ]:

            flash(
                (
                    "Pengembalian dana pesanan ini "
                    "sudah dikonfirmasi sebelumnya."
                ),
                "info"
            )


        else:

            refund_amount = (
                result[
                    "refund"
                ][
                    "amount"
                ]
            )


            flash(
                (
                    "Dana sebesar "
                    f"Rp{refund_amount:,.0f}"
                    .replace(
                        ",",
                        "."
                    )
                    +
                    " berhasil ditandai "
                    "sebagai dikembalikan."
                ),
                "success"
            )


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except RuntimeError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except Exception:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[DRIVER CUSTOMER REFUND CONFIRM ERROR]"
        )


        flash(
            (
                "Pengembalian dana belum "
                "dapat dikonfirmasi."
            ),
            "error"
        )


    finally:

        if connection is not None:

            connection.close()


    # ========================================================
    # RETURN TO ORDER DETAIL
    # ========================================================

    if order:

        return redirect(
            url_for(
                "driver_order_detail",

                order_id=
                    order[
                        "id"
                    ]
            )
        )


    return redirect(
        url_for(
            "driver_refund_requests"
        )
    )

# ============================================================
# PHASE 20I.3E
# DRIVER REJECT CUSTOMER REFUND
# ============================================================

@app.route(
    "/driver/orders/<string:order_code>/refund-request/reject",
    methods=["POST"]
)
@driver_login_required
@driver_csrf_required
def driver_reject_customer_refund(
    order_code
):

    order_code = str(
        order_code
        or ""
    ).strip().upper()


    if not order_code:

        flash(
            "Kode pesanan tidak valid.",
            "error"
        )

        return redirect(
            url_for(
                "driver_refund_requests"
            )
        )


    rejection_reason = (
        request.form.get(
            "rejection_reason",
            ""
        )
    )


    connection = None
    order_id = None


    try:

        connection = (
            get_db()
        )


        order = (
            connection.execute(
                """
                SELECT *

                FROM orders

                WHERE order_code = ?

                LIMIT 1
                """,
                (
                    order_code,
                )
            )
            .fetchone()
        )


        if not order:

            flash(
                "Pesanan tidak ditemukan.",
                "error"
            )

            return redirect(
                url_for(
                    "driver_refund_requests"
                )
            )


        order_id = int(
            order[
                "id"
            ]
        )


        result = (
            reject_customer_refund_request(
                connection,
                order,
                rejection_reason=rejection_reason
            )
        )


        # UPDATE + AUDIT COMMIT TOGETHER
        connection.commit()


        if result[
            "already_rejected"
        ]:

            flash(
                (
                    "Permintaan pengembalian dana "
                    "sudah ditolak sebelumnya."
                ),
                "info"
            )

        else:

            flash(
                (
                    "Permintaan pengembalian dana "
                    "berhasil ditolak."
                ),
                "success"
            )


    except ValueError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except RuntimeError as error:

        if connection is not None:

            connection.rollback()


        flash(
            str(
                error
            ),
            "error"
        )


    except Exception:

        if connection is not None:

            connection.rollback()


        app.logger.exception(
            "[DRIVER CUSTOMER REFUND REJECT ERROR]"
        )


        flash(
            (
                "Permintaan refund belum "
                "dapat ditolak."
            ),
            "error"
        )


    finally:

        if connection is not None:

            connection.close()


    if order_id is not None:

        return redirect(
            url_for(
                "driver_order_detail",
                order_id=order_id
            )
        )


    return redirect(
        url_for(
            "driver_refund_requests"
        )
    )


# ============================================================
# PHASE 20E
# DRIVER PAYMENT CONTROL
# ============================================================

@app.route(
    "/driver/payments",
    methods=["GET"]
)
@driver_login_required
def driver_payments():

    payment_filter = (
        str(
            request.args.get(
                "status",
                "all"
            )
            or "all"
        )
        .strip()
        .lower()
    )


    payment_method = (
        str(
            request.args.get(
                "method",
                "ALL"
            )
            or "ALL"
        )
        .strip()
        .upper()
    )


    allowed_filters = {

        "all",

        "needs_confirmation",

        "waiting",

        "paid",
    }


    if payment_filter not in allowed_filters:

        payment_filter = "all"


    allowed_methods = {

        "ALL",

        PAYMENT_METHOD_CASH,

        PAYMENT_METHOD_QRIS,

        PAYMENT_METHOD_BANK_TRANSFER,
    }


    if payment_method not in allowed_methods:

        payment_method = "ALL"


    payment_control = (
        get_driver_payment_control_summary()
    )


    payment_orders = (
        get_driver_payment_orders(
            payment_filter=
                payment_filter,

            payment_method=
                payment_method
        )
    )


    return render_template(
        "admin/payments.html",

        payment_orders=
            payment_orders,

        payment_control=
            payment_control,

        payment_filter=
            payment_filter,

        payment_method_filter=
            payment_method,
    )
    
    # ============================================================
# PHASE 20I.3C
# DRIVER REFUND REQUEST REVIEW PAGE
# ============================================================

@app.route(
    "/driver/refunds",
    methods=["GET"]
)
@driver_login_required
def driver_refund_requests():

    connection = None


    try:

        connection = (
            get_db()
        )


        refund_requests = (
            get_driver_pending_refund_requests(
                connection,
                limit=50
            )
        )


        return render_template(
            "admin/refund_requests.html",

            refund_requests=
                refund_requests,

            total_refund_requests=
                len(
                    refund_requests
                ),
        )


    except Exception:

        app.logger.exception(
            "[DRIVER REFUND REQUEST REVIEW ERROR]"
        )


        flash(
            (
                "Permintaan pengembalian dana "
                "belum dapat dimuat."
            ),
            "error"
        )


        return redirect(
            url_for(
                "driver_dashboard"
            )
        )


    finally:

        if connection is not None:

            connection.close()

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

    # ========================================================
    # AFTER ID
    # ========================================================

    raw_after_id = str(
        request.args.get(
            "after_id",
            "0"
        )
        or "0"
    ).strip()


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


    connection = None


    try:

        connection = (
            get_db()
        )


        # ====================================================
        # LATEST ORDER ID
        # ====================================================

        latest_row = (
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
            .fetchone()
        )


        latest_order_id = int(
            latest_row[
                "latest_order_id"
            ]
            or 0
        )


        # ====================================================
        # NEW WAITING ORDERS
        # ====================================================

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

        # ====================================================
        # RESPONSE
        # ====================================================

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
                            int(
                                order[
                                    "id"
                                ]
                            ),

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
                            int(
                                order[
                                    "fare"
                                ]
                                or 0
                            ),

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


    except Exception as error:

        app.logger.exception(
            "[DRIVER NEW ORDERS ERROR]"
        )


        response_data = {

            "success":
                False,

            "message":
                (
                    "Notifikasi pesanan baru "
                    "belum dapat dimuat."
                ),
        }


        if APP_ENV == "development":

            response_data[
                "debug"
            ] = (
                f"{type(error).__name__}: "
                f"{str(error)}"
            )


        return jsonify(
            response_data
        ), 500


    finally:

        if connection is not None:

            connection.close()

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
        
        response.headers[
            "Expires"
        ] = "0"


        response.headers[
            "Vary"
        ] = "Cookie"
        
            # ========================================================
    # CUSTOMER LIVE ORDER STATUS
    # Jangan cache progress perjalanan.
    # ========================================================

    if (
        request.path.startswith(
            "/api/orders/"
        )
        and
        request.path.endswith(
            "/status"
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


        response.headers[
            "Expires"
        ] = "0"


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