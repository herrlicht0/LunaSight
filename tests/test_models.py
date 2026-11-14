import unittest
from datetime import timezone

from lunasight.models import build_scenario


class BuildScenarioTests(unittest.TestCase):
    def test_valid_scenario_is_utc(self):
        scenario = build_scenario("Test site", "-89.5", "0", "2027-01-15", "12:00")
        self.assertEqual(scenario.latitude_deg, -89.5)
        self.assertEqual(scenario.longitude_deg, 0.0)
        self.assertEqual(scenario.date_time_utc.tzinfo, timezone.utc)

    def test_invalid_latitude_is_rejected(self):
        with self.assertRaises(ValueError):
            build_scenario("Test site", "91", "0", "2027-01-15", "12:00")

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            build_scenario("Test site", "-89", "0", "2027-02-30", "12:00")


if __name__ == "__main__":
    unittest.main()
