import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score

# Load datasets
co_df = pd.read_csv('data1kelas/co.csv')
no2_df = pd.read_csv('data1kelas/no2.csv')
so2_df = pd.read_csv('data1kelas/so2.csv')

meta_cols = ['id', 'nama', 'daerah']
feat_cols = [c for c in co_df.columns if c not in meta_cols]

# Find index for Wonoayu and Jabon
idx_wonoayu = co_df[co_df['daerah'].str.contains('Wonoayu', case=False, na=False)].index[0]
idx_jabon = co_df[co_df['daerah'].str.contains('jabon', case=False, na=False)].index[0]

print(f"Index Wonoayu: {idx_wonoayu}, Nama: {co_df.loc[idx_wonoayu, 'nama']}, Daerah: {co_df.loc[idx_wonoayu, 'daerah']}")
print(f"Index Jabon: {idx_jabon}, Nama: {co_df.loc[idx_jabon, 'nama']}, Daerah: {co_df.loc[idx_jabon, 'daerah']}")

# Feature scaling & PCA per pollutant
def analyze_pollutant(df, name):
    X = df[feat_cols].values
    # Clean inf/nan if any
    X = np.nan_to_num(X)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=10)
    X_pca = pca.fit_transform(X_scaled)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_pca)

    w_cluster = labels[idx_wonoayu]
    j_cluster = labels[idx_jabon]

    # Euclidean distance between Wonoayu and Jabon in feature space
    dist_raw = np.linalg.norm(X_scaled[idx_wonoayu] - X_scaled[idx_jabon])
    dist_pca = np.linalg.norm(X_pca[idx_wonoayu] - X_pca[idx_jabon])

    print(f"\n--- Analisis Polutan {name} ---")
    print(f"Cluster Wonoayu: {w_cluster}")
    print(f"Cluster Jabon  : {j_cluster}")
    print(f"Apakah dalam klaster yang sama? {'YA ✅' if w_cluster == j_cluster else 'TIDAK ❌'}")
    print(f"Jarak Euclidean (Scaled Features): {dist_raw:.4f}")
    print(f"Jarak Euclidean (PCA Space)     : {dist_pca:.4f}")

    # Mean pollutant level proxy (e.g. calc_mean)
    if 'calc_mean' in df.columns:
        print(f"Rata-rata {name} Wonoayu: {df.loc[idx_wonoayu, 'calc_mean']:.6f}")
        print(f"Rata-rata {name} Jabon  : {df.loc[idx_jabon, 'calc_mean']:.6f}")

analyze_pollutant(co_df, 'CO')
analyze_pollutant(no2_df, 'NO2')
analyze_pollutant(so2_df, 'SO2')

# Combined Analysis (CO + NO2 + SO2 concatenated features)
X_combined = np.hstack([
    StandardScaler().fit_transform(np.nan_to_num(co_df[feat_cols].values)),
    StandardScaler().fit_transform(np.nan_to_num(no2_df[feat_cols].values)),
    StandardScaler().fit_transform(np.nan_to_num(so2_df[feat_cols].values))
])

pca_comb = PCA(n_components=10)
X_comb_pca = pca_comb.fit_transform(X_combined)

kmeans_comb = KMeans(n_clusters=3, random_state=42, n_init=10)
labels_comb = kmeans_comb.fit_predict(X_comb_pca)

w_comb_cluster = labels_comb[idx_wonoayu]
j_comb_cluster = labels_comb[idx_jabon]
dist_comb = np.linalg.norm(X_comb_pca[idx_wonoayu] - X_comb_pca[idx_jabon])

print(f"\n==========================================")
print(f"=== HASIL COMBINED MULTI-POLUTAN (CO+NO2+SO2) ===")
print(f"==========================================")
print(f"Cluster Wonoayu: Cluster {w_comb_cluster}")
print(f"Cluster Jabon  : Cluster {j_comb_cluster}")
print(f"Apakah Wonoayu dan Jabon dalam Klaster yang Sama? {'SANGAT MIRIP (Satu Klaster) ✅' if w_comb_cluster == j_comb_cluster else 'BERBEDA KLASTER ❌'}")
print(f"Jarak Similarity PCA Combined: {dist_comb:.4f}")
