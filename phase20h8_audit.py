from pathlib import Path
from collections import defaultdict
import ast
import os

from dotenv import load_dotenv
import psycopg


# ============================================================
# PHASE 20H.8
# SECURITY & FINAL AUDIT
#
# READ ONLY
# Tidak mengubah database.
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent

APP_FILE = (
    BASE_DIR
    /
    "app.py"
)

ENV_FILE = (
    BASE_DIR
    /
    ".env"
)


load_dotenv(
    ENV_FILE
)


DATABASE_URL = (
    os.getenv(
        "DATABASE_URL",
        ""
    )
    .strip()
)


passed = 0
failed = 0
warnings = 0


def pass_test(
    label
):

    global passed

    passed += 1

    print(
        f"[PASS] {label}"
    )


def fail_test(
    label,
    detail=""
):

    global failed

    failed += 1

    print(
        f"[FAIL] {label}"
    )

    if detail:

        print(
            f"       {detail}"
        )


def warn_test(
    label,
    detail=""
):

    global warnings

    warnings += 1

    print(
        f"[WARN] {label}"
    )

    if detail:

        print(
            f"       {detail}"
        )


# ============================================================
# APP.PY
# ============================================================

if not APP_FILE.exists():

    raise SystemExit(
        "app.py tidak ditemukan."
    )


source = (
    APP_FILE.read_text(
        encoding="utf-8"
    )
)


# ============================================================
# SYNTAX
# ============================================================

try:

    tree = ast.parse(
        source
    )

    pass_test(
        "Syntax app.py valid"
    )


except SyntaxError as error:

    fail_test(
        "Syntax app.py valid",
        str(
            error
        )
    )

    raise SystemExit(
        1
    )


# ============================================================
# ROUTES
# ============================================================

routes = []


for node in ast.walk(
    tree
):

    if not isinstance(
        node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
        )
    ):

        continue


    for decorator in node.decorator_list:

        if not isinstance(
            decorator,
            ast.Call
        ):

            continue


        if not isinstance(
            decorator.func,
            ast.Attribute
        ):

            continue


        if decorator.func.attr != "route":

            continue


        if not decorator.args:

            continue


        route_node = (
            decorator.args[
                0
            ]
        )


        if not isinstance(
            route_node,
            ast.Constant
        ):

            continue


        route_path = (
            route_node.value
        )


        methods = (
            "GET",
        )


        for keyword in decorator.keywords:

            if keyword.arg == "methods":

                try:

                    methods = tuple(
                        ast.literal_eval(
                            keyword.value
                        )
                    )

                except Exception:

                    pass


        routes.append(
            (
                route_path,
                tuple(
                    sorted(
                        methods
                    )
                ),
                node.name,
            )
        )


route_groups = (
    defaultdict(
        list
    )
)


for route in routes:

    route_groups[
        (
            route[
                0
            ],
            route[
                1
            ]
        )
    ].append(
        route[
            2
        ]
    )


duplicates = {

    key:
        names

    for key, names
    in route_groups.items()

    if len(
        names
    )
    > 1

}


if duplicates:

    fail_test(
        "Tidak ada duplicate Flask route",
        repr(
            duplicates
        )
    )


else:

    pass_test(
        "Tidak ada duplicate Flask route"
    )


# ============================================================
# CRITICAL DECORATORS
# ============================================================

function_decorators = {}


for node in tree.body:

    if not isinstance(
        node,
        ast.FunctionDef
    ):

        continue


    names = []


    for decorator in node.decorator_list:

        target = (
            decorator.func
            if isinstance(
                decorator,
                ast.Call
            )
            else decorator
        )


        if isinstance(
            target,
            ast.Name
        ):

            names.append(
                target.id
            )


        elif isinstance(
            target,
            ast.Attribute
        ):

            names.append(
                target.attr
            )


    function_decorators[
        node.name
    ] = set(
        names
    )


critical_functions = {

    "driver_payment_history_page": {
        "driver_login_required",
    },

    "driver_payment_history_api": {
        "driver_api_required",
    },

    "driver_order_receipt": {
        "driver_login_required",
    },

    "driver_confirm_cash_payment": {
        "driver_login_required",
        "driver_csrf_required",
    },

    "driver_confirm_manual_payment": {
        "driver_login_required",
        "driver_csrf_required",
    },

}


for function_name, required in (
    critical_functions.items()
):

    actual = (
        function_decorators.get(
            function_name,
            set()
        )
    )


    missing = (
        required
        -
        actual
    )


    if missing:

        fail_test(
            (
                f"Security decorator "
                f"{function_name}"
            ),
            (
                "Missing: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )
        )


    else:

        pass_test(
            (
                f"Security decorator "
                f"{function_name}"
            )
        )


# ============================================================
# DATABASE AUDIT
# ============================================================

if not DATABASE_URL:

    warn_test(
        "Database audit",
        "DATABASE_URL belum tersedia."
    )


else:

    try:

        with psycopg.connect(
            DATABASE_URL,
            connect_timeout=15
        ) as connection:

            with connection.cursor() as cursor:

                # ------------------------------------------------
                # INVALID PAID TRANSACTIONS
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM orders

                    WHERE
                        status = 'SELESAI'
                        AND payment_status = 'DIBAYAR'
                        AND (
                            payment_amount IS NULL
                            OR payment_amount <= 0
                            OR paid_at IS NULL
                            OR payment_method NOT IN (
                                'TUNAI',
                                'QRIS',
                                'TRANSFER_BANK'
                            )
                        )
                    """
                )


                invalid_paid = int(
                    cursor.fetchone()[0]
                    or 0
                )


                if invalid_paid == 0:

                    pass_test(
                        "Semua transaksi DIBAYAR valid"
                    )

                else:

                    fail_test(
                        "Semua transaksi DIBAYAR valid",
                        f"{invalid_paid} transaksi bermasalah"
                    )


                # ------------------------------------------------
                # AMOUNT MISMATCH
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM orders

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
                        AND payment_amount != fare
                    """
                )


                mismatch = int(
                    cursor.fetchone()[0]
                    or 0
                )


                if mismatch == 0:

                    pass_test(
                        "Payment amount cocok dengan fare"
                    )

                else:

                    fail_test(
                        "Payment amount cocok dengan fare",
                        f"{mismatch} transaksi mismatch"
                    )


                # ------------------------------------------------
                # DRIVER CONFIRM TIMESTAMP
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM orders

                    WHERE
                        payment_status = 'DIBAYAR'
                        AND paid_at IS NOT NULL
                        AND payment_driver_confirmed_at IS NULL
                    """
                )


                missing_confirmation = int(
                    cursor.fetchone()[0]
                    or 0
                )


                if missing_confirmation == 0:

                    pass_test(
                        "Driver confirmation timestamp lengkap"
                    )

                else:

                    fail_test(
                        "Driver confirmation timestamp lengkap",
                        (
                            f"{missing_confirmation} "
                            "transaksi belum tercatat"
                        )
                    )


                # ------------------------------------------------
                # DUPLICATE ORDER CODE
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM (
                        SELECT order_code

                        FROM orders

                        GROUP BY order_code

                        HAVING COUNT(*) > 1
                    ) duplicates
                    """
                )


                duplicate_orders = int(
                    cursor.fetchone()[0]
                    or 0
                )


                if duplicate_orders == 0:

                    pass_test(
                        "Tidak ada duplicate order_code"
                    )

                else:

                    fail_test(
                        "Tidak ada duplicate order_code",
                        f"{duplicate_orders} duplicate"
                    )


                # ------------------------------------------------
                # RAW RECEIPT TOKEN COLUMN
                # ------------------------------------------------

                cursor.execute(
                    """
                    SELECT COUNT(*)

                    FROM information_schema.columns

                    WHERE
                        table_name = 'orders'
                        AND column_name = 'receipt_token'
                    """
                )


                raw_receipt_column = int(
                    cursor.fetchone()[0]
                    or 0
                )


                if raw_receipt_column == 0:

                    pass_test(
                        "Database tidak menyimpan raw receipt token"
                    )

                else:

                    fail_test(
                        "Database tidak menyimpan raw receipt token"
                    )


    except Exception as error:

        fail_test(
            "Database audit dapat dijalankan",
            (
                f"{type(error).__name__}: "
                f"{error}"
            )
        )


# ============================================================
# RESULT
# ============================================================

print()
print(
    "========================================"
)

print(
    "PHASE 20H.8 FINAL AUDIT"
)

print(
    "========================================"
)

print(
    f"PASS : {passed}"
)

print(
    f"WARN : {warnings}"
)

print(
    f"FAIL : {failed}"
)

print(
    "========================================"
)


if failed:

    raise SystemExit(
        1
    )


print(
    "STATUS: LULUS"
)