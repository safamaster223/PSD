import os
import glob

# 1. Update sidebars across all HTML files
sub_files_05 = glob.glob('_build/html/05_kmeans_clustering/*.html')
for fpath in sub_files_05:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    target1 = '<li class="toctree-l1"><a class="reference internal" href="5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    target2 = '<li class="toctree-l1 current active"><a class="current reference internal" href="#">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    addition = '\n<li class="toctree-l1"><a class="reference internal" href="5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    if '5.8_clustering_polynomial.html' not in content:
        if target1 in content:
            content = content.replace(target1, target1 + addition)
        elif target2 in content:
            content = content.replace(target2, target2 + addition)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated sidebar in {fpath}")

root_files = glob.glob('_build/html/*.html')
for fpath in root_files:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    target = '<li class="toctree-l1"><a class="reference internal" href="05_kmeans_clustering/5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    addition = '\n<li class="toctree-l1"><a class="reference internal" href="05_kmeans_clustering/5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    if target in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(target, target + addition)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated sidebar in {fpath}")

sub_other_files = glob.glob('_build/html/*/*.html')
for fpath in sub_other_files:
    if '05_kmeans_clustering' in fpath:
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    target = '<li class="toctree-l1"><a class="reference internal" href="../05_kmeans_clustering/5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    addition = '\n<li class="toctree-l1"><a class="reference internal" href="../05_kmeans_clustering/5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    if target in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(target, target + addition)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated sidebar in {fpath}")

# 2. Build _build/html/05_kmeans_clustering/5.8_clustering_polynomial.html from 5.7_clustering_satu_kelas.html template
with open('_build/html/05_kmeans_clustering/5.7_clustering_satu_kelas.html', 'r', encoding='utf-8') as f:
    template = f.read()

# Replace titles and navigation
h58 = template
h58 = h58.replace(
    '<title>5.7 Analisis K-Means Clustering &amp; Reduksi Dimensi PCA Data 1 Kelas (CO, NO2, SO2) &#8212; Analisis Polutan Atmosfer Kecamatan Wonoayu</title>',
    '<title>5.8 Analisis K-Means Clustering &amp; Reduksi Dimensi PCA (Data Polynomial Interpolation) &#8212; Analisis Polutan Atmosfer Kecamatan Wonoayu</title>'
)
h58 = h58.replace(
    'DOCUMENTATION_OPTIONS.pagename = \'05_kmeans_clustering/5.7_clustering_satu_kelas\';',
    'DOCUMENTATION_OPTIONS.pagename = \'05_kmeans_clustering/5.8_clustering_polynomial\';'
)
h58 = h58.replace(
    '<link rel="prev" title="BAB 5 — K-Means Clustering &amp; Reduksi Dimensi PCA (Analisis Granular Per Polutan &amp; Combined)" href="05_kmeans_clustering.html" />',
    '<link rel="prev" title="5.7 Notebook Clustering Data 1 Kelas" href="5.7_clustering_satu_kelas.html" />'
)

# Active state in sidebar
h58 = h58.replace(
    '<li class="toctree-l1 current active"><a class="current reference internal" href="#">5.7 Notebook Clustering Data 1 Kelas</a></li>\n<li class="toctree-l1"><a class="reference internal" href="5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>',
    '<li class="toctree-l1"><a class="reference internal" href="5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>\n<li class="toctree-l1 current active"><a class="current reference internal" href="#">5.8 Notebook Clustering Data Polynomial</a></li>'
)

# Replace main content header
h58 = h58.replace(
    '<h1>5.7 Analisis K-Means Clustering &amp; Reduksi Dimensi PCA Data 1 Kelas (CO, NO2, SO2)<a class="headerlink" href="#analisis-k-means-clustering-reduksi-dimensi-pca-data-1-kelas-co-no2-so2" title="Permalink to this heading">#</a></h1>',
    '<h1>5.8 Analisis K-Means Clustering &amp; Reduksi Dimensi PCA (Data Polynomial Interpolation)<a class="headerlink" href="#analisis-k-means-clustering-reduksi-dimensi-pca-data-polynomial-interpolation" title="Permalink to this heading">#</a></h1>'
)

with open('_build/html/05_kmeans_clustering/5.8_clustering_polynomial.html', 'w', encoding='utf-8') as f:
    f.write(h58)

print("✅ Successfully built 5.8_clustering_polynomial.html!")
