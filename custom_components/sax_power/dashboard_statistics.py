"""Berechtigte Recorder-Auswertung für Vue (REQ-VUE-SAVINGS)."""

from __future__ import annotations

import calendar
import logging
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Literal, TypedDict

import voluptuous as vol
from homeassistant.auth.permissions.const import POLICY_READ
from homeassistant.components import websocket_api
from homeassistant.const import WEEKDAYS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.recorder import DATA_INSTANCE
from homeassistant.util import dt as dt_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
STATISTICS_COMMAND = "sax_power/dashboard/statistics"
_CALENDAR_PERIODS = ("day", "week", "month", "year")
_DATE_SCHEMA = vol.All(str, vol.Match(r"\A\d{4}-\d{2}-\d{2}\Z"))


class _Period(TypedDict):
    start: str | None
    end: str | None
    change: float | None


class _Bucket(TypedDict):
    start: str
    end: str
    change: float | None


class _Selection(_Period):
    start_date: str
    end_date: str
    period: Literal["hour", "day", "month"]
    buckets: list[_Bucket]


class _Statistics(TypedDict):
    entity_id: str | None
    time_zone: str
    today: str
    status: Literal["ok", "missing_entity", "recorder_unavailable"]
    periods: dict[str, _Period]
    selected: _Selection


@callback
def async_register_dashboard_statistics(hass: HomeAssistant) -> None:
    """Registriere die authentifizierte, ausschließlich lesende Auswertung."""
    if STATISTICS_COMMAND not in hass.data.get(websocket_api.DOMAIN, {}):
        websocket_api.async_register_command(hass, websocket_dashboard_statistics)


def _entity(hass: HomeAssistant, entry_id: str) -> er.RegistryEntry | None:
    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry_id}_economics_net_savings"
    )
    entity = registry.async_get(entity_id) if entity_id else None
    if entity is None or entity.config_entry_id != entry_id or entity.disabled:
        return None
    return entity


def _empty_result(hass: HomeAssistant, msg: dict[str, Any]) -> _Statistics:
    zone = dt_util.get_time_zone(hass.config.time_zone)
    assert zone is not None
    today = dt_util.now(zone).date()
    if ("start_date" in msg) != ("end_date" in msg):
        raise ValueError("Both dates are required")
    start_date = date.fromisoformat(msg.get("start_date", today.isoformat()))
    end_date = date.fromisoformat(msg.get("end_date", today.isoformat()))
    if start_date > end_date:
        raise ValueError("The start date must not follow the end date")
    start = datetime.combine(start_date, time.min, zone).astimezone(UTC)
    end = datetime.combine(end_date + timedelta(days=1), time.min, zone).astimezone(UTC)
    # HA frontend 20260729.7, data/energy.ts:getSuggestedPeriod. Energy's
    # inclusive end-of-day yields this many full local days, also across DST.
    days = (end_date - start_date).days
    period: Literal["hour", "day", "month"] = "hour"
    if (
        start_date.day == 1
        and end_date.day == calendar.monthrange(end_date.year, end_date.month)[1]
        and days > 35
    ):
        period = "month"
    elif days > 2:
        period = "day"
    return {
        "entity_id": None,
        "time_zone": hass.config.time_zone,
        "today": today.isoformat(),
        "status": "missing_entity",
        "periods": {
            period: {"start": None, "end": None, "change": None}
            for period in _CALENDAR_PERIODS
        },
        "selected": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "change": None,
            "period": period,
            "buckets": [],
        },
    }


def _read_statistics(
    hass: HomeAssistant,
    entity_id: str,
    result: _Statistics,
    first_weekday: str,
) -> _Statistics:
    # Recorder ist optional. Seine SQL-Abhängigkeiten werden erst importiert,
    # nachdem eine laufende Instanz gefunden wurde, und nur in deren Executor.
    from homeassistant.components.recorder.statistics import (  # noqa: PLC0415
        statistic_during_period,
        statistics_during_period,
    )
    from homeassistant.components.recorder.util import (  # noqa: PLC0415
        resolve_period,
    )

    for period in _CALENDAR_PERIODS:
        definition: dict[str, Any] = {"period": period}
        if period == "week":
            definition["first_weekday"] = first_weekday
        start, end = resolve_period({"calendar": definition})
        result["periods"][period] = {
            "start": start.isoformat() if start else None,
            "end": end.isoformat() if end else None,
            "change": statistic_during_period(
                hass, start, end, entity_id, {"change"}, None
            ).get("change"),
        }
    selected = result["selected"]
    assert selected["start"] is not None and selected["end"] is not None
    start = datetime.fromisoformat(selected["start"])
    end = datetime.fromisoformat(selected["end"])
    selected["change"] = statistic_during_period(
        hass, start, end, entity_id, {"change"}, None
    ).get("change")
    # hui-statistic-card rounds the Energy end up to midnight; the graph
    # keeps 23:59:59.999. Preserve both native boundaries, not a sum of bars.
    rows = statistics_during_period(
        hass,
        start,
        end - timedelta(milliseconds=1),
        {entity_id},
        selected["period"],
        None,
        {"change"},
    ).get(entity_id, [])
    selected["buckets"] = [
        {
            "start": datetime.fromtimestamp(row["start"], UTC).isoformat(),
            "end": datetime.fromtimestamp(row["end"], UTC).isoformat(),
            "change": row.get("change"),
        }
        for row in rows
    ]
    result["status"] = "ok"
    return result


@websocket_api.websocket_command(
    {
        vol.Required("type"): STATISTICS_COMMAND,
        vol.Required("entry_id"): vol.All(str, vol.Length(min=1, max=128)),
        vol.Optional("start_date"): _DATE_SCHEMA,
        vol.Optional("end_date"): _DATE_SCHEMA,
        vol.Optional("first_weekday", default="mon"): vol.In(WEEKDAYS),
    }
)
@websocket_api.async_response
async def websocket_dashboard_statistics(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Liefere nur die Statistik des berechtigten Netto-Ersparnis-Sensors."""
    entry_id = msg["entry_id"]
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Entry not found")
        return
    entity = _entity(hass, entry_id)
    if not connection.user.is_active or (
        entity is not None
        and not connection.user.permissions.check_entity(entity.entity_id, POLICY_READ)
    ):
        connection.send_error(msg["id"], websocket_api.ERR_UNAUTHORIZED, "Unauthorized")
        return
    try:
        result = _empty_result(hass, msg)
    except ValueError, OverflowError:
        connection.send_error(msg["id"], "invalid_format", "Invalid date range")
        return
    if entity is None:
        connection.send_result(msg["id"], result)
        return
    result["entity_id"] = entity.entity_id
    recorder = hass.data.get(DATA_INSTANCE)
    if recorder is None or recorder.engine is None:
        result["status"] = "recorder_unavailable"
        connection.send_result(msg["id"], result)
        return
    try:
        result = await recorder.async_add_executor_job(
            _read_statistics, hass, entity.entity_id, result, msg["first_weekday"]
        )
    except Exception:
        _LOGGER.exception("Vue-Statistik konnte nicht aus dem Recorder gelesen werden")
        connection.send_error(msg["id"], "recorder_error", "Statistics unavailable")
        return
    # Reconfigure, Entity-Umbenennung und Rechteentzug können während der
    # Datenbankabfrage erfolgen. Alte Ergebnisse dürfen dann nichts offenlegen.
    current = _entity(hass, entry_id)
    if (
        hass.config_entries.async_get_entry(entry_id) is not entry
        or current is None
        or current.entity_id != entity.entity_id
    ):
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Entity changed")
        return
    if not connection.user.is_active or not connection.user.permissions.check_entity(
        entity.entity_id, POLICY_READ
    ):
        connection.send_error(msg["id"], websocket_api.ERR_UNAUTHORIZED, "Unauthorized")
        return
    connection.send_result(msg["id"], result)
