import pandas as pd
import numpy as np
import inspect
import tsfel.feature_extraction.features as tsfel_features
import os

# ---------- 1. Muat dan bersihkan data ----------
# Menggunakan path absolut agar tidak error saat di-run dari direktori mana pun
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "downloads", "sidoarjo_pollutants_data")

# Daftar file input dan output yang akan diekstraksi
TASKS = [
    {
        "input_csv": os.path.join(DATA_DIR, "wonoayu_SO2_imputed.csv"),
        "output_csv": os.path.join(DATA_DIR, "SO2_Wonoayu_TSFEL.csv"),
        "pollutant_col": "SO2"
    },
    {
        "input_csv": os.path.join(DATA_DIR, "wonoayu_CO_imputed.csv"),
        "output_csv": os.path.join(DATA_DIR, "CO_Wonoayu_TSFEL.csv"),
        "pollutant_col": "CO"
    }
]

# ---------- 2. Daftar PERSIS fitur yang diminta ----------
FEATURE_LIST = """abs_energy auc autocorr average_power calc_centroid calc_max calc_mean
calc_median calc_min calc_std calc_var dfa distance ecdf ecdf_percentile ecdf_percentile_count
ecdf_slope entropy fundamental_frequency higuchi_fractal_dimension hist_mode human_range_energy
hurst_exponent interq_range kurtosis lempel_ziv lpcc max_frequency max_power_spectrum
maximum_fractal_length mean_abs_deviation mean_abs_diff mean_diff median_abs_deviation
median_abs_diff median_diff median_frequency mfcc mse negative_turning neighbourhood_peaks
petrosian_fractal_dimension pk_pk_distance positive_turning power_bandwidth rms skewness slope
spectral_centroid spectral_decrease spectral_distance spectral_entropy spectral_kurtosis
spectral_positive_turning spectral_roll_off spectral_roll_on spectral_skewness spectral_slope
spectral_spread spectral_variation spectrogram_mean_coeff sum_abs_diff wavelet_abs_mean
wavelet_energy wavelet_entropy wavelet_std wavelet_var zero_cross""".split()


def to_scalar(result):
    if isinstance(result, dict) and "values" in result:
        result = result["values"]
    if isinstance(result, (list, tuple, np.ndarray)):
        arr = np.asarray(result, dtype=float)
        return float(np.nanmean(arr))
    return float(result)


def extract_one(fn_name, signal, fs):
    fn = getattr(tsfel_features, fn_name)
    params = inspect.signature(fn).parameters
    if "fs" in params:
        result = fn(signal, fs)
    else:
        result = fn(signal)
    return to_scalar(result)


# ---------- 3. Ekstraksi Fitur per File ----------
print("Jumlah fitur yang diminta:", len(FEATURE_LIST))

for task in TASKS:
    INPUT_CSV = task["input_csv"]
    OUTPUT_CSV = task["output_csv"]

    if not os.path.exists(INPUT_CSV):
        print(f"Warning: File input tidak ditemukan: {INPUT_CSV}")
        continue

    print(f"\n--- Memproses file: {os.path.basename(INPUT_CSV)} ---")
    df = pd.read_csv(INPUT_CSV)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)

    target_pollutant = task["pollutant_col"]
    if target_pollutant not in df.columns:
        possible_cols = [c for c in df.columns if c != 'date']
        if possible_cols:
            target_pollutant = possible_cols[0]
        else:
            raise KeyError(f"Kolom target {target_pollutant} tidak ditemukan di {INPUT_CSV}")

    df[target_pollutant] = pd.to_numeric(df[target_pollutant], errors='coerce')

    n_missing_before = df[target_pollutant].isna().sum()
    print(f"Jumlah nilai non-numerik/kosong yang dikonversi jadi NaN: {n_missing_before}")

    Q1 = df[target_pollutant].quantile(0.25)
    Q3 = df[target_pollutant].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df.loc[(df[target_pollutant] < lower_bound) | (df[target_pollutant] > upper_bound), target_pollutant] = np.nan

    df_clean = df.set_index('date').interpolate(method='time').ffill().bfill()

    fs = 1
    signal_1d = df_clean[target_pollutant].astype(float).values

    row = {}
    for fn_name in FEATURE_LIST:
        row[fn_name] = extract_one(fn_name, signal_1d, fs)

    extracted_features_final = pd.DataFrame([row])

    print(f"Berhasil! Jumlah fitur yang dihasilkan untuk {target_pollutant}: {extracted_features_final.shape[1]}")
    extracted_features_final.to_csv(OUTPUT_CSV, index=False)
    print(f"File hasil ekstraksi disimpan di: {OUTPUT_CSV}")
