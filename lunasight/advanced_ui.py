from __future__ import annotations

import math
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.colors import LightSource
from mpl_toolkits.mplot3d import proj3d

from .science import (
    DSN_PROFILES, MEAN_EARTH_MOON_RANGE_KM,
    calculate_rf_link, estimate_solar_illuminance_lux,
    estimate_solar_irradiance_w_m2, preliminary_site_assessment,
)
from .i18n import source_text, translate
from .surface_view import render_surface_view
from .terrain import (
    LOLA_SOURCE, TerrainGrid, latlon_to_polar_xy, polar_xy_to_latlon,
    make_demo_grid, make_demo_site_patch, load_nasa_lola_grid,
    load_nasa_5m_site_tile, LOLA_5M_SITES,
    local_patch, nearest_grid_index, terrain_horizon_at_azimuth,
    orthographic_globe_click_to_latlon, MOON_RADIUS_M,
    global_dem_local_patch, nasa_lola_surface_patch,
    load_nasa_trek_site_grid, resample_global_elevation,
)

BG = "#0b1220"
PANEL = "#121c2d"
PANEL2 = "#172338"
BORDER = "#26364d"
TEXT = "#edf3fb"
MUTED = "#adbed3"
ACCENT = "#69a9ff"
GREEN = "#55c69a"
AMBER = "#e8b45b"
RED = "#f07178"


class LunarSurfaceExplorer:
    """Whole-Moon site picker with NASA global LOLA elevation and a simple POV."""

    QUICK_SITES = {
        "Apollo 11": (0.6741, 23.4729),
        "Apollo 12": (-3.0124, -23.4216),
        "Apollo 14": (-3.6453, -17.4714),
        "Apollo 15": (26.1322, 3.6339),
        "Apollo 16": (-8.9734, 15.5011),
        "Apollo 17": (20.1908, 30.7717),
        "Luna 9": (7.08, -64.37),
        "Luna 16": (-0.5137, 56.3638),
        "Luna 20": (3.786, 56.624),
        "Luna 24": (12.714, 62.209),
        "Chandrayaan-3": (-69.373, 32.319),
        "South pole · Shackleton region": (-89.5, 0.0),
        "South pole · Malapert region": (-85.0, 0.0),
    }

    VIEW_PRESETS = {
        "Earth-facing side": (0.0, 0.0),
        "Far side": (180.0, 0.0),
        "East side": (90.0, 0.0),
        "West side": (-90.0, 0.0),
        "North pole": (0.0, 90.0),
        "South pole": (0.0, -90.0),
    }

    def __init__(self, parent: tk.Widget, app):
        self.parent = parent
        self.app = app
        self.grid: TerrainGrid = make_demo_grid()  # local south-polar detail only
        self.global_model = None
        self.trek_site_grid: TerrainGrid | None = None
        self._trek_site_key: tuple[float, float] | None = None
        self.scenario = None
        self.result = None
        self.selected_lat = -89.5
        self.selected_lon = 0.0
        self.selected_x, self.selected_y = latlon_to_polar_xy(self.selected_lat, self.selected_lon)
        self._camera_azimuth, self._camera_elevation = self.VIEW_PRESETS["South pole"]
        self._globe_zoom = 1.0
        self._drag_origin = None
        self._drag_view_origin = None
        self._drag_moved = False
        self._map_surface = None
        self._map_marker = None
        self._map_marker_is_visible = True
        self._map_surface_model = None
        self._map_view_radius = 1.16
        self._pov_photo = None
        self._pov_render_job = None
        self._loading = False
        self._terrain_site_index = None
        self._fraction_cache_key = None
        self._fraction_cache = None
        self._build()
        self._refresh_terrain_site_index()
        self._draw_map()
        self._draw_pov()

    def _build(self):
        shell = tk.Frame(self.parent, bg=BG)
        shell.pack(fill="both", expand=True)
        shell.grid_columnconfigure(0, weight=3)
        shell.grid_columnconfigure(1, weight=2)
        shell.grid_rowconfigure(0, weight=1)

        left = tk.Frame(shell, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(left, text="CHOOSE ANY PLACE ON THE MOON", bg=PANEL,
                 fg=TEXT, font=("Helvetica", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 3))
        tk.Label(left, text="Drag to rotate; click to select. Use the six views to explore the near side, far side, east, west and both poles.",
                 bg=PANEL, fg=MUTED, font=("Helvetica", 9), wraplength=730,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 9))

        toolbar = tk.Frame(left, bg=PANEL)
        toolbar.pack(fill="x", padx=14, pady=(0, 7))
        self.global_download_button = tk.Button(
            toolbar, text="Global map · 4 MB", command=self.load_global_base,
            bg=ACCENT, fg="#07111f", relief="flat", padx=10, pady=8,
            font=("Helvetica", 8, "bold"), cursor="hand2")
        self.global_download_button.pack(side="left")
        self.global_detail_button = tk.Button(
            toolbar, text="Detail · 63 MB", command=self.load_global_detail,
            bg=PANEL2, fg=TEXT, relief="flat", padx=9, pady=8,
            font=("Helvetica", 8, "bold"), cursor="hand2")
        self.global_detail_button.pack(side="left", padx=(7, 0))
        self.trek_button = tk.Button(
            toolbar,
            text=translate("NASA TREK terrain here", self.app.language),
            command=self.load_nasa_trek_terrain,
            bg=PANEL2,
            fg=TEXT,
            relief="flat",
            padx=9,
            pady=8,
            font=("Helvetica", 8, "bold"),
            cursor="hand2",
        )
        self.trek_button.pack(side="left", padx=(7, 0))

        navigation = tk.Frame(left, bg=PANEL)
        navigation.pack(fill="x", padx=14, pady=(0, 7))
        self.view_var = tk.StringVar(value="South pole")
        self.view_combo = ttk.Combobox(navigation, textvariable=self.view_var, state="readonly",
                                       values=list(self.VIEW_PRESETS), width=19)
        self.view_combo.pack(side="right")
        self.view_combo.bind("<<ComboboxSelected>>", self._preset_view_changed)
        self.zoom_controls = tk.Frame(navigation, bg=PANEL)
        self.zoom_controls.pack(side="left")
        tk.Button(
            self.zoom_controls, text="−", command=lambda: self._zoom_globe(1 / 1.2),
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=4,
            font=("Helvetica", 10, "bold"), cursor="hand2",
        ).pack(side="left")
        tk.Button(
            self.zoom_controls, text="+", command=lambda: self._zoom_globe(1.2),
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=4,
            font=("Helvetica", 10, "bold"), cursor="hand2",
        ).pack(side="left", padx=(4, 0))
        tk.Button(
            self.zoom_controls, text="Reset view", command=self._reset_view,
            bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=5,
            font=("Helvetica", 8, "bold"), cursor="hand2",
        ).pack(side="left", padx=(4, 0))

        shortcuts = tk.Frame(left, bg=PANEL)
        shortcuts.pack(fill="x", padx=14, pady=(0, 7))
        tk.Label(shortcuts, text="Quick site:", bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8)).pack(side="left")
        self.quick_site_var = tk.StringVar(value="South pole · Shackleton region")
        self.quick_site_combo = ttk.Combobox(
            shortcuts, textvariable=self.quick_site_var, state="readonly",
            values=list(self.QUICK_SITES), width=31)
        self.quick_site_combo.pack(side="left", padx=(7, 5))
        tk.Button(shortcuts, text="Go", command=self.select_quick_site,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=10, pady=5,
                  font=("Helvetica", 8, "bold")).pack(side="left")

        local_tools = tk.Frame(left, bg=PANEL)
        local_tools.pack(fill="x", padx=14, pady=(0, 6))
        self.load_lola_button = tk.Button(
            local_tools, text="South Pole · 80 m/px", command=self.load_lola,
            bg=PANEL2, fg=TEXT, relief="flat", padx=9, pady=6,
            font=("Helvetica", 8, "bold"), cursor="hand2")
        self.load_lola_button.pack(side="left")
        self.site_tile_var = tk.StringVar(value="04")
        self.site_tile_combo = ttk.Combobox(
            local_tools, textvariable=self.site_tile_var, state="readonly", width=4,
            values=list(LOLA_5M_SITES.keys()))
        self.site_tile_combo.pack(side="left", padx=(7, 3))
        tk.Button(local_tools, text="5 m site tile", command=self.load_local_lola_tile,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=6,
                  font=("Helvetica", 8, "bold")).pack(side="left")

        self.map_status = tk.StringVar(value="Schematic Moon globe · Load NASA data to show global elevation.")
        tk.Label(left, textvariable=self.map_status, bg=PANEL, fg=AMBER,
                 font=("Helvetica", 8), wraplength=760, justify="left").pack(anchor="w", padx=16, pady=(0, 4))

        self.map_figure = Figure(figsize=(7.4, 6.0), dpi=95, facecolor=PANEL)
        self.map_ax = self.map_figure.add_subplot(111, projection="3d")
        self.map_ax.set_proj_type("ortho")
        self.map_ax.mouse_init(rotate_btn=[], pan_btn=[], zoom_btn=[])
        self.map_canvas = FigureCanvasTkAgg(self.map_figure, master=left)
        self.map_canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.map_canvas.mpl_connect("button_press_event", self._on_globe_press)
        self.map_canvas.mpl_connect("motion_notify_event", self._on_globe_motion)
        self.map_canvas.mpl_connect("button_release_event", self._on_globe_release)
        self.map_canvas.mpl_connect("scroll_event", self._on_globe_scroll)
        tk.Label(left,
                 text="Every latitude and longitude can be selected by clicking the globe. The global map gives a useful overview; precise shadow checks need higher-detail terrain for that exact area.",
                 bg=PANEL, fg=MUTED, font=("Helvetica", 8), wraplength=740,
                 justify="left").pack(fill="x", padx=16, pady=(0, 12))

        right = tk.Frame(shell, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)
        info = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        info.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        tk.Label(info, text="YOUR SELECTED PLACE", bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 5))
        self.coordinate_label = tk.Label(info, text="89.50000° S · 0.00000° E", bg=PANEL,
                                         fg=TEXT, font=("Helvetica", 16, "bold"))
        self.coordinate_label.pack(anchor="w", padx=14)
        self.site_note = tk.Label(info, text="Click any visible part of the Moon to select a place.",
                                  bg=PANEL, fg=MUTED, font=("Helvetica", 8), wraplength=390,
                                  justify="left")
        self.site_note.pack(anchor="w", padx=14, pady=(4, 10))

        self.coord_details_open = tk.BooleanVar(value=False)
        self.coord_toggle = tk.Button(info, text="Show coordinates", command=self._toggle_coordinates,
                                      bg=PANEL2, fg=TEXT, relief="flat", padx=9, pady=6,
                                      font=("Helvetica", 8, "bold"))
        self.coord_toggle.pack(anchor="w", padx=14, pady=(0, 10))
        self.coord_frame = tk.Frame(info, bg=PANEL)
        self.coord_frame.pack(fill="x", padx=14, pady=(0, 10))
        self.coord_frame.pack_forget()
        self.lat_edit_var = tk.StringVar(value=f"{self.selected_lat:.5f}")
        self.lon_edit_var = tk.StringVar(value=f"{self.selected_lon:.5f}")
        row = tk.Frame(self.coord_frame, bg=PANEL)
        row.pack(fill="x")
        tk.Label(row, text="Latitude", bg=PANEL, fg=MUTED, font=("Helvetica", 8)).pack(side="left")
        tk.Entry(row, textvariable=self.lat_edit_var, width=10, bg=PANEL2, fg=TEXT,
                 insertbackground=TEXT, relief="flat").pack(side="left", padx=(5, 12))
        tk.Label(row, text="Longitude", bg=PANEL, fg=MUTED, font=("Helvetica", 8)).pack(side="left")
        tk.Entry(row, textvariable=self.lon_edit_var, width=10, bg=PANEL2, fg=TEXT,
                 insertbackground=TEXT, relief="flat").pack(side="left", padx=5)
        tk.Button(self.coord_frame, text="Use these coordinates", command=self.apply_manual_coordinates,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=8, pady=6,
                  font=("Helvetica", 8, "bold")).pack(anchor="e", pady=(7, 0))

        pov_panel = tk.Frame(right, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        pov_panel.grid(row=1, column=0, sticky="nsew")
        tk.Label(
            pov_panel,
            text=translate(
                "LUNAR SURFACE VIEW · LIFTED ABOVE TERRAIN", self.app.language
            ),
            bg=PANEL,
            fg=TEXT,
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 2))
        self.pov_note = tk.StringVar(value="Choose a location and run the Sun/Earth check to light this view.")
        tk.Label(pov_panel, textvariable=self.pov_note, bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8), wraplength=390, justify="left").pack(anchor="w", padx=14)
        self.pov_canvas = tk.Canvas(
            pov_panel, bg="#020307", highlightthickness=0, height=230
        )
        self.pov_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.pov_image_item = self.pov_canvas.create_image(0, 0, anchor="nw")
        self.pov_canvas.bind("<Configure>", self._schedule_pov_redraw, add="+")
        tk.Button(pov_panel, text="Refresh surface view", command=self._draw_pov,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=10, pady=7,
                  font=("Helvetica", 8, "bold")).pack(anchor="e", padx=12, pady=(0, 11))

    def _go_to_mission_check(self):
        self.app.notebook.select(self.app.dashboard_tab)
        self.app.date_entry.focus_set() if hasattr(self.app, "date_entry") else None

    def _suggest_view_for_coordinate(self, latitude_deg: float, longitude_deg: float):
        lat = math.radians(latitude_deg)
        lon = math.radians(longitude_deg)
        components = {
            "Earth-facing side": math.cos(lat) * math.cos(lon),
            "Far side": -math.cos(lat) * math.cos(lon),
            "East side": math.cos(lat) * math.sin(lon),
            "West side": -math.cos(lat) * math.sin(lon),
            "North pole": math.sin(lat),
            "South pole": -math.sin(lat),
        }
        preset = max(components, key=components.get)
        self.view_var.set(translate(preset, self.app.language))
        self._camera_azimuth, self._camera_elevation = self.VIEW_PRESETS[preset]

    def _toggle_coordinates(self):
        if self.coord_details_open.get():
            self.coord_frame.pack_forget()
            self.coord_details_open.set(False)
            self.coord_toggle.configure(text="Show coordinates")
        else:
            self.coord_frame.pack(fill="x", padx=14, pady=(0, 10))
            self.coord_details_open.set(True)
            self.coord_toggle.configure(text="Hide coordinates")

    def _current_view(self):
        return self._camera_azimuth, self._camera_elevation

    def _preset_view_changed(self, _event=None):
        preset = source_text(self.view_var.get())
        self._camera_azimuth, self._camera_elevation = self.VIEW_PRESETS[preset]
        self._globe_zoom = 1.0
        self._draw_map()

    def _reset_view(self):
        self.view_var.set(translate("South pole", self.app.language))
        self._camera_azimuth, self._camera_elevation = self.VIEW_PRESETS["South pole"]
        self._globe_zoom = 1.0
        self._draw_map()

    def _zoom_globe(self, factor: float):
        self._globe_zoom = min(2.0, max(0.7, self._globe_zoom * factor))
        self._draw_map()

    def _on_globe_scroll(self, event):
        if event.inaxes != self.map_ax:
            return
        if event.button == "up" or getattr(event, "step", 0) > 0:
            self._zoom_globe(1.2)
        elif event.button == "down" or getattr(event, "step", 0) < 0:
            self._zoom_globe(1 / 1.2)

    def _draw_map(self):
        rebuild_surface = (
            self._map_surface is None
            or self._map_surface_model is not self.global_model
        )
        if rebuild_surface:
            self.map_ax.clear()
            self.map_ax.set_facecolor(PANEL)
        azimuth, elevation = self._current_view()
        if rebuild_surface:
            # A regular whole-Moon mesh; global DEM is sampled only for display.
            lat_axis = np.linspace(90.0, -90.0, 81)
            lon_axis = np.linspace(-180.0, 180.0, 161)
            lon_grid, lat_grid = np.meshgrid(np.radians(lon_axis), np.radians(lat_axis))
            if self.global_model is not None:
                heights = resample_global_elevation(
                    self.global_model, len(lat_axis), len(lon_axis)
                )
                valid_heights = np.isfinite(heights)
                if valid_heights.any():
                    heights = np.nan_to_num(
                        heights, nan=float(np.median(heights[valid_heights]))
                    )
                else:
                    heights = np.zeros_like(heights)
                if self.global_model.color_rgb is not None:
                    from PIL import Image
                    texture = Image.fromarray(self.global_model.color_rgb).resize(
                            (len(lon_axis), len(lat_axis)), Image.Resampling.LANCZOS)
                    facecolors = np.asarray(texture, dtype=float) / 255.0
                    facecolors = LightSource(azdeg=315, altdeg=35).shade_rgb(
                        facecolors, heights, vert_exag=4.0, blend_mode="soft")
                else:
                    low, high = np.nanpercentile(heights, [2, 98])
                    facecolors = mpl.colormaps["gist_earth"](
                        np.clip((heights-low)/max(high-low, 1.0), 0, 1))
                self.map_status.set(
                    f"{self.global_model.source}. Whole globe is covered at locator resolution. "
                    f"{('NASA LROC WAC display texture loaded (polar fill is lower detail). ' if self.global_model.color_rgb is not None else 'Elevation shading is used; color texture unavailable. ')}"
                    "For a precise landing check, use a detailed local elevation model where one is available."
                )
            else:
                heights = np.zeros_like(lat_grid)
                facecolors = np.empty((*lat_grid.shape, 4), dtype=float)
                facecolors[:] = mpl.colors.to_rgba("#77869a")
                self.map_status.set("Schematic globe only. Choose ‘Load NASA whole-Moon map’ to download global LOLA elevation and LROC texture.")

            # The relief exaggeration is for visibility only; actual heights remain in the data model.
            radius = 1.0 + (heights / MOON_RADIUS_M) * 8.0
            cos_lat = np.cos(lat_grid)
            x = radius * cos_lat * np.cos(lon_grid)
            y = radius * cos_lat * np.sin(lon_grid)
            z = radius * np.sin(lat_grid)
            self._map_surface = self.map_ax.plot_surface(
                x, y, z, rstride=1, cstride=1, facecolors=facecolors,
                linewidth=0, antialiased=False, shade=False, alpha=1.0
            )
            self._map_surface_model = self.global_model

        sel_height = 0.0
        if self.global_model is not None:
            from .terrain import global_dem_height_at
            value = global_dem_height_at(self.global_model, self.selected_lat, self.selected_lon)
            if value is not None:
                sel_height = value
        sel_r = 1.0 + sel_height / MOON_RADIUS_M * 8.0 + 0.003
        lat_r, lon_r = math.radians(self.selected_lat), math.radians(self.selected_lon)
        sx = sel_r * math.cos(lat_r) * math.cos(lon_r)
        sy = sel_r * math.cos(lat_r) * math.sin(lon_r)
        sz = sel_r * math.sin(lat_r)
        if self._map_marker is None or rebuild_surface:
            self._map_marker = self.map_ax.text2D(
                0.5, 0.5, r"$\star$",
                transform=self.map_ax.transAxes,
                color="#ffd166", fontsize=17, ha="center", va="center",
                zorder=20, clip_on=False,
            )
        self.map_ax.set_box_aspect((1, 1, 1))
        self._map_view_radius = 1.16 / self._globe_zoom
        self.map_ax.set_xlim(-self._map_view_radius, self._map_view_radius)
        self.map_ax.set_ylim(-self._map_view_radius, self._map_view_radius)
        self.map_ax.set_zlim(-self._map_view_radius, self._map_view_radius)
        self.map_ax.view_init(elev=elevation, azim=azimuth)
        self.map_ax.set_axis_off()
        self.map_ax.set_title(
            f"{translate('FULL MOON', self.app.language)} · "
            f"{translate(source_text(self.view_var.get()), self.app.language)} · "
            f"{translate('DRAG TO ROTATE', self.app.language)} · "
            f"{translate('CLICK TO PICK', self.app.language)}",
            color=TEXT, fontsize=9, pad=10)
        if rebuild_surface:
            self.map_figure.tight_layout(pad=1.4)
        self._update_site_marker(sx, sy, sz)
        self.map_canvas.draw_idle()

    def _update_site_marker(self, x: float, y: float, z: float):
        if self._map_marker is None:
            return
        projection = self.map_ax.get_proj()
        center_projected = np.asarray(
            proj3d.proj_transform(0.0, 0.0, 0.0, projection)[:2]
        )
        center_pixel = self.map_ax.transData.transform(center_projected)
        site_projected = np.asarray(
            proj3d.proj_transform(x, y, z, projection)[:2]
        )
        site_pixel = self.map_ax.transData.transform(site_projected)
        radius_pixels = min(
            np.linalg.norm(
                self.map_ax.transData.transform(
                    proj3d.proj_transform(*self.map_ax._view_u, projection)[:2]
                ) - center_pixel
            ),
            np.linalg.norm(
                self.map_ax.transData.transform(
                    proj3d.proj_transform(*self.map_ax._view_v, projection)[:2]
                ) - center_pixel
            ),
        )
        site_direction = np.array([x, y, z], dtype=float)
        site_direction /= max(float(np.linalg.norm(site_direction)), 1e-12)
        self._map_marker_is_visible = float(
            np.dot(site_direction, self.map_ax._view_w)
        ) >= 0.0
        offset = site_pixel - center_pixel
        if self._map_marker_is_visible:
            marker_pixel = site_pixel
            self._map_marker.set_text(r"$\star$")
            self._map_marker.set_rotation(0)
        else:
            offset_length = float(np.linalg.norm(offset))
            if offset_length < 1e-6:
                offset = np.array([0.0, 1.0])
                offset_length = 1.0
            direction = offset / offset_length
            marker_pixel = center_pixel + direction * radius_pixels * 0.94
            self._map_marker.set_text("↑")
            self._map_marker.set_rotation(
                math.degrees(math.atan2(direction[1], direction[0])) - 90.0
            )
        axes_bounds = self.map_ax.get_window_extent()
        self._map_marker.set_position((
            (marker_pixel[0] - axes_bounds.x0) / axes_bounds.width,
            (marker_pixel[1] - axes_bounds.y0) / axes_bounds.height,
        ))

    def _on_globe_press(self, event):
        if event.inaxes != self.map_ax or event.button != 1 or event.x is None or event.y is None:
            return
        self._drag_origin = (event.x, event.y)
        self._drag_view_origin = self._current_view()
        self._drag_moved = False

    def _on_globe_motion(self, event):
        if self._drag_origin is None or event.x is None or event.y is None:
            return
        dx = event.x - self._drag_origin[0]
        dy = event.y - self._drag_origin[1]
        if math.hypot(dx, dy) < 5 and not self._drag_moved:
            return
        self._drag_moved = True
        origin_azimuth, origin_elevation = self._drag_view_origin
        self._camera_azimuth = origin_azimuth + dx * 0.6
        elevation = origin_elevation - dy * 0.5
        while elevation > 90.0 or elevation < -90.0:
            if elevation > 90.0:
                elevation = 180.0 - elevation
            else:
                elevation = -180.0 - elevation
            self._camera_azimuth += 180.0
        self._camera_elevation = elevation
        self.map_ax.view_init(elev=self._camera_elevation, azim=self._camera_azimuth)
        if self._map_marker is not None:
            marker_height = 0.0
            if self.global_model is not None:
                from .terrain import global_dem_height_at
                marker_height = global_dem_height_at(
                    self.global_model, self.selected_lat, self.selected_lon
                ) or 0.0
            marker_radius = 1.0 + marker_height / MOON_RADIUS_M * 8.0 + 0.003
            latitude = math.radians(self.selected_lat)
            longitude = math.radians(self.selected_lon)
            self._update_site_marker(
                marker_radius * math.cos(latitude) * math.cos(longitude),
                marker_radius * math.cos(latitude) * math.sin(longitude),
                marker_radius * math.sin(latitude),
            )
        self.map_canvas.draw_idle()

    def _on_globe_release(self, event):
        if self._drag_origin is None:
            return
        was_drag = self._drag_moved
        self._drag_origin = None
        self._drag_view_origin = None
        self._drag_moved = False
        if not was_drag:
            self._select_globe_location(event)

    def _select_globe_location(self, event):
        """Convert a short click on the visible globe disk to a lunar coordinate."""
        if event.x is None or event.y is None:
            return
        bbox = self.map_ax.get_window_extent()
        if not (bbox.x0 <= event.x <= bbox.x1 and bbox.y0 <= event.y <= bbox.y1):
            return
        azimuth, elevation = self._current_view()
        projected_click = self.map_ax.transData.inverted().transform(
            (event.x, event.y)
        )
        projection = self.map_ax.get_proj()
        center = np.asarray(proj3d.proj_transform(0.0, 0.0, 0.0, projection)[:2])
        azimuth_radians = math.radians(azimuth)
        elevation_radians = math.radians(elevation)
        right = np.array([
            -math.sin(azimuth_radians), math.cos(azimuth_radians), 0.0,
        ])
        up = np.array([
            -math.sin(elevation_radians) * math.cos(azimuth_radians),
            -math.sin(elevation_radians) * math.sin(azimuth_radians),
            math.cos(elevation_radians),
        ])
        right_projected = np.asarray(
            proj3d.proj_transform(*right, projection)[:2]
        ) - center
        up_projected = np.asarray(
            proj3d.proj_transform(*up, projection)[:2]
        ) - center
        screen_coordinates = np.linalg.solve(
            np.column_stack((right_projected, up_projected)),
            projected_click - center,
        )
        coordinate = orthographic_globe_click_to_latlon(
            float(screen_coordinates[0]),
            float(screen_coordinates[1]),
            azimuth_deg=azimuth,
            elevation_deg=elevation,
        )
        if coordinate is None:
            return
        self._select_coordinate(*coordinate, source="3D Moon globe")

    def _select_coordinate(self, latitude_deg: float, longitude_deg: float, source: str):
        if not -90.0 <= latitude_deg <= 90.0:
            return
        self.selected_lat = float(latitude_deg)
        self.selected_lon = ((float(longitude_deg) + 180.0) % 360.0) - 180.0
        if source != "3D Moon globe":
            self._suggest_view_for_coordinate(self.selected_lat, self.selected_lon)
        if -90.0 <= self.selected_lat <= -80.0:
            self.selected_x, self.selected_y = latlon_to_polar_xy(self.selected_lat, self.selected_lon)
        else:
            self.selected_x = self.selected_y = None
        self._refresh_terrain_site_index()
        lat, lon = self.selected_lat, self.selected_lon
        self.app.site_var.set(source)
        self.app.lat_var.set(f"{lat:.6f}")
        self.app.lon_var.set(f"{lon:.6f}")
        self.lat_edit_var.set(f"{lat:.6f}")
        self.lon_edit_var.set(f"{lon:.6f}")
        self.coordinate_label.configure(
            text=f"{abs(lat):.4f}° {'S' if lat < 0 else 'N'}  ·  {abs(lon):.4f}° {'W' if lon < 0 else 'E'}")
        if self.terrain_coverage_available:
            coverage = "Detailed NASA LOLA terrain is available at this point."
        else:
            coverage = "Global elevation is for browsing only; detailed local terrain has not been loaded for this point."
        self.site_note.configure(text=f"Selected from {source}. {coverage}")
        # A new point invalidates every previous-site result.
        self.result = None
        self.scenario = None
        self._fraction_cache_key = None
        self._fraction_cache = None
        if hasattr(self.app, "radio_panel"):
            self.app.radio_panel.result = None
            self.app.radio_panel.scenario = None
            self.app.radio_panel.refresh()
        if hasattr(self.app, "metric_values"):
            for value in self.app.metric_values:
                value.configure(text="—")
            for note in self.app.metric_notes:
                note.configure(text="Run the Sun and Earth check")
            self.app._draw_empty_sky()
            self.app.analysis_message.set("New Moon location selected. Choose ‘Check this place’ to calculate sunlight and Earth visibility.")
            self.app.status_label.configure(text="●  NEW PLACE SELECTED · CHECK NEEDED", fg=AMBER)
        self._draw_map()
        self._draw_pov()

    def select_quick_site(self):
        name = source_text(self.quick_site_var.get())
        coordinate = self.QUICK_SITES.get(name)
        if coordinate:
            self._select_coordinate(*coordinate, source=name)

    def apply_manual_coordinates(self):
        try:
            lat = float(self.lat_edit_var.get())
            lon = float(self.lon_edit_var.get())
            if not -90 <= lat <= 90 or not -180 <= lon <= 360:
                raise ValueError("Latitude must be −90 to +90 and longitude −180 to +360 degrees.")
        except ValueError as exc:
            messagebox.showerror(
                translate("Check coordinates", self.app.language),
                translate(str(exc), self.app.language), parent=self.app.root)
            return
        self._select_coordinate(lat, lon, source="Manual coordinate")

    def load_global_base(self):
        self._start_global_load(4)

    def load_global_detail(self):
        self._start_global_load(16)

    def _start_global_load(self, resolution_ppd: int):
        if self._loading:
            return
        self._loading = True
        self.global_download_button.configure(state="disabled", text="Loading map…")
        self.global_detail_button.configure(state="disabled")
        self.map_status.set("Downloading NASA global LOLA terrain and LROC color map. The files are cached so you only need to do this once.")
        def worker():
            try:
                from .terrain import load_nasa_global_moon_model
                model = load_nasa_global_moon_model(resolution_ppd, include_color=True)
            except Exception as exc:
                self.app.root.after(0, lambda err=str(exc): self._global_load_failed(err))
            else:
                self.app.root.after(0, lambda: self._global_loaded(model))
        threading.Thread(target=worker, name="lunasight-global-lola", daemon=True).start()

    def _global_load_failed(self, error):
        self._loading = False
        self.global_download_button.configure(state="normal", text="Retry map")
        self.global_detail_button.configure(state="normal")
        self.map_status.set("NASA global data was not loaded. The schematic globe remains available.")
        messagebox.showwarning(
            translate("NASA map unavailable", self.app.language),
            translate(error, self.app.language), parent=self.app.root)

    def _global_loaded(self, model):
        self.global_model = model
        self._loading = False
        self.global_download_button.configure(state="normal", text="Map ready")
        self.global_detail_button.configure(state="normal", text="Load 16 px/° detail")
        self._draw_map()
        self._draw_pov()

    def load_nasa_trek_terrain(self):
        if self._loading:
            return
        latitude = self.selected_lat
        longitude = self.selected_lon
        self._loading = True
        self.trek_button.configure(
            state="disabled",
            text=translate("Loading NASA terrain…", self.app.language),
        )
        self.map_status.set(
            translate(
                "Loading high-resolution NASA Moon Trek LOLA terrain for this place.",
                self.app.language,
            )
        )

        def worker():
            try:
                grid = load_nasa_trek_site_grid(latitude, longitude)
            except Exception as exc:
                self.app.root.after(
                    0,
                    lambda error=str(exc): self._trek_terrain_failed(error),
                )
            else:
                self.app.root.after(
                    0,
                    lambda: self._trek_terrain_loaded(
                        grid, latitude, longitude
                    ),
                )

        threading.Thread(
            target=worker, name="lunasight-nasa-trek-dem", daemon=True
        ).start()

    def _trek_terrain_failed(self, error: str):
        self._loading = False
        self.trek_button.configure(
            state="normal",
            text=translate("NASA TREK terrain here", self.app.language),
        )
        self.map_status.set(
            translate(
                "NASA Moon Trek terrain could not be loaded. Existing terrain remains available.",
                self.app.language,
            )
        )
        messagebox.showwarning(
            translate("NASA terrain unavailable", self.app.language),
            error,
            parent=self.app.root,
        )

    def _trek_terrain_loaded(
        self, grid: TerrainGrid, latitude: float, longitude: float
    ):
        self.trek_site_grid = grid
        self._trek_site_key = (round(latitude, 6), round(longitude, 6))
        self._loading = False
        self.trek_button.configure(
            state="normal",
            text=translate("NASA terrain ready", self.app.language),
        )
        if self._trek_site_key == (
            round(self.selected_lat, 6),
            round(self.selected_lon, 6),
        ):
            self.site_note.configure(
                text=f"{translate('NASA Moon Trek terrain loaded for this place.', self.app.language)} {grid.source}"
            )
            self._draw_pov()
        else:
            self.map_status.set(
                translate(
                    "NASA Moon Trek terrain loaded for the earlier selected place.",
                    self.app.language,
                )
            )

    def load_lola(self):
        if self._loading:
            return
        self._loading = True
        self.load_lola_button.configure(state="disabled", text="Loading terrain…")
        self.map_status.set(
            translate(
                "Opening NASA/GSFC high-resolution south-polar LOLA elevation data. Internet connection required.",
                self.app.language,
            )
        )
        def worker():
            try:
                grid = load_nasa_lola_grid(out_size=1200)
            except Exception as exc:
                self.app.root.after(0, lambda err=str(exc): self._lola_failed(err))
            else:
                self.app.root.after(0, lambda: self._lola_loaded(grid))
        threading.Thread(target=worker, name="lunasight-lola", daemon=True).start()

    def load_local_lola_tile(self):
        if self._loading:
            return
        self._loading = True
        site_id = self.site_tile_var.get()
        self.load_lola_button.configure(state="disabled", text=f"Loading tile {site_id}…")
        self.map_status.set(
            translate("Loading NASA high-detail local terrain for", self.app.language)
            + f" {LOLA_5M_SITES.get(site_id, site_id)}."
        )
        def worker():
            try:
                grid = load_nasa_5m_site_tile(site_id, out_size=900)
            except Exception as exc:
                self.app.root.after(0, lambda err=str(exc): self._lola_failed(err))
            else:
                self.app.root.after(0, lambda: self._lola_loaded(grid))
        threading.Thread(target=worker, name="lunasight-lola-local", daemon=True).start()

    def _lola_failed(self, error):
        self._loading = False
        self.load_lola_button.configure(state="normal", text="South Pole · 80 m/px")
        messagebox.showwarning(
            translate("Detailed terrain unavailable", self.app.language),
            translate(error, self.app.language), parent=self.app.root)

    def _lola_loaded(self, grid):
        self.grid = grid
        self._fraction_cache_key = None
        self._refresh_terrain_site_index()
        self._loading = False
        self.load_lola_button.configure(state="normal", text="Terrain ready")
        if self.terrain_coverage_available:
            self.site_note.configure(text=f"Detailed NASA terrain loaded for this point. {grid.source}")
        else:
            self.site_note.configure(text=f"NASA terrain tile loaded, but it does not cover the selected point ({self.selected_lat:.4f}°, {self.selected_lon:.4f}°). The app will not use it for this location.")
        self._draw_map()
        self._draw_pov()
        if hasattr(self.app, "radio_panel"):
            self.app.radio_panel.refresh()

    def set_analysis(self, scenario, result):
        self.scenario, self.result = scenario, result
        self.selected_lat = scenario.latitude_deg
        self.selected_lon = ((scenario.longitude_deg + 180.0) % 360.0) - 180.0
        if -90.0 <= self.selected_lat <= -80.0:
            self.selected_x, self.selected_y = latlon_to_polar_xy(self.selected_lat, self.selected_lon)
        else:
            self.selected_x = self.selected_y = None
        self._refresh_terrain_site_index()
        self.coordinate_label.configure(
            text=f"{abs(self.selected_lat):.4f}° {'S' if self.selected_lat < 0 else 'N'}  ·  "
                 f"{abs(self.selected_lon):.4f}° {'W' if self.selected_lon < 0 else 'E'}")
        self.lat_edit_var.set(f"{self.selected_lat:.6f}")
        self.lon_edit_var.set(f"{self.selected_lon:.6f}")
        self.site_note.configure(text=f"Analysis loaded for {scenario.site_name}. The map marker shows the analysed place.")
        self._draw_map()
        self._draw_pov()
        if hasattr(self.app, "radio_panel"):
            self.app.radio_panel.refresh()

    def _refresh_terrain_site_index(self):
        self._terrain_site_index = None
        if self.selected_x is None or self.selected_y is None:
            return
        self._fraction_cache_key = None
        if "NASA/GSFC" not in self.grid.source:
            return
        try:
            i, j = nearest_grid_index(self.grid, self.selected_x, self.selected_y)
            dx = float(self.grid.x[i, j]) - self.selected_x
            dy = float(self.grid.y[i, j]) - self.selected_y
            if math.hypot(dx, dy) <= max(250.0, self.grid.spacing_m * 2.5):
                self._terrain_site_index = (i, j)
        except Exception:
            self._terrain_site_index = None
        self._fraction_cache_key = None

    @property
    def terrain_coverage_available(self) -> bool:
        return self._terrain_site_index is not None and "NASA/GSFC" in self.grid.source

    def local_horizon(self, azimuth_deg: float, eye_height_m: float = 1.7) -> float:
        if not self.terrain_coverage_available:
            return 0.0
        try:
            return terrain_horizon_at_azimuth(
                self.grid, self.selected_x, self.selected_y, azimuth_deg,
                eye_height_m=eye_height_m, max_range_m=120_000.0,
                site_index=self._terrain_site_index,
            )
        except Exception:
            return 0.0

    def terrain_adjusted_fractions(self):
        if self.result is None:
            return None
        if not self.terrain_coverage_available:
            return (self.result.sunlight_fraction,
                    self.result.earth_visibility_fraction,
                    self.result.simultaneous_visibility_fraction)
        cache_key = (id(self.result), id(self.grid), round(self.selected_x, 1), round(self.selected_y, 1))
        if cache_key == self._fraction_cache_key and self._fraction_cache is not None:
            return self._fraction_cache
        sun_visible, earth_visible = [], []
        for sample in self.result.samples:
            sun_visible.append(sample.sun_elevation_deg > self.local_horizon(sample.sun_azimuth_deg))
            earth_visible.append(sample.earth_elevation_deg > self.local_horizon(sample.earth_azimuth_deg))
        count = max(1, len(sun_visible))
        values = (sum(sun_visible) / count, sum(earth_visible) / count,
                  sum(a and b for a, b in zip(sun_visible, earth_visible)) / count)
        self._fraction_cache_key, self._fraction_cache = cache_key, values
        return values

    def _schedule_pov_redraw(self, _event=None):
        if self._pov_render_job is not None:
            self.parent.after_cancel(self._pov_render_job)
        self._pov_render_job = self.parent.after(120, self._draw_pov)

    def _draw_pov(self):
        self._pov_render_job = None
        using_local_dem = False
        using_trek_dem = False
        using_global_dem = False
        terrain_grid = None
        if self.terrain_coverage_available:
            try:
                terrain_grid = nasa_lola_surface_patch(
                    self.grid,
                    self.selected_lat,
                    self.selected_lon,
                    half_width_m=5_000.0,
                    size=121,
                )
                using_local_dem = True
            except (RuntimeError, ValueError):
                terrain_grid = None

        site_key = (round(self.selected_lat, 6), round(self.selected_lon, 6))
        if (
            terrain_grid is None
            and self.trek_site_grid is not None
            and self._trek_site_key == site_key
        ):
            terrain_grid = self.trek_site_grid
            using_trek_dem = True

        if terrain_grid is None and self.global_model is not None:
            xx, yy, zz, _center = global_dem_local_patch(
                self.global_model,
                self.selected_lat,
                self.selected_lon,
                half_width_m=60_000.0,
                size=71,
            )
            sample_spacing = float(np.median(np.diff(xx[0, :])))
            terrain_grid = TerrainGrid(
                xx, yy, zz, "NASA global LOLA preview", sample_spacing
            )
            using_global_dem = True

        if terrain_grid is None:
            terrain_grid = make_demo_site_patch(
                self.selected_lat, self.selected_lon
            )
            terrain_label = "site-specific illustrative relief only (not NASA data)"
        elif using_local_dem:
            terrain_label = (
                f"detailed NASA LOLA local terrain · {self.grid.spacing_m:.0f} m grid"
            )
        elif using_trek_dem:
            terrain_label = terrain_grid.source
        else:
            terrain_label = (
                f"NASA global LOLA preview · {self.global_model.ppd} "
                "pixels/degree (coarse)"
            )

        terrain_grid.z = np.asarray(terrain_grid.z, dtype=float)
        finite = np.isfinite(terrain_grid.z)
        if not finite.any():
            terrain_grid.z = np.zeros_like(terrain_grid.z)
        elif not finite.all():
            terrain_grid.z = np.where(
                finite,
                terrain_grid.z,
                float(np.nanmedian(terrain_grid.z[finite])),
            )

        solar_azimuth = 135.0
        solar_elevation = 10.0
        lux = 0.0
        sun_visible = True
        earth_visible = True
        if self.result is not None:
            solar_azimuth = self.result.solar_azimuth_deg
            solar_elevation = self.result.solar_elevation_deg
            sun_visible = solar_elevation > self.local_horizon(
                solar_azimuth, eye_height_m=1.7
            )
            earth_visible = self.result.earth_elevation_deg > self.local_horizon(
                self.result.earth_azimuth_deg, eye_height_m=1.7
            )
            lux = estimate_solar_illuminance_lux(
                solar_elevation,
                self.local_horizon(solar_azimuth, eye_height_m=1.7),
            )

        width = self.pov_canvas.winfo_width()
        height = self.pov_canvas.winfo_height()
        if width <= 1:
            width = 560
        if height <= 1:
            height = 260
        camera_heading = solar_azimuth if self.result is not None else 0.0
        image_array = render_surface_view(
            terrain_grid, width, height,
            eye_height_m=1.7,
            heading_deg=camera_heading,
            solar_azimuth_deg=solar_azimuth,
            solar_elevation_deg=solar_elevation,
            sun_visible=sun_visible,
        )
        from PIL import Image, ImageDraw, ImageTk
        image = Image.fromarray(image_array, mode="RGB")
        draw = ImageDraw.Draw(image)
        if self.result is not None:
            horizontal_fov = 88.0
            vertical_fov = 38.0
            for label, azimuth, elevation, color, visible in [
                ("SUN" if self.app.language == "English" else "GÜNEŞ",
                 self.result.solar_azimuth_deg, self.result.solar_elevation_deg,
                 "#ffd36a", sun_visible),
                ("EARTH" if self.app.language == "English" else "DÜNYA",
                 self.result.earth_azimuth_deg, self.result.earth_elevation_deg,
                 "#91caff", earth_visible),
            ]:
                if not visible:
                    continue
                relative_azimuth = (
                    (azimuth - solar_azimuth + 180.0) % 360.0
                ) - 180.0
                if abs(relative_azimuth) > horizontal_fov / 2:
                    continue
                px = int(width * (0.5 + relative_azimuth / horizontal_fov))
                py = int(height * (0.5 - elevation / vertical_fov))
                if not 0 <= py < height:
                    continue
                draw.ellipse((px - 5, py - 5, px + 5, py + 5),
                             fill=color, outline="#ffffff", width=1)
                draw.text((px + 8, py - 7), f"{label} {elevation:+.1f}°",
                          fill=color, stroke_width=1, stroke_fill="#020307")

        self._pov_photo = ImageTk.PhotoImage(image)
        self.pov_canvas.itemconfigure(self.pov_image_item, image=self._pov_photo)
        self.pov_canvas.coords(self.pov_image_item, 0, 0)
        if self.result is not None:
            light_state = f"estimated direct surface light {lux:,.0f} lux" if lux > 0 else "no direct sunlight at this time"
            self.pov_note.set(
                f"{light_state}. Terrain: {terrain_label}. "
                + translate(
                    "Viewpoint lifted above nearby terrain for a clear view; perspective preview, not a calibrated camera image.",
                    self.app.language,
                )
            )
        else:
            self.pov_note.set(
                f"Terrain: {terrain_label}. "
                + translate(
                    "Viewpoint lifted above nearby terrain for a clear view.",
                    self.app.language,
                )
                + " "
                + translate("Run the Sun and Earth check", self.app.language)
                + "."
            )


class RadioLightingPanel:
    def __init__(self, parent: tk.Widget, app):
        self.parent = parent
        self.app = app
        self.scenario = None
        self.result = None
        self._build()
        self.refresh()

    def _build(self):
        shell = tk.Frame(self.parent, bg=BG)
        shell.pack(fill="both", expand=True, padx=2, pady=2)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_columnconfigure(1, weight=2)
        left = tk.Frame(shell, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = tk.Frame(shell, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        tk.Label(left, text="HOW WELL CAN THE LANDER CONTACT EARTH?", bg=PANEL,
                 fg=TEXT, font=("Helvetica", 11, "bold"), wraplength=340,
                 justify="left").pack(anchor="w", padx=16, pady=(15, 5))
        tk.Label(left, text="Choose an example ground-station radio profile. LunaSight estimates how much signal could reach a lander in clear space.",
                 bg=PANEL, fg=MUTED, font=("Helvetica", 8), wraplength=340,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 10))
        self.profile_labels = {profile.label: key for key, profile in DSN_PROFILES.items()}
        self.profile_var = tk.StringVar(value=DSN_PROFILES["S_34M_20KW"].label)
        tk.Label(left, text="RADIO EXAMPLE", bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", padx=16)
        self.profile_combo = ttk.Combobox(left, textvariable=self.profile_var, state="readonly",
                                          values=list(self.profile_labels.keys()))
        self.profile_combo.pack(fill="x", padx=16, pady=(5, 8))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        self.rx_gain_var = tk.StringVar(value="0")
        self.antenna_height_var = tk.StringVar(value="1.7")
        self.loss_var = tk.StringVar(value="2")
        self.range_var = tk.StringVar(value=str(int(MEAN_EARTH_MOON_RANGE_KM)))
        self.horizon_var = tk.StringVar(value="0")
        self.advanced_open = False
        self.advanced_toggle = tk.Button(
            left, text="Show technical settings", command=self._toggle_advanced,
            bg=PANEL2, fg=TEXT, relief="flat", padx=9, pady=6,
            font=("Helvetica", 8, "bold"))
        self.advanced_toggle.pack(fill="x", padx=16, pady=(0, 5))
        self.advanced_frame = tk.Frame(left, bg=PANEL)
        self._entry(self.advanced_frame, "Lander antenna gain (dBi)", self.rx_gain_var,
                    "0 dBi is a simple reference, not a specific lander antenna.")
        self._entry(self.advanced_frame, "Lander antenna height (m)", self.antenna_height_var,
                    "Used when checking whether terrain blocks the view of Earth.")
        self._entry(self.advanced_frame, "Other radio losses (dB)", self.loss_var,
                    "An adjustable placeholder for additional losses.")
        self._entry(self.advanced_frame, "Earth–Moon distance (km)", self.range_var,
                    "Filled from JPL when available; otherwise an average distance is used.")
        self._entry(self.advanced_frame, "Local horizon toward Earth (degrees)", self.horizon_var,
                    "Updated automatically when detailed local terrain covers the selected place.")

        buttons = tk.Frame(left, bg=PANEL)
        buttons.pack(fill="x", padx=16, pady=(8, 10))
        tk.Button(buttons, text="Update results", command=self.refresh,
                  bg=ACCENT, fg="#07111f", relief="flat", padx=12, pady=9,
                  font=("Helvetica", 9, "bold"), cursor="hand2").pack(fill="x")
        tk.Button(buttons, text="Save a simple report", command=self.export_report,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=12, pady=8,
                  font=("Helvetica", 8, "bold"), cursor="hand2").pack(fill="x", pady=(7, 0))

        self.profile_details = tk.StringVar()
        tk.Label(left, textvariable=self.profile_details, bg=PANEL2, fg=MUTED,
                 font=("Helvetica", 8), wraplength=330, justify="left",
                 padx=12, pady=10).pack(fill="x", padx=16, pady=(0, 14))

        tk.Label(right, text="RESULTS IN PLAIN LANGUAGE", bg=BG, fg=TEXT,
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(4, 10))
        self.metric_vars = {}
        metric_specs = [
            ("lux", "DIRECT SUNLIGHT ON THE GROUND", "— lux"),
            ("irr", "SUN ENERGY REACHING THE GROUND", "— W/m²"),
            ("power", "ESTIMATED RADIO POWER FROM EARTH", "— dBm"),
            ("fspl", "SIGNAL LOST OVER THE DISTANCE", "— dB"),
            ("los", "CAN THE LANDER SEE EARTH?", "Not checked"),
            ("assessment", "DOES THIS PLACE LOOK PROMISING?", "Not enough data"),
        ]
        cards = tk.Frame(right, bg=BG)
        cards.pack(fill="x")
        for i, (key, title, default) in enumerate(metric_specs):
            row, col = divmod(i, 2)
            cards.grid_columnconfigure(col, weight=1, uniform="radio_metric")
            card = tk.Frame(cards, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=row, column=col, sticky="nsew",
                      padx=(0, 7 if col == 0 else 0), pady=(0, 8))
            tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                     font=("Helvetica", 8, "bold"), wraplength=280,
                     justify="left").pack(anchor="w", padx=12, pady=(11, 4))
            value = tk.Label(card, text=default, bg=PANEL, fg=TEXT,
                             font=("Helvetica", 18, "bold"), wraplength=280,
                             justify="left")
            value.pack(anchor="w", padx=12, pady=(0, 11))
            self.metric_vars[key] = value

        self.explanation = tk.StringVar(value="Choose a Moon location, run the NASA/JPL check, and LunaSight will explain what the lighting and communication numbers mean.")
        note = tk.Frame(right, bg=PANEL2, highlightbackground=BORDER, highlightthickness=1)
        note.pack(fill="both", expand=True, pady=(2, 0))
        tk.Label(note, text="WHAT SHOULD I LOOK FOR?", bg=PANEL2, fg=ACCENT,
                 font=("Helvetica", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 5))
        tk.Label(note, textvariable=self.explanation, bg=PANEL2, fg=TEXT,
                 font=("Helvetica", 9), wraplength=760, justify="left").pack(fill="x", padx=14, pady=(0, 10))
        tk.Label(note,
                 text="Remember: sunlight and radio signals are different things. Bright ground does not make a radio signal stronger. The radio number is a simplified estimate from a published example; real mission hardware details are needed to know whether a data link will work.",
                 bg=PANEL2, fg=AMBER, font=("Helvetica", 8, "bold"), wraplength=760,
                 justify="left").pack(anchor="w", padx=14, pady=(0, 14))

    def _toggle_advanced(self):
        self.advanced_open = not self.advanced_open
        if self.advanced_open:
            self.advanced_frame.pack(fill="x", padx=0, pady=(0, 5))
            self.advanced_toggle.configure(text="Hide technical settings")
        else:
            self.advanced_frame.pack_forget()
            self.advanced_toggle.configure(text="Show technical settings")

    def _entry(self, parent, label, variable, hint):
        block = tk.Frame(parent, bg=PANEL)
        block.pack(fill="x", padx=16, pady=(0, 8))
        tk.Label(block, text=label.upper(), bg=PANEL, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w", pady=(0, 4))
        tk.Entry(block, textvariable=variable, bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Helvetica", 9)).pack(fill="x", ipady=7)
        tk.Label(block, text=hint, bg=PANEL, fg="#75869f", font=("Helvetica", 7),
                 wraplength=320, justify="left").pack(anchor="w", pady=(3, 0))

    def set_analysis(self, scenario, result):
        self.scenario, self.result = scenario, result
        if result.earth_range_km is not None:
            self.range_var.set(f"{result.earth_range_km:.1f}")
        self.refresh()

    def _selected_profile(self):
        key = self.profile_labels.get(source_text(self.profile_var.get()), "S_34M_20KW")
        return DSN_PROFILES[key]

    def refresh(self):
        profile = self._selected_profile()
        self.profile_details.set(
            f"Example ground-station radio: {profile.band} band.\n"
            f"Frequency: {profile.frequency_hz/1e6:.1f} MHz · wavelength: {profile.wavelength_m*100:.2f} cm.\n"
            "This is a published DSN example, not the confirmed radio on every lander."
        )
        if self.result is None:
            self._set_metric("lux", "— lux")
            self._set_metric("irr", "— W/m²")
            self._set_metric("power", "— dBm")
            self._set_metric("fspl", "— dB")
            self._set_metric("los", "Not checked")
            self._set_metric("assessment", "Needs data", AMBER)
            self.explanation.set(
                "Choose a place on the Moon, then press ‘Check this place with NASA/JPL data’. "
                "LunaSight will estimate sunlight, whether Earth is above the horizon, and a reference radio signal level."
            )
            self._last_rf = None
            self._last_lux = None
            self._last_irradiance = None
            self._last_fractions = None
            self._last_assessment = "INSUFFICIENT DATA"
            self._last_assessment_note = "Run the NASA/JPL check first."
            return

        explorer = getattr(self.app, "explorer_panel", None)
        terrain_available = bool(explorer and explorer.terrain_coverage_available)
        sun_horizon = 0.0
        earth_horizon = 0.0
        if explorer is not None:
            sun_horizon = explorer.local_horizon(self.result.solar_azimuth_deg, eye_height_m=1.7)
            try:
                antenna_height = max(0.0, float(self.antenna_height_var.get()))
            except ValueError:
                antenna_height = 1.7
            earth_horizon = explorer.local_horizon(
                self.result.earth_azimuth_deg, eye_height_m=antenna_height)

        lux = estimate_solar_illuminance_lux(
            self.result.solar_elevation_deg, sun_horizon)
        irradiance = estimate_solar_irradiance_w_m2(
            self.result.solar_elevation_deg, sun_horizon)
        try:
            rx_gain = float(self.rx_gain_var.get())
            other_losses = float(self.loss_var.get())
            earth_range = float(self.range_var.get())
            if earth_range <= 0:
                raise ValueError("Earth–Moon distance must be greater than zero.")
            if other_losses < 0:
                raise ValueError("Other radio losses cannot be negative.")
        except ValueError as exc:
            self.explanation.set(f"Check the technical settings: {exc}")
            return

        rf = calculate_rf_link(
            profile, self.result.earth_elevation_deg, range_km=earth_range,
            receiver_gain_dbi=rx_gain, other_losses_db=other_losses,
            local_horizon_deg=earth_horizon,
        )
        fractions = (self.result.sunlight_fraction,
                     self.result.earth_visibility_fraction,
                     self.result.simultaneous_visibility_fraction)
        if explorer is not None:
            adjusted = explorer.terrain_adjusted_fractions()
            if adjusted is not None:
                fractions = adjusted
        sunlight, earth_fraction, both = fractions
        assessment, assessment_note = preliminary_site_assessment(
            sunlight, earth_fraction, both, terrain_available)

        self._set_metric("lux", f"{lux:,.0f} lux", GREEN if lux > 0 else MUTED)
        self._set_metric("irr", f"{irradiance:,.1f} W/m²")
        self._set_metric("power", f"{rf.received_power_dbm_if_los:.1f} dBm",
                         GREEN if rf.line_of_sight else AMBER)
        self._set_metric("fspl", f"{rf.free_space_path_loss_db:.1f} dB")
        self._set_metric("los", "Yes — Earth above terrain" if rf.line_of_sight else "No — below / blocked",
                         GREEN if rf.line_of_sight else RED)
        assessment_labels = {
            "INSUFFICIENT DATA": ("Needs more data", AMBER),
            "HIGH CONSTRAINT": ("Major constraint", RED),
            "TRADE STUDY REQUIRED": ("Compare alternatives", AMBER),
            "GEOMETRICALLY PROMISING": ("Promising geometry", GREEN),
        }
        friendly_assessment, assessment_color = assessment_labels.get(
            assessment, (assessment.replace("_", " ").title(), AMBER))
        self._set_metric("assessment", friendly_assessment, assessment_color)
        self.explanation.set(
            f"Over the next 24 hours: sunlight is available for about {sunlight*100:.1f}% of the sampled time; "
            f"Earth is above the local/reference horizon for about {earth_fraction*100:.1f}%; "
            f"both are visible together for about {both*100:.1f}%.\n\n"
            f"Right now, the estimated direct light on a flat surface is {lux:,.0f} lux. "
            f"The example {profile.band}-band radio gives a theoretical clear-path received level of "
            f"{rf.received_power_dbm_if_los:.1f} dBm. "
            f"{'A geometric path to Earth is visible. ' if rf.line_of_sight else 'Earth is below the local terrain horizon, so there is no direct path now. '}"
            f"{('A detailed NASA LOLA local terrain mask was used. ' if terrain_available else 'Detailed terrain for this exact place is not loaded; visibility uses a simpler horizon. ')}"
            f"Assessment: {friendly_assessment}. {assessment_note}"
        )
        self._last_rf = rf
        self._last_lux = lux
        self._last_irradiance = irradiance
        self._last_fractions = fractions
        self._last_assessment = assessment
        self._last_assessment_note = assessment_note
        self._last_sun_horizon = sun_horizon
        self._last_earth_horizon = earth_horizon
        self._last_antenna_height = self.antenna_height_var.get()

    def _set_metric(self, key, value, color=TEXT):
        self.metric_vars[key].configure(text=value, fg=color)

    def export_report(self):
        path = filedialog.asksaveasfilename(
            parent=self.app.root, defaultextension=".md", initialfile="LunaSight_RF_Aydinlatma_Raporu.md",
            filetypes=[("Markdown report", "*.md"), ("Text file", "*.txt")],
        )
        if not path:
            return
        try:
            from pathlib import Path
            from .reporting import build_session_report
            profile = self._selected_profile()
            # Rebuild the exact assumptions/results shown in the panel for the exported report.
            content = build_session_report(
                self.scenario, self.result, profile,
                self.rx_gain_var.get(), self.loss_var.get(), self.range_var.get(),
                receiver_height_m=getattr(self, "_last_antenna_height", self.antenna_height_var.get()),
                lux=getattr(self, "_last_lux", None),
                irradiance=getattr(self, "_last_irradiance", None),
                rf=getattr(self, "_last_rf", None),
                sunlight_fraction=getattr(self, "_last_fractions", None)[0] if getattr(self, "_last_fractions", None) else None,
                earth_visibility_fraction=getattr(self, "_last_fractions", None)[1] if getattr(self, "_last_fractions", None) else None,
                simultaneous_fraction=getattr(self, "_last_fractions", None)[2] if getattr(self, "_last_fractions", None) else None,
                suitability=getattr(self, "_last_assessment", None),
                suitability_note=getattr(self, "_last_assessment_note", None),
                sun_horizon_deg=getattr(self, "_last_sun_horizon", None),
                earth_horizon_deg=getattr(self, "_last_earth_horizon", None),
                terrain_source=(getattr(self.app, "explorer_panel", None).grid.source
                                if getattr(self.app, "explorer_panel", None) is not None else "Not loaded"),
            )
            Path(path).write_text(content, encoding="utf-8")
        except Exception as exc:
            messagebox.showerror(
                translate("Report export failed", self.app.language),
                translate(str(exc), self.app.language), parent=self.app.root)
            return
        messagebox.showinfo(
            translate("Report exported", self.app.language),
            f"{translate('Saved report:', self.app.language)}\n{path}",
            parent=self.app.root)
