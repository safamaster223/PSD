"""Download Sentinel-2A Jawa Timur via openEO (Copernicus Data Space Ecosystem).

Fase (jalankan berurutan):
  python download_raster_jatim.py --phase auth      # 1x saja: login device-flow (klik link), simpan refresh token
  python download_raster_jatim.py --phase features  # ekstraksi mean 6 band per poligon training -> jatim/features/*.csv
  python download_raster_jatim.py --phase demo      # download raster komposit jendela demo -> jatim/raster/*.tif

Butuh: pip install openeo geopandas  (+ akun Copernicus Data Space gratis)
"""

import argparse
import json
import os

import geopandas as gpd
import openeo
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JATIM_DIR = os.path.join(BASE_DIR, "jatim")
SAMPLES_GPKG = os.path.join(JATIM_DIR, "training_samples_jawa_timur.gpkg")
FEATURES_DIR = os.path.join(JATIM_DIR, "features")
RASTER_DIR = os.path.join(JATIM_DIR, "raster")

BACKEND = "openeo.dataspace.copernicus.eu"
COLLECTION = "SENTINEL2_L2A"
TEMPORAL_EXTENT = ["2025-08-01", "2025-10-15"]  # musim kemarau Jatim, minim awan
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]

# Jendela demo peta: Sidoarjo-Surabaya-Selat Madura (ada 184 poligon sampel, 5 kelas)
DEMO_EXTENT = {"west": 112.60, "south": -7.55, "east": 113.00, "north": -7.05}


def connect():
    conn = openeo.connect(BACKEND)
    try:
        conn.authenticate_oidc_refresh_token()
        print("auth: refresh token OK (tanpa login ulang)")
    except Exception as e:
        raise SystemExit(
            f"auth GAGAL ({e}). Jalankan dulu: python download_raster_jatim.py --phase auth"
        )
    return conn


def phase_auth(args):
    conn = connect()
    print("Membuka device-flow. Klik link verifikasi yang muncul di bawah,")
    print("masukkan kode user bila diminta, lalu kembali ke sini.")
    conn.authenticate_oidc_device(
        store_refresh_token=True, max_poll_time=args.wait
    )
    print("AUTH OK — refresh token tersimpan, job berikutnya tanpa login ulang.")


def base_cube(conn):
    cube = conn.load_collection(
        COLLECTION,
        temporal_extent=TEMPORAL_EXTENT,
        bands=BANDS,
    )
    cube = cube.reduce_dimension(dimension="t", reducer="median")
    return cube


def _run_part(task):
    import time
    cid, p, geoms, part_csv, redo = task
    if os.path.exists(part_csv) and not redo:
        return f"[skip] kelas {cid} part {p} sudah ada"
    last = None
    for attempt in range(1, 7):
        try:
            conn = connect()
            cube = base_cube(conn)
            cube = cube.aggregate_spatial(
                reducer="mean",
                geometries={"type": "FeatureCollection", "features": geoms},
            )
            cube.execute_batch(
                title=f"Jatim S2 features kelas {cid} p{p}",
                outputfile=part_csv, out_format="CSV",
            )
            if (not os.path.exists(part_csv)) or os.path.getsize(part_csv) == 0:
                if os.path.exists(part_csv):
                    os.remove(part_csv)
                raise IOError(f"hasil kosong (0 byte): {part_csv}")
            return f"[ok] tersimpan: {part_csv}"
        except Exception as e:
            last = e
            msg = f"{type(e).__name__}: {str(e)[:120]}"
            if "429" in msg or "Too Many" in msg or "timeout" in msg.lower() or "hasil kosong" in msg:
                wait = 30 * attempt
                print(f"[retry {attempt}/6] kelas {cid} part {p} ({msg}) — tunggu {wait}s")
                time.sleep(wait)
            else:
                break
    return f"[GAGAL] kelas {cid} part {p}: {type(last).__name__}: {str(last)[:200]}"


def phase_features(args):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    os.makedirs(FEATURES_DIR, exist_ok=True)
    g = gpd.read_file(SAMPLES_GPKG, layer="training_samples")
    # Sederhanakan geometri (toleransi ~10 m = ukuran piksel) + bulatkan koordinat:
    # payload process-graph backend dibatasi (~413 di atas ~3 MB), jadi kirim per chunk kecil.
    gs = g.copy()
    gs["geometry"] = (
        g.to_crs("EPSG:32749").geometry.simplify(10).to_crs("EPSG:4326")
    )
    tasks, chunks = [], {}
    for cid in sorted(g["class_id"].unique().tolist()):
        sub = gs[gs["class_id"] == cid].reset_index(drop=True)
        chunks[cid] = []
        for p, start in enumerate(range(0, len(sub), 100)):
            chunk = sub.iloc[start:start + 100]
            part_csv = os.path.join(FEATURES_DIR, f"features_class{cid}_p{p}.csv")
            chunks[cid].append(part_csv)
            geoms = [
                {"type": "Feature", "properties": {"fid": int(i)},
                 "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]}
                for i, geom in zip(chunk.index, chunk.geometry)
            ]
            tasks.append((cid, p, geoms, part_csv, args.redo))
    print(f"[info] {len(tasks)} job, {args.workers} worker paralel")
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(_run_part, t): t for t in tasks}
        for f in as_completed(futs):
            try:
                print(f.result())
            except Exception as e:
                t = futs[f]
                print(f"[GAGAL] kelas {t[0]} part {t[1]}: {type(e).__name__}: {str(e)[:200]}")
    for cid, parts in chunks.items():
        done = [p for p in parts if os.path.exists(p)]
        if len(done) != len(parts):
            print(f"[WARN] kelas {cid}: {len(done)}/{len(parts)} part — gabungan ditunda")
            continue
        out_csv = os.path.join(FEATURES_DIR, f"features_class{cid}.csv")
        pd.concat([pd.read_csv(p) for p in parts], ignore_index=True).to_csv(out_csv, index=False)
        print(f"[ok] gabungan kelas {cid}: {out_csv}")


def phase_demo(args):
    import time
    os.makedirs(RASTER_DIR, exist_ok=True)
    out_tif = os.path.join(RASTER_DIR, "s2_demo_sidoarjo.tif")
    if os.path.exists(out_tif) and os.path.getsize(out_tif) > 0 and not args.redo:
        print(f"[skip] sudah ada: {out_tif}")
        return
    conn = connect()
    cube = base_cube(conn)
    cube = cube.filter_bbox(**DEMO_EXTENT)
    cube = cube.resample_spatial(resolution=args.res, projection=32749)
    last = None
    for attempt in range(1, 5):
        try:
            print(f"[job] batch demo {DEMO_EXTENT} @ {args.res}m (coba {attempt}/4) ...")
            job = cube.create_job(title="Jatim S2 demo Sidoarjo", out_format="GTiff")
            print("job id:", job.job_id, "- menunggu selesai ...")
            job.start_and_wait()
            assets = job.download_results(RASTER_DIR)
            tifs = [a for a in (assets or []) if str(a).lower().endswith(".tif")]
            if not tifs:
                tifs = [os.path.join(RASTER_DIR, f) for f in os.listdir(RASTER_DIR)
                        if f.lower().endswith(".tif")]
            if not tifs:
                raise IOError("tidak ada aset .tif dari job")
            src = tifs[0] if isinstance(tifs[0], str) else str(tifs[0])
            if os.path.abspath(src) != os.path.abspath(out_tif):
                if os.path.exists(out_tif):
                    os.remove(out_tif)
                os.rename(src, out_tif)
            print(f"[ok] tersimpan: {out_tif}")
            return
        except Exception as e:
            last = e
            print(f"[retry {attempt}/4] {type(e).__name__}: {str(e)[:150]} — tunggu 60s")
            time.sleep(60)
    raise SystemExit(f"demo GAGAL permanen: {last}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["auth", "features", "demo"], required=True)
    ap.add_argument("--wait", type=int, default=1800, help="detik maks menunggu klik auth")
    ap.add_argument("--res", type=int, default=20, help="resolusi meter raster demo")
    ap.add_argument("--redo", action="store_true", help="ulangi job features walau CSV ada")
    ap.add_argument("--workers", type=int, default=5, help="worker paralel fase features")
    ns = ap.parse_args()
    {"auth": phase_auth, "features": phase_features, "demo": phase_demo}[ns.phase](ns)
