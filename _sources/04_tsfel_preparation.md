# Persiapan Tugas: Time Series Feature Extraction
**Panduan Pre-Processing dan Ekstraksi Fitur TSFEL**

---

## Latar Belakang & Tujuan
Dokumen ini merangkum tahapan pra-pemrosesan (*pre-processing*) dan ekstraksi fitur tingkat lanjut untuk data *time series* polutan. Tahapan ini sangat krusial sebelum data dimasukkan ke dalam model *Machine Learning*. Data mentah dari satelit sering kali mengandung kekosongan (*missing values*) akibat tutupan awan dan lonjakan ekstrem (*outliers*) akibat anomali lokal. 

Tujuan utama dari proses ini adalah:
1. Mendeteksi dan memperbaiki *Missing Value* menggunakan metode **Interpolasi Linear**.
2. Mendeteksi dan memperbaiki *Outlier* untuk memastikan kualitas data (*Data Quality*).
3. Mengekstrak **65 fitur** *time series* menggunakan *library* **TSFEL** (*Time Series Feature Extraction Library*).

---

## Tahap 1: Penanganan Missing Value (Imputasi)
Data *time series* memiliki sifat temporal (berurutan berdasarkan waktu). Oleh karena itu, kita **tidak boleh sembarangan menghapus baris yang kosong (Drop NA)**, karena akan merusak jarak waktu antar observasi.

**Metode: Interpolasi Linear (Linear Interpolation)**
Interpolasi linear adalah metode estimasi nilai yang hilang dengan menarik garis lurus antara titik data sebelum dan sesudah nilai yang kosong. 

**Cara Kerja:**
Jika konsentrasi NO₂ pada hari ke-1 adalah 10, hari ke-2 kosong (NaN), dan hari ke-3 adalah 20, maka interpolasi linear akan mengisi hari ke-2 dengan nilai 15.
Rumus matematisnya: $y = y_1 + \frac{(x - x_1)(y_2 - y_1)}{(x_2 - x_1)}$

**Implementasi di Python (Pandas):**
```python
# Mengisi missing value dengan interpolasi linear
df['NO2'] = df['NO2'].interpolate(method='linear')
```

---

## Tahap 2: Deteksi dan Perbaikan Outlier
*Outlier* adalah titik data yang nilainya menyimpang sangat jauh dari observasi lainnya. Mendeteksi *outlier* penting untuk mengetahui apakah data kita 'bagus' (stabil) atau penuh dengan anomali (*noise*).

**Metode Deteksi: Interquartile Range (IQR)**
IQR adalah rentang antara kuartil pertama (Q1, persentil ke-25) dan kuartil ketiga (Q3, persentil ke-75).
*   $IQR = Q3 - Q1$
*   Batas Bawah = $Q1 - (1.5 \times IQR)$
*   Batas Atas = $Q3 + (1.5 \times IQR)$

Data yang berada di luar Batas Bawah dan Batas Atas didefinisikan sebagai *Outlier*.

**Metode Perbaikan: Capping / Winsorization**
Sama seperti *missing value*, kita tidak boleh menghapus baris *outlier*. Sebagai gantinya, kita melakukan '*Capping*'. Jika ada nilai yang melebihi Batas Atas, nilai tersebut akan diubah (ditekan) menjadi sama dengan nilai Batas Atas. Hal ini mempertahankan urutan waktu namun menghilangkan efek ekstrem dari *outlier* tersebut.

**Implementasi di Python:**
```python
Q1 = df['NO2'].quantile(0.25)
Q3 = df['NO2'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Memperbaiki outlier dengan Capping
df['NO2'] = np.where(df['NO2'] > upper_bound, upper_bound, 
            np.where(df['NO2'] < lower_bound, lower_bound, df['NO2']))
```

---

## Tahap 3: Ekstraksi Fitur menggunakan TSFEL
Setelah data bersih dari *missing value* dan *outlier*, data siap diekstraksi. TSFEL (*Time Series Feature Extraction Library*) adalah pustaka Python yang secara otomatis mengekstrak puluhan fitur dari sinyal *time series*.

Berdasarkan instruksi, kita akan mengekstrak **65 fitur** yang terbagi dalam tiga domain utama:
1. **Domain Statistik (Statistical):** Mengekstrak metrik seperti Mean, Variance, Skewness, Kurtosis, Minimum, Maximum, dll.
2. **Domain Temporal (Temporal):** Mengekstrak fitur yang bergantung pada urutan waktu, seperti Autocorrelation, Mean Absolute Difference, Zero Crossing Rate, dll.
3. **Domain Spektral (Spectral):** Mengekstrak fitur berdasarkan frekuensi sinyal (menggunakan Fast Fourier Transform / FFT), seperti Spectral Entropy, FFT Mean, Wavelet Variance, dll.

**Implementasi di Python (TSFEL):**
```python
import tsfel

# Menggunakan konfigurasi bawaan TSFEL untuk mengekstrak semua fitur
cfg = tsfel.get_features_by_domain()

# Melakukan ekstraksi fitur pada kolom yang sudah bersih
X_features = tsfel.time_series_features_extractor(cfg, df['NO2'])
```

Hasil dari proses ini adalah sebuah dataset baru di mana satu deret waktu (misalnya 1 tahun data NO₂) diubah menjadi 1 baris data yang memiliki 65 kolom fitur. Fitur-fitur inilah yang nantinya akan menjadi *input* (X) untuk algoritma *Machine Learning*.