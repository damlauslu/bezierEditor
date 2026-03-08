# Bezier Eğrisi Editörü – Teknik Dokümantasyon

**Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Odev 1**

| Alan | Bilgi |
|------|-------|
| Programlama Dili | Python 3.8+ (yalnızca standart kütüphane) |
| Grafik Arayüz | tkinter |
| Konu | Kübik (4 kontrol noktalı) Bezier Eğrisi |
| Tarih | Mart 2026 |

---

## İçindekiler

1. [Giriş ve Genel Bakış](#1-giriş-ve-genel-bakış)
2. [Matematiksel Temel](#2-matematiksel-temel)
   - 2.1 Bezier Eğrisi Nedir?
   - 2.2 Bernstein Taban Polinomları
   - 2.3 Matris Formu
   - 2.4 Eğri Uzunluğu
3. [Uygulama Özellikleri](#3-uygulama-özellikleri)
4. [Arayüz Bileşenleri](#4-arayüz-bileşenleri)
   - 4.1 Sol Bilgi Paneli
   - 4.2 Ana Çizim Alanı (Tuval)
   - 4.3 Durum Çubuğu
5. [Kullanım Adımları](#5-kullanım-adımları)
   - 5.1 Uygulamayı Başlatma
   - 5.2 Kontrol Noktalarını Yerleştirme
   - 5.3 Eğriyi İnceleme
   - 5.4 Noktaları Düzenleme
   - 5.5 Sıfırlama
6. [Teknik Detaylar](#6-teknik-detaylar)
   - 6.1 Gereksinimler
   - 6.2 Çalıştırma
   - 6.3 Kod Yapısı
   - 6.4 Temel Algoritmalar
7. [Sonuç](#7-sonuç)

---

## 1. Giriş ve Genel Bakış

Bu uygulama, **kübik Bezier eğrisi** kavramını görsel olarak anlamayı ve etkileşimli biçimde keşfetmeyi sağlayan bir masaüstü editörüdür. Kullanıcı dört kontrol noktasını (P0, P1, P2, P3) fareyle tuval üzerine işaretler ya da koordinatlarını doğrudan girerek tanımlar; uygulama Bezier eğrisini anlık olarak hesaplayıp çizer.

> **Neden Bezier Eğrileri?**
> Bezier eğrileri bilgisayar grafiği, CAD, animasyon, yazı tipi tasarımı ve oyun motoru gibi alanlarda temel bileşen olarak kullanılmaktadır. Kontrol noktaları sayesinde sezgisel biçimde şekillendirilebilen bu eğriler, hem matematiksel sağlamlıkları hem de uygulama kolaylıkları nedeniyle endüstri standardı haline gelmiştir.

Uygulama yalnızca Python 3 standart kütüphanesi (`tkinter` + `math`) kullanılarak geliştirilmiştir; **ek paket kurulumu gerekmemektedir**.

---

## 2. Matematiksel Temel

### 2.1 Bezier Eğrisi Nedir?

Bezier eğrisi, *n+1* kontrol noktasıyla tanımlanan parametrik bir eğridir. Parametresi *t* ∈ [0, 1] aralığında değişir. Bu uygulamada **n = 3** (kübik) kullanılmakta olup dört kontrol noktası mevcuttur:

| Nokta | Rol |
|-------|-----|
| **P0** | Eğrinin başlangıç noktası — eğri buradan geçer |
| **P1** | Birinci kontrol noktası — P0'daki teğetin yönünü belirler |
| **P2** | İkinci kontrol noktası — P3'teki teğetin yönünü belirler |
| **P3** | Eğrinin bitiş noktası — eğri buradan geçer |

P0 ve P3 eğrinin *üzerindeki* (interpolasyon) noktalardır. P1 ve P2 eğrinin *dışındaki* (yaklaşım) kontrol noktalarıdır; doğrudan eğri üzerinde yer almaz, ancak şekli belirler.

### 2.2 Bernstein Taban Polinomları

Kübik Bezier eğrisinin parametrik denklemi:

```
B(t) = (1−t)³·P0  +  3(1−t)²t·P1  +  3(1−t)t²·P2  +  t³·P3
```

Bernstein taban fonksiyonları (n = 3):

```
B₀,₃(t) = (1−t)³
B₁,₃(t) = 3(1−t)²t
B₂,₃(t) = 3(1−t)t²
B₃,₃(t) = t³
```

**Temel özellikler:**

- **Bölüm özdeşliği:** B₀,₃ + B₁,₃ + B₂,₃ + B₃,₃ = 1 (her t için)
- **Negatif olmama:** Tüm katsayılar t ∈ [0,1] için ≥ 0
- **Uç nokta interpolasyonu:** B(0) = P0, B(1) = P3
- **Teğet koşulları:** B′(0) = 3(P1 − P0), B′(1) = 3(P3 − P2)

Bu son iki özellik neden teğet okların P0→P1 ve P3→P2 yönünde çizildiğini açıklamaktadır.

### 2.3 Matris Formu

Eğri daha kompakt biçimde matris çarpımı olarak yazılabilir. Bu formülasyon özellikle hesaplama açısından avantajlıdır ve uygulamanın bilgi panelinde gösterilmektedir:

```
B(t) = T · M_bezier · G
```

Parametre vektörü (1×4):

```
T = [t³  t²  t  1]
```

Kübik Bezier katsayı matrisi (4×4, sabit):

```
         ⎡ −1   3  −3   1 ⎤
M_bezier=⎢  3  −6   3   0 ⎥
         ⎢ −3   3   0   0 ⎥
         ⎣  1   0   0   0 ⎦
```

Geometri / kontrol nokta matrisi G (4×2, kullanıcı girdisi):

```
    ⎡ P0x  P0y ⎤
G = ⎢ P1x  P1y ⎥
    ⎢ P2x  P2y ⎥
    ⎣ P3x  P3y ⎦
```

Sonuç: B(t) boyutu 1×2 → `[Bx(t), By(t)]`

Uygulama sol panelde hem **G matrisini** (kontrol noktalarının koordinatları) hem de sabit **M matrisini** göstermektedir.

### 2.4 Eğri Uzunluğu

Bezier eğrisinin analitik uzunluğunun kapalı formu yoktur. Uygulama **kümülatif kiriş toplamı** yöntemiyle sayısal yaklaşım kullanır:

```
L ≈ Σ ‖B(tᵢ) − B(tᵢ₋₁)‖     (i = 1..N,  N = 200 adım)

Her adımda: Δᵢ = √( (xᵢ−xᵢ₋₁)² + (yᵢ−yᵢ₋₁)² )
```

200 adım, piksel düzeyinde hassasiyet için yeterlidir. Bulunan sonuç panel üzerinde *"L ≈ … piksel"* olarak gösterilir.

---

## 3. Uygulama Özellikleri

| Özellik | Açıklama |
|---------|----------|
| **Fareyle Nokta Girişi** | Kullanıcı tuvale tıklayarak P0, P3, P1, P2 sırasıyla dört kontrol noktası yerleştirir |
| **Koordinat Girişi** | Sol panelden herhangi bir noktanın X ve Y koordinatı klavye ile sayısal olarak girilebilir |
| **Anlık Eğri Çizimi** | Dördüncü nokta yerleştirildiği anda Bezier eğrisi otomatik çizilir; nokta güncellendiğinde eğri anlık yenilenir |
| **Kontrol Çokgeni** | P0–P1–P2–P3 noktalarını birleştiren kesikli çizgi eğrinin "kafesini" görselleştirir |
| **Teğet Okları** | P0'dan P1 yönüne yeşil, P3'ten P2 yönüne kırmızı ok; uç noktalardaki teğet yönlerini gösterir |
| **Fare Üzeri t Parametresi** | Fare tuvalde hareket ettiğinde eğri üzerindeki en yakın nokta hesaplanır; t değeri ve B(t) koordinatları sol panelde canlı güncellenir |
| **G ve M Matris Gösterimi** | Kontrol nokta matrisi (G) ve kübik Bezier katsayı matrisi (M) sol panelde sürekli gösterilir |
| **Eğri Uzunluğu** | 200 adımlı sayısal integrasyon ile eğrinin piksel cinsinden yaklaşık uzunluğu hesaplanır |
| **Nokta Düzenleme** | Dört ayrı güncelleme düğmesiyle istenilen nokta seçilip tuvale tıklanarak veya koordinat girilerek güncellenebilir |
| **Sıfırlama** | Tek tuşla tüm noktalar temizlenerek yeni bir eğri oluşturulabilir |
| **Izgara Arka Planı** | 50 piksel aralıklı yatay/dikey ızgara çizgileri konum tahminine yardımcı olur |
| **Duyarlı Pencere** | Pencere yeniden boyutlandırıldığında tuval ve eğri otomatik ölçeklenir |

---

## 4. Arayüz Bileşenleri

Uygulama penceresi iki ana alandan oluşmaktadır: sol sabit genişlikli (290 px) **bilgi paneli** ve sağda tam ekrana genişleyen **çizim tuvali**.

### 4.1 Sol Bilgi Paneli

| Bileşen | İçerik |
|---------|--------|
| **Nokta Koordinatları** | P0–P3 noktalarının anlık (x, y) piksel koordinatları; her nokta kendi rengiyle gösterilir (P0 yeşil, P1 turuncu, P2 mor, P3 kırmızı) |
| **G Matrisi** | 4×2 geometri matrisi; kontrol noktalarının x ve y koordinat sütunları |
| **Bezier Matrisi (M)** | Sabit 4×4 kübik Bezier katsayı matrisi |
| **Fare Pozisyonu** | Farenin tuval üzerindeki anlık (x, y) koordinatı |
| **t Değeri** | Farenin eğri üzerindeki en yakın noktanın parametre değeri (0.0000–1.0000) |
| **B(t) Noktası** | t değerine karşılık gelen eğri noktasının (x, y) koordinatı |
| **Eğri Uzunluğu** | L ≈ … piksel |
| **Nokta Düzenleme Düğmeleri** | P0–P3 için dört "Güncelle" düğmesi; aktif nokta sarı halkasıyla vurgulanır |
| **Koordinat Giriş Kutusu** | Düzenleme modunda görünür; X ve Y alanları, Onayla/İptal düğmeleri |
| **Sıfırla Düğmesi** | Panelin en altında; tüm noktaları ve eğriyi temizler |

Sol panel dikey kaydırma çubuğuna sahiptir ve fare tekerleğiyle kaydırılabilir.

### 4.2 Ana Çizim Alanı (Tuval)

Koyu lacivert arka plan üzerine şunlar çizilir:

- **Izgara:** 50 px aralıklı gri yatay/dikey çizgiler
- **Kontrol noktaları:** Renkli dolgulu daireler; yanlarında nokta adı ve koordinat etiketi
- **Kontrol çokgeni:** P0→P1→P2→P3 arası kesikli çizgiler
- **Bezier eğrisi:** 200 kırık çizgi parçasından oluşan parlak camgöbeği eğri
- **Teğet okları:** P0→P1 yönünde yeşil ok (başlangıç teğeti), P3→P2 yönünde kırmızı ok (bitiş teğeti)
- **Fare üzeri işaretçi:** En yakın eğri noktasında beyaz dolgulu küçük daire + `t=…` etiketi
- **Düzenleme halkası:** Düzenleme modundaki nokta sarı dış halkayla işaretlenir

### 4.3 Durum Çubuğu

Pencerenin en altında konumlanan durum çubuğu, kullanıcıya anlık yönerge mesajı gösterir:

| Durum | Mesaj |
|-------|-------|
| 1. tıklama bekleniyor | Adım 1/4: P0 başlangıç noktasını tıklayın |
| 2. tıklama bekleniyor | Adım 2/4: P3 bitiş noktasını tıklayın |
| 3. tıklama bekleniyor | Adım 3/4: P1 kontrol noktasını tıklayın |
| 4. tıklama bekleniyor | Adım 4/4: P2 kontrol noktasını tıklayın |
| Eğri hazır | Eğri çizildi. Fareyi eğri üzerinde gezdirin veya nokta düzenleyin. |
| Düzenleme modu | Düzenleme modu: [Pn] için yeni konumu tıklayın veya koordinat girin |

---

## 5. Kullanım Adımları

### 5.1 Uygulamayı Başlatma

**Python ile:**

```bash
python bezier_editor.py
```

**Yürütülebilir dosya ile:**

`bezier_editor.exe` dosyasına çift tıklayın. Python kurulumuna gerek yoktur.

Uygulama açıldığında durum çubuğu "Adım 1/4: P0 başlangıç noktasını tıklayın" mesajını gösterir ve fare imleci artı (+) şeklindedir.

### 5.2 Kontrol Noktalarını Yerleştirme

Dört kontrol noktası **belirli bir sırayla** girilir. Bu sıra, kullanıcının önce eğrinin başını ve sonunu, ardından şekli belirleyen kontrol noktalarını koymasına imkân tanır:

**Adım 1 — P0 (Başlangıç noktası):**
Tuvale bir kez tıklayın. Yeşil daire görünür.

**Adım 2 — P3 (Bitiş noktası):**
İkinci tıklamayı yapın. Kırmızı daire görünür.

**Adım 3 — P1 (İlk kontrol noktası):**
Üçüncü tıklama. Turuncu daire görünür; P0 ile P1 arası kesikli çizgiyle bağlanır.

**Adım 4 — P2 (İkinci kontrol noktası):**
Dördüncü tıklama. Mor daire görünür. Dört nokta tamamlandığı anda eğri, kontrol çokgeni ve teğet okları hemen çizilir.

> **Not:** Giriş sırası P0 → P3 → P1 → P2 şeklindedir (P1 ve P2 sonra girilir). Bu sıra durum çubuğunda her adımda hatırlatılır.

### 5.3 Eğriyi İnceleme

Eğri çizildikten sonra fareyi tuval üzerinde hareket ettirin:

- Sol panelin **Fare Pozisyonu** alanı anlık koordinatı gösterir.
- Fare eğriye yaklaştıkça **t Değeri** ve **B(t) Noktası** güncellenir; tuval üzerinde beyaz yuvarlak işaretçi en yakın eğri noktasına atlayarak `t` değerini gösterir.
- Sol panelde **Eğri Uzunluğu** (L) piksel cinsinden görüntülenir.
- **G Matrisi** noktaların koordinatlarını matris biçiminde sunar.

### 5.4 Noktaları Düzenleme

Yerleştirilmiş herhangi bir nokta iki yolla güncellenebilir:

**Yöntem A – Tıklayarak Güncelleme:**

1. Sol panelden ilgili düğmeye tıklayın (örn. *P1 Güncelle*). Düğme sarıya döner; fare imleci çift artı işaretine dönüşür.
2. Tuvale tıklayın; nokta tıklanan konuma taşınır.
3. Eğri anında yenilenir.

**Yöntem B – Koordinat Girerek Güncelleme:**

1. İlgili *Güncelle* düğmesine tıklayın. Sol panelde X ve Y giriş kutuları açılır.
2. X ve Y değerlerini yazın.
3. *Onayla* düğmesine tıklayın ya da Enter'a basın.
4. İptal etmek için *İptal* düğmesine tıklayın.

> Her iki yöntem de kullanılabilir; koordinat kutusundaki mevcut değerler, düzenleme moduna girildiğinde noktanın mevcut konumuyla otomatik olarak doldurulur.

### 5.5 Sıfırlama

Sol panelin altındaki **Sıfırla** düğmesine tıklayın. Tüm noktalar, eğri ve hesaplamalar temizlenerek uygulama başlangıç durumuna döner.

---

## 6. Teknik Detaylar

### 6.1 Gereksinimler

| Bileşen | Versiyon | Açıklama |
|---------|----------|----------|
| Python | 3.8 veya üzeri | Ana çalışma zamanı |
| tkinter | Python ile birlikte gelir | Grafik arayüz kütüphanesi |
| math | Standart kütüphane | Hipotenüs ve karekök hesapları |
| İşletim Sistemi | Windows / macOS / Linux | tkinter'ın desteklediği her platform |

**Üçüncü parti paket kullanılmamıştır.** `pip install` ya da sanal ortam kurulumu gerekmez.

### 6.2 Çalıştırma

```bash
# Terminal / Komut İstemi üzerinden:
python bezier_editor.py
```

Windows'ta dosyaya çift tıklanarak da çalıştırılabilir.

**Yürütülebilir (.exe) Oluşturma:**

PyInstaller aracıyla bağımsız bir yürütülebilir dosya oluşturulmuştur:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed bezier_editor.py
```

`dist/bezier_editor.exe` dosyası Python kurulumu olmayan sistemlerde de çalışmaktadır.

### 6.3 Kod Yapısı

Tüm uygulama tek dosyadan (`bezier_editor.py`) oluşmaktadır. Dosya ~625 satırdır.

| Bölüm | Satır Aralığı | Sorumluluk |
|-------|---------------|------------|
| Sabitler | 1–50 | M_BEZIER matrisi, renk paleti, adım mesajları |
| `BezierEditor.__init__` | 59–80 | Uygulama durumu ve font nesnelerinin başlatılması |
| `_build_ui` ve alt metotlar | 84–305 | Sol panel, tuval, giriş widget'larının oluşturulması |
| `_on_click` | 308–323 | Fare tıklama olayı: nokta yerleştirme veya düzenleme |
| `_on_motion` | 325–339 | Fare hareketi: koordinat güncellemesi + hover hesabı |
| `_activate_edit`, `_finish_edit`, `_apply_entry` | 343–394 | Nokta düzenleme modu yönetimi |
| `_reset` | 398–417 | Tam sıfırlama |
| `_refresh_info`, `_update_status` | 421–457 | Bilgi paneli ve durum çubuğu güncellemeleri |
| `_bezier` | 465–475 | B(t) hesabı – Bernstein formülü |
| `_closest_t` | 477–489 | Fareye en yakın t parametresi (200 örnek) |
| `_arc_length` | 491–500 | Eğri uzunluğu sayısal integrasyonu (200 adım) |
| Çizim metotları | 504–611 | Izgara, eğri, noktalar, kontrol çokgeni, oklar, hover |
| `main` | 617–624 | Giriş noktası: Tk penceresi ve olay döngüsü |

### 6.4 Temel Algoritmalar

#### Eğri Örnekleme (`_bezier`)

Bernstein taban polinomları açık çarpımla hesaplanmaktadır. 4 kontrol noktası, 4 katsayı ve bir parametre değeri alınarak tek bir (x, y) çifti döndürülür. Çizim için 201 nokta (t = 0/200 … 200/200) örneklenerek `canvas.create_line` ile polilin olarak çizilir.

```python
def _bezier(self, t):
    p0, p1, p2, p3 = self.points
    mt  = 1.0 - t
    c0  = mt * mt * mt            # (1-t)³
    c1  = 3.0 * mt * mt * t       # 3(1-t)²t
    c2  = 3.0 * mt * t  * t       # 3(1-t)t²
    c3  = t  * t  * t             # t³
    x = c0*p0[0] + c1*p1[0] + c2*p2[0] + c3*p3[0]
    y = c0*p0[1] + c1*p1[1] + c2*p2[1] + c3*p3[1]
    return (x, y)
```

#### En Yakın t Parametresi (`_closest_t`)

Farenin eğri üzerindeki en yakın noktasını bulmak için kaba kuvvet (brute-force) arama kullanılır: eğri 200 eşit adıma bölünür, her adımda Öklid uzaklığı hesaplanır, minimum uzaklıklı t değeri döndürülür. Hesaplama yükü hafif olduğundan fare hareketi olayında performans sorunu yaşanmaz.

```python
def _closest_t(self, mx, my, n=200):
    best_t, best_d, best_pt = 0.0, float('inf'), None
    for i in range(n + 1):
        t  = i / n
        pt = self._bezier(t)
        d  = (pt[0] - mx)**2 + (pt[1] - my)**2
        if d < best_d:
            best_t, best_d, best_pt = t, d, pt
    return best_t, best_pt
```

#### Eğri Uzunluğu (`_arc_length`)

Ardışık örnekler arasındaki kiriş uzunlukları toplanır. 200 adım yeterli hassasiyet sağlar:

```python
def _arc_length(self, n=200):
    total = 0.0
    prev  = self._bezier(0.0)
    for i in range(1, n + 1):
        curr = self._bezier(i / n)
        dx, dy = curr[0] - prev[0], curr[1] - prev[1]
        total += math.sqrt(dx*dx + dy*dy)
        prev = curr
    return total
```

#### Yeniden Çizim Stratejisi

Yapısal değişiklikler (nokta ekleme/güncelleme, pencere yeniden boyutlandırma) tüm tuvali silen ve sıfırdan çizen `_redraw()` metodunu çağırır. Yalnızca fare hover işaretçisi `canvas.delete('hover')` ile seçici olarak silinip yeniden çizilir; bu sayede her fare hareketi için tam yeniden çizim yapılmaz.

---

## 7. Sonuç

Bu uygulama, kübik Bezier eğrisinin matematiksel temelini görsel ve etkileşimli biçimde deneyimlemeyi sağlamaktadır. Kullanıcı dört kontrol noktasını fareyle veya koordinat girerek tanımlar; uygulama Bernstein polinomlarıyla eğriyi hesaplar, matris gösterimini günceller, teğet yönlerini görselleştirir ve eğri uzunluğunu sayısal integrasyon ile tahmin eder.

**Uygulamanın sunduğu temel öğrenme çıktıları:**

- Kontrol noktaları ile eğri şekli arasındaki ilişkinin sezgisel anlaşılması
- B(t) formülünün farklı t değerlerinde nasıl çalıştığının gözlemlenmesi
- Teğet koşullarının (P0→P1 ve P3→P2) eğri başlangıç/bitiş yönlerine etkisi
- Kontrol çokgeninin eğriyi nasıl "çektiğinin" görsel olarak kavranması
- Matris formu ile denklem formu arasındaki denkliğin gösterilmesi

---

*Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Ödev 1*
