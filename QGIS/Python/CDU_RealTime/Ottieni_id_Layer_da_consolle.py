"""
AGis - QGIS 3.44.15
Script di supporto che permette di estrarre gli ID dei layer tematici
da utilizzare per l'azione di intersezione al click
"""

project = QgsProject.instance()

for layer in project.mapLayers().values():
    print("-" * 80)
    print("NOME:", layer.name())
    print("ID:", layer.id())
    print("TIPO:", type(layer).__name__)
    print("GEOMETRIA:", layer.geometryType() if hasattr(layer, "geometryType") else "N/D")
