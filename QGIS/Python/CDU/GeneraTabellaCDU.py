"""
==========================================================================
ESPERIMENTO SU QGIS 3.28
Questo script esegue le intersezioni tra le particelle catastali e tutti
i layer contenuti nel gruppo "URBANISTICA" e le registra all'interno di una
tabella preconfigurata chiamata tabella CDU. Per ottenere una tabella corente
e consistente, le tabelle dei layer da coinvolgere nelle intersezioni devono
essere preventivamente omogeneizzati.
Questp script è progettato per funzionare come azione Python definito sul
layer "Particelle"
===========================================================================
"""

import processing
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsField, QgsFeature
from qgis.PyQt.QtCore import QVariant
from qgis.utils import iface
from qgis.core import Qgis
from qgis.core import QgsMessageLog  # Corretto
from PyQt5.QtWidgets import QMessageBox

def esegui_script():
    print("🔄 Avvio script...")

    try:
        # **Ottieni il layer "Particelle"**
        particelle_layer = QgsProject.instance().mapLayersByName("Particelle") # Layer che contiene le particelle catastali

        if not particelle_layer:
            iface.messageBar().pushMessage("Attenzione", "Il layer Particelle non esiste", level=Qgis.Critical, duration=5)
            QgsMessageLog.logMessage("Layer 'Particelle' non trovato.", "CustomScript", Qgis.Critical)
            return  

        particelle_layer = particelle_layer[0]
        print("✅ Layer 'Particelle' trovato.")

        # **Verifica la selezione**
        if not particelle_layer.selectedFeatureCount():
            iface.messageBar().pushMessage("Attenzione", "Devi selezionare almeno una particella", level=Qgis.Critical, duration=5)
            QgsMessageLog.logMessage("Nessuna particella selezionata.", "CustomScript", Qgis.Critical)
            return  

        print(f"✅ {particelle_layer.selectedFeatureCount()} particelle selezionate.")

        selected_layer = processing.run("native:saveselectedfeatures", {
            'INPUT': particelle_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

        # **Ottieni il layer "TabellaCDU" dal progetto**
        tabellaCDU_layer = QgsProject.instance().mapLayersByName("TabellaCDU") # Qui bisogna definire il nome della tabella che accoglierà il risultato delle intersezioni

        if not tabellaCDU_layer:
            iface.messageBar().pushMessage("ATTENZIONE", "Non esiste la Tabella CDU", level=Qgis.Critical, duration=5)
            QgsMessageLog.logMessage("Layer 'TabellaCDU' non trovato.", "CustomScript", Qgis.Critical)
            return  

        tabellaCDU_layer = tabellaCDU_layer[0]
        print("✅ Layer 'TabellaCDU' trovato.")

        # **Verifica se il layer contiene dati e chiedi all'utente se vuole svuotarlo**
        if tabellaCDU_layer.featureCount() > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setText("⚠️ Il layer 'TabellaCDU' contiene dati! Vuoi svuotarlo?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)

            user_choice = msg_box.exec_()

            if user_choice == QMessageBox.No:
                iface.messageBar().pushMessage("Operazione annullata", "Il Layer TabellaCDU non sarà modificato", level=Qgis.Info, duration=5)
                return  

            tabellaCDU_layer.startEditing()
            tabellaCDU_layer.dataProvider().deleteFeatures([f.id() for f in tabellaCDU_layer.getFeatures()])
            tabellaCDU_layer.commitChanges()
            print("✅ Layer 'TabellaCDU' svuotato.")

        # **Recupera i layer poligonali nel gruppo URBANISTICA**
        urbanistica_group = QgsProject.instance().layerTreeRoot().findGroup("URBANISTICA") # Qui occorre definire il nome del gruppo che contiene i layer da intersecare con le particelle
        urbanistica_layers = [
            layer.layer() for layer in urbanistica_group.children()
            if isinstance(layer, QgsLayerTreeLayer) and layer.layer().geometryType() == 2
        ]

        print(f"✅ Recuperati {len(urbanistica_layers)} layer poligonali da 'URBANISTICA'.")

        intersections = []

        for layer in urbanistica_layers:
            if not layer.isValid():
                print(f"⚠️ Il layer '{layer.name()}' non è valido, salto l'intersezione.")
                continue
            result = processing.run("native:intersection", {
                'INPUT': selected_layer,
                'OVERLAY': layer,
                'OUTPUT': f'memory:Intersezione_{layer.name()}'
            })['OUTPUT']
            intersections.append(result)
            print(f"✅ Intersezione con '{layer.name()}' completata.")

        merged_layer = processing.run("native:mergevectorlayers", {
            'LAYERS': intersections,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

        if merged_layer:
            print("✅ Le intersezioni sono state unite in un unico layer temporaneo.")

            merged_layer_provider = merged_layer.dataProvider()
            merged_layer_provider.addAttributes([QgsField("percent", QVariant.Int)])
            merged_layer.updateFields()

            merged_layer.startEditing()
            for feature in merged_layer.getFeatures():
                area_value = feature.geometry().area()
                area1_value = feature["Area1"]
                percent_value = round(area_value / float(area1_value) * 100) if area1_value else 0
                feature["percent"] = percent_value
                merged_layer.updateFeature(feature)
                print(f"ℹ️ Percentuale calcolata: {percent_value}% per feature {feature.id()}.")

            merged_layer.commitChanges()
            print("✅ Il campo 'percent' è stato popolato.")

            fields_to_keep = ["foglio", "allegato", "mappale", "tema", "zona", "descrizion", "percent"]
            reorganized_layer = processing.run("native:retainfields", {
                'INPUT': merged_layer,
                'FIELDS': fields_to_keep,
                'OUTPUT': 'TEMPORARY_OUTPUT'
            })['OUTPUT']

            reorganized_layer.setName("Tabella_CDU")
            print("✅ Layer 'Tabella_CDU' creato con campi selezionati.")

            # **Copiatura con corrispondenza dei campi**
            tabellaCDU_layer.startEditing()
            source_fields = reorganized_layer.fields()
            destination_fields = tabellaCDU_layer.fields()

            copied_count = 0
            for feature in reorganized_layer.getFeatures():
                new_feature = QgsFeature(destination_fields)
                new_feature.setGeometry(feature.geometry())

                attributes = [None] * len(destination_fields)
                for i, field in enumerate(destination_fields):
                    source_index = source_fields.indexOf(field.name())
                    if source_index != -1:
                        attributes[i] = feature.attributes()[source_index]

                new_feature.setAttributes(attributes)
                tabellaCDU_layer.addFeature(new_feature)
                copied_count += 1

            tabellaCDU_layer.commitChanges()
            print(f"✅ Copiate {copied_count} feature in 'TabellaCDU'.")

        # **Finestra di dialogo finale per apertura tabella attributi**
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText("✅ Processo completato con successo!")
        msg_box.setInformativeText("Premi 'OK' per aprire la tabella degli attributi di 'TabellaCDU'.")
        msg_box.setStandardButtons(QMessageBox.Ok)

        user_choice = msg_box.exec_()

        if user_choice == QMessageBox.Ok:
            iface.showAttributeTable(tabellaCDU_layer)
            print("✅ Tabella degli attributi aperta per 'TabellaCDU'.")

        iface.messageBar().pushMessage("CONCLUSIONE", "Processo completato con successo!", level=Qgis.Info, duration=5)
        print("🎉 Processo completato con successo!")

    except Exception as e:
        iface.messageBar().pushMessage("Errore", f"Si è verificato un errore: {str(e)}", level=Qgis.Critical, duration=5)
        QgsMessageLog.logMessage(f"Errore: {str(e)}", "CustomScript", Qgis.Critical)
        print(f"❌ Errore: {str(e)}")

# **Esegui la funzione**
esegui_script()
