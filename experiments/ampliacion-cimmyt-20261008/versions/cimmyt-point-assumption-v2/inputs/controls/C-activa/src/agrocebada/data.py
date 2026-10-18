"""Importación y auditoría; ninguna función modifica archivos originales."""
import json
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
from .common import DATASET, CHANGE, EXTERNAL, ID, TARGET, ROOT, PROCESSED, sha256, write_json


def verify_master(table, geometries, expected=True):
    for name, d in [("CSV", table), ("geometría", geometries)]:
        if d[ID].isna().any() or d[ID].duplicated().any():
            raise ValueError(f"Identificadores faltantes o duplicados en {name}")
    if set(table[ID]) != set(geometries[ID]):
        raise ValueError("Identificadores incompatibles entre CSV y geometría")
    if not table.CONJUNTO.isin(["ENTRENAMIENTO", "PREDICCION"]).all():
        raise ValueError("Conjunto oficial no reconocido")
    hidden = table.CONJUNTO.eq("PREDICCION")
    if table.loc[hidden, TARGET].notna().any():
        raise ValueError("Etiqueta inesperada en PREDICCION")
    y = table.loc[~hidden, TARGET]
    if y.isna().any() or not np.isfinite(y).all() or (y <= 0).any():
        raise ValueError("Etiqueta de entrenamiento inválida")
    j = table.merge(geometries[[ID, "área_ha", "CONJUNTO"]], on=ID, validate="one_to_one", suffixes=("", "_shp"))
    if not np.allclose(j.AREA_HA, j["área_ha"], atol=0.001) or not j.CONJUNTO.eq(j.CONJUNTO_shp).all():
        raise ValueError("Área o conjunto discrepantes")
    if (table.AREA_HA <= 0).any():
        raise ValueError("Superficie inválida")
    if expected and (len(table), len(y), int(hidden.sum())) != (197, 138, 59):
        raise ValueError("Se esperan 197 parcelas, 138 etiquetas y 59 casos ocultos")


def load_master():
    table = pd.read_csv(DATASET / "Data/ID_area_rendimiento_70_30_Reto_AgroCebada.csv").dropna(axis=1, how="all")
    shp = next(DATASET.rglob("*.shp"))
    geo = gpd.read_file(shp, engine="pyogrio", encoding="UTF-8").rename(columns={"ID_POLIGON": ID})
    verify_master(table, geo)
    if geo.crs is None or geo.geometry.isna().any() or geo.geometry.is_empty.any() or not geo.is_valid.all():
        raise ValueError("Geometrías inválidas o CRS ausente; revisar auditoría antes de reparar")
    master = geo[[ID, "Estado", "Municipio", "geometry"]].merge(table, on=ID, validate="one_to_one")
    return master.sort_values(ID).reset_index(drop=True)


def load_satellite():
    frames = [pd.read_csv(p) for p in sorted((DATASET / "Data").glob("Conjunto*.csv"))]
    d = pd.concat(frames, ignore_index=True)
    d["date"] = pd.to_datetime(d.fecha_captura, format="%d/%m/%Y", errors="raise")
    if d.duplicated([ID, "date", "sensor"]).any():
        raise ValueError("Captura duplicada por parcela/fecha/sensor")
    if not d.porcentaje_nubosidad.dropna().between(0, 100).all():
        raise ValueError("Nubosidad fuera de 0–100")
    if np.isinf(d.select_dtypes("number")).any().any():
        raise ValueError("Valores satelitales no finitos")
    return d


def provenance(promote=True):
    entries = []
    for p in sorted(DATASET.rglob("*")):
        if p.is_file():
            units="Índices: ecuaciones originales; rendimiento t/ha, área ha"
            scale="por parcela y captura"
            if p.suffix==".tif":
                units="PREC mm/mes; Tmin/Tmax °C promedio mensual; elevación m; pendiente grados"
                scale="clima 0.05 grados; topografía 120 m"
            entries.append({"path": str(p.relative_to(ROOT)), "sha256": sha256(p), "bytes": p.stat().st_size, "provider": "Dataset oficial AgroCebada 2026", "units":units,"scale":scale,"citation":"Bases AgroCebada 2026 y Ecuaciones_indices_AgroCebada_FIRA_2026.pdf","conditions": "Uso del reto; revisar redistribución antes de publicar"})
    downloads = json.loads((CHANGE / "evidence/download-manifest.json").read_text(encoding="utf-8"))
    for entry in downloads:
        p = CHANGE / "evidence" / entry["file"]
        if sha256(p) != entry["sha256"]:
            raise ValueError(f"Hash externo incompatible: {p.name}")
        if promote:
            dst = EXTERNAL / p.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists() and sha256(dst) != entry["sha256"]:
                raise ValueError("Caché externa existente alterada")
            if not dst.exists():
                shutil.copy2(p, dst)
        nasa = p.name.startswith("nasa")
        units={k:v["units"] for k,v in json.loads(p.read_text(encoding="utf-8"))["parameters"].items()} if nasa else "producción toneladas; superficie ha; cociente t/ha"
        entries.append({**entry, "path": str((EXTERNAL / p.name).relative_to(ROOT)), "provider": "NASA POWER" if nasa else "DGSIAP", "units":units,"status": "candidato", "scale": "regional; MERRA2 0.5°×0.625°, solar SYN1deg" if nasa else "municipal anual", "conditions": "Datos públicos; citar proveedor y metadatos originales", "citation": "https://power.larc.nasa.gov/docs/methodology/" if nasa else "https://nube.agricultura.gob.mx/datosAbiertos/Agricola.php"})
    write_json(PROCESSED / "source-manifest.json", entries)
    return entries


def audit(master, satellite):
    if set(satellite[ID]) != set(master[ID]):
        raise ValueError("Cobertura de identificadores satelitales incompatible")
    projected = master.to_crs(32614)
    overlaps = []
    for i, row in projected.iterrows():
        for j in projected.sindex.query(row.geometry, predicate="intersects"):
            if j > i:
                area = row.geometry.intersection(projected.iloc[j].geometry).area
                if area > 1:
                    overlaps.append({"left": row[ID], "right": projected.iloc[j][ID], "area_m2": area})
    result = {"rows": len(master), "training": int(master[TARGET].notna().sum()), "hidden": int(master[TARGET].isna().sum()), "crs": str(master.crs), "invalid_geometries": int((~master.is_valid).sum()), "overlaps_gt_1m2": overlaps, "states": master.groupby("Estado")[TARGET].agg(["count", "mean", "nunique"]).to_dict(), "satellite": {}, "units": {"yield": "t/ha", "area": "ha", "precip": "mm/mes", "temperatures": "°C; medias mensuales", "elevation": "m", "slope": "grados"}}
    for s, g in satellite.groupby("sensor"):
        means = [c for c in g if c.endswith("_promedio")]
        bad = {}
        for c in means:
            stem = c.removesuffix("_promedio")
            cnt = ((g[c] < g[stem+"_min"] - .001) | (g[c] > g[stem+"_max"] + .001) | (g[stem+"_std"] < 0)).sum()
            if cnt:
                bad[c] = int(cnt)
        result["satellite"][s] = {"rows": len(g), "date_min": str(g.date.min().date()), "date_max": str(g.date.max().date()), "available": g[means].count().to_dict(), "cloud_missing": int(g.porcentaje_nubosidad.isna().sum()), "negative_lai": int(g.lai_promedio.lt(0).sum()), "inconsistent_stats": bad}
    result["tlaxcala_labels"]=master.loc[master.Estado.eq("Tlaxcala"),TARGET].dropna().value_counts().sort_index().to_dict()
    result["encodings"]={"csv":"UTF-8; fechas día/mes/año","shapefile":"UTF-8 explícito, alias ID_POLIGON","siap":"CP1252 verificado"}
    write_json(PROCESSED / "audit.json", result)
    return result
