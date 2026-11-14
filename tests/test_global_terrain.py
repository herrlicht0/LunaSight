import unittest
from affine import Affine
import numpy as np

from lunasight.terrain import (
    GlobalLolaGrid,
    global_dem_height_at,
    global_dem_local_patch,
    global_dem_sample,
    latlon_to_global_grid_index,
    make_demo_site_patch,
    nasa_lola_surface_patch,
    orthographic_globe_click_to_latlon,
    resample_global_elevation,
    TerrainGrid,
)


class GlobalMoonSelectionTests(unittest.TestCase):
    def test_global_index_covers_both_poles_and_all_longitudes(self):
        shape = (181, 360)
        north = latlon_to_global_grid_index(90.0, 0.0, shape)
        south = latlon_to_global_grid_index(-90.0, 0.0, shape)
        self.assertEqual(north[0], 0)
        self.assertEqual(south[0], 180)
        self.assertGreaterEqual(latlon_to_global_grid_index(0.0, -180.0, shape)[1], 0)
        self.assertGreaterEqual(latlon_to_global_grid_index(0.0, 179.9, shape)[1], 0)

    def test_longitude_wrap_is_consistent(self):
        shape = (181, 360)
        self.assertEqual(
            latlon_to_global_grid_index(10, -180, shape),
            latlon_to_global_grid_index(10, 180, shape),
        )
        self.assertEqual(
            latlon_to_global_grid_index(10, 0, shape),
            latlon_to_global_grid_index(10, 360, shape),
        )

    def test_global_height_lookup(self):
        elevation = np.zeros((181, 360), dtype=np.float32)
        elevation[90, 180] = 1234.5
        grid = GlobalLolaGrid(elevation, 4, "test global grid")
        self.assertAlmostEqual(global_dem_height_at(grid, 0, 0), 1234.5)

    def test_global_dem_sampling_interpolates_bilinearly(self):
        elevation = np.arange(12, dtype=np.float32).reshape(3, 4)
        grid = GlobalLolaGrid(elevation, 4, "test global grid")

        self.assertAlmostEqual(global_dem_height_at(grid, 45.0, -135.0), 2.5)

    def test_global_dem_sampling_wraps_longitude_seam(self):
        elevation = np.tile(np.array([0.0, 0.0, 0.0, 100.0]), (3, 1))
        grid = GlobalLolaGrid(elevation, 4, "test global grid")
        longitudes = np.array([-180.0, 180.0, 181.0, -179.0])

        heights = global_dem_sample(grid, np.zeros(4), longitudes)

        self.assertAlmostEqual(heights[0], heights[1])
        self.assertAlmostEqual(heights[2], heights[3])

    def test_global_resampling_interpolates_and_wraps_longitude_seam(self):
        elevation = np.arange(12, dtype=np.float32).reshape(3, 4)
        grid = GlobalLolaGrid(elevation, 4, "test global grid")

        sampled = resample_global_elevation(grid, 5, 9)

        self.assertEqual(sampled.shape, (5, 9))
        self.assertAlmostEqual(sampled[1, 1], 2.5)
        np.testing.assert_allclose(sampled[:, 0], sampled[:, -1])

    def test_global_resampling_averages_downsampled_data(self):
        elevation = np.arange(32, dtype=np.float32).reshape(4, 8)
        grid = GlobalLolaGrid(elevation, 16, "test global grid")

        sampled = resample_global_elevation(grid, 3, 5)

        self.assertAlmostEqual(sampled[0, 1], 5.5)
        np.testing.assert_allclose(sampled[:, 0], sampled[:, -1])

    def test_global_resampling_skips_missing_source_values(self):
        elevation = np.ones((3, 4), dtype=np.float32)
        elevation[0, 0] = np.nan
        grid = GlobalLolaGrid(elevation, 4, "test global grid")

        sampled = resample_global_elevation(grid, 5, 9)

        self.assertTrue(np.isnan(sampled[0, 0]))
        self.assertAlmostEqual(sampled[1, 1], 1.0)
        self.assertTrue(np.isfinite(sampled[1:, 1:]).all())

    def test_global_dem_local_patch_is_centred_on_selected_point(self):
        elevation = np.arange(181 * 360, dtype=np.float32).reshape(181, 360)
        grid = GlobalLolaGrid(elevation, 4, "synthetic test grid")
        _east, _north, patch, centre = global_dem_local_patch(
            grid, 0.0, 0.0, half_width_m=10_000.0, size=9
        )
        self.assertEqual(patch.shape, (9, 9))
        self.assertEqual(patch[centre], global_dem_height_at(grid, 0.0, 0.0))

    def test_global_dem_local_patch_handles_both_poles(self):
        elevation = np.ones((181, 360), dtype=np.float32)
        grid = GlobalLolaGrid(elevation, 4, "synthetic test grid")
        for latitude in (-90.0, 90.0):
            east, north, patch, _centre = global_dem_local_patch(
                grid, latitude, 175.0, half_width_m=5_000.0, size=11
            )
            self.assertEqual(patch.shape, (11, 11))
            self.assertTrue(np.isfinite(patch).all())
            self.assertAlmostEqual(float(east[5, 5]), 0.0)
            self.assertAlmostEqual(float(north[5, 5]), 0.0)

    def test_lola_surface_patch_reprojects_to_a_regular_local_grid(self):
        rows, columns = np.mgrid[0:200, 0:200]
        raster_transform = Affine(0.1, 0.0, -10.0, 0.0, -0.1, 10.0)
        pixel_centers_x = -10.0 + (columns + 0.5) * 0.1
        pixel_centers_y = 10.0 - (rows + 0.5) * 0.1
        elevation = 2.0 * pixel_centers_x + 3.0 * pixel_centers_y

        class IdentityTransformer:
            @staticmethod
            def transform(longitude, latitude):
                return longitude, latitude

        source = TerrainGrid(
            np.zeros_like(elevation),
            np.zeros_like(elevation),
            elevation,
            "synthetic LOLA",
            1_000.0,
            IdentityTransformer(),
            raster_transform,
        )

        patch = nasa_lola_surface_patch(
            source, 0.0, 0.0, half_width_m=200_000.0, size=17
        )

        self.assertEqual(patch.x.shape, patch.z.shape)
        np.testing.assert_allclose(patch.x[0], patch.x[-1])
        np.testing.assert_allclose(patch.y[:, 0], patch.y[:, -1])
        self.assertAlmostEqual(float(patch.z[8, 8]), 0.0, places=5)

    def test_centre_click_selects_the_centre_of_each_globe_view(self):
        expected = [
            ((0.0, 0.0), (0.0, 0.0)),
            ((180.0, 0.0), (0.0, -180.0)),
            ((90.0, 0.0), (0.0, 90.0)),
            ((-90.0, 0.0), (0.0, -90.0)),
            ((0.0, 90.0), (90.0, 0.0)),
            ((0.0, -90.0), (-90.0, 0.0)),
        ]
        for (azimuth, elevation), (expected_lat, expected_lon) in expected:
            with self.subTest(view=(azimuth, elevation)):
                point = orthographic_globe_click_to_latlon(
                    0.0, 0.0, azimuth_deg=azimuth, elevation_deg=elevation
                )
                self.assertIsNotNone(point)
                self.assertAlmostEqual(point[0], expected_lat, places=6)
                self.assertAlmostEqual(point[1], expected_lon, places=6)

    def test_demo_surface_varies_by_site_but_is_repeatable(self):
        first = make_demo_site_patch(-89.5, 0.0)
        repeat = make_demo_site_patch(-89.5, 0.0)
        other_site = make_demo_site_patch(20.0, 30.0)

        np.testing.assert_array_equal(first.z, repeat.z)
        self.assertFalse(np.array_equal(first.z, other_site.z))


if __name__ == "__main__":
    unittest.main()
