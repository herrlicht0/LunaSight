import math
import unittest
from types import SimpleNamespace

import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import proj3d

from lunasight.advanced_ui import LunarSurfaceExplorer
from lunasight.terrain import TerrainGrid


class GlobeInteractionTests(unittest.TestCase):
    def test_chang_e_sites_are_not_in_quick_site_list(self):
        self.assertNotIn("Chang'e 4", LunarSurfaceExplorer.QUICK_SITES)
        self.assertNotIn("Chang'e 5", LunarSurfaceExplorer.QUICK_SITES)
        self.assertIn("Chandrayaan-3", LunarSurfaceExplorer.QUICK_SITES)

    def test_selected_nasa_trek_patch_is_used_for_radio_horizon(self):
        explorer = LunarSurfaceExplorer.__new__(LunarSurfaceExplorer)
        axis = np.linspace(-1_000.0, 1_000.0, 21)
        x, y = np.meshgrid(axis, axis)
        elevation = np.zeros_like(x)
        elevation[5, 10] = 100.0
        explorer.selected_lat = -30.0
        explorer.selected_lon = 45.0
        explorer.selected_x = None
        explorer.selected_y = None
        explorer._terrain_site_index = None
        explorer.grid = TerrainGrid(x, y, np.zeros_like(x), "demo", 100.0)
        explorer.trek_site_grid = TerrainGrid(
            x, y, elevation, "NASA Moon Trek test patch", 100.0
        )
        explorer._trek_site_key = (round(-30.0, 6), round(45.0, 6))

        horizon = explorer.local_horizon(0.0, eye_height_m=1.7)

        self.assertGreater(horizon, 10.0)

    def setUp(self):
        self.explorer = LunarSurfaceExplorer.__new__(LunarSurfaceExplorer)
        self.explorer.map_ax = SimpleNamespace(view_init=self._set_view)
        self.explorer.map_canvas = SimpleNamespace(draw_idle=lambda: None)
        self.explorer._camera_azimuth = 0.0
        self.explorer._camera_elevation = 0.0
        self.explorer._drag_origin = None
        self.explorer._drag_view_origin = None
        self.explorer._drag_moved = False
        self.explorer._globe_zoom = 1.0
        self.explorer._map_marker = None
        self.explorer._draw_map = lambda: None
        self.selected_events = []
        self.explorer._select_globe_location = self.selected_events.append

    def _set_view(self, elev, azim):
        self.explorer._camera_elevation = elev
        self.explorer._camera_azimuth = azim

    def test_drag_rotates_globe_without_selecting_a_location(self):
        self.explorer._on_globe_press(SimpleNamespace(
            inaxes=self.explorer.map_ax, button=1, x=100, y=100))
        self.explorer._on_globe_motion(SimpleNamespace(x=150, y=120))
        self.explorer._on_globe_release(SimpleNamespace(x=150, y=120))

        self.assertAlmostEqual(self.explorer._camera_azimuth, 30.0)
        self.assertAlmostEqual(self.explorer._camera_elevation, -10.0)
        self.assertEqual(self.selected_events, [])

    def test_drag_crosses_the_south_pole_without_sticking(self):
        self.explorer._camera_elevation = -90.0
        self.explorer._on_globe_press(SimpleNamespace(
            inaxes=self.explorer.map_ax, button=1, x=100, y=100))
        self.explorer._on_globe_motion(SimpleNamespace(x=100, y=120))
        self.explorer._on_globe_release(SimpleNamespace(x=100, y=120))

        self.assertAlmostEqual(self.explorer._camera_elevation, -80.0)
        self.assertAlmostEqual(self.explorer._camera_azimuth, 180.0)
        self.assertEqual(self.selected_events, [])

    def test_short_click_selects_and_zoom_is_bounded(self):
        click = SimpleNamespace(inaxes=self.explorer.map_ax, button=1, x=100, y=100)
        self.explorer._on_globe_press(click)
        self.explorer._on_globe_release(click)
        self.assertEqual(self.selected_events, [click])

        self.explorer._zoom_globe(10.0)
        self.assertEqual(self.explorer._globe_zoom, 2.0)
        self.explorer._zoom_globe(0.01)
        self.assertEqual(self.explorer._globe_zoom, 0.7)

    def test_globe_selection_uses_the_projected_disk_and_accepts_canvas_release(self):
        figure = Figure(figsize=(4.0, 4.0), dpi=100)
        canvas = FigureCanvasAgg(figure)
        axes = figure.add_subplot(111, projection="3d")
        axes.set_proj_type("ortho")
        axes.set_box_aspect((1, 1, 1))
        axes.set_xlim(-1.16, 1.16)
        axes.set_ylim(-1.16, 1.16)
        axes.set_zlim(-1.16, 1.16)
        axes.view_init(elev=0.0, azim=0.0)
        canvas.draw()
        self.explorer.map_ax = axes
        selected = []
        self.explorer._select_coordinate = (
            lambda *coordinate, **_kwargs: selected.append(coordinate)
        )
        latitude, longitude = 20.0, 0.0
        lat_radians, lon_radians = math.radians(latitude), math.radians(longitude)
        world = (
            math.cos(lat_radians) * math.cos(lon_radians),
            math.cos(lat_radians) * math.sin(lon_radians),
            math.sin(lat_radians),
        )
        projected = proj3d.proj_transform(*world, axes.get_proj())[:2]
        pixel = axes.transData.transform(projected)
        click = SimpleNamespace(inaxes=None, x=pixel[0], y=pixel[1])

        LunarSurfaceExplorer._select_globe_location(self.explorer, click)

        self.assertEqual(len(selected), 1)
        self.assertAlmostEqual(selected[0][0], latitude, places=5)
        self.assertAlmostEqual(selected[0][1], longitude, places=5)

    def test_click_outside_globe_disk_does_not_select_a_site(self):
        figure = Figure(figsize=(4.0, 4.0), dpi=100)
        canvas = FigureCanvasAgg(figure)
        axes = figure.add_subplot(111, projection="3d")
        axes.set_proj_type("ortho")
        axes.set_box_aspect((1, 1, 1))
        axes.set_xlim(-1.16, 1.16)
        axes.set_ylim(-1.16, 1.16)
        axes.set_zlim(-1.16, 1.16)
        axes.view_init(elev=0.0, azim=0.0)
        canvas.draw()
        self.explorer.map_ax = axes
        selected = []
        self.explorer._select_coordinate = (
            lambda *coordinate, **_kwargs: selected.append(coordinate)
        )
        pixel = axes.transData.transform((0.8, 0.8))

        LunarSurfaceExplorer._select_globe_location(
            self.explorer,
            SimpleNamespace(inaxes=axes, x=pixel[0], y=pixel[1])
        )

        self.assertEqual(selected, [])

    def test_selected_site_indicator_moves_to_limb_on_far_side(self):
        figure = Figure(figsize=(4.0, 4.0), dpi=100)
        canvas = FigureCanvasAgg(figure)
        axes = figure.add_subplot(111, projection="3d")
        axes.set_proj_type("ortho")
        axes.set_box_aspect((1, 1, 1))
        axes.set_xlim(-1.16, 1.16)
        axes.set_ylim(-1.16, 1.16)
        axes.set_zlim(-1.16, 1.16)
        axes.view_init(elev=0.0, azim=0.0)
        canvas.draw()
        self.explorer.map_ax = axes
        self.explorer._map_marker = axes.text2D(
            0.5, 0.5, r"$\star$", transform=axes.transAxes
        )

        LunarSurfaceExplorer._update_site_marker(self.explorer, 1.003, 0.0, 0.0)
        front_position = self.explorer._map_marker.get_position()
        self.assertTrue(self.explorer._map_marker_is_visible)

        axes.view_init(elev=0.0, azim=180.0)
        LunarSurfaceExplorer._update_site_marker(self.explorer, 1.003, 0.0, 0.0)
        far_side_position = self.explorer._map_marker.get_position()

        self.assertFalse(self.explorer._map_marker_is_visible)
        self.assertEqual(self.explorer._map_marker.get_text(), "↑")
        self.assertTrue(all(0.0 <= value <= 1.0 for value in far_side_position))
        self.assertNotEqual(front_position, far_side_position)


if __name__ == "__main__":
    unittest.main()
