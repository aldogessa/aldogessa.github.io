"""
=================================================================================================
VERSIONE TESTATA SU QGIS 3.40
Lo script esegue un filtro sulla stessa tabella a partire da una riga selezionata, restituendo
in una nuova tabella, solamente le righe che hanno la stessa chiave esterna (non occorre definire
una relazione in QGIS).
In questo caso specificio la tabella rappresenta le pratiche edilizie di un comune e la chiave
esterna unisce tutte le pratiche che riguardano lo stesso immobile. Lo script, selezionata una
pratica, restituisce dunque tutte le pratiche che hanno riguardato lo stesso immobile.
=================================================================================================
"""


from qgis.core import QgsProject
from qgis.utils import iface

# Ottieni il layer
layer = QgsProject.instance().mapLayersByName("Pratiche edilizie")[0] # Qui definire il layer delle pratiche edilizie

# Assicurati che ci sia una selezione attiva
selected_features = layer.selectedFeatures()
if not selected_features:
    iface.messageBar().pushMessage("Errore", "Nessuna pratica selezionata!", level=3)
else:
    # Ottieni i valori delle colonne 'racc_num' e 'racc_anno' dal record selezionato
    selected_record = selected_features[0]
    racc_num_value = selected_record["racc_num"] # Qui definire i campi di unione - il primo rappresenta il nmero di una pratica qualsiasi
    racc_anno_value = selected_record["racc_anno"] # Qui definire i campi unione - il secondo rappresenta l'anno della pratica scelta come unione

    # Crea una query per filtrare i record corrispondenti
    expression = f'"racc_num" = {racc_num_value} AND "racc_anno" = {racc_anno_value}'

    # Controlla se il filtro restituirebbe risultati
    filtered_features = layer.getFeatures(expression)
    if not any(filtered_features):
        iface.messageBar().pushMessage("Errore", "La pratica non è associata ad altre pratiche!", level=3)
    else:
        # Mostra la tabella filtrata senza modificare la selezione del layer
        iface.showAttributeTable(layer, expression)
        iface.messageBar().pushMessage("Informazione", "Tabella aperta mostrando i record filtrati!", level=0)

