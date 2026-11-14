"""Live lunar-site ephemeris backend powered by the JPL Horizons API.

The backend requests topocentric observer tables for the Sun and Earth from a
user-defined site on the Moon. It samples the 24 hours following the selected
UTC epoch at 30-minute intervals.

Important model boundary: Horizons supplies the local topocentric direction
relative to its lunar reference ellipsoid. This prototype does not yet apply
LOLA-derived local terrain masks, spacecraft attitude, array pointing, or a
radio-link budget. Visibility percentages are therefore geometric, ideal-
horizon estimates, not mission-certified results.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

import requests

from .models import MissionScenario


HORIZONS_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
WINDOW_HOURS = 24
SAMPLE_MINUTES = 30
REQUEST_TIMEOUT_SECONDS = 35


@dataclass(frozen=True)
class EphemerisSample:
    time_utc: datetime
    sun_azimuth_deg: float
    sun_elevation_deg: float
    earth_azimuth_deg: float
    earth_elevation_deg: float
    earth_range_km: float | None = None


@dataclass(frozen=True)
class AnalysisResult:
    solar_elevation_deg: float
    solar_azimuth_deg: float
    earth_elevation_deg: float
    earth_azimuth_deg: float
    sunlight_fraction: float
    earth_visibility_fraction: float
    simultaneous_visibility_fraction: float
    earth_visibility: bool
    simultaneous_visibility: bool
    earth_range_km: float | None
    samples: tuple[EphemerisSample, ...]
    model_name: str
    source_note: str


class EphemerisError(RuntimeError):
    """Raised when JPL Horizons cannot provide a usable ephemeris result."""


# Kept as a compatibility alias for code that imported the v0.1 stub error.
class EphemerisNotConfiguredError(EphemerisError):
    pass


def _as_float(value: str) -> float | None:
    cleaned = value.strip().replace("D", "E").replace("d", "E")
    if not cleaned or cleaned in {"--", "n.a.", "n/a", "NaN"}:
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _parse_horizons_csv(
    result_text: str,
    start_time: datetime,
    step_minutes: int = SAMPLE_MINUTES,
) -> list[tuple[datetime, float, float, float | None]]:
    """Extract timestamp, azimuth/elevation and (when requested) observer range.

    Horizons quantity 20 appends target-observer range and range-rate. Its
    distance is normally printed in AU; values above 2 are treated as km.
    Older/mocked two-column tables remain supported and yield range=None.
    """
    if "$$SOE" not in result_text or "$$EOE" not in result_text:
        raise EphemerisError(
            "JPL Horizons returned no ephemeris table. Check the selected date "
            "and coordinates, then try again."
        )

    table = result_text.split("$$SOE", 1)[1].split("$$EOE", 1)[0]
    parsed: list[tuple[datetime, float, float, float | None]] = []
    reader = csv.reader(io.StringIO(table), skipinitialspace=True)

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue

        # Observer tables may include non-numeric event/presence marker columns.
        numeric_values = [value for cell in row if (value := _as_float(cell)) is not None]
        if len(numeric_values) < 2:
            continue
        if len(numeric_values) >= 4:
            azimuth, elevation = numeric_values[-4], numeric_values[-3]
            range_value = numeric_values[-2]
            range_km = range_value * 149_597_870.7 if abs(range_value) < 2.0 else range_value
            if range_km <= 0:
                range_km = None
        else:
            azimuth, elevation = numeric_values[-2], numeric_values[-1]
            range_km = None
        if not (-360.0 <= azimuth <= 720.0 and -90.5 <= elevation <= 90.5):
            continue

        timestamp = _parse_horizons_time(row[0].strip(), start_time + timedelta(minutes=step_minutes * len(parsed)))
        parsed.append((timestamp, azimuth % 360.0, elevation, range_km))

    if not parsed:
        raise EphemerisError(
            "JPL Horizons responded, but LunaSight could not read the azimuth/elevation columns. "
            "The API table format may have changed."
        )
    return parsed


def _parse_horizons_time(value: str, fallback: datetime) -> datetime:
    value = value.strip().strip('"')
    formats = (
        "%Y-%b-%d %H:%M",
        "%Y-%b-%d %H:%M:%S",
        "%Y-%b-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return fallback


def _fetch_observer_series(
    scenario: MissionScenario,
    target_id: str,
    start_time: datetime,
    stop_time: datetime,
) -> list[tuple[datetime, float, float, float | None]]:
    """Fetch one target's apparent azimuth/elevation from a lunar surface site."""
    # Horizons Moon surface coordinates use east-positive longitude and
    # geodetic latitude in its lunar mean-Earth reference convention.
    east_longitude = scenario.longitude_deg % 360.0
    site_coord = f"{east_longitude:.8f},{scenario.latitude_deg:.8f},0.000"

    params = {
        "format": "json",
        "COMMAND": f"'{target_id}'",
        "OBJ_DATA": "'NO'",
        "MAKE_EPHEM": "'YES'",
        "EPHEM_TYPE": "'OBSERVER'",
        "CENTER": "'coord@301'",
        "COORD_TYPE": "'GEODETIC'",
        "SITE_COORD": f"'{site_coord}'",
        "START_TIME": f"'{start_time.strftime('%Y-%b-%d %H:%M')}'",
        "STOP_TIME": f"'{stop_time.strftime('%Y-%b-%d %H:%M')}'",
        "STEP_SIZE": f"'{SAMPLE_MINUTES}m'",
        "TIME_TYPE": "'UT'",
        "TIME_DIGITS": "'MINUTES'",
        "QUANTITIES": "'4,20'",  # apparent az/el + target-observer range/range-rate
        "APPARENT": "'AIRLESS'",
        "CSV_FORMAT": "'YES'",
    }

    try:
        response = requests.get(
            HORIZONS_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers={"User-Agent": "LunaSight-Desktop/0.4 (JPL Horizons client)"},
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise EphemerisError(
            "The JPL Horizons request timed out. Check your internet connection and try again."
        ) from exc
    except requests.RequestException as exc:
        raise EphemerisError(
            f"Could not reach the JPL Horizons API: {exc}. Check your internet connection."
        ) from exc
    except ValueError as exc:
        raise EphemerisError("JPL Horizons returned an unreadable response.") from exc

    if payload.get("error"):
        raise EphemerisError(f"JPL Horizons: {payload['error']}")
    result_text = payload.get("result")
    if not isinstance(result_text, str):
        raise EphemerisError("JPL Horizons response did not contain an ephemeris result.")

    return _parse_horizons_csv(result_text, start_time)


def _nearest_sample(
    samples: Iterable[tuple[datetime, float, float, float | None]], target_time: datetime
) -> tuple[datetime, float, float, float | None]:
    values = list(samples)
    return min(values, key=lambda item: abs((item[0] - target_time).total_seconds()))


def analyze(scenario: MissionScenario) -> AnalysisResult:
    """Analyze Sun/Earth directions and visibility over the next 24 UTC hours.

    Visibility currently means the target's *centre* is above the local
    reference-ellipsoid horizon (elevation > 0 degrees). It does not include
    the finite angular disk or local LOLA terrain masking yet.
    """
    start_time = scenario.date_time_utc
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    else:
        start_time = start_time.astimezone(timezone.utc)
    stop_time = start_time + timedelta(hours=WINDOW_HOURS)

    sun_rows = _fetch_observer_series(scenario, "10", start_time, stop_time)
    earth_rows = _fetch_observer_series(scenario, "399", start_time, stop_time)

    if len(sun_rows) < 2 or len(earth_rows) < 2:
        raise EphemerisError("JPL Horizons returned too few samples to assess the 24-hour window.")

    # Match the two tables by timestamp, tolerating minor formatting differences.
    earth_by_time = {row[0]: row for row in earth_rows}
    samples: list[EphemerisSample] = []
    for sun_time, sun_az, sun_el, _sun_range in sun_rows:
        earth_row = earth_by_time.get(sun_time)
        if earth_row is None:
            earth_row = _nearest_sample(earth_rows, sun_time)
            if abs((earth_row[0] - sun_time).total_seconds()) > 60:
                continue
        samples.append(
            EphemerisSample(
                time_utc=sun_time,
                sun_azimuth_deg=sun_az,
                sun_elevation_deg=sun_el,
                earth_azimuth_deg=earth_row[1],
                earth_elevation_deg=earth_row[2],
                earth_range_km=earth_row[3],
            )
        )

    if len(samples) < 2:
        raise EphemerisError("Sun and Earth ephemeris samples could not be aligned in time.")

    epoch_sample = min(samples, key=lambda sample: abs((sample.time_utc - start_time).total_seconds()))
    solar_visible = [sample.sun_elevation_deg > 0.0 for sample in samples]
    earth_visible = [sample.earth_elevation_deg > 0.0 for sample in samples]
    both_visible = [sun and earth for sun, earth in zip(solar_visible, earth_visible)]
    count = len(samples)

    return AnalysisResult(
        solar_elevation_deg=epoch_sample.sun_elevation_deg,
        solar_azimuth_deg=epoch_sample.sun_azimuth_deg,
        earth_elevation_deg=epoch_sample.earth_elevation_deg,
        earth_azimuth_deg=epoch_sample.earth_azimuth_deg,
        sunlight_fraction=sum(solar_visible) / count,
        earth_visibility_fraction=sum(earth_visible) / count,
        simultaneous_visibility_fraction=sum(both_visible) / count,
        earth_visibility=epoch_sample.earth_elevation_deg > 0.0,
        simultaneous_visibility=(epoch_sample.sun_elevation_deg > 0.0 and epoch_sample.earth_elevation_deg > 0.0),
        earth_range_km=epoch_sample.earth_range_km,
        samples=tuple(samples),
        model_name="JPL Horizons Observer Ephemeris",
        source_note=(
            "Live JPL Horizons topocentric apparent AZ/EL; Moon site coordinates "
            "are east-positive, geodetic, and interpreted in Horizons' lunar "
            "mean-Earth (DE421) convention. Visibility is centre-above-ideal-horizon "
            "at 30-minute sampling. Quantity 20 supplies the time-specific observer-to-Earth range. "
            "LOLA terrain masking is applied separately by the desktop UI; finite-disc corrections are not yet modeled."
        ),
    )
