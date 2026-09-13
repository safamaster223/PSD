import json
import os
import pandas as pd
import shapely.geometry
import openeo

# 1. Konfigurasi Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GEOJSON_PATH = os.path.join(BASE_DIR, "02_data_understanding", "wonoayu.geojson")
OUT_DIR = os.path.join(BASE_DIR, "data", "downloads", "sidoarjo_pollutants_data")
os.makedirs(OUT_DIR, exist_ok=True)

POLLUTANTS = ["NO2", "SO2", "CO", "HCHO", "O3", "CH4"]
TIME_EXTENT = ["2023-01-01", "2023-12-31"] # Menggunakan data historis 1 tahun penuh yang valid

# 2. Parsing Geometri Wonoayu
print(f"Membaca batas wilayah dari: {GEOJSON_PATH}")
with open(GEOJSON_PATH, "r") as f:
    geojson_data = json.load(f)
geometry = geojson_data["features"][0]["geometry"]
shp = shapely.geometry.shape(geometry)
spatial_extent = dict(zip(["west", "south", "east", "north"], shp.bounds))

# 3. Autentikasi OpenEO
print("Menghubungkan ke Copernicus Data Space Ecosystem...")
connection = openeo.connect("openeo.dataspace.copernicus.eu").authenticate_oidc()

all_dfs = []

# 4. Looping Ekstraksi Data per Polutan
for pol in POLLUTANTS:
    print(f"\n--- Memproses {pol} ---")
    out_csv = os.path.join(OUT_DIR, f"wonoayu_{pol}.csv")
    
    # Bangun Data Cube
    cube = connection.load_collection(
        "SENTINEL_5P_L2",
        temporal_extent=TIME_EXTENT,
        spatial_extent=spatial_extent,
        bands=[pol]
    )
    
    # Agregasi Temporal (Rata-rata harian) & Spasial (Rata-rata area Wonoayu)
    cube = cube.aggregate_temporal_period(reducer="mean", period="day")
    cube = cube.aggregate_spatial(reducer="mean", geometries=geometry)
    
    # Download langsung (Synchronous)
    print(f"Mengunduh data {pol} dari satelit (ini mungkin memakan waktu 1-3 menit)...")
    cube.download(out_csv, format="CSV")
    
    # Merapikan CSV hasil download
    df = pd.read_csv(out_csv)
    time_col = [c for c in df.columns if c.lower() in ("date", "time", "t", "datetime")][0]
    exclude_cols = {time_col, "feature_index", "geometry"}
    val_col = [c for c in df.columns if c not in exclude_cols and pd.api.types.is_numeric_dtype(df[c])][0]
    
    df["date"] = pd.to_datetime(df[time_col]).dt.date
    df = df[["date", val_col]].rename(columns={val_col: pol})
    df = df.groupby("date").mean().reset_index() # Memastikan tidak ada duplikat tanggal
    
    df.to_csv(out_csv, index=False)
    all_dfs.append(df)
    print(f"Selesai! Data {pol} tersimpan di {out_csv}")

# 5. Menggabungkan Semua Data
print("\n--- Menggabungkan semua data polutan ---")
merged_df = all_dfs[0]
for d in all_dfs[1:]:
    merged_df = pd.merge(merged_df, d, on="date", how="outer")

merged_df = merged_df.sort_values("date").reset_index(drop=True)
merged_csv = os.path.join(OUT_DIR, "wonoayu_pollutants.csv")
merged_df.to_csv(merged_csv, index=False)
print(f"Data gabungan tersimpan di: {merged_csv}")

# 6. Membuat Versi Rolling Mean 30 Hari
print("Menghitung Rolling Mean 30 Hari...")
rolling_df = merged_df.copy()
for pol in POLLUTANTS:
    rolling_df[pol] = rolling_df[pol].rolling(window=30, min_periods=1).mean()

rolling_csv = os.path.join(OUT_DIR, "wonoayu_pollutants_rolling30.csv")
rolling_df.to_csv(rolling_csv, index=False)
print(f"Data rolling mean tersimpan di: {rolling_csv}")

print("\nSEMUA PROSES SELESAI! Data Wonoayu siap digunakan.")