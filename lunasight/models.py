from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class MissionScenario:
    """A user-defined lunar landing scenario."""

    site_name: str
    latitude_deg: float
    longitude_deg: float
    date_time_utc: datetime

    @property
    def label(self) -> str:
        return f"{self.site_name} · {self.date_time_utc:%Y-%m-%d %H:%M} UTC"


def build_scenario(
    site_name: str,
    latitude_text: str,
    longitude_text: str,
    date_text: str,
    time_text: str,
) -> MissionScenario:
    """Validate form values and return a scenario in UTC."""
    name = site_name.strip()
    if not name:
        raise ValueError("Please enter a landing-site name.")

    try:
        latitude = float(latitude_text.strip())
    except ValueError as exc:
        raise ValueError("Latitude must be a number between -90 and 90.") from exc

    try:
        longitude = float(longitude_text.strip())
    except ValueError as exc:
        raise ValueError("Longitude must be a number between -180 and 360.") from exc

    if not -90.0 <= latitude <= 90.0:
        raise ValueError("Latitude must be between -90° and 90°.")
    if not -180.0 <= longitude <= 360.0:
        raise ValueError("Longitude must be between -180° and 360°.")

    try:
        parsed = datetime.strptime(
            f"{date_text.strip()} {time_text.strip()}", "%Y-%m-%d %H:%M"
        ).replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError("Use date YYYY-MM-DD and time HH:MM (UTC).") from exc

    return MissionScenario(
        site_name=name,
        latitude_deg=latitude,
        longitude_deg=longitude,
        date_time_utc=parsed,
    )
