"""
==========================================================================
SCRIPT DEFINITIVO – QGIS 3.40.11
Interseca le particelle selezionate con i layer poligonali scelti tramite
finestra di dialogo, e inserisce i risultati nella tabella "TabellaCDU".

Versione con finestra di dialogo stile pannello Layer (QTreeWidget)
+ Espandi/Collassa gruppi
+ Preview layer selezionati
+ Barra di avanzamento professionale
==========================================================================
"""

import processing

from qgis.core import (
    QgsProject,
    QgsField,
    QgsFeature,
    Qgis
)

from qgis.utils import iface

from qgis.PyQt.QtCore import (
    Qt,
    QVariant,
    QSettings
)

from qgis.PyQt.QtGui import (
    QIcon
)

from qgis.PyQt.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QProgressBar,
    QApplication
)


# ============================================================
#  DIALOGO DI SELEZIONE LAYER (VERSIONE CON GRUPPI + PREVIEW)
# ============================================================

class LayerSelectionDialog(QDialog):
    def __init__(self, polygon_layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleziona i layer da intersecare")
        self.resize(750, 650)

        self.settings = QSettings("AGis", "IntersezioniCDU")
        self.polygon_layers = polygon_layers

        # --- Layout principale orizzontale ---
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # --- Colonna sinistra (albero + controlli) ---
        left_layout = QVBoxLayout()

        # Barra di ricerca
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca layer...")
        self.search_box.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_box)

        # Pulsanti espandi/collassa
        btn_expand = QPushButton("Espandi tutto")
        btn_collapse = QPushButton("Collassa tutto")
        btn_expand.clicked.connect(lambda: self.tree.expandAll())
        btn_collapse.clicked.connect(lambda: self.tree.collapseAll())

        expand_layout = QHBoxLayout()
        expand_layout.addWidget(btn_expand)
        expand_layout.addWidget(btn_collapse)
        left_layout.addLayout(expand_layout)

        # TreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        # Popola struttura
        self.populate_tree()

        # Pulsante pulisci selezione
        btn_clear = QPushButton("Pulisci selezione")
        btn_clear.clicked.connect(self.clear_selection)
        left_layout.addWidget(btn_clear)

        # Pulsanti OK / Annulla
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Annulla")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        left_layout.addLayout(btn_layout)

        # Aggiunge la colonna sinistra al layout principale
        main_layout.addLayout(left_layout, 2)

        # --- Colonna destra: pannelli laterali ---
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        # Titolo pannello selezionati
        lbl_sel = QLabel("<b>Layer selezionati</b>")
        right_layout.addWidget(lbl_sel)

        # Pannello lista layer selezionati
        self.preview_panel = QTextEdit()
        self.preview_panel.setReadOnly(True)
        self.preview_panel.setPlaceholderText("Nessun layer selezionato")
        right_layout.addWidget(self.preview_panel)

        # Titolo pannello informazioni
        lbl_info = QLabel("<b>Informazioni layer corrente</b>")
        right_layout.addWidget(lbl_info)

        # Pannello informativo
        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setPlaceholderText("Seleziona un layer per vedere le informazioni")
        right_layout.addWidget(self.info_panel)

        # Segnali
        self.tree.itemChanged.connect(self.update_selected_preview)
        self.tree.itemClicked.connect(self.update_layer_info)

        # Aggiorna preview iniziale
        self.update_selected_preview()

    # ---------------------------------------------------------
    # POPOLAMENTO ALBERO
    # ---------------------------------------------------------
    def populate_tree(self):
        self.tree.clear()
        saved = self.settings.value("selected_layers", [], type=list)

        root = QgsProject.instance().layerTreeRoot()

        def add_group(group, parent_item):
            group_item = QTreeWidgetItem(parent_item, [group.name()])
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsUserCheckable)

            # Icona cartella
            group_item.setIcon(0, QIcon(":/images/themes/default/mIconFolder.svg"))

            for child in group.children():
                if child.nodeType() == 0:  # Gruppo
                    add_group(child, group_item)

                elif child.nodeType() == 1:  # Layer
                    layer = child.layer()
                    if layer in self.polygon_layers:
                        item = QTreeWidgetItem(group_item, [layer.name()])
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.Checked if layer.name() in saved else Qt.Unchecked)
                        item.setData(0, Qt.UserRole, layer.id())

                        # Icona layer poligonale
                        item.setIcon(0, QIcon(":/images/themes/default/mIconPolygonLayer.svg"))

        add_group(root, self.tree)
        self.tree.expandAll()

    # ---------------------------------------------------------
    # FILTRO
    # ---------------------------------------------------------
    def filter_tree(self, text):
        text = text.lower()

        def filter_item(item):
            visible = text in item.text(0).lower()
            for i in range(item.childCount()):
                child_visible = filter_item(item.child(i))
                visible = visible or child_visible
            item.setHidden(not visible)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    # ---------------------------------------------------------
    # RIMOZIONE CHECKBOX DAI GRUPPI
    # ---------------------------------------------------------
    def remove_group_checkboxes(self):
        def clean(item):
            if item.data(0, Qt.UserRole) is None:  # È un gruppo
                item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Unchecked)

            for i in range(item.childCount()):
                clean(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            clean(self.tree.topLevelItem(i))

    # ---------------------------------------------------------
    # PULISCI SELEZIONE
    # ---------------------------------------------------------
    def clear_selection(self):
        def clear_item(item):
            if item.flags() & Qt.ItemIsUserCheckable:
                item.setCheckState(0, Qt.Unchecked)
            for i in range(item.childCount()):
                clear_item(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            clear_item(self.tree.topLevelItem(i))

        self.remove_group_checkboxes()
        self.update_selected_preview()

    # ---------------------------------------------------------
    # PREVIEW LATERALE
    # ---------------------------------------------------------
    def update_selected_preview(self):
        selected = []

        def scan(item):
            if item.flags() & Qt.ItemIsUserCheckable:
                if item.checkState(0) == Qt.Checked:
                    selected.append(item.text(0))
            for i in range(item.childCount()):
                scan(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            scan(self.tree.topLevelItem(i))

        if selected:
            self.preview_panel.setText("\n".join(selected))
        else:
            self.preview_panel.setText("Nessun layer selezionato")

    # ---------------------------------------------------------
    # PANNELLO INFORMATIVO
    # ---------------------------------------------------------
    def update_layer_info(self, item, column):
        # Se è un gruppo → svuota pannello
        if item.data(0, Qt.UserRole) is None:
            self.info_panel.setText("Nessun layer selezionato")
            return

        layer_id = item.data(0, Qt.UserRole)
        layer = QgsProject.instance().mapLayer(layer_id)

        if not layer:
            self.info_panel.setText("Layer non trovato")
            return

        # Informazioni base
        name = layer.name()
        crs = layer.crs().authid()
        provider = layer.dataProvider().name()
        feature_count = layer.featureCount()

        # Warning
        warnings = []
        if feature_count == 0:
            warnings.append("⚠️ Layer vuoto")
        if layer.crs() != QgsProject.instance().crs():
            warnings.append("⚠️ CRS diverso dal progetto")

        warn_text = "\n".join(warnings) if warnings else "Nessun problema rilevato"

        # Aggiorna pannello
        self.info_panel.setText(
            f"Nome: {name}\n"
            f"CRS: {crs}\n"
            f"Feature: {feature_count}\n"
            f"Provider: {provider}\n\n"
            f"{warn_text}"
        )

    # ---------------------------------------------------------
    # RECUPERO LAYER SELEZIONATI
    # ---------------------------------------------------------
    def selected_layers(self):
        selected_ids = []

        def scan(item):
            if item.flags() & Qt.ItemIsUserCheckable:
                if item.checkState(0) == Qt.Checked:
                    selected_ids.append(item.data(0, Qt.UserRole))
            for i in range(item.childCount()):
                scan(item.child(i))

        for i in range(self.tree.topLevelItemCount()):
            scan(self.tree.topLevelItem(i))

        # Salva preferenze
        self.settings.setValue("selected_layers", [
            QgsProject.instance().mapLayer(lid).name()
            for lid in selected_ids
        ])

        return [
            QgsProject.instance().mapLayer(lid)
            for lid in selected_ids
            if QgsProject.instance().mapLayer(lid)
        ]

# ============================================================
#  SCRIPT PRINCIPALE CON BARRA DI AVANZAMENTO
# ============================================================

def esegui_script():
    print("🔄 Avvio script...")

    try:
        # ---------------------------------------------------------
        # BARRA DI AVANZAMENTO
        # ---------------------------------------------------------
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        progress.setValue(0)

        msg = iface.messageBar().createMessage("Intersezioni CDU", "Preparazione in corso…")
        msg.layout().addWidget(progress)
        iface.messageBar().pushWidget(msg, Qgis.Info)

        def update_progress(value, text=None):
            progress.setValue(value)
            if text:
                msg.setText(f"Intersezioni CDU — {text}")
            QApplication.processEvents()


        # ---------------------------------------------------------
        # 1. Recupero layer Particelle
        # ---------------------------------------------------------
        update_progress(5, "Recupero particelle…")

        particelle_layer = QgsProject.instance().mapLayersByName("ParticelleRAS")
        if not particelle_layer:
            iface.messageBar().pushMessage("Errore", "Layer 'ParticelleRAS' non trovato.", level=Qgis.Critical)
            return

        particelle_layer = particelle_layer[0]

        if particelle_layer.selectedFeatureCount() == 0:
            iface.messageBar().pushMessage("Errore", "Seleziona almeno una particella.", level=Qgis.Critical)
            return

        selected_layer = processing.run("native:saveselectedfeatures", {
            'INPUT': particelle_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 2. Recupero TabellaCDU
        # ---------------------------------------------------------
        update_progress(10, "Preparazione tabella…")

        tabellaCDU_layer = QgsProject.instance().mapLayersByName("IntersezioniCATRAS")
        if not tabellaCDU_layer:
            iface.messageBar().pushMessage("Errore", "Layer 'IntersezioniCATRAS' non trovato.", level=Qgis.Critical)
            return

        tabellaCDU_layer = tabellaCDU_layer[0]

        if tabellaCDU_layer.featureCount() > 0:
            msgbox = QMessageBox.question(None, "Tabella non vuota",
                                       "⚠️ La Tabella IntersezioniCATRAS contiene dati.\nVuoi svuotarla?",
                                       QMessageBox.Yes | QMessageBox.No)
            if msgbox == QMessageBox.No:
                return

            tabellaCDU_layer.startEditing()
            tabellaCDU_layer.dataProvider().deleteFeatures([f.id() for f in tabellaCDU_layer.getFeatures()])
            tabellaCDU_layer.commitChanges()


        # ---------------------------------------------------------
        # 3. Finestra di selezione layer
        # ---------------------------------------------------------
        update_progress(15, "Selezione layer…")

        excluded = ["ParticelleRAS", "IntersezioniCATRAS"]

        all_polygon_layers = sorted(
            [
                lyr for lyr in QgsProject.instance().mapLayers().values()
                if hasattr(lyr, "geometryType")
                and lyr.geometryType() == 2
                and lyr.name() not in excluded
            ],
            key=lambda l: l.name().lower()
        )

        dialog = LayerSelectionDialog(all_polygon_layers)
        if dialog.exec_() != QDialog.Accepted:
            iface.messageBar().pushMessage("Operazione annullata", "Nessun layer selezionato", level=Qgis.Info)
            return

        selected_layers = dialog.selected_layers()
        if not selected_layers:
            iface.messageBar().pushMessage("Errore", "Non hai selezionato alcun layer", level=Qgis.Critical)
            return


        # ---------------------------------------------------------
        # 4. VALIDAZIONE LAYER
        # ---------------------------------------------------------
        update_progress(20, "Validazione layer…")

        valid_layers = []
        invalid = []

        for lyr in selected_layers:

            if not lyr.isValid():
                invalid.append(f"{lyr.name()} (non valido)")
                continue

            if lyr.geometryType() != 2:
                invalid.append(f"{lyr.name()} (non poligonale)")
                continue

            if lyr.featureCount() == 0:
                invalid.append(f"{lyr.name()} (vuoto)")
                continue

            valid_layers.append(lyr)

        if invalid:
            iface.messageBar().pushMessage(
                "Attenzione",
                "Layer esclusi: " + ", ".join(invalid),
                level=Qgis.Warning,
                duration=8
            )

        if not valid_layers:
            iface.messageBar().pushMessage("Errore", "Nessun layer valido da intersecare.", level=Qgis.Critical)
            return


        # ---------------------------------------------------------
        # 5. INTERSEZIONI
        # ---------------------------------------------------------
        update_progress(25, "Intersezioni in corso…")

        intersections = []
        layers_ok = []
        layers_error = {}

        total = len(valid_layers)
        current = 0

        for lyr in valid_layers:
            current += 1
            perc = 25 + int((current / total) * 40)  # 25–65%
            update_progress(perc, f"Intersezione con {lyr.name()}…")

            try:
                result = processing.run("native:intersection", {
                    'INPUT': selected_layer,
                    'OVERLAY': lyr,
                    'OUTPUT': 'TEMPORARY_OUTPUT'
                })

                intersections.append(result['OUTPUT'])
                layers_ok.append(lyr.name())

            except Exception as e:
                layers_error[lyr.name()] = str(e)
                continue

        # ---------------------------------------------------------
        # 6. MERGE
        # ---------------------------------------------------------
        update_progress(70, "Merge risultati…")

        merged = processing.run("native:mergevectorlayers", {
            'LAYERS': intersections,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 7. CALCOLO PERCENTUALE
        # ---------------------------------------------------------
        update_progress(80, "Calcolo percentuali…")

        merged.startEditing()

        if "percent" not in merged.fields().names():
            merged.dataProvider().addAttributes([QgsField("percent", QVariant.Int)])
            merged.updateFields()

        for f in merged.getFeatures():
            area = f.geometry().area()
            area1 = f["Area1"] if "Area1" in f.fields().names() else None
            percent = round(area / float(area1) * 100) if area1 else 0
            f["percent"] = percent
            merged.updateFeature(f)

        merged.commitChanges()


        # ---------------------------------------------------------
        # 8. RETAIN FIELDS
        # ---------------------------------------------------------
        update_progress(90, "Pulizia campi…")

        fields_to_keep = ["foglio", "allegato", "mappale", "tema", "zona", "descrizion", "percent", "J_norme"]

        cleaned = processing.run("native:retainfields", {
            'INPUT': merged,
            'FIELDS': fields_to_keep,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 9. COPIA NELLA TABELLA CDU
        # ---------------------------------------------------------
        update_progress(95, "Scrittura risultati…")

        tabellaCDU_layer.startEditing()

        src_fields = cleaned.fields()
        dst_fields = tabellaCDU_layer.fields()

        for f in cleaned.getFeatures():
            new_f = QgsFeature(dst_fields)
            new_f.setGeometry(f.geometry())

            attrs = []
            for dst in dst_fields:
                idx = src_fields.indexOf(dst.name())
                attrs.append(f[idx] if idx != -1 else None)

            new_f.setAttributes(attrs)
            tabellaCDU_layer.addFeature(new_f)

        tabellaCDU_layer.commitChanges()


        # ---------------------------------------------------------
        # 10. CHIUSURA BARRA + MESSAGGIO FINALE
        # ---------------------------------------------------------
        update_progress(100, "Completato!")
        iface.messageBar().clearWidgets()

        iface.messageBar().pushMessage(
            "Intersezioni CDU",
            "Operazione completata con successo!",
            level=Qgis.Success,
            duration=5
        )

        QMessageBox.information(None, "Completato", "Processo completato con successo.")
        iface.showAttributeTable(tabellaCDU_layer)


    except Exception as e:
        iface.messageBar().clearWidgets()
        iface.messageBar().pushMessage("Errore", str(e), level=Qgis.Critical)
        print(f"❌ Errore: {e}")


# ---------------------------------------------------------
# ESECUZIONE
# ---------------------------------------------------------
esegui_script()

