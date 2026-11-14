from __future__ import annotations

import tkinter as tk
from tkinter import ttk


_TRANSLATIONS = {
    "EXPLORE THE MOON · PLAN A MISSION": "AY'I KEŞFET · GÖREV PLANLA",
    "READY · INTERNET REQUIRED FOR LIVE NASA/JPL DATA": "HAZIR · CANLI NASA/JPL VERİSİ İÇİN İNTERNET GEREKLİ",
    "Moon coordinates: degrees · Times: UTC": "Ay koordinatları: derece · Saat: UTC",
    "Plan your Moon landing": "Ay inişinizi planlayın",
    "Pick a spot on the Moon, choose a date and see how much sunlight it gets and when Earth is visible.": "Ay'da bir konum ve tarih seçerek Güneş ışığını ve Dünya'nın ne zaman görülebildiğini inceleyin.",
    "PLACE NAME": "KONUM ADI",
    "Enter coordinates manually (optional)": "Koordinatları elle gir (isteğe bağlı)",
    "Hide manual coordinates": "Elle koordinat girişini gizle",
    "Latitude": "Enlem",
    "Longitude": "Boylam",
    "−90° to +90°": "−90° ile +90° arası",
    "East-positive; −180° to +360°": "Doğu pozitif; −180° ile +360° arası",
    "Landing date": "İniş tarihi",
    "Use YYYY-MM-DD. The calculation uses UTC.": "YYYY-AA-GG biçimi. Hesaplama UTC kullanır.",
    "Landing time": "İniş saati",
    "24-hour time, UTC (for example, 12:00).": "24 saat biçimi, UTC (ör. 12:00).",
    "Add this place to comparison": "Bu konumu karşılaştırmaya ekle",
    "SUN HEIGHT ABOVE HORIZON": "GÜNEŞİN UFUKTAN YÜKSEKLİĞİ",
    "Higher usually means stronger direct light": "Yükseklik arttıkça doğrudan ışık genelde artar",
    "EARTH HEIGHT ABOVE HORIZON": "DÜNYA'NIN UFUKTAN YÜKSEKLİĞİ",
    "Above the horizon means a direct view": "Ufkun üzerindeyse doğrudan görüş vardır",
    "DAYLIGHT IN THE NEXT 24 HOURS": "SONRAKİ 24 SAATTE GÜN IŞIĞI",
    "Share of the day with the Sun visible": "Güneş'in göründüğü zaman oranı",
    "WHEN EARTH IS VISIBLE": "DÜNYA'NIN GÖRÜNDÜĞÜ SÜRE",
    "Share of the day with Earth visible": "Dünya'nın göründüğü zaman oranı",
    "What is in the sky above this place?": "Bu konumdan gökyüzü nasıl görünür?",
    "The chart shows where the Sun and Earth appear from the selected location.": "Grafik, seçilen konumdan Güneş ve Dünya'nın yönünü gösterir.",
    "Height above horizon (°)": "Ufuktan yükseklik (°)",
    "Azimuth (°)": "Azimut (°)",
    "THE SKY ABOVE YOUR SELECTED PLACE": "SEÇİLEN KONUMUN GÖKYÜZÜ",
    "Choose a place on the Moon, set a date, then press ‘Check sunlight and Earth’.": "Ay'da konum ve tarih seçin, ardından ‘Güneş ve Dünya'yı incele’ düğmesine basın.",
    "Added '{scenario.label}' to the comparison list. Select Analyze with JPL Horizons to fetch live Sun/Earth positions.": "‘{scenario.label}’ karşılaştırma listesine eklendi. Canlı Güneş/Dünya konumları için JPL Horizons analizi yapın.",
    "Checking with NASA/JPL…": "NASA/JPL ile kontrol ediliyor…",
    "CHECKING THE SELECTED PLACE": "SEÇİLEN KONUM KONTROL EDİLİYOR",
    "Check sunlight and Earth with NASA/JPL": "NASA/JPL ile Güneş ve Dünya'yı incele",
    "NASA/JPL DATA NOT AVAILABLE": "NASA/JPL VERİSİ ALINAMADI",
    "NASA/JPL DATA LOADED": "NASA/JPL VERİSİ YÜKLENDİ",
    "azimuth": "azimut",
    "range": "menzil",
    "next 24 h · 30-min samples": "sonraki 24 saat · 30 dk örnekleme",
    "CSV files": "CSV dosyaları",
    "Remove selected": "Seçilenleri kaldır",
    "Export CSV": "CSV dışa aktar",
    "Clear all": "Tümünü temizle",
    "LANDING SITE": "İNIŞ KONUMU",
    "LATITUDE": "ENLEM",
    "LONGITUDE": "BOYLAM",
    "LANDING EPOCH (UTC)": "İNIŞ ZAMANI (UTC)",
    "ANALYSIS STATUS": "ANALİZ DURUMU",
    "CALCULATED": "HESAPLANDI",
    "NOT CALCULATED": "HESAPLANMADI",
    "Where the information comes from": "Bilgilerin kaynakları",
    "WHAT THE RESULTS MEAN": "SONUÇLAR NE ANLAMA GELİYOR?",
    "Load NASA whole-Moon map (4 MB)": "NASA tüm Ay haritasını yükle (4 MB)",
    "Earth-facing side": "Dünya'ya bakan yüz",
    "Far side": "Uzak yüz",
    "East side": "Doğu yüzü",
    "West side": "Batı yüzü",
    "North pole": "Kuzey kutbu",
    "South pole": "Güney kutbu",
    "Go": "Git",
    "Refresh surface view": "Yüzey görünümünü yenile",
    "Run the Sun and Earth check": "Güneş ve Dünya kontrolünü çalıştırın",
    "Show technical settings": "Teknik ayarları göster",
    "Hide technical settings": "Teknik ayarları gizle",
    "Update results": "Sonuçları güncelle",
    "Save a simple report": "Özet raporu kaydet",
    "Upgrade to 16 ppd detail": "16 piksel/derece ayrıntıya geç",
    "Loading south-pole data…": "Güney kutbu verisi hazırlanıyor…",
    "NASA whole-Moon map": "NASA tüm Ay haritası",
    "NASA data was not loaded.": "NASA verisi yüklenmedi.",
    "Manual coordinate": "Elle girilen koordinat",
    "3D Moon globe": "3B Ay küresi",
    "Choose a Moon location": "Ay'da konum seç",
    "Choose a place on the Moon": "Ay'da bir konum seç",
    "Check this place": "Bu konumu incele",
    "Check this place with NASA/JPL data": "Bu konumu NASA/JPL verileriyle incele",
    "Checking the Sun and Earth positions for this place and the next 24 hours…": "Bu konumda Güneş ve Dünya'nın şu anki ve sonraki 24 saatteki konumları hesaplanıyor…",
    "Detailed local terrain has not been loaded for this point.": "Bu noktaya ait ayrıntılı yerel arazi verisi yüklenmedi.",
    "Global elevation is for browsing only": "Küresel yükseklik verisi yalnızca genel inceleme içindir",
    "Click anywhere on the Moon": "Ay üzerinde istediğiniz yere tıklayın",
    "Schematic Moon globe": "Şematik Ay küresi",
    "NASA global LOLA terrain and LROC color map": "NASA küresel LOLA arazisi ve LROC renk haritası",
    "Over the next 24 hours:": "Sonraki 24 saat içinde:",
    "sunlight is available for about": "Güneş ışığı yaklaşık şu süre boyunca alınabilir:",
    "Language": "Dil",
    "English": "İngilizce",
    "Turkish": "Türkçe",
    "Latitude must be": "Enlem şu aralıkta olmalı:",
    "Longitude must be": "Boylam şu aralıkta olmalı:",
    "Use YYYY-MM-DD": "YYYY-AA-GG biçimini kullanın",
    "The calculation uses UTC.": "Hesaplama UTC kullanır.",
    "Not enough data": "Yeterli veri yok",
    "South pole · Shackleton region": "Güney Kutbu · Shackleton bölgesi",
    "South pole · Malapert region": "Güney Kutbu · Malapert bölgesi",
    "S-band · DSS-24 · 34 m · 20 kW": "S bandı · DSS-24 · 34 m · 20 kW",
    "S-band · DSS-26 · 34 m · 250 W": "S bandı · DSS-26 · 34 m · 250 W",
    "X-band · DSS-24 · 34 m · 20 kW": "X bandı · DSS-24 · 34 m · 20 kW",
    "X-band · DSS-26 · 34 m · 80 kW": "X bandı · DSS-26 · 34 m · 80 kW",
    "Schematic Moon globe · Load NASA data to show global elevation.": "Şematik Ay küresi · Küresel yüksekliği görmek için NASA verisini yükleyin.",
    "Global elevation is for browsing only; detailed local terrain has not been loaded for this point.": "Küresel yükseklik yalnızca genel inceleme içindir; bu noktada ayrıntılı arazi yüklenmedi.",
    "Detailed NASA LOLA terrain is available at this point.": "Bu noktada ayrıntılı NASA LOLA arazisi mevcut.",
    "Click any visible part of the Moon to select a place.": "Konum seçmek için Ay'ın görünen bir yerine tıklayın.",
    "Choose a place on the Moon, set the date and check it. An internet connection is needed for live NASA/JPL results.": "Ay'da konum ve tarih seçip inceleyin. Canlı NASA/JPL sonuçları için internet bağlantısı gerekir.",
    "Tip: You do not need to type coordinates. Open ‘Choose a Moon location’ and click anywhere on the 3D globe. The global map helps you explore; detailed local terrain is loaded separately.": "İpucu: Koordinat yazmanız gerekmez. ‘Konum seç’ sekmesini açıp 3B kürede bir yere tıklayın. Ayrıntılı yerel arazi verisi ayrıca yüklenir.",
    "Important: the global map is a location finder, not a detailed landing-hazard map. The local astronaut preview stays illustrative unless high-resolution terrain for that exact location is loaded. Radio power is an estimate, not proof that a mission link will work. LunaSight is an educational planning aid, not a landing approval or flight tool.": "Önemli: Küresel harita konum bulmaya yarar; ayrıntılı iniş tehlikesi haritası değildir. O noktaya ait yüksek çözünürlüklü arazi yüklenmedikçe astronot görünümü temsili kalır. Radyo gücü tahmindir, bağlantının çalışacağını kanıtlamaz. LunaSight eğitim amaçlı bir planlama aracıdır; iniş onayı veya uçuş aracı değildir.",
    "This is a visual estimate, not a calibrated helmet-camera image.": "Bu görsel bir tahmindir; kalibre edilmiş kask kamerası görüntüsü değildir.",
    "The global map gives a useful overview; precise shadow checks need higher-detail terrain for that exact area.": "Küresel harita genel bakış sağlar; hassas gölge incelemesi için o bölgenin ayrıntılı arazisi gerekir.",
    "Sunlight is available for about": "Güneş ışığının bulunduğu süre yaklaşık:",
    "Both are visible together for about": "İkisi birlikte yaklaşık şu süre görünür:",
    "Detailed NASA LOLA local terrain mask": "Ayrıntılı NASA LOLA yerel arazi ufku",
    "The example": "Örnek",
    "gives a theoretical clear-path received level of": "teorik, engelsiz yol alınan güç seviyesi:",
    "Choose a place on the Moon, then press": "Ay'da bir konum seçin, ardından basın",
    "Check the technical settings:": "Teknik ayarları kontrol edin:",
    "Analysis loaded for": "Analiz yüklendi:",
    "New Moon location selected. Choose": "Yeni Ay konumu seçildi. Hesaplamak için",
    "Use these coordinates": "Bu koordinatları kullan",
    "latitude": "enlem",
    "longitude": "boylam",
    "Longitude is east-positive. Time is UTC.": "Boylam doğu pozitiftir. Saat UTC'dir.",
    "landed site": "iniş konumu",
    "Select a Moon location": "Ay'da konum seçin",
    "CHOOSE ANY PLACE ON THE MOON": "AY'DA HERHANGİ BİR KONUM SEÇİN",
    "YOUR SELECTED PLACE": "SEÇİLEN KONUM",
    "WHAT AN ASTRONAUT WOULD SEE": "BİR ASTRONOT NE GÖRÜRDÜ?",
    "RADIO EXAMPLE": "RADYO ÖRNEĞİ",
    "Lander antenna gain (dBi)": "İniş aracı anten kazancı (dBi)",
    "Lander antenna height (m)": "İniş aracı anten yüksekliği (m)",
    "Other radio losses (dB)": "Diğer radyo kayıpları (dB)",
    "Earth–Moon distance (km)": "Dünya–Ay mesafesi (km)",
    "Local horizon toward Earth (degrees)": "Dünya yönündeki yerel ufuk (derece)",
    "0 dBi is a simple reference, not a specific lander antenna.": "0 dBi basit bir referanstır; belirli bir iniş aracı antenini göstermez.",
    "Used when checking whether terrain blocks the view of Earth.": "Arazinin Dünya görüşünü engelleyip engellemediğini hesaplarken kullanılır.",
    "An adjustable placeholder for additional losses.": "Ek kayıplar için değiştirilebilir varsayılan değer.",
    "Filled from JPL when available; otherwise an average distance is used.": "JPL verisi varsa kullanılır; yoksa ortalama mesafe alınır.",
    "Updated automatically when detailed local terrain covers the selected place.": "Seçilen noktayı ayrıntılı arazi kapsıyorsa otomatik güncellenir.",
    "DIRECT SUNLIGHT ON THE GROUND": "ZEMİNDEKİ DOĞRUDAN GÜNEŞ IŞIĞI",
    "SUN ENERGY REACHING THE GROUND": "ZEMİNE ULAŞAN GÜNEŞ ENERJİSİ",
    "ESTIMATED RADIO POWER FROM EARTH": "DÜNYA'DAN TAHMİNİ RADYO GÜCÜ",
    "SIGNAL LOST OVER THE DISTANCE": "MESAFEDEKİ SİNYAL KAYBI",
    "CAN THE LANDER SEE EARTH?": "İNİŞ ARACI DÜNYA'YI GÖREBİLİYOR MU?",
    "DOES THIS PLACE LOOK PROMISING?": "BU KONUM UMUT VERİCİ Mİ?",
    "Sun & Earth positions": "Güneş ve Dünya konumları",
    "Moon elevation": "Ay yüzey yüksekliği",
    "Radio signal example": "Radyo sinyali örneği",
    "Live · internet": "Canlı · internet",
    "Download in app": "Uygulamadan indir",
    "Reference model": "Referans model",
    "Calculates where the Sun and Earth appear from the selected Moon location and how far away Earth is.": "Seçilen Ay konumundan Güneş ve Dünya'nın yönünü ve Dünya'nın uzaklığını hesaplar.",
    "Global 4 px/degree or 16 px/degree elevation for browsing, plus a high-detail 80 m South Pole model and six 5 m site tiles. Global data is not detailed enough to certify a landing spot.": "Genel inceleme için 4 veya 16 piksel/derece küresel yükseklik verisi; ayrıca 80 m Güney Kutbu modeli ve altı adet 5 m yerel arazi karosu. Küresel veri iniş yerini onaylamak için yeterince ayrıntılı değildir.",
    "Uses published example frequency and transmitter information to estimate free-space received power. Actual lander radio specifications are mission-specific.": "Serbest uzayda alınan gücü tahmin etmek için yayımlanmış örnek frekans ve verici bilgilerini kullanır. Gerçek iniş aracı radyo özellikleri göreve özeldir.",
    "1. Sunlight: an estimate based on the Sun’s angle and whether the Sun is above the local terrain horizon.": "1. Güneş ışığı: Güneş'in açısına ve yerel arazi ufkunun üzerinde olup olmadığına dayalı tahmin.",
    "2. Earth view: a geometric visibility check. Hills and crater rims can block the direct line of sight.": "2. Dünya görüşü: geometrik görünürlük kontrolü. Tepeler ve krater kenarları doğrudan görüşü engelleyebilir.",
    "3. Radio power: a free-space estimate using a published example ground-station profile, not the confirmed radio of every lander.": "3. Radyo gücü: yayımlanmış örnek yer istasyonu profiline dayalı serbest uzay tahmini; her iniş aracının kesin radyo sistemi değildir.",
    "4. Global map: lets you choose any latitude and longitude. Higher-detail local terrain is available only for selected regions.": "4. Küresel harita: istenen enlem ve boylamı seçmenizi sağlar. Ayrıntılı yerel arazi yalnızca belirli bölgelerde mevcuttur.",
    "Show coordinates": "Koordinatları göster",
    "Hide coordinates": "Koordinatları gizle",
    "Set date and check this place": "Tarihi seç ve konumu incele",
    "Check sunlight and Earth": "Güneş ışığını ve Dünya'yı incele",
    "Choose a place": "Konum seç",
    "Date & sky view": "Tarih ve gökyüzü",
    "Sunlight & Earth link": "Güneş ışığı ve Dünya bağlantısı",
    "Compare places": "Konumları karşılaştır",
    "Data & sources": "Veri ve kaynaklar",
    "EDUCATIONAL RESEARCH TOOL · NOT A LANDING CERTIFICATION OR FLIGHT TOOL": "EĞİTİM VE ARAŞTIRMA ARACI · İNİŞ ONAYI VEYA UÇUŞ ARACI DEĞİLDİR",
    "NASA/JPL data loaded": "NASA/JPL verisi yüklendi",
    "NASA/JPL data not available": "NASA/JPL verisi alınamadı",
    "New place selected · check needed": "Yeni konum seçildi · kontrol gerekli",
    "Loading NASA data…": "NASA verisi yükleniyor…",
    "Loading South Pole data…": "Güney Kutbu verisi indiriliyor…",
    "Global map loaded": "Küresel harita yüklendi",
    "The global map is a location finder, not a detailed landing-hazard map.": "Küresel harita konum bulmak içindir; ayrıntılı iniş tehlikesi haritası değildir.",
    "For a precise landing check, use a detailed local elevation model where one is available.": "Hassas iniş incelemesi için mevcutsa ayrıntılı yerel yükseklik modeli kullanın.",
    "NASA LROC WAC display texture loaded (polar fill is lower detail).": "NASA LROC WAC görüntü dokusu yüklendi (kutup bölgeleri daha düşük ayrıntılıdır).",
    "Elevation shading is used; color texture unavailable.": "Yükseklik gölgelendirmesi kullanılıyor; renk dokusu kullanılamıyor.",
    "Whole globe is covered at locator resolution.": "Tüm küre, konum seçme çözünürlüğünde kapsanır.",
    "Retry NASA whole-Moon map": "NASA tüm Ay haritasını yeniden dene",
    "No direct sunlight at this time": "Şu anda doğrudan güneş ışığı yok",
    "Site comparison": "Konum karşılaştırması",
    "Quick site:": "Hızlı konum:",
    "Global map · 4 MB": "Küresel harita · 4 MB",
    "Detail · 63 MB": "Ayrıntı · 63 MB",
    "South Pole · 80 m/px": "Güney Kutbu · 80 m/piksel",
    "NASA TREK terrain here": "Buradaki NASA TREK arazisi",
    "Loading NASA terrain…": "NASA arazisi yükleniyor…",
    "NASA terrain ready": "NASA arazisi hazır",
    "5 m site tile": "5 m yerel arazi",
    "Reset view": "Görünümü sıfırla",
    "Loading map…": "Harita yükleniyor…",
    "Retry map": "Haritayı yeniden dene",
    "Map ready": "Harita hazır",
    "Load 16 px/° detail": "16 piksel/° ayrıntıyı yükle",
    "Loading terrain…": "Arazi yükleniyor…",
    "Loading tile": "Arazi karosu yükleniyor",
    "Terrain ready": "Arazi hazır",
    "Check coordinates": "Koordinatları kontrol edin",
    "Check mission inputs": "Görev bilgilerini kontrol edin",
    "Ephemeris request failed": "Yörünge verisi alınamadı",
    "Clear comparison": "Karşılaştırmayı temizle",
    "Remove all saved scenarios from this session?": "Bu oturumdaki tüm kayıtlı senaryolar kaldırılsın mı?",
    "Nothing to export": "Dışa aktarılacak veri yok",
    "Add at least one scenario first.": "Önce en az bir konum ekleyin.",
    "Export failed": "Dışa aktarma başarısız",
    "Export complete": "Dışa aktarma tamamlandı",
    "Scenario list saved to:\n{path}": "Konum listesi şuraya kaydedildi:\n{path}",
    "Report export failed": "Rapor dışa aktarılamadı",
    "Report exported": "Rapor dışa aktarıldı",
    "Saved report:": "Kaydedilen rapor:",
    "Latitude must be −90 to +90 and longitude −180 to +360 degrees.": "Enlem −90 ile +90, boylam −180 ile +360 derece arasında olmalıdır.",
    "Unexpected analysis error:": "Beklenmeyen analiz hatası:",
    "LunaSight | Explore the Moon": "LunaSight | Ay'ı Keşfet",
    "Scenario comparison": "Senaryo karşılaştırması",
    "Keep candidate locations and landing epochs together. Double-click a row to load it into Mission Analysis.": "Aday konumları ve iniş zamanlarını birlikte saklayın. Görev analizine yüklemek için bir satıra çift tıklayın.",
    "LunaSight uses public NASA/JPL datasets and calculations. Some views are global previews; detailed landing checks need local terrain data.": "LunaSight, NASA/JPL'nin herkese açık veri ve hesaplamalarını kullanır. Bazı görünümler küresel önizlemedir; ayrıntılı iniş incelemesi yerel arazi verisi gerektirir.",
    "Added": "Eklendi",
    "to the comparison list. Select Analyze with JPL Horizons to fetch live Sun/Earth positions.": "karşılaştırma listesine. Canlı Güneş/Dünya konumları için JPL Horizons analizi yapın.",
    "NASA/JPL data loaded for": "NASA/JPL verisi şu konum için yüklendi:",
    "Over the next 24 hours, sunlight is available for about": "Sonraki 24 saatte Güneş ışığı yaklaşık",
    "Earth is visible for about": "Dünya yaklaşık şu süre görünür:",
    "The detailed local LOLA terrain model was used.": "Ayrıntılı yerel LOLA arazi modeli kullanıldı.",
    "No detailed local terrain is loaded here, so the percentages use a smooth reference horizon.": "Burada ayrıntılı yerel arazi yüklenmediğinden yüzdeler düz bir referans ufkuna dayanır.",
    "Opening NASA/GSFC high-resolution south-polar LOLA elevation data. Internet connection required.": "NASA/GSFC yüksek çözünürlüklü güney kutbu LOLA yükseklik verisi açılıyor. İnternet bağlantısı gerekir.",
    "Loading NASA high-detail local terrain for": "NASA ayrıntılı yerel arazi verisi yükleniyor:",
    "Detailed NASA terrain loaded for this point.": "Bu nokta için ayrıntılı NASA arazisi yüklendi.",
    "NASA terrain tile loaded, but it does not cover the selected point (": "NASA arazi karosu yüklendi ancak seçilen noktayı kapsamıyor (",
    "). The app will not use it for this location.": "). Uygulama bu konumda bu veriyi kullanmayacak.",
    "Run the NASA/JPL check first.": "Önce NASA/JPL kontrolünü çalıştırın.",
    "Earth–Moon distance must be greater than zero.": "Dünya–Ay mesafesi sıfırdan büyük olmalıdır.",
    "Other radio losses cannot be negative.": "Diğer radyo kayıpları negatif olamaz.",
    "Terrain:": "Arazi:",
    "ASTRONAUT EYE VIEW · 1.7 m": "ASTRONOT GÖZÜNDEN GÖRÜNÜM · 1,7 m",
    "Elevation (4× display scale)": "Yükseklik (4× görüntü ölçeği)",
    "Loading NASA global LOLA terrain and LROC color map. The files are cached so you only need to do this once.": "Küresel NASA LOLA arazi ve LROC renk haritası yükleniyor. Dosyalar önbelleğe alınır; bu işlemi yalnızca bir kez yapmanız gerekir.",
    "Important:": "Önemli:",
    "Global map:": "Küresel harita:",
    "Download global NASA LOLA terrain and LROC color map": "Küresel NASA LOLA arazi ve LROC renk haritasını indir",
    "1 · CHOOSE A PLACE": "1 · KONUM SEÇ",
    "2 · DATE & SKY VIEW": "2 · TARİH VE GÖKYÜZÜ",
    "3 · SUNLIGHT & EARTH LINK": "3 · GÜNEŞ IŞIĞI VE DÜNYA BAĞLANTISI",
    "4 · COMPARE PLACES": "4 · KONUM KARŞILAŞTIR",
    "5 · DATA & SOURCES": "5 · VERİ VE KAYNAKLAR",
    "Schematic globe only. Choose ‘Load NASA whole-Moon map’ to download global LOLA elevation and LROC texture.": "Yalnızca şematik küre. Küresel LOLA yüksekliği ve LROC dokusunu indirmek için ‘NASA tüm Ay haritasını yükle’ seçeneğini kullanın.",
    "NASA global data was not loaded. The schematic globe remains available.": "NASA küresel verisi yüklenmedi. Şematik küre kullanılabilir.",
    "Loading NASA whole-Moon map (4 MB)": "NASA tüm Ay haritası yükleniyor (4 MB)",
    "More detail (about 63 MB)": "Daha ayrıntılı (yaklaşık 63 MB)",
    "NASA global map loaded": "NASA küresel haritası yüklendi",
    "Load South Pole detail (80 m/px)": "Güney Kutbu ayrıntısını yükle (80 m/piksel)",
    "Load 5 m local tile": "5 m yerel araziyi yükle",
    "South Pole detail loaded": "Güney Kutbu ayrıntısı yüklendi",
    "Detailed terrain unavailable": "Ayrıntılı arazi kullanılamıyor",
    "NASA map unavailable": "NASA haritası kullanılamıyor",
    "NASA terrain unavailable": "NASA arazisi kullanılamıyor",
    "Loading high-resolution NASA Moon Trek LOLA terrain for this place.": "Bu konum için yüksek çözünürlüklü NASA Moon Trek LOLA arazisi yükleniyor.",
    "NASA Moon Trek terrain could not be loaded. Existing terrain remains available.": "NASA Moon Trek arazisi yüklenemedi. Mevcut arazi kullanılabilir.",
    "NASA Moon Trek terrain loaded for this place.": "Bu konum için NASA Moon Trek arazisi yüklendi.",
    "NASA Moon Trek terrain loaded for the earlier selected place.": "Önceki seçili konum için NASA Moon Trek arazisi yüklendi.",
    "Viewpoint lifted above nearby terrain for a clear view; perspective preview, not a calibrated camera image.": "Net görünüm için bakış noktası yakındaki arazinin üzerine yükseltilir; bu kalibre edilmiş kamera görüntüsü değil, perspektif önizlemedir.",
    "Viewpoint lifted above nearby terrain for a clear view.": "Net görünüm için bakış noktası yakındaki arazinin üzerine yükseltilir.",
    "LUNAR SURFACE VIEW · LIFTED ABOVE TERRAIN": "AY YÜZEYİ GÖRÜNÜMÜ · ARAZİNİN ÜZERİNDEN",
    "Every latitude and longitude can be selected by clicking the globe. The global map gives a useful overview; precise shadow checks need higher-detail terrain for that exact area.": "Küreye tıklayarak tüm enlem ve boylamlar seçilebilir. Küresel harita genel bakış sağlar; hassas gölge incelemesi için o bölgenin ayrıntılı arazisi gerekir.",
    "Click anywhere on the Moon. Six views show the near side, far side, east, west and both poles so every area is reachable.": "Ay üzerinde istediğiniz yere tıklayın. Altı görünüm, yakın ve uzak yüzleri, doğu ve batıyı, iki kutbu gösterir.",
    "Drag to rotate; click to select. Use the six views to explore the near side, far side, east, west and both poles.": "Döndürmek için sürükleyin, konum seçmek için tıklayın. Altı görünümle Ay'ın yakın ve uzak yüzlerini, doğu ve batısını ve kutuplarını inceleyin.",
    "Jump to a known landing site or landing region:": "Bilinen iniş konumuna veya bölgesine git:",
    "HOW WELL CAN THE LANDER CONTACT EARTH?": "İNİŞ ARACI DÜNYA'YA NE KADAR İYİ BAĞLANABİLİR?",
    "Choose an example ground-station radio profile. LunaSight estimates how much signal could reach a lander in clear space.": "Örnek bir yer istasyonu radyo profili seçin. LunaSight, engelsiz durumda iniş aracına ulaşabilecek sinyali tahmin eder.",
    "RESULTS IN PLAIN LANGUAGE": "SONUÇLARIN ÖZETİ",
    "WHAT SHOULD I LOOK FOR?": "NELERE DİKKAT ETMELİYİM?",
    "Choose a Moon location, run the NASA/JPL check, and LunaSight will explain what the lighting and communication numbers mean.": "Ay'da konum seçip NASA/JPL kontrolünü çalıştırın; ışık ve iletişim sonuçları açıklanır.",
    "Remember: sunlight and radio signals are different things. Bright ground does not make a radio signal stronger. The radio number is a simplified estimate from a published example; real mission hardware details are needed to know whether a data link will work.": "Unutmayın: Güneş ışığı ve radyo sinyali farklıdır. Aydınlık zemin radyo sinyalini güçlendirmez. Radyo değeri yayımlanmış bir örneğe dayalı basit tahmindir; bağlantı için gerçek görev donanımının ayrıntıları gerekir.",
    "FULL MOON": "TÜM AY",
    "DRAG TO ROTATE": "DÖNDÜRMEK İÇİN SÜRÜKLEYİN",
    "CLICK TO PICK": "SEÇMEK İÇİN TIKLAYIN",
    "CLICK TO PICK A LOCATION": "KONUM SEÇMEK İÇİN TIKLAYIN",
    "East / West (m)": "Doğu / Batı (m)",
    "North / South (m)": "Kuzey / Güney (m)",
    "Astronaut eye-level preview": "Astronot göz hizası önizlemesi",
    "Perspective preview, not a calibrated camera image.": "Perspektif önizlemesidir; kalibre edilmiş kamera görüntüsü değildir.",
    "Ideal horizon": "İdeal ufuk",
    "Azimuth clockwise from north (°)": "Kuzeyden saat yönünde azimut (°)",
    "N · 0°": "K · 0°",
    "E · 90°": "D · 90°",
    "S · 180°": "G · 180°",
    "W · 270°": "B · 270°",
    "N · 360°": "K · 360°",
    "Sun · 30-min samples": "Güneş · 30 dk örnekler",
    "Earth · 30-min samples": "Dünya · 30 dk örnekler",
    "Sun · selected epoch": "Güneş · seçilen zaman",
    "Earth · selected epoch": "Dünya · seçilen zaman",
    "Your selected place": "Seçilen konum",
    "Detailed NASA LOLA local terrain": "Ayrıntılı NASA LOLA yerel arazisi",
    "illustrative relief only (not NASA data)": "temsili arazi (NASA verisi değildir)",
    "site-specific illustrative relief only (not NASA data)": "konuma özel temsili arazi (NASA verisi değildir)",
    "NASA global LOLA preview": "NASA küresel LOLA önizlemesi",
    "estimated direct surface light": "tahmini doğrudan yüzey ışığı",
    "no direct sunlight at this time": "şu anda doğrudan güneş ışığı yok",
    "Choose a location and run the Sun/Earth check to light this view.": "Bu görünümü aydınlatmak için konum seçip Güneş/Dünya kontrolünü çalıştırın.",
    "Choose a place on the Moon, then press ‘Check this place with NASA/JPL data’.": "Ay'da bir konum seçin, ardından ‘NASA/JPL verileriyle incele’ düğmesine basın.",
    "Run the Sun and Earth check to set the light direction.": "Işık yönünü görmek için Güneş ve Dünya kontrolünü çalıştırın.",
    "Example ground-station radio:": "Örnek yer istasyonu radyosu:",
    "Frequency:": "Frekans:",
    "wavelength:": "dalga boyu:",
    "This is a published DSN example, not the confirmed radio on every lander.": "Bu yayımlanmış bir DSN örneğidir; her iniş aracının kullandığı radyo olduğu doğrulanmamıştır.",
    "Over the next 24 hours: sunlight is available for about": "Sonraki 24 saatte: Güneş ışığının bulunduğu süre yaklaşık",
    "Earth is above the local/reference horizon for about": "Dünya yerel/referans ufkun üzerinde yaklaşık",
    "both are visible together for about": "ikisi birlikte yaklaşık",
    "Right now, the estimated direct light on a flat surface is": "Şu anda düz yüzeye ulaşan doğrudan ışık tahmini",
    "A geometric path to Earth is visible.": "Dünya'ya geometrik görüş hattı açık.",
    "Earth is below the local terrain horizon, so there is no direct path now.": "Dünya yerel arazi ufkunun altında; şu anda doğrudan bağlantı yolu yok.",
    "A detailed NASA LOLA local terrain mask was used.": "Ayrıntılı NASA LOLA yerel arazi ufku kullanıldı.",
    "Detailed terrain for this exact place is not loaded; visibility uses a simpler horizon.": "Bu konum için ayrıntılı arazi yüklenmedi; görünürlük basit ufuk varsayımına dayanıyor.",
    "Assessment:": "Değerlendirme:",
    "Yes — Earth above terrain": "Evet — Dünya arazinin üzerinde",
    "No — below / blocked": "Hayır — ufuk altında / engelli",
    "Not checked": "Kontrol edilmedi",
    "Needs more data": "Daha fazla veri gerekli",
    "Major constraint": "Önemli kısıt",
    "Compare alternatives": "Alternatifleri karşılaştırın",
    "Promising geometry": "Umut verici geometri",
}

_TURKISH_TO_ENGLISH = {turkish: english for english, turkish in _TRANSLATIONS.items()}


def source_text(text: str) -> str:
    """Return the English catalog text for a displayed English or Turkish value."""
    if text in _TURKISH_TO_ENGLISH:
        return _TURKISH_TO_ENGLISH[text]
    for turkish, english in sorted(
        _TURKISH_TO_ENGLISH.items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(turkish, english)
    return text


def translate(text: str, language: str) -> str:
    """Translate a UI string, including English fragments in dynamic messages."""
    english = source_text(str(text))
    if language != "Turkish":
        return english
    if english in _TRANSLATIONS:
        return _TRANSLATIONS[english]
    for source, target in sorted(
        _TRANSLATIONS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if source and source in english:
            english = english.replace(source, target)
    return english


def apply_language(root: tk.Misc, app, language: str) -> None:
    """Translate visible widgets while keeping programmatic combo values stable."""
    app.language = language
    variables: dict[str, tk.Variable] = {}
    for owner in (app, getattr(app, "explorer_panel", None), getattr(app, "radio_panel", None)):
        if owner is None:
            continue
        for value in vars(owner).values():
            if isinstance(value, tk.Variable):
                variables[str(value)] = value
                variables[value._name] = value

    def visit(widget: tk.Misc) -> None:
        kind = widget.winfo_class()
        if kind in {"Label", "Button", "TLabel", "TButton", "Checkbutton", "Radiobutton"}:
            try:
                if not hasattr(widget, "_lunasight_original_text"):
                    widget._lunasight_original_text = widget.cget("text")
                widget.configure(text=translate(widget._lunasight_original_text, language))
                if not hasattr(widget, "_lunasight_configure_wrapped"):
                    original_configure = widget.configure

                    def localized_configure(cnf=None, _configure=original_configure, **kwargs):
                        if "text" in kwargs:
                            kwargs["text"] = translate(kwargs["text"], app.language)
                        return _configure(cnf, **kwargs)

                    widget.configure = localized_configure
                    widget._lunasight_configure_wrapped = True
            except tk.TclError:
                pass
        elif kind == "TCombobox":
            try:
                if widget is getattr(app, "language_combo", None):
                    pass
                else:
                    if not hasattr(widget, "_lunasight_original_values"):
                        widget._lunasight_original_values = tuple(widget.cget("values"))
                    widget.configure(
                        values=tuple(translate(value, language) for value in widget._lunasight_original_values)
                    )
                    variable = variables.get(str(widget.cget("textvariable")))
                    if variable is not None:
                        value = source_text(variable.get())
                        variable.set(translate(value, language))
            except tk.TclError:
                pass
        elif kind == "TNotebook":
            for tab_id in widget.tabs():
                if not hasattr(widget, "_lunasight_tab_text"):
                    widget._lunasight_tab_text = {}
                if tab_id not in widget._lunasight_tab_text:
                    widget._lunasight_tab_text[tab_id] = widget.tab(tab_id, "text")
                widget.tab(
                    tab_id,
                    text=translate(widget._lunasight_tab_text[tab_id].strip(), language),
                )
        elif kind == "Treeview":
            if not hasattr(widget, "_lunasight_headings"):
                widget._lunasight_headings = {}
            for column in widget["columns"]:
                heading = widget.heading(column, "text")
                source = widget._lunasight_headings.setdefault(column, heading)
                widget.heading(column, text=translate(source, language))

        textvariable = widget.cget("textvariable") if kind in {"Label", "TLabel"} else ""
        variable = variables.get(str(textvariable))
        if variable is not None:
            if not hasattr(variable, "_lunasight_trace"):
                guard = {"active": False}

                def localize_variable(*_args, _variable=variable, _guard=guard):
                    if _guard["active"]:
                        return
                    current = _variable.get()
                    localized = translate(current, app.language)
                    if localized != current:
                        _guard["active"] = True
                        try:
                            _variable.set(localized)
                        finally:
                            _guard["active"] = False

                variable._lunasight_localize = localize_variable
                variable._lunasight_trace = variable.trace_add("write", localize_variable)
            variable._lunasight_localize()

        for child in widget.winfo_children():
            visit(child)

    visit(root)
