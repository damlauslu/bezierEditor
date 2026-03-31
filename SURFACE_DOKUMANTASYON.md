# Parametrik Yüzey Editörü – Teknik Dokümantasyon

**Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Odev 4**

| Alan | Bilgi |
|------|-------|
| Programlama Dili | Python 3.8+ (yalnızca standart kütüphane) |
| Grafik Arayüz | tkinter |
| Konu | Bezier / B-Spline / NURBS Tensor-Product Yüzeyleri (3B) |
| Tarih | Mart 2026 |

---

## İçindekiler

1. [Giriş ve Genel Bakış](#1-giriş-ve-genel-bakış)
2. [Matematiksel Temel](#2-matematiksel-temel)
   - 2.1 Parametrik Yüzey Nedir?
   - 2.2 Bezier Yüzeyi
   - 2.3 B-Spline Yüzeyi
   - 2.4 NURBS Yüzeyi
   - 2.5 Cox–de Boor Özyinelemesi
   - 2.6 Düğüm Vektörü (Knot Vector)
   - 2.7 3B → 2B Projeksiyon
3. [Uygulama Özellikleri](#3-uygulama-özellikleri)
4. [Arayüz Bileşenleri](#4-arayüz-bileşenleri)
   - 4.1 Sol Kontrol Paneli
   - 4.2 Ana Çizim Alanı (Tuval)
   - 4.3 Durum Çubuğu
5. [Kullanım Adımları](#5-kullanım-adımları)
   - 5.1 Uygulamayı Başlatma
   - 5.2 Ön Tanımlı Yüzey Seçimi
   - 5.3 Yüzey Tipini Değiştirme
   - 5.4 Derece Ayarlama
   - 5.5 Görünümü Döndürme ve Yakınlaştırma
   - 5.6 Kontrol Noktası Seçme ve Düzenleme
   - 5.7 Sıfırlama
6. [Teknik Detaylar](#6-teknik-detaylar)
   - 6.1 Gereksinimler
   - 6.2 Çalıştırma
   - 6.3 Kod Yapısı
   - 6.4 Temel Algoritmalar
7. [Ders Notu Referansı](#7-ders-notu-referansı)
8. [Sonuç](#8-sonuç)

---

## 1. Giriş ve Genel Bakış

Bu uygulama, **3 boyutlu parametrik yüzeyleri** (Bezier, B-Spline, NURBS) görsel olarak anlamayı ve etkileşimli biçimde keşfetmeyi sağlayan bir masaüstü editörüdür. Yüzey eğrilerin iki parametrik yönde (*u* ve *v*) genelleştirilmesiyle elde edilir; bu yapıya **tensor-product yüzey** adı verilir.

> **Neden Parametrik Yüzeyler?**  
> Bezier, B-Spline ve NURBS yüzeyleri CAD/CAM sistemlerinde, otomotiv tasarımında, mimari modelleme yazılımlarında ve oyun motorlarında temel bileşen olarak kullanılır. NURBS, ISO 10303 (STEP) standardıyla endüstrinin ortak dili haline gelmiştir.

Uygulama yalnızca Python 3 standart kütüphanesi (`tkinter` + `math`) kullanılarak geliştirilmiştir; **ek paket kurulumu gerekmemektedir**.

---

## 2. Matematiksel Temel

### 2.1 Parametrik Yüzey Nedir?

Parametrik yüzey, iki bağımsız parametre (*u*, *v*) aracılığıyla tanımlanan bir yüzey fonksiyonudur:

```
S : [0,1] × [0,1] → ℝ³
    (u, v) ↦ (x(u,v), y(u,v), z(u,v))
```

Yüzey noktaları, **kontrol ağı** adı verilen (m+1)×(n+1) boyutlu bir nokta dizisinden elde edilir. Kontrol ağı düzenlenerek yüzey şekli interaktif biçimde değiştirilebilir.

---

### 2.2 Bezier Yüzeyi

**Tensor-product Bezier yüzeyi**, Bezier eğrisinin iki parametrik yöne genelleştirilmesiyle elde edilir:

```
S(u,v) = Σᵢ₌₀ⁿ Σⱼ₌₀ᵐ  Pᵢⱼ · Bᵢ,ₙ(u) · Bⱼ,ₘ(v),    0 ≤ u ≤ 1,  0 ≤ v ≤ 1
```

Burada:
- **Pᵢⱼ** → (i,j). kontrol noktası (3B koordinat)
- **Bᵢ,ₙ(u)** → u yönünde Bernstein taban polinomu
- **Bⱼ,ₘ(v)** → v yönünde Bernstein taban polinomu

**Bernstein taban polinomu:**

```
Bᵢ,ₙ(t) = C(n,i) · tⁱ · (1−t)ⁿ⁻ⁱ
```

| Özellik | Açıklama |
|---------|----------|
| Köşe interpolasyonu | Köşe kontrol noktaları P₀₀, Pₙ₀, P₀ₘ, Pₙₘ yüzey üzerindedir |
| Dışbükey omurga | Yüzey, kontrol ağının dışbükey zarfı içinde kalır |
| Derece | u yönünde n, v yönünde m |
| Globallik | Tek bir nokta tüm yüzeyi etkiler |

---

### 2.3 B-Spline Yüzeyi

B-Spline eğrisinin yüzeye genelleştirilmesiyle elde edilir:

```
P(u,v) = Σᵢ₌₀ⁿ Σⱼ₌₀ᵐ  Pᵢⱼ · Nᵢ,ₖ(u) · Nⱼ,ₗ(v)
```

Matris formunda (bikübik, n=m=3 için):

```
P(u,v) = [N₀,ₖ(u)  N₁,ₖ(u)  ···  Nₙ,ₖ(u)] · [P] · [N₀,ₗ(v)]
                                                       [N₁,ₗ(v)]
                                                       [  ···   ]
                                                       [Nₘ,ₗ(v)]
```

Burada **[P]**, kontrol noktalarının (n+1)×(m+1)'lik matrisidir.

**B-Spline yüzeyinin özellikleri:**
- Yerel destek: Bir kontrol noktası en fazla (k+1)×(l+1) yama dilimini etkiler
- Süreklilik: Düğüm vektöründe tekrar yok ise Cᵏ⁻² ve Cˡ⁻²
- Her iki yönde kontrol sayısı = mertebe ise B-Spline yüzeyi Bezier yüzeyine dönüşür
- Dışbükey omurga özelliği korunur

---

### 2.4 NURBS Yüzeyi

NURBS (Non-Uniform Rational B-Spline) yüzeyi, B-Spline'ın rasyonel genellemesidir. Her kontrol noktasına bir **ağırlık (Wᵢⱼ)** eklenir:

```
S(u,v) = Σᵢ₌₀ⁿ Σⱼ₌₀ᵐ  Pᵢⱼ · Rᵢ,ₖ,ⱼ,ₗ(u,v)
```

**Rasyonel taban fonksiyonu:**

```
              Wᵢⱼ · Nᵢ,ₖ(u) · Nⱼ,ₗ(v)
Rᵢ,ₖ,ⱼ,ₗ(u,v) = ──────────────────────────────────
                 Σᵣ Σₛ  Wᵣₛ · Nᵣ,ₖ(u) · Nₛ,ₗ(v)
```

**NURBS'ün üstünlükleri:**
- Analitik şekiller (küre, silindir, koni, toroid) tam olarak temsil edilebilir
- B-Spline'ın tüm özellikleri miras alınır
- Afin ve perspektif dönüşümler altında değişmezlik
- CAD endüstri standardı (IGES, STEP)

**Ağırlık etkisi:**
- `Wᵢⱼ = 1` tüm noktalarda → standart B-Spline yüzeyi
- `Wᵢⱼ > 1` → yüzey o noktaya yaklaşır
- `Wᵢⱼ < 1` → yüzey o noktadan uzaklaşır

---

### 2.5 Cox–de Boor Özyinelemesi

B-Spline ve NURBS taban fonksiyonları Cox–de Boor formülüyle özyinelemeli hesaplanır:

**Sıfırıncı derece (p = 0):**
```
         ⎧ 1,  tᵢ ≤ t < tᵢ₊₁
Nᵢ,₀(t) = ⎨
         ⎩ 0,  aksi halde
```

**p. derece (p ≥ 1):**
```
           t − tᵢ                    tᵢ₊ₚ₊₁ − t
Nᵢ,ₚ(t) = ─────────── Nᵢ,ₚ₋₁(t)  +  ─────────────── Nᵢ₊₁,ₚ₋₁(t)
           tᵢ₊ₚ − tᵢ                 tᵢ₊ₚ₊₁ − tᵢ₊₁
```

> **Not:** 0/0 durumunda terim sıfır kabul edilir.

---

### 2.6 Düğüm Vektörü (Knot Vector)

Düğüm vektörü, parametrik alanı bölümlere ayırır. Bu uygulama **açık düzgün (open/clamped uniform)** düğüm vektörü kullanır:

```
U = { 0, …, 0 (p+1 kez),  iç değerler,  1, …, 1 (p+1 kez) }
```

Ders notundaki iki NURBS yüzeyi için:
- **u yönü** (5 nokta, derece 3): `{0, 0, 0, 0, 0.5, 1, 1, 1, 1}`
- **v yönü** (2 nokta, derece 1): `{0, 0, 1, 1}`

Düğüm uzunluğu kuralı: `|knot| = n_pts + degree + 1`

---

### 2.7 3B → 2B Projeksiyon

Ders notunda verilen **izometrik/dimetrik projeksiyon** formülü kullanılmaktadır:

```
p'(y', z') = [ 0.7071(−x + y),   0.4082(x + y + 2z) ]
```

Bu uygulama, önce 3B noktayı **Y ekseni etrafında döndürür** (fare ile etkileşimli), ardından projeksiyonu uygular:

```python
# Y ekseni döndürme
rx =  cos(θ) · x + sin(θ) · z
ry =  y
rz = −sin(θ) · x + cos(θ) · z

# İzometrik projeksiyon (ekran y'si tersine çevrilir, +z yukarı)
screen_x =  0.7071 · (−rx + ry) · scale + cx
screen_y = −0.4082 · (rx + ry + 2·rz) · scale + cy
```

---

## 3. Uygulama Özellikleri

| Özellik | Detay |
|---------|-------|
| Yüzey tipleri | Bezier, B-Spline, NURBS |
| Kontrol ağı | Değişken boyut (satır × sütun) |
| Ön tanımlı yüzeyler | Varsayılan (4×4 Bezier), Yüzey 1 ve 2 (ders notundan) |
| Derece ayarı | u ve v yönleri bağımsız (1–9) |
| Tel kafes görünüm | 20×20 izoparametrik eğri |
| Kontrol ağı gösterimi | Kesik çizgili mesh |
| 3B döndürme | Sol tık + sürükle (Y ekseni) |
| Yakınlaştırma | Fare tekerleği |
| Nokta seçimi | Sol tık ile en yakın kontrol noktası |
| Nokta düzenleme | X, Y, Z, W değerleri doğrudan giriş |
| Projeksiyon | Ders notundaki formül + Y döndürme |
| Eksen göstergesi | Sol alt köşe XYZ yönleri |

---

## 4. Arayüz Bileşenleri

### 4.1 Sol Kontrol Paneli

Sol panel kaydırılabilir bir liste alanından oluşur ve şu bölümleri içerir:

| Bölüm | İçerik |
|-------|--------|
| **Yüzey Tipi** | Bezier / B-Spline / NURBS radyo düğmeleri |
| **Ön Tanımlı Yüzeyler** | Varsayılan, Yüzey 1, Yüzey 2 düğmeleri |
| **Derece (u / v)** | Artırma/azaltma kutucukları |
| **Kontrol Ağı** | Aktif satır × sütun sayısı |
| **u Düğüm Vektörü** | Hesaplanan/yüklenen u düğümleri |
| **v Düğüm Vektörü** | Hesaplanan/yüklenen v düğümleri |
| **Seçili Kontrol Noktası** | P(i,j) etiketi + X/Y/Z/W giriş alanları |
| **3B→2B Projeksiyon** | Ders notundan formül referansı |
| **Kontroller** | Fare kullanım kılavuzu |
| **Sıfırla** | Varsayılan yüzeye dön |

### 4.2 Ana Çizim Alanı (Tuval)

Sağ bölümdeki tuval şunları gösterir:

- **Arka plan ızgarası** (50 px aralıklı)
- **Yüzey tel kafesi** (izoparametrik eğriler; Bezier=mavi, B-Spline=yeşil, NURBS=turuncu)
- **Kontrol ağı** (kesik çizgili, koyu mavi)
- **Kontrol noktaları** (sarı daireler, P(i,j) etiketli)
- **Seçili nokta** sarı halka ile vurgulanır
- **XYZ ekseni göstergesi** sol alt köşede
- **Yüzey tipi etiketi** sağ üst köşede

### 4.3 Durum Çubuğu

Alttaki durum çubuğu, seçilen noktanın koordinatlarını veya genel kullanım ipuçlarını gösterir.

---

## 5. Kullanım Adımları

### 5.1 Uygulamayı Başlatma

```bash
python surface_editor.py
```

veya derlenmiş sürüm:

```bash
SurfaceEditor.exe
```

Uygulama, 4×4 bikübik **Bezier yüzeyi** ile başlar (dalgalı saddle şekli).

---

### 5.2 Ön Tanımlı Yüzey Seçimi

Sol paneldeki **"Ön Tanımlı Yüzeyler"** bölümünden üç seçenek mevcuttur:

| Düğme | Açıklama |
|-------|----------|
| **Varsayılan** | 4×4 bikübik Bezier dalgalı yüzey |
| **Yüzey 1** | Ders notundaki 1. NURBS yüzeyi (dalga formu) |
| **Yüzey 2** | Ders notundaki 2. NURBS yüzeyi (kanat/bıçak formu) |

> Yüzey 1 ve Yüzey 2, ders notunun 7–8. sayfalarındaki NURBS verilerini birebir kullanır:  
> K1=4, M1=3, K2=1, M2=1, S={0,0,0,0,0.5,1,1,1,1}, T={0,0,1,1}

---

### 5.3 Yüzey Tipini Değiştirme

Sol panelin en üstündeki radyo düğmelerinden yüzey tipi seçilir:

- **Bezier** → Bernstein taban polinomları, derece = ağ boyutu − 1
- **B-Spline** → Cox–de Boor, serbestçe ayarlanabilir derece
- **NURBS** → Rasyonel B-Spline, ağırlık etkisi aktif

> Yüzey tipi değiştirildiğinde kontrol noktaları ve ağırlıklar korunur; yalnızca hesaplama yöntemi değişir.

---

### 5.4 Derece Ayarlama

**"Derece (u / v)"** bölümündeki artırma/azaltma kutucuklarıyla u ve v yönlerinin dereceleri ayrı ayrı ayarlanabilir.

- Minimum: 1 (doğrusal)
- Maksimum: kontrol noktası sayısı − 1
- Derece değiştiğinde düğüm vektörü otomatik yeniden hesaplanır
- **Bezier yüzeyinde derece, ağ boyutuna bağlı olduğundan bu ayar etkisizdir**

---

### 5.5 Görünümü Döndürme ve Yakınlaştırma

| İşlem | Kontrol |
|-------|---------|
| Y ekseni etrafında döndür | Sol tık + sürükle (yatay hareket) |
| Yakınlaştır | Fare tekerleği ↑ |
| Uzaklaştır | Fare tekerleği ↓ |

---

### 5.6 Kontrol Noktası Seçme ve Düzenleme

1. Tuval üzerinde bir kontrol noktasına **sol tıklayın** (sarı halka seçimi gösterir)
2. Sol panelde **X, Y, Z, W** değerlerini girin
3. **Enter** tuşuna basın veya **"Uygula"** düğmesine tıklayın
4. Yüzey anlık olarak güncellenir

> **W (ağırlık):** Yalnızca NURBS tipinde anlamlıdır. W > 1 yüzeyi noktaya çeker, W < 1 uzaklaştırır. Bezier ve B-Spline'da tüm ağırlıklar 1 kabul edilir.

---

### 5.7 Sıfırlama

**"Varsayılana Sıfırla"** düğmesi, tüm ayarları ve kontrol noktalarını başlangıç durumuna (4×4 Bezier) döndürür.

---

## 6. Teknik Detaylar

### 6.1 Gereksinimler

- Python 3.8 veya üstü
- Ek kütüphane **gerekmez** (`tkinter` ve `math` standart kütüphaneden)

### 6.2 Çalıştırma

```bash
python surface_editor.py
```

**Exe olarak derleme (PyInstaller):**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name SurfaceEditor surface_editor.py
# Çıktı: dist/SurfaceEditor.exe
```

### 6.3 Kod Yapısı

```
surface_editor.py
├── Matematik fonksiyonları
│   ├── _comb(n, k)                  – Binom katsayısı
│   ├── bernstein(n, i, t)           – Bernstein B_{i,n}(t)
│   ├── cox_de_boor(t, i, p, knots)  – Cox–de Boor N_{i,p}(t)
│   ├── make_knots(n_pts, degree)    – Açık uniform düğüm vektörü
│   └── eval_surface(u,v,...)        – Yüzey noktası hesaplama
│
├── 3B → 2B projeksiyon
│   └── project(x,y,z, angle_y, scale, cx, cy)
│
├── Ön tanımlı veri
│   ├── _make_preset_1()  – NURBS Yüzey 1 (ders notu)
│   ├── _make_preset_2()  – NURBS Yüzey 2 (ders notu)
│   └── _make_default()   – 4×4 Bezier varsayılan
│
└── SurfaceEditor sınıfı
    ├── __init__           – Durum değişkenleri, fontlar
    ├── _build_ui          – Ana çerçeve düzeni
    ├── _build_left_panel  – Kaydırılabilir sol panel
    ├── _build_canvas_area – Tuval ve olay bağlayıcıları
    ├── _on_click/drag/wheel – Fare olayları
    ├── _nearest_ctrl_pt   – En yakın kontrol noktası
    ├── _load_preset       – Ön tanımlı yüzey yükleme
    ├── _auto_scale        – Otomatik ölçek ayarı
    ├── _on_type_change    – Yüzey tipi değişimi
    ├── _on_degree_change  – Derece değişimi
    ├── _apply_edit        – Nokta koordinatı güncelleme
    ├── _refresh_panel     – Sol panel yenileme
    ├── _compute_wireframe – İzoparametrik eğri hesaplama
    └── _redraw            – Tam tuval yeniden çizimi
```

### 6.4 Temel Algoritmalar

#### Yüzey Tel Kafes Hesaplama

```
U_STEPS = 20, V_STEPS = 20

Sabit-v eğrileri (V_STEPS+1 adet):
  Her v ∈ {v₀, v₀+(v₁-v₀)/V_STEPS, ..., v₁} için:
    u ∈ [u₀, u₁] arasında U_STEPS+1 nokta hesapla
    → polyline olarak çiz

Sabit-u eğrileri (U_STEPS+1 adet):
  Her u ∈ {u₀, ..., u₁} için:
    v ∈ [v₀, v₁] arasında V_STEPS+1 nokta hesapla
    → polyline olarak çiz
```

**Toplam hesaplama:** `(21+21) × 21 = 882` yüzey noktası (her çizimde)

#### Ön Tanımlı Veri – Ders Notu Uyumu

Yüzey 1 ve Yüzey 2, ders notunun 7–8. sayfalarındaki verilerle birebir örtüşür:

```
K1=4  M1=3  R=8   → u yönü: 5 nokta, derece 3, 9 düğüm
K2=1  M2=1  S=3   → v yönü: 2 nokta, derece 1, 4 düğüm

S_knot = {0, 0, 0, 0, 0.5, 1, 1, 1, 1}
T_knot = {0, 0, 1, 1}
```

---

## 7. Ders Notu Referansı

Bu uygulama, **"6. Hafta – Parametrik Yüzeyler"** ders notunu temel alır:

| Denklem | Formül | Uygulama Karşılığı |
|---------|--------|---------------------|
| (1) | `S(u,v) = ΣΣ Pᵢⱼ Bᵢ,ₙ(u) Bⱼ,ₘ(v)` | `eval_surface(..., 'bezier')` |
| (2) | `P(u,v) = ΣΣ Pᵢⱼ Nᵢ,ₖ(u) Nⱼ,ₗ(v)` | `eval_surface(..., 'bspline')` |
| (3) | Matris formu B-Spline yüzeyi | `eval_surface` iç döngüsü |
| (4) | 4×4 kübik B-Spline yaması | Yüzey 1 / Yüzey 2 örnekleri |
| (5) | NURBS eğrisi rasyonel formül | `cox_de_boor` + ağırlık |
| (6) | NURBS yüzeyi `Rᵢ,ₖ,ⱼ,ₗ(u,v)` | `eval_surface(..., 'nurbs')` |
| Ek bilgi | `p'=[0.7071(−x+y), 0.4082(x+y+2z)]` | `project(x,y,z,...)` |

---

## 8. Sonuç

Bu uygulama, 3B parametrik yüzey teorisini görselleştirip deneyimlemenin etkileşimli bir aracıdır. Kullanıcı aynı kontrol ağı üzerinde Bezier, B-Spline ve NURBS yüzeylerini anlık olarak karşılaştırabilir; derece, düğüm vektörü ve ağırlık değişikliklerinin yüzey üzerindeki etkisini doğrudan gözlemleyebilir.

Ders notundaki iki NURBS yüzey örneğini (pervane/bıçak formları) hazır ön-tanımlı veri olarak içermesi, teorik formüllerin gerçek verilerle doğrulanmasını kolaylaştırmaktadır.
