"""Photometric and radio-frequency estimates for LunaSight.

All RF profiles are lunar-vicinity / near-Earth uplink configurations drawn
from NASA/JPL DSN engineering and services references. They are examples,
not the radio configuration of every NASA or CLPS spacecraft. Received power is a free-space reference estimate; a true
link closure additionally needs mission-specific spacecraft antenna patterns,
receiver G/T, modulation/coding, bandwidth, pointing and polarization losses.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

C_M_S = 299_792_458.0
MEAN_EARTH_MOON_RANGE_KM = 384_400.0
SOLAR_TSI_W_M2 = 1361.0
# Approximate photopic conversion for the unattenuated solar spectrum at 1 AU.
# It is a display/education estimate, not a calibrated lunar lux prediction.
NORMAL_SOLAR_ILLUMINANCE_LUX = 127_000.0


@dataclass(frozen=True)
class DSNProfile:
    key: str
    label: str
    band: str
    frequency_hz: float
    uplink_range_mhz: str
    eirp_dbw: float
    transmitter_power_w: float
    antenna: str
    source_note: str

    @property
    def wavelength_m(self) -> float:
        return C_M_S / self.frequency_hz


# Lunar vicinity communications use the near-Earth allocations, not the
# deep-space S/X/Ka allocations. Frequencies are the nominal centres from
# JPL DSN 810-005 Module 104 Rev. N and NASA HLS-CONOP-008 Table 4-1.
# EIRP values below are near-Earth 34 m DSN configurations where the source
# provides a technically consistent antenna-specific value.
DSN_PROFILES: dict[str, DSNProfile] = {
    "S_34M_20KW": DSNProfile(
        "S_34M_20KW", "S-band · DSS-24 · 34 m · 20 kW", "S", 2.0675e9,
        "2025–2110 MHz (near-Earth lunar uplink)", 98.3, 20_000.0, "34 m BWG · DSS-24",
        "JPL DSN 810-005 Module 104 Rev. N, Table 2: near-Earth maximum EIRP 128.3 dBm = 98.3 dBW; nominal 20 kW transmitter.",
    ),
    "S_34M_250W": DSNProfile(
        "S_34M_250W", "S-band · DSS-26 · 34 m · 250 W", "S", 2.0675e9,
        "2025–2110 MHz (near-Earth lunar uplink)", 78.9, 250.0, "34 m BWG · DSS-26",
        "JPL DSN 810-005 Module 104 Rev. N, Table 2: near-Earth maximum EIRP 108.9 dBm = 78.9 dBW; 250 W transmitter.",
    ),
    "X_34M_20KW": DSNProfile(
        "X_34M_20KW", "X-band · DSS-24 · 34 m · 20 kW", "X", 7.2125e9,
        "7190–7235 MHz (near-Earth lunar uplink)", 109.7, 20_000.0, "34 m BWG · DSS-24",
        "JPL DSN 810-005 Module 104 Rev. N, Table 3: near-Earth maximum EIRP 139.7 dBm = 109.7 dBW; 20 kW transmitter.",
    ),
    "X_34M_80KW": DSNProfile(
        "X_34M_80KW", "X-band · DSS-26 · 34 m · 80 kW", "X", 7.2125e9,
        "7190–7235 MHz (near-Earth lunar uplink)", 115.3, 80_000.0, "34 m BWG · DSS-26",
        "JPL DSN 810-005 Module 104 Rev. N, Table 3: near-Earth maximum EIRP 145.3 dBm = 115.3 dBW; 80 kW transmitter.",
    ),
}

# Bands recommended for Earth-to-lunar-surface links by NASA HLS-CONOP-008
# (Table 4-1). K-band is included in the report, but not offered as a numeric
# EIRP profile because the summarized DSN catalogue's 127.7 dBW / 250 W entry
# is not independently reconciled with the antenna-specific engineering data available here.
LUNAR_RF_BANDS = {
    "S": {"uplink": "2025–2110 MHz", "downlink": "2200–2290 MHz", "center_hz": 2.0675e9},
    "X": {"uplink": "7190–7235 MHz", "downlink": "8450–8500 MHz", "center_hz": 7.2125e9},
    "K": {"uplink": "22.55–23.15 GHz", "downlink": "25.5–27.0 GHz", "center_hz": 22.85e9},
}



@dataclass(frozen=True)
class RFLinkResult:
    profile: DSNProfile
    range_km: float
    free_space_path_loss_db: float
    eirp_dbw: float
    receiver_gain_dbi: float
    other_losses_db: float
    received_power_dbw_if_los: float
    received_power_dbm_if_los: float
    earth_elevation_deg: float
    local_horizon_deg: float
    line_of_sight: bool
    status: str


def free_space_path_loss_db(frequency_hz: float, range_km: float) -> float:
    if (
        not math.isfinite(frequency_hz)
        or not math.isfinite(range_km)
        or frequency_hz <= 0
        or range_km <= 0
    ):
        raise ValueError("Frequency and range must be positive.")
    distance_m = range_km * 1000.0
    return 20.0 * math.log10(4.0 * math.pi * distance_m * frequency_hz / C_M_S)


def calculate_rf_link(
    profile: DSNProfile,
    earth_elevation_deg: float,
    range_km: float = MEAN_EARTH_MOON_RANGE_KM,
    receiver_gain_dbi: float = 0.0,
    other_losses_db: float = 2.0,
    local_horizon_deg: float = 0.0,
) -> RFLinkResult:
    """Calculate Earth-to-Moon uplink power at an idealized lander receiver.

    DSN EIRP already combines ground transmitter output and ground antenna
    gain. `receiver_gain_dbi=0` is an isotropic reference, not a claimed CLPS
    antenna. `line_of_sight` is only a center-of-Earth-above-local-horizon
    check. Power is a clear-path free-space reference; a below-horizon result
    is not an estimate of diffracted or reflected signal or a station-specific
    link.
    """
    if not math.isfinite(range_km) or range_km <= 0:
        raise ValueError("Earth–Moon range must be greater than zero.")
    if not math.isfinite(receiver_gain_dbi):
        raise ValueError("Receiver gain must be finite.")
    if not math.isfinite(other_losses_db) or other_losses_db < 0:
        raise ValueError("Other losses cannot be negative.")
    path_loss = free_space_path_loss_db(profile.frequency_hz, range_km)
    pr_dbw = profile.eirp_dbw - path_loss + receiver_gain_dbi - other_losses_db
    los = earth_elevation_deg > local_horizon_deg
    if los:
        status = "Earth center is above the modeled local horizon"
    else:
        status = (
            "Earth center is below the modeled horizon; "
            "station-specific and partial-disk visibility are not modeled"
        )
    return RFLinkResult(
        profile=profile,
        range_km=range_km,
        free_space_path_loss_db=path_loss,
        eirp_dbw=profile.eirp_dbw,
        receiver_gain_dbi=receiver_gain_dbi,
        other_losses_db=other_losses_db,
        received_power_dbw_if_los=pr_dbw,
        received_power_dbm_if_los=pr_dbw + 30.0,
        earth_elevation_deg=earth_elevation_deg,
        local_horizon_deg=local_horizon_deg,
        line_of_sight=los,
        status=status,
    )


def estimate_solar_illuminance_lux(
    solar_elevation_deg: float,
    local_horizon_deg: float = 0.0,
    normal_illuminance_lux: float = NORMAL_SOLAR_ILLUMINANCE_LUX,
) -> float:
    """Direct-beam illuminance on a horizontal surface (not helmet visor lux)."""
    if solar_elevation_deg <= local_horizon_deg:
        return 0.0
    incidence = math.sin(math.radians(max(0.0, solar_elevation_deg)))
    return normal_illuminance_lux * incidence


def estimate_solar_irradiance_w_m2(
    solar_elevation_deg: float, local_horizon_deg: float = 0.0
) -> float:
    if solar_elevation_deg <= local_horizon_deg:
        return 0.0
    return SOLAR_TSI_W_M2 * math.sin(math.radians(solar_elevation_deg))


def preliminary_site_assessment(
    sunlight_fraction: float | None,
    earth_visibility_fraction: float | None,
    simultaneous_fraction: float | None,
    has_terrain_data: bool,
) -> tuple[str, str]:
    """A transparent educational screen, never a landing certification."""
    if sunlight_fraction is None or earth_visibility_fraction is None or simultaneous_fraction is None:
        return "INSUFFICIENT DATA", "Run JPL Horizons analysis before assessing this site."
    sun = sunlight_fraction * 100.0
    earth = earth_visibility_fraction * 100.0
    both = simultaneous_fraction * 100.0
    if sun < 20 or earth < 10:
        label = "HIGH CONSTRAINT"
    elif sun >= 70 and earth >= 50 and both >= 30 and has_terrain_data:
        label = "GEOMETRICALLY PROMISING"
    else:
        label = "TRADE STUDY REQUIRED"
    terrain_note = "LOLA terrain mask available." if has_terrain_data else "No local LOLA horizon mask: flat-horizon geometry only; a positive label is withheld."
    return label, f"24 h sampled geometry: sunlight {sun:.1f}%, Earth visibility {earth:.1f}%, simultaneous {both:.1f}%. {terrain_note} Not a landing certification."
