from __future__ import annotations

import math

import numpy as np

from .terrain import TerrainGrid


def _axis_brackets(
    axis: np.ndarray, values: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    reverse = axis[0] > axis[-1]
    ordered_axis = axis[::-1] if reverse else axis
    upper = np.searchsorted(ordered_axis, values)
    lower = np.clip(upper - 1, 0, len(axis) - 2)
    upper = lower + 1
    fraction = np.clip(
        (values - ordered_axis[lower])
        / (ordered_axis[upper] - ordered_axis[lower]),
        0.0,
        1.0,
    )
    if reverse:
        return len(axis) - 1 - upper, len(axis) - 1 - lower, fraction
    return lower, upper, fraction


def _sample_elevation(
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    x_values: np.ndarray,
    y_values: np.ndarray,
) -> np.ndarray:
    x0, x1, fx = _axis_brackets(x_axis, x_values)
    y0, y1, fy = _axis_brackets(y_axis, y_values)
    return (
        elevation[y0, x0] * (1.0 - fx) * (1.0 - fy)
        + elevation[y0, x1] * fx * (1.0 - fy)
        + elevation[y1, x0] * (1.0 - fx) * fy
        + elevation[y1, x1] * fx * fy
    )


def _safe_viewpoint_height(
    elevation: np.ndarray,
    x_axis: np.ndarray,
    y_axis: np.ndarray,
    spacing_m: float,
    requested_height_m: float,
) -> float:
    center = float(
        _sample_elevation(
            elevation, x_axis, y_axis, np.array([0.0]), np.array([0.0])
        )[0]
    )
    center_row = int(np.argmin(np.abs(y_axis)))
    center_column = int(np.argmin(np.abs(x_axis)))
    row_slice = slice(max(0, center_row - 2), min(len(y_axis), center_row + 3))
    column_slice = slice(
        max(0, center_column - 2), min(len(x_axis), center_column + 3)
    )
    nearby = elevation[row_slice, column_slice]
    nearby = nearby[np.isfinite(nearby)]
    local_peak = float(np.max(nearby)) if nearby.size else center
    clearance = max(15.0, float(spacing_m) * 0.4)
    return max(float(requested_height_m), local_peak - center + clearance)


def render_surface_view(
    grid: TerrainGrid,
    width: int,
    height: int,
    *,
    eye_height_m: float = 1.7,
    heading_deg: float = 0.0,
    solar_azimuth_deg: float = 135.0,
    solar_elevation_deg: float = 10.0,
    sun_visible: bool | None = None,
    horizontal_fov_deg: float = 88.0,
    vertical_fov_deg: float = 38.0,
) -> np.ndarray:
    """Render a grayscale lunar surface perspective from a local height grid."""
    width = max(160, min(int(width), 960))
    height = max(100, min(int(height), 540))
    if grid.z.ndim != 2 or grid.z.shape[0] < 2 or grid.z.shape[1] < 2:
        raise ValueError("Surface view needs a two-dimensional elevation grid.")

    x_axis = grid.x[0, :]
    y_axis = grid.y[:, 0]
    x_steps = np.diff(x_axis)
    y_steps = np.diff(y_axis)
    if not (
        np.all(x_steps > 0) or np.all(x_steps < 0)
    ) or not (
        np.all(y_steps > 0) or np.all(y_steps < 0)
    ):
        raise ValueError("Surface view needs monotonic terrain grid axes.")
    elevation = np.array(grid.z, dtype=np.float32, copy=True)
    elevation = np.nan_to_num(
        elevation, nan=float(np.nanmedian(elevation[np.isfinite(elevation)]))
        if np.isfinite(elevation).any() else 0.0,
    )
    center_elevation = float(
        _sample_elevation(
            elevation, x_axis, y_axis, np.array([0.0]), np.array([0.0])
        )[0]
    )
    viewpoint_height = _safe_viewpoint_height(
        elevation,
        x_axis,
        y_axis,
        grid.spacing_m,
        eye_height_m,
    )
    elevation -= center_elevation

    rows = np.arange(height, dtype=np.float32)
    ray_elevation = np.radians(
        ((height * 0.5 - rows) / height) * vertical_fov_deg
    )
    ray_slope = np.tan(ray_elevation)
    columns = np.arange(width, dtype=np.float32)
    ray_azimuth = np.radians(
        heading_deg + ((columns + 0.5) / width - 0.5) * horizontal_fov_deg
    )

    sky = np.zeros((height, width, 3), dtype=np.uint8)
    sky_top = np.array([2.0, 3.0, 7.0])
    sky_horizon = np.array([18.0, 19.0, 22.0])
    sky_fraction = np.clip(rows / max(height * 0.68, 1.0), 0.0, 1.0)
    sky[:, :, :] = (
        sky_top[None, None, :] * (1.0 - sky_fraction[:, None, None])
        + sky_horizon[None, None, :] * sky_fraction[:, None, None]
    ).astype(np.uint8)
    rng = np.random.default_rng(41)
    star_count = max(25, width * height // 4200)
    star_x = rng.integers(0, width, size=star_count)
    star_y = rng.integers(0, max(1, int(height * 0.58)), size=star_count)
    star_value = rng.integers(75, 190, size=star_count, dtype=np.uint8)
    sky[star_y, star_x] = np.stack(
        (star_value, star_value, np.minimum(star_value + 18, 220)), axis=1
    )

    image = sky
    hit_mask = np.zeros((height, width), dtype=bool)
    hit_grid_rows = np.zeros((height, width), dtype=np.intp)
    hit_grid_cols = np.zeros((height, width), dtype=np.intp)
    extent = max(
        float(np.nanmax(np.abs(grid.x))),
        float(np.nanmax(np.abs(grid.y))),
        float(grid.spacing_m) * 4.0,
    )
    max_distance = extent * 1.4
    steps = min(260, max(64, int(max_distance / max(grid.spacing_m, 1.0))))
    start_distance = max(float(grid.spacing_m) * 0.5, 1.0)
    distances = np.linspace(start_distance, max_distance, steps)
    unresolved = np.ones((height, width), dtype=bool)
    sampled_columns = np.sin(ray_azimuth)
    sampled_rows_direction = np.cos(ray_azimuth)
    x_margin = max(float(grid.spacing_m) * 1.8, 1.0)
    y_margin = x_margin
    for distance in distances:
        sample_x = distance * sampled_columns
        sample_y = distance * sampled_rows_direction
        valid_columns = (
            (sample_x >= min(x_axis[0], x_axis[-1]) - x_margin)
            & (sample_x <= max(x_axis[0], x_axis[-1]) + x_margin)
            & (sample_y >= min(y_axis[0], y_axis[-1]) - y_margin)
            & (sample_y <= max(y_axis[0], y_axis[-1]) + y_margin)
        )
        sampled_ground = _sample_elevation(
            elevation, x_axis, y_axis, sample_x, sample_y
        )
        newly_hit = (
            unresolved
            & (viewpoint_height + ray_slope[:, None] * distance <= sampled_ground[None, :])
            & valid_columns[None, :]
        )
        if newly_hit.any():
            hit_rows, hit_columns = np.nonzero(newly_hit)
            hit_mask[hit_rows, hit_columns] = True
            grid_x0, grid_x1, grid_fx = _axis_brackets(x_axis, sample_x)
            grid_y0, grid_y1, grid_fy = _axis_brackets(y_axis, sample_y)
            hit_grid_rows[hit_rows, hit_columns] = np.where(
                grid_fy[hit_columns] < 0.5,
                grid_y0[hit_columns],
                grid_y1[hit_columns],
            )
            hit_grid_cols[hit_rows, hit_columns] = np.where(
                grid_fx[hit_columns] < 0.5,
                grid_x0[hit_columns],
                grid_x1[hit_columns],
            )
            unresolved[newly_hit] = False
        if not unresolved.any():
            break

    if hit_mask.any():
        hit_rows_array, hit_cols_array = np.nonzero(hit_mask)
        sampled_rows = hit_grid_rows[hit_rows_array, hit_cols_array]
        sampled_cols = hit_grid_cols[hit_rows_array, hit_cols_array]

        spacing_y = float(np.median(np.diff(y_axis)))
        spacing_x = float(np.median(np.diff(x_axis)))
        if abs(spacing_y) < 1e-9 or abs(spacing_x) < 1e-9:
            raise ValueError("Surface view needs non-zero terrain grid spacing.")
        slope_y, slope_x = np.gradient(elevation, spacing_y, spacing_x)
        sun_azimuth = math.radians(solar_azimuth_deg)
        sun_elevation = math.radians(max(-5.0, min(90.0, solar_elevation_deg)))
        normal_x = -slope_x[sampled_rows, sampled_cols]
        normal_y = -slope_y[sampled_rows, sampled_cols]
        normal_z = np.ones_like(normal_x)
        normal_length = np.sqrt(normal_x**2 + normal_y**2 + normal_z**2)
        incidence = (
            normal_x * math.sin(sun_azimuth) * math.cos(sun_elevation)
            + normal_y * math.cos(sun_azimuth) * math.cos(sun_elevation)
            + normal_z * math.sin(sun_elevation)
        ) / normal_length
        direct_sun_visible = (
            solar_elevation_deg > 0.0 if sun_visible is None else sun_visible
        )
        if direct_sun_visible:
            ambient = 0.16
            illumination = ambient + 0.84 * np.clip(incidence, 0.0, 1.0)
        else:
            illumination = np.full_like(incidence, 0.035)
        terrain_albedo = 0.66 + np.clip(
            elevation[sampled_rows, sampled_cols] / 4000.0, -0.08, 0.08
        )
        texture = np.random.default_rng(7).normal(0.0, 3.0, len(hit_rows_array))
        gray = np.clip(
            (illumination * terrain_albedo * 255.0) + texture, 0, 220
        ).astype(np.uint8)
        image[hit_rows_array, hit_cols_array] = gray[:, None]

    return image
