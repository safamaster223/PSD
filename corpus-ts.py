pip install openeo
import openeo
import json
import pandas as pd
import numpy as np
import os
import sys

import folium
import json
import shapely.geometry
import os

# Baca GeoJSON batas wilayah Kecamatan Wonoayu
_geojson_path = 'wonoayu.geojson'
if not os.path.exists(_geojson_path):
    _geojson_path = '../wonoayu.geojson'

with open(_geojson_path, 'r') as _f:
    _geojson_data = json.load(_f)

# Hitung centroid wilayah untuk memusatkan peta
_shp = shapely.geometry.shape(_geojson_data['features'][0]['geometry'])
_centroid = _shp.centroid

# Buat peta interaktif Folium
_m = folium.Map(
    location=[_centroid.y, _centroid.x],
    zoom_start=12
)

# Tambahkan poligon batas Kecamatan Wonoayu
folium.GeoJson(
    _geojson_data,
    name='Kecamatan Wonoayu'
).add_to(_m)

# Tampilkan peta
_m

connection = openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc()

GEOJSON_PATH = "wonoayu.geojson"

if not os.path.exists(GEOJSON_PATH):
    if "google.colab" in sys.modules:
        from google.colab import files
        print("File 'wonoayu.geojson' tidak ditemukan di sesi ini. Silakan upload:")
        uploaded = files.upload()
        # Jika nama file hasil upload berbeda, ubah namanya menjadi wonoayu.geojson
        uploaded_name = list(uploaded.keys())[0]
        if uploaded_name != GEOJSON_PATH:
            os.rename(uploaded_name, GEOJSON_PATH)
    else:
        raise FileNotFoundError(
            f"'{GEOJSON_PATH}' tidak ditemukan. Letakkan file ini di direktori kerja sebelum lanjut."
        )

print(f"Menggunakan file AOI: {GEOJSON_PATH}")

import shapely.geometry

# Baca file GeoJSON berisi batas wilayah Kecamatan Wonoayu
with open(GEOJSON_PATH, 'r') as f:
    geojson_data = json.load(f)

feature = geojson_data['features'][0]
geometry = feature['geometry']

# Ubah GeoJSON menjadi objek geometri shapely untuk seluruh wilayah kabupaten
shp = shapely.geometry.shape(geometry)
print(f"Geometry type: {shp.geom_type}")
if shp.geom_type == 'MultiPolygon':
    print(f"Jumlah bagian polygon: {len(shp.geoms)}")
    for i, part in enumerate(shp.geoms):
        pw, ps, pe, pn = part.bounds
        print(f"  bagian {i}: bbox approx {(pe-pw)*111:.2f} km x {(pn-ps)*111:.2f} km, {len(part.exterior.coords)} vertices")

# Gunakan geometri lengkap sebagai area of interest (AOI)
aoi = geometry

# Hitung bounding box dari keseluruhan geometri kabupaten
west, south, east, north = shp.bounds
spatial_extent = {
    "west": west,
    "south": south,
    "east": east,
    "north": north,
}

print(f"\nAOI defined for Kecamatan Wonoayu region")
print(f"Bounding box: {spatial_extent}")
print(f"Bounding box size (approx): {(east-west)*111:.1f} km x {(north-south)*111:.1f} km")

pollutant_bands = ["NO2", "CO", "HCHO", "SO2", "O3", "CH4"]
time_extent = ["2025-08-31", "2026-08-31"]

def build_pollutant_cube(band):
    cube = connection.load_collection(
        "SENTINEL_5P_L2",
        temporal_extent=time_extent,
        spatial_extent=spatial_extent,
        bands=[band],
    )
    # Rata-ratakan nilai per hari agar setiap tanggal hanya punya satu nilai
    cube = cube.aggregate_temporal_period(reducer="mean", period="day")
    # Hitung rata-rata spasial di seluruh wilayah sehingga menjadi deret waktu harian
    cube = cube.aggregate_spatial(reducer="mean", geometries=aoi)
    return cube

print(f"Akan membuat {len(pollutant_bands)} job terpisah, satu per polutan: {pollutant_bands}")

output_files = {}

for band in pollutant_bands:
    print(f"\n=== Menjalankan job untuk band: {band} ===")
    cube = build_pollutant_cube(band)
    outputfile = f"wonoayu_{band}.csv"
    # Simpan hasil dalam format CSV
    job = cube.execute_batch(title=f"Polutan Kecamatan Wonoayu - {band}", outputfile=outputfile, out_format="CSV")
    output_files[band] = outputfile
    print(f"Selesai: {outputfile}")

print("\nSemua job selesai. File output:", output_files)

import matplotlib.pyplot as plt

series_by_pollutant = {}

for band, path in output_files.items():
    df = pd.read_csv(path)
    print(f"{band}: kolom = {list(df.columns)}")

    # Cari kolom yang berisi tanggal/waktu
    time_col_candidates = [c for c in df.columns if c.lower() in ("date", "time", "t", "datetime")]
    time_col = time_col_candidates[0] if time_col_candidates else df.columns[0]

    # Tentukan kolom yang berisi nilai konsentrasi polutan
    exclude_cols = {time_col, "feature_index", "geometry"}
    if band in df.columns:
        value_col = band
    else:
        numeric_candidates = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])]
        value_col = numeric_candidates[0]

    times = pd.to_datetime(df[time_col])
    series_by_pollutant[band] = pd.Series(df[value_col].values, index=times, name=band)
    print(f"  -> {len(times)} titik waktu, kolom waktu='{time_col}', kolom nilai='{value_col}'")

# Gabungkan kelima polutan menjadi satu tabel berdasarkan tanggal
combined = pd.concat(series_by_pollutant.values(), axis=1).sort_index()
combined.index.name = "date"
combined.head()

rolling = combined.rolling(window=30, min_periods=1).mean()
rolling.head()

# Gambar grafik garis tren waktu untuk masing-masing polutan
pollutant_labels = {
    'NO2': 'NO₂ (mol/m²)',
    'CO': 'CO (mol/m²)',
    'HCHO': 'HCHO (mol/m²)',
    'SO2': 'SO₂ (mol/m²)',
    'O3': 'O₃ (mol/m²)',
    'CH4': 'CH₄ (mol/m²)',
}
colors = {'NO2': 'red', 'CO': 'blue', 'HCHO': 'green', 'SO2': 'orange', 'O3': 'purple', 'CH4': 'brown'}

fig, axes = plt.subplots(len(pollutant_bands), 1, figsize=(12, 18), dpi=100)

for i, band in enumerate(pollutant_bands):
    if band in rolling.columns:
        label = pollutant_labels.get(band, band)
        axes[i].plot(rolling.index, rolling[band], color=colors.get(band, 'black'), label=label)
        axes[i].set_ylabel(label)
        axes[i].set_title(f'Konsentrasi {label} di Kecamatan Wonoayu')
        axes[i].grid(True, alpha=0.3)
        axes[i].legend(loc='upper right')

axes[-1].set_xlabel('Waktu')
plt.tight_layout()
plt.show()

# Simpan data gabungan dan versi rolling mean ke file CSV
combined.reset_index().to_csv('wonoayu_pollutants.csv', index=False)
rolling.reset_index().to_csv('wonoayu_pollutants_rolling30.csv', index=False)
print('Data disimpan ke wonoayu_pollutants.csv dan wonoayu_pollutants_rolling30.csv')
print(f'Data shape: {combined.shape}')
print('\nFirst few rows:')
combined.head()

import zipfile

output_zip_filename = 'wonoayu_pollutants_data.zip'
csv_files_to_zip = [
    'wonoayu_NO2.csv',
    'wonoayu_CO.csv',
    'wonoayu_HCHO.csv',
    'wonoayu_SO2.csv',
    'wonoayu_O3.csv',
    'wonoayu_CH4.csv',
    'wonoayu_pollutants.csv',
    'wonoayu_pollutants_rolling30.csv'
]

with zipfile.ZipFile(output_zip_filename, 'w') as zipf:
    for csv_file in csv_files_to_zip:
        if os.path.exists(csv_file):
            zipf.write(csv_file, os.path.basename(csv_file))
            print(f'Menambahkan {csv_file} ke {output_zip_filename}')
        else:
            print(f'Peringatan: {csv_file} tidak ditemukan dan tidak akan ditambahkan ke ZIP.')

print(f'Semua file CSV berhasil di-ZIP ke: {output_zip_filename}')

# Jika berjalan di Google Colab, unduh file ZIP secara otomatis
if 'google.colab' in sys.modules:
    from google.colab import files
    files.download(output_zip_filename)
    
    