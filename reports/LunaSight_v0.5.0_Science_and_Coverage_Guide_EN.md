# LunaSight v0.5.0 — Science, Models and Data Coverage

**Purpose:** Explain the science behind LunaSight in plain language and record what the desktop application actually calculates.

## 1. What the user sees

LunaSight is a desktop planning aid with a whole-Moon site picker. The user can switch between six orthographic views (Earth-facing side, far side, east side, west side, north pole and south pole) and click the visible globe to choose a site. A latitude/longitude can also be entered manually, but this is an optional advanced control.

The globe covers the complete lunar surface in the location-selection sense: every latitude and longitude is reachable by switching views. This does not mean that equally detailed terrain data exist at every location.

## 2. Data inventory

| Dataset / service | Role in v0.5.0 | Coverage and important limit |
|---|---|---|
| JPL Horizons API | Sun/Earth topocentric direction, range and 24-hour samples | Requested live for the chosen lunar coordinate and UTC date. Depends on internet access and the Horizons lunar reference-site convention. |
| NASA global LOLA 4 px/degree | Whole-Moon elevation locator | Coarse global relief; about 7.5 km per pixel at the equator. |
| NASA global LOLA 16 px/degree | Higher-detail global locator | Larger optional download; about 1.9 km per pixel at the equator. Still too coarse for landing hazards or reliable small-scale local horizons. |
| NASA LROC WAC-derived global color map | Globe appearance / visual context | Display texture, not an elevation or photometric calibration product. NASA notes that the high polar regions use lower-resolution fill data. |
| NASA/GSFC PGDA LOLA 80S DEM | Detailed south-polar terrain and local horizon where coverage exists | 80 m/pixel regional terrain; only for the southern polar region. |
| NASA/GSFC PGDA 5 m site tiles | Local terrain for selected south-polar candidate regions | Six specific tile areas only; not a global 5 m model. |
| NASA SLDEM2015 | Documented source for future regional terrain loading | Merged LOLA + SELENE/Kaguya terrain, approximately 60–100 m effective resolution, approximately 60°S–60°N coverage. Not downloaded automatically in this version; polar areas need dedicated LOLA products. |

NASA's SLDEM2015 product page states that the merged terrain combines LOLA and SELENE Terrain Camera data, covers the ±60° latitude band and has roughly 60–100 m effective horizontal resolution. NASA also notes typical vertical residuals around 3–4 m for the product. The global float files are multi-gigabyte, which is why v0.5.0 does not fetch them automatically on first launch.

## 3. Model inventory

### 3.1 Celestial geometry

For the selected lunar surface location, LunaSight asks JPL Horizons for observer-centred Sun and Earth azimuth/elevation. Earth range is used when returned by the Horizons table. The next 24 hours are sampled every 30 minutes.

Current model boundary:
- The apparent centre of each body is compared with the reference or terrain horizon.
- The full angular diameter of the Sun/Earth is not yet ray-traced for partial visibility.
- Rise/set times are sampled, not event-refined; the 30-minute interval limits time resolution.
- The current live ephemeris provider is Horizons. NAIF SPICE is listed as a future independent validation path, not as a current engine dependency.

### 3.2 Terrain and local horizon

When the selected coordinate is covered by a loaded high-resolution NASA south-polar terrain grid, LunaSight samples the surrounding elevation along an azimuth ray to estimate the terrain horizon. The local horizon can then adjust the 24-hour visibility percentages.

If there is no suitable high-resolution terrain for the selected point, the programme uses the smooth reference horizon for visibility percentages. The global 4/16 px-per-degree LOLA model may still show a real coarse elevation patch in the astronaut preview, but it is deliberately not treated as an accurate local horizon mask.

This distinction is important: a global terrain grid is useful for choosing a region and viewing broad relief, but local crater rims, small ridges, boulders and landing-scale slope conditions need much finer elevation data.

### 3.3 Sunlight, irradiance and lux

The app calculates a simple direct-beam estimate for a horizontal surface:

- Solar irradiance: `1361 W/m² × sin(elevation)` when the Sun is above the modeled horizon; otherwise `0 W/m²`.
- Photopic illuminance: `127,000 lux × sin(elevation)` when the Sun is above the modeled horizon; otherwise `0 lux`.

These values are clear-sky geometric estimates based on the solar elevation. The Moon has no Earth-like atmosphere to diffuse sunlight. However, the current model does not include surface reflectance, detailed photometric scattering, Earthshine, dust, visor transmission, local hardware shadowing, solar-array tilt or electrical conversion efficiency. The POV rendering is therefore an illustrative terrain-lighting view, not a calibrated astronaut camera simulation.

Lux and radio power are different physical quantities and are calculated separately.

### 3.4 Earth visibility and radio estimate

The radio panel calculates a free-space received-power reference using:

`Pr (dBW) = EIRP (dBW) − free-space path loss (dB) + receiver gain (dBi) − other losses (dB)`

The selected S/X-band examples use published DSN ground-station EIRP profiles. Earth–Moon distance comes from Horizons when available; the panel allows the reference assumptions to be edited. A terrain horizon can suppress the direct Earth path when high-resolution local terrain covers the selected point.

This is not a complete communications link budget. A real design also requires the spacecraft's actual antenna gain/pattern, receiver G/T or noise temperature, bandwidth, data rate, modulation/coding, antenna pointing, polarization and implementation losses. The chosen DSN example is not evidence that every NASA or commercial lander uses that station or transmitter configuration.

### 3.5 Suitability indicator

The indicator is a transparent educational screen:

- **Major constraint:** sampled sunlight below 20% or Earth visibility below 10%.
- **Promising geometry:** sunlight ≥70%, Earth visibility ≥50%, simultaneous visibility ≥30%, and high-resolution local NASA LOLA terrain loaded for the selected point.
- **Compare alternatives:** an analysed site that does not meet the two rules above.
- **Needs more data:** no valid ephemeris analysis has been run.

These thresholds are LunaSight prototype screening values, not official NASA requirements. They do not evaluate slope, boulder density, landing ellipse, plume interaction, thermal control, power-storage sizing, safe touchdown areas, mission constraints or operational rules. A favourable screen is not a landing approval.

## 4. Why site-dependent results change

1. **Local horizon:** A crater rim or ridge can block the Sun or Earth even when a smooth-sphere calculation says the body is above the reference horizon.
2. **Lunar curvature:** The visible sky changes with position and observer height. The antenna height may differ from an astronaut's eye height.
3. **Sun geometry:** Small latitude/longitude or time changes near the poles can change the solar elevation and the duration of illumination.
4. **Earth geometry:** Earth is not overhead at every lunar site. Its elevation and visibility depend on the selected surface location, lunar orientation and terrain horizon.
5. **Radio frequency and range:** At the same distance, free-space path loss grows with frequency. Earth–Moon range also varies over time. Antenna gain and pointing are central to a real link.
6. **Data resolution:** A 7.5 km or 1.9 km global pixel cannot represent every local ridge, crater rim or boulder. Fine-scale horizon conclusions need local higher-resolution terrain.

## 5. Coverage promise and limits

**All lunar surface coordinates can be selected in the UI.** The science coverage is layered rather than uniform:

- Global 4/16 px-per-degree LOLA is available for whole-Moon broad relief.
- High-detail terrain is integrated for the south-polar regional model and six named 5 m site tiles.
- NASA SLDEM2015 offers materially finer terrain across much of the mid-latitude Moon, but its multi-gigabyte global files are not automatically downloaded or yet wired into the v0.5.0 local horizon pipeline.
- There is not yet an equivalent high-resolution local horizon product integrated for every northern polar, far-side and equatorial site.

The correct application behaviour is to keep the location selectable while visibly identifying when high-resolution terrain is missing. LunaSight should never silently treat a coarse global preview as a precise local hazard or horizon model.

## 6. Primary sources

1. **JPL Horizons API:** https://ssd-api.jpl.nasa.gov/doc/horizons.html
2. **NASA/GSFC SVS — CGI Moon Kit:** https://svs.gsfc.nasa.gov/4720
3. **NASA PGDA — High-resolution Lunar Topography (SLDEM2015):** https://pgda.gsfc.nasa.gov/products/54
4. **NASA/GSFC PGDA — A New View of the Lunar South Pole from LOLA:** https://pgda.gsfc.nasa.gov/products/90
5. **NASA Moon Trek:** https://trek.nasa.gov/moon/
6. **LROC WMS map and products:** https://data.lroc.imldi.com/lroc
7. **NASA HLS RF ConOps:** https://ntrs.nasa.gov/api/citations/20250003508/downloads/HLS-CONOP-008_Sustained_Phase_HLS_RF_ConOps_Rev_A.pdf
8. **NASA/JPL DSN Services Catalog:** https://www.nasa.gov/wp-content/uploads/2023/09/dsn-services-catalog.pdf
9. **JPL DSN Frequency and Channel Assignments:** https://deepspace.jpl.nasa.gov/dsndocs/810-005/201/201D.pdf
10. **NAIF SPICE Toolkit:** https://naif.jpl.nasa.gov/naif/

## 7. Validation status for v0.5.0

- 23 automated tests pass.
- A headless Tk desktop smoke test passed, both before and after injecting a synthetic ephemeris result into the UI.
- Live JPL API access and NASA asset downloads were not testable from the release-building environment. The first user run needs an internet connection to verify those network-backed services.
