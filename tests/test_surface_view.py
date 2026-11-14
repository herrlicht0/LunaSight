import unittest

import numpy as np

from lunasight.surface_view import _safe_viewpoint_height, render_surface_view
from lunasight.terrain import TerrainGrid


class SurfaceViewTests(unittest.TestCase):
    def setUp(self):
        axis = np.linspace(-1500.0, 1500.0, 81)
        x, y = np.meshgrid(axis, axis)
        z = (
            110.0 * np.exp(-((y + 500.0) / 280.0) ** 2)
            + 45.0 * np.sin(x / 180.0) * np.cos(y / 350.0)
        )
        self.grid = TerrainGrid(x, y, z, "synthetic test terrain", 37.5)

    def test_surface_view_returns_a_sky_and_terrain_rgb_image(self):
        image = render_surface_view(self.grid, 240, 120)

        self.assertEqual(image.shape, (120, 240, 3))
        self.assertEqual(image.dtype, np.uint8)
        self.assertLess(float(image[:20].mean()), float(image[-20:].mean()))
        self.assertGreater(np.unique(image.reshape(-1, 3), axis=0).shape[0], 20)

    def test_surface_view_is_deterministic_for_same_view(self):
        first = render_surface_view(self.grid, 200, 100, solar_azimuth_deg=75)
        second = render_surface_view(self.grid, 200, 100, solar_azimuth_deg=75)

        np.testing.assert_array_equal(first, second)

    def test_surface_horizon_is_continuous_across_center(self):
        image = render_surface_view(
            self.grid, 200, 100, solar_azimuth_deg=0, solar_elevation_deg=45
        )
        red_channel = image[:, :, 0]

        def horizon_row(column):
            for row in range(image.shape[0] - 2):
                if np.all(red_channel[row:row + 3, column] > 35):
                    return row
            return image.shape[0]

        center = image.shape[1] // 2
        self.assertLessEqual(
            abs(horizon_row(center - 1) - horizon_row(center)),
            4,
        )

    def test_surface_view_faces_north_by_default_and_can_face_south(self):
        north_view = render_surface_view(
            self.grid, 200, 100, solar_azimuth_deg=0, solar_elevation_deg=45
        )
        south_view = render_surface_view(
            self.grid, 200, 100, heading_deg=180,
            solar_azimuth_deg=0, solar_elevation_deg=45,
        )

        def horizon_row(image):
            for row in range(image.shape[0] - 2):
                if np.all(image[row:row + 3, 100, 0] > 35):
                    return row
            return image.shape[0]

        self.assertGreater(horizon_row(north_view) - horizon_row(south_view), 20)

    def test_surface_view_dims_when_the_sun_is_below_the_horizon(self):
        daylight = render_surface_view(
            self.grid, 200, 100, solar_azimuth_deg=0, solar_elevation_deg=45
        )
        nighttime = render_surface_view(
            self.grid, 200, 100, solar_azimuth_deg=0, solar_elevation_deg=-5,
            sun_visible=False,
        )

        self.assertGreater(float(daylight[55:].mean()), float(nighttime[55:].mean()) * 4)

    def test_surface_view_does_not_modify_source_elevations(self):
        source = self.grid.z.astype(np.float32)
        original = source.copy()
        grid = TerrainGrid(
            self.grid.x, self.grid.y, source, self.grid.source, self.grid.spacing_m
        )

        render_surface_view(grid, 200, 100)

        np.testing.assert_array_equal(source, original)

    def test_viewpoint_clears_nearby_higher_terrain(self):
        axis = np.arange(-2.0, 3.0)
        x, y = np.meshgrid(axis, axis)
        elevation = np.zeros((5, 5), dtype=float)
        elevation[1, 1] = 45.0
        height = _safe_viewpoint_height(elevation, axis, axis, 25.0, 1.7)

        self.assertGreaterEqual(height, 60.0)


if __name__ == "__main__":
    unittest.main()
