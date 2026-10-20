"""Export verified existing results for the standalone React dashboard.

No training or mutation of scientific source data/artifacts. Run from project venv.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil

import numpy as np
import pandas as pd
import shapely
from export_map_geometry import export_map_geometry
from agrocebada.inference import Predictor
from agrocebada.modeling import metric

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "frontend/public"
DATA = PUBLIC / "data"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")


def number(value, digits=6):
    return round(float(value), digits) if pd.notna(value) and np.isfinite(value) else None


def main():
    predictor = Predictor("selected")
    master = predictor.master.sort_values("ID_POLIGONO").reset_index(drop=True)
    ids = master.ID_POLIGONO.tolist()
    predictions = predictor.predict(ids).set_index("ID_POLIGONO")
    validation = json.loads((ROOT / "artifacts/validation.json").read_text(encoding="utf-8"))
    plan = json.loads((PUBLIC / "media/parcel-videos/assignment.json").read_text(encoding="utf-8"))
    current_sha = hashlib.sha256((ROOT / "data/processed/parcels.parquet").read_bytes()).hexdigest()
    assert current_sha == plan["source_sha256"]
    assert len(ids) == len(set(ids)) == 197
    projected = master.to_crs(32614)
    bounds = projected.total_bounds
    scale = 850 / max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    ox, oy = (bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2

    def xy(x, y):
        return [round(500 + (x - ox) * scale, 4), round(500 - (y - oy) * scale, 4)]

    # Spatial coordinates are projected then uniformly scaled; the map never warps shapes.
    # A 1000-square map frame leaves padding around all parcels.
    parcels = []
    for i, row in master.iterrows():
        g = shapely.force_2d(projected.geometry.iloc[i])
        points = [xy(x, y) for x, y, *_ in g.exterior.coords]
        a = np.asarray(points)
        p = predictions.loc[row.ID_POLIGONO]
        video_id = plan["parcel_to_video"][row.ID_POLIGONO]
        definition = next(v for v in plan["videos"] if v["video_id"] == video_id)
        folder = f"{video_id}_{definition['reference_parcel_id']}"
        parcels.append({
            "id": row.ID_POLIGONO, "state": row.Estado, "municipality": row.Municipio,
            "area": number(row.AREA_HA), "observed": number(row.RENDIMIENTO_T_HA),
            "estimate": number(p.RENDIMIENTO_T_HA), "production": number(p.PRODUCCION_T),
            "low": number(p.get("INTERVAL_LOW")) if validation["interval"]["available"] else None,
            "high": number(p.get("INTERVAL_HIGH")) if validation["interval"]["available"] else None,
            "points": points, "center": xy(g.representative_point().x, g.representative_point().y),
            "bounds": [float(a[:, 0].min()), float(a[:, 1].min()), float(a[:, 0].max()), float(a[:, 1].max())],
            "videoId": video_id, "videoPath": f"/media/parcel-videos/{folder}/clip.mp4",
        })
    write(DATA / "parcels.json", parcels)
    export_map_geometry()
    quality = pd.read_parquet(ROOT / "data/processed/quality_whittaker_20_10.parquet")
    curves = pd.read_parquet(ROOT / "data/processed/curves.parquet")
    curves = curves[(curves.cloud_threshold == 20) & (curves["lambda"] == 10)]
    for pid in ids:
        entries = []
        for sensor in ["Sentinel-2", "Planet"]:
            group = curves[(curves.ID_POLIGONO == pid) & (curves.sensor == sensor)].sort_values("date")
            q = quality[(quality.ID_POLIGONO == pid) & (quality.sensor == sensor)]
            entries.append({"sensor": sensor, "quality": None if q.empty else {"observations": int(q.iloc[0].observations), "usable": int(q.iloc[0].usable)}, "points": [
                {"date": str(pd.Timestamp(row.date).date()), "value": number(row.value), "hasObservation": bool(row.observed_bin)} for row in group.itertuples()
            ]})
        write(DATA / "curves" / f"{pid}.json", entries)
    oof = pd.read_csv(ROOT / "artifacts/oof.csv")
    assert len(oof) == 138 and oof.ID_POLIGONO.is_unique
    for key, value in metric(oof.RENDIMIENTO_T_HA, oof.selected).items():
        assert np.isclose(value, validation["metrics"]["selected"][key], rtol=0, atol=1e-12)
    for state, group in oof.groupby("Estado"):
        for key, value in metric(group.RENDIMIENTO_T_HA, group.selected).items():
            assert np.isclose(value, validation["by_state"][state][key], rtol=0, atol=1e-12)
    presentation = predictor.contract["presentation"]
    assert validation["champion_model"]["name"].startswith(presentation["id"] + "_")
    _, explanation = predictor.explain(ids[0])
    write(DATA / "model.json", {
        "id": presentation["id"], "name": presentation["name"], "version": predictor.contract["model_hash"][:10],
        "cutoff": presentation["feature_period_end"], "artifactCutoff": predictor.contract["cutoff"],
        "sourceCommit": presentation["source_commit"], "scope": presentation["scope"],
        "method": presentation["method"], "validationScheme": presentation["validation_scheme"],
        "metrics": validation["metrics"]["selected"],
        "byState": validation["by_state"], "interval": validation["interval"],
        "sources": presentation["context_sources"], "explanation": explanation,
        "oof": [{"id": r.ID_POLIGONO, "state": r.Estado, "observed": number(r.RENDIMIENTO_T_HA), "estimated": number(r.selected)} for r in oof.itertuples()],
        "sourceHashes": {"parcels": current_sha, "model": predictor.contract["model_hash"], "contract": hashlib.sha256(predictor.contract_path.read_bytes()).hexdigest(),
                         "validation": hashlib.sha256((ROOT / "artifacts/validation.json").read_bytes()).hexdigest(),
                         "oof": hashlib.sha256((ROOT / "artifacts/oof.csv").read_bytes()).hexdigest()},
        "curveMethod": {"cloudThreshold": 20, "lambda": 10, "label": "NDVI · Whittaker · nubosidad ≤20% · λ=10"},
    })
    target = PUBLIC / "media/parcel-videos"
    for video in plan["videos"]:
        folder = target / f"{video['video_id']}_{video['reference_parcel_id']}"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch()
    write(target / "assignment.json", plan)
    downloads = PUBLIC / "downloads"
    downloads.mkdir(exist_ok=True)
    for filename in ["predictions_59.csv", "predictions_59_intervals.csv"]:
        shutil.copyfile(ROOT / "artifacts" / filename, downloads / filename)
    # Reopen exported files and verify IDs, numbers, and frame bounds.
    saved = json.loads((DATA / "parcels.json").read_text(encoding="utf-8"))
    assert len(saved) == 197 and len({p["id"] for p in saved}) == 197
    for p in saved:
        assert math.isfinite(p["estimate"]) and p["estimate"] >= 0
        assert np.isclose(p["estimate"], predictions.loc[p["id"], "RENDIMIENTO_T_HA"], atol=1e-6)
        if validation["interval"]["available"]:
            assert np.isclose(p["low"], predictions.loc[p["id"], "INTERVAL_LOW"], atol=1e-6)
            assert np.isclose(p["high"], predictions.loc[p["id"], "INTERVAL_HIGH"], atol=1e-6)
        assert 0 <= min(p["bounds"]) and max(p["bounds"]) <= 1000
    print(f"Exported {len(saved)} verified parcels, {len(oof)} OOF points, and {len(plan['videos'])} empty video folders.")


if __name__ == "__main__":
    main()
