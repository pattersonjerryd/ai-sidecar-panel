from __future__ import annotations

import json
import smtplib
import ssl
import time
from email.message import EmailMessage
from typing import Optional, Dict
from urllib import request, error

from apps.sidecar.core.settings import (
    EMAIL_ENABLED,
    EMAIL_SMTP_HOST,
    EMAIL_SMTP_PORT,
    EMAIL_SMTP_TLS,
    EMAIL_USERNAME,
    EMAIL_PASSWORD,
    EMAIL_FROM,
    EMAIL_TO,
    WEBHOOK_ENABLED,
    WEBHOOK_URL,
    NOTIFY_DEDUP_SECONDS,
    QUIET_HOURS,  # "22-6" to suppress between 22:00–06:00 local
)

_last_sent_per_sensor: Dict[str, float] = {}

def _in_quiet_hours(now_local: time.struct_time) -> bool:
    """
    QUIET_HOURS format: "startHour-endHour" 24h clock, e.g. "22-6".
    If unset or invalid -> not quiet.
    """
    if not QUIET_HOURS:
        return False
    try:
        start_s, end_s = QUIET_HOURS.split("-", 1)
        start = int(start_s)
        end = int(end_s)
        h = now_local.tm_hour
        if start == end:
            return False  # no quiet if 24h wrap of zero length
        if start < end:
            return start <= h < end
        # wrap over midnight
        return h >= start or h < end
    except Exception:
        return False

def _should_skip(sensor_id: str, now: float) -> bool:
    last = _last_sent_per_sensor.get(sensor_id, 0.0)
    if NOTIFY_DEDUP_SECONDS <= 0:
        return False
    if now - last < NOTIFY_DEDUP_SECONDS:
        return True
    _last_sent_per_sensor[sensor_id] = now
    return False

def _send_email(subject: str, body: str) -> None:
    if not EMAIL_ENABLED:
        return
    if not (EMAIL_SMTP_HOST and EMAIL_FROM and EMAIL_TO):
        return
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(EMAIL_TO)
    msg.set_content(body)
    context = ssl.create_default_context()
    if EMAIL_SMTP_TLS:
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.starttls(context=context)
            if EMAIL_USERNAME or EMAIL_PASSWORD:
                server.login(EMAIL_USERNAME or "", EMAIL_PASSWORD or "")
            server.send_message(msg)
    else:
        with smtplib.SMTP_SSL(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT, context=context) as server:
            if EMAIL_USERNAME or EMAIL_PASSWORD:
                server.login(EMAIL_USERNAME or "", EMAIL_PASSWORD or "")
            server.send_message(msg)

def _post_webhook(payload: dict) -> None:
    if not WEBHOOK_ENABLED or not WEBHOOK_URL:
        return
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as _resp:
            pass
    except error.URLError:
        # Best-effort; avoid raising in request path
        pass

def notify_alert(*, sensor_id: str, t: float, v: float, z: float, msg: str) -> None:
    """
    Best-effort notification fanout. Dedupe, quiet hours, then send email + webhook.
    Non-blocking philosophy: failures are swallowed (logged externally if desired).
    """
    now = time.time()
    if _should_skip(sensor_id, now):
        return
    if _in_quiet_hours(time.localtime(now)):
        return
    subject = f"[Sidecar] Alert on {sensor_id} z={z:.2f}"
    body = f"""Sensor: {sensor_id}
Time:  {int(t)} (epoch)
Value: {v}
Z:     {z:.2f}
Msg:   {msg}
"""
    _send_email(subject, body)
    _post_webhook(
        {
            "type": "sidecar.alert",
            "sensor_id": sensor_id,
            "t": t,
            "v": v,
            "z": z,
            "msg": msg,
        }
    )
