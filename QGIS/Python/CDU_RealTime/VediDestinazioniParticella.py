# -*- coding: utf-8 -*-

from qgis.PyQt.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QApplication,
    QFrame
)

from qgis.PyQt.QtCore import (
    QVariant,
    QUrl,
    Qt
)

from qgis.PyQt.QtGui import QPixmap

from qgis.PyQt.QtNetwork import (
    QNetworkAccessManager,
    QNetworkRequest
)

from qgis.core import (
    QgsProject,
    QgsFeature,
    QgsField,
    QgsVectorLayer,
    QgsWkbTypes
)

import processing
import re


# ============================================================
# DATI DELLA FEATURE CLICCATA
# ============================================================

fid_val = "[% "fid" %]"
foglio_val = "[% "FOGLIO" %]"
allegato_val = "[% "ALLEGATO" %]"
mappale_val = "[% "MAPPALE" %]"

layer_id = "[% @layer_id %]"

project = QgsProject.instance()


# ============================================================
# CONTROLLI INIZIALI
# ============================================================

parcels_layer = project.mapLayer(layer_id)

if not parcels_layer:

    QMessageBox.critical(
        None,
        "CDU particella",
        "Impossibile individuare il layer della particella."
    )

    raise Exception("Layer particelle non trovato")


# ============================================================
# CERCA IL CAMPO FID
# ============================================================

fid_field = next(
    (
        name
        for name in parcels_layer.fields().names()
        if name.lower() == "fid"
    ),
    None
)


if not fid_field:

    QMessageBox.critical(
        None,
        "CDU particella",
        "Nel layer delle particelle non è presente "
        "il campo 'fid'."
    )

    raise Exception("Campo fid non trovato")


# ============================================================
# CERCA LA FEATURE CLICCATA
# ============================================================

clicked_feature = None


for feature in parcels_layer.getFeatures():

    value = feature[fid_field]

    if str(value).strip() == str(fid_val).strip():

        clicked_feature = feature
        break


if clicked_feature is None:

    QMessageBox.critical(
        None,
        "CDU particella",
        "La particella cliccata non è stata trovata "
        "nel layer."
    )

    raise Exception("Feature non trovata")


# ============================================================
# LAYER TEMATICI CONFIGURATI TRAMITE ID QGIS
# ============================================================

THEMATIC_IDS = [
    "T010101_ZONIZZAZIONE_VIGENTE_ab1d7544_a791_4094_bd62_1b5c79ce0698",
    "T020201_FASCE_ART_30TER_676e6ed8_2690_4c6d_a24e_3847b3482828",
    "T020301_PERICOLOSITA_IDRAULICA_VIGENTE_967d343d_9e5e_49d2_8d7a_fc68648c1862",
    "T020401_PERICOLO_FRANA_VIGENTE_c0c02102_add4_469a_ad5b_d13dbf51d4ad",
    "T020501_RISCHIO_IDRAULICO_5571db8d_84b9_474c_97d7_e8aaadaf9be1",
    "T020601_RISCHIO_FRANA_7bc80673_0b24_4569_95f6_267b280ae0b0",
    "T030101_AREE_INCENDIATE_8fa9b765_b58e_4220_ad98_faaebdabd4dc",
    "T040201_FASCIA_150MT_ACQUE_PUBBLICHE_0cea6c1d_d63e_49a2_902f_14a816be7df4",
    "T040301_LAGHI_a0a1f85b_4ff9_4107_8b9c_90b15928dd7c",
    "T040401_FASCIA_300MT_LAGHI_db3adaa1_836e_4dff_ae81_6342f13bc6d7",
    "T040501_USI_CIVICI_70c71919_4270_4aa5_8726_bc35f084ea90",
    "T050301_FASCIA_150MT_FIUMI_MAPPATI_b3ac42f7_e965_4ce8_9216_22804c6bd958",
    "T050401_LAGHI_STAGNI_10630cba_75ae_47f2_aac5_8bb50dfb9024",
    "T050501_FASCIA_300MT_LAGHI_STAGNI_7a144963_50d9_4cf5_a24b_50991b7aec8a",
    "T050601_AREE_BOSCATE_6307084e_7064_48e6_8a7d_49fbb378e6d3",
    "T050701_CENTRO_MATRICE_87559ab8_96f7_4b34_a768_ac21b2891a37",
    "T050901_FASCIA_RISP_IMM_TIP_29722617_89ec_4b81_95b8_cea8bca7cb18",
    "T051001_AREE_GEST_ENTE_FORESTE_59af63e1_c566_434e_9a6b_966e8733fb9e",
    "T051101_AREE_DEGRADATE_SCAVI_6e9a996c_9a86_487d_b69b_f87b75751e98",
    "T051301_ASSETTO_INSEDIATIVO_34c3010b_aa57_4a3d_8d56_484407639d2d",
    "T051401_ASSETTO_AMBIENTALE_f443cd16_a46b_4b58_8a22_d2933f20a737",
    "TestZ_aab538fd_a10d_44c5_a9a9_07a1fdbb1817"
]

selected_layers = []


for layer_id in THEMATIC_IDS:

    layer = project.mapLayer(layer_id)

    if not layer:

        QMessageBox.critical(
            None,
            "CDU particella",
            "Layer tematico non trovato.\n\n"
            "ID layer:\n" + layer_id
        )

        raise Exception(
            "Layer tematico non trovato: " + layer_id
        )

    selected_layers.append(layer)


# ============================================================
# CREA LAYER TEMPORANEO CON LA SOLA PARTICELLA CLICCATA
# ============================================================

geom_string = QgsWkbTypes.displayString(
    parcels_layer.wkbType()
)

temp_uri = (
    geom_string
    + "?crs="
    + parcels_layer.crs().authid()
)

single_parcel = QgsVectorLayer(
    temp_uri,
    "Particella CDU",
    "memory"
)


if not single_parcel.isValid():

    QMessageBox.critical(
        None,
        "CDU particella",
        "Impossibile creare il layer temporaneo "
        "della particella."
    )

    raise Exception(
        "Layer temporaneo non valido"
    )


single_parcel.dataProvider().addAttributes(
    parcels_layer.fields()
)

single_parcel.dataProvider().addAttributes([
    QgsField("FK_SRC", QVariant.Int)
])

single_parcel.updateFields()


new_feature = QgsFeature(
    single_parcel.fields()
)

new_feature.setGeometry(
    clicked_feature.geometry()
)

attributes = []


for field in single_parcel.fields():

    field_name = field.name()

    if field_name == "FK_SRC":

        try:
            attributes.append(
                int(fid_val)
            )

        except:
            attributes.append(None)

    else:

        if field_name in parcels_layer.fields().names():

            attributes.append(
                clicked_feature[field_name]
            )

        else:

            attributes.append(None)


new_feature.setAttributes(
    attributes
)

single_parcel.dataProvider().addFeature(
    new_feature
)

single_parcel.updateExtents()


# ============================================================
# NORMALIZZAZIONE TEMATICA
# ELIMINAZIONE TEMPORANEA DI Z / M
#
# I layer originali nella TOC NON vengono modificati.
#
# I layer già 2D vengono utilizzati direttamente.
#
# I layer con Z o M vengono elaborati con:
#
# native:dropmzvalues
#
# ottenendo una copia temporanea 2D.
# ============================================================

normalized_layers = []


for thematic_layer in selected_layers:

    wkb_type = thematic_layer.wkbType()

    has_z = QgsWkbTypes.hasZ(
        wkb_type
    )

    has_m = QgsWkbTypes.hasM(
        wkb_type
    )


    # --------------------------------------------------------
    # LAYER GIÀ 2D
    # --------------------------------------------------------

    if not has_z and not has_m:

        normalized_layers.append(
            thematic_layer
        )

        continue


    # --------------------------------------------------------
    # LAYER CON Z/M
    #
    # Creazione di una copia temporanea 2D.
    # Il layer originale non viene modificato.
    # --------------------------------------------------------

    try:

        result = processing.run(
            "native:dropmzvalues",
            {
                "INPUT": thematic_layer,
                "DROP_M_VALUES": True,
                "DROP_Z_VALUES": True,
                "OUTPUT": "TEMPORARY_OUTPUT"
            }
        )


        normalized_layer = result["OUTPUT"]


        if not normalized_layer:

            raise Exception(
                "L'algoritmo non ha restituito un layer."
            )


        # ----------------------------------------------------
        # CONTROLLO DI SICUREZZA
        #
        # Il risultato deve essere realmente 2D.
        # ----------------------------------------------------

        normalized_wkb = normalized_layer.wkbType()


        if (
            QgsWkbTypes.hasZ(
                normalized_wkb
            )
            or
            QgsWkbTypes.hasM(
                normalized_wkb
            )
        ):

            raise Exception(
                "Il layer risultante contiene ancora "
                "Z o M."
            )


        normalized_layers.append(
            normalized_layer
        )


    except Exception as e:

        QMessageBox.critical(
            None,
            "CDU particella",
            "Errore durante l'eliminazione "
            "dei valori Z/M dal layer:\n\n"
            + thematic_layer.name()
            + "\n\n"
            + str(e)
        )

        raise


# ============================================================
# MERGE DEI LAYER TEMATICI NORMALIZZATI
# ============================================================

try:

    merged = processing.run(
        "native:mergevectorlayers",
        {
            "LAYERS": normalized_layers,
            "CRS": parcels_layer.crs().authid(),
            "OUTPUT": "TEMPORARY_OUTPUT"
        }
    )["OUTPUT"]


except Exception as e:

    QMessageBox.critical(
        None,
        "CDU particella",
        "Errore nella fusione dei layer tematici:\n\n"
        + str(e)
    )

    raise


# ============================================================
# INTERSEZIONE
# ============================================================

try:

    inter = processing.run(
        "native:intersection",
        {
            "INPUT": single_parcel,
            "OVERLAY": merged,
            "OUTPUT": "TEMPORARY_OUTPUT"
        }
    )["OUTPUT"]


except Exception as e:

    QMessageBox.critical(
        None,
        "CDU particella",
        "Errore durante l'intersezione:\n\n"
        + str(e)
    )

    raise


# ============================================================
# INDIVIDUA SUPCALC
# ============================================================

supcalc_field = next(
    (
        name
        for name in inter.fields().names()
        if name.upper().startswith("SUPCALC")
    ),
    None
)


if not supcalc_field:

    QMessageBox.critical(
        None,
        "CDU particella",
        "Nel risultato dell'intersezione non è stato "
        "trovato il campo SUPCALC."
    )

    raise Exception(
        "SUPCALC non trovato"
    )


# ============================================================
# AGGIUNGE I CAMPI PERCENT E PERCENT_V
# ============================================================

field_names_upper = [
    name.upper()
    for name in inter.fields().names()
]


inter.startEditing()


if "PERCENT" not in field_names_upper:

    inter.dataProvider().addAttributes([
        QgsField("PERCENT", QVariant.Int)
    ])


if "PERCENT_V" not in field_names_upper:

    inter.dataProvider().addAttributes([
        QgsField("PERCENT_V", QVariant.String)
    ])


inter.updateFields()


# ============================================================
# CALCOLO PERCENTUALE
# STESSA LOGICA DEL CDU ATTUALE
# ============================================================

for feature in inter.getFeatures():

    area = feature.geometry().area()


    try:

        sup = float(
            str(
                feature[supcalc_field]
            ).replace(",", ".")
        )


        if sup > 0:

            percent = round(
                area / sup * 100
            )

        else:

            percent = 0


    except:

        percent = 0


    feature["PERCENT"] = percent


    feature["PERCENT_V"] = (
        "<1"
        if percent == 0
        else str(percent)
    )


    inter.updateFeature(
        feature
    )


inter.commitChanges()


# ============================================================
# ESTRAZIONE RECORD
# ============================================================

records = []


def get_field_value(
    feature,
    layer,
    field_name
):

    if field_name in layer.fields().names():

        value = feature[field_name]

        if value is None:

            return ""

        return str(value)


    return ""


for feature in inter.getFeatures():

    rec = {

        "foglio": get_field_value(
            feature,
            inter,
            "FOGLIO"
        ),

        "allegato": get_field_value(
            feature,
            inter,
            "ALLEGATO"
        ),

        "mappale": get_field_value(
            feature,
            inter,
            "MAPPALE"
        ),

        "tema": get_field_value(
            feature,
            inter,
            "TEMA"
        ),

        "zona": get_field_value(
            feature,
            inter,
            "ZONA"
        ),

        "dettaglio": get_field_value(
            feature,
            inter,
            "DETTAGLIO"
        ),

        "norme": get_field_value(
            feature,
            inter,
            "NORME"
        ),

        "percent_v": get_field_value(
            feature,
            inter,
            "PERCENT_V"
        ),

        "fk_cat": get_field_value(
            feature,
            inter,
            "FK_SRC"
        )
    }


    records.append(
        rec
    )


# ============================================================
# ORDINAMENTO
# ============================================================

def parse_mappale(value):

    v = str(value).strip()


    if v.isdigit():

        return (
            0,
            int(v),
            ""
        )


    match = re.match(
        r"^(\d+)([A-Za-z]+)$",
        v
    )


    if match:

        return (
            1,
            int(match.group(1)),
            match.group(2)
        )


    if v.isalpha():

        return (
            2,
            0,
            v
        )


    return (
        3,
        0,
        v
    )


def foglio_sort(value):

    try:

        return int(
            str(value)
        )

    except:

        return 0


records = sorted(
    records,
    key=lambda r: (
        foglio_sort(
            r["foglio"]
        ),
        parse_mappale(
            r["mappale"]
        ),
        r["tema"],
        r["zona"],
        r["percent_v"]
    )
)


# ============================================================
# FINESTRA RISULTATI
# ============================================================

dialog = QDialog()


dialog.setWindowTitle(
    "CDU - Particella "
    + str(mappale_val)
)


dialog.resize(
    900,
    600
)


layout = QVBoxLayout(
    dialog
)


# ============================================================
# LOGO AGIS DA GITHUB
# ============================================================

logo_url = (
    "https://raw.githubusercontent.com/"
    "aldogessa/aldogessa.github.io/main/"
    "docs/risorse/immagini/LogoAgisModulo.png"
)


logo_frame = QFrame()


logo_frame.setMinimumHeight(
    80
)


logo_frame.setStyleSheet(
    "background-color: white;"
)


logo_layout = QHBoxLayout(
    logo_frame
)


logo_layout.setContentsMargins(
    0,
    0,
    0,
    0
)


logo_layout.setAlignment(
    Qt.AlignLeft | Qt.AlignVCenter
)


logo_label = QLabel()


logo_label.setAlignment(
    Qt.AlignLeft | Qt.AlignVCenter
)


logo_label.setMinimumHeight(
    80
)


logo_layout.addWidget(
    logo_label
)


layout.addWidget(
    logo_frame
)


network_manager = QNetworkAccessManager(
    dialog
)


request = QNetworkRequest(
    QUrl(logo_url)
)


reply = network_manager.get(
    request
)


def logo_download_finished():

    if reply.error() == reply.NetworkError.NoError:

        pixmap = QPixmap()


        if pixmap.loadFromData(
            reply.readAll()
        ):

            logo_label.setPixmap(
                pixmap.scaled(
                    260,
                    75,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
            )


        else:

            logo_label.setText(
                "AGis – Aldo Gessa"
            )


    else:

        logo_label.setText(
            "AGis – Aldo Gessa"
        )


    reply.deleteLater()


reply.finished.connect(
    logo_download_finished
)


# ============================================================
# INTESTAZIONE PARTICELLA
# ============================================================

info_layout = QHBoxLayout()


info_layout.addWidget(
    QLabel(
        "<b>FID:</b> "
        + str(fid_val)
    )
)


info_layout.addWidget(
    QLabel(
        "<b>Foglio:</b> "
        + str(foglio_val)
    )
)


info_layout.addWidget(
    QLabel(
        "<b>Allegato:</b> "
        + str(allegato_val)
    )
)


info_layout.addWidget(
    QLabel(
        "<b>Mappale:</b> "
        + str(mappale_val)
    )
)


info_layout.addStretch()


layout.addLayout(
    info_layout
)


# ============================================================
# TABELLA
# ============================================================

headers = [
    "Fg.",
    "All.",
    "Map.",
    "Tema",
    "Zona",
    "Dettaglio",
    "Norme Specifiche",
    "Q.tà* %"
]


table = QTableWidget()


table.setColumnCount(
    len(headers)
)


table.setHorizontalHeaderLabels(
    headers
)


table.setRowCount(
    len(records)
)


for row, record in enumerate(
    records
):

    values = [

        record["foglio"],
        record["allegato"],
        record["mappale"],
        record["tema"],
        record["zona"],
        record["dettaglio"],
        record["norme"],
        record["percent_v"]

    ]


    for col, value in enumerate(
        values
    ):

        item = QTableWidgetItem(
            str(value)
        )


        item.setToolTip(
            str(value)
        )


        item.setTextAlignment(
            0x0001 | 0x0080
        )


        table.setItem(
            row,
            col,
            item
        )


# ============================================================
# DIMENSIONAMENTO DELLE COLONNE
# ============================================================

SHORT_WIDTH = {

    0: 45,
    1: 45,
    2: 55,
    7: 65

}


LONG_WIDTH = {

    3: 113,
    4: 113,
    5: 170,
    6: 226

}


header = table.horizontalHeader()


header.setSectionResizeMode(
    QHeaderView.Fixed
)


for column, width in SHORT_WIDTH.items():

    table.setColumnWidth(
        column,
        width
    )


for column, width in LONG_WIDTH.items():

    table.setColumnWidth(
        column,
        width
    )


table.setWordWrap(
    True
)


for row in range(
    table.rowCount()
):

    table.resizeRowToContents(
        row
    )


table.verticalHeader().setMinimumSectionSize(
    30
)


table.setAlternatingRowColors(
    True
)


table.setSelectionBehavior(
    QTableWidget.SelectRows
)


table.setEditTriggers(
    QTableWidget.NoEditTriggers
)


layout.addWidget(
    table
)


if not records:

    label = QLabel(
        "<b>Nessuna intersezione trovata "
        "con i layer selezionati.</b>"
    )


    layout.addWidget(
        label
    )


# ============================================================
# FUNZIONE COPIA NEGLI APPUNTI
# ============================================================

def copia_tabella():

    righe = []

    headers = []


    for col in range(
        table.columnCount()
    ):

        headers.append(
            table.horizontalHeaderItem(
                col
            ).text()
        )


    righe.append(
        "\t".join(headers)
    )


    for row in range(
        table.rowCount()
    ):

        valori = []


        for col in range(
            table.columnCount()
        ):

            item = table.item(
                row,
                col
            )


            if item:

                valore = item.text()

            else:

                valore = ""


            valore = (
                valore
                .replace("\t", " ")
                .replace("\n", " ")
                .replace("\r", " ")
            )


            valori.append(
                valore
            )


        righe.append(
            "\t".join(valori)
        )


    testo = "\n".join(
        righe
    )


    QApplication.clipboard().setText(
        testo
    )


# ============================================================
# PULSANTE CHIUDI
# ============================================================

button_layout = QHBoxLayout()


button_layout.addStretch()


copy_button = QPushButton(
    "Copia tabella"
)


copy_button.clicked.connect(
    copia_tabella
)


button_layout.addWidget(
    copy_button
)


close_button = QPushButton(
    "Chiudi"
)


close_button.clicked.connect(
    dialog.close
)


button_layout.addWidget(
    close_button
)


layout.addLayout(
    button_layout
)


# ============================================================
# MOSTRA RISULTATO
# ============================================================

dialog.exec()
