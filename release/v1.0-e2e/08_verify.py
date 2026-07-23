"""
Day 12 demo -- re-open the STEP files in FreeCAD and report stats.
This is the same script our customer would use to verify they can
open the deliverables.
"""
import json
import sys
from pathlib import Path

import FreeCAD
import Import

COOLER = "C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/05_cooler_v050_calibrated.step"
KILN   = "C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/06_hetauda_kiln.step"

def inspect(path):
    Import.open(path)
    doc = FreeCAD.ActiveDocument
    objs = list(doc.Objects)
    # Some imported objects (e.g. App.GeoFeature) don't have .Shape
    solid_objs = [o for o in objs if hasattr(o, "Shape") and hasattr(o.Shape, "Faces")]
    n_faces = sum(len(o.Shape.Faces) for o in solid_objs)
    n_edges = sum(len(o.Shape.Edges) for o in solid_objs)
    n_verts = sum(len(o.Shape.Vertexes) for o in solid_objs)
    # Use the largest solid for bbox
    if solid_objs:
        largest = max(solid_objs, key=lambda o: o.Shape.BoundBox.XLength * o.Shape.BoundBox.YLength * o.Shape.BoundBox.ZLength)
        bb = largest.Shape.BoundBox
    else:
        bb = objs[0].Shape.BoundBox
    return {
        "ok": True,
        "path": path,
        "size_bytes": Path(path).stat().st_size,
        "n_objects": len(objs),
        "n_solids": len(solid_objs),
        "total_faces": n_faces,
        "total_edges": n_edges,
        "total_vertices": n_verts,
        "bounding_box_mm": [round(bb.XLength*1000, 1), round(bb.YLength*1000, 1), round(bb.ZLength*1000, 1)],
    }

print(json.dumps({"cooler": inspect(COOLER), "kiln": inspect(KILN)}, indent=2))
