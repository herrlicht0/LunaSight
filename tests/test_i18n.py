import unittest

from lunasight.i18n import source_text, translate


class LocalizationTests(unittest.TestCase):
    def test_translates_ui_labels_and_restores_english(self):
        turkish = translate("Choose a place", "Turkish")

        self.assertEqual(turkish, "Konum seç")
        self.assertEqual(source_text(turkish), "Choose a place")
        self.assertEqual(translate(turkish, "English"), "Choose a place")

    def test_translates_dynamic_text_and_preserves_values(self):
        message = translate("Scenario list saved to:\n{path}", "Turkish")

        self.assertEqual(message.format(path="/tmp/scenarios.csv"),
                         "Konum listesi şuraya kaydedildi:\n/tmp/scenarios.csv")

    def test_localizes_compact_site_controls(self):
        self.assertEqual(translate("Global map · 4 MB", "Turkish"),
                         "Küresel harita · 4 MB")
        self.assertEqual(source_text("Güney kutbu"), "South pole")

    def test_translates_dynamic_analysis_fragments(self):
        phrase = "Over the next 24 hours, sunlight is available for about"
        radio_phrase = "Over the next 24 hours: sunlight is available for about"

        self.assertEqual(translate(phrase, "Turkish"),
                         "Sonraki 24 saatte Güneş ışığı yaklaşık")
        self.assertEqual(source_text(translate(phrase, "Turkish")), phrase)
        self.assertEqual(source_text(translate(radio_phrase, "Turkish")), radio_phrase)

    def test_translates_globe_interaction_instructions(self):
        instruction = (
            "Drag to rotate; click to select. Use the six views to explore the near side, "
            "far side, east, west and both poles."
        )

        self.assertIn("sürükleyin", translate(instruction, "Turkish"))

    def test_translates_surface_view_accuracy_note(self):
        note = (
            "Terrain: illustrative relief only (not NASA data). "
            "Perspective preview, not a calibrated camera image."
        )

        translated = translate(note, "Turkish")

        self.assertIn("Perspektif önizlemesidir", translated)
        self.assertIn("kalibre edilmiş kamera görüntüsü değildir", translated)

    def test_translates_site_specific_terrain_label(self):
        translated = translate(
            "Terrain: site-specific illustrative relief only (not NASA data).",
            "Turkish",
        )

        self.assertIn("konuma özel", translated)
        self.assertIn("NASA verisi değildir", translated)


if __name__ == "__main__":
    unittest.main()
