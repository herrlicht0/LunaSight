from __future__ import annotations

import csv
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .engine import AnalysisResult, EphemerisError, analyze
from .i18n import apply_language, source_text, translate
from .models import MissionScenario, build_scenario


BG = "#0b1220"
PANEL = "#121c2d"
PANEL_2 = "#172338"
BORDER = "#26364d"
TEXT = "#edf3fb"
MUTED = "#adbed3"
ACCENT = "#69a9ff"
GREEN = "#55c69a"
AMBER = "#e8b45b"


class LunaSightApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LunaSight | Explore the Moon")
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = min(1440, max(900, screen_width - 60))
        height = min(900, max(620, screen_height - 100))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(min(980, width), min(620, height))
        self.root.configure(bg=BG)
        self.language = "English"
        self.scenarios: list[MissionScenario] = []
        self.analysis_results: dict[tuple, AnalysisResult] = {}
        self._analysis_in_progress = False
        self._configure_style()
        self._build_shell()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "TNotebook", background=BG, borderwidth=0, tabmargins=(0, 0, 0, 0)
        )
        style.configure(
            "TNotebook.Tab", background=PANEL_2, foreground=MUTED,
            padding=(18, 11), borderwidth=0, font=("Helvetica", 10, "bold")
        )
        style.map(
            "TNotebook.Tab", background=[("selected", PANEL)],
            foreground=[("selected", TEXT)]
        )
        style.configure(
            "Treeview", background=PANEL, fieldbackground=PANEL,
            foreground=TEXT, rowheight=32, borderwidth=0,
            font=("Helvetica", 10)
        )
        style.configure(
            "Treeview.Heading", background=PANEL_2, foreground=MUTED,
            relief="flat", font=("Helvetica", 9, "bold")
        )
        style.map("Treeview", background=[("selected", "#24466b")])
        style.configure(
            "TCombobox", fieldbackground=PANEL_2, background=PANEL_2,
            foreground=TEXT, arrowcolor=TEXT, padding=7
        )

    def _build_shell(self) -> None:
        header = tk.Frame(self.root, bg=BG, padx=28, pady=18)
        header.pack(fill="x")

        brand = tk.Frame(header, bg=BG)
        brand.pack(side="left")
        tk.Label(
            brand, text="LUNASIGHT", bg=BG, fg=TEXT,
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w")
        tk.Label(
            brand, text="EXPLORE THE MOON · PLAN A MISSION", bg=BG, fg=MUTED,
            font=("Helvetica", 8, "bold")
        ).pack(anchor="w", pady=(2, 0))

        status = tk.Frame(header, bg=BG)
        status.pack(side="right", anchor="center")
        self.status_label = tk.Label(
            status, text="●  READY · INTERNET REQUIRED FOR LIVE NASA/JPL DATA", bg=BG,
            fg=GREEN, font=("Helvetica", 9, "bold")
        )
        self.status_label.pack(anchor="e")
        tk.Label(
            status, text="LunaSight Desktop v0.5.1", bg=BG,
            fg=MUTED, font=("Helvetica", 9)
        ).pack(anchor="e", pady=(4, 0))
        language_box = tk.Frame(header, bg=BG)
        language_box.pack(side="right", padx=(0, 20))
        tk.Label(language_box, text="Language", bg=BG, fg=MUTED,
                 font=("Helvetica", 8, "bold")).pack(anchor="w")
        self.language_var = tk.StringVar(value="English")
        self.language_combo = ttk.Combobox(
            language_box, textvariable=self.language_var, values=("English", "Turkish"),
            state="readonly", width=11
        )
        self.language_combo.pack(anchor="e", pady=(3, 0))
        self.language_combo.bind("<<ComboboxSelected>>", self._language_selected)

        separator = tk.Frame(self.root, bg=BORDER, height=1)
        separator.pack(fill="x")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=22, pady=(18, 10))

        self.dashboard_tab = tk.Frame(self.notebook, bg=BG)
        self.compare_tab = tk.Frame(self.notebook, bg=BG)
        self.data_tab = tk.Frame(self.notebook, bg=BG)
        self.explorer_tab = tk.Frame(self.notebook, bg=BG)
        self.radio_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.explorer_tab, text="  1 · CHOOSE A PLACE  ")
        self.notebook.add(self.dashboard_tab, text="  2 · DATE & SKY VIEW  ")
        self.notebook.add(self.radio_tab, text="  3 · SUNLIGHT & EARTH LINK  ")
        self.notebook.add(self.compare_tab, text="  4 · COMPARE PLACES  ")
        self.notebook.add(self.data_tab, text="  5 · DATA & SOURCES  ")

        self._build_dashboard()
        self._build_compare()
        self._build_data_tab()
        from .advanced_ui import LunarSurfaceExplorer, RadioLightingPanel
        self.explorer_panel = LunarSurfaceExplorer(self.explorer_tab, self)
        self.radio_panel = RadioLightingPanel(self.radio_tab, self)
        self.notebook.select(self.explorer_tab)

        footer = tk.Frame(self.root, bg=BG, padx=26, pady=8)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="EDUCATIONAL RESEARCH TOOL · NOT A LANDING CERTIFICATION OR FLIGHT TOOL",
            bg=BG, fg="#9aabc1", font=("Helvetica", 8, "bold")
        ).pack(side="left")
        tk.Label(
            footer, text="Moon coordinates: degrees · Times: UTC",
            bg=BG, fg=MUTED, font=("Helvetica", 8)
        ).pack(side="right")
        apply_language(self.root, self, self.language)
        self.root.bind("<Configure>", self._fit_text_to_window, add="+")
        self.root.after_idle(self._fit_text_to_window)

    def _language_selected(self, _event=None) -> None:
        selected = source_text(self.language_var.get())
        self.language = "Turkish" if selected == "Turkish" else "English"
        self.root.title(
            "LunaSight | Explore the Moon"
            if self.language == "English" else "LunaSight | Ay'ı Keşfet"
        )
        apply_language(self.root, self, self.language)
        self.language_combo.configure(values=("English", "Turkish"))
        self.language_var.set("English" if self.language == "English" else "Turkish")
        if hasattr(self, "explorer_panel") and self.explorer_panel.result is not None:
            self._draw_sky_result(self.explorer_panel.result)
        else:
            self._draw_empty_sky()
        if hasattr(self, "explorer_panel"):
            self.explorer_panel._draw_map()
            self.explorer_panel._draw_pov()
        if hasattr(self, "radio_panel"):
            self.radio_panel.refresh()

    def _fit_text_to_window(self, event=None) -> None:
        if event is not None and event.widget is not self.root:
            return

        def resize_labels(parent: tk.Misc) -> None:
            for child in parent.winfo_children():
                if isinstance(child, tk.Label):
                    try:
                        if int(child.cget("wraplength")) > 0:
                            available = child.master.winfo_width() - 28
                            if available > 80:
                                child.configure(wraplength=available)
                        if not hasattr(child, "_lunasight_original_font"):
                            child._lunasight_original_font = child.cget("font")
                            font = tkfont.Font(root=self.root, font=child._lunasight_original_font)
                            if font.cget("size") in {7, 8}:
                                font.configure(size=9)
                            child._lunasight_accessible_font = font
                        child.configure(font=child._lunasight_accessible_font)
                    except (tk.TclError, ValueError):
                        pass
                elif isinstance(child, tk.Button):
                    try:
                        if not hasattr(child, "_lunasight_accessible_font"):
                            font = tkfont.Font(root=self.root, font=child.cget("font"))
                            if font.cget("size") < 10:
                                font.configure(size=10)
                            child._lunasight_accessible_font = font
                        foreground = child.cget("fg")
                        child.configure(
                            font=child._lunasight_accessible_font,
                            activeforeground=foreground,
                            disabledforeground="#9aabc1",
                        )
                    except (tk.TclError, ValueError):
                        pass
                resize_labels(child)

        resize_labels(self.root)

    def _panel(self, parent: tk.Widget, **kwargs) -> tk.Frame:
        return tk.Frame(
            parent, bg=PANEL, highlightbackground=BORDER,
            highlightthickness=1, **kwargs
        )

    def _section_title(self, parent: tk.Widget, title: str, subtitle: str = "") -> None:
        block = tk.Frame(parent, bg=PANEL)
        block.pack(fill="x", padx=18, pady=(16, 12))
        tk.Label(
            block, text=title, bg=PANEL, fg=TEXT,
            font=("Helvetica", 12, "bold")
        ).pack(anchor="w")
        if subtitle:
            tk.Label(
                block, text=subtitle, bg=PANEL, fg=MUTED,
                font=("Helvetica", 9), wraplength=340, justify="left"
            ).pack(anchor="w", pady=(4, 0))

    def _field(self, parent: tk.Widget, label: str, variable: tk.StringVar,
               hint: str = "") -> tk.Entry:
        block = tk.Frame(parent, bg=PANEL)
        block.pack(fill="x", padx=18, pady=(0, 10))
        tk.Label(
            block, text=label.upper(), bg=PANEL, fg=MUTED,
            font=("Helvetica", 8, "bold")
        ).pack(anchor="w", pady=(0, 5))
        entry = tk.Entry(
            block, textvariable=variable, bg=PANEL_2, fg=TEXT,
            insertbackground=TEXT, relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=("Helvetica", 10),
        )
        entry.pack(fill="x", ipady=8, ipadx=9)
        if hint:
            tk.Label(
                block, text=hint, bg=PANEL, fg="#75869f",
                font=("Helvetica", 8)
            ).pack(anchor="w", pady=(4, 0))
        return entry

    def _button(self, parent: tk.Widget, text: str, command,
                primary: bool = False) -> tk.Button:
        bg = ACCENT if primary else PANEL_2
        fg = "#07111f" if primary else TEXT
        return tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground="#8abaff" if primary else "#22334d",
            activeforeground=fg, relief="flat", bd=0,
            cursor="hand2", font=("Helvetica", 9, "bold"),
            padx=13, pady=10,
        )

    def _build_dashboard(self) -> None:
        layout = tk.Frame(self.dashboard_tab, bg=BG)
        layout.pack(fill="both", expand=True)
        layout.grid_columnconfigure(0, weight=0, minsize=315)
        layout.grid_columnconfigure(1, weight=1)
        layout.grid_rowconfigure(0, weight=1)

        # Input panel
        input_panel = self._panel(layout)
        input_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self._section_title(
            input_panel, "Plan your Moon landing",
            "Pick a spot on the Moon, choose a date and see how much sunlight it gets and when Earth is visible."
        )
        self.site_var = tk.StringVar(value="South pole · Shackleton region")
        self.lat_var = tk.StringVar(value="-89.5")
        self.lon_var = tk.StringVar(value="0.0")
        self.date_var = tk.StringVar(value="2027-01-15")
        self.time_var = tk.StringVar(value="12:00")

        name_block = tk.Frame(input_panel, bg=PANEL)
        name_block.pack(fill="x", padx=18, pady=(0, 10))
        tk.Label(
            name_block, text="PLACE NAME", bg=PANEL, fg=MUTED,
            font=("Helvetica", 8, "bold")
        ).pack(anchor="w", pady=(0, 5))
        self.site_entry = tk.Entry(
            name_block, textvariable=self.site_var, bg=PANEL_2, fg=TEXT,
            insertbackground=TEXT, relief="flat", highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=("Helvetica", 10)
        )
        self.site_entry.pack(fill="x", ipady=8, ipadx=9)

        self.manual_coordinates_open = False
        self.manual_coordinates_button = tk.Button(
            input_panel, text="Enter coordinates manually (optional)",
            command=self._toggle_manual_coordinates, bg=PANEL_2, fg=TEXT,
            activebackground="#22334d", relief="flat", bd=0,
            font=("Helvetica", 8, "bold"), padx=10, pady=7, cursor="hand2")
        self.manual_coordinates_button.pack(fill="x", padx=18, pady=(0, 8))
        self.manual_coordinates_frame = tk.Frame(input_panel, bg=PANEL)
        self._field(self.manual_coordinates_frame, "Latitude", self.lat_var, "−90° to +90°")
        self._field(self.manual_coordinates_frame, "Longitude", self.lon_var, "East-positive; −180° to +360°")
        self.date_entry = self._field(input_panel, "Landing date", self.date_var, "Use YYYY-MM-DD. The calculation uses UTC.")
        self._field(input_panel, "Landing time", self.time_var, "24-hour time, UTC (for example, 12:00).")

        btns = tk.Frame(input_panel, bg=PANEL)
        btns.pack(fill="x", padx=18, pady=(6, 8))
        self._button(btns, "Add this place to comparison", self.add_scenario).pack(fill="x")
        self.analyze_button = self._button(btns, "Check sunlight and Earth with NASA/JPL", self.analyze_current, primary=True)
        self.analyze_button.pack(fill="x", pady=(8, 0))

        tk.Label(
            input_panel,
            text="Tip: You do not need to type coordinates. Open ‘Choose a Moon location’ and click anywhere on the 3D globe. The global map helps you explore; detailed local terrain is loaded separately.",
            bg=PANEL, fg=MUTED, wraplength=270, justify="left",
            font=("Helvetica", 8)
        ).pack(fill="x", padx=18, pady=(8, 17))

        # Results area
        results = tk.Frame(layout, bg=BG)
        results.grid(row=0, column=1, sticky="nsew")
        results.grid_columnconfigure(0, weight=1)
        results.grid_rowconfigure(1, weight=1)

        cards = tk.Frame(results, bg=BG)
        cards.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        for i in range(4):
            cards.grid_columnconfigure(i, weight=1, uniform="metric")
        self.metric_values: list[tk.Label] = []
        self.metric_notes: list[tk.Label] = []
        metrics = [
            ("SUN HEIGHT ABOVE HORIZON", "—", "Higher usually means stronger direct light"),
            ("EARTH HEIGHT ABOVE HORIZON", "—", "Above the horizon means a direct view"),
            ("DAYLIGHT IN THE NEXT 24 HOURS", "—", "Share of the day with the Sun visible"),
            ("WHEN EARTH IS VISIBLE", "—", "Share of the day with Earth visible"),
        ]
        for i, (title, value, note) in enumerate(metrics):
            card = self._panel(cards)
            card.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 7, 0 if i == 3 else 7))
            tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=12, pady=(12, 6))
            value_label = tk.Label(card, text=value, bg=PANEL, fg=TEXT, font=("Helvetica", 22, "bold"))
            value_label.pack(anchor="w", padx=12)
            self.metric_values.append(value_label)
            note_label = tk.Label(card, text=note, bg=PANEL, fg=MUTED, font=("Helvetica", 8))
            note_label.pack(anchor="w", padx=12, pady=(3, 12))
            self.metric_notes.append(note_label)

        plot_panel = self._panel(results)
        plot_panel.grid(row=1, column=0, sticky="nsew")
        plot_panel.grid_rowconfigure(1, weight=1)
        plot_panel.grid_columnconfigure(0, weight=1)
        self._section_title(
            plot_panel, "What is in the sky above this place?",
            "The chart shows where the Sun and Earth appear from the selected location."
        )
        self.figure = Figure(figsize=(8, 4.5), dpi=100, facecolor=PANEL)
        self.ax = self.figure.add_subplot(111)
        self._draw_empty_sky()
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_panel)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.analysis_message = tk.StringVar(
            value="Choose a place on the Moon, set the date and check it. An internet connection is needed for live NASA/JPL results."
        )
        message_box = tk.Frame(results, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        message_box.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        tk.Label(
            message_box, textvariable=self.analysis_message, bg=PANEL,
            fg=AMBER, wraplength=850, justify="left",
            font=("Helvetica", 9), padx=14, pady=11
        ).pack(fill="x")

    def _toggle_manual_coordinates(self) -> None:
        self.manual_coordinates_open = not self.manual_coordinates_open
        if self.manual_coordinates_open:
            self.manual_coordinates_frame.pack(fill="x", padx=0, pady=(0, 6))
            self.manual_coordinates_button.configure(text="Hide manual coordinates")
        else:
            self.manual_coordinates_frame.pack_forget()
            self.manual_coordinates_button.configure(text="Enter coordinates manually (optional)")

    def _draw_empty_sky(self) -> None:
        self.ax.clear()
        self.ax.set_facecolor(PANEL)
        self.ax.set_xlim(0, 360)
        self.ax.set_ylim(-90, 90)
        self.ax.set_xticks([0, 90, 180, 270, 360])
        self.ax.set_xticklabels([
            translate(value, self.language)
            for value in ["N · 0°", "E · 90°", "S · 180°", "W · 270°", "N · 360°"]
        ])
        self.ax.set_yticks([-90, -60, -30, 0, 30, 60, 90])
        self.ax.set_ylabel(translate("Height above horizon (°)", self.language), color=MUTED, fontsize=9)
        self.ax.set_xlabel(translate("Azimuth (°)", self.language), color=MUTED, fontsize=9)
        self.ax.axhline(0, color="#9aa9bd", linewidth=1.3, linestyle="--", alpha=0.8)
        self.ax.text(180, 20, translate("THE SKY ABOVE YOUR SELECTED PLACE", self.language), color=MUTED,
                     ha="center", va="center", fontsize=10, weight="bold")
        self.ax.text(180, 10, translate("Choose a place on the Moon, set a date, then press ‘Check sunlight and Earth’.", self.language),
                     color="#74869f", ha="center", va="center", fontsize=8)
        self.ax.grid(True, color="#33445e", alpha=0.55, linewidth=0.6)
        self.ax.tick_params(colors=MUTED, labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_color(BORDER)
        self.figure.tight_layout(pad=2)
        if hasattr(self, "canvas"):
            self.canvas.draw_idle()

    def _current_scenario(self) -> Optional[MissionScenario]:
        try:
            return build_scenario(
                self.site_var.get(), self.lat_var.get(), self.lon_var.get(),
                self.date_var.get(), self.time_var.get()
            )
        except ValueError as exc:
            messagebox.showerror(
                translate("Check mission inputs", self.language),
                translate(str(exc), self.language), parent=self.root)
            return None

    def add_scenario(self) -> None:
        scenario = self._current_scenario()
        if scenario is None:
            return
        self.scenarios.append(scenario)
        self._refresh_tree()
        self.analysis_message.set(
            f"{translate('Added', self.language)} '{scenario.label}' "
            f"{translate('to the comparison list. Select Analyze with JPL Horizons to fetch live Sun/Earth positions.', self.language)}"
        )
        self.notebook.select(self.compare_tab)

    @staticmethod
    def _scenario_key(scenario: MissionScenario) -> tuple:
        return (
            scenario.site_name,
            round(scenario.latitude_deg, 8),
            round(scenario.longitude_deg, 8),
            scenario.date_time_utc.isoformat(),
        )

    def analyze_current(self) -> None:
        scenario = self._current_scenario()
        if scenario is None or self._analysis_in_progress:
            return

        self._analysis_in_progress = True
        self.analyze_button.configure(state="disabled", text="Checking with NASA/JPL…")
        self.status_label.configure(text="●  CHECKING THE SELECTED PLACE", fg=AMBER)
        self.analysis_message.set(
            "Checking the Sun and Earth positions for this place and the next 24 hours…"
        )
        self.notebook.select(self.dashboard_tab)

        def worker() -> None:
            try:
                result = analyze(scenario)
            except EphemerisError as exc:
                self.root.after(0, lambda message=str(exc): self._analysis_failed(message))
            except Exception as exc:  # keep unexpected backend errors visible, not silent
                self.root.after(0, lambda message=str(exc): self._analysis_failed(
                    f"Unexpected analysis error: {message}"
                ))
            else:
                self.root.after(0, lambda: self._analysis_succeeded(scenario, result))

        threading.Thread(target=worker, name="lunasight-ephemeris", daemon=True).start()

    def _analysis_failed(self, message: str) -> None:
        self._analysis_in_progress = False
        self.analyze_button.configure(state="normal", text="Check sunlight and Earth with NASA/JPL")
        self.status_label.configure(text="●  NASA/JPL DATA NOT AVAILABLE", fg=AMBER)
        self.analysis_message.set(message)
        messagebox.showerror(
            translate("Ephemeris request failed", self.language),
            translate(message, self.language), parent=self.root)

    def _analysis_succeeded(self, scenario: MissionScenario, result: AnalysisResult) -> None:
        self._analysis_in_progress = False
        self.analyze_button.configure(state="normal", text="Check sunlight and Earth with NASA/JPL")
        self.status_label.configure(text="●  NASA/JPL DATA LOADED", fg=GREEN)
        self.analysis_results[self._scenario_key(scenario)] = result
        self._refresh_tree()

        if hasattr(self, "explorer_panel"):
            self.explorer_panel.set_analysis(scenario, result)
        fractions = (result.sunlight_fraction, result.earth_visibility_fraction,
                     result.simultaneous_visibility_fraction)
        terrain_note = "The detailed local LOLA terrain model was used."
        if hasattr(self, "explorer_panel"):
            adjusted = self.explorer_panel.terrain_adjusted_fractions()
            if adjusted is not None:
                fractions = adjusted
            if not self.explorer_panel.terrain_coverage_available:
                terrain_note = "No detailed local terrain is loaded here, so the percentages use a smooth reference horizon."

        self.metric_values[0].configure(text=f"{result.solar_elevation_deg:+.2f}°")
        self.metric_values[1].configure(text=f"{result.earth_elevation_deg:+.2f}°")
        self.metric_values[2].configure(text=f"{fractions[0] * 100:.1f}%")
        self.metric_values[3].configure(text=f"{fractions[1] * 100:.1f}%")
        self.metric_notes[0].configure(text=f"azimuth {result.solar_azimuth_deg:.1f}°")
        self.metric_notes[1].configure(
            text=(f"azimuth {result.earth_azimuth_deg:.1f}° · range {result.earth_range_km:,.0f} km"
                  if result.earth_range_km else f"azimuth {result.earth_azimuth_deg:.1f}°")
        )
        self.metric_notes[2].configure(text="next 24 h · 30-min samples")
        self.metric_notes[3].configure(text="next 24 h · 30-min samples")
        self._draw_sky_result(result)
        if hasattr(self, "radio_panel"):
            self.radio_panel.set_analysis(scenario, result)

        self.analysis_message.set(
            f"{translate('NASA/JPL data loaded for', self.language)} {scenario.label}. "
            f"{translate('Over the next 24 hours, sunlight is available for about', self.language)} "
            f"{fractions[0] * 100:.1f}%; {translate('Earth is visible for about', self.language)} "
            f"{fractions[1] * 100:.1f}%; {translate('both are visible together for about', self.language)} "
            f"{fractions[2] * 100:.1f}%. {translate(terrain_note, self.language)} "
            f"{translate(result.source_note, self.language)}"
        )

    def _draw_sky_result(self, result: AnalysisResult) -> None:
        self.ax.clear()
        self.ax.set_facecolor(PANEL)
        self.ax.set_xlim(0, 360)
        self.ax.set_ylim(-90, 90)
        self.ax.set_xticks([0, 90, 180, 270, 360])
        self.ax.set_xticklabels([
            translate(value, self.language)
            for value in ["N · 0°", "E · 90°", "S · 180°", "W · 270°", "N · 360°"]
        ])
        self.ax.set_yticks([-90, -60, -30, 0, 30, 60, 90])
        self.ax.set_ylabel(translate("Height above horizon (°)", self.language), color=MUTED, fontsize=9)
        self.ax.set_xlabel(translate("Azimuth clockwise from north (°)", self.language), color=MUTED, fontsize=9)
        self.ax.axhline(0, color="#9aa9bd", linewidth=1.3, linestyle="--", alpha=0.9,
                        label=translate("Ideal horizon", self.language))

        samples = result.samples
        self.ax.scatter(
            [sample.sun_azimuth_deg for sample in samples],
            [sample.sun_elevation_deg for sample in samples],
            s=18, color="#f4bf55", alpha=0.62,
            label=translate("Sun · 30-min samples", self.language), zorder=3,
        )
        self.ax.scatter(
            [sample.earth_azimuth_deg for sample in samples],
            [sample.earth_elevation_deg for sample in samples],
            s=18, color="#69a9ff", alpha=0.62,
            label=translate("Earth · 30-min samples", self.language), zorder=3,
        )
        first = samples[0]
        self.ax.scatter([first.sun_azimuth_deg], [first.sun_elevation_deg], marker="*", s=150,
                        color="#ffdf85", edgecolors="#754e0c", linewidths=0.8,
                        label=translate("Sun · selected epoch", self.language), zorder=5)
        self.ax.scatter([first.earth_azimuth_deg], [first.earth_elevation_deg], marker="*", s=150,
                        color="#a8d2ff", edgecolors="#174a80", linewidths=0.8,
                        label=translate("Earth · selected epoch", self.language), zorder=5)
        self.ax.grid(True, color="#33445e", alpha=0.55, linewidth=0.6)
        self.ax.tick_params(colors=MUTED, labelsize=8)
        self.ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.12), ncol=2,
                       frameon=False, fontsize=7, labelcolor=TEXT)
        for spine in self.ax.spines.values():
            spine.set_color(BORDER)
        self.figure.tight_layout(pad=2)
        self.canvas.draw_idle()

    def _build_compare(self) -> None:
        outer = self._panel(self.compare_tab)
        outer.pack(fill="both", expand=True)
        self._section_title(
            outer, "Scenario comparison",
            "Keep candidate locations and landing epochs together. Double-click a row to load it into Mission Analysis."
        )
        table_frame = tk.Frame(outer, bg=PANEL)
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 12))
        columns = ("site", "latitude", "longitude", "epoch", "model_status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        headings = {
            "site": ("LANDING SITE", 220),
            "latitude": ("LATITUDE", 110),
            "longitude": ("LONGITUDE", 110),
            "epoch": ("LANDING EPOCH (UTC)", 190),
            "model_status": ("ANALYSIS STATUS", 210),
        }
        for col, (label, width) in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, width=width, anchor="w")
        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Double-1>", self._load_selected)

        actions = tk.Frame(outer, bg=PANEL)
        actions.pack(fill="x", padx=18, pady=(0, 18))
        self._button(actions, "Remove selected", self.remove_selected).pack(side="left")
        self._button(actions, "Export CSV", self.export_csv).pack(side="left", padx=(8, 0))
        self._button(actions, "Clear all", self.clear_scenarios).pack(side="right")

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for index, scenario in enumerate(self.scenarios):
            self.tree.insert(
                "", "end", iid=str(index),
                values=(
                    scenario.site_name,
                    f"{scenario.latitude_deg:.5f}°",
                    f"{scenario.longitude_deg:.5f}°",
                    scenario.date_time_utc.strftime("%Y-%m-%d %H:%M"),
                    translate(
                        "CALCULATED" if self._scenario_key(scenario) in self.analysis_results
                        else "NOT CALCULATED",
                        self.language,
                    ),
                ),
            )

    def remove_selected(self) -> None:
        selected = sorted((int(x) for x in self.tree.selection()), reverse=True)
        for index in selected:
            if 0 <= index < len(self.scenarios):
                self.scenarios.pop(index)
        self._refresh_tree()

    def clear_scenarios(self) -> None:
        if not self.scenarios:
            return
        if messagebox.askyesno(
            translate("Clear comparison", self.language),
            translate("Remove all saved scenarios from this session?", self.language),
            parent=self.root):
            self.scenarios.clear()
            self._refresh_tree()

    def _load_selected(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        scenario = self.scenarios[int(selected[0])]
        self.site_var.set(scenario.site_name)
        self.lat_var.set(str(scenario.latitude_deg))
        self.lon_var.set(str(scenario.longitude_deg))
        self.date_var.set(scenario.date_time_utc.strftime("%Y-%m-%d"))
        self.time_var.set(scenario.date_time_utc.strftime("%H:%M"))
        self.notebook.select(self.dashboard_tab)

    def export_csv(self) -> None:
        if not self.scenarios:
            messagebox.showinfo(
                translate("Nothing to export", self.language),
                translate("Add at least one scenario first.", self.language),
                parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")], initialfile="lunasight_scenarios.csv"
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow([
                    "site_name", "latitude_deg", "longitude_deg", "date_time_utc",
                    "analysis_status", "sun_azimuth_deg", "sun_elevation_deg",
                    "earth_azimuth_deg", "earth_elevation_deg", "earth_range_km", "sunlight_fraction_next_24h",
                    "earth_visibility_fraction_next_24h", "simultaneous_visibility_fraction_next_24h",
                ])
                for scenario in self.scenarios:
                    result = self.analysis_results.get(self._scenario_key(scenario))
                    writer.writerow([
                        scenario.site_name, scenario.latitude_deg,
                        scenario.longitude_deg, scenario.date_time_utc.isoformat(),
                        "CALCULATED" if result else "NOT_CALCULATED",
                        result.solar_azimuth_deg if result else "",
                        result.solar_elevation_deg if result else "",
                        result.earth_azimuth_deg if result else "",
                        result.earth_elevation_deg if result else "",
                        result.earth_range_km if result and result.earth_range_km else "",
                        result.sunlight_fraction if result else "",
                        result.earth_visibility_fraction if result else "",
                        result.simultaneous_visibility_fraction if result else "",
                    ])
        except OSError as exc:
            messagebox.showerror(
                translate("Export failed", self.language),
                translate(str(exc), self.language), parent=self.root)
            return
        messagebox.showinfo(
            translate("Export complete", self.language),
            translate("Scenario list saved to:\n{path}", self.language).format(path=path),
            parent=self.root)

    def _build_data_tab(self) -> None:
        panel = self._panel(self.data_tab)
        panel.pack(fill="both", expand=True)
        self._section_title(
            panel, "Where the information comes from",
            "LunaSight uses public NASA/JPL datasets and calculations. Some views are global previews; detailed landing checks need local terrain data."
        )

        cards = tk.Frame(panel, bg=PANEL)
        cards.pack(fill="x", padx=18, pady=(0, 14))
        self._data_source_card(cards, "JPL Horizons", "Sun & Earth positions", "Live · internet", "Calculates where the Sun and Earth appear from the selected Moon location and how far away Earth is.", 0)
        self._data_source_card(cards, "NASA LOLA", "Moon elevation", "Download in app", "Global 4 px/degree or 16 px/degree elevation for browsing, plus a high-detail 80 m South Pole model and six 5 m site tiles. Global data is not detailed enough to certify a landing spot.", 1)
        self._data_source_card(cards, "NASA/JPL DSN", "Radio signal example", "Reference model", "Uses published example frequency and transmitter information to estimate free-space received power. Actual lander radio specifications are mission-specific.", 2)

        note = tk.Frame(panel, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        note.pack(fill="x", padx=18, pady=(0, 18))
        tk.Label(
            note, text="WHAT THE RESULTS MEAN", bg=PANEL_2, fg=ACCENT,
            font=("Helvetica", 9, "bold")
        ).pack(anchor="w", padx=15, pady=(13, 6))
        requirements = [
            "1. Sunlight: an estimate based on the Sun’s angle and whether the Sun is above the local terrain horizon.",
            "2. Earth view: a geometric visibility check. Hills and crater rims can block the direct line of sight.",
            "3. Radio power: a free-space estimate using a published example ground-station profile, not the confirmed radio of every lander.",
            "4. Global map: lets you choose any latitude and longitude. Higher-detail local terrain is available only for selected regions.",
        ]
        for line in requirements:
            tk.Label(
                note, text=line, bg=PANEL_2, fg=TEXT,
                font=("Helvetica", 9), anchor="w", justify="left", wraplength=1000
            ).pack(fill="x", padx=15, pady=3)
        tk.Label(
            note,
            text="Important: the global map is a location finder, not a detailed landing-hazard map. The local astronaut preview stays illustrative unless high-resolution terrain for that exact location is loaded. Radio power is an estimate, not proof that a mission link will work. LunaSight is an educational planning aid, not a landing approval or flight tool.",
            bg=PANEL_2, fg=AMBER, font=("Helvetica", 9, "bold"),
            wraplength=1000, justify="left"
        ).pack(anchor="w", padx=15, pady=(10, 14))

    def _data_source_card(self, parent: tk.Widget, title: str, category: str,
                          status: str, description: str, column: int) -> None:
        parent.grid_columnconfigure(column, weight=1, uniform="source")
        card = tk.Frame(parent, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 6 if column < 2 else 0))
        tk.Label(card, text=category.upper(), bg=PANEL_2, fg=MUTED, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=13, pady=(13, 6))
        tk.Label(card, text=title, bg=PANEL_2, fg=TEXT, font=("Helvetica", 12, "bold")).pack(anchor="w", padx=13)
        status_color = GREEN if status == "Ready" else AMBER
        tk.Label(card, text=f"● {status}", bg=PANEL_2, fg=status_color, font=("Helvetica", 8, "bold")).pack(anchor="w", padx=13, pady=(7, 5))
        tk.Label(card, text=description, bg=PANEL_2, fg=MUTED, font=("Helvetica", 8), justify="left", wraplength=280).pack(fill="x", padx=13, pady=(0, 13))


def launch() -> None:
    root = tk.Tk()
    LunaSightApp(root)
    root.mainloop()
