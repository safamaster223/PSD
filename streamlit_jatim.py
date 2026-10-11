"""Sistem Informasi Klasifikasi Penutup Lahan Jawa Timur (Sentinel-2A, 6 kelas).

Jalankan:  streamlit run streamlit_jatim.py
Butuh:     jatim/model/jatim_best.joblib  (dari 6.2) + jatim/model/jatim_model_compare.csv
"""

import os

import joblib
import pandas as pd
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_P = os.path.join(BASE, "jatim", "model", "jatim_best.joblib")
CMP_P = os.path.join(BASE, "jatim", "model", "jatim_model_compare.csv")

NAMES = {1: "Sawah", 2: "Bangunan / Permukiman", 3: "Mangrove",
         4: "Lahan hijau", 5: "Laut", 6: "Danau"}
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]

st.set_page_config(page_title="Klasifikasi Lahan Jatim", layout="wide")
st.title("Sistem Informasi Klasifikasi Penutup Lahan — Jawa Timur")
st.caption("Sentinel-2A Level-2A | 6 kelas | 12 fitur (6 band + 6 indeks)")

if not os.path.exists(MODEL_P):
    st.warning("Model belum ada. Jalankan 6.2 dulu (`jatim/model/jatim_best.joblib`).")
    st.stop()

clf = joblib.load(MODEL_P)
if os.path.exists(CMP_P):
    with st.expander("Perbandingan model (akurasi tertinggi menang)"):
        st.dataframe(pd.read_csv(CMP_P).round(4), use_container_width=True)

tab1, tab2 = st.tabs(["Tebak kelas", "Klasifikasi CSV"])

with tab1:
    st.subheader("Input nilai reflektansi 6 band (0–10000)")
    cols = st.columns(3)
    vals = [cols[i % 3].number_input(b, value=1000.0, step=50.0) for i, b in enumerate(BANDS)]
    if st.button("Klasifikasikan", type="primary"):
        B02, B03, B04, B08, B11, B12 = vals
        feats = [B02, B03, B04, B08, B11, B12,
                 (B08 - B04) / (B08 + B04 + 1e-9),
                 (B03 - B08) / (B03 + B08 + 1e-9),
                 (B11 - B08) / (B11 + B08 + 1e-9),
                 (B08 - B11) / (B08 + B11 + 1e-9),
                 2.5 * (B08 - B04) / (B08 + 6 * B04 - 7.5 * B02 + 1 + 1e-9),
                 ((B08 - B04) / (B08 + B04 + 0.5 + 1e-9)) * 1.5]
        pred = int(clf.predict([feats])[0])
        proba = clf.predict_proba([feats])[0] if hasattr(clf, "predict_proba") else None
        st.success(f"Hasil: **Kelas {pred} — {NAMES[pred]}**")
        if proba is not None:
            st.bar_chart(pd.Series(proba, index=[NAMES[i] for i in sorted(NAMES)]))

with tab2:
    st.subheader("Upload CSV berisi kolom B02,B03,B04,B08,B11,B12")
    up = st.file_uploader("Pilih CSV", type="csv")
    if up is not None:
        d = pd.read_csv(up)
        if all(c in d.columns for c in BANDS):
            B02, B03, B04, B08, B11, B12 = (d[c] for c in BANDS)
            d["NDVI"] = (B08 - B04) / (B08 + B04)
            d["NDWI"] = (B03 - B08) / (B03 + B08)
            d["NDBI"] = (B11 - B08) / (B11 + B08)
            d["NDMI"] = (B08 - B11) / (B08 + B11)
            d["EVI"] = 2.5 * (B08 - B04) / (B08 + 6 * B04 - 7.5 * B02 + 1)
            d["SAVI"] = ((B08 - B04) / (B08 + B04 + 0.5)) * 1.5
            d["prediksi"] = clf.predict(d[BANDS + ["NDVI", "NDWI", "NDBI", "NDMI", "EVI", "SAVI"]])
            d["kelas"] = d["prediksi"].map(NAMES)
            st.dataframe(d.head(50), use_container_width=True)
            st.download_button("Unduh hasil", d.to_csv(index=False), "hasil_klasifikasi.csv")
        else:
            st.error(f"Kolom wajib: {BANDS}")
