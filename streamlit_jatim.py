"""Sistem Informasi Klasifikasi Penutup Lahan Jawa Timur + Wonoayu.

Jalankan:  streamlit run streamlit_jatim.py
Data:      jatim/model/jatim_dataset_12fitur.csv (2658 sampel, 6 kelas, 12 fitur)
           jatim/model/wonoayu_*.csv bila ada (87 poligon biner) -- fallback: zonal dari shapefile
Isi:       eksplorasi data + training & perbandingan model live + tebak kelas + batch CSV.
"""

import os

import joblib
import matplotlib
import numpy as np
import pandas as pd
import streamlit as st

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE, "jatim", "model")
DATA_P = os.path.join(MODEL_DIR, "jatim_dataset_12fitur.csv")
BEST_P = os.path.join(MODEL_DIR, "jatim_best.joblib")

NAMES = {1: "Sawah", 2: "Bangunan / Permukiman", 3: "Mangrove",
         4: "Lahan hijau", 5: "Laut", 6: "Danau"}
BANDS = ["B02", "B03", "B04", "B08", "B11", "B12"]
INDICES = ["NDVI", "NDWI", "NDBI", "NDMI", "EVI", "SAVI"]
FEATS = BANDS + INDICES


@st.cache_data
def load_dataset():
    d = pd.read_csv(DATA_P)
    return d


def add_indices(d):
    d = d.copy()
    B02, B03, B04, B08, B11, B12 = (pd.to_numeric(d[c], errors="coerce") for c in BANDS)
    d["NDVI"] = (B08 - B04) / (B08 + B04)
    d["NDWI"] = (B03 - B08) / (B03 + B08)
    d["NDBI"] = (B11 - B08) / (B11 + B08)
    d["NDMI"] = (B08 - B11) / (B08 + B11)
    d["EVI"] = 2.5 * (B08 - B04) / (B08 + 6 * B04 - 7.5 * B02 + 1)
    d["SAVI"] = ((B08 - B04) / (B08 + B04 + 0.5)) * 1.5
    return d.dropna(subset=FEATS).reset_index(drop=True)


def candidates(seed):
    from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC
    return {
        "RandomForest": RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=-1),
        "SVM-RBF-C10": make_pipeline(StandardScaler(), SVC(kernel="rbf", C=10, random_state=seed)),
        "KNN-15": make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=15)),
        "HistGradBoost": HistGradientBoostingClassifier(random_state=seed),
    }


@st.cache_resource
def train_all(X, y, seed, test_size):
    from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                                 recall_score)
    from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)
    rows, fitted, preds = [], {}, {}
    cv = StratifiedKFold(5, shuffle=True, random_state=seed)
    for nama, clf in candidates(seed).items():
        clf.fit(Xtr, ytr)
        p = clf.predict(Xte)
        s = cross_val_score(clf, X, y, cv=cv)
        rows.append({"model": nama, "accuracy": accuracy_score(yte, p),
                     "precision_macro": precision_score(yte, p, average="macro", zero_division=0),
                     "recall_macro": recall_score(yte, p, average="macro", zero_division=0),
                     "f1_macro": f1_score(yte, p, average="macro", zero_division=0),
                     "cv5_mean": float(s.mean())})
        fitted[nama] = clf
        preds[nama] = (yte, p)
    res = pd.DataFrame(rows).sort_values("accuracy", ascending=False).reset_index(drop=True)
    return res, fitted, preds, (Xtr, Xte, ytr, yte)


st.set_page_config(page_title="Klasifikasi Lahan Jatim", layout="wide")
st.title("Sistem Informasi Klasifikasi Penutup Lahan — Jawa Timur")
st.caption("Sentinel-2A Level-2A | 6 kelas | 12 fitur (6 band + 6 indeks) | training & banding model live")

if not os.path.exists(DATA_P):
    st.error("Dataset belum ada. Jalankan 6.2 dulu (`jatim/model/jatim_dataset_12fitur.csv`).")
    st.stop()

df = add_indices(load_dataset())
X = df[FEATS].to_numpy()
y = df["class_id"].to_numpy().astype(int)

with st.sidebar:
    st.header("Pengaturan training")
    seed = st.number_input("Seed", value=42, step=1)
    test_size = st.slider("Test size", 0.1, 0.4, 0.2, 0.05)

tab1, tab2, tab3, tab4 = st.tabs(["Data", "Banding model (live)", "Tebak kelas", "Klasifikasi CSV"])

with tab1:
    st.subheader(f"Dataset: {len(df)} sampel × {len(FEATS)} fitur")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Jumlah per kelas")
        st.bar_chart(df["class_id"].map(NAMES).value_counts())
    with c2:
        st.write("Statistik deskriptif fitur")
        st.dataframe(df[FEATS].describe().round(1), use_container_width=True)
    st.write("Tanda tangan spektral rata-rata per kelas (6 band)")
    fig, ax = plt.subplots(figsize=(9, 4))
    for cid in sorted(NAMES):
        ax.plot(BANDS, df[df.class_id == cid][BANDS].mean().to_numpy(),
                marker="o", label=f"{cid} {NAMES[cid]}")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)
    with st.expander("Lihat data mentah"):
        st.dataframe(df.head(200), use_container_width=True)

with tab2:
    st.subheader("Training + perbandingan 4 model (dihitung saat ini juga)")
    with st.spinner("Melatih RandomForest, SVM-RBF-C10, KNN-15, HistGradBoost + CV 5-fold ..."):
        res, fitted, preds, (Xtr, Xte, ytr, yte) = train_all(X, y, int(seed), float(test_size))
    st.dataframe(res.round(4), use_container_width=True)
    best = res.loc[0, "model"]
    st.success(f"Model terbaik: **{best}** (akurasi {res.loc[0, 'accuracy']:.4f}, CV {res.loc[0, 'cv5_mean']:.4f})")
    c1, c2 = st.columns(2)
    with c1:
        from sklearn.metrics import confusion_matrix
        yte0, pb = preds[best]
        cm = confusion_matrix(yte0, pb)
        fig, ax = plt.subplots(figsize=(6, 5))
        ax.imshow(cm)
        labs = [NAMES[i] for i in sorted(NAMES)]
        ax.set_xticks(range(6), labs, rotation=20)
        ax.set_yticks(range(6), labs)
        for i in range(6):
            for j in range(6):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center")
        ax.set_title(f"Confusion matrix — {best}")
        fig.tight_layout()
        st.pyplot(fig)
    with c2:
        clf = fitted[best]
        if hasattr(clf, "feature_importances_"):
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.barh(FEATS, clf.feature_importances_)
            ax.set_title("Feature importance")
            fig.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Model ini tidak punya feature_importances_ (bukan tree-based).")
    if st.button("Simpan model terbaik"):
        joblib.dump(fitted[best], os.path.join(MODEL_DIR, "jatim_best_streamlit.joblib"))
        res.to_csv(os.path.join(MODEL_DIR, "jatim_model_compare_streamlit.csv"), index=False)
        st.success("Tersimpan: jatim_best_streamlit.joblib + jatim_model_compare_streamlit.csv")

with tab3:
    st.subheader("Input nilai reflektansi 6 band (0–10000)")
    if "live_best" not in st.session_state:
        with st.spinner("Training cepat untuk prediksi ..."):
            _, fitted0, _, _ = train_all(X, y, int(seed), float(test_size))
            st.session_state["live_best"] = fitted0["SVM-RBF-C10"]
    clf = st.session_state["live_best"]
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
        st.success(f"Hasil: **Kelas {pred} — {NAMES[pred]}**")

with tab4:
    st.subheader("Upload CSV berisi kolom B02,B03,B04,B08,B11,B12")
    if "live_best" not in st.session_state:
        with st.spinner("Training cepat untuk prediksi ..."):
            _, fitted0, _, _ = train_all(X, y, int(seed), float(test_size))
            st.session_state["live_best"] = fitted0["SVM-RBF-C10"]
    clf = st.session_state["live_best"]
    up = st.file_uploader("Pilih CSV", type="csv")
    if up is not None:
        d = pd.read_csv(up)
        if all(c in d.columns for c in BANDS):
            d = add_indices(d)
            d["prediksi"] = clf.predict(d[FEATS].to_numpy())
            d["kelas"] = d["prediksi"].map(NAMES)
            st.dataframe(d.head(50), use_container_width=True)
            st.download_button("Unduh hasil", d.to_csv(index=False), "hasil_klasifikasi.csv")
        else:
            st.error(f"Kolom wajib: {BANDS}")
