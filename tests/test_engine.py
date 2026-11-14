import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from lunasight.engine import (
    EphemerisError,
    _parse_horizons_csv,
    analyze,
)
from lunasight.models import build_scenario


class HorizonsCsvParserTests(unittest.TestCase):
    def test_parses_azimuth_elevation_rows(self):
        result = """\
Header text
$$SOE
2027-Jan-15 12:00, , , 123.450, -5.670
2027-Jan-15 12:30, , , 124.450, -4.670
$$EOE
Footer text
"""
        start = datetime(2027, 1, 15, 12, 0, tzinfo=timezone.utc)
        rows = _parse_horizons_csv(result, start)
        self.assertEqual(len(rows), 2)
        self.assertAlmostEqual(rows[0][1], 123.45)
        self.assertAlmostEqual(rows[0][2], -5.67)
        self.assertEqual(rows[1][0].minute, 30)

    def test_parses_jpl_observer_range_quantity_20(self):
        result = """\
Header text
$$SOE
2027-Jan-15 12:00, , , 123.450, -5.670, 0.002570, 0.00001
$$EOE
"""
        start = datetime(2027, 1, 15, 12, 0, tzinfo=timezone.utc)
        rows = _parse_horizons_csv(result, start)
        self.assertAlmostEqual(rows[0][3], 0.002570 * 149_597_870.7, places=2)

    def test_missing_table_raises_clear_error(self):
        with self.assertRaises(EphemerisError):
            _parse_horizons_csv("JPL API error", datetime.now(timezone.utc))


class AnalyzeTests(unittest.TestCase):
    def test_combines_sun_and_earth_visibility_series(self):
        scenario = build_scenario("Test Site", "-89.5", "0", "2027-01-15", "12:00")
        sun_text = """\
$$SOE
2027-Jan-15 12:00, , , 100.0, 10.0
2027-Jan-15 12:30, , , 101.0, -2.0
$$EOE
"""
        earth_text = """\
$$SOE
2027-Jan-15 12:00, , , 200.0, 20.0, 0.002570, 0.0
2027-Jan-15 12:30, , , 201.0, 5.0, 0.002571, 0.0
$$EOE
"""

        response_sun = Mock()
        response_sun.json.return_value = {"result": sun_text}
        response_earth = Mock()
        response_earth.json.return_value = {"result": earth_text}

        with patch("lunasight.engine.requests.get", side_effect=[response_sun, response_earth]):
            result = analyze(scenario)

        self.assertAlmostEqual(result.solar_elevation_deg, 10.0)
        self.assertAlmostEqual(result.earth_elevation_deg, 20.0)
        self.assertAlmostEqual(result.sunlight_fraction, 0.5)
        self.assertAlmostEqual(result.earth_visibility_fraction, 1.0)
        self.assertAlmostEqual(result.simultaneous_visibility_fraction, 0.5)
        self.assertTrue(result.earth_visibility)
        self.assertAlmostEqual(result.earth_range_km, 0.002570 * 149_597_870.7, places=2)
        self.assertEqual(len(result.samples), 2)


if __name__ == "__main__":
    unittest.main()
