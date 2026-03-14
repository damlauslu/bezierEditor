# B-Spline Eğrisi Editörü – Teknik Dokümantasyon

**Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Odev 2**

| Alan | Bilgi |
|------|-------|
| Programlama Dili | Python 3.8+ (yalnızca standart kütüphane) |
| Grafik Arayüz | tkinter |
| Konu | Ayarlanabilir Dereceli B-Spline Eğrisi |
| Tarih | Mart 2026 |

---

## İçindekiler

1. [Giriş ve Genel Bakış](#1-giriş-ve-genel-bakış)
2. [Matematiksel Temel](#2-matematiksel-temel)
   - 2.1 B-Spline Eğrisi Nedir?
   - 2.2 Cox–de Boor Özyineleme Formülü
   - 2.3 Düğüm Vektörü
   - 2.4 Uniform Clamped Düğüm Vektörü
   - 2.5 Eğri Uzunluğu
3. [Uygulama Özellikleri](#3-uygulama-özellikleri)
4. [Arayüz Bileşenleri](#4-arayüz-bileşenleri)
   - 4.1 Sol Kontrol Paneli
   - 4.2 Ana Çizim Alanı (Tuval)
   - 4.3 Durum Çubuğu
5. [Kullanım Adımları](#5-kullanım-adımları)
   - 5.1 Uygulamayı Başlatma
   - 5.2 Kontrol Noktası Ekleme
   - 5.3 Derece ve Order Ayarlama
   - 5.4 Düğüm Vektörü Ayarlama
   - 5.5 Eğriyi İnceleme
   - 5.6 Noktaları Düzenleme
   - 5.7 Sıfırlama
6. [Teknik Detaylar](#6-teknik-detaylar)
   - 6.1 Gereksinimler
   - 6.2 Çalıştırma
   - 6.3 Kod Yapısı
   - 6.4 Temel Algoritmalar
7. [Sonuç](#7-sonuç)

---

## 1. Giriş ve Genel Bakış

Bu uygulama, **B-Spline eğrisi** kavramını görsel olarak anlamayı ve etkileşimli biçimde keşfetmeyi sağlayan bir masaüstü editörüdür. Kullanıcı istediği sayıda kontrol noktasını fareyle tuval üzerine işaretler; eğri derecesini (p) ve düğüm vektörünü (knot vector) sol panelden ayarlar. Uygulama, Cox–de Boor algoritmasıyla B-Spline eğrisini anlık olarak hesaplayıp çizer. Yeni kontrol noktası eklendikçe eğri otomatik güncellenir; noktalar sürüklenebilir.

> **Neden B-Spline Eğrileri?**
> Bezier eğrilerinin en önemli sınırlaması, tüm kontrol noktalarının eğrinin global şeklini etkilemesidir. B-Spline eğrileri bunu **yerel kontrol** özelliğiyle aşar: bir kontrol noktasının hareketi yalnızca yakın çevresindeki eğri parçasını etkiler. Bu özellik, B-Spline'ları CAD sistemleri, bilgisayar grafiği, animasyon ve oyun motorlarında tercih edilen standart hale getirmiştir. NURBS (Non-Uniform Rational B-Spline) gibi daha gelişmiş eğri türleri de B-Spline'ın doğal bir uzantısıdır.

Uygulama yalnızca Python 3 standart kütüphanesi (`tkinter` + `math`) kullanılarak geliştirilmiştir; **ek paket kurulumu gerekmemektedir**.

---

## 2. Matematiksel Temel

### 2.1 B-Spline Eğrisi Nedir?

B-Spline eğrisi, *n+1* kontrol noktası **P₀, P₁, …, Pₙ**, bir **derece p** (veya eşdeğer olarak order *k = p+1*) ve bir **düğüm vektörü** **T** tarafından tamamen belirlenen parametrik bir eğridir.

```
S(t) = Σ Nᵢ,ₚ(t) · Pᵢ     (i = 0, 1, …, n)
```

| Sembol | Açıklama |
|--------|----------|
| **Pᵢ** | i. kontrol noktası |
| **Nᵢ,ₚ(t)** | i. B-Spline taban fonksiyonu, derece p |
| **t** | Parametre değeri, T₀ ≤ t ≤ Tₘ |
| **p** | Eğri derecesi (order k = p+1) |
| **T = [t₀, t₁, …, tₘ]** | Düğüm vektörü, m = n + p + 1 |

**Bezier ile farklar:**

| Özellik | Bezier | B-Spline |
|---------|--------|----------|
| Kontrol noktası sayısı | Sabit (dereceden bağımlı) | İstenen sayıda |
| Etki alanı | Global (tüm noktalar her yeri etkiler) | Yerel (bir nokta en fazla p+1 aralığı etkiler) |
| Derece ayarı | Nokta sayısıyla bağlantılı | Nokta sayısından bağımsız ayarlanabilir |
| Süreklilik | C^(n-1) | Düğüm vektörüne bağlı, tipik olarak C^(p-1) |

### 2.2 Cox–de Boor Özyineleme Formülü

B-Spline taban fonksiyonları **Cox–de Boor özyinelemesiyle** hesaplanır:

**Taban durumu (p = 0):**

```
         ⎧ 1   eğer tᵢ ≤ t < tᵢ₊₁
Nᵢ,₀(t) = ⎨
         ⎩ 0   diğer durumlarda
```

**Özyinelemeli adım (p ≥ 1):**

```
             (t − tᵢ)                       (tᵢ₊ₚ₊₁ − t)
Nᵢ,ₚ(t) = ————————————— · Nᵢ,ₚ₋₁(t)  +  ————————————————— · Nᵢ₊₁,ₚ₋₁(t)
           (tᵢ₊ₚ − tᵢ)                     (tᵢ₊ₚ₊₁ − tᵢ₊₁)
```

> **Sıfıra bölme kuralı:** Payda sıfır olduğunda ilgili terim sıfır kabul edilir (`0/0 = 0`). Bu kural hesabı her zaman geçerli kılar ve süreksizliği engeller.

Bu özyineleme, eğri noktasını doğrudan matris çarpımı yerine ağaç biçiminde hesaplar. Uygulamada `cox_de_boor(t, i, p, knots)` fonksiyonu olarak kodlanmıştır.

### 2.3 Düğüm Vektörü

Düğüm vektörü **T = [t₀, t₁, …, tₘ]**, parametrik aralığı aralıklara (knot spans) bölen azalmayan gerçel sayı dizisidir.

**Temel gereksinimler:**

- Uzunluk: `m + 1 = n + p + 2` (n+1 kontrol noktası, derece p için)
- Azalmama koşulu: `t₀ ≤ t₁ ≤ … ≤ tₘ`
- Eğri `t ∈ [t_p, t_{n+1}]` aralığında tanımlıdır

**Tekrar eden düğümler:** Bir düğüm değeri *r* kez tekrar ederse, o noktadaki süreklilik derecesi `C^(p−r)` olur. Özellikle bir değer *p+1* kez tekrarlanırsa eğri o noktadan geçer (interpolasyon).

### 2.4 Uniform Clamped Düğüm Vektörü

Uygulama "otomatik" modda **uniform clamped** (tekdüze tutturulmuş) düğüm vektörü üretir. Bu, en yaygın kullanılan düğüm vektörü türüdür:

```
Yapı:
  ┌────────────────────────────────────────────────────────┐
  │  p+1 kez 0  │  iç düğümler  │  p+1 kez 1             │
  └────────────────────────────────────────────────────────┘
```

n+1 kontrol noktası ve derece p için:

```
tᵢ = 0                          eğer i < p+1
tᵢ = (i − p) / (n − p)         eğer p+1 ≤ i ≤ n
tᵢ = 1                          eğer i > n
```

**Örnek:** 6 nokta (n=5), derece 3 (p=3) için m = 5+3+1 = 9:

```
T = [0, 0, 0, 0, 1/3, 2/3, 1, 1, 1, 1]
      ←p+1=4→              ←p+1=4→
```

**Clamped özelliğinin önemi:** Baştaki ve sondaki p+1 tekrar sayesinde eğri, ilk kontrol noktasından (P₀) başlar ve son kontrol noktasında (Pₙ) biter — Bezier eğrisindeki uç nokta interpolasyonuna benzer şekilde.

### 2.5 Eğri Uzunluğu

B-Spline eğrisinin analitik uzunluğunun kapalı formu yoktur. Uygulama **kümülatif kiriş toplamı** yöntemiyle sayısal yaklaşım kullanır:

```
L ≈ Σ ‖S(tᵢ) − S(tᵢ₋₁)‖     (i = 1..N,  N = 300 adım)

Her adımda: Δᵢ = √( (xᵢ−xᵢ₋₁)² + (yᵢ−yᵢ₋₁)² )
```

Örnekleme parametrenin etkin aralığında `[t_p, t_{n+1}]` yapılır. 300 adım, görsel hassasiyet için yeterlidir. Bulunan sonuç *"L ≈ … piksel"* olarak gösterilir.

---

## 3. Uygulama Özellikleri

| Özellik | Açıklama |
|---------|----------|
| **Fareyle Nokta Girişi** | Tuvale her tıklamada yeni kontrol noktası eklenir; minimum nokta sayısı beklenmez, eğri minimum koşul sağlandığı anda çizilir |
| **Sınırsız Nokta** | Kontrol noktası sayısında üst sınır yoktur; eğri her yeni noktayla anlık yenilenir |
| **Derece Ayarı** | Sol panelden Spinbox ile eğri derecesi (p) 1'den 20'ye kadar ayarlanabilir; order değeri (k = p+1) otomatik hesaplanır |
| **Düğüm Vektörü – Otomatik Mod** | Uniform clamped düğüm vektörü nokta sayısı ve dereceye göre otomatik üretilir |
| **Düğüm Vektörü – Manuel Mod** | Kullanıcı boşluk veya virgülle ayrılmış düğüm değerlerini klavyeden girebilir; uzunluk ve monotonluk doğrulaması anlık yapılır |
| **Anlık Eğri Çizimi** | Derece + 1 koşulu sağlandığı anda eğri çizilir; nokta, derece veya düğüm değiştiğinde eğri anlık güncellenir |
| **Kontrol Çokgeni** | Kontrol noktalarını P₀→P₁→…→Pₙ sırasıyla birleştiren kesikli çizgi |
| **Sürükleme** | Mevcut herhangi bir kontrol noktası fareyle sürüklenerek yeniden konumlandırılabilir; eğri gerçek zamanlı güncellenir |
| **Fare Üzeri t Parametresi** | Fare tuvalde hareket ettiğinde eğri üzerindeki en yakın nokta hesaplanır; t değeri ve S(t) koordinatları sol panelde canlı güncellenir |
| **Eğri Uzunluğu** | 300 adımlı sayısal integrasyon ile eğrinin piksel cinsinden yaklaşık uzunluğu hesaplanır |
| **Koordinat Listesi** | Tüm kontrol noktalarının anlık koordinatları sol panelde listelenir |
| **Koordinat Düzenleme – Klavye** | İndeks + X/Y giriş alanlarıyla herhangi bir noktanın koordinatı klavyeden güncellenebilir |
| **Koordinat Düzenleme – Mouse ile** | İndeks girilip "Mouse ile Güncelle" butonuna basıldıktan sonra tuval üzerinde tıklanan konum o noktaya atanır; ESC veya butona tekrar tıklanarak iptal edilebilir |
| **Son Noktayı Sil** | Tek tuşla son eklenen kontrol noktası kaldırılabilir |
| **Sıfırlama** | Tüm noktalar, eğri, derece ve parametreler başlangıç durumuna döner |
| **Izgara Arka Planı** | 50 piksel aralıklı yatay/dikey ızgara çizgileri konum tahminine yardımcı olur |
| **Duyarlı Pencere** | Pencere yeniden boyutlandırıldığında tuval ve eğri otomatik ölçeklenir |

---

## 4. Arayüz Bileşenleri

Uygulama penceresi iki ana alandan oluşmaktadır: sol sabit genişlikli (300 px) **kontrol paneli** ve sağda tam ekrana genişleyen **çizim tuvali**.

### 4.1 Sol Kontrol Paneli

| Bileşen | İçerik |
|---------|--------|
| **Derece / Order** | Derece (p) için Spinbox giriş alanı; order (k = p+1) otomatik olarak yanında gösterilir; geçersiz derece için uyarı satırı |
| **Eğri Bilgisi** | Kontrol noktası sayısı, güncel derece/order, fare üzeri t değeri, S(t) koordinatı, eğri uzunluğu, fare koordinatı |
| **Düğüm Vektörü** | "Otomatik" / "Manuel giriş" radyo düğmeleri; güncel düğüm vektörünün metin kutusunda gösterimi; manuel modda giriş alanı, Uygula ve Otomatiğe Dön düğmeleri; hata mesajı satırı |
| **Kontrol Noktaları** | Tüm noktaların P0…Pₙ indeksiyle koordinat listesi (kaydırılabilir metin kutusu) |
| **Son Noktayı Sil** | Listenin son elemanını kaldıran düğme |
| **Koordinat Düzenleme** | İndeks, X ve Y giriş alanları + "Koordinatı Güncelle" düğmesi; hata mesajı satırı |
| **Sıfırla** | Panelin en altında; tüm durumu sıfırlar |

Sol panel dikey kaydırma çubuğuna sahiptir ve fare tekerleğiyle kaydırılabilir.

### 4.2 Ana Çizim Alanı (Tuval)

Koyu lacivert arka plan üzerine şunlar çizilir:

- **Izgara:** 50 px aralıklı gri yatay/dikey çizgiler
- **Kontrol noktaları:** Renkli (12 renklik döngüsel palet) dolgulu daireler; yanlarında `Pᵢ(x,y)` etiketi
- **Kontrol çokgeni:** P₀→P₁→…→Pₙ arası kesikli çizgiler
- **B-Spline eğrisi:** 400 kırık çizgi parçasından oluşan parlak camgöbeği eğri
- **Sürükleme halkası:** Sürüklenen nokta sarı dış halkayla işaretlenir
- **Mouse düzenleme halkası:** Mouse ile güncelleme modunda hedef nokta çift sarı/turuncu halkayla vurgulanır
- **Fare üzeri işaretçi:** En yakın eğri noktasında beyaz dolgulu küçük daire + `t=…` etiketi

### 4.3 Durum Çubuğu

Pencerenin en altında konumlanan durum çubuğu, kullanıcıya anlık bağlam bilgisi gösterir:

| Durum | Mesaj |
|-------|-------|
| Hiç nokta yok | Tuvale tıklayarak kontrol noktası ekleyin. |
| Yetersiz nokta | n nokta var. Derece p için en az p+1 nokta gerekli. |
| Eğri hazır | n kontrol noktası \| Derece: p \| Sürükle: noktayı taşı \| Tıkla: yeni nokta |
| Mouse düzenleme modu | Mouse düzenleme modu: Pn için yeni konumu tıklayın \| ESC veya İptal ile çıkın |

---

## 5. Kullanım Adımları

### 5.1 Uygulamayı Başlatma

**Python ile:**

```bash
python bspline_editor.py
```

Uygulama açıldığında tuval boştur, derece 3 (kübik) olarak ayarlıdır, düğüm vektörü otomatik moddadır ve durum çubuğu ilk yönergeyi gösterir.

### 5.2 Kontrol Noktası Ekleme

Tuvale tıklayın; her tıklamada yeni bir kontrol noktası eklenir. Kontrol noktaları otomatik olarak P₀, P₁, P₂, … şeklinde numaralandırılır.

- **Eğri ne zaman görünür?** Nokta sayısı `derece + 1`'e ulaştığı anda eğri ilk kez çizilir. Derece 3 için 4. nokta eklendiğinde eğri belirir.
- **Eklemeye devam:** 4. noktadan sonra da tıklamaya devam edebilirsiniz; her yeni nokta eğriyi anlık günceller. Eklenecek nokta sayısında bir sınır yoktur.

### 5.3 Derece ve Order Ayarlama

Sol paneldeki **Derece (p)** Spinbox'ından değeri artırın/azaltın ya da sayıyı doğrudan yazıp Enter'a basın.

- **Minimum:** 1 (doğrusal)
- **Maksimum:** n − 1 (n = kontrol noktası sayısı)
- Degree değiştirildiğinde **order** (k = p + 1) otomatik güncellenir.
- Otomatik düğüm modunda düğüm vektörü yeniden hesaplanır.
- Nokta sayısı yetersizse panelde uyarı mesajı görünür.

**Örnek davranışlar:**

| Kontrol Noktası Sayısı | Derece 1 | Derece 2 | Derece 3 | Derece 4 |
|------------------------|----------|----------|----------|----------|
| 4 | Parçalı doğru | Quadratic | Kübik | — |
| 5 | Parçalı doğru | Quadratic | Kübik | Quartik |
| 6 | Parçalı doğru | Quadratic | Kübik | Quartik |

### 5.4 Düğüm Vektörü Ayarlama

**Otomatik Mod (varsayılan):**

"Otomatik (uniform clamped)" seçeneği işaretli olduğunda uygulama, kontrol noktası sayısı ve derece değiştiğinde düğüm vektörünü otomatik olarak yeniden üretir. Güncel vektör, sol panelin "Düğüm Vektörü" kutusunda anlık gösterilir.

**Manuel Mod:**

1. "Manuel giriş" radyo düğmesini seçin. Giriş alanı açılır; mevcut otomatik vektör oraya kopyalanır.
2. Düğüm değerlerini boşluk veya virgülle ayrılarak yazın. Örnek:
   ```
   0 0 0 0 0.25 0.5 0.75 1 1 1 1
   ```
3. **Uygula** düğmesine tıklayın ya da Enter'a basın.
4. Doğrulama kuralları:
   - Uzunluk: tam olarak `n + p + 2` değer olmalı
   - Monotonluk: değerler azalmayan sırada olmalı
5. Hata varsa kırmızı mesaj gösterilir, vektör uygulanmaz.
6. **Otomatiğe Dön** ile veya radyo düğmesiyle otomatik moda geri dönülebilir.

### 5.5 Eğriyi İnceleme

Eğri çizildikten sonra fareyi tuval üzerinde hareket ettirin:

- Sol panelin **Fare** alanı anlık koordinatı gösterir.
- Fare eğriye yaklaştıkça **t Değeri** ve **S(t) Noktası** güncellenir; tuval üzerinde beyaz yuvarlak işaretçi en yakın eğri noktasına konumlanarak `t` değerini gösterir.
- Sol panelde **Eğri Uzunluğu** (L) piksel cinsinden görüntülenir.
- **Kontrol Noktaları** listesi tüm noktaların koordinatlarını gösterir.

### 5.6 Noktaları Düzenleme

**Yöntem A – Sürükleme:**

Varolan bir kontrol noktasının üzerine tıklayın (10 piksel toleranslı) ve fareyi basılı tutarak sürükleyin. Nokta gerçek zamanlı olarak takip edilir, eğri anlık güncellenir.

**Yöntem B – Koordinat Girişi:**

1. Sol panelin "Nokta Koordinatı Düzenle" bölümünde **İndeks** alanına hedef noktanın numarasını yazın (0 tabanlı).
2. **X** ve **Y** alanlarına yeni koordinatları yazın.
3. **Koordinatı Güncelle** düğmesine tıklayın.
4. Geçersiz indeks veya format için kırmızı hata mesajı gösterilir.

**Yöntem C – Mouse ile Yerleştirme:**

1. **İndeks** alanına taşımak istediğiniz noktanın numarasını yazın.
2. **Mouse ile Güncelle** düğmesine tıklayın. Düğme sarıya döner ve "İptal (ESC)" yazısına dönüşür; fare imleci çift artı (`tcross`) biçimine geçer; hedef nokta tuval üzerinde çift sarı/turuncu halkayla vurgulanır; durum çubuğu yönerge gösterir.
3. Tuvalde istediğiniz konuma tıklayın — nokta oraya taşınır, mod otomatik kapanır.
4. Vazgeçmek için **ESC** tuşuna basın veya düğmeye tekrar tıklayın.

**Son Noktayı Silme:**

"Son Noktayı Sil" düğmesine tıklayın. En son eklenen kontrol noktası kaldırılır ve eğri güncellenir.

### 5.7 Sıfırlama

Sol panelin altındaki **Sıfırla** düğmesine tıklayın. Tüm kontrol noktaları, eğri, derece (3'e döner), düğüm vektörü ve hesaplamalar temizlenerek uygulama başlangıç durumuna döner.

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
python bspline_editor.py
```

Windows'ta dosyaya çift tıklanarak da çalıştırılabilir.

**Yürütülebilir (.exe) Oluşturma:**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed bspline_editor.py
```

`dist/bspline_editor.exe` dosyası Python kurulumu olmayan sistemlerde de çalışmaktadır.

### 6.3 Kod Yapısı

Tüm uygulama tek dosyadan (`bspline_editor.py`) oluşmaktadır.

| Bölüm | Sorumluluk |
|-------|------------|
| Sabitler ve renk paleti | Renk tanımları, STEPS sabiti |
| `cox_de_boor(t, i, p, knots)` | Özyinelemeli B-Spline taban fonksiyonu |
| `bspline_point(t, ctrl_pts, knots, degree)` | Eğri noktası hesabı |
| `make_uniform_knots(n_pts, degree)` | Uniform clamped düğüm vektörü üretimi |
| `parse_knot_vector(text)` | Metin ayrıştırma – manuel düğüm girişi |
| `validate_knots(knots, n_pts, degree)` | Düğüm vektörü doğrulama |
| `BSplineEditor.__init__` | Uygulama durumu ve font nesnelerinin başlatılması |
| `_build_ui` ve alt metotlar | Sol panel, tuval, tüm widget'ların oluşturulması |
| `_on_click` | Yeni nokta ekleme veya sürükleme başlatma |
| `_on_drag` | Kontrol noktası sürükleme |
| `_on_release` | Sürükleme sona erme |
| `_on_motion` | Fare hareketi: koordinat + hover hesabı |
| `_on_degree_change` | Derece Spinbox değişikliği |
| `_auto_knots` | Otomatik düğüm vektörü yeniden hesaplama |
| `_on_knot_mode_change` | Otomatik/manuel mod geçişi |
| `_apply_manual_knots` | Manuel düğüm vektörü doğrulama ve uygulama |
| `_delete_last` | Son kontrol noktasını silme |
| `_apply_coord_edit` | Koordinat girişiyle nokta güncelleme |
| `_activate_click_edit` | Mouse ile güncelleme modunu başlatma; indeks doğrulama, imleç ve buton değişikliği |
| `_cancel_click_edit` | Mouse ile güncelleme modundan çıkma (ESC veya buton) |
| `_reset` | Tam sıfırlama |
| `_refresh_all` | Sol panel ve durum çubuğu güncellemesi |
| `_can_draw` | Eğri çizim koşulunun kontrolü |
| `_eval(t)` | Tek parametre değerinde eğri noktası |
| `_closest_t` | Fareye en yakın t parametresi (300 örnek) |
| `_arc_length` | Eğri uzunluğu sayısal integrasyonu (300 adım) |
| Çizim metotları | Izgara, eğri, noktalar, kontrol çokgeni, hover |
| `main` | Giriş noktası: Tk penceresi ve olay döngüsü |

### 6.4 Temel Algoritmalar

#### Cox–de Boor Özyinelemesi (`cox_de_boor`)

B-Spline taban fonksiyonları özyinelemeli olarak hesaplanır. Her `bspline_point` çağrısı, n+1 kontrol noktasının her biri için bir `cox_de_boor` ağacı oluşturur. Derinlik p düzeyindedir.

```python
def cox_de_boor(t, i, p, knots):
    if p == 0:
        if knots[i] <= t < knots[i + 1]:
            return 1.0
        if t == knots[-1] and knots[i] <= t <= knots[i + 1]:
            return 1.0   # son düğümde özel durum
        return 0.0
    denom1 = knots[i + p] - knots[i]
    denom2 = knots[i + p + 1] - knots[i + 1]
    c1 = ((t - knots[i]) / denom1 * cox_de_boor(t, i, p - 1, knots)
          if denom1 != 0 else 0.0)
    c2 = ((knots[i + p + 1] - t) / denom2 * cox_de_boor(t, i + 1, p - 1, knots)
          if denom2 != 0 else 0.0)
    return c1 + c2
```

#### Eğri Noktası Hesabı (`bspline_point`)

n+1 kontrol noktasının her biri için taban fonksiyonu değeri hesaplanır ve ağırlıklı toplamı alınır:

```python
def bspline_point(t, control_pts, knots, degree):
    n = len(control_pts) - 1
    x = sum(cox_de_boor(t, i, degree, knots) * control_pts[i][0]
            for i in range(n + 1))
    y = sum(cox_de_boor(t, i, degree, knots) * control_pts[i][1]
            for i in range(n + 1))
    return (x, y)
```

#### Uniform Clamped Düğüm Vektörü (`make_uniform_knots`)

n_pts kontrol noktası ve degree için tam otomatik üretim:

```python
def make_uniform_knots(n_pts, degree):
    order   = degree + 1
    n_knots = n_pts + order
    knots   = []
    for i in range(n_knots):
        if i < order:
            knots.append(0.0)
        elif i >= n_pts:
            knots.append(1.0)
        else:
            knots.append((i - degree) / (n_pts - degree))
    return knots
```

#### En Yakın t Parametresi (`_closest_t`)

Farenin eğri üzerindeki en yakın noktasını bulmak için kaba kuvvet arama: parametrenin etkin aralığı `[t_p, t_{n+1}]`, 300 eşit adıma bölünür; her adımda Öklid uzaklığı hesaplanır, minimum uzaklıklı t değeri döndürülür.

```python
def _closest_t(self, mx, my, n=300):
    t_start = self.knots[self.degree]
    t_end   = self.knots[-(self.degree + 1)]
    best_t, best_d, best_pt = t_start, float('inf'), None
    for i in range(n + 1):
        t  = t_start + (t_end - t_start) * i / n
        pt = self._eval(t)
        d  = (pt[0] - mx)**2 + (pt[1] - my)**2
        if d < best_d:
            best_t, best_d, best_pt = t, d, pt
    return best_t, best_pt
```

#### Eğri Uzunluğu (`_arc_length`)

Ardışık örnekler arasındaki kiriş uzunlukları toplanır. Örnekleme parametrenin etkin aralığında yapılır:

```python
def _arc_length(self, n=300):
    t_start = self.knots[self.degree]
    t_end   = self.knots[-(self.degree + 1)]
    total = 0.0
    prev  = self._eval(t_start)
    for i in range(1, n + 1):
        t    = t_start + (t_end - t_start) * i / n
        curr = self._eval(t)
        dx, dy = curr[0] - prev[0], curr[1] - prev[1]
        total += math.sqrt(dx * dx + dy * dy)
        prev = curr
    return total
```

#### Yeniden Çizim Stratejisi

Yapısal değişiklikler (nokta ekleme/güncelleme/sürükleme, derece/düğüm değişikliği, pencere yeniden boyutlandırma) tüm tuvali silen ve sıfırdan çizen `_redraw()` metodunu çağırır. Yalnızca fare hover işaretçisi `canvas.delete('hover')` ile seçici olarak silinip yeniden çizilir; bu sayede her fare hareketi için tam yeniden çizim yapılmaz.

---

## 7. Sonuç

Bu uygulama, B-Spline eğrisinin matematiksel temelini görsel ve etkileşimli biçimde deneyimlemeyi sağlamaktadır. Kullanıcı istediği sayıda kontrol noktasını fareyle tanımlar; derece ve düğüm vektörünü anlık olarak değiştirir. Uygulama Cox–de Boor algoritmasıyla eğriyi hesaplar, kontrol çokgenini görselleştirir, hover ile t parametresini gösterir ve eğri uzunluğunu sayısal integrasyon ile tahmin eder.

**Uygulamanın sunduğu temel öğrenme çıktıları:**

- Kontrol noktaları ile eğri şekli arasındaki **yerel kontrol** ilişkisinin gözlemlenmesi
- Derece değişikliğinin eğri pürüzlülüğüne etkisinin anlık görülmesi (düşük derece → köşeli, yüksek derece → pürüzsüz)
- Düğüm vektörünün eğri tanım aralığını ve sürekliliğini nasıl belirlediğinin keşfedilmesi
- Uniform clamped yapısının uç nokta interpolasyonunu nasıl sağladığının görsel olarak kavranması
- Cox–de Boor özyinelemesinin adım adım Bernstein yerine neden kullanıldığının anlaşılması
- B-Spline ile Bezier arasındaki farkların (global vs. yerel etki, sabit vs. değişken derece) pratik olarak deneyimlenmesi

---

*Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Ödev 2*
