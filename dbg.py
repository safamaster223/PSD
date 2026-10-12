t = open('6.6_evaluasi_poligon.ipynb', encoding='utf-8').read()
i = t.find('2 HTML Folium')
print(repr(t[i-100:i+200]))
