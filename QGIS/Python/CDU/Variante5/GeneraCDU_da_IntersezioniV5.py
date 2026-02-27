"""
===================================================================================
VERSIONE MIGLIORATA – QGIS 3.40
Generazione CDU da layer intersezioni, con:
✔ riconoscimento automatico del layer dell’azione (via @layer_id)
✔ finestra di dialogo per selezionare il template .docx
✔ memoria persistente del template
===================================================================================
"""

from qgis.PyQt.QtWidgets import (
    QFileDialog, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton
)
from qgis.PyQt.QtCore import QSettings
from qgis.utils import iface
from qgis.core import QgsProject

from docx import Document
from docx.shared import Pt
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

import os
import platform


# ============================================================
#  FINESTRA DI DIALOGO PER LA SCELTA DEL TEMPLATE
# ============================================================

class TemplateSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Seleziona template CDU")
        self.resize(500, 120)

        self.settings = QSettings("AGis", "CDUGenerator")

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Campo percorso template
        self.txt_path = QLineEdit()
        saved = self.settings.value("template_path", "")
        if saved:
            self.txt_path.setText(saved)

        layout.addWidget(QLabel("<b>Template CDU (.docx)</b>"))
        layout.addWidget(self.txt_path)

        # Pulsante per sfogliare
        btn_browse = QPushButton("Sfoglia…")
        btn_browse.clicked.connect(self.browse_template)

        # Pulsanti OK / Annulla
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Annulla")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        h = QHBoxLayout()
        h.addWidget(btn_browse)
        h.addStretch()
        h.addWidget(btn_ok)
        h.addWidget(btn_cancel)

        layout.addLayout(h)

    def browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleziona il template CDU (.docx)",
            "",
            "Documenti Word (*.docx)"
        )
        if path:
            self.txt_path.setText(path)

    def selected_template(self):
        """Restituisce il percorso scelto e lo salva."""
        path = self.txt_path.text().strip()
        if path:
            self.settings.setValue("template_path", path)
        return path


# ============================================================
#  FUNZIONE PRINCIPALE
# ============================================================

def export_selected_data_to_existing_table():
    try:
        # ---------------------------------------------------------
        # 1) RECUPERO SICURO DEL LAYER DELL’AZIONE (NON activeLayer)
        # ---------------------------------------------------------
        layer_id = "[% @layer_id %]"   # QGIS sostituisce automaticamente l’ID
        layer = QgsProject.instance().mapLayer(layer_id)

        if not layer:
            iface.messageBar().pushMessage("Errore", "Impossibile identificare il layer dell'azione.", level=3)
            return

        if layer.selectedFeatureCount() == 0:
            iface.messageBar().pushMessage("Avviso", "Nessun record selezionato!", level=2)
            return

        selected_features = layer.selectedFeatures()

        # ---------------------------------------------------------
        # 2) FINESTRA DI DIALOGO PER IL TEMPLATE
        # ---------------------------------------------------------
        dlg = TemplateSelectorDialog()

        if dlg.exec_() != QDialog.Accepted:
            iface.messageBar().pushMessage("Operazione annullata", "Nessun template selezionato.", level=1)
            return

        template_path = dlg.selected_template()

        if not template_path or not os.path.exists(template_path):
            iface.messageBar().pushMessage("Errore", "Template non valido o inesistente.", level=3)
            return

        # ---------------------------------------------------------
        # 3) SCELTA DEL FILE DI OUTPUT
        # ---------------------------------------------------------
        output_file_path, _ = QFileDialog.getSaveFileName(
            None,
            "Scegli dove salvare il documento",
            "",
            "Documenti Word (*.docx)"
        )

        if not output_file_path:
            iface.messageBar().pushMessage("Informazione", "Operazione annullata dall'utente.", level=1)
            return

        # ---------------------------------------------------------
        # 4) CARICAMENTO TEMPLATE
        # ---------------------------------------------------------
        doc = Document(template_path)

        if not doc.tables:
            iface.messageBar().pushMessage("Errore", "Nessuna tabella trovata nel documento!", level=3)
            return

        table = doc.tables[0]

        # ---------------------------------------------------------
        # 5) ORDINAMENTO FEATURE
        # ---------------------------------------------------------
        sorted_features = sorted(
            selected_features,
            key=lambda f: (int(f["foglio"]), f["mappale"], f["tema"], f["zona"], f["percent"])
        )

        # ---------------------------------------------------------
        # 6) INTESTAZIONE TABELLA
        # ---------------------------------------------------------
        header_cells = table.rows[0].cells
        headers = ["Fg.", "All.", "Map.", "Tema", "Zona", "Dettaglio", "Norme Specifiche", "Q.tà* %"]

        for i, header in enumerate(headers):
            header_cells[i].text = header
            for paragraph in header_cells[i].paragraphs:
                run = paragraph.runs[0]
                run.bold = True
                run.font.name = "Calibri Light"
                run.font.size = Pt(10)

            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="D3D3D3"/>')
            header_cells[i]._element.get_or_add_tcPr().append(shading)
            header_cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        # ---------------------------------------------------------
        # 7) POPOLAMENTO TABELLA
        # ---------------------------------------------------------
        for feature in sorted_features:
            row = table.add_row()
            row.cells[0].text = str(int(feature["foglio"]))
            row.cells[1].text = str(feature["allegato"])
            row.cells[2].text = str(feature["mappale"])
            row.cells[3].text = str(feature["tema"])
            row.cells[4].text = str(feature["zona"])
            row.cells[5].text = str(feature["descrizion"])
            row.cells[6].text = str(feature["J_norme"])
            row.cells[7].text = str(feature["percent"])

            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    run = paragraph.runs[0]
                    run.font.name = "Calibri Light"
                    run.font.size = Pt(10)
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

        # ---------------------------------------------------------
        # 8) SALVATAGGIO FILE
        # ---------------------------------------------------------
        doc.save(output_file_path)

        iface.messageBar().pushMessage(
            "Informazione",
            f'Documento salvato con successo: <a href="{output_file_path}">{output_file_path}</a>',
            level=0
        )

        # Apertura automatica
        if platform.system() == "Windows":
            os.startfile(output_file_path)
        elif platform.system() == "Darwin":
            os.system(f"open '{output_file_path}'")
        elif platform.system() == "Linux":
            os.system(f"xdg-open '{output_file_path}'")

    except Exception as e:
        iface.messageBar().pushMessage("Errore", f"Errore durante l'esportazione: {e}", level=3)


# ---------------------------------------------------------
# ESECUZIONE
# ---------------------------------------------------------
export_selected_data_to_existing_table()
