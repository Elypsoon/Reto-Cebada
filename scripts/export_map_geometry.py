"""Export the original parcel boundaries as RFC 7946 GeoJSON for the web map."""
from pathlib import Path
import hashlib
import json

import geopandas as gpd
import shapely

ROOT = Path(__file__).resolve().parents[1]


def export_map_geometry():
    source = ROOT / "data/processed/parcels.parquet"
    target = ROOT / "frontend/public/data/parcels.geojson"
    parcels = gpd.read_parquet(source).sort_values("ID_POLIGONO")
    assert parcels.crs is not None
    assert len(parcels) == 197 and parcels.ID_POLIGONO.is_unique
    assert parcels.geometry.notna().all() and not parcels.geometry.is_empty.any()
    assert parcels.is_valid.all() and parcels.geom_type.isin(["Polygon", "MultiPolygon"]).all()
    geographic = parcels[["ID_POLIGONO", "Estado", "Municipio", "geometry"]].to_crs(4326)
    geographic.geometry = shapely.force_2d(geographic.geometry)
    geographic = geographic.rename(columns={"ID_POLIGONO": "id", "Estado": "state", "Municipio": "municipality"})
    collection = json.loads(geographic.to_json(drop_id=True))
    for feature in collection["features"]:
        feature["id"] = feature["properties"]["id"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(collection, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    reopened = gpd.GeoDataFrame.from_features(json.loads(target.read_text(encoding="utf-8")), crs=4326)
    assert reopened.id.tolist() == geographic.id.tolist() and reopened.is_valid.all()
    assert shapely.equals_exact(reopened.geometry.to_numpy(), geographic.geometry.to_numpy(), tolerance=1e-12).all()
    provenance = {
        "source": "data/processed/parcels.parquet", "sourceSha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "sourceCrs": parcels.crs.to_string(), "outputCrs": "EPSG:4326", "axisOrder": "longitude,latitude",
        "operation": "to_crs(4326), force_2d; no simplification, repair, joins or rounding",
        "features": len(reopened), "geopandasVersion": gpd.__version__, "shapelyVersion": shapely.__version__,
    }
    target.with_name("map-provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Verified {len(reopened)} original parcel boundaries in WGS84.")


if __name__ == "__main__":
    export_map_geometry()
