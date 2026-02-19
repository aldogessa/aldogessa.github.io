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
    QApplication,
    QComboBox
)

# ============================================================
#  DIALOGO DI SELEZIONE LAYER (PARTICELLE + TABELLA + POLIGONALI)
# ============================================================

class LayerSelectionDialog(QDialog):
    def __init__(self, polygon_layers, parcel_layers, output_tables, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Intersezioni CDU – Selezione layer")
        self.resize(800, 700)

        self.settings = QSettings("AGis", "IntersezioniCDU")
        self.polygon_layers = polygon_layers
        self.parcel_layers = parcel_layers
        self.output_tables = output_tables

        # --- Layout principale orizzontale ---
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # ---------------------------------------------------------
        # COLONNA SINISTRA (combo + albero + pulsanti)
        # ---------------------------------------------------------
        left_layout = QVBoxLayout()

        # ------------------
        # Combo layer particelle
        # ------------------
        lbl_parcels = QLabel("<b>Layer particelle</b>")
        left_layout.addWidget(lbl_parcels)

        self.cmb_parcels = QComboBox()

        last_parcels = self.settings.value("last_parcels_layer", None)

        # Prima aggiungiamo il layer salvato (se esiste ancora)
        if last_parcels:
            lyr = QgsProject.instance().mapLayer(last_parcels)
            if lyr and lyr in self.parcel_layers:
                self.cmb_parcels.addItem(f"{lyr.name()} (ultimo usato)", lyr.id())

        # Poi aggiungiamo tutti gli altri
        for lyr in self.parcel_layers:
            if lyr.id() != last_parcels:
                self.cmb_parcels.addItem(lyr.name(), lyr.id())

        left_layout.addWidget(self.cmb_parcels)

        # ------------------
        # Combo tabella destinazione
        # ------------------
        lbl_output = QLabel("<b>Tabella destinazione</b>")
        left_layout.addWidget(lbl_output)

        self.cmb_output = QComboBox()

        last_output = self.settings.value("last_output_table", None)

        # Prima il layer salvato
        if last_output:
            lyr = QgsProject.instance().mapLayer(last_output)
            if lyr and lyr in self.output_tables:
                self.cmb_output.addItem(f"{lyr.name()} (ultimo usato)", lyr.id())

        # Poi gli altri
        for lyr in self.output_tables:
            if lyr.id() != last_output:
                self.cmb_output.addItem(lyr.name(), lyr.id())

        left_layout.addWidget(self.cmb_output)

        # ------------------
        # Barra di ricerca
        # ------------------
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca layer poligonali...")
        self.search_box.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_box)

        # ------------------
        # Pulsanti espandi/collassa
        # ------------------
        btn_expand = QPushButton("Espandi tutto")
        btn_collapse = QPushButton("Collassa tutto")
        btn_expand.clicked.connect(lambda: self.tree.expandAll())
        btn_collapse.clicked.connect(lambda: self.tree.collapseAll())

        expand_layout = QHBoxLayout()
        expand_layout.addWidget(btn_expand)
        expand_layout.addWidget(btn_collapse)
        left_layout.addLayout(expand_layout)

        # ------------------
        # Albero layer poligonali
        # ------------------
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        self.populate_tree()

        # ------------------
        # Pulsante pulisci selezione
        # ------------------
        btn_clear = QPushButton("Pulisci selezione")
        btn_clear.clicked.connect(self.clear_selection)
        left_layout.addWidget(btn_clear)

        # ------------------
        # Pulsanti OK / Annulla
        # ------------------
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Annulla")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        left_layout.addLayout(btn_layout)

        main_layout.addLayout(left_layout, 2)

        # ---------------------------------------------------------
        # COLONNA DESTRA (preview + info)
        # ---------------------------------------------------------
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        # Titolo pannello selezionati
        lbl_sel = QLabel("<b>Layer poligonali selezionati</b>")
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
    # POPOLAMENTO ALBERO POLIGONALI
    # ---------------------------------------------------------
    def populate_tree(self):
        self.tree.clear()
        saved = self.settings.value("selected_layers", [], type=list)

        root = QgsProject.instance().layerTreeRoot()

        def add_group(group, parent_item):
            group_item = QTreeWidgetItem(parent_item, [group.name()])
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsUserCheckable)
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
                        item.setIcon(0, QIcon(":/images/themes/default/mIconPolygonLayer.svg"))

        add_group(root, self.tree)
        self.tree.expandAll()


    # ---------------------------------------------------------
    # FILTRO ALBERO
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

        self.preview_panel.setText("\n".join(selected) if selected else "Nessun layer selezionato")


    # ---------------------------------------------------------
    # INFO LAYER CORRENTE
    # ---------------------------------------------------------
    def update_layer_info(self, item, column):
        if item.data(0, Qt.UserRole) is None:
            self.info_panel.setText("Nessun layer selezionato")
            return

        layer_id = item.data(0, Qt.UserRole)
        layer = QgsProject.instance().mapLayer(layer_id)

        if not layer:
            self.info_panel.setText("Layer non trovato")
            return

        name = layer.name()
        crs = layer.crs().authid()
        provider = layer.dataProvider().name()
        feature_count = layer.featureCount()

        warnings = []
        if feature_count == 0:
            warnings.append("⚠️ Layer vuoto")
        if layer.crs() != QgsProject.instance().crs():
            warnings.append("⚠️ CRS diverso dal progetto")

        warn_text = "\n".join(warnings) if warnings else "Nessun problema rilevato"

        self.info_panel.setText(
            f"Nome: {name}\n"
            f"CRS: {crs}\n"
            f"Feature: {feature_count}\n"
            f"Provider: {provider}\n\n"
            f"{warn_text}"
        )


    # ---------------------------------------------------------
    # RECUPERO LAYER POLIGONALI SELEZIONATI
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

        self.settings.setValue("selected_layers", [
            QgsProject.instance().mapLayer(lid).name()
            for lid in selected_ids
        ])

        return [
            QgsProject.instance().mapLayer(lid)
            for lid in selected_ids
            if QgsProject.instance().mapLayer(lid)
        ]


    # ---------------------------------------------------------
    # RECUPERO LAYER PARTICELLE
    # ---------------------------------------------------------
    def selected_parcels_layer(self):
        layer_id = self.cmb_parcels.currentData()
        return QgsProject.instance().mapLayer(layer_id)


    # ---------------------------------------------------------
    # RECUPERO TABELLA DESTINAZIONE
    # ---------------------------------------------------------
    def selected_output_table(self):
        layer_id = self.cmb_output.currentData()
        return QgsProject.instance().mapLayer(layer_id)

# ============================================================
#  VALIDAZIONE STRUTTURE LAYER
# ============================================================

def validate_parcels_structure(layer):
    """Controlla che il layer particelle abbia i campi obbligatori,
       e che 'foglio' sia un intero (32 o 64 bit).
    """

    fields = layer.fields()
    field_names = [f.name().lower() for f in fields]

    # Campi obbligatori
    required = ["foglio", "allegato", "mappale", "area1"]

    # Controllo presenza campi
    for name in required:
        if name not in field_names:
            QMessageBox.critical(
                None,
                "Errore struttura particelle",
                f"Il layer particelle non contiene il campo obbligatorio '{name}'."
            )
            return False

    # --- Controllo Area1: deve essere numerico ---
    idx_area = fields.indexOf("Area1")
    t_area = fields[idx_area].type()

    if t_area not in (QVariant.Double, QVariant.Int, QVariant.LongLong):
        QMessageBox.critical(
            None,
            "Errore tipo campo",
            "Il campo 'Area1' deve essere numerico."
        )
        return False

    # --- Controllo foglio: deve essere INT32 o INT64 ---
    idx_foglio = fields.indexOf("foglio")
    t_foglio = fields[idx_foglio].type()

    if t_foglio not in (QVariant.Int, QVariant.LongLong):
        QMessageBox.critical(
            None,
            "Errore tipo campo",
            "Il campo 'foglio' deve essere un intero (32 o 64 bit)."
        )
        return False

    return True



def validate_parcels_population(layer):
    """Controlla che i campi obbligatori siano popolati e validi."""

    required = ["foglio", "allegato", "mappale", "Area1"]

    for f in layer.getFeatures():
        for name in required:
            val = f[name]

            if val is None or val == "":
                QMessageBox.critical(
                    None,
                    "Errore dati particelle",
                    f"Il campo '{name}' contiene valori nulli o vuoti."
                )
                return False

            if name.lower() == "area1":
                try:
                    if float(val) <= 0:
                        QMessageBox.critical(
                            None,
                            "Errore Area1",
                            "Il campo 'Area1' contiene valori non validi (<= 0)."
                        )
                        return False
                except:
                    QMessageBox.critical(
                        None,
                        "Errore Area1",
                        "Il campo 'Area1' deve essere numerico."
                    )
                    return False

    return True



def validate_output_table_structure(layer):
    """Controlla che la tabella destinazione abbia i campi richiesti,
       indipendentemente dall'ordine, e con tipi flessibili dove necessario.
    """

    fields = layer.fields()
    field_names = [f.name() for f in fields]

    # Campi richiesti e tipi accettati
    required = {
        "foglio": (QVariant.Int, QVariant.LongLong),   # int32 o int64
        "allegato": (QVariant.String,),
        "mappale": (QVariant.String,),
        "tema": (QVariant.String,),
        "zona": (QVariant.String,),
        "descrizion": (QVariant.String,),
        "J_norme": (QVariant.String,),
        "percent": (QVariant.Int, QVariant.LongLong)   # percent può essere int32 o int64
    }

    # Controllo presenza campi
    for name in required.keys():
        if name not in field_names:
            QMessageBox.critical(
                None,
                "Errore struttura tabella",
                f"La tabella '{layer.name()}' non contiene il campo obbligatorio '{name}'."
            )
            return False

    # Controllo tipo campi
    for name, accepted_types in required.items():
        idx = fields.indexOf(name)
        field_type = fields[idx].type()

        if field_type not in accepted_types:
            QMessageBox.critical(
                None,
                "Errore tipo campo",
                f"Il campo '{name}' deve essere di tipo {accepted_types}, trovato {field_type}."
            )
            return False

    return True



# ============================================================
#  SCRIPT PRINCIPALE CON BARRA DI AVANZAMENTO
# ============================================================

def esegui_script():
    print("🔄 Avvio script...")

    try:
        # ---------------------------------------------------------
        # PREPARAZIONE BARRA DI AVANZAMENTO
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
        # 1. RECUPERO LAYER DA DIALOGO
        # ---------------------------------------------------------
        update_progress(5, "Recupero layer selezionati…")

        # Recupero layer poligonali
        polygon_layers = [
            lyr for lyr in QgsProject.instance().mapLayers().values()
            if hasattr(lyr, "geometryType") and lyr.geometryType() == 2
        ]

        # Recupero layer candidati particelle (poligonali)
        parcel_layers = polygon_layers

        # Recupero tabelle destinazione (layer poligonali)
        output_tables = [
            lyr for lyr in QgsProject.instance().mapLayers().values()
            if hasattr(lyr, "geometryType") and lyr.geometryType() == 2
]



        dialog = LayerSelectionDialog(polygon_layers, parcel_layers, output_tables)

        if dialog.exec_() != QDialog.Accepted:
            iface.messageBar().pushMessage("Operazione annullata", "Nessun layer selezionato", level=Qgis.Info)
            return

        parcels_layer = dialog.selected_parcels_layer()
        output_layer = dialog.selected_output_table()
        # Salva le scelte dell’utente
        dialog.settings.setValue("last_parcels_layer", parcels_layer.id())
        dialog.settings.setValue("last_output_table", output_layer.id())

        selected_layers = dialog.selected_layers()

        if not parcels_layer:
            iface.messageBar().pushMessage("Errore", "Nessun layer particelle selezionato.", level=Qgis.Critical)
            return

        if not output_layer:
            iface.messageBar().pushMessage("Errore", "Nessuna tabella destinazione selezionata.", level=Qgis.Critical)
            return

        if not selected_layers:
            iface.messageBar().pushMessage("Errore", "Nessun layer poligonale selezionato.", level=Qgis.Critical)
            return


        # ---------------------------------------------------------
        # 2. VALIDAZIONE STRUTTURA PARTICELLE
        # ---------------------------------------------------------
        update_progress(10, "Validazione struttura particelle…")

        if not validate_parcels_structure(parcels_layer):
            return

        if not validate_parcels_population(parcels_layer):
            return


        # ---------------------------------------------------------
        # 3. VALIDAZIONE STRUTTURA TABELLA DESTINAZIONE
        # ---------------------------------------------------------
        update_progress(15, "Validazione tabella destinazione…")

        if not validate_output_table_structure(output_layer):
            return


        # ---------------------------------------------------------
        # 3b. CONTROLLO SE LA TABELLA DESTINAZIONE È POPOLATA
        # ---------------------------------------------------------
        if output_layer.featureCount() > 0:

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Question)
            msg_box.setWindowTitle("Tabella destinazione non vuota")
            msg_box.setText(
                f"La tabella '{output_layer.name()}' contiene già {output_layer.featureCount()} record."
            )
            msg_box.setInformativeText("Vuoi svuotarla prima di inserire i nuovi risultati?")
            btn_clear = msg_box.addButton("Svuota", QMessageBox.DestructiveRole)
            btn_append = msg_box.addButton("Aggiungi", QMessageBox.AcceptRole)
            btn_cancel = msg_box.addButton("Annulla", QMessageBox.RejectRole)

            msg_box.exec_()

            if msg_box.clickedButton() == btn_cancel:
                update_progress(15, "Operazione annullata dall'utente")
                return

            elif msg_box.clickedButton() == btn_clear:
                output_layer.startEditing()
                ids = [f.id() for f in output_layer.getFeatures()]
                output_layer.deleteFeatures(ids)
                output_layer.commitChanges()
                update_progress(17, "Tabella destinazione svuotata")

            else:
                update_progress(17, "Aggiunta dei nuovi risultati alla tabella esistente")



        # ---------------------------------------------------------
        # 4. SALVATAGGIO PARTICELLE SELEZIONATE
        # ---------------------------------------------------------
        update_progress(20, "Preparazione particelle…")

        if parcels_layer.selectedFeatureCount() == 0:
            iface.messageBar().pushMessage("Errore", "Seleziona almeno una particella.", level=Qgis.Critical)
            return

        selected_layer = processing.run("native:saveselectedfeatures", {
            'INPUT': parcels_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 5. VALIDAZIONE LAYER POLIGONALI
        # ---------------------------------------------------------
        update_progress(25, "Validazione layer poligonali…")

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
        # 6. INTERSEZIONI (continua in BLOCCO 3)
        # ---------------------------------------------------------
        update_progress(30, "Intersezioni in corso…")

        # ---------------------------------------------------------
        # 6. INTERSEZIONI
        # ---------------------------------------------------------
        update_progress(30, "Intersezioni in corso…")

        intersections = []
        layers_ok = []
        layers_error = {}

        total = len(valid_layers)
        current = 0

        for lyr in valid_layers:
            current += 1
            perc = 30 + int((current / total) * 40)  # 30–70%
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
        # 7. MERGE RISULTATI
        # ---------------------------------------------------------
        update_progress(75, "Merge risultati…")

        merged = processing.run("native:mergevectorlayers", {
            'LAYERS': intersections,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 8. CALCOLO PERCENTUALI
        # ---------------------------------------------------------
        update_progress(85, "Calcolo percentuali…")

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
        # 9. RETAIN FIELDS
        # ---------------------------------------------------------
        update_progress(90, "Pulizia campi…")

        fields_to_keep = ["foglio", "allegato", "mappale", "tema", "zona", "descrizion", "percent", "J_norme"]

        cleaned = processing.run("native:retainfields", {
            'INPUT': merged,
            'FIELDS': fields_to_keep,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']


        # ---------------------------------------------------------
        # 10. COPIA NELLA TABELLA DESTINAZIONE
        # ---------------------------------------------------------
        update_progress(95, "Scrittura risultati…")

        output_layer.startEditing()

        src_fields = cleaned.fields()
        dst_fields = output_layer.fields()

        for f in cleaned.getFeatures():
            new_f = QgsFeature(dst_fields)
            new_f.setGeometry(f.geometry())

            attrs = []
            for dst in dst_fields:
                idx = src_fields.indexOf(dst.name())
                attrs.append(f[idx] if idx != -1 else None)

            new_f.setAttributes(attrs)
            output_layer.addFeature(new_f)

        output_layer.commitChanges()


        # ---------------------------------------------------------
        # 11. CHIUSURA BARRA + MESSAGGIO FINALE
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
        iface.showAttributeTable(output_layer)


    except Exception as e:
        iface.messageBar().clearWidgets()
        iface.messageBar().pushMessage("Errore", str(e), level=Qgis.Critical)
        print(f"❌ Errore: {e}")


# ---------------------------------------------------------
# ESECUZIONE
# ---------------------------------------------------------
esegui_script()


