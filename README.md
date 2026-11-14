# LunaSight Desktop — v0.5.1

LunaSight is a cross-platform desktop application for exploring lunar landing locations and comparing the sunlight and direct-to-Earth view from a selected point. It is designed to be understandable to non-specialists while keeping the underlying assumptions visible to technical users.

## Start here

1. Start LunaSight with an internet connection.
2. Select **English** or **Turkish** from the Language menu in the upper-right corner.
3. The app opens on **Choose a place**.
4. Choose a globe preset (near side, far side, east, west, north pole or south pole).
5. Hold the left mouse button and drag the Moon to rotate it. Dragging rotates without changing the selected site.
6. Zoom with the mouse wheel/trackpad or the **+ / −** buttons. **Reset view** returns to the South Pole view and default zoom.
7. Click a spot on the lunar surface to select it. A short click selects; a drag only rotates.
8. Click **Set date and check this place**, choose a UTC date and time, then press **Check sunlight and Earth with NASA/JPL**.
9. Open **Sunlight & Earth link** for the simple lighting and radio explanation, or **Compare places** to save multiple scenarios.

Manual latitude/longitude entry is available but hidden by default because the 3D globe is the primary site selector.

For a larger, high-contrast guide, open [`reports/LunaSight_User_Guide.html`](reports/LunaSight_User_Guide.html) in your browser. The detailed science guide is also available as [`reports/LunaSight_Science_and_Coverage_Guide.html`](reports/LunaSight_Science_and_Coverage_Guide.html).

## What's new in v0.5.1

- Rotate the Moon by dragging, select locations with a short click, and zoom with the wheel or on-screen controls.
- **Reset view** returns to the South Pole preset and default zoom.
- Instruction text, secondary labels and the in-app data guide use larger fonts and stronger contrast.
- The selected-site preview is now a lunar surface perspective with a dark sky and terrain horizon, replacing the labeled 3D terrain chart. Calculated Sun/Earth directions are marked when visible.
- The selected-site marker stays visible while rotating: it follows the location on the near side and moves to the globe's edge with a direction cue when the location is on the far side.
- The app now opens at the whole-Moon site selector instead of the analysis form.
- Six orthogonal geographic views make every part of the Moon reachable: Earth-facing side, far side, east side, west side, north pole and south pole.
- Click the 3D globe to select a coordinate; quick links cover Apollo, Luna, Chang'e, Chandrayaan-3 and south-polar reference areas.
- NASA global LOLA elevation can be downloaded at 4 px/degree (small starter model) or 16 px/degree (larger global model). Downloads are cached locally.
- An optional NASA LROC WAC-derived color texture is loaded for the globe. It is a display texture; high-latitude fill has lower detail and is not a substitute for measured terrain.
- The NASA globe uses an 81 × 161 anti-aliased display mesh (about 2.25° between vertices), improving visible relief and color detail while keeping the full-Moon view responsive. This display mesh does not increase the source DEM's resolution.
- The surface perspective uses detailed local LOLA terrain when available, otherwise the downloaded global LOLA grid. With no NASA terrain loaded it creates a repeatable, site-specific illustrative landscape, clearly labeled as not NASA data. The view faces the Sun after analysis and dims when the Sun is below the local horizon.
- **NASA TREK terrain here** downloads a cached, 16 km local LOLA patch from the NASA Moon Trek global service (256 pixels/degree) or its 100 m/pixel polar services. The surface preview reprojects it onto a regular local east/north grid; availability still depends on NASA's service and local coverage.
- The surface-view camera is automatically raised above higher nearby terrain to prevent the viewpoint from clipping below the rendered ground. Its displayed elevation is therefore not a fixed astronaut eye height.
- The communication panel now starts safely before an analysis and presents a beginner-friendly summary.
- The dashboard's 24-hour sunlight and Earth visibility percentages are adjusted by the local LOLA horizon when detailed terrain is available.
- A direct “Set date and check this place” action connects site selection to mission date and analysis.

## Scientific models and data

### 1. Sun and Earth positions

- Live topocentric azimuth, elevation and Earth range are requested from the JPL Horizons API for the selected lunar latitude/longitude and UTC epoch.
- The following 24 hours are sampled at 30-minute intervals.
- The current visibility percentages use the centre of the Sun/Earth relative to the selected horizon. The model does not yet calculate the full partial-disk occultation or refine exact rise/set event times.

### 2. Lunar topography and global site selection

- **Global LOLA 4 px/degree:** approximately 7.5 km per pixel at the equator; recommended for a quick full-Moon overview.
- **Global LOLA 16 px/degree:** approximately 1.9 km per pixel at the equator; optional larger download for a more detailed full-Moon overview.
- The globe display anti-aliases those source grids onto an 81 × 161 mesh for smoother, more detailed rendering; this is visualization resampling, not new terrain measurement.
- **South polar LOLA 80 m/pixel:** regional high-resolution elevation product for the south polar area.
- **Six 5 m/pixel site tiles:** selected south-polar candidate areas (Connecting Ridge, Shackleton rim, peak near Shackleton, de Gerlache rim, Leibnitz beta plateau and Malapert massif).
- Global LOLA samples are bilinearly interpolated with longitude wrapping and nodata-aware weights to reduce blocky artifacts in local previews. The global model remains coarse; it is not a high-resolution horizon mask and cannot identify small rocks, lander-scale slopes or landing hazards.
- **NASA Moon Trek local LOLA:** use **NASA TREK terrain here** to request a cached patch centered on the selected coordinates. Moon Trek provides a global 256-pixel/degree service and 100 m/pixel north/south polar services. The local view samples this source at its native coverage and does not imply hazard-scale resolution.

The higher-resolution SLDEM2015 merged LOLA/Kaguya terrain product covers approximately 60°S–60°N, with effective spatial resolution around 60–100 m. Its published global files are multi-gigabyte, and the highest-resolution versions are distributed as regional tiles. It is documented as a source for a future regional-download feature but is **not automatically downloaded by v0.5.1**. Polar areas require their own LOLA products. See the NASA PGDA data page in Sources.

### 3. Sunlight and lux

- Solar elevation is taken from JPL Horizons.
- Direct horizontal-surface illuminance is estimated as `127,000 lx × sin(solar elevation)` when the Sun is above the modeled horizon; otherwise it is zero.
- Direct solar irradiance is estimated as `1361 W/m² × sin(solar elevation)` when above the horizon.
- These are ideal direct-beam estimates. They do not include surface reflectance, thermal emission, Earthshine, visor optical effects, dust, local shading if no detailed DEM is loaded, or the actual solar-array tilt and efficiency.
- Lux is a human-vision-weighted photometric unit. It is not radio signal power.

### 4. Earth visibility and radio reference estimate

- Earth visibility checks whether Earth's centre is above the reference/local terrain horizon.
- The S- and X-band RF examples use published DSN ground-station EIRP profiles, JPL Horizons Earth range when available, and the free-space path-loss equation.
- The default lander receive gain and additional-loss values are simple reference assumptions that can be changed under **Show technical settings**.
- This produces a theoretical received-power reference in dBm. It is not a completed communications link budget and does not prove a modem can establish a link.

A mission-specific link closure also needs the actual lander antenna pattern and gain, receiver G/T or noise temperature, bandwidth, data rate, modulation/coding, pointing error, polarization and implementation losses. The DSN ground-station example is not the confirmed hardware configuration of every NASA or CLPS mission.

### 5. Simple site suitability indicator

LunaSight uses a transparent educational screen:

- **Major constraint:** sampled sunlight is below 20% or Earth visibility is below 10%.
- **Promising geometry:** sunlight is at least 70%, Earth visibility at least 50%, simultaneous visibility at least 30%, and detailed local LOLA terrain is loaded.
- **Compare alternatives:** other calculated cases that do not meet the above conditions.
- **Needs more data:** no ephemeris calculation has been run.

These thresholds are prototype screening rules, not NASA requirements or a landing approval. No positive “promising geometry” label is shown without detailed local LOLA terrain coverage.

## Important coverage boundary

**Any lunar location can be selected. High-resolution science data are not available at equal resolution everywhere in this prototype.** The whole-Moon grid is appropriate for browsing and broad context; the most detailed horizon calculations are currently limited to the loaded south-polar LOLA coverage and six named site tiles. For other regions, the app clearly falls back to a simple horizon unless a detailed local dataset is integrated.

LunaSight v0.5.1 is an educational and early-planning prototype. It is not a flight tool, landing-site certification system or substitute for mission-specific SPICE, terrain, thermal, power, communications and hazard analyses.

## Install and run

Requirements: Python 3.10+, Tkinter, and an internet connection for live JPL/NASA data.

### macOS

Double-click `run_mac.command`, or in Terminal:

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

Install the Tk package for your distribution if needed, then run:

```bash
python3 -m pip install -r requirements.txt
python3 main.py
```

The first launch can download global LOLA data and the optional color texture when you press the relevant buttons. These files are cached in `~/.cache/lunasight/global_moon` (or the equivalent home-cache directory on your OS). The build environment used for this release could not verify live NASA downloads or a live Horizons request; test the first network-backed run on your computer.

## Tests

```bash
python -m unittest discover -s tests -v
```

The v0.5.1 build was checked with 30 automated tests and a desktop-window smoke test that included zoom, drag rotation, reset, Turkish/English switching, the empty dashboard state and a synthetic analysis result.

## Sources

- [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [NAIF SPICE documentation](https://naif.jpl.nasa.gov/naif/) — future validation/integration source; SPICE is not yet the active calculation backend.
- [NASA/GSFC SVS — CGI Moon Kit global LOLA maps and LROC-derived texture](https://svs.gsfc.nasa.gov/4720)
- [NASA PGDA — High-resolution Lunar Topography (SLDEM2015)](https://pgda.gsfc.nasa.gov/products/54)
- [NASA/GSFC PGDA — LOLA south-polar DEM and site tiles](https://pgda.gsfc.nasa.gov/products/90)
- [NASA Moon Trek](https://trek.nasa.gov/moon/) — global map and additional lunar datasets.
- [LROC WMS map and layers](https://data.lroc.imldi.com/lroc)
- [NASA HLS RF ConOps](https://ntrs.nasa.gov/api/citations/20250003508/downloads/HLS-CONOP-008_Sustained_Phase_HLS_RF_ConOps_Rev_A.pdf)
- [NASA/JPL DSN Services Catalog](https://www.nasa.gov/wp-content/uploads/2023/09/dsn-services-catalog.pdf)
- [JPL DSN Frequency and Channel Assignments](https://deepspace.jpl.nasa.gov/dsndocs/810-005/201/201D.pdf)
- [NASA OCHMO — Artemis Lighting Considerations](https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-001-artemis-lighting-considerations.pdf)
- [LunaSight detailed technical report (Turkish)](reports/LunaSight_NASA_RF_ve_Aydinlatma_Teknik_Raporu_TR.md)
- [LunaSight science and coverage guide (HTML, readable)](reports/LunaSight_Science_and_Coverage_Guide.html)
- [LunaSight easy user guide (HTML, readable)](reports/LunaSight_User_Guide.html)
- [LunaSight science and coverage guide (English)](reports/LunaSight_v0.5.0_Science_and_Coverage_Guide_EN.md)

## Project structure

```text
LunaSight-Desktop/
├── main.py
├── requirements.txt
├── run_mac.command
├── run_windows.bat
├── run_linux.sh
├── reports/
├── tests/
└── lunasight/
    ├── engine.py
    ├── science.py
    ├── terrain.py
    ├── advanced_ui.py
    ├── reporting.py
    ├── models.py
    └── ui.py
```
