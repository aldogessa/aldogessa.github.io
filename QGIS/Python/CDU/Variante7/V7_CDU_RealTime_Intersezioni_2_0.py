"""
==========================================================================
AGis - Aldo Gessa
SCRIPT – QGIS 3.40.11 (versione GeoPackage)
Interseca le particelle selezionate con i layer poligonali scelti tramite
finestra di dialogo, e inserisce i risultati nella tabella di destinazione.

Versione 2.0:
- Usa il MERGE dei layer tematici in un unico layer
- Esegue UNA sola intersezione particelle × layer unificato
- Mantiene tutti i campi tematici
- Usa SUPCALC dal layer particelle
- Copia il fid particella in FK_CAT
Maggio 2026
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
#  DIALOGO DI SELEZIONE LAYER
# ============================================================

class LayerSelectionDialog(QDialog):
    def __init__(self, polygon_layers, parcel_layers, output_tables, active_layer, parent=None):
        super().__init__(parent)
        
        self.active_layer = active_layer
        self.setWindowTitle("Intersezioni CDU – Selezione layer")
        self.resize(800, 700)

        self.settings = QSettings("AGis", "IntersezioniCDU")
        self.polygon_layers = polygon_layers
        self.parcel_layers = parcel_layers
        self.output_tables = output_tables

        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # ---------------------------------------------------------
        # COLONNA SINISTRA
        # ---------------------------------------------------------
        left_layout = QVBoxLayout()

        # Layer particelle (non modificabile)
        lbl_parcels = QLabel("<b>Layer particelle</b>")
        left_layout.addWidget(lbl_parcels)

        self.cmb_parcels = QComboBox()

        if self.active_layer and self.active_layer in self.parcel_layers:
            self.cmb_parcels.addItem(self.active_layer.name(), self.active_layer.id())
        else:
            for lyr in self.parcel_layers:
                self.cmb_parcels.addItem(lyr.name(), lyr.id())

        self.cmb_parcels.setEnabled(False)
        left_layout.addWidget(self.cmb_parcels)

        # Tabella destinazione
        lbl_output = QLabel("<b>Tabella destinazione</b>")
        left_layout.addWidget(lbl_output)

        self.cmb_output = QComboBox()
        last_output = self.settings.value("last_output_table", None)

        if last_output:
            lyr = QgsProject.instance().mapLayer(last_output)
            if lyr and lyr in self.output_tables:
                self.cmb_output.addItem(f"{lyr.name()} (ultimo usato)", lyr.id())

        for lyr in self.output_tables:
            if lyr.id() != last_output:
                self.cmb_output.addItem(lyr.name(), lyr.id())

        left_layout.addWidget(self.cmb_output)

        # Ricerca layer poligonali
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Cerca layer poligonali...")
        self.search_box.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_box)

        # Espandi/Collassa
        btn_expand = QPushButton("Espandi tutto")
        btn_collapse = QPushButton("Collassa tutto")
        btn_expand.clicked.connect(lambda: self.tree.expandAll())
        btn_collapse.clicked.connect(lambda: self.tree.collapseAll())

        expand_layout = QHBoxLayout()
        expand_layout.addWidget(btn_expand)
        expand_layout.addWidget(btn_collapse)
        left_layout.addLayout(expand_layout)

        # Albero layer
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        left_layout.addWidget(self.tree)

        self.populate_tree()

        # Pulisci selezione
        btn_clear = QPushButton("Pulisci selezione")
        btn_clear.clicked.connect(self.clear_selection)
        left_layout.addWidget(btn_clear)

        # OK / Annulla
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
        # COLONNA DESTRA
        # ---------------------------------------------------------
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 1)

        lbl_sel = QLabel("<b>Layer poligonali selezionati</b>")
        right_layout.addWidget(lbl_sel)

        self.preview_panel = QTextEdit()
        self.preview_panel.setReadOnly(True)
        self.preview_panel.setPlaceholderText("Nessun layer selezionato")
        right_layout.addWidget(self.preview_panel)

        lbl_info = QLabel("<b>Informazioni layer corrente</b>")
        right_layout.addWidget(lbl_info)

        self.info_panel = QTextEdit()
        self.info_panel.setReadOnly(True)
        self.info_panel.setPlaceholderText("Seleziona un layer per vedere le informazioni")
        right_layout.addWidget(self.info_panel)

        self.tree.itemChanged.connect(self.update_selected_preview)
        self.tree.itemClicked.connect(self.update_layer_info)

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
            group_item.setIcon(0, QIcon(":/images/themes/default/mIconFolder.svg"))

            for child in group.children():
                if child.nodeType() == 0:
                    add_group(child, group_item)
                elif child.nodeType() == 1:
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
    # PREVIEW
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
    # INFO LAYER
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
    # LAYER SELEZIONATI
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

    def selected_parcels_layer(self):
        layer_id = self.cmb_parcels.currentData()
        return QgsProject.instance().mapLayer(layer_id)

    def selected_output_table(self):
        layer_id = self.cmb_output.currentData()
        return QgsProject.instance().mapLayer(layer_id)


# ============================================================
#  VALIDAZIONE STRUTTURE
# ============================================================

def validate_parcels_structure(layer):
    """
    Layer particelle (GeoPackage):
    fid (int), FOGLIO (int), ALLEGATO (text), MAPPALE (text), SUPCALC (real)
    """

    fields = layer.fields()
    field_names = [f.name().upper() for f in fields]

    required = ["FID", "FOGLIO", "ALLEGATO", "MAPPALE", "SUPCALC"]

    for name in required:
        if name not in field_names:
            QMessageBox.critical(
                None,
                "Errore struttura particelle",
                f"Il layer particelle non contiene il campo obbligatorio '{name}'."
            )
            return False

    # FOGLIO deve essere intero
    idx_foglio = fields.indexOf("FOGLIO")
    t_foglio = fields[idx_foglio].type()

    if t_foglio not in (QVariant.Int, QVariant.LongLong):
        QMessageBox.critical(
            None,
            "Errore tipo campo",
            "Il campo 'FOGLIO' deve essere un intero (32 o 64 bit)."
        )
        return False

    # SUPCALC deve essere numerico
    idx_sup = fields.indexOf("SUPCALC")
    t_sup = fields[idx_sup].type()

    if t_sup not in (QVariant.Double, QVariant.Int, QVariant.LongLong):
        QMessageBox.critical(
            None,
            "Errore tipo campo",
            "Il campo 'SUPCALC' deve essere numerico."
        )
        return False

    return True


def validate_parcels_population(layer):
    """Controlla che FOGLIO, ALLEGATO, MAPPALE, SUPCALC siano popolati e validi."""

    required = ["FID", "FOGLIO", "ALLEGATO", "MAPPALE", "SUPCALC"]

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

            if name == "SUPCALC":
                try:
                    if float(val) <= 0:
                        QMessageBox.critical(
                            None,
                            "Errore SUPCALC",
                            "Il campo 'SUPCALC' contiene valori non validi (<= 0)."
                        )
                        return False
                except:
                    QMessageBox.critical(
                        None,
                        "Errore SUPCALC",
                        "Il campo 'SUPCALC' deve essere numerico."
                    )
                    return False

    return True


def validate_output_table_structure(layer):
    """
    Tabella destinazione (GeoPackage):
    FOGLIO, ALLEGATO, MAPPALE, TEMA, ZONA, DETTAGLIO, NORME,
    PERCENT, PERCENT_V, FK_CAT,
    IMGZONA, DESCRIZ_A, DESCRIZ_B, DESCRIZ_C,
    LINK_A, DESLINK_A, LINK_B, DESLINK_B, LINK_C, DESLINK_C,
    LINK_D, DESLINK_D, LINK_E, DESLINK_E, LINK_F, DESLINK_F,
    LINK_G, DESLINK_G, VIRTID
    """

    fields = layer.fields()
    field_names = [f.name().upper() for f in fields]

    required = [
        "FOGLIO", "ALLEGATO", "MAPPALE",
        "TEMA", "ZONA", "DETTAGLIO", "NORME",
        "PERCENT", "PERCENT_V", "FK_CAT",
        "IMGZONA", "DESCRIZ_A", "DESCRIZ_B", "DESCRIZ_C",
        "LINK_A", "DESLINK_A", "LINK_B", "DESLINK_B",
        "LINK_C", "DESLINK_C", "LINK_D", "DESLINK_D",
        "LINK_E", "DESLINK_E", "LINK_F", "DESLINK_F",
        "LINK_G", "DESLINK_G", "VIRTID"
    ]

    for name in required:
        if name not in field_names:
            QMessageBox.critical(
                None,
                "Errore struttura tabella",
                f"La tabella '{layer.name()}' non contiene il campo obbligatorio '{name}'."
            )
            return False

    return True

# ============================================================
#  SCRIPT PRINCIPALE
# ============================================================

def esegui_script():
    print("🔄 Avvio script...")

    try:
        # Barra di avanzamento
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
        # 1. RECUPERO LAYER
        # ---------------------------------------------------------
        update_progress(5, "Recupero layer selezionati…")

        polygon_layers = [
            lyr for lyr in QgsProject.instance().mapLayers().values()
            if hasattr(lyr, "geometryType") and lyr.geometryType() == 2
        ]

        parcel_layers = polygon_layers
        output_tables = polygon_layers

        # Identifica il layer _Particelle_ dall'azione
        layer_id = "[% @layer_id %]"
        active_layer = QgsProject.instance().mapLayer(layer_id)

        if not active_layer:
            iface.messageBar().pushMessage(
                "Errore",
                "Impossibile trovare il layer dell'azione nel progetto.",
                level=Qgis.Critical
            )
            return

        dialog = LayerSelectionDialog(polygon_layers, parcel_layers, output_tables, active_layer)

        if dialog.exec_() != QDialog.Accepted:
            iface.messageBar().pushMessage(
                "Operazione annullata",
                "Nessun layer selezionato",
                level=Qgis.Info
            )
            return

        parcels_layer = dialog.selected_parcels_layer()
        output_layer = dialog.selected_output_table()

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
        # 2. VALIDAZIONE PARTICELLE
        # ---------------------------------------------------------
        update_progress(10, "Validazione struttura particelle…")

        if not validate_parcels_structure(parcels_layer):
            return

        if not validate_parcels_population(parcels_layer):
            return

        # ---------------------------------------------------------
        # 3. VALIDAZIONE TABELLA DESTINAZIONE
        # ---------------------------------------------------------
        update_progress(15, "Validazione tabella destinazione…")

        if not validate_output_table_structure(output_layer):
            return

        # ---------------------------------------------------------
        # 3b. TABELLA NON VUOTA
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
        # 4. CONTROLLO PARTICELLE SELEZIONATE
        # ---------------------------------------------------------
        update_progress(20, "Preparazione particelle…")

        if parcels_layer.selectedFeatureCount() == 0:
            iface.messageBar().pushMessage("Errore", "Seleziona almeno una particella.", level=Qgis.Critical)
            return

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
        # 6. MOTORE 2.0 — MERGE + INTERSEZIONE UNICA
        # ---------------------------------------------------------
        update_progress(30, "Unione layer tematici…")

        # MERGE dei layer tematici selezionati
        merged_layer = processing.run("native:mergevectorlayers", {
            'LAYERS': valid_layers,
            'CRS': parcels_layer.crs().authid(),
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

        if not merged_layer:
            iface.messageBar().pushMessage("Errore", "Impossibile creare il layer unificato.", level=Qgis.Critical)
            return

        # ---------------------------------------------------------
        # 7. CREAZIONE LAYER TEMPORANEO DELLE PARTICELLE SELEZIONATE
        # ---------------------------------------------------------
        update_progress(35, "Preparazione particelle selezionate…")

        parcels_sel = processing.run("native:saveselectedfeatures", {
            'INPUT': parcels_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

        if not parcels_sel:
            iface.messageBar().pushMessage("Errore", "Impossibile creare il layer delle particelle selezionate.", level=Qgis.Critical)
            return

        # ---------------------------------------------------------
        # 7b. AGGIUNTA CAMPO FK_SRC (fid originale della particella)
        # ---------------------------------------------------------
        parcels_sel.startEditing()

        # Aggiungo campo FK_SRC
        parcels_sel.dataProvider().addAttributes([QgsField("FK_SRC", QVariant.Int)])
        parcels_sel.updateFields()

        # Trovo campo fid originale
        fid_field = None
        for name in parcels_sel.fields().names():
            if name.lower() == "fid":
                fid_field = name
                break

        if not fid_field:
            iface.messageBar().pushMessage("Errore", "Il layer particelle non contiene il campo fid.", level=Qgis.Critical)
            return

        # Copio fid → FK_SRC
        for f in parcels_sel.getFeatures():
            f["FK_SRC"] = f[fid_field]
            parcels_sel.updateFeature(f)

        parcels_sel.commitChanges()

        # ---------------------------------------------------------
        # 8. INTERSEZIONE UNICA PARTICELLE × LAYER TEMATICI
        # ---------------------------------------------------------
        update_progress(45, "Intersezione unica in corso…")

        inter_layer = processing.run("native:intersection", {
            'INPUT': parcels_sel,
            'OVERLAY': merged_layer,
            'OUTPUT': 'TEMPORARY_OUTPUT'
        })['OUTPUT']

        if not inter_layer:
            iface.messageBar().pushMessage("Errore", "Intersezione fallita.", level=Qgis.Critical)
            return

        # ---------------------------------------------------------
        # 9. CALCOLO PERCENTUALI
        # ---------------------------------------------------------
        update_progress(70, "Calcolo percentuali…")

        inter_layer.startEditing()

        # Trovo campo SUPCALC (può essere SUPCALC o SUPCALC_1)
        supcalc_field = None
        for name in inter_layer.fields().names():
            if name.upper().startswith("SUPCALC"):
                supcalc_field = name
                break

        # Creo campi PERCENT e PERCENT_V se mancanti
        existing = [n.upper() for n in inter_layer.fields().names()]

        if "PERCENT" not in existing:
            inter_layer.dataProvider().addAttributes([QgsField("PERCENT", QVariant.Int)])
        if "PERCENT_V" not in existing:
            inter_layer.dataProvider().addAttributes([QgsField("PERCENT_V", QVariant.String)])

        inter_layer.updateFields()

        # Calcolo percentuali
        for f in inter_layer.getFeatures():
            area = f.geometry().area()

            if supcalc_field:
                raw = f[supcalc_field]
                try:
                    sup = float(str(raw).replace(",", "."))
                    percent = round(area / sup * 100) if sup > 0 else 0
                except:
                    percent = 0
            else:
                percent = 0

            f["PERCENT"] = percent
            f["PERCENT_V"] = "<1" if percent == 0 else str(percent)
            inter_layer.updateFeature(f)

        inter_layer.commitChanges()

        # ---------------------------------------------------------
        # 10. SCRITTURA NELLA TABELLA DESTINAZIONE
        # ---------------------------------------------------------
        update_progress(90, "Scrittura risultati nella tabella…")

        output_layer.startEditing()

        src_fields = inter_layer.fields()
        dst_fields = output_layer.fields()

        # Mappa sorgente (upper → index)
        src_map = {name.upper(): i for i, name in enumerate(src_fields.names())}

        # Campo FK_SRC (fid particella originale)
        fk_src_field = "FK_SRC"

        for f in inter_layer.getFeatures():
            new_f = QgsFeature(dst_fields)
            new_f.setGeometry(f.geometry())

            attrs = []
            for dst in dst_fields:
                dst_upper = dst.name().upper()

                # Mai scrivere nel FID della tabella destinazione
                if dst_upper == "FID":
                    attrs.append(None)
                    continue

                # FK_CAT = fid particella originale
                if dst_upper == "FK_CAT":
                    attrs.append(f[fk_src_field])
                    continue

                # Copia normale case-insensitive
                if dst_upper in src_map:
                    attrs.append(f[src_map[dst_upper]])
                else:
                    attrs.append(None)

            new_f.setAttributes(attrs)
            output_layer.addFeature(new_f)

        # ---------------------------------------------------------
        # 11. COMMIT FINALE
        # ---------------------------------------------------------
        update_progress(97, "Finalizzazione…")

        if not output_layer.commitChanges():
            iface.messageBar().pushMessage(
                "Errore",
                "Impossibile salvare i risultati nella tabella destinazione.",
                level=Qgis.Critical
            )
            return

        output_layer.updateExtents()
        output_layer.triggerRepaint()

        # ---------------------------------------------------------
        # 12. COMPLETAMENTO
        # ---------------------------------------------------------
        update_progress(100, "Completato")

        iface.messageBar().pushMessage(
            "Intersezioni CDU",
            "Operazione completata con successo.",
            level=Qgis.Success,
            duration=6
        )

        print("✅ Script completato.")

    except Exception as e:
        iface.messageBar().pushMessage(
            "Errore critico",
            f"Si è verificato un errore: {str(e)}",
            level=Qgis.Critical,
            duration=10
        )
        print(f"❌ Errore critico: {e}")


# ============================================================
#  AVVIO SCRIPT (per uso come Azione o da Console Python)
# ============================================================

esegui_script()
