# -*- coding: utf-8 -*-
"""
AGis - Aldo Gessa
Trasformazione 3003 ↔ 7791  con API IGM
Versione STRICT + LOG DETTAGLIATO
Compatibile con QGIS 3.44

Ostacolo:
Le API IGM non supportano la trasformazione diretta

Soluzione:
API IGM per utilizzo grigliati trasformazione da 3003 -> 6706
Strumento nativo di QGIS (PROJ) per passaggio da 6706 -> 7791

Pipeline:
- 3003 → 6706 (API IGM) → 7791 (PROJ)
- 7791 → 6706 (PROJ) → 3003 (API IGM)
Rilevata empiricamente precisione millimetrica in Sardegna

Utilizzo:
Lo script deve essere utilizzato come script di processing, dunque il file.py
deve essere salvato nell'apposta cartella .../processing/script/
"""

import json
import urllib.request
import urllib.error
import time

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFeatureSink,
    QgsProcessingException,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsVectorLayer
)
import processing


API_URL = "https://igmi.esercito.difesa.it/porta-magna/wps/volapi"


class IGM3003_7791(QgsProcessingAlgorithm):

    PARAM_INPUT = "INPUT"
    PARAM_OUTPUT = "OUTPUT"

    def tr(self, string):
        return QCoreApplication.translate("IGM3003_7791", string)

    def createInstance(self):
        return IGM3003_7791()

    def name(self):
        return "igm_3003_7791"

    def displayName(self):
        return self.tr("Trasformazione ufficiale 3003 ↔ 7791 (API IGM)")

    def group(self):
        return self.tr("IGM")

    def groupId(self):
        return "igm_tools"

    def shortHelpString(self):
        return self.tr(
            "Esegue la trasformazione ufficiale Monte Mario ↔ RDN2008/TM32.\n"
            "Input accettati: EPSG:3003 o EPSG:7791.\n"
            "Output determinato automaticamente.\n"
            "Pipeline:\n"
            " - 3003 → 6706 (API IGM) → 7791 (PROJ)\n"
            " - 7791 → 6706 (PROJ) → 3003 (API IGM)\n"
            "Versione STRICT: blocca in caso di geometrie invalide."
        )

    # ---------------------------------------------------------
    # API CALL
    # ---------------------------------------------------------
    def call_api(self, payload):
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(API_URL, data=data, headers={"Content-Type": "application/json"})

        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            raise QgsProcessingException(f"Errore chiamando l'API IGM: {e}")

    # ---------------------------------------------------------
    # FLATTEN GEOMETRY
    # ---------------------------------------------------------
    def flatten(self, geom):
        pts = []
        meta = []

        if geom.type() == QgsWkbTypes.PolygonGeometry:
            parts = geom.asMultiPolygon() if geom.isMultipart() else [geom.asPolygon()]
            for poly in parts:
                rings = []
                for ring in poly:
                    rings.append(len(ring))
                    pts.extend([(p.x(), p.y()) for p in ring])
                meta.append(rings)

        else:
            parts = geom.asMultiPolyline() if geom.isMultipart() else [geom.asPolyline()]
            for line in parts:
                meta.append(len(line))
                pts.extend([(p.x(), p.y()) for p in line])

        return pts, meta

    # ---------------------------------------------------------
    # REBUILD GEOMETRY
    # ---------------------------------------------------------
    def rebuild(self, pts_iter, meta, geom_type, is_multi):
        if geom_type == QgsWkbTypes.PolygonGeometry:
            polys = []
            for rings in meta:
                poly = []
                for n in rings:
                    ring = [QgsPointXY(*next(pts_iter)) for _ in range(n)]
                    poly.append(ring)
                polys.append(poly)
            return QgsGeometry.fromMultiPolygonXY(polys) if is_multi else QgsGeometry.fromPolygonXY(polys[0])

        else:
            lines = []
            for n in meta:
                line = [QgsPointXY(*next(pts_iter)) for _ in range(n)]
                lines.append(line)
            return QgsGeometry.fromMultiPolylineXY(lines) if is_multi else QgsGeometry.fromPolylineXY(lines[0])

    # ---------------------------------------------------------
    # MAIN
    # ---------------------------------------------------------
    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.PARAM_INPUT,
                self.tr("Layer di input (3003 o 7791)"),
                [QgsProcessing.TypeVectorAnyGeometry]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PARAM_OUTPUT,
                self.tr("Layer trasformato")
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        t0 = time.time()

        # INPUT
        source = self.parameterAsSource(parameters, self.PARAM_INPUT, context)
        crs_in = source.sourceCrs().authid()

        if crs_in not in ("EPSG:3003", "EPSG:7791"):
            raise QgsProcessingException("Questo script accetta solo layer in EPSG:3003 o EPSG:7791.")

        crs_out = "EPSG:7791" if crs_in == "EPSG:3003" else "EPSG:3003"

        feedback.pushInfo("--------------------------------------------------")
        feedback.pushInfo(" TRASFORMAZIONE UFFICIALE 3003 ↔ 7791 (API IGM)")
        feedback.pushInfo("--------------------------------------------------")
        feedback.pushInfo(f"CRS input:  {crs_in}")
        feedback.pushInfo(f"CRS output: {crs_out}")

        # SINK
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.PARAM_OUTPUT,
            context,
            source.fields(),
            source.wkbType(),
            QgsCoordinateReferenceSystem(crs_out)
        )

        # LETTURA FEATURE
        features = list(source.getFeatures())
        total_feats = len(features)
        feedback.pushInfo(f"Numero feature: {total_feats}")

        all_pts = []
        metas = []
        geom_types = []
        is_multis = []

        # VALIDAZIONE STRICT
        for f in features:
            geom = f.geometry()

            if not geom.isGeosValid():
                raise QgsProcessingException(
                    f"Geometria invalida nella feature ID {f.id()}. "
                    "Correggere il layer prima di procedere."
                )

            geom_types.append(QgsWkbTypes.geometryType(geom.wkbType()))
            is_multis.append(geom.isMultipart())
            pts, meta = self.flatten(geom)
            all_pts.extend(pts)
            metas.append(meta)

        total_pts = len(all_pts)
        feedback.pushInfo(f"Vertici totali: {total_pts}")

        # PIPELINE
        if crs_in == "EPSG:3003":

            # 3003 → 6706 (API)
            feedback.pushInfo("STEP 1: API IGM 3003 → 6706")
            chunks = [all_pts[i:i+32000] for i in range(0, total_pts, 32000)]
            feedback.pushInfo(f"Chunk API: {len(chunks)}")

            converted = []
            for i, chunk in enumerate(chunks):
                feedback.pushInfo(f" - Invio chunk {i+1}/{len(chunks)} ({len(chunk)} punti)")
                req = {
                    "richiesta": "conversione",
                    "utente": "qgis_user",
                    "chiave": "secret",
                    "inEpsg": 3003,
                    "outEpsg": 6706,
                    "coordinate": [{"e": e, "n": n} for e, n in chunk]
                }
                resp = self.call_api(req)
                converted.extend([(c["e"], c["n"]) for c in resp["coordinate"]])

            # 6706 → 7791 (PROJ)
            feedback.pushInfo("STEP 2: PROJ 6706 → 7791")
            temp = QgsVectorLayer("Point?crs=EPSG:6706", "tmp", "memory")
            pr = temp.dataProvider()
            for e, n in converted:
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(e, n)))
                pr.addFeature(f)

            result = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": temp,
                    "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:7791"),
                    "OUTPUT": "memory:"
                },
                context=context,
                feedback=feedback
            )["OUTPUT"]

            final_pts = [(f.geometry().asPoint().x(), f.geometry().asPoint().y()) for f in result.getFeatures()]

        else:

            # 7791 → 6706 (PROJ)
            feedback.pushInfo("STEP 1: PROJ 7791 → 6706")
            temp = QgsVectorLayer("Point?crs=EPSG:7791", "tmp", "memory")
            pr = temp.dataProvider()
            for e, n in all_pts:
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(e, n)))
                pr.addFeature(f)

            result = processing.run(
                "native:reprojectlayer",
                {
                    "INPUT": temp,
                    "TARGET_CRS": QgsCoordinateReferenceSystem("EPSG:6706"),
                    "OUTPUT": "memory:"
                },
                context=context,
                feedback=feedback
            )["OUTPUT"]

            pts_6706 = [(f.geometry().asPoint().x(), f.geometry().asPoint().y()) for f in result.getFeatures()]

            # 6706 → 3003 (API)
            feedback.pushInfo("STEP 2: API IGM 6706 → 3003")
            chunks = [pts_6706[i:i+32000] for i in range(0, len(pts_6706), 32000)]
            feedback.pushInfo(f"Chunk API: {len(chunks)}")

            final_pts = []
            for i, chunk in enumerate(chunks):
                feedback.pushInfo(f" - Invio chunk {i+1}/{len(chunks)} ({len(chunk)} punti)")
                req = {
                    "richiesta": "conversione",
                    "utente": "qgis_user",
                    "chiave": "secret",
                    "inEpsg": 6706,
                    "outEpsg": 3003,
                    "coordinate": [{"e": e, "n": n} for e, n in chunk]
                }
                resp = self.call_api(req)
                final_pts.extend([(c["e"], c["n"]) for c in resp["coordinate"]])

        # REBUILD
        feedback.pushInfo("Ricostruzione geometrie…")
        it = iter(final_pts)

        for i, f in enumerate(features):
            new_f = QgsFeature(source.fields())
            new_f.setAttributes(f.attributes())
            new_geom = self.rebuild(it, metas[i], geom_types[i], is_multis[i])
            new_f.setGeometry(new_geom)
            sink.addFeature(new_f)

        # LOG FINALE
        t1 = time.time()
        feedback.pushInfo("--------------------------------------------------")
        feedback.pushInfo(" TRASFORMAZIONE COMPLETATA ")
        feedback.pushInfo("--------------------------------------------------")
        feedback.pushInfo(f"Feature elaborate: {total_feats}")
        feedback.pushInfo(f"Vertici elaborati: {total_pts}")
        feedback.pushInfo(f"CRS input:  {crs_in}")
        feedback.pushInfo(f"CRS output: {crs_out}")
        feedback.pushInfo(f"Tempo totale: {round(t1 - t0, 2)} secondi")
        feedback.pushInfo("--------------------------------------------------")

        return {self.PARAM_OUTPUT: dest_id}

