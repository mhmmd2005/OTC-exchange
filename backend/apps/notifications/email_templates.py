"""Reusable HTML notification email template for Rosha."""

import json
from datetime import date, datetime
from html import escape
from urllib.parse import urljoin, urlparse

CATEGORY_LABELS = {
    "security": "امنیت حساب",
    "deposit": "واریز",
    "withdrawal": "برداشت",
    "wallet": "کیف پول",
    "order": "پرداخت و سفارش",
    "transaction": "تراکنش",
    "kyc": "احراز هویت",
    "identity_verification": "احراز هویت",
    "verification": "احراز هویت",
    "support": "پشتیبانی",
}

FONT_STACK = (
    "'Vazirmatn', -apple-system, BlinkMacSystemFont, Tahoma, sans-serif"
)

STATUS_STYLES = {
    "success": {
        "background": "#f0fdf4",
        "color": "#166534",
        "border": "#bbf7d0",
        "dot": "#16a34a",
        "label": "عملیات با موفقیت انجام شد",
    },
    "warning": {
        "background": "#fffbeb",
        "color": "#92400e",
        "border": "#fde68a",
        "dot": "#d97706",
        "label": "در انتظار بررسی",
    },
    "error": {
        "background": "#fef2f2",
        "color": "#991b1b",
        "border": "#fecaca",
        "dot": "#dc2626",
        "label": "عملیات ناموفق بود",
    },
    "info": {
        "background": "#eff6ff",
        "color": "#1d4ed8",
        "border": "#bfdbfe",
        "dot": "#2563eb",
        "label": "اعلان سیستمی",
    },
}

DETAIL_DEFINITIONS = (
    (
        "tracking_code",
        "کد پیگیری",
        (
            "tracking_code",
            "reference_code",
            "reference",
            "transaction_id",
            "txid",
            "request_id",
            "order_id",
            "ticket_id",
            "code",
        ),
    ),
    (
        "created_at",
        "زمان ثبت",
        (
            "created_at",
            "occurred_at",
            "transaction_date",
            "requested_at",
            "processed_at",
            "timestamp",
        ),
    ),
    (
        "amount",
        "مبلغ",
        ("amount", "total_amount", "amount_usd", "value"),
    ),
    (
        "currency",
        "ارز",
        ("currency", "currency_code", "asset", "symbol"),
    ),
    (
        "network",
        "شبکه",
        ("network", "chain", "blockchain"),
    ),
    (
        "payment_method",
        "روش پرداخت",
        ("payment_method", "method"),
    ),
    (
        "status",
        "وضعیت نهایی",
        (
            "status_label",
            "transaction_status",
            "verification_status",
            "payment_status",
            "status",
        ),
    ),
)


def _safe_action_url(raw_url, frontend_url):
    """Accept valid HTTP(S) URLs and relative frontend paths."""

    raw_url = str(raw_url or "").strip()

    if not raw_url or raw_url.startswith("#"):
        return ""

    parsed = urlparse(raw_url)

    if parsed.scheme:
        if parsed.scheme not in {"http", "https"}:
            return ""

        if not parsed.netloc:
            return ""

        return raw_url

    base = str(frontend_url or "").strip()

    if not base:
        return ""

    base_parsed = urlparse(base)

    if (
            base_parsed.scheme not in {"http", "https"}
            or not base_parsed.netloc
    ):
        return ""

    return urljoin(
        base.rstrip("/") + "/",
        raw_url.lstrip("/"),
    )


def _metadata_for(notification):
    """Read supported dictionary or JSON metadata."""

    result = {}

    for attr in (
            "metadata",
            "extra_data",
            "data",
            "details",
            "payload",
    ):
        try:
            value = getattr(notification, attr, None)
        except Exception:
            value = None

        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (ValueError, TypeError):
                value = None

        if isinstance(value, dict):
            result.update(value)

    return result


def _display_value(value):
    if value is None or value == "":
        return ""

    if isinstance(value, bool):
        return "بله" if value else "خیر"

    if isinstance(value, datetime):
        try:
            if value.tzinfo is not None:
                value = value.astimezone()
        except (ValueError, TypeError, OverflowError):
            pass

        return value.strftime("%Y-%m-%d - %H:%M")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, (dict, list, tuple, set)):
        return ""

    return str(value).strip()


def _find_value(notification, metadata, aliases):
    for key in aliases:
        if key in metadata:
            value = _display_value(metadata.get(key))

            if value:
                return value

    for key in aliases:
        try:
            value = _display_value(
                getattr(notification, key, None)
            )
        except Exception:
            value = ""

        if value:
            return value

    return ""


def _status_for(notification, metadata, category_label):
    """Choose a status badge from available status data or message text."""

    raw = _find_value(
        notification,
        metadata,
        (
            "status_label",
            "transaction_status",
            "verification_status",
            "payment_status",
            "status",
        ),
    )

    if not raw:
        try:
            display_method = getattr(
                notification,
                "get_status_display",
                None,
            )

            if callable(display_method):
                raw = _display_value(display_method())
        except Exception:
            raw = ""

    if not raw:
        text = (
                str(getattr(notification, "title", "") or "")
                + " "
                + str(getattr(notification, "message", "") or "")
        ).lower()

        error_terms = (
            "ناموفق",
            "رد شد",
            "ردشده",
            "لغو شد",
            "خطا",
            "failed",
            "failure",
            "rejected",
            "declined",
            "cancelled",
            "canceled",
            "error",
        )

        waiting_terms = (
            "در انتظار",
            "درحال بررسی",
            "در حال بررسی",
            "در حال پردازش",
            "pending",
            "processing",
            "under review",
            "waiting",
            "submitted",
        )

        success_terms = (
            "با موفقیت",
            "موفقیت آمیز",
            "تایید شد",
            "تأیید شد",
            "تایید شده",
            "تأیید شده",
            "تکمیل شد",
            "successful",
            "success",
            "completed",
            "approved",
            "confirmed",
            "verified",
            "paid",
            "resolved",
            "accepted",
        )

        if any(term in text for term in error_terms):
            return (
                STATUS_STYLES["error"]["label"],
                STATUS_STYLES["error"],
            )

        if any(term in text for term in waiting_terms):
            return (
                STATUS_STYLES["warning"]["label"],
                STATUS_STYLES["warning"],
            )

        if any(term in text for term in success_terms):
            return (
                STATUS_STYLES["success"]["label"],
                STATUS_STYLES["success"],
            )

        return (
            category_label or STATUS_STYLES["info"]["label"],
            STATUS_STYLES["info"],
        )

    normalized = (
        raw.strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )

    has_persian = any(
        "\u0600" <= char <= "\u06ff"
        for char in raw
    )

    error_terms = (
        "ناموفق",
        "تایید نشده",
        "تأیید نشده",
        "رد شد",
        "ردشده",
        "لغو",
        "خطا",
        "failed",
        "failure",
        "rejected",
        "declined",
        "cancelled",
        "canceled",
        "error",
        "blocked",
        "unverified",
    )

    waiting_terms = (
        "در انتظار",
        "درحال بررسی",
        "در حال بررسی",
        "در حال پردازش",
        "pending",
        "processing",
        "in progress",
        "under review",
        "waiting",
        "submitted",
    )

    success_terms = (
        "موفق",
        "تایید شد",
        "تأیید شد",
        "تایید شده",
        "تأیید شده",
        "تکمیل شد",
        "success",
        "completed",
        "approved",
        "confirmed",
        "verified",
        "paid",
        "resolved",
        "accepted",
    )

    if any(term in normalized for term in error_terms):
        style = STATUS_STYLES["error"]

        if not has_persian:
            raw = style["label"]

    elif any(term in normalized for term in waiting_terms):
        style = STATUS_STYLES["warning"]

        if not has_persian:
            raw = style["label"]

    elif any(term in normalized for term in success_terms):
        style = STATUS_STYLES["success"]

        if not has_persian:
            if "paid" in normalized:
                raw = "پرداخت انجام شد"
            elif "approved" in normalized or "confirmed" in normalized:
                raw = "تأیید شد"
            elif "verified" in normalized:
                raw = "احراز هویت تأیید شد"
            elif "resolved" in normalized:
                raw = "درخواست رسیدگی شد"
            elif "completed" in normalized:
                raw = "تکمیل شد"
            else:
                raw = style["label"]

    else:
        style = STATUS_STYLES["info"]

    return raw, style


def _details_rows(notification, metadata):
    """Build the table from fields actually present."""

    rows = []
    seen_values = set()

    for key, label, aliases in DETAIL_DEFINITIONS:
        value = _find_value(
            notification,
            metadata,
            aliases,
        )

        if not value or value in seen_values:
            continue

        seen_values.add(value)
        rows.append((key, label, value))

    return rows


def _render_details(rows):
    """Render the same details table design only when data exists."""

    if not rows:
        return ""

    rendered_rows = []

    for index, (_key, label, value) in enumerate(rows):
        last = index == len(rows) - 1

        if index == 0 and last:
            padding = "padding:0 0 4px;"
        elif index == 0:
            padding = "padding-bottom:12px;"
        elif last:
            padding = "padding-top:12px;"
        else:
            padding = "padding:12px 0;"

        border = (
            ""
            if last
            else "border-bottom:1px solid #edf2f7;"
        )

        rendered_rows.append(
            f"""
            <tr>
                <td style="{padding}{border}
                           font-size:13px;
                           color:#64748b;
                           width:35%;
                           line-height:1.8;
                           vertical-align:top;">
                    {escape(label)}:
                </td>
                <td style="{padding}{border}
                           font-size:13px;
                           font-weight:600;
                           color:#0f172a;
                           line-height:1.8;
                           overflow-wrap:anywhere;
                           word-break:break-word;"
                    align="left">
                    {escape(value)}
                </td>
            </tr>
            """
        )

    return f"""
    <table border="0" cellpadding="0" cellspacing="0" width="100%"
           style="background-color:#f8fafc;
                  border:1px solid #e2e8f0;
                  border-radius:8px;
                  border-collapse:separate;
                  margin-bottom:28px;">
        <tr>
            <td style="padding:20px 24px;border-radius:8px;">
                <table border="0" cellpadding="0" cellspacing="0"
                       width="100%">
                    {''.join(rendered_rows)}
                </table>
            </td>
        </tr>
    </table>
    """


def render_notification_email(
        notification,
        user,
        frontend_url,
        force_email=False,
):
    """Render the shared Rosha template with dynamic notification content."""

    category = str(
        getattr(notification, "category", "") or ""
    ).strip().lower()

    category_label = CATEGORY_LABELS.get(
        category,
        "اعلان سیستمی",
    )

    metadata = _metadata_for(notification)

    title = (
            _display_value(
                getattr(notification, "title", None)
            )
            or "اعلان سامانه"
    )

    message = _display_value(
        getattr(notification, "message", None)
    )

    full_name = getattr(user, "full_name", None)
    if callable(full_name):
        full_name = full_name()

    name = _display_value(full_name)

    if not name:
        get_full_name = getattr(user, "get_full_name", None)

        if callable(get_full_name):
            name = _display_value(get_full_name())

    if not name:
        name = (
                _display_value(getattr(user, "first_name", None))
                or _display_value(getattr(user, "username", None))
                or "کاربر گرامی"
        )

    safe_title = escape(title)
    safe_message = escape(message).replace("\n", "<br>\n")
    safe_name = escape(name)

    status_label, status_style = _status_for(
        notification,
        metadata,
        category_label,
    )

    status_html = f"""
    <table border="0" cellpadding="0" cellspacing="0"
           style="margin-bottom:24px;">
        <tr>
            <td style="padding:6px 14px;
                       border-radius:6px;
                       font-size:12px;
                       font-weight:600;
                       display:inline-block;
                       background-color:{status_style['background']};
                       color:{status_style['color']};
                       border:1px solid {status_style['border']};">
                <span style="display:inline-block;
                             width:6px;
                             height:6px;
                             background-color:{status_style['dot']};
                             border-radius:50%;
                             margin-left:6px;
                             vertical-align:middle;">&nbsp;</span>
                {escape(status_label)}
            </td>
        </tr>
    </table>
    """

    details_html = _render_details(
        _details_rows(notification, metadata)
    )

    action_url = _safe_action_url(
        getattr(notification, "action_url", ""),
        frontend_url,
    )

    action_label = (
            _display_value(
                getattr(notification, "action_label", None)
            )
            or "مشاهده جزئیات در پنل کاربری"
    )

    button_html = ""

    if action_url:
        button_html = f"""
        <table border="0" cellpadding="0" cellspacing="0"
               width="100%">
            <tr>
                <td align="right" style="padding-bottom:28px;">
                    <a href="{escape(action_url, quote=True)}"
                       target="_blank"
                       class="btn-green"
                       style="display:inline-block;
                              padding:12px 28px;
                              font-size:13px;
                              font-weight:600;
                              text-decoration:none;
                              border-radius:6px;
                              text-align:center;
                              background-color:#15803d;
                              color:#ffffff;
                              box-shadow:0 2px 4px rgba(21,128,61,0.15);
                              font-family:{FONT_STACK};">
                        {escape(action_label)}
                    </a>
                </td>
            </tr>
        </table>
        """

    settings_url = _safe_action_url(
        metadata.get("settings_url")
        or getattr(notification, "settings_url", ""),
        frontend_url,
    )

    settings_html = ""

    if settings_url:
        settings_html = f"""
        <a href="{escape(settings_url, quote=True)}"
           style="font-size:11px;
                  color:#64748b;
                  text-decoration:underline;">
            تنظیمات اعلان‌ها
        </a>
        """

    current_year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{safe_title}</title>

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700&display=swap"
          rel="stylesheet">

    <style>
        body, table, td, a {{
            font-family:{FONT_STACK} !important;
            text-size-adjust:100%;
            -webkit-text-size-adjust:100%;
        }}

        table, td {{
            mso-table-lspace:0pt;
            mso-table-rspace:0pt;
        }}

        img {{
            border:0;
            height:auto;
            line-height:100%;
            outline:none;
            text-decoration:none;
        }}

        table {{
            border-collapse:separate !important;
        }}

        body {{
            height:100% !important;
            margin:0 !important;
            padding:0 !important;
            width:100% !important;
            background-color:#f6f8fb;
        }}

        .btn-green {{
            background-color:#15803d;
            color:#ffffff;
        }}

        .btn-green:hover {{
            background-color:#166534 !important;
        }}

        @media screen and (max-width:600px) {{
            .outer-padding {{
                padding:28px 12px !important;
            }}

            .email-header {{
                padding:24px 22px 18px !important;
            }}

            .email-content {{
                padding:28px 22px !important;
            }}

            .email-footer {{
                padding:20px 22px !important;
            }}
        }}
    </style>
</head>

<body style="margin:0;padding:0;background-color:#f6f8fb;">

    <table border="0" cellpadding="0" cellspacing="0"
           width="100%" dir="rtl"
           style="table-layout:fixed;background-color:#f6f8fb;">

        <tr>
            <td align="center" class="outer-padding"
                style="padding:56px 16px;">

                <table border="0" cellpadding="0" cellspacing="0"
                       width="100%"
                       style="max-width:800px;
                              background-color:#ffffff;
                              border-radius:12px;
                              border:1px solid #cbd5e1;
                              border-collapse:separate;
                              box-shadow:0 4px 20px rgba(15,23,42,0.04);
                              overflow:hidden;">

                    <!-- Fixed header -->
                    <tr>
                        <td align="right" class="email-header"
                            style="padding:30px 40px 22px;
                                   border-bottom:1px solid #f1f5f9;
                                   border-top-left-radius:12px;
                                   border-top-right-radius:12px;">

                            <table border="0" cellpadding="0"
                                   cellspacing="0" width="100%">
                                <tr>
                                    <td align="right">
                                        <span style="font-size:14px;
                                                     font-weight:700;
                                                     color:#0f172a;
                                                     letter-spacing:-0.3px;">
                                            روشا
                                        </span>
                                    </td>

                                    <td align="left">
                                        <span style="font-size:11px;
                                                     font-weight:500;
                                                     color:#64748b;
                                                     background-color:#f8fafc;
                                                     padding:4px 10px;
                                                     border-radius:6px;
                                                     border:1px solid #e2e8f0;">
                                            اعلان سیستمی
                                        </span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Dynamic body -->
                    <tr>
                        <td class="email-content" style="padding:40px;">

                            {status_html}

                            <h1 style="margin:0 0 14px;
                                       font-size:20px;
                                       font-weight:700;
                                       color:#0f172a;
                                       line-height:1.7;
                                       letter-spacing:-0.4px;">
                                {safe_title}
                            </h1>

                            <p style="margin:0 0 28px;
                                      font-size:14px;
                                      color:#475569;
                                      line-height:1.9;
                                      font-weight:400;">
                                کاربر گرامی
                                <strong style="color:#0f172a;">
                                    {safe_name}
                                </strong>،<br>
                                {safe_message}
                            </p>

                            {details_html}

                            {button_html}

                            <p style="margin:0;
                                      font-size:12px;
                                      color:#94a3b8;
                                      line-height:1.6;
                                      border-top:1px solid #f1f5f9;
                                      padding-top:18px;">
                                این پیام به‌صورت خودکار صادر شده است؛
                                لطفاً از پاسخ دادن به آن خودداری فرمایید.
                            </p>

                        </td>
                    </tr>

                    <!-- Fixed footer -->
                    <tr>
                        <td align="right" class="email-footer"
                            style="padding:22px 40px;
                                   background-color:#f8fafc;
                                   border-bottom-left-radius:12px;
                                   border-bottom-right-radius:12px;
                                   border-top:1px solid #f1f5f9;">

                            <table border="0" cellpadding="0"
                                   cellspacing="0" width="100%">
                                <tr>
                                    <td>
                                        <p style="margin:0;
                                                  font-size:11px;
                                                  color:#94a3b8;
                                                  line-height:1.5;">
                                            © {current_year}
                                            تمامی حقوق برای روشا محفوظ است.
                                        </p>
                                    </td>

                                    <td align="left" valign="top">
                                        {settings_html}
                                    </td>
                                </tr>
                            </table>

                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>

</body>
</html>"""
