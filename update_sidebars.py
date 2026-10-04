import os
import glob

# Pattern 1: files in 05_kmeans_clustering/
files_05 = glob.glob('_build/html/05_kmeans_clustering/*.html')
for fpath in files_05:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_target = '<li class="toctree-l1"><a class="reference internal" href="5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    old_target_active = '<li class="toctree-l1 current active"><a class="current reference internal" href="#">5.7 Notebook Clustering Data 1 Kelas</a></li>'

    new_addition = '\n<li class="toctree-l1"><a class="reference internal" href="5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    updated = False
    if old_target in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(old_target, old_target + new_addition)
        updated = True
    elif old_target_active in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(old_target_active, old_target_active + new_addition)
        updated = True

    if updated:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fpath}")

# Pattern 2: files in root _build/html/
files_root = glob.glob('_build/html/*.html')
for fpath in files_root:
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_target = '<li class="toctree-l1"><a class="reference internal" href="05_kmeans_clustering/5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    new_addition = '\n<li class="toctree-l1"><a class="reference internal" href="05_kmeans_clustering/5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    if old_target in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(old_target, old_target + new_addition)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fpath}")

# Pattern 3: files in subdirectories (01_*, 02_*, 03_*, 04_*)
files_sub = glob.glob('_build/html/*/*.html')
for fpath in files_sub:
    if '05_kmeans_clustering' in fpath:
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_target = '<li class="toctree-l1"><a class="reference internal" href="../05_kmeans_clustering/5.7_clustering_satu_kelas.html">5.7 Notebook Clustering Data 1 Kelas</a></li>'
    new_addition = '\n<li class="toctree-l1"><a class="reference internal" href="../05_kmeans_clustering/5.8_clustering_polynomial.html">5.8 Notebook Clustering Data Polynomial</a></li>'

    if old_target in content and '5.8_clustering_polynomial.html' not in content:
        content = content.replace(old_target, old_target + new_addition)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {fpath}")
