from __future__ import annotations

from .science import (
    DSNProfile, MEAN_EARTH_MOON_RANGE_KM, free_space_path_loss_db,
)


def build_session_report(
    scenario, result, profile: DSNProfile, receiver_gain: str = "0",
    losses: str = "2", range_km: str = "384400", *,
    receiver_height_m: str = "1.7",
    lux: float | None = None, irradiance: float | None = None, rf=None,
    sunlight_fraction: float | None = None,
    earth_visibility_fraction: float | None = None,
    simultaneous_fraction: float | None = None,
    suitability: str | None = None, suitability_note: str | None = None,
    sun_horizon_deg: float | None = None, earth_horizon_deg: float | None = None,
    terrain_source: str | None = None,
) -> str:
    try:
        gain = float(receiver_gain)
        loss = float(losses)
        distance = float(range_km)
        antenna_height = float(receiver_height_m)
    except ValueError:
        gain, loss, distance, antenna_height = 0.0, 2.0, MEAN_EARTH_MOON_RANGE_KM, 1.7
    if result is not None and getattr(result, "earth_range_km", None):
        distance = float(result.earth_range_km)
    fspl = free_space_path_loss_db(profile.frequency_hz, distance)
    pr_dbm = profile.eirp_dbw - fspl + gain - loss + 30.0
    if rf is not None:
        fspl = rf.free_space_path_loss_db
        pr_dbm = rf.received_power_dbm_if_los
        calculation_range = rf.range_km
    else:
        calculation_range = distance
    wavelength_cm = profile.wavelength_m * 100.0
    if result is None:
        line_of_sight_label = "BİLİNMİYOR (JPL analizi yok)"
    elif rf is not None:
        line_of_sight_label = (
            "DÜNYA MERKEZİ MODELLENEN UFUK ÜZERİNDE"
            if rf.line_of_sight
            else "DÜNYA MERKEZİ MODELLENEN UFUK ALTINDA"
        )
    else:
        line_of_sight_label = (
            "DÜNYA MERKEZİ İDEAL UFUK ÜZERİNDE"
            if result.earth_elevation_deg > 0
            else "DÜNYA MERKEZİ İDEAL UFUK ALTINDA"
        )
    if result is None:
        rf_interpretation = (
            "Anlık geometri bilinmiyor; bu değer yalnızca engelsiz yol "
            "referansıdır, bağlantı göstergesi değildir."
        )
    elif rf is not None and not rf.line_of_sight:
        rf_interpretation = (
            "Dünya merkezi modellenen ufkun altındadır. Serbest-uzay güç "
            "değeri varsayımsal engelsiz yol referansıdır; gerçek alınan "
            "sinyal değildir. Görünen Dünya kenarı, DSN istasyon konumu, "
            "kırınım ve yansımalar modellenmez."
        )
    else:
        rf_interpretation = (
            "Serbest-uzay güç değeri engelsiz yol referansıdır; belirli "
            "istasyona görüşü, alıcı hassasiyetini veya bağlantı marjını "
            "kanıtlamaz."
        )
    site_line = "Görev koordinatı seçilmedi."
    geometry = "Canlı JPL Horizons sonucu bulunmuyor."
    if scenario is not None:
        site_line = (f"{scenario.site_name} — enlem {scenario.latitude_deg:.6f}°, "
                     f"doğu-pozitif boylam {scenario.longitude_deg:.6f}°, "
                     f"{scenario.date_time_utc:%Y-%m-%d %H:%M} UTC")
    if result is not None:
        sun_fraction = result.sunlight_fraction if sunlight_fraction is None else sunlight_fraction
        earth_fraction = result.earth_visibility_fraction if earth_visibility_fraction is None else earth_visibility_fraction
        both_fraction = result.simultaneous_visibility_fraction if simultaneous_fraction is None else simultaneous_fraction
        range_line = (f"- JPL Horizons anlık Dünya menzili: {result.earth_range_km:,.1f} km\n"
                      if getattr(result, "earth_range_km", None) else
                      "- JPL Horizons menzili alınamadı; RF hesabında kullanıcı/ortalama menzil değeri kullanıldı.\n")
        geometry = (
            f"- Güneş azimut/yükseklik: {result.solar_azimuth_deg:.3f}° / {result.solar_elevation_deg:.3f}°\n"
            f"- Dünya azimut/yükseklik: {result.earth_azimuth_deg:.3f}° / {result.earth_elevation_deg:.3f}°\n"
            + range_line +
            f"- Sonraki 24 saatte örneklenmiş Güneş görünürlüğü: %{sun_fraction*100:.2f}\n"
            f"- Sonraki 24 saatte yerel ufuk üzerinde Dünya görünürlüğü: %{earth_fraction*100:.2f}\n"
            f"- Güneş ve Dünya'nın aynı anda görünür olduğu örnekler: %{both_fraction*100:.2f}\n"
        )

    return f'''# LunaSight — Ay Güney Kutbu Aydınlanma ve RF İletişim Raporu

## 1. Amaç ve kapsam

Bu rapor, LunaSight masaüstü prototipindeki ışık ve Dünya'dan Ay'a radyo bağlantısı modellerini açıklar. Hesaplar NASA/JPL tarafından yayımlanan veri ve teknik aralıklara dayanır; ancak uygulama bir NASA görev tasarım aracı, uçuş yazılımı, iniş sertifikasyonu veya doğrulanmış uçtan uca iletişim bağlantı bütçesi değildir.

## 2. Seçili senaryo

{site_line}

## 3. Güneş ve Dünya geometrisi

{geometry}

JPL Horizons, seçilen Ay yüzeyi koordinatından görülen Güneş ve Dünya'nın topocentric azimut/yükseklik açılarını sağlar. Uygulamanın 24 saatlik görünürlük oranları 30 dakikalık örneklerden türetilir. NASA LOLA arazi modeli yüklendiğinde azimut yönündeki yerel ufuk, örneklenmiş arazi yüksekliklerinden yaklaşık olarak hesaplanır. LOLA yüklenmemişse ideal düz ufuk (0°) kullanılır.

## 4. Ay çevresi haberleşme bantları, dalga boyları ve verici gücü

Ay yüzeyiyle Dünya arasındaki bağlantı, NASA HLS-CONOP-008 (2025) Tablo 4-1 ve JPL DSN frekans belgelerinde **near-Earth / lunar-region** olarak listelenen tahsislerle değerlendirilmelidir. Derin uzay uplink bantları (S: 2110–2120 MHz, X: 7145–7190 MHz, Ka: 34.2–34.7 GHz) Ay yüzeyi bağlantısı için varsayılan alınmamalıdır.

| Bant | Dünya → Ay yüzeyi uplink | Ay yüzeyi → Dünya downlink | Uplink merkez frekansı | Dalga boyu |
|---|---:|---:|---:|---:|
| S | 2025–2110 MHz | 2200–2290 MHz | 2067.5 MHz | 14.50 cm |
| X | 7190–7235 MHz | 8450–8500 MHz | 7212.5 MHz | 4.16 cm |
| K | 22.55–23.15 GHz | 25.5–27.0 GHz | 22.85 GHz | 1.31 cm |

Dalga boyları `λ = c/f` ile uplink orta frekansından hesaplanır. Bunlar bölgesel frekans önerileri/tahsisleridir; belirli bir CLPS iniş aracının gerçekten hangi frekansı kullandığını göstermez. NASA HLS RF ConOps, Ay yüzeyine giden S/X/K uplink aralıklarını ve Ay yüzeyinden Dünya'ya giden karşılık gelen downlink aralıklarını ayrıca listeler. 2025–2110 MHz bandında Ay görevleri için dikkatli frekans koordinasyonu gerekir.

### 4.1 DSN yer istasyonu örnekleri ve EIRP

JPL DSN 810-005 Module 104 Rev. N, **near-Earth** S-band için 34 m anten örneklerinde 20 kW vericiyle en yüksek EIRP'yi 128.3 dBm (98.3 dBW), 250 W konfigürasyonda 108.9 dBm (78.9 dBW) olarak verir. Aynı belgenin X-band tablosu near-Earth bandında 20 kW için yaklaşık 139.5–139.7 dBm (109.5–109.7 dBW), DSS-26 80 kW seçeneği için 145.3 dBm (115.3 dBW) bildirir. LunaSight profilleri bu nedenle eski derin-uzay nominal frekanslarını değil, 2067.5 MHz ve 7212.5 MHz merkezlerini kullanır.

| Profil (örnek yer istasyonu) | Verici çıkışı | Near-Earth EIRP | Merkez frekansı |
|---|---:|---:|---:|
| S · DSS-24 · 34 m | 20 kW | 98.3 dBW (128.3 dBm) | 2067.5 MHz |
| S · DSS-26 · 34 m | 250 W | 78.9 dBW (108.9 dBm) | 2067.5 MHz |
| X · DSS-24 · 34 m | 20 kW | 109.7 dBW (139.7 dBm) | 7212.5 MHz |
| X · DSS-26 · 34 m | 80 kW | 115.3 dBW (145.3 dBm) | 7212.5 MHz |

**K-band uyarısı:** NASA DSN Services Catalog, 22.55–23.15 GHz near-Earth K uplink'i ve 34 m BWG / 250 W için 127.7 dBW EIRP özet satırını yayımlar. Ancak bu EIRP değeri bu rapordaki antene-özel mühendislik tablolarıyla doğrulanmadığından uygulamanın otomatik alınan-güç profiline eklenmemiştir. K bandı frekans ve dalga boyu olarak raporlanır; görev/istasyon doğrulaması olmadan alınan güç iddiası üretilmez.

EIRP, yalnızca vericinin fiziksel watt değeri değildir; verici gücü, anten kazancı ve ilgili kayıpların birleşik etkisini ana huzme yönünde ifade eder. DSN katalog gücü her NASA/CLPS aracı için geçerli değildir; bu profiller belirli DSN yer istasyonu örnekleridir. DSN kaynakları ayrıca near-Earth X-band EIRP'nin antene göre katalog özetinden daha düşük olabileceğini ve ayrıntılı istasyon dokümanına bakılması gerektiğini belirtir.

## 5. Dünya → Ay alınan sinyal gücü modeli

İlk mertebe serbest-uzay bağlantı denklemimiz:

`FSPL(dB) = 20 log10(4πR/λ)`

`Pr(dBW) = EIRP(dBW) − FSPL(dB) + Grx(dBi) − Lother(dB)`

`Pr(dBm) = Pr(dBW) + 30`

Burada:

- `R`: Dünya–Ay bağlantı mesafesi (metre). Uygulama JPL Horizons Observer quantity 20 ile anlık gözlemci-hedef menzilini ister; API menzil sağlamazsa 384.400 km ortalama varsayımına döner.
- `λ`: seçilen uplink dalga boyu.
- `EIRP`: DSN hizmet kataloğundan seçilen yer istasyonu EIRP değeri.
- `Grx`: Ay iniş aracının alıcı anten kazancı. Varsayılan 0 dBi izotropik referanstır; belirli bir CLPS aracının anten özelliği olduğu iddia edilmez.
- `Lother`: ek kayıp payı. Varsayılan 2 dB yalnızca prototip varsayımıdır.

Uygulamadaki otomatik EIRP profilleri yalnızca S ve X near-Earth örnekleridir. K-bandı da Ay bölgesi uplink tahsisi olarak gösterilir; ancak istasyon-özel doğrulanmış EIRP profili olmadığı için otomatik Pr hesabına sokulmaz. Ay görevi için Ka-band derin-uzay uplink profili kullanılmaz.

### 5.1 Ortalama mesafede örnek hesap

Aşağıdaki tablo 384.400 km, 0 dBi alıcı anten kazancı ve 2 dB ek kayıp varsayar. Sayılar serbest-uzay referansıdır; Dünya'nın yerel ufuk tarafından kapatılmadığı durum içindir.

| DSN örnek profili | EIRP | Frekans | FSPL | Tahmini alınan güç |
|---|---:|---:|---:|---:|
| S-band DSS-24 / 20 kW | 98.3 dBW | 2.0675 GHz | {free_space_path_loss_db(2.0675e9, MEAN_EARTH_MOON_RANGE_KM):.2f} dB | {98.3-free_space_path_loss_db(2.0675e9, MEAN_EARTH_MOON_RANGE_KM)-2+30:.2f} dBm |
| X-band DSS-24 / 20 kW | 109.7 dBW | 7.2125 GHz | {free_space_path_loss_db(7.2125e9, MEAN_EARTH_MOON_RANGE_KM):.2f} dB | {109.7-free_space_path_loss_db(7.2125e9, MEAN_EARTH_MOON_RANGE_KM)-2+30:.2f} dBm |
| X-band DSS-26 / 80 kW | 115.3 dBW | 7.2125 GHz | {free_space_path_loss_db(7.2125e9, MEAN_EARTH_MOON_RANGE_KM):.2f} dB | {115.3-free_space_path_loss_db(7.2125e9, MEAN_EARTH_MOON_RANGE_KM)-2+30:.2f} dBm |

Bu güç değerleri alıcı hassasiyeti veya bağlantı marjı değildir. Alıcı gürültü sıcaklığı, G/T, kanal bant genişliği, veri hızı, modülasyon/kodlama, polarizasyon uyumsuzluğu, anten yönelimi ve gerçek uzay aracı donanımı bilinmeden “bağlantı kapanıyor” sonucu çıkarılamaz.

## 5.2 Seçili senaryonun anlık sonuçları

{f"- Tahmini doğrudan yatay yüzey aydınlanması: {lux:,.0f} lux\n" if lux is not None else "- Anlık lux sonucu hesaplanmadı.\n"}{f"- Doğrudan güneş ışınımı: {irradiance:,.1f} W/m²\n" if irradiance is not None else "- Anlık güneş ışınımı sonucu hesaplanmadı.\n"}{f"- Güneş yönündeki yerel arazi ufku: {sun_horizon_deg:.2f}°\n" if sun_horizon_deg is not None else ""}{f"- Dünya yönündeki yerel arazi ufku: {earth_horizon_deg:.2f}°\n" if earth_horizon_deg is not None else ""}{f"- Ön saha göstergesi: {suitability}\n" if suitability else "- Ön saha göstergesi: hesaplanmadı.\n"}{f"- Gösterge açıklaması: {suitability_note}\n" if suitability_note else ""}{f"- Yükseklik veri kaynağı: {terrain_source}\n" if terrain_source else ""}
RF modelindeki seçili profil: **{profile.label}**. Frekans {profile.frequency_hz/1e9:.5f} GHz, dalga boyu {wavelength_cm:.3f} cm, EIRP {profile.eirp_dbw:.1f} dBW. Alıcı anten kazancı {gain:.1f} dBi, varsayılan arazi ufuk gözlemci yüksekliği {antenna_height:.1f} m, ek kayıp {loss:.1f} dB.

- FSPL: {fspl:.2f} dB
- RF hesabında kullanılan menzil: {calculation_range:,.2f} km
- Engelsiz yol varsayımsal alınan güç referansı: {pr_dbm:.2f} dBm
- Dünya merkezi / modellenen ufuk kontrolü: {line_of_sight_label}

{rf_interpretation}

## 6. Ay'daki farklı konumlarda RF gücü neden değişir?

1. **En önemli konum etkisi arazi görüş hattıdır.** Krater duvarı veya sırt, Dünya'yı kapatırsa doğrudan bağlantı kesilir. Serbest-uzay denklemi bir güç seviyesi üretse de bu durumda gerçek doğrudan sinyal yolu yoktur.
2. **Dünya'nın azimut ve yükseklik açısı değişir.** Düşük yükseklikteki Dünya, yerel krater kenarları ve sırtlar tarafından daha kolay örtülür. Anten de Dünya yönüne çevrilmelidir.
3. **Dünya–Ay uzaklığı zamanla değişir.** Serbest-uzay kaybı mesafenin logaritmasıyla artar. JPL Horizons quantity 20 menzili verirse RF hesabı seçilen tarih/saatteki bu değeri kullanır; veri dönmezse 384.400 km yalnızca ortalama menzil yedeğidir.
4. **Yüzey koordinatının Ay merkezine göre mesafeye etkisi küçüktür.** Ay yarıçapı, Dünya–Ay uzaklığına kıyasla çok küçüktür. Bu nedenle tek başına iniş koordinatının menzile etkisi genellikle birkaç yüzde bir dB düzeyindedir; bir krater sırtının görüş hattını tamamen kapatması çok daha önemlidir.
5. **Anten deseni ve yönelimi önemlidir.** Alıcı kazancı frekansa, anten türüne, gövdeye göre yönelime, polarizasyona ve Dünya'nın anten ana huzmesine göre açısına bağlıdır.
6. **Yüksek frekanslar daha yüksek serbest-uzay kaybı getirir.** X ve Ka bantlarında yönlü, yüksek kazançlı antenlerle bu telafi edilebilir; ancak anten yönlendirme hassasiyeti artar. Dünya atmosferindeki yağmur ve gaz kayıpları da özellikle yüksek bantlarda önem kazanır.

Bu nedenle konumlar arasında ölçülen RF farkını yalnızca koordinata bağlamak doğru değildir. Öncelik: Dünya görüş hattı ve yerel ufuk; ardından anten örüntüsü, link konfigürasyonu ve gerçek menzil.

## 7. Ay yüzeyi aydınlanması ve lux

NASA, 1 AU'daki toplam güneş ışınımını yaklaşık 1361 W/m² olarak verir. Yatay bir yüzey için Güneş yüksekliği `h` olduğunda doğrudan ışınımın ilk yaklaşımı:

`Esolar(W/m²) ≈ 1361 × max(0, sin(h))`, yalnızca `h > hterrain` ise; aksi durumda 0.

LunaSight, görsel açıklama amacıyla normal gelişte yaklaşık 127.000 lux doğrudan güneş aydınlanması varsayar. `h` Güneş'in geometrik ufuk yüksekliği, `hterrain` Güneş azimutundaki arazi ufuk açısıdır. Arazi ufku yalnızca Güneş'i bloke edip etmediğini belirler; ışın yüzeye ulaştığında yatay yüzeydeki izdüşüm `sin(h)` ile hesaplanır:

`Illuminance(lux) ≈ 127000 × max(0, sin(h))`, yalnızca `h > hterrain` ise; aksi durumda 0.

Bu, yatay yüzey üzerindeki doğrudan ışık için yaklaşık fotopik modeldir; astronot vizöründe ölçülen lux, gözün algısı veya kamera pozlaması değildir. Gerçek fotopik lux için Güneş'in spektral ışınımının gözün fotopik duyarlılık eğrisiyle integrali gerekir.

Güneş ufka yaklaştığında yatay yüzeye düşen enerji sinüs faktörü nedeniyle azalır. Ay'da atmosferik saçılma olmadığından doğrudan güneş alan alanlar ve gölgeler arasındaki kontrast çok yüksektir. Güneş ufukta kalırken uzak sırtlar bile uzun gölgeler oluşturabilir.

**Earthshine:** NASA'nın keşif sistemleri aydınlatma rehberi, Dünya'dan yansıyan ışığın Ay gölgelerinde ikincil bir aydınlatma kaynağı olabileceğini; miktarın Dünya'nın fazına ve yerel yüzey koşullarına bağlı olduğunu belirtir. Güney Kutbu'nda bu katkı daha zayıf ve değişkendir. Mevcut lux kartı Earthshine, yüzey yansıtıcılığı veya yamaç yönelimini henüz eklemez; yalnızca doğrudan Güneş bileşenini verir.

Lux ile RF sinyal gücü farklı fiziksel büyüklüklerdir ve birbirinin yerine kullanılamaz. Arayüz bunları ayrı hesaplama motorlarında tutar.

## 8. İniş uygunluğu göstergesi nasıl yorumlanmalı?

Uygulamadaki “Geometrically Promising / Trade Study Required / High Constraint” etiketi yalnızca 24 saatlik örneklenmiş Güneş ve Dünya görünürlüğü oranlarına dayanan bir **ön taramadır**. “Geometrically Promising” etiketi için prototip eşiği Güneş görünürlüğü ≥ %70, Dünya görünürlüğü ≥ %50, eşzamanlı görünürlük ≥ %30 ve seçili koordinatı gerçekten kapsayan NASA LOLA arazi verisinin mevcut olmasıdır. Güneş görünürlüğü <%20 veya Dünya görünürlüğü <%10 ise “High Constraint” gösterilir; diğer durumlarda “Trade Study Required” görünür. Bu eşikler görev standardı değildir ve etiket gerçek iniş emniyeti değerlendirmesi sayılmaz.

Gerçek iniş uygunluğu için ayrıca eğim, pürüzlülük, taş/kaya tehlikeleri, iniş elipsi, navigasyon belirsizliği, iniş motoru toz etkisi, termal koşullar, güç sistemi, haberleşme anteni örüntüsü, veri hızı ve görev gereksinimleri modellenmelidir.

## 9. Bu sürümde uygulanan veri ve model kapsamı

- **JPL Horizons:** seçilen Ay koordinatından Güneş ve Dünya'nın topocentric azimut/yükseklik açıları; Dünya için quantity 20 menzil ve menzil hızı talebi.
- **NASA/GSFC PGDA LOLA:** `LDEM_80S_80MPP_ADJ.TIF`, bulut-uyumlu GeoTIFF olarak isteğe bağlı yükleme; görünüm için azaltılmış çözünürlükte örneklenir.
- **3D site seçimi:** Güney kutbu topografik görünümüne tıklanarak koordinat belirleme; tıklama ile enlem/boylam alanları senkronize edilir.
- **Astronot POV:** yaklaşık 1,7 m göz yüksekliği konseptiyle yerel arazi görünümü; yüzey aydınlatması Güneş'in JPL azimut/yüksekliğine göre yönlendirilir ve yaklaşık doğrudan lux ile ölçeklenir. Bu bir görselleştirme, fotogerçekçi render veya vizör kalibrasyonu değildir.
- **RF:** DSN katalog EIRP + JPL menzili (varsa) + serbest-uzay yol kaybı + ayarlanabilir referans alıcı kazancı, anten yüksekliği ve ek kayıp; LOLA ufku doğrudan görüşü maskeleyebilir. Lux RF gücünü değiştirmez.
- **Lux:** doğrudan güneş ışığının yatay yüzeye geliş açısına dayalı yaklaşık fotopik değer.

## 10. Kaynakça

1. NASA/JPL, *Deep Space Network Services Catalog*, 820-100 Rev. H (2022), DSN hizmet bantları ve EIRP örnekleri: https://www.nasa.gov/wp-content/uploads/2023/09/dsn-services-catalog.pdf
2. NASA, *HLS Sustaining Phase RF Communications Concept of Operations*, HLS-CONOP-008 Rev. A (21 Mar 2025), Table 4-1 Ay yüzeyi uplink/downlink aralıkları: https://ntrs.nasa.gov/api/citations/20250003508/downloads/HLS-CONOP-008_Sustained_Phase_HLS_RF_ConOps_Rev_A.pdf
3. JPL DSN, *34-m BWG Stations Telecommunications Interfaces*, 810-005 Module 104 Rev. N (2021), S/X near-Earth verici gücü ve EIRP: https://deepspace.jpl.nasa.gov/dsndocs/810-005/104/104N.pdf
4. JPL DSN, *Frequency and Channel Assignments*, 810-005 Module 201 Rev. D (2020): https://deepspace.jpl.nasa.gov/dsndocs/810-005/201/201D.pdf
5. NASA SmallSat Institute, *Communications*: https://www.nasa.gov/smallsat-institute/sst-soa/soa-communications/
6. NASA/GSFC PGDA, *A New View of the Lunar South Pole from LOLA*: https://pgda.gsfc.nasa.gov/products/90
7. NASA/JPL, *Horizons System Manual*: https://ssd.jpl.nasa.gov/horizons/manual.html
8. NASA, *Exploration Systems Exterior Lighting Design Guidance*, NESC-RP-21-01706: https://ntrs.nasa.gov/api/citations/20240016463/downloads/1-3-25%2020240016463.pdf
9. NASA, *Climate and Earth's Energy Budget* (TSI context): https://science.nasa.gov/earth/earth-observatory/climate-and-earths-energy-budget/
10. NASA OCHMO, *Artemis Lighting Considerations*, NASA-STD-3001 Technical Brief (2023): https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-001-artemis-lighting-considerations.pdf
11. Barker et al. (2023), LOLA south-polar DEM dataset paper: https://doi.org/10.3847/PSJ/acf3e1
'''
