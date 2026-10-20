"""Web-map boundaries must retain the authoritative geographic geometry."""
import hashlib
import json

import geopandas as gpd
import shapely

from agrocebada.common import ROOT


def test_web_map_preserves_all_original_boundaries_and_identifiers():
    source = ROOT / "data/processed/parcels.parquet"
    public = ROOT / "frontend/public/data"
    original = gpd.read_parquet(source).sort_values("ID_POLIGONO").to_crs(4326)
    collection = json.loads((public / "parcels.geojson").read_text(encoding="utf-8"))
    exported = gpd.GeoDataFrame.from_features(collection, crs=4326)
    assert len(exported) == 197 and exported.id.is_unique
    assert exported.id.tolist() == original.ID_POLIGONO.tolist()
    assert exported.state.tolist() == original.Estado.tolist()
    assert exported.is_valid.all() and not exported.geometry.is_empty.any()
    assert shapely.equals_exact(exported.geometry.to_numpy(), shapely.force_2d(original.geometry.to_numpy()), tolerance=1e-12).all()
    assert [feature["id"] for feature in collection["features"]] == exported.id.tolist()
    # The geographic web map and the result cards must resolve the same selections/videos.
    cards = json.loads((public / "parcels.json").read_text(encoding="utf-8"))
    assert set(exported.id) == {card["id"] for card in cards}
    provenance = json.loads((public / "map-provenance.json").read_text(encoding="utf-8"))
    assert provenance["sourceSha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert provenance["outputCrs"] == "EPSG:4326"
    assert provenance["axisOrder"] == "longitude,latitude"
