# LunaSight — NASA Ay Haberleşmesi, RF Bağlantısı ve Yüzey Aydınlatması Teknik Raporu

**Sürüm:** LunaSight Desktop v0.4.0  
**Kapsam:** Ay Güney Kutbu'nda iniş alanı seçimi, astronot POV aydınlatma taslağı ve Dünya→Ay doğrudan RF uplink ön değerlendirmesi  
**Önemli:** Bu rapor ve yazılım eğitim/ön tasarım amaçlıdır. NASA onaylı görev analizi, iniş emniyeti sertifikası veya doğrulanmış uçtan uca haberleşme bütçesi değildir.

## 1. Özet

LunaSight, seçilen Ay koordinatında JPL Horizons ile Güneş ve Dünya'nın azimut/yükseklik açılarını hesaplar; NASA/GSFC LOLA sayısal yükseklik modeli yüklendiğinde yerel arazi ufkunu yaklaşık olarak değerlendirir. POV görüntüsünün doğrudan aydınlatması, yatay yüzeye gelen güneş ışığından türetilen yaklaşık lux ve W/m² değerleriyle ölçeklenir.

Dünya'dan Ay'a RF gücü ayrı bir fiziksel modeldir. Yüzeydeki lux, RF sinyalinin gücünü artırmaz veya azaltmaz. RF hesabında frekans/dalga boyu, örnek yer istasyonunun EIRP'si, seçilen zaman için JPL Horizons topomerkezli Dünya menzili, varsayılan alıcı anten kazancı ve ek kayıplar kullanılır. Ay yüzeyindeki konumun menzile etkisi çok küçük; yerel ufuk ve arazi ise merkez-yönü görünürlük için önemlidir.

## 2. Ay bölgesi için uygun frekanslar

NASA'nın *HLS Sustaining Phase RF Communications Concept of Operations* belgesindeki Tablo 4-1, Dünya→Ay yüzeyi ile Ay yüzeyi→Dünya bağlantıları için aşağıdaki lunar-region frekanslarını önerir. JPL DSN frekans dokümanı da bunları near-Earth bandı olarak ayırır. Ay bağlantısı için derin-uzay S/X/Ka aralıkları otomatik olarak kullanılmamalıdır.

| Bant | Dünya → Ay yüzeyi uplink | Ay yüzeyi → Dünya downlink | Uplink merkez frekansı | Uplink dalga boyu |
|---|---:|---:|---:|---:|
| S | 2025–2110 MHz | 2200–2290 MHz | 2067.5 MHz | 14.50 cm |
| X | 7190–7235 MHz | 8450–8500 MHz | 7212.5 MHz | 4.16 cm |
| K | 22.55–23.15 GHz | 25.5–27.0 GHz | 22.85 GHz | 1.31 cm |

Dalga boyu `λ = c/f` formülüyle hesaplanır. Tablodaki dalga boyları uplink orta frekansına göredir. Downlink frekansları farklı olduğundan aynı dalga boyuna sahip değildir.

**Frekans koordinasyonu:** NASA HLS ConOps, 2025–2110 MHz bandının Ay bölgesindeki görevlerce kullanımında LEO ve L1/L2 uzay araçlarına girişimi azaltmak için dikkatli koordinasyon gerektiğini özellikle not eder. Frekans aralığının listelenmesi, belirli bir CLPS aracının o bandı kullandığını veya o frekansın tek başına her görev için onaylandığını göstermez.

## 3. Yer istasyonu verici gücü ve EIRP

RF bağlantı hesabında iki farklı kavramı ayırmak gerekir:

- **RF verici çıkış gücü (W):** Vericinin fiziksel olarak ürettiği radyo frekansı gücü.
- **EIRP (dBW):** Verici çıkışı, anten kazancı ve ilgili kayıpların ana huzme yönündeki birleşik eşdeğeri. Serbest-uzay alıcı güç hesabının başlangıç değeri EIRP'dir.

JPL DSN 810-005 Module 104 Rev. N, 34 m anten örnekleri için near-Earth S/X verici tabloları verir:

| Bant / DSN örneği | RF verici çıkışı | Near-Earth maksimum EIRP | Kaynakta EIRP birimi |
|---|---:|---:|---:|
| S · DSS-24 / 34 m | 20 kW | 128.3 dBm = 98.3 dBW | 128.3 dBm |
| S · DSS-26 / 34 m | 250 W | 108.9 dBm = 78.9 dBW | 108.9 dBm |
| X · DSS-24 / 34 m | 20 kW | 139.7 dBm = 109.7 dBW | 139.7 dBm |
| X · DSS-26 / 34 m | 80 kW | 145.3 dBm = 115.3 dBW | 145.3 dBm |

Bu değerler belirli DSN anten/verici örnekleridir; tüm DSN istasyonları, NASA görevleri veya ticari CLPS araçları için tek tip değer değildir. EIRP azami değeri istasyon, frekans, anten konfigürasyonu, yükseliş açısı ve verici konfigürasyonuna göre değişebilir.

### K-band notu

NASA DSN Services Catalog near-Earth K-band uplink frekansını 22.55–23.15 GHz olarak listeler ve özet hizmet tablosunda 34 m BWG / 250 W için 127.7 dBW EIRP satırı verir. Ancak bu değer istasyon-özel teknik parametrelerle burada bağımsız olarak uzlaştırılamadığından LunaSight v0.4.0 otomatik RF profilinde kullanılmaz. K-band frekansı ve dalga boyu raporlanır; görev/istasyon-özel teknik doğrulama olmadan alınan güç tahmini üretilmez.

### Deep-space bantları neden kullanılmıyor?

JPL'nin deep-space nominal değerleri S uplink 2115 MHz, X uplink 7167.5 MHz ve Ka uplink 34.45 GHz'dir. Bunlar DSN el kitabında ayrı olarak “deep-space” diye sınıflanır. Ay yüzeyiyle haberleşme için NASA HLS ConOps'un lunar-region S/X/K uplink aralıkları esas alınmıştır. Bu nedenle eski prototipteki 2.115 GHz, 7.1675 GHz ve 34.45 GHz profilleri v0.4.0'dan çıkarılmıştır.

## 4. Dünya→Ay alınan güç modeli

İlk mertebe serbest-uzay yol kaybı:

`FSPL(dB) = 20 log10(4πR/λ)`

Alıcıda hesaplanan referans güç:

`Pr(dBW) = EIRP(dBW) − FSPL(dB) + Grx(dBi) − Lother(dB)`

`Pr(dBm) = Pr(dBW) + 30`

- `R`: seçilen epokta JPL Horizons'tan gelen topomerkezli Dünya menzili; veri yoksa prototip 384.400 km ortalama menzil varsayımına döner. Teknik ayarlardaki kullanıcı girdisi hesabı değiştirebilir.
- `λ`: seçilen Dünya→Ay uplink dalga boyu.
- `EIRP`: DSN örnek yer istasyonu konfigürasyonundan alınır.
- `Grx`: Ay iniş aracının alıcı anten kazancı. Varsayılan 0 dBi, izotropik referanstır; gerçek CLPS anteni olduğu iddia edilmez.
- `Lother`: varsayılan 2 dB prototip kayıp payıdır; görev-özel ölçüm değildir.

### 4.1 Örnek hesap

384.400 km menzil, 0 dBi alıcı kazancı ve 2 dB ek kayıp varsayımıyla:

| Profil | EIRP | Frekans | FSPL | Tahmini Pr |
|---|---:|---:|---:|---:|
| S / DSS-24 / 20 kW | 98.3 dBW | 2.0675 GHz | 210.45 dB | −84.15 dBm |
| S / DSS-26 / 250 W | 78.9 dBW | 2.0675 GHz | 210.45 dB | −103.55 dBm |
| X / DSS-24 / 20 kW | 109.7 dBW | 7.2125 GHz | 221.31 dB | −83.61 dBm |
| X / DSS-26 / 80 kW | 115.3 dBW | 7.2125 GHz | 221.31 dB | −78.01 dBm |

Bunlar engelsiz yol için serbest-uzay referans güçleridir; gerçek alınan sinyal, alıcı hassasiyeti ya da link marjı değildir. Bir alıcının sinyali çözebilmesi için gürültü sıcaklığı, G/T, bant genişliği, modülasyon, kodlama, veri hızı, sembol hızı, polarizasyon ve anten yönelimi bilinmelidir. Uygulama bu girdiler olmadan “iletişim başarılı” dememelidir.

## 5. RF gücü Ay'daki konuma göre neden değişir?

1. **Dünya merkezi / yerel ufuk kontrolü:** Krater kenarı, sırt veya yakındaki yükselti Dünya merkezinin yönünü kapatabilir. Bu geometri bir istasyon-özel LOS testi değildir: uygulama belirli DSN istasyonunun Dünya üzerindeki konumu ve kullanılabilirliğini, Dünya'nın görünen kenarını, anten örüntüsünü, kırınımı veya yansımaları modellemez. Merkez ufkun altındaysa panel varsayımsal engelsiz güç değerini mevcut alınan sinyal gibi göstermez.
2. **Dünya'nın ufuk yüksekliği:** Dünya ufka yaklaştıkça küçük topografik yükseltilerin görüşü kesme olasılığı artar. Ay Güney Kutbu'ndaki alçak Güneş açısı gibi düşük Dünya elevasyonu da uzun mesafeli yüzey engellerine duyarlıdır.
3. **Anten yüksekliği:** İniş aracının anteni, astronotun 1.7 m göz yüksekliğiyle aynı yerde/yükseklikte değildir. Yazılım RF ufkunu ayrı bir alıcı anten yüksekliğinden hesaplar.
4. **Anten yönelimi ve kazancı:** Yüksek kazançlı antenin ana huzmesi Dünya'ya bakmalıdır. Açısal sapma, polarizasyon uyumsuzluğu ve antenin araç gövdesince gölgelenmesi alınan gücü azaltır.
5. **Dünya–Ay menzili:** Ay yörüngesi nedeniyle `R` zamanla değişir; FSPL mesafeyle artar. İki yüzey konumunun menzil farkı en çok yaklaşık bir Ay çapı (~3.475 km), Dünya–Ay yolu ise yaklaşık 400.000 km mertebesindedir. Bu fark FSPL'yi 0,1 dB'den az değiştirir. Bu nedenle koordinat değişince güç değerinin hemen hemen aynı kalması beklenir; bu değişimi yapay büyütmek doğru olmaz. Uygulama küçük farkı görünür kılmak için güç ve FSPL'yi iki ondalıkla gösterir.
6. **Frekans:** Aynı mesafede daha yüksek frekans daha yüksek serbest-uzay yol kaybı verir. Daha yüksek kazançlı antenler bu farkı telafi edebilir ancak daha hassas yöneltme gerektirir. K-bandında Dünya atmosferinin gaz/yağmur etkileri de sistem bütçesine eklenmelidir.
7. **Röle uyduları:** Dünya doğrudan görünmüyorsa bir röle yörünge aracı alternatif yol sağlayabilir. Bu, doğrudan Dünya görüşü ölçümünden farklı bir mimaridir ve mevcut RF paneli röle bağlantısını hesaplamaz.

**Konum karşılaştırma sonucu:** Aynı DSN profili ve alıcı varsayımları altında serbest-uzay Pr değerlerinin hemen hemen aynı kalması fiziksel olarak beklenir. İki konumun gerçek menzili JPL Horizons'tan ayrı alınır; değişim küçük olduğundan FSPL ve Pr yalnızca az miktarda farklılaşır. Ufuk kartı Dünya merkezinin modellenen ufkun üzerinde olup olmadığını ayrı gösterir. Bu, link kapanışı ya da belirli DSN istasyonuna görüş kanıtı değildir.

## 6. Lux ve astronaut POV aydınlatması

Lux, insan gözünün fotopik duyarlılığına göre ağırlıklandırılmış aydınlanma birimidir. RF gücü değildir.

Ay yörüngesinde atmosferik saçılma olmadığı için gölgeler keskin, doğrudan Güneş alan yüzey ile gölgeli yüzey arasındaki kontrast yüksektir. Güney Kutbu'nda Güneş çok düşük yükseliş açılarında görünebilir; bu nedenle uzak sırt ve krater duvarları uzun gölgeler oluşturabilir.

LunaSight v0.4.0, yatay yüzeye doğrudan aydınlatma için ilk yaklaşımı kullanır:

`Esolar ≈ 1361 × max(0, sin(h)) W/m²`

`Ev ≈ 127000 × max(0, sin(h)) lux`

Burada `h`, Güneş'in geometrik yükseliş açısıdır; fakat bu ifadeler yalnızca Güneş, seçilen azimuttaki yerel arazi ufkunun üzerindeyse uygulanır. Bu yaklaşık model; yamaç yönünü, yüzey albedosunu, uzay giysisinin vizör geçirgenliğini, göz adaptasyonunu, Dünya ışığını (Earthshine) ve gölgede yansıyan ışığı henüz modellemez. Elde edilen lux astronot vizöründe ölçülen lux değil, yatay referans yüzeydeki doğrudan güneş aydınlanması tahminidir.

POV görüntüsü yaklaşık 1.7 m göz yüksekliğinden yerel topografya ve Güneş/Dünya yönlerini gösteren bir görselleştirme konseptidir. Fotogerçekçi kask optiği, lens/vizör bozulması veya kalibre edilmiş kamera pozlaması değildir.

## 7. İniş alanı göstergesi

LunaSight'ın kullanıcı dostu göstergesi yalnızca örneklenmiş ışık ve Dünya görünürlüğü geometrisine dayalı bir ön taramadır:

- **Olumlu görünüyor:** Güneş görünürlüğü ≥ %70, Dünya görünürlüğü ≥ %50, eşzamanlı görünürlük ≥ %30 ve seçilen koordinat için NASA LOLA arazi kapsaması mevcut.
- **Yüksek kısıt:** Örneklenmiş Güneş görünürlüğü <%20 veya Dünya görünürlüğü <%10.
- **Ek inceleme gerekli:** Diğer durumlar veya gerekli arazi verisi eksikse.

Eşikler NASA standardı değildir. Gerçek iniş uygunluğu için eğim, pürüzlülük, kaya/boulder tehlikeleri, iniş elipsi, navigasyon belirsizliği, iniş motoru tozu, termal sınırlar, batarya/enerji depolama, anten yönü ve görev veri hızı gibi ek parametreler gerekir. Bu nedenle “olumlu görünüyor” hiçbir zaman “inişe güvenlidir” anlamına gelmez.

## 8. Yazılımda bu raporla eşleşen özellikler

- 3B güney-kutup arazi modeline tıklayarak koordinat seçimi.
- Küresel Ay modelindeki güney-kutup işaretçisini ve koordinatı takip etme; küre tıklamasıyla 80–90°G alanı seçimi.
- NASA/GSFC LOLA 80 m/piksel güney-kutup DEM'i ve mevcut bölgesel 5 m/piksel aday alanı karolarını isteğe bağlı yükleme.
- JPL Horizons üzerinden Güneş/Dünya topocentric azimut/yükseklik ve Dünya menzili sorgulama.
- Astronot göz hizası POV görünümü, yönlü güneş ışığı gölgelendirmesi ve yaklaşık lux HUD.
- Near-Earth S/X DSN uplink profilleriyle RF serbest-uzay referans gücü; K-band frekansı raporlanır ama EIRP profili doğrulanana kadar hesap dışıdır.
- Türkçe teknik rapor ve senaryo CSV çıktısı.

## 9. Kaynaklar

1. NASA, *HLS Sustaining Phase RF Communications Concept of Operations*, HLS-CONOP-008 Rev. A, 21 March 2025, Table 4-1: https://ntrs.nasa.gov/api/citations/20250003508/downloads/HLS-CONOP-008_Sustained_Phase_HLS_RF_ConOps_Rev_A.pdf
2. JPL DSN, *34-m BWG Stations Telecommunications Interfaces*, 810-005 Module 104 Rev. N, 2021, Tables 2–3: https://deepspace.jpl.nasa.gov/dsndocs/810-005/104/104N.pdf
3. NASA/JPL, *Deep Space Network Services Catalog*, 820-100 Rev. H, 2022, Tables 3-2 and 3-3: https://www.nasa.gov/wp-content/uploads/2023/09/dsn-services-catalog.pdf
4. JPL, *Horizons System Manual*: https://ssd.jpl.nasa.gov/horizons/manual.html
5. NASA/GSFC PGDA, *A New View of the Lunar South Pole from LOLA*: https://pgda.gsfc.nasa.gov/products/90
6. NASA OCHMO, *Artemis Lighting Considerations*: https://www.nasa.gov/wp-content/uploads/2023/12/ochmo-tb-001-artemis-lighting-considerations.pdf
7. NASA, *Exploration Systems Exterior Lighting Design Guidance*, NESC-RP-21-01706: https://ntrs.nasa.gov/api/citations/20240016463/downloads/1-3-25%2020240016463.pdf
