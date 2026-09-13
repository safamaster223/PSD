# Analisis Statistik Deskriptif

## Latar Belakang

Setelah melakukan pengumpulan data (*Data Understanding*) dan interpretasi awal terhadap konsentrasi polutan di Kabupaten Sidoarjo menggunakan data satelit Sentinel-5P TROPOMI, langkah selanjutnya adalah melakukan analisis statistik deskriptif. Analisis ini bertujuan untuk memahami karakteristik, sebaran, dan anomali dari data *time series* polutan (NO₂, CO, HCHO, SO₂, O₃, dan CH₄) yang telah kita kumpulkan.

Dalam proses ini, kita menggunakan platform **KNIME Analytics** yang terhubung dengan basis data **PostgreSQL (Aiven)**. Data *time series* yang sebelumnya telah digabungkan (`sidoarjo_pollutants.csv`) diunggah ke dalam basis data, kemudian ditarik kembali ke KNIME untuk dihitung nilai statistiknya menggunakan *node* **Statistics**.

## Fitur Statistik dan Cara Menghitungnya

*Node* Statistics pada KNIME menghasilkan berbagai metrik deskriptif. Berikut adalah penjelasan, rumus matematis, dan contoh perhitungan konseptual untuk setiap fitur yang dihasilkan.

### 1. Minimum (Min) & Maximum (Max)

**Penjelasan:** 
Nilai terkecil (Minimum) dan terbesar (Maximum) dalam suatu himpunan data. Metrik ini sangat berguna untuk mengetahui rentang (*range*) ekstrem dari konsentrasi polutan, misalnya untuk mengidentifikasi hari dengan tingkat polusi terendah dan tertinggi dalam satu tahun.

**Rumus:**
- $Min = \min(x_1, x_2, ..., x_n)$
- $Max = \max(x_1, x_2, ..., x_n)$

**Contoh Perhitungan:**
Misalkan kita memiliki 5 sampel data konsentrasi NO₂ harian (dalam mol/m²): $X = [0.0001, 0.0003, 0.0002, 0.0005, 0.0004]$
- $Min = 0.0001$
- $Max = 0.0005$

### 2. Mean (Rata-rata)

**Penjelasan:** 
Rata-rata aritmatika dari seluruh nilai dalam himpunan data. Mean menunjukkan titik pusat gravitasi dari distribusi data polutan selama periode pengamatan.

**Rumus:**
$$ \mu = \frac{\sum_{i=1}^{n} x_i}{n} $$
*(Dimana $\sum x_i$ adalah total jumlah data, dan $n$ adalah banyaknya data)*

**Contoh Perhitungan:**
Menggunakan data $X$ di atas:
$$ \mu = \frac{0.0001 + 0.0003 + 0.0002 + 0.0005 + 0.0004}{5} = \frac{0.0015}{5} = 0.0003 $$

### 3. Median (Nilai Tengah)

**Penjelasan:** 
Nilai tengah dari himpunan data yang telah diurutkan dari terkecil hingga terbesar. Median lebih kebal terhadap nilai ekstrem (*outlier*) dibandingkan Mean. Jika ada satu hari dengan polusi sangat tinggi akibat kebakaran, nilai Mean akan melonjak, tetapi Median akan tetap stabil.

**Rumus:**
- Jika $n$ ganjil: Nilai pada posisi ke-$\frac{n+1}{2}$
- Jika $n$ genap: Rata-rata dari dua nilai di tengah.

**Contoh Perhitungan:**
Data terurut: $0.0001, 0.0002, 0.0003, 0.0004, 0.0005$ ($n=5$, ganjil)
Posisi median = $\frac{5+1}{2} = 3$.
Nilai pada posisi ke-3 adalah $0.0003$.

### 4. Variance (Varians)

**Penjelasan:** 
Varians mengukur seberapa jauh data tersebar dari nilai rata-ratanya. KNIME menggunakan rumus Varians Sampel (*Sample Variance*). Semakin besar varians, semakin fluktuatif tingkat polusi di Sidoarjo.

**Rumus:**
$$ s^2 = \frac{\sum_{i=1}^{n} (x_i - \mu)^2}{n - 1} $$

**Contoh Perhitungan:**
$$ s^2 = \frac{(0.0001-0.0003)^2 + (0.0003-0.0003)^2 + ... + (0.0004-0.0003)^2}{5 - 1} $$
$$ s^2 = \frac{0.00000004 + 0 + 0.00000001 + 0.00000004 + 0.00000001}{4} = 0.000000025 $$

### 5. Standard Deviation (Standar Deviasi)

**Penjelasan:** 
Akar kuadrat dari varians. Standar deviasi menunjukkan rata-rata penyimpangan setiap titik data dari nilai Mean. Metrik ini lebih mudah diinterpretasikan karena memiliki satuan yang sama dengan data aslinya (mol/m²).

**Rumus:**
$$ s = \sqrt{s^2} $$

**Contoh Perhitungan:**
$$ s = \sqrt{0.000000025} = 0.000158 $$

### 6. Skewness (Kemencengan)

**Penjelasan:** 
Skewness mengukur tingkat ketidaksimetrisan (kemencengan) distribusi data terhadap rata-ratanya. 
- **Nilai = 0:** Distribusi simetris sempurna (Normal).
- **Nilai > 0:** Menceng ke kanan (*Right-skewed*). Artinya, sebagian besar hari memiliki polusi rendah, tetapi ada beberapa hari dengan polusi sangat tinggi (ekor panjang di kanan).
- **Nilai < 0:** Menceng ke kiri (*Left-skewed*).

**Rumus (Sample Skewness):**
$$ Skewness = \frac{n}{(n-1)(n-2)} \sum_{i=1}^{n} \left( \frac{x_i - \mu}{s} \right)^3 $$

### 7. Kurtosis (Keruncingan)

**Penjelasan:** 
Kurtosis mengukur 'keruncingan' distribusi data, atau seberapa banyak data yang berada di bagian ekor (*outliers*) dibandingkan dengan distribusi normal. KNIME menggunakan *Excess Kurtosis*.
- **Kurtosis = 0:** Distribusi normal (*Mesokurtik*).
- **Kurtosis > 0:** Puncak tajam, banyak outlier (*Leptokurtik*). Menunjukkan sering terjadi lonjakan polusi ekstrem yang tiba-tiba.
- **Kurtosis < 0:** Puncak datar, sedikit outlier (*Platikurtik*). Menunjukkan tingkat polusi yang relatif stabil sepanjang tahun.

**Rumus (Sample Excess Kurtosis):**
$$ Kurtosis = \left\{ \frac{n(n+1)}{(n-1)(n-2)(n-3)} \sum_{i=1}^{n} \left( \frac{x_i - \mu}{s} \right)^4 \right\} - \frac{3(n-1)^2}{(n-2)(n-3)} $$

---
*Catatan: Hasil perhitungan statistik aktual dari dataset `sidoarjo_pollutants.csv` dapat dilihat langsung melalui output node Statistics pada platform KNIME.*