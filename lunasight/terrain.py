"""NASA LOLA lunar south-polar terrain access and projection helpers.

The global 80S, 80 m/pixel LOLA COG is read remotely via GDAL's HTTP range
reader where supported. A small downsampled surface is kept in memory; the
large source GeoTIFF is not bundled with LunaSight.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
import os
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

import numpy as np

LOLA_COG_URL = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF"
LOLA_SOURCE = "NASA/GSFC PGDA · LRO LOLA · LDEM_80S_80MPP_ADJ · 80 m/pixel"
NASA_TREK_GLOBAL_DEM_URL = (
    "https://trek.nasa.gov/moon/trekarcgis/rest/services/"
    "LRO_LOLA_DEM_Global_256ppd_v06/ImageServer/exportImage"
)
NASA_TREK_POLAR_DEM_URLS = {
    "north": (
        "https://trek.nasa.gov/moon/trekarcgis/rest/services/"
        "LRO_LOLA_DEM_NPole45_100mp_v04/ImageServer/exportImage"
    ),
    "south": (
        "https://trek.nasa.gov/moon/trekarcgis/rest/services/"
        "LRO_LOLA_DEM_SPole45_100mp_v04/ImageServer/exportImage"
    ),
}
MOON_RADIUS_M = 1_737_400.0


@dataclass
class TerrainGrid:
    x: np.ndarray
    y: np.ndarray
    z: np.ndarray
    source: str
    spacing_m: float
    geographic_transformer: object | None = None
    raster_transform: object | None = None


def latlon_to_polar_xy(latitude_deg: float, longitude_deg: float) -> tuple[float, float]:
    """South-polar stereographic coordinates, Moon radius 1,737.4 km."""
    colat = math.radians(90.0 + latitude_deg)
    rho = 2.0 * MOON_RADIUS_M * math.tan(colat / 2.0)
    lon = math.radians(longitude_deg)
    return rho * math.sin(lon), -rho * math.cos(lon)


def polar_xy_to_latlon(x_m: float, y_m: float) -> tuple[float, float]:
    rho = math.hypot(x_m, y_m)
    colat = 2.0 * math.atan(rho / (2.0 * MOON_RADIUS_M))
    latitude = -90.0 + math.degrees(colat)
    longitude = math.degrees(math.atan2(x_m, -y_m))
    return latitude, ((longitude + 180.0) % 360.0) - 180.0


def orthographic_globe_click_to_latlon(
    screen_x: float, screen_y: float, *, azimuth_deg: float = -90.0,
    elevation_deg: float = -58.0,
) -> tuple[float, float] | None:
    """Invert a normalized click on a fixed orthographic sphere (front hemisphere).

    screen_x/screen_y are normalized to the projected globe radius, with y
    positive upward. Returns None for a click outside the visible disk.
    """
    disk2 = screen_x * screen_x + screen_y * screen_y
    if disk2 > 1.0:
        return None
    az = math.radians(azimuth_deg)
    elev = math.radians(elevation_deg)
    view = np.array([math.cos(elev) * math.cos(az), math.cos(elev) * math.sin(az), math.sin(elev)])
    right = np.array([-math.sin(az), math.cos(az), 0.0])
    up = np.array([-math.sin(elev) * math.cos(az), -math.sin(elev) * math.sin(az), math.cos(elev)])
    world = screen_x * right + screen_y * up + math.sqrt(max(0.0, 1.0 - disk2)) * view
    latitude = math.degrees(math.asin(max(-1.0, min(1.0, float(world[2])))))
    longitude = math.degrees(math.atan2(float(world[1]), float(world[0])))
    return latitude, ((longitude + 180.0) % 360.0) - 180.0


def make_demo_grid(size: int = 180) -> TerrainGrid:
    """Procedural relief for UI interaction when NASA data is not yet loaded.

    This is explicitly NOT a scientific terrain dataset.
    """
    axis = np.linspace(-300_000.0, 300_000.0, size)
    x, y = np.meshgrid(axis, axis)
    z = np.zeros_like(x, dtype=float)
    craters = [
        (-70_000, 80_000, 36_000, 5_000),
        (55_000, 35_000, 48_000, 6_500),
        (95_000, -105_000, 32_000, 4_500),
        (-145_000, -55_000, 55_000, 6_000),
        (15_000, -190_000, 28_000, 3_800),
        (-210_000, 150_000, 40_000, 4_700),
    ]
    for cx, cy, radius, depth in craters:
        r = np.hypot(x - cx, y - cy)
        bowl = -depth * np.exp(-((r / (radius * 0.72)) ** 4))
        rim = 850.0 * np.exp(-(((r - radius) / (radius * 0.12)) ** 2))
        z += bowl + rim
    # Gentle long-wavelength relief only to make the demonstration surface legible.
    z += 220.0 * np.sin(x / 72_000.0) * np.cos(y / 88_000.0)
    return TerrainGrid(x=x, y=y, z=z, source="ILLUSTRATIVE DEMO RELIEF · NOT NASA DATA", spacing_m=float(axis[1]-axis[0]))


def make_demo_site_patch(
    latitude_deg: float,
    longitude_deg: float,
    *,
    size: int = 90,
    half_width_m: float = 1_500.0,
) -> TerrainGrid:
    """Make deterministic, site-specific illustrative relief when no DEM is loaded."""
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("Latitude must be between -90 and +90 degrees.")
    if not math.isfinite(longitude_deg) or size < 2 or half_width_m <= 0:
        raise ValueError("Longitude, patch size, and patch width must be valid.")

    seed_latitude = int(round((latitude_deg + 90.0) * 10_000))
    seed_longitude = int(round((longitude_deg + 180.0) * 10_000))
    rng = np.random.default_rng(seed_latitude * 1_000_003 + seed_longitude)
    axis = np.linspace(-half_width_m, half_width_m, size)
    x, y = np.meshgrid(axis, axis)
    phase_x, phase_y = rng.uniform(-math.pi, math.pi, size=2)
    z = (
        24.0 * np.sin(x / 310.0 + phase_x)
        + 19.0 * np.cos(y / 420.0 + phase_y)
        + 13.0 * np.sin((x + y) / 560.0)
    )
    for _ in range(5):
        center_x, center_y = rng.uniform(-0.72, 0.72, size=2) * half_width_m
        radius = rng.uniform(0.12, 0.32) * half_width_m
        depth = rng.uniform(18.0, 85.0)
        distance = np.hypot(x - center_x, y - center_y)
        z -= depth * np.exp(-((distance / (radius * 0.72)) ** 4))
        z += 0.18 * depth * np.exp(
            -(((distance - radius) / (radius * 0.12)) ** 2)
        )

    spacing = float(axis[1] - axis[0])
    return TerrainGrid(
        x=x,
        y=y,
        z=z,
        source="SITE-SPECIFIC ILLUSTRATIVE RELIEF · NOT NASA DATA",
        spacing_m=spacing,
    )


def load_nasa_lola_grid(out_size: int = 1200, url: str = LOLA_COG_URL, source_label: str = LOLA_SOURCE) -> TerrainGrid:
    """Load the NASA 80S polar LOLA COG via HTTP range reads.

    Requires rasterio and pyproj. If the COG server or GDAL range access is
    unavailable, the caller should keep the labeled demo terrain visible.
    """
    try:
        import rasterio
        from rasterio.enums import Resampling
        from affine import Affine
        from pyproj import CRS, Transformer
    except Exception as exc:  # pragma: no cover - platform dependency
        raise RuntimeError("Install rasterio and pyproj to load NASA LOLA terrain.") from exc

    remote_url = "/vsicurl/" + url
    env = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_USE_HEAD": "NO",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".TIF,.tif",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_CACHEMAX": "128",
    }
    try:
        with rasterio.Env(**env):
            with rasterio.open(remote_url) as dataset:
                height = out_size
                width = out_size
                data = dataset.read(
                    1, out_shape=(height, width), masked=True,
                    resampling=Resampling.bilinear,
                )
                scale_x = dataset.width / width
                scale_y = dataset.height / height
                transform = dataset.transform * Affine.scale(scale_x, scale_y)
                cols = np.arange(width, dtype=float) + 0.5
                rows = np.arange(height, dtype=float) + 0.5
                xs = transform.c + cols * transform.a
                ys = transform.f + rows * transform.e
                xx, yy = np.meshgrid(xs, ys)
                if dataset.crs:
                    moon_geo = CRS.from_proj4(
                        f"+proj=longlat +R={MOON_RADIUS_M} +no_defs"
                    )
                    transformer = Transformer.from_crs(
                        dataset.crs, moon_geo, always_xy=True
                    )
                    lon, lat = transformer.transform(xx, yy)
                    # Convert geographic coordinates to LunaSight's south-polar map frame.
                    colat = np.radians(90.0 + np.asarray(lat))
                    rho = 2.0 * MOON_RADIUS_M * np.tan(colat / 2.0)
                    lonr = np.radians(lon)
                    map_x = rho * np.sin(lonr)
                    map_y = -rho * np.cos(lonr)
                    inverse = Transformer.from_crs(moon_geo, dataset.crs, always_xy=True)
                else:
                    map_x, map_y = xx, yy
                    inverse = None
                z = np.ma.filled(data, np.nan).astype(float)
                valid = np.isfinite(z)
                if valid.sum() < 100:
                    raise RuntimeError("NASA LOLA DEM did not contain enough valid elevation samples.")
                spacing = float(np.nanmedian(np.hypot(np.diff(map_x, axis=1), np.diff(map_y, axis=1))))
                return TerrainGrid(
                    map_x, map_y, z, source_label, spacing, inverse, transform
                )
    except Exception as exc:
        raise RuntimeError(f"Could not load NASA LOLA COG: {exc}") from exc


def _local_offsets_to_latlon(
    latitude_deg: float,
    longitude_deg: float,
    east_m: np.ndarray,
    north_m: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    distance = np.hypot(east_m, north_m)
    bearing = np.arctan2(east_m, north_m)
    angular_distance = distance / MOON_RADIUS_M
    latitude = math.radians(latitude_deg)
    longitude = math.radians(longitude_deg)
    sin_latitude = (
        math.sin(latitude) * np.cos(angular_distance)
        + math.cos(latitude) * np.sin(angular_distance) * np.cos(bearing)
    )
    target_latitude = np.arcsin(np.clip(sin_latitude, -1.0, 1.0))
    target_longitude = longitude + np.arctan2(
        np.sin(bearing) * np.sin(angular_distance) * math.cos(latitude),
        np.cos(angular_distance) - math.sin(latitude) * np.sin(target_latitude),
    )
    return np.degrees(target_latitude), (
        (np.degrees(target_longitude) + 180.0) % 360.0
    ) - 180.0


def _sample_raster_bilinear(
    elevation: np.ndarray,
    columns: np.ndarray,
    rows: np.ndarray,
) -> np.ndarray:
    """Sample pixel-center coordinates, ignoring nodata and out-of-bounds cells."""
    source = np.asarray(np.ma.filled(elevation, np.nan), dtype=float)
    columns, rows = np.broadcast_arrays(
        np.asarray(columns, dtype=float), np.asarray(rows, dtype=float)
    )
    valid_location = (
        np.isfinite(columns)
        & np.isfinite(rows)
        & (columns >= 0.0)
        & (rows >= 0.0)
        & (columns <= source.shape[1] - 1)
        & (rows <= source.shape[0] - 1)
    )
    col0 = np.clip(np.floor(np.nan_to_num(columns)).astype(np.intp), 0, source.shape[1] - 1)
    row0 = np.clip(np.floor(np.nan_to_num(rows)).astype(np.intp), 0, source.shape[0] - 1)
    col1 = np.minimum(col0 + 1, source.shape[1] - 1)
    row1 = np.minimum(row0 + 1, source.shape[0] - 1)
    col_fraction = columns - col0
    row_fraction = rows - row0

    result = np.zeros(columns.shape, dtype=float)
    weight_sum = np.zeros(columns.shape, dtype=float)
    for row_index, row_weight in (
        (row0, 1.0 - row_fraction),
        (row1, row_fraction),
    ):
        for col_index, col_weight in (
            (col0, 1.0 - col_fraction),
            (col1, col_fraction),
        ):
            weights = row_weight * col_weight
            values = source[row_index, col_index]
            valid = np.isfinite(values) & (np.abs(values) < 30_000.0) & valid_location
            result += np.where(valid, values, 0.0) * weights
            weight_sum += np.where(valid, weights, 0.0)
    return np.divide(
        result,
        weight_sum,
        out=np.full_like(result, np.nan),
        where=weight_sum > 0.0,
    )


def nasa_lola_surface_patch(
    grid: TerrainGrid,
    latitude_deg: float,
    longitude_deg: float,
    *,
    half_width_m: float = 5_000.0,
    size: int = 121,
) -> TerrainGrid:
    """Reproject a loaded LOLA raster to a regular local east/north view grid."""
    if grid.geographic_transformer is None or grid.raster_transform is None:
        raise ValueError("This LOLA grid does not include its source raster transform.")
    if not -90.0 <= latitude_deg <= 90.0 or not math.isfinite(longitude_deg):
        raise ValueError("A valid lunar coordinate is required for a terrain patch.")
    if half_width_m <= 0.0 or size < 5:
        raise ValueError("Patch width must be positive and size must be at least 5.")

    axis = np.linspace(-half_width_m, half_width_m, size)
    east, north = np.meshgrid(axis, axis)
    target_latitude, target_longitude = _local_offsets_to_latlon(
        latitude_deg, longitude_deg, east, north
    )
    source_x, source_y = grid.geographic_transformer.transform(
        target_longitude, target_latitude
    )
    pixel_columns, pixel_rows = (~grid.raster_transform) * (source_x, source_y)
    elevation = _sample_raster_bilinear(
        grid.z,
        np.asarray(pixel_columns) - 0.5,
        np.asarray(pixel_rows) - 0.5,
    ).astype(np.float32)
    if not np.isfinite(elevation).any():
        raise ValueError("The selected point is outside the loaded LOLA terrain coverage.")
    return TerrainGrid(
        east,
        north,
        elevation,
        grid.source,
        float(axis[1] - axis[0]),
    )


def _nasa_trek_cache_path(url: str, params: dict[str, str]) -> Path:
    cache_dir = Path.home() / ".cache" / "lunasight" / "trek_dem"
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(
        f"{url}?{urlencode(sorted(params.items()))}".encode("utf-8")
    ).hexdigest()
    return cache_dir / f"{key}.tif"


def _download_nasa_trek_image(
    url: str, bbox: tuple[float, float, float, float], spatial_reference: int,
    width: int, height: int,
) -> Path:
    params = {
        "bbox": ",".join(f"{coordinate:.8f}" for coordinate in bbox),
        "bboxSR": str(spatial_reference),
        "imageSR": str(spatial_reference),
        "size": f"{width},{height}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_Bilinear",
        "f": "image",
    }
    destination = _nasa_trek_cache_path(url, params)
    if destination.exists() and destination.stat().st_size > 1_024:
        return destination

    import requests

    temporary = destination.with_suffix(".part")
    try:
        response = requests.get(
            url,
            params=params,
            timeout=60,
            headers={"User-Agent": "LunaSight-Desktop/0.5 (NASA Moon Trek DEM client)"},
        )
        response.raise_for_status()
        content = response.content
        if not (content.startswith(b"II*\x00") or content.startswith(b"MM\x00*")):
            raise RuntimeError(
                "NASA Moon Trek did not return a GeoTIFF elevation image."
            )
        temporary.write_bytes(content)
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _sample_trek_images(
    image_paths: list[Path], x_values: np.ndarray, y_values: np.ndarray
) -> np.ndarray:
    import rasterio

    result = np.full(np.broadcast_shapes(x_values.shape, y_values.shape), np.nan)
    for path in image_paths:
        with rasterio.open(path) as dataset:
            data = dataset.read(1, masked=True)
            pixel_columns, pixel_rows = (~dataset.transform) * (x_values, y_values)
            values = _sample_raster_bilinear(
                data,
                np.asarray(pixel_columns) - 0.5,
                np.asarray(pixel_rows) - 0.5,
            )
            fill = ~np.isfinite(result) & np.isfinite(values)
            result[fill] = values[fill]
    return result


def load_nasa_trek_site_grid(
    latitude_deg: float,
    longitude_deg: float,
    *,
    half_width_m: float = 8_000.0,
    size: int = 161,
) -> TerrainGrid:
    """Fetch a local LOLA patch from NASA Moon Trek's global or polar service."""
    if not math.isfinite(latitude_deg) or not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("Latitude must be finite and between -90 and +90 degrees.")
    if not math.isfinite(longitude_deg):
        raise ValueError("Longitude must be finite.")
    if half_width_m <= 0.0 or size < 17 or size > 1_024:
        raise ValueError("Patch width must be positive and size must be from 17 to 1024.")

    latitude = float(latitude_deg)
    longitude = ((float(longitude_deg) + 180.0) % 360.0) - 180.0
    axis = np.linspace(-half_width_m, half_width_m, size)
    east, north = np.meshgrid(axis, axis)

    if abs(latitude) >= 60.0:
        hemisphere = "north" if latitude > 0.0 else "south"
        spatial_reference = 30118 if hemisphere == "north" else 30120
        latitude_radius = 90.0 - abs(latitude)
        rho = 2.0 * MOON_RADIUS_M * math.tan(math.radians(latitude_radius) / 2.0)
        longitude_radians = math.radians(longitude)
        center_x = rho * math.sin(longitude_radians)
        center_y = rho * math.cos(longitude_radians)
        if hemisphere == "south":
            center_y = -center_y
            target_x = (
                center_x + east * math.cos(longitude_radians)
                + north * math.sin(longitude_radians)
            )
            target_y = (
                center_y + east * math.sin(longitude_radians)
                - north * math.cos(longitude_radians)
            )
        else:
            target_x = (
                center_x + east * math.cos(longitude_radians)
                - north * math.sin(longitude_radians)
            )
            target_y = (
                center_y - east * math.sin(longitude_radians)
                - north * math.cos(longitude_radians)
            )
        url = NASA_TREK_POLAR_DEM_URLS[hemisphere]
        bbox = (
            center_x - half_width_m,
            center_y - half_width_m,
            center_x + half_width_m,
            center_y + half_width_m,
        )
        path = _download_nasa_trek_image(
            url, bbox, spatial_reference, size, size
        )
        elevation = _sample_trek_images([path], target_x, target_y)
        source = f"NASA Moon Trek · LRO LOLA {hemisphere}-polar DEM · 100 m/pixel"
    else:
        latitude_delta = math.degrees(half_width_m / MOON_RADIUS_M) * 1.5
        longitude_delta = latitude_delta / max(
            math.cos(math.radians(latitude)), 0.5
        )
        south = max(-90.0, latitude - latitude_delta)
        north_bound = min(90.0, latitude + latitude_delta)
        west = longitude - longitude_delta
        east_bound = longitude + longitude_delta
        segments: list[tuple[float, float]] = []
        if west < -180.0:
            segments = [(west + 360.0, 180.0), (-180.0, east_bound)]
        elif east_bound > 180.0:
            segments = [(west, 180.0), (-180.0, east_bound - 360.0)]
        else:
            segments = [(west, east_bound)]

        url = NASA_TREK_GLOBAL_DEM_URL
        image_paths = []
        total_width = east_bound - west
        for segment_west, segment_east in segments:
            segment_width = segment_east - segment_west
            if segment_width <= 0.0:
                continue
            image_width = max(
                17, int(round(size * segment_width / total_width))
            )
            image_paths.append(
                _download_nasa_trek_image(
                    url,
                    (segment_west, south, segment_east, north_bound),
                    104903,
                    image_width,
                    size,
                )
            )
        target_latitude, target_longitude = _local_offsets_to_latlon(
            latitude, longitude, east, north
        )
        elevation = _sample_trek_images(
            image_paths, target_longitude, target_latitude
        )
        source = "NASA Moon Trek · LRO LOLA global DEM · 256 pixels/degree"

    valid = np.isfinite(elevation)
    if not valid.any():
        raise RuntimeError(
            "NASA Moon Trek returned no valid LOLA elevations for this area."
        )
    return TerrainGrid(
        east,
        north,
        elevation.astype(np.float32),
        source,
        float(axis[1] - axis[0]),
    )


def nearest_grid_index(grid: TerrainGrid, x_m: float, y_m: float) -> tuple[int, int]:
    distance2 = (grid.x - x_m) ** 2 + (grid.y - y_m) ** 2
    idx = int(np.nanargmin(distance2))
    return np.unravel_index(idx, distance2.shape)


def local_patch(grid: TerrainGrid, x_m: float, y_m: float, half_width_m: float = 12_000.0):
    i, j = nearest_grid_index(grid, x_m, y_m)
    spacing = max(grid.spacing_m, 1.0)
    radius = max(4, min(100, int(half_width_m / spacing)))
    r0, r1 = max(0, i-radius), min(grid.z.shape[0], i+radius+1)
    c0, c1 = max(0, j-radius), min(grid.z.shape[1], j+radius+1)
    return grid.x[r0:r1, c0:c1], grid.y[r0:r1, c0:c1], grid.z[r0:r1, c0:c1], (i-r0, j-c0)


def terrain_horizon_at_azimuth(
    grid: TerrainGrid, x_m: float, y_m: float, azimuth_deg: float,
    eye_height_m: float = 1.7, max_range_m: float = 60_000.0,
    site_index: tuple[int, int] | None = None,
) -> float:
    """Approximate terrain horizon angle using the loaded DEM samples."""
    i, j = site_index if site_index is not None else nearest_grid_index(grid, x_m, y_m)
    ground = grid.z[i, j]
    if not np.isfinite(ground):
        return 0.0
    # Step along a ray in the map frame. Azimuth is clockwise from north.
    step = max(grid.spacing_m, 20.0)
    angle = math.radians(azimuth_deg)
    max_elevation = -90.0
    for distance in np.arange(step, max_range_m + step, step):
        sx = x_m + distance * math.sin(angle)
        sy = y_m - distance * math.cos(angle)
        ri, rj = nearest_grid_index_local(grid, sx, sy)
        if ri is None:
            break
        height = grid.z[ri, rj]
        if np.isfinite(height):
            elev = math.degrees(math.atan2(float(height) - float(ground) - eye_height_m, distance))
            max_elevation = max(max_elevation, elev)
    return max(0.0, max_elevation)


def nearest_grid_index_local(grid: TerrainGrid, x_m: float, y_m: float):
    # Grid is rectangular to map precision; avoid a full-array nearest search for every ray sample.
    xline = grid.x[0, :]
    yline = grid.y[:, 0]
    if len(xline) < 2 or len(yline) < 2:
        return None, None
    if xline[0] <= xline[-1]:
        col = int(np.searchsorted(xline, x_m))
        col = min(max(col, 0), len(xline) - 1)
        if col > 0 and abs(xline[col - 1] - x_m) < abs(xline[col] - x_m):
            col -= 1
    else:
        reversed_x = xline[::-1]
        col_rev = int(np.searchsorted(reversed_x, x_m))
        col_rev = min(max(col_rev, 0), len(xline) - 1)
        if col_rev > 0 and abs(reversed_x[col_rev - 1] - x_m) < abs(reversed_x[col_rev] - x_m):
            col_rev -= 1
        col = len(xline) - 1 - col_rev
    if yline[0] <= yline[-1]:
        row = int(np.searchsorted(yline, y_m))
        row = min(max(row, 0), len(yline) - 1)
        if row > 0 and abs(yline[row - 1] - y_m) < abs(yline[row] - y_m):
            row -= 1
    else:
        reversed_y = yline[::-1]
        row_rev = int(np.searchsorted(reversed_y, y_m))
        row_rev = min(max(row_rev, 0), len(yline) - 1)
        if row_rev > 0 and abs(reversed_y[row_rev - 1] - y_m) < abs(reversed_y[row_rev] - y_m):
            row_rev -= 1
        row = len(yline) - 1 - row_rev
    if row < 0 or col < 0 or row >= grid.z.shape[0] or col >= grid.z.shape[1]:
        return None, None
    if abs(float(xline[col]) - x_m) > grid.spacing_m * 1.8 or abs(float(yline[row]) - y_m) > grid.spacing_m * 1.8:
        return None, None
    return row, col


LOLA_5M_SITES = {
    "01": "Connecting ridge",
    "04": "Shackleton rim",
    "07": "Peak near Shackleton",
    "11": "de Gerlache rim",
    "20": "Leibnitz beta plateau",
    "23": "Malapert massif",
}

def load_nasa_5m_site_tile(site_number: str, out_size: int = 900) -> TerrainGrid:
    site = str(site_number).zfill(2)
    if site not in LOLA_5M_SITES:
        raise ValueError("Select one of NASA PGDA's six published south-pole 5 m LOLA site tiles.")
    url = (
        "https://pgda.gsfc.nasa.gov/data/LOLA_5mpp/"
        f"Site{site}/Site{site}_final_adj_5mpp_surf.tif"
    )
    label = f"NASA/GSFC PGDA · LRO LOLA · Site {site} ({LOLA_5M_SITES[site]}) · 5 m/pixel source"
    return load_nasa_lola_grid(out_size=out_size, url=url, source_label=label)

# Whole-Moon locator products from NASA's Scientific Visualization Studio.
# The 4 px/degree DEM is small enough for a one-click download; 16 px/degree
# is an optional higher-detail global model. Both cover the full globe.
GLOBAL_LOLA_URLS = {
    4: "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_4.tif",
    16: "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_16.tif",
}
GLOBAL_LOLA_SOURCES = {
    4: "NASA/GSFC SVS CGI Moon Kit · LRO LOLA global DEM · 4 pixels/degree",
    16: "NASA/GSFC SVS CGI Moon Kit · LRO LOLA global DEM · 16 pixels/degree",
}
GLOBAL_COLOR_URL = "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/lroc_color_2k.jpg"
GLOBAL_COLOR_SOURCE = "NASA/GSFC SVS · 2025 LROC WAC-derived global color map (polar fill is lower-resolution LDAM)"


@dataclass
class GlobalLolaGrid:
    """Global equirectangular LOLA elevation grid for whole-Moon navigation.

    Elevations are metres relative to the 1,737.4 km reference sphere.
    Array convention: north-to-south rows, west-to-east columns, longitude
    centred on 0 degrees (-180 to +180). This is a global locator DEM, not a
    substitute for local high-resolution landing-site topography.
    """
    elevation_m: np.ndarray
    ppd: int
    source: str
    color_rgb: np.ndarray | None = None
    color_source: str | None = None

    @property
    def latitude_count(self) -> int:
        return int(self.elevation_m.shape[0])

    @property
    def longitude_count(self) -> int:
        return int(self.elevation_m.shape[1])


def _cache_directory() -> Path:
    path = Path.home() / ".cache" / "lunasight" / "global_moon"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _download_cached(url: str, filename: str, timeout_seconds: int = 90) -> Path:
    """Download a public NASA dataset once and keep it in the user's cache."""
    import requests

    destination = _cache_directory() / filename
    if destination.exists() and destination.stat().st_size > 1024:
        return destination
    temporary = destination.with_suffix(destination.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=timeout_seconds,
                          headers={"User-Agent": "LunaSight-Desktop/0.5 (NASA lunar data client)"}) as response:
            response.raise_for_status()
            with temporary.open("wb") as stream:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        stream.write(chunk)
        if not temporary.exists() or temporary.stat().st_size <= 1024:
            raise RuntimeError("NASA returned an empty or incomplete data file.")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def load_nasa_global_moon_model(resolution_ppd: int = 4, include_color: bool = True) -> GlobalLolaGrid:
    """Download/read a NASA global LOLA DEM and optional NASA global texture.

    4 ppd is the recommended first load (~4 MB). 16 ppd is a larger optional
    global DEM (~63 MB). The color JPEG is a visualization texture only; the
    elevation model remains the LOLA DEM. Its high-polar-latitude fill should
    not be interpreted as high-resolution optical photography.
    """
    if resolution_ppd not in GLOBAL_LOLA_URLS:
        raise ValueError("Available global LOLA DEM resolutions are 4 or 16 pixels per degree.")
    try:
        import rasterio
    except Exception as exc:  # pragma: no cover - platform dependency
        raise RuntimeError("Install rasterio to read NASA's global LOLA GeoTIFF.") from exc

    path = _download_cached(GLOBAL_LOLA_URLS[resolution_ppd], f"ldem_{resolution_ppd}.tif")
    try:
        with rasterio.open(path) as dataset:
            elevation_km = dataset.read(1, masked=True)
        elevation_m = np.ma.filled(elevation_km, np.nan).astype(np.float32) * 1000.0
        if elevation_m.ndim != 2 or elevation_m.size < 100_000:
            raise RuntimeError("The downloaded global LOLA raster has an unexpected shape.")
        # NASA SVS provides the floating-point maps in kilometres relative to
        # the 1,737.4 km reference sphere; convert the offset to metres.
    except Exception as exc:
        raise RuntimeError(f"Could not read NASA global LOLA DEM: {exc}") from exc

    color_rgb = None
    color_source = None
    if include_color:
        try:
            from PIL import Image
            color_path = _download_cached(GLOBAL_COLOR_URL, "lroc_color_2k.jpg")
            with Image.open(color_path) as image_file:
                color_rgb = np.asarray(image_file.convert("RGB"), dtype=np.uint8)
            color_source = GLOBAL_COLOR_SOURCE
        except Exception:
            # Elevation-based shading remains available if the texture service
            # is temporarily unreachable or Pillow cannot decode the image.
            color_rgb = None
            color_source = None

    return GlobalLolaGrid(
        elevation_m=elevation_m,
        ppd=resolution_ppd,
        source=GLOBAL_LOLA_SOURCES[resolution_ppd],
        color_rgb=color_rgb,
        color_source=color_source,
    )


def latlon_to_global_grid_index(latitude_deg: float, longitude_deg: float,
                                shape: tuple[int, int]) -> tuple[int, int]:
    """Map a Moon coordinate to a north-up, 0°-centred global raster index."""
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("Latitude must be between -90 and +90 degrees.")
    height, width = shape
    row = int(round((90.0 - latitude_deg) / 180.0 * (height - 1)))
    lon = ((longitude_deg + 180.0) % 360.0) - 180.0
    col = int(round((lon + 180.0) / 360.0 * width)) % width
    return min(max(row, 0), height - 1), col


def global_dem_height_at(grid: GlobalLolaGrid, latitude_deg: float,
                         longitude_deg: float) -> float | None:
    value = global_dem_sample(grid, latitude_deg, longitude_deg)
    return float(value) if math.isfinite(float(value)) else None


def global_dem_sample(
    grid: GlobalLolaGrid, latitude_deg: np.ndarray | float,
    longitude_deg: np.ndarray | float,
) -> np.ndarray | float:
    """Bilinearly sample the global DEM, wrapping longitude and ignoring nodata."""
    latitude = np.asarray(latitude_deg, dtype=float)
    longitude = np.asarray(longitude_deg, dtype=float)
    if not np.isfinite(latitude).all() or np.any((latitude < -90.0) | (latitude > 90.0)):
        raise ValueError("Latitude must be finite and between -90 and +90 degrees.")
    if not np.isfinite(longitude).all():
        raise ValueError("Longitude must be finite.")

    elevation = np.asarray(grid.elevation_m)
    if elevation.ndim != 2 or min(elevation.shape) < 2:
        raise ValueError("Global elevation must be a two-dimensional grid.")
    row_position = (90.0 - latitude) * (elevation.shape[0] - 1) / 180.0
    column_position = np.mod(longitude + 180.0, 360.0) * elevation.shape[1] / 360.0
    row0 = np.floor(row_position).astype(np.intp)
    col0 = np.floor(column_position).astype(np.intp) % elevation.shape[1]
    row1 = np.minimum(row0 + 1, elevation.shape[0] - 1)
    col1 = (col0 + 1) % elevation.shape[1]
    row_fraction = row_position - row0
    col_fraction = column_position - np.floor(column_position)

    samples = (
        elevation[row0, col0],
        elevation[row0, col1],
        elevation[row1, col0],
        elevation[row1, col1],
    )
    weights = (
        (1.0 - row_fraction) * (1.0 - col_fraction),
        (1.0 - row_fraction) * col_fraction,
        row_fraction * (1.0 - col_fraction),
        row_fraction * col_fraction,
    )
    result = np.zeros(np.broadcast_shapes(latitude.shape, longitude.shape), dtype=float)
    weight_sum = np.zeros_like(result)
    for sample, weight in zip(samples, weights):
        sample_values, sample_weights = np.broadcast_arrays(
            np.asarray(sample, dtype=float), np.asarray(weight, dtype=float)
        )
        valid = np.isfinite(sample_values)
        result += np.where(valid, sample_values, 0.0) * sample_weights
        weight_sum += np.where(valid, sample_weights, 0.0)
    result = np.divide(
        result, weight_sum, out=np.full_like(result, np.nan), where=weight_sum > 0.0
    )
    return float(result) if result.ndim == 0 else result


def resample_global_elevation(
    grid: GlobalLolaGrid, latitude_count: int, longitude_count: int
) -> np.ndarray:
    """Resample global elevation onto a screen-sized mesh without aliasing."""
    source = np.asarray(grid.elevation_m, dtype=float)
    if source.ndim != 2 or min(source.shape) < 2:
        raise ValueError("Global elevation must be a two-dimensional grid.")
    if latitude_count < 2 or longitude_count < 2:
        raise ValueError("Resampled grid dimensions must each be at least 2.")

    source_rows, source_cols = source.shape
    target_cell_rows = latitude_count - 1
    target_cell_cols = longitude_count - 1
    if target_cell_rows < source_rows and target_cell_cols < source_cols:
        from PIL import Image

        valid = np.isfinite(source)
        size = (target_cell_cols, target_cell_rows)
        cell_weights = np.asarray(
            Image.fromarray(valid.astype(np.float32)).resize(
                size, Image.Resampling.BOX
            ),
            dtype=float,
        )
        cell_totals = np.asarray(
            Image.fromarray(
                np.where(valid, source, 0.0).astype(np.float32)
            ).resize(size, Image.Resampling.BOX),
            dtype=float,
        )
        cell_values = np.divide(
            cell_totals,
            cell_weights,
            out=np.zeros_like(cell_totals),
            where=cell_weights > 0.0,
        )

        row_totals = np.empty((latitude_count, target_cell_cols), dtype=float)
        row_weights = np.empty_like(row_totals)
        row_totals[0] = cell_values[0] * cell_weights[0]
        row_weights[0] = cell_weights[0]
        row_totals[-1] = cell_values[-1] * cell_weights[-1]
        row_weights[-1] = cell_weights[-1]
        row_totals[1:-1] = (
            cell_values[:-1] * cell_weights[:-1]
            + cell_values[1:] * cell_weights[1:]
        )
        row_weights[1:-1] = cell_weights[:-1] + cell_weights[1:]

        result_totals = np.empty((latitude_count, longitude_count), dtype=float)
        result_weights = np.empty_like(result_totals)
        result_totals[:, 0] = row_totals[:, -1] + row_totals[:, 0]
        result_weights[:, 0] = row_weights[:, -1] + row_weights[:, 0]
        result_totals[:, 1:-1] = row_totals[:, :-1] + row_totals[:, 1:]
        result_weights[:, 1:-1] = row_weights[:, :-1] + row_weights[:, 1:]
        result_totals[:, -1] = result_totals[:, 0]
        result_weights[:, -1] = result_weights[:, 0]
        return np.divide(
            result_totals,
            result_weights,
            out=np.full_like(result_totals, np.nan),
            where=result_weights > 0.0,
        )

    row_positions = np.linspace(0.0, source_rows - 1, latitude_count)
    col_positions = np.linspace(0.0, source_cols, longitude_count)
    row0 = np.floor(row_positions).astype(int)
    row1 = np.minimum(row0 + 1, source_rows - 1)
    col0 = np.floor(col_positions).astype(int) % source_cols
    col1 = (col0 + 1) % source_cols
    row_weight = row_positions - row0
    col_weight = col_positions - np.floor(col_positions)

    result = np.zeros((latitude_count, longitude_count), dtype=float)
    weight_sum = np.zeros_like(result)
    for rows, row_weights in (
        (row0, 1.0 - row_weight),
        (row1, row_weight),
    ):
        for cols, col_weights in (
            (col0, 1.0 - col_weight),
            (col1, col_weight),
        ):
            weights = row_weights[:, None] * col_weights[None, :]
            values = source[rows[:, None], cols[None, :]]
            valid = np.isfinite(values)
            result += np.where(valid, values, 0.0) * weights
            weight_sum += valid * weights

    return np.divide(
        result,
        weight_sum,
        out=np.full_like(result, np.nan),
        where=weight_sum > 0.0,
    )


def global_dem_local_patch(
    grid: GlobalLolaGrid, latitude_deg: float, longitude_deg: float,
    half_width_m: float = 60_000.0, size: int = 71,
):
    """Extract a coarse local elevation patch from a whole-Moon global DEM.

    A spherical azimuthal-equidistant patch is used so that local east/north
    distances remain meaningful near both poles. The DEM's native resolution
    remains the limit: this is a preview, not a landing-hazard or precise
    local-horizon product.
    """
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("Latitude must be between -90 and +90 degrees.")
    if half_width_m <= 0 or size < 5:
        raise ValueError("Patch width must be positive and size must be at least 5.")

    offsets = np.linspace(-half_width_m, half_width_m, size)
    east, north = np.meshgrid(offsets, offsets)
    distance = np.hypot(east, north)
    bearing = np.arctan2(east, north)
    angular_distance = distance / MOON_RADIUS_M
    lat1 = math.radians(latitude_deg)
    lon1 = math.radians(longitude_deg)
    sin_lat2 = (math.sin(lat1) * np.cos(angular_distance) +
                math.cos(lat1) * np.sin(angular_distance) * np.cos(bearing))
    lat2 = np.arcsin(np.clip(sin_lat2, -1.0, 1.0))
    lon2 = lon1 + np.arctan2(
        np.sin(bearing) * np.sin(angular_distance) * math.cos(lat1),
        np.cos(angular_distance) - math.sin(lat1) * np.sin(lat2),
    )
    lat_deg = np.degrees(lat2)
    lon_deg = ((np.degrees(lon2) + 180.0) % 360.0) - 180.0

    heights = np.asarray(
        global_dem_sample(grid, lat_deg, lon_deg), dtype=np.float32
    )
    return east, north, heights, (size // 2, size // 2)
