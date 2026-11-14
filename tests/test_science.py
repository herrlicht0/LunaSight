import math
import unittest

from lunasight.science import (
    C_M_S,
    DSN_PROFILES,
    calculate_rf_link,
    estimate_solar_illuminance_lux,
    estimate_solar_irradiance_w_m2,
    free_space_path_loss_db,
    preliminary_site_assessment,
)
from lunasight.terrain import (latlon_to_polar_xy, polar_xy_to_latlon, orthographic_globe_click_to_latlon)
from lunasight.reporting import build_session_report


class RadioAndPhotometryTests(unittest.TestCase):
    def test_profile_wavelength_matches_frequency(self):
        profile = DSN_PROFILES["S_34M_20KW"]
        self.assertAlmostEqual(profile.wavelength_m, C_M_S / 2.0675e9, places=12)
        self.assertAlmostEqual(profile.wavelength_m * 100, 14.50, delta=0.03)


    def test_lunar_profiles_use_near_earth_bands(self):
        s_profile = DSN_PROFILES["S_34M_20KW"]
        x_profile = DSN_PROFILES["X_34M_20KW"]
        self.assertEqual(s_profile.uplink_range_mhz, "2025–2110 MHz (near-Earth lunar uplink)")
        self.assertEqual(x_profile.uplink_range_mhz, "7190–7235 MHz (near-Earth lunar uplink)")
        self.assertAlmostEqual(s_profile.frequency_hz, 2.0675e9)
        self.assertAlmostEqual(x_profile.frequency_hz, 7.2125e9)

    def test_higher_frequency_has_higher_fspl_at_same_range(self):
        distance_km = 384_400.0
        s_loss = free_space_path_loss_db(2.0675e9, distance_km)
        x_loss = free_space_path_loss_db(7.2125e9, distance_km)
        k_loss = free_space_path_loss_db(22.85e9, distance_km)
        self.assertLess(s_loss, x_loss)
        self.assertLess(x_loss, k_loss)

    def test_rf_reference_and_terrain_line_of_sight(self):
        profile = DSN_PROFILES["S_34M_20KW"]
        visible = calculate_rf_link(profile, 5.0, 384_400.0, 0.0, 2.0, 2.0)
        blocked = calculate_rf_link(profile, 1.0, 384_400.0, 0.0, 2.0, 2.0)
        self.assertTrue(visible.line_of_sight)
        self.assertFalse(blocked.line_of_sight)
        # Power is retained as an explicitly theoretical, unobstructed reference.
        self.assertAlmostEqual(visible.received_power_dbm_if_los, blocked.received_power_dbm_if_los)

    def test_lux_and_irradiance_use_direct_sun_and_horizon_gate(self):
        self.assertAlmostEqual(estimate_solar_illuminance_lux(30), 63_500, delta=1)
        self.assertEqual(estimate_solar_illuminance_lux(4, local_horizon_deg=5), 0)
        self.assertEqual(estimate_solar_irradiance_w_m2(-1), 0)
        self.assertAlmostEqual(estimate_solar_irradiance_w_m2(90), 1361.0, places=5)


    def test_lux_does_not_enter_rf_received_power_formula(self):
        profile = DSN_PROFILES["S_34M_20KW"]
        before = calculate_rf_link(profile, 10.0, 384_400.0, 0.0, 2.0, 0.0)
        # Illuminance is calculated independently; no lux value is accepted by the RF model.
        estimate_solar_illuminance_lux(0.0)
        after = calculate_rf_link(profile, 10.0, 384_400.0, 0.0, 2.0, 0.0)
        self.assertAlmostEqual(before.received_power_dbm_if_los, after.received_power_dbm_if_los)

    def test_positive_screen_requires_lola_coverage(self):
        args = (0.80, 0.60, 0.35)
        label_without_dem, _ = preliminary_site_assessment(*args, has_terrain_data=False)
        label_with_dem, _ = preliminary_site_assessment(*args, has_terrain_data=True)
        self.assertEqual(label_without_dem, "TRADE STUDY REQUIRED")
        self.assertEqual(label_with_dem, "GEOMETRICALLY PROMISING")

    def test_report_does_not_claim_los_without_ephemeris(self):
        report = build_session_report(None, None, DSN_PROFILES["S_34M_20KW"])
        self.assertIn("BİLİNMİYOR (JPL analizi yok)", report)
        self.assertIn("quantity 20", report)


class PolarCoordinateTests(unittest.TestCase):

    def test_orthographic_globe_click_maps_the_visible_south_pole(self):
        # With the locator camera at elevation -58°, the south pole projects to y=-cos(elevation).
        y = -math.cos(math.radians(-58.0))
        coordinate = orthographic_globe_click_to_latlon(0.0, y)
        self.assertIsNotNone(coordinate)
        lat, _lon = coordinate
        self.assertAlmostEqual(lat, -90.0, places=6)
        self.assertIsNone(orthographic_globe_click_to_latlon(1.1, 0.0))

    def test_south_polar_projection_round_trip(self):
        lat, lon = -89.25, 123.4
        x, y = latlon_to_polar_xy(lat, lon)
        out_lat, out_lon = polar_xy_to_latlon(x, y)
        self.assertAlmostEqual(out_lat, lat, places=8)
        self.assertAlmostEqual(out_lon, lon, places=8)


if __name__ == "__main__":
    unittest.main()
