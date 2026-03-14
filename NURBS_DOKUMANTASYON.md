# NURBS Eğrisi Editörü – Teknik Dokümantasyon

**Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Odev 3**

| Alan | Bilgi |
|------|-------|
| Programlama Dili | Python 3.8+ (yalnızca standart kütüphane) |
| Grafik Arayüz | tkinter |
| Konu | NURBS (Non-Uniform Rational B-Spline) Eğrisi |
| Tarih | Mart 2026 |

---

## İçindekiler

1. [Giriş ve Genel Bakış](#1-giriş-ve-genel-bakış)
2. [Matematiksel Temel](#2-matematiksel-temel)
   - 2.1 NURBS Nedir?
   - 2.2 Rasyonel Formül
   - 2.3 Ağırlıkların Etkisi
   - 2.4 Cox–de Boor Özyinelemesi
   - 2.5 Düğüm Vektörü ve Uniform Clamped Yapısı
   - 2.6 B-Spline ve Bezier ile İlişki
   - 2.7 Eğri Uzunluğu
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
   - 5.5 Ağırlık Düzenleme
   - 5.6 Eğriyi İnceleme
   - 5.7 Noktaları Düzenleme
   - 5.8 Sıfırlama
6. [Teknik Detaylar](#6-teknik-detaylar)
   - 6.1 Gereksinimler
   - 6.2 Çalıştırma
   - 6.3 Kod Yapısı
   - 6.4 Temel Algoritmalar
7. [Sonuç](#7-sonuç)

---

## 1. Giriş ve Genel Bakış

Bu uygulama, **NURBS (Non-Uniform Rational B-Spline)** eğrisini görsel olarak anlamayı ve etkileşimli biçimde keşfetmeyi sağlayan bir masaüstü editörüdür. NURBS, B-Spline eğrisinin rasyonel (kesirli) bir genellemesidir; her kontrol noktasına bir **ağırlık (wᵢ)** eklenerek eğri üzerindeki yerel etki derecesi ayarlanabilir hale gelir.

Kullanıcı fareyle tuval üzerine kontrol noktaları yerleştirir; derece (p), düğüm vektörü (T) ve her noktanın ağırlığını (wᵢ) sol panelden anlık olarak değiştirir. Eğri her parametre güncellemesinde gerçek zamanlı olarak yeniden hesaplanıp çizilir.

> **Neden NURBS?**
> B-Spline eğrileri serbest formda şekiller için güçlüdür, ancak konik kesitler (daire, elips, parabol, hiperbol) gibi **analitik eğrileri tam olarak temsil edemezler** — yalnızca yaklaşık gösterim üretirler. NURBS ise ağırlıklar aracılığıyla hem serbest form hem de analitik eğrileri **tek bir birleşik formülasyon** altında tam olarak ifade edebilir. Bu nedenle CAD yazılımlarının (AutoCAD, SolidWorks, CATIA, Rhino) tamamı ve film/oyun endüstrisindeki üretim araçları NURBS'ü temel eğri/yüzey standardı olarak kullanmaktadır.

Uygulama yalnızca Python 3 standart kütüphanesi (`tkinter` + `math`) kullanılarak geliştirilmiştir; **ek paket kurulumu gerekmemektedir**.

---

## 2. Matematiksel Temel

### 2.1 NURBS Nedir?

NURBS eğrisi, n+1 kontrol noktası **P₀, P₁, …, Pₙ**, karşılık gelen **ağırlıklar w₀, w₁, …, wₙ**, bir **derece p** ve bir **düğüm vektörü T** tarafından belirlenen **parçalı rasyonel polinom** eğrisidir.

| Sembol | Açıklama |
|--------|----------|
| **Pᵢ** | i. kontrol noktası |
| **wᵢ** | i. kontrol noktasının ağırlığı (wᵢ ≥ 0) |
| **Nᵢ,ₚ(u)** | i. B-Spline taban fonksiyonu, derece p |
| **u** | Parametre değeri, u ∈ [uₚ, uₙ₊₁] |
| **p** | Eğri derecesi (order k = p+1) |
| **T = [u₀, u₁, …, uₘ]** | Düğüm vektörü, m = n + p + 1 |

### 2.2 Rasyonel Formül

NURBS eğrisinin parametrik denklemi:

```
         Σ [ Nᵢ,ₚ(u) · wᵢ · Pᵢ ]
C(u) = ——————————————————————————————     (i = 0, 1, …, n)
              Σ [ Nᵢ,ₚ(u) · wᵢ ]
```

Bu ifadeyi daha kompakt yazmak için **rasyonel taban fonksiyonu** Rᵢ,ₚ(u) tanımlanır:

```
           Nᵢ,ₚ(u) · wᵢ
Rᵢ,ₚ(u) = ————————————————————
            Σ [ Nⱼ,ₚ(u) · wⱼ ]
```

Böylece:

```
C(u) = Σ Rᵢ,ₚ(u) · Pᵢ
```

**B-Spline'dan fark:** B-Spline'da payda her zaman 1'dir (Nᵢ,ₚ taban fonksiyonları bölüm özdeşliğini sağlar). NURBS'te ağırlıklar payda toplamını 1'den farklı kılar → formül **rasyonel** (kesirli) olur.

### 2.3 Ağırlıkların Etkisi

Ağırlık wᵢ, i. kontrol noktasının eğri üzerindeki **çekim gücünü** belirler:

| Ağırlık Değeri | Etki |
|----------------|------|
| `wᵢ = 1` | Standart B-Spline davranışı |
| `wᵢ > 1` | Eğri o noktaya **doğru çekilir**; ağırlık arttıkça eğri noktaya daha yakın geçer |
| `0 < wᵢ < 1` | Eğri o noktadan **uzaklaşır** |
| `wᵢ = 0` | Nokta eğri üzerinde hiçbir etkiye sahip değildir; ilgili Rᵢ,ₚ = 0 |

**Özel durum — tüm ağırlıklar eşit:** Tüm wᵢ değerleri aynı olduğunda NURBS, standart (ağırlıksız) B-Spline ile özdeşleşir.

**Özel durum — konik kesitler:** Uygun kontrol noktaları ve `wᵢ = cos(θ/2)` ağırlıkları seçildiğinde NURBS, bir daire yayını **tam olarak** (yaklaşık değil) temsil eder. Bu, B-Spline ile asla mümkün değildir.

### 2.4 Cox–de Boor Özyinelemesi

NURBS taban fonksiyonları Nᵢ,ₚ(u), B-Spline'daki Cox–de Boor özyinelemesiyle birebir aynı formülle hesaplanır:

**Taban durumu (p = 0):**

```
         ⎧ 1   eğer uᵢ ≤ u < uᵢ₊₁
Nᵢ,₀(u) = ⎨
         ⎩ 0   diğer durumlarda
```

**Özyinelemeli adım (p ≥ 1):**

```
             (u − uᵢ)                       (uᵢ₊ₚ₊₁ − u)
Nᵢ,ₚ(u) = ————————————— · Nᵢ,ₚ₋₁(u)  +  ————————————————— · Nᵢ₊₁,ₚ₋₁(u)
           (uᵢ₊ₚ − uᵢ)                     (uᵢ₊ₚ₊₁ − uᵢ₊₁)
```

> **Sıfıra bölme kuralı:** Payda sıfır olduğunda ilgili terim sıfır kabul edilir.

NURBS'ü B-Spline'dan matematiksel olarak ayıran tek şey bu taban fonksiyonlarının ağırlıklarla çarpılarak **rasyonel** forma getirilmesidir.

### 2.5 Düğüm Vektörü ve Uniform Clamped Yapısı

Düğüm vektörü **T = [u₀, u₁, …, uₘ]** azalmayan gerçel sayı dizisidir; uzunluğu `m + 1 = n + p + 2`'dir.

Uygulama otomatik modda **uniform clamped** düğüm vektörü üretir:

```
uᵢ = 0                          eğer i < p+1
uᵢ = (i − p) / (n − p)         eğer p+1 ≤ i ≤ n
uᵢ = 1                          eğer i > n
```

Bu yapı, eğrinin P₀'dan başlayıp Pₙ'de bitmesini (uç nokta interpolasyonu) garanti eder.

Manuel modda kullanıcı istediği düğüm vektörünü girebilir; uygulama uzunluk ve monotonluk doğrulamasını anlık olarak yapar.

### 2.6 B-Spline ve Bezier ile İlişki

```
Bezier  ⊂  B-Spline  ⊂  NURBS
```

| Durum | Sonuç |
|-------|-------|
| NURBS'te tüm wᵢ = 1 | Standart B-Spline eğrisi |
| B-Spline'da tek segment, n+1 = p+1 nokta | Bezier eğrisi |
| NURBS'te tüm wᵢ = 1, tek segment | Bezier eğrisi |

NURBS, Bezier ve B-Spline'ı özel durumları olarak kapsar; daha geniş bir model sınıfıdır.

### 2.7 Eğri Uzunluğu

NURBS eğrisinin analitik uzunluğunun kapalı formu yoktur. Uygulama **kümülatif kiriş toplamı** yöntemiyle sayısal yaklaşım kullanır:

```
L ≈ Σ ‖C(uᵢ) − C(uᵢ₋₁)‖     (i = 1..N,  N = 300 adım)

Her adımda: Δᵢ = √( (xᵢ−xᵢ₋₁)² + (yᵢ−yᵢ₋₁)² )
```

Örnekleme parametrenin etkin aralığında `[u_p, u_{n+1}]` yapılır.

---

## 3. Uygulama Özellikleri

| Özellik | Açıklama |
|---------|----------|
| **Fareyle Nokta Girişi** | Tuvale her tıklamada yeni kontrol noktası eklenir; eğri minimum koşul sağlandığı anda çizilir |
| **Sınırsız Nokta** | Kontrol noktası sayısında üst sınır yoktur; eğri her yeni noktayla anlık yenilenir |
| **Derece Ayarı** | Sol panelden Spinbox ile eğri derecesi (p) 1'den 20'ye kadar ayarlanabilir; order (k = p+1) otomatik hesaplanır |
| **Düğüm Vektörü – Otomatik** | Uniform clamped düğüm vektörü nokta sayısı ve dereceye göre otomatik üretilir |
| **Düğüm Vektörü – Manuel** | Boşluk/virgülle ayrılmış düğüm değerleri klavyeden girilebilir; uzunluk ve monotonluk doğrulaması anlık yapılır |
| **Ağırlık Listesi** | Tüm wᵢ değerleri blok grafik (█) ile birlikte sol panelde gösterilir |
| **Ağırlık Düzenleme – Panel** | İndeks + ağırlık değeri girilerek "Ağırlığı Güncelle" düğmesiyle herhangi bir noktanın ağırlığı değiştirilebilir |
| **Ağırlık Düzenleme – Tekerlek** | Tuval üzerinde fare tekerleği döndürüldüğünde en yakın kontrol noktasının ağırlığı ±0.1 adımlarla değişir |
| **Tüm Ağırlıkları Sıfırla** | Tek tuşla tüm ağırlıklar 1.0'a döndürülür |
| **Görsel Ağırlık Göstergesi** | Kontrol noktası dairelerinin yarıçapı ağırlıkla orantılı büyür; w≠1 ise turuncu dış halka gösterilir; w=0 ise gri çarpı işareti çizilir |
| **Anlık Eğri Çizimi** | Derece, düğüm vektörü veya ağırlık değiştiğinde eğri anlık yenilenir |
| **Kontrol Çokgeni** | Kontrol noktalarını P₀→…→Pₙ sırasıyla birleştiren kesikli çizgi |
| **Sürükleme** | Kontrol noktası fareyle sürüklenerek yeniden konumlandırılabilir |
| **Koordinat Düzenleme – Klavye** | İndeks + X/Y girişiyle herhangi bir noktanın koordinatı klavyeden güncellenebilir |
| **Koordinat Düzenleme – Mouse ile** | İndeks girilip "Mouse ile Güncelle" butonuna basıldıktan sonra tuval üzerinde tıklanan konum o noktaya atanır; ESC ile iptal edilebilir |
| **Son Noktayı Sil** | Tek tuşla son eklenen kontrol noktası ve ağırlığı kaldırılır |
| **Fare Üzeri u Parametresi** | Fare hareketi sırasında eğri üzerindeki en yakın nokta hesaplanır; u değeri ve C(u) koordinatları sol panelde gösterilir |
| **Eğri Uzunluğu** | 300 adımlı sayısal integrasyon ile piksel cinsinden yaklaşık uzunluk |
| **Sıfırlama** | Tüm noktalar, ağırlıklar, eğri ve parametreler başlangıç durumuna döner |
| **Izgara Arka Planı** | 50 piksel aralıklı yatay/dikey ızgara çizgileri |
| **Duyarlı Pencere** | Pencere yeniden boyutlandırıldığında tuval ve eğri otomatik ölçeklenir |

---

## 4. Arayüz Bileşenleri

Uygulama penceresi iki ana alandan oluşmaktadır: sol sabit genişlikli (310 px) **kontrol paneli** ve sağda tam ekrana genişleyen **çizim tuvali**.

### 4.1 Sol Kontrol Paneli

| Bileşen | İçerik |
|---------|--------|
| **Derece / Order** | Derece (p) için Spinbox; order (k = p+1) otomatik gösterim; geçersiz derece için uyarı |
| **Eğri Bilgisi** | Kontrol noktası sayısı, güncel derece/order, fare üzeri u değeri, C(u) koordinatı, eğri uzunluğu, fare koordinatı |
| **Düğüm Vektörü** | Otomatik/Manuel radyo düğmeleri; güncel vektörün metin kutusunda gösterimi; manuel modda giriş alanı + Uygula / Otomatiğe Dön düğmeleri; hata mesajı satırı |
| **Ağırlıklar (wᵢ)** | Tüm ağırlıkların blok grafik eşliğinde listesi |
| **Ağırlık Düzenleme** | İndeks + ağırlık değeri giriş alanları + "Ağırlığı Güncelle" düğmesi; w etkisi hakkında kısa açıklama; "Tüm Ağırlıkları 1.0 Yap" düğmesi; hata mesajı satırı |
| **Kontrol Noktaları** | Tüm noktaların `Pᵢ(x,y) w=…` formatında koordinat ve ağırlık listesi |
| **Son Noktayı Sil** | En son eklenen noktayı ve ağırlığını kaldıran düğme |
| **Koordinat Düzenleme** | İndeks + X/Y giriş alanları + "Koordinatı Güncelle" ve "Mouse ile Güncelle" yan yana düğmeler; hata mesajı satırı |
| **Sıfırla** | Panelin en altında; tüm durumu sıfırlar |

Sol panel dikey kaydırma çubuğuna sahiptir ve fare tekerleğiyle kaydırılabilir.

### 4.2 Ana Çizim Alanı (Tuval)

Koyu lacivert arka plan üzerine şunlar çizilir:

- **Izgara:** 50 px aralıklı gri yatay/dikey çizgiler
- **Kontrol noktaları:** Renkli (12 renklik döngüsel palet) dolgulu daireler; yarıçap ağırlıkla orantılı büyür; yanlarında `Pᵢ(x,y) w=…` etiketi
- **Ağırlık halkası:** w ≠ 1 olduğunda nokta etrafında turuncu dış halka; halka kalınlığı ağırlığa göre değişir
- **Sıfır ağırlık göstergesi:** w = 0 ise daire yerine gri çarpı işareti çizilir
- **Kontrol çokgeni:** P₀→P₁→…→Pₙ arası kesikli çizgiler
- **NURBS eğrisi:** 400 kırık çizgi parçasından oluşan turuncu eğri (B-Spline'dan renk farkı ile ayırt edilir)
- **Sürükleme halkası:** Sürüklenen nokta sarı dış halkayla işaretlenir
- **Mouse düzenleme halkası:** Mouse ile güncelleme modunda hedef nokta çift sarı/turuncu halkayla vurgulanır
- **Fare üzeri işaretçi:** En yakın eğri noktasında beyaz dolgulu küçük daire + `u=…` etiketi

### 4.3 Durum Çubuğu

| Durum | Mesaj |
|-------|-------|
| Hiç nokta yok | Tuvale tıklayarak kontrol noktası ekleyin. |
| Yetersiz nokta | n nokta var. Derece p için en az p+1 nokta gerekli. |
| Eğri hazır | n nokta \| Derece: p \| Sürükle: taşı \| Tekerlek: ağırlık değiştir \| Tıkla: yeni nokta |
| Mouse düzenleme modu | Mouse düzenleme modu: Pn için yeni konumu tıklayın \| ESC veya İptal ile çıkın |

---

## 5. Kullanım Adımları

### 5.1 Uygulamayı Başlatma

```bash
python nurbs_editor.py
```

Uygulama açıldığında tuval boştur, derece 3 (kübik) olarak ayarlıdır, düğüm vektörü otomatik moddadır ve tüm yeni noktalar varsayılan ağırlık `w = 1.0` ile eklenir.

### 5.2 Kontrol Noktası Ekleme

Tuvale tıklayın; her tıklamada yeni bir kontrol noktası eklenir ve `w = 1.0` ağırlığıyla listeye girer.

- **Eğri ne zaman görünür?** Nokta sayısı `derece + 1`'e ulaştığında eğri ilk kez çizilir. Derece 3 için 4. nokta eklendiğinde eğri belirir.
- **Eklemeye devam:** Eğri çizildikten sonra nokta eklemeye devam edilebilir; her yeni nokta eğriyi anlık günceller.

### 5.3 Derece ve Order Ayarlama

Sol paneldeki **Derece (p)** Spinbox'ından değeri artırın/azaltın ya da doğrudan yazıp Enter'a basın.

- Minimum: 1 (doğrusal), Maksimum: n − 1
- Order (k = p + 1) otomatik güncellenir.
- Otomatik düğüm modunda vektör yeniden hesaplanır.

### 5.4 Düğüm Vektörü Ayarlama

**Otomatik Mod (varsayılan):** Nokta sayısı veya derece değiştiğinde otomatik yeniden üretilir.

**Manuel Mod:**
1. "Manuel giriş" radyo düğmesini seçin; mevcut vektör giriş kutusuna kopyalanır.
2. Değerleri boşluk veya virgülle ayrılmış olarak yazın. Örnek:
   ```
   0 0 0 0 0.25 0.5 0.75 1 1 1 1
   ```
3. **Uygula** düğmesine tıklayın veya Enter'a basın.
4. Uzunluk (`n + p + 2`) ve monotonluk hataları kırmızı mesajla gösterilir.
5. **Otomatiğe Dön** ile otomatik moda geri dönülebilir.

### 5.5 Ağırlık Düzenleme

Ağırlıklar üç yolla değiştirilebilir:

**Yöntem A – Panel Girişi:**
1. "Ağırlık Düzenle" bölümünde **İndeks** alanına noktanın numarasını yazın.
2. **Ağırlık (w)** alanına yeni değeri yazın (≥ 0).
3. **Ağırlığı Güncelle** düğmesine tıklayın veya Enter'a basın.
4. Eğri anlık güncellenir.

**Yöntem B – Fare Tekerleği:**
Tuval üzerinde fareyi bir kontrol noktasına yaklaştırın ve tekerleği döndürün:
- Tekerlek yukarı → ağırlık +0.1
- Tekerlek aşağı → ağırlık −0.1 (minimum 0.0)

Panel üzerindeki İndeks ve Ağırlık alanları da senkronize olarak güncellenir.

**Yöntem C – Tüm Ağırlıkları Sıfırla:**
"Tüm Ağırlıkları 1.0 Yap" düğmesiyle tüm ağırlıklar standart değere döndürülür.

**Ağırlık davranışını gözlemlemek için:**
Bir noktanın ağırlığını 1'den büyük bir değere (örn. 5.0) çıkarın → eğri o noktaya doğru belirgin biçimde çekilir. Ağırlığı 0'a indirin → o nokta eğri üzerinde hiçbir etkisi kalmaz.

### 5.6 Eğriyi İnceleme

Fare tuvalde hareket ettiğinde:
- Sol panelin **Fare** alanı anlık koordinatı gösterir.
- **u Değeri** ve **C(u) Noktası** güncellenir; tuval üzerinde beyaz daire en yakın eğri noktasına konumlanır.
- **Eğri Uzunluğu** (L) piksel cinsinden görüntülenir.
- **Ağırlıklar** listesi ve **Kontrol Noktaları** listesi anlık koordinat ve ağırlık bilgisi gösterir.

### 5.7 Noktaları Düzenleme

**Yöntem A – Sürükleme:**
Varolan bir kontrol noktasının üzerine tıklayın (12 piksel toleranslı) ve fareyi basılı tutarak sürükleyin. Eğri ve düğüm vektörü gerçek zamanlı güncellenir.

**Yöntem B – Koordinat Girişi:**
1. **İndeks** alanına hedef noktanın numarasını yazın (0 tabanlı).
2. **X** ve **Y** alanlarına yeni koordinatları yazın.
3. **Koordinatı Güncelle** düğmesine tıklayın.
4. Geçersiz indeks veya format için kırmızı hata mesajı gösterilir.

**Yöntem C – Mouse ile Yerleştirme:**
1. **İndeks** alanına noktanın numarasını yazın.
2. **Mouse ile Güncelle** düğmesine tıklayın. Düğme sarıya döner ve "İptal (ESC)" yazısına dönüşür; fare imleci çift artı biçimine geçer; hedef nokta çift sarı/turuncu halkayla vurgulanır.
3. Tuvalde istediğiniz konuma tıklayın — nokta oraya taşınır, mod otomatik kapanır.
4. Vazgeçmek için **ESC** tuşuna basın veya düğmeye tekrar tıklayın.

**Son Noktayı Silme:**
"Son Noktayı Sil" düğmesi en son eklenen kontrol noktasını ve ağırlığını kaldırır.

### 5.8 Sıfırlama

Sol panelin altındaki **Sıfırla** düğmesine tıklayın. Tüm kontrol noktaları, ağırlıklar, eğri, derece (3'e döner) ve düğüm vektörü temizlenerek uygulama başlangıç durumuna döner.

---

## 6. Teknik Detaylar

### 6.1 Gereksinimler

| Bileşen | Versiyon | Açıklama |
|---------|----------|----------|
| Python | 3.8 veya üzeri | Ana çalışma zamanı |
| tkinter | Python ile birlikte gelir | Grafik arayüz kütüphanesi |
| math | Standart kütüphane | Hipotenüs ve karekök hesapları |
| İşletim Sistemi | Windows / macOS / Linux | tkinter'ın desteklediği her platform |

**Üçüncü parti paket kullanılmamıştır.**

### 6.2 Çalıştırma

```bash
python nurbs_editor.py
```

**Yürütülebilir (.exe) Oluşturma:**

```bash
pip install pyinstaller
pyinstaller --onefile --windowed nurbs_editor.py
```

### 6.3 Kod Yapısı

Tüm uygulama tek dosyadan (`nurbs_editor.py`) oluşmaktadır.

| Bölüm | Sorumluluk |
|-------|------------|
| Sabitler ve renk paleti | `STEPS`, `BASE_RADIUS`, `WEIGHT_SCALE`, `DEFAULT_W`, renk tanımları |
| `cox_de_boor(t, i, p, knots)` | Özyinelemeli B-Spline taban fonksiyonu |
| `nurbs_point(t, ctrl_pts, weights, knots, degree)` | Rasyonel NURBS noktası hesabı |
| `make_uniform_knots(n_pts, degree)` | Uniform clamped düğüm vektörü üretimi |
| `parse_float_list(text)` | Metin ayrıştırma – manuel düğüm/ağırlık girişi |
| `validate_knots(knots, n_pts, degree)` | Düğüm vektörü doğrulama |
| `NURBSEditor.__init__` | Uygulama durumu, ağırlık listesi ve font nesnelerinin başlatılması |
| `_build_ui` ve alt metotlar | Sol panel, tuval, tüm widget'ların oluşturulması |
| `_on_click` | Click-edit modu kontrolü → yeni nokta ekleme veya sürükleme başlatma |
| `_on_drag` | Kontrol noktası sürükleme |
| `_on_release` | Sürükleme sona erme |
| `_on_motion` | Fare hareketi: koordinat + hover hesabı |
| `_on_canvas_scroll` | Fare tekerleği ile en yakın noktanın ağırlığını değiştirme |
| `_on_degree_change` | Derece Spinbox değişikliği |
| `_auto_knots` | Otomatik düğüm vektörü yeniden hesaplama |
| `_on_knot_mode_change` | Otomatik/manuel mod geçişi |
| `_apply_manual_knots` | Manuel düğüm vektörü doğrulama ve uygulama |
| `_apply_weight_edit` | Panel üzerinden ağırlık güncelleme |
| `_reset_weights` | Tüm ağırlıkları 1.0'a döndürme |
| `_activate_click_edit` | Mouse ile güncelleme modunu başlatma; indeks doğrulama, imleç ve buton değişikliği |
| `_cancel_click_edit` | Mouse ile güncelleme modundan çıkma (ESC veya buton) |
| `_delete_last` | Son kontrol noktası ve ağırlığını silme |
| `_apply_coord_edit` | Koordinat girişiyle nokta güncelleme |
| `_reset` | Tam sıfırlama |
| `_refresh_all` | Sol panel ve durum çubuğu güncellemesi |
| `_can_draw` | Eğri çizim koşulunun kontrolü |
| `_eval(t)` | Tek parametre değerinde rasyonel NURBS noktası |
| `_closest_t` | Fareye en yakın u parametresi (300 örnek) |
| `_arc_length` | Eğri uzunluğu sayısal integrasyonu (300 adım) |
| Çizim metotları | Izgara, eğri, noktalar, ağırlık halkaları, kontrol çokgeni, hover |
| `main` | Giriş noktası: Tk penceresi ve olay döngüsü |

### 6.4 Temel Algoritmalar

#### NURBS Noktası Hesabı (`nurbs_point`)

Her u değeri için Cox–de Boor taban fonksiyonları hesaplanır, ağırlıklarla çarpılarak pay ve payda ayrı ayrı toplanır:

```python
def nurbs_point(t, ctrl_pts, weights, knots, degree):
    n = len(ctrl_pts) - 1
    wx, wy, wsum = 0.0, 0.0, 0.0
    for i in range(n + 1):
        b  = cox_de_boor(t, i, degree, knots)  # Nᵢ,ₚ(t)
        bw = b * weights[i]                     # Nᵢ,ₚ · wᵢ
        wx   += bw * ctrl_pts[i][0]             # pay – x
        wy   += bw * ctrl_pts[i][1]             # pay – y
        wsum += bw                              # payda
    if wsum == 0.0:
        return ctrl_pts[0]                      # dejenere koruma
    return (wx / wsum, wy / wsum)               # C(t) = pay / payda
```

#### Fare Tekerleği ile Ağırlık Değiştirme (`_on_canvas_scroll`)

Tuval üzerinde fare tekerleği döndürüldüğünde en yakın kontrol noktası bulunarak ağırlığı anlık güncellenir:

```python
def _on_canvas_scroll(self, event):
    idx   = min(range(len(self.ctrl_pts)),
                key=lambda i: math.hypot(self.ctrl_pts[i][0] - event.x,
                                         self.ctrl_pts[i][1] - event.y))
    delta = 0.1 if event.delta > 0 else -0.1
    self.weights[idx] = max(0.0, round(self.weights[idx] + delta, 4))
    self._refresh_all()
    self._redraw()
```

#### Mouse ile Yerleştirme (`_activate_click_edit` / `_on_click`)

```python
# Mod aktivasyonu
def _activate_click_edit(self):
    idx = int(self.edit_idx_var.get())   # indeks doğrulama
    self.click_edit_idx = idx
    self.canvas.config(cursor='tcross')  # imleç değişimi
    # buton → "İptal (ESC)" olarak güncellenir

# Tıklama ile yerleştirme
def _on_click(self, event):
    if self.click_edit_idx is not None:
        self.ctrl_pts[self.click_edit_idx] = (event.x, event.y)
        self._cancel_click_edit()        # mod kapatılır
        ...
        return
    # normal tıklama → yeni nokta ekleme
```

#### Yeniden Çizim Stratejisi

Yapısal değişiklikler (nokta ekleme/sürükleme, derece/düğüm/ağırlık değişikliği) tüm tuvali silen ve sıfırdan çizen `_redraw()` metodunu tetikler. Yalnızca fare hover işaretçisi `canvas.delete('hover')` ile seçici olarak silinip yeniden çizilir; bu sayede her fare hareketi için tam yeniden çizim yapılmaz.

---

## 7. Sonuç

Bu uygulama, NURBS eğrisinin matematiksel temelini görsel ve etkileşimli biçimde deneyimlemeyi sağlamaktadır. Kullanıcı kontrol noktalarını fareyle tanımlar; derece, düğüm vektörü ve ağırlıkları anlık olarak değiştirir. Uygulama, Cox–de Boor özyinelemesi üzerine inşa edilmiş rasyonel formülle eğriyi hesaplar; ağırlık görselleştirmesi, hover u parametresi ve eğri uzunluğu tahmini ile kapsamlı bir inceleme ortamı sunar.

**Uygulamanın sunduğu temel öğrenme çıktıları:**

- Ağırlık artışının eğriyi kontrol noktasına nasıl çektiğinin, azalışının nasıl uzaklaştırdığının gerçek zamanlı gözlemlenmesi
- `w = 0` durumunda noktanın eğri üzerindeki etkisinin tamamen ortadan kalkmasının görülmesi
- Tüm ağırlıklar eşit olduğunda NURBS'ün standart B-Spline'a dönüştüğünün keşfedilmesi
- Rasyonel formülün neden `Σ Nᵢwᵢ = 1` yerine `Σ (Nᵢwᵢ) / Σ (Nⱼwⱼ)` şeklinde tanımlandığının anlaşılması
- NURBS'ün Bezier ve B-Spline'ı özel durum olarak kapsayan daha geniş model ailesi olduğunun kavranması
- Düğüm vektörü ve ağırlık parametrelerinin birlikte nasıl çalıştığının pratik olarak deneyimlenmesi

---

*Bilgisayarlı Modelleme ve Yapay Zeka Uygulamaları, Ödev 3*
