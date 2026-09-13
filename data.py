# -*- coding: utf-8 -*-
"""Ekstraksi NO2 Sentinel-5P Kecamatan Wonoayu, Sidoarjo."""

import json
import os
import sys
import matplotlib.pyplot as plt
import openeo
import pandas as pd
import shapely.geometry

# 1. Konfigurasi File GeoJSON & Parameter
# Menggunakan path absolut agar tidak error saat di-run dari direktori mana pun
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(BASE_DIR, "data", "downloads", "sidoarjo.geojson")
POLLUTANT_BAND = "NO2"
TIME_EXTENT = ["2025-08-24", "2026-08-24"]
OUTPUT_CSV = os.path.join(BASE_DIR, "data", "downloads", "sidoarjo_pollutants_data", "wonoayu_NO2.csv")

# Cek file GeoJSON (upload otomatis jika pakai Google Colab)
if not os.path.exists(GEOJSON_PATH):
    if "google.colab" in sys.modules:
        from google.colab import files

        print(
            f"File '{GEOJSON_PATH}' tidak ditemukan. Silakan upload file GeoJSON Wonoayu:"
        )
        uploaded = files.upload()
        uploaded_name = list(uploaded.keys())[0]
        if uploaded_name != GEOJSON_PATH:
            os.rename(uploaded_name, GEOJSON_PATH)
    else:
        raise FileNotFoundError(
            f"'{GEOJSON_PATH}' tidak ditemukan di direktori kerja saat ini."
        )

print(f"Menggunakan file AOI: {GEOJSON_PATH}")

# 2. Parsing Geometri Wonoayu
with open(GEOJSON_PATH, "r") as f:
    geojson_data = json.load(f)

feature = geojson_data["features"][0]
geometry = feature["geometry"]
shp = shapely.geometry.shape(geometry)

west, south, east, north = shp.bounds
spatial_extent = {
    "west": west,
    "south": south,
    "east": east,
    "north": north,
}

print(f"Geometry type : {shp.geom_type}")
print(f"Bounding Box  : {spatial_extent}")
print(
    f"Perkiraan Area: {(east-west)*111:.2f} km x {(north-south)*111:.2f} km"
)

# 3. Autentikasi OpenEO
connection = openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc()

# 4. Bangun Data Cube untuk NO2
print(
    f"\nMenyiapkan pemrosesan data {POLLUTANT_BAND} Sentinel-5P L2 Wonoayu..."
)
cube = connection.load_collection(
    "SENTINEL_5P_L2",
    temporal_extent=TIME_EXTENT,
    spatial_extent=spatial_extent,
    bands=[POLLUTANT_BAND],
)

# Rata-rata harian (temporal) dan rata-rata area poligon Wonoayu (spatial)
cube = cube.aggregate_temporal_period(reducer="mean", period="day")
cube = cube.aggregate_spatial(reducer="mean", geometries=geometry)

# 5. Jalankan Batch Job & Simpan ke CSV Tunggal
print(f"Menjalankan batch job OpenEO -> Output: {OUTPUT_CSV} ...")
job = cube.execute_batch(
    title=f"Polutan Wonoayu - {POLLUTANT_BAND}",
    outputfile=OUTPUT_CSV,
    out_format="CSV",
)
print(f"Sukses! File berhasil disimpan ke: {OUTPUT_CSV}")

# 6. Membaca & Merapikan Data Hasil Ekstraksi
df = pd.read_csv(OUTPUT_CSV)

# Deteksi kolom waktu/tanggal
time_cols = [
    c for c in df.columns if c.lower() in ("date", "time", "t", "datetime")
]
time_col = time_cols[0] if time_cols else df.columns[0]

# Deteksi kolom konsentrasi NO2
exclude_cols = {time_col, "feature_index", "geometry"}
if POLLUTANT_BAND in df.columns:
    value_col = POLLUTANT_BAND
else:
    numeric_candidates = [
        c
        for c in df.columns
        if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])
    ]
    value_col = numeric_candidates[0]

df["date"] = pd.to_datetime(df[time_col])
df = df.sort_values("date").reset_index(drop=True)
df["NO2_rolling30"] = df[value_col].rolling(window=30, min_periods=1).mean()

# Timpa / perbarui file CSV agar kolom tanggal dan nilai tersusun rapi
df[["date", value_col, "NO2_rolling30"]].rename(
    columns={value_col: "NO2_mean"}
).to_csv(OUTPUT_CSV, index=False)
print(f"File CSV {OUTPUT_CSV} telah dirapikan (kolom: date, NO2_mean, NO2_rolling30).")

# 7. Visualisasi Tren NO2
plt.figure(figsize=(12, 5), dpi=100)
plt.plot(
    df["date"],
    df["NO2_rolling30"],
    color="crimson",
    label="NO₂ Rolling 30-Hari (mol/m²)",
)
plt.title("Konsentrasi NO₂ di Kabupaten Sidoarjo (2025 - 2026)")
plt.xlabel("Waktu")
plt.ylabel("NO₂ (mol/m²)")
plt.grid(True, alpha=0.3)
plt.legend(loc="upper right")
plt.tight_layout()
plt.show()

# 8. Otomatis Download jika di Google Colab
if "google.colab" in sys.modules:
    from google.colab import files

    files.download(OUTPUT_CSV)