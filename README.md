# LunaSight — Interactive Lunar Landing-Site Explorer

**LunaSight** is a cross-platform lunar exploration and mission-planning project designed to help users explore potential lunar landing locations and understand the scientific and engineering trade-offs involved in selecting a landing site.

The project provides two complementary applications:

- **LunaSight Web:** A browser-based interactive lunar mission planner with a 3D Moon, mission timeline, sunlight and Earth visibility analysis, and guided simulations.
- **LunaSight Desktop (v0.5.1):** A standalone Python application offering interactive lunar site selection, NASA terrain integration, scientific calculations, and more detailed technical analysis.

Both applications are designed to make lunar mission planning accessible to non-specialists while keeping scientific assumptions, data sources, and model limitations transparent.

---

# 1. Project Overview

LunaSight explores the relationship between lunar geography, sunlight availability, Earth visibility, terrain, and communication conditions.

Its primary objectives are to:

- Explore the lunar surface through an interactive 3D globe.
- Identify and compare potential lunar landing locations.
- Examine the position of the Sun and Earth relative to a selected location.
- Investigate sunlight availability and direct-to-Earth visibility.
- Explore lunar terrain using NASA elevation datasets.
- Understand the relationship between geographical conditions and communication availability.
- Compare different landing-site scenarios under the same mission conditions.

## Two ways to use LunaSight

| Feature                | Web Version                        | Desktop Version                        |
| ---------------------- | ---------------------------------- | -------------------------------------- |
| Platform               | Web browser                        | macOS, Windows, Linux                  |
| Interface              | Interactive web HUD                | Python desktop GUI                     |
| 3D Moon exploration    | Yes                                | Yes                                    |
| Site selection         | Interactive globe and coordinates  | Interactive globe and coordinates      |
| Sun and Earth analysis | Yes                                | Yes                                    |
| Mission timeline       | Yes                                | UTC-based analysis                     |
| NASA/JPL Horizons      | Analytic ephemeris in browser demo | Live API requests                      |
| NASA LOLA terrain      | Illustrative/local assets          | Global and regional datasets           |
| Terrain visualization  | Panorama and horizon profiles      | 3D globe and local surface perspective |
| Communication analysis | Educational radio simulation       | S- and X-band reference calculations   |
| Language options       | English                            | English and Turkish                    |

---

# 2. LunaSight Web

The browser-based version is an interactive concept for exploring lunar landing-site trade-offs.

The main application is located in `index.html`, while `showcase.html` contains the project presentation and guided mission scenarios.

## Launch the Web Application

### From VS Code

Open the repository folder and run the launcher for your operating system.

**macOS**

- Double-click `run_mac.command`.
- Alternatively, execute `bash run_mac.command` in the integrated terminal.

**Windows**

- Double-click `run_windows.bat`.

**Linux**

- Execute `bash run_linux.sh` in the integrated terminal.

The launcher starts a local web server and opens:

`http://127.0.0.1:8000/`

Keep the terminal and server window open while using the application.

No package installation is required. The launchers use Python's built-in static web server.

Alternatively, open `index.html` using the VS Code Live Server extension.

To start the server manually:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

Then visit `http://127.0.0.1:8000/`.

**Internet connection:** Tailwind CSS is loaded from its CDN. Panorama and audio assets are served locally from the repository.

## Install as a Desktop App

The web application includes a standalone-app manifest and application icons.

With the local server running:

- **Safari:** Open the application and select File → Add to Dock.
- **Chrome / Edge:** Use the browser's Install LunaSight action.

The installed application opens in its own window. The local server must remain active while using this installation.

## Jury Presentation

Open `showcase.html` to explore the Cosmic Variance project presentation, workflow, and three guided lunar simulations.

The presentation includes three scenarios:

1. Slater Plain
2. Malapert Massif
3. Nobile Rim

Each scenario opens the interactive HUD at a different lunar location using the same UTC epoch, allowing direct comparison of environmental conditions.

The GitHub Pages workflow deploys both the interactive application and presentation.

- Main application: Repository root (`/`)
- Project presentation: `/showcase.html`

## Using the Web Simulator

1. Select a lunar landing site in the mission planner.
2. Inspect the modeled Sun and Earth against the local horizon.
3. Use the mission timeline to explore changing environmental conditions.
4. Rotate the Moon to explore different geographical locations.
5. Enter coordinates manually if needed.
6. Compare sunlight and direct-to-Earth visibility using the telemetry panel.
7. Explore the optional communication channel, which combines local radio and static audio.

The browser demonstration uses an analytic ephemeris, illustrative horizon profiles, and panorama imagery. It is an educational simulation rather than a landing-site certification tool.

---

# 3. LunaSight Desktop (v0.5.1)

The desktop version is a cross-platform application for exploring lunar landing locations and comparing sunlight availability and direct-to-Earth visibility from a selected point.

It is designed to be understandable to non-specialists while keeping the underlying scientific assumptions visible to technical users.

## Getting Started

1. Start LunaSight with an internet connection.
2. Select **English** or **Turkish** from the Language menu in the upper-right corner.
3. The application opens on **Choose a place**.
4. Select a globe preset:
   - Near side
   - Far side
   - East
   - West
   - North pole
   - South pole
5. Hold the left mouse button and drag the Moon to rotate it. Dragging rotates the globe without changing the selected location.
6. Zoom using the mouse wheel, trackpad, or the **+ / −** buttons.
7. Use **Reset view** to return to the South Pole view and default zoom.
8. Click a location on the lunar surface to select it. A short click selects a location; dragging rotates the globe.
9. Select **Set date and check this place**, choose a UTC date and time, and press **Check sunlight and Earth with NASA/JPL**.
10. Open **Sunlight & Earth link** for a simplified explanation or **Compare places** to save and compare multiple scenarios.

Manual latitude and longitude entry is also available, although it is hidden by default because the 3D globe is the primary location selector.

## User Guides

- `reports/LunaSight_User_Guide.html` — Accessible, high-contrast user guide.
- `reports/LunaSight_Science_and_Coverage_Guide.html` — Detailed scientific models, datasets, and coverage limitations.

## What's New in v0.5.1

- Interactive Moon rotation using mouse dragging.
- Location selection through short clicks.
- Zoom controls and reset functionality.
- Improved typography, readability, and interface contrast.
- A lunar surface perspective with a dark sky and terrain horizon.
- Visible Sun and Earth direction indicators when applicable.
- A persistent selected-site marker while rotating the globe.
- Six geographical presets covering the entire Moon.
- Quick links to Apollo, Luna, Chang'e, Chandrayaan-3, and South Pole reference locations.
- Optional NASA LOLA elevation downloads at 4 px/degree and 16 px/degree.
- Optional NASA LROC WAC-derived color texture.
- An anti-aliased 81 × 161 globe display mesh.
- Detailed local LOLA terrain integration when available.
- NASA Moon Trek local terrain downloads.
- Improved horizon-aware sunlight and Earth visibility calculations.
- A beginner-friendly communication dashboard.
- Direct integration between site selection, mission date, and scientific analysis.

The display mesh improves visualization but does not increase the resolution of the original elevation dataset.

---

# 4. Scientific Models and Data

The desktop application includes several scientific and engineering models. Their assumptions and limitations are described below.

## 4.1 Sun and Earth Positions

- Live topocentric azimuth, elevation, and Earth range are requested from the JPL Horizons API.
- Calculations use the selected lunar latitude, longitude, and UTC epoch.
- The following 24 hours are sampled at 30-minute intervals.
- Visibility percentages use the centre of the Sun or Earth relative to the selected horizon.

The current implementation does not calculate full partial-disk occultation or refine exact rise and set event times.

## 4.2 Lunar Topography and Global Site Selection

LunaSight integrates several NASA lunar elevation datasets.

| Dataset                       | Resolution                   | Purpose                         |
| ----------------------------- | ---------------------------- | ------------------------------- |
| Global LOLA                   | 4 px/degree                  | Full-Moon overview              |
| Global LOLA                   | 16 px/degree                 | More detailed global overview   |
| South Polar LOLA              | 80 m/pixel                   | Regional south-polar elevation  |
| Selected site tiles           | 5 m/pixel                    | High-resolution candidate areas |
| NASA Moon Trek                | 256 px/degree global service | Local terrain patches           |
| NASA Moon Trek polar services | 100 m/pixel                  | Polar terrain coverage          |

The six high-resolution south-polar candidate areas are:

- Connecting Ridge
- Shackleton rim
- Peak near Shackleton
- de Gerlache rim
- Leibnitz beta plateau
- Malapert massif

Global LOLA samples are bilinearly interpolated with longitude wrapping and nodata-aware weights to reduce blocky artifacts in local previews.

However, the global elevation model remains relatively coarse and cannot identify small rocks, lander-scale slopes, or landing hazards.

### SLDEM2015

The higher-resolution SLDEM2015 merged LOLA/Kaguya terrain product covers approximately 60°S–60°N, with an effective spatial resolution of around 60–100 metres.

Its global files are several gigabytes in size, and the highest-resolution products are distributed as regional tiles.

SLDEM2015 is documented as a potential source for future regional downloads but is not automatically downloaded in v0.5.1. Polar regions require their own LOLA products.

## 4.3 Sunlight and Illuminance

The desktop application estimates direct horizontal-surface illuminance using:

`127,000 lx × sin(solar elevation)`

Direct solar irradiance is estimated using:

`1361 W/m² × sin(solar elevation)`

Both estimates are zero when the Sun is below the modeled horizon.

These are ideal direct-beam estimates. They do not account for:

- Surface reflectance.
- Thermal emission.
- Earthshine.
- Visor optical effects.
- Dust.
- Local shading when detailed terrain is unavailable.
- Actual solar-array tilt and efficiency.

Lux is a human-vision-weighted photometric unit and should not be confused with radio signal power.

## 4.4 Earth Visibility and Communication Analysis

The application checks whether Earth's centre is above the reference or local terrain horizon.

The S- and X-band radio examples use:

- Published DSN ground-station EIRP profiles.
- JPL Horizons topocentric Earth range.
- The Friis free-space path-loss equation.

The displayed received power is a theoretical clear-path reference, not a measured signal or completed communications link budget.

The lunar coordinates change Earth-centre range by at most approximately one lunar diameter (3,475 km), compared with an Earth–Moon distance of roughly 400,000 km.

Consequently, the difference in free-space loss between lunar locations can be less than 0.1 dB.

The visibility model does not include:

- Earth's complete visible limb.
- Specific DSN station availability.
- Antenna patterns and pointing.
- Diffraction and reflections.
- A complete mission communications link budget.

A mission-specific communications assessment would also require the actual lander antenna pattern, receiver G/T or noise temperature, bandwidth, data rate, modulation and coding, pointing error, polarization, and implementation losses.

The DSN ground-station example is not a confirmed hardware configuration for every NASA or CLPS mission.

## 4.5 Site Suitability Indicator

LunaSight uses a transparent educational screening system.

| Classification       | Conditions                                                                                                                         |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| Major constraint     | Sampled sunlight below 20% or Earth visibility below 10%                                                                           |
| Promising geometry   | Sunlight at least 70%, Earth visibility at least 50%, simultaneous visibility at least 30%, and detailed local LOLA terrain loaded |
| Compare alternatives | Other calculated cases that do not meet the above conditions                                                                       |
| Needs more data      | No ephemeris calculation has been performed                                                                                        |

These thresholds are prototype screening rules, not official NASA requirements or landing approval criteria.

A positive **Promising geometry** classification is not displayed without detailed local LOLA terrain coverage.

---

# 5. Important Scientific Limitations

**LunaSight is an educational and early-stage mission-planning prototype.**

Any lunar location can be selected, but high-resolution scientific data are not available at equal resolution everywhere.

The whole-Moon elevation grid is suitable for browsing and broad geographical context. More detailed horizon calculations are currently limited to loaded south-polar LOLA coverage and six named site tiles.

For other locations, the application falls back to a simplified horizon unless a detailed local dataset is integrated.

The applications are not flight tools, landing-site certification systems, or substitutes for mission-specific engineering analysis.

Their results must not be interpreted as operational guidance or proof that a particular location is safe for landing.

Validated ephemerides, measured terrain, hazard analysis, and mission-specific thermal, power, communications, and engineering reviews are required for actual mission decisions.

---

# 6. Installation and Requirements

## 6.1 Web Version

**Requirements:**

- A modern web browser.
- Python for the local static server.
- Internet connection for Tailwind CSS.

No additional Python packages are required.

Run the appropriate launcher or start the server manually:

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

## 6.2 Desktop Version

**Requirements:**

- Python 3.10 or newer.
- Tkinter.
- Internet connection for live JPL/NASA data.

### macOS

Double-click `run_mac.command`, or run:

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

### Windows

Double-click `run_windows.bat`, or run:

```powershell
py -m pip install -r requirements.txt
py main.py
```

### Linux

Install the Tk package for your Linux distribution if necessary, then run:

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

The first launch can download global LOLA elevation data and the optional color texture when requested.

Downloaded datasets are cached locally in:

`~/.cache/lunasight/global_moon`

The exact cache location depends on the operating system.

The v0.5.1 build environment could not verify live NASA downloads or a live Horizons request. The first network-backed run should therefore be tested on the user's computer.

---

# 7. Testing

The desktop application includes automated tests.

Run the test suite using:

```bash
python -m unittest discover -s tests -v
```

The v0.5.1 build was checked with 30 automated tests and a desktop-window smoke test covering:

- Zoom.
- Drag rotation.
- Reset functionality.
- Turkish and English language switching.
- Empty dashboard state.
- Synthetic analysis results.

---

# 8. Repository Structure

The repository contains both the browser-based and desktop implementations.

```text
LunaSight/
│
├── LunaSightWeb/
│   ├── index.html
│   ├── showcase.html
│   ├── assets/
│   ├── panorama-*.png
│   ├── cosmic-variance-logo.png
│   └── *.mp3
│
├── lunasight/
│   ├── engine.py
│   ├── science.py
│   ├── terrain.py
│   ├── advanced_ui.py
│   ├── reporting.py
│   ├── models.py
│   └── ui.py
│
├── reports/
│   ├── LunaSight_User_Guide.html
│   ├── LunaSight_Science_and_Coverage_Guide.html
│   └── ...
│
├── tests/
│
├── main.py
├── requirements.txt
│
├── run_mac.command
├── run_windows.bat
├── run_linux.sh
│
├── .gitignore
└── README.md
```

*Note: The directory names above illustrate the combined project organization. Adjust them to match the actual repository structure.*

---

# 9. Scientific References and Data Sources

LunaSight draws on publicly available NASA and JPL resources.

### Orbital Mechanics and Ephemerides

- [NASA/JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [NAIF SPICE Documentation](https://naif.jpl.nasa.gov/naif/)

SPICE is a potential future validation and integration source; it is not the active calculation backend in Desktop v0.5.1.

### Lunar Topography and Mapping

- [NASA Moon Trek](https://trek.nasa.gov/moon/)
- [NASA/GSFC SVS — CGI Moon Kit Global LOLA Maps and LROC-derived Texture](https://svs.gsfc.nasa.gov/4720)
- [NASA PGDA — High-resolution Lunar Topography (SLDEM2015)](https://pgda.gsfc.nasa.gov/products/54)
- [NASA/GSFC PGDA — LOLA South Polar DEM and Site Tiles](https://pgda.gsfc.nasa.gov/products/90)
- [LROC WMS Map and Layers](https://data.lroc.imldi.com/lroc)

### Communications and Radio Engineering

- [NASA HLS RF ConOps](https://ntrs.nasa.gov/api/citations/20250003508/downloads/HLS-CONOP-008_Sustained_Phase_HLS_RF_ConOps_Rev_A.pdf)
- [NASA/JPL DSN Services Catalog](https://www.nasa.gov/wp-content/uploads/2023/09/dsn-services-catalog.pdf)
- [JPL DSN Frequency and Channel Assignments](https://deepspace.jpl.nasa.gov/dsndocs/810-005/201/201D.pdf)

### Lunar Lighting

- [NASA OCHMO — Artemis Lighting Considerations](https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-001-artemis-lighting-considerations.pdf)

### LunaSight Documentation

- `reports/LunaSight_NASA_RF_ve_Aydinlatma_Teknik_Raporu_TR.md` — Detailed technical report in Turkish.
- `reports/LunaSight_Science_and_Coverage_Guide.html` — Science and coverage guide.
- `reports/LunaSight_User_Guide.html` — User guide.
- `reports/LunaSight_v0.5.0_Science_and_Coverage_Guide_EN.md` — English science and coverage documentation.

---

# 10. Project Vision

LunaSight aims to make lunar exploration and landing-site analysis more accessible through interactive visualization and transparent scientific modeling.

By combining geographical exploration, orbital calculations, terrain data, lighting conditions, and communication constraints, the project provides an educational environment for understanding the challenges of future lunar missions.

The long-term vision is to expand the integration of validated scientific datasets, improve local terrain and horizon modeling, and develop increasingly comprehensive tools for comparing potential lunar landing locations.

**LunaSight — Explore the Moon. Understand the Environment. Evaluate the Possibilities.**

---

*LunaSight is an independent educational and research-oriented project. NASA and JPL datasets and documentation are referenced as scientific sources; their inclusion does not imply NASA endorsement or affiliation.*

