"""Conserva modelos y verifica una migración limitada a la ruta de evidencia."""
import json
import shutil
import sys
from pathlib import Path

import joblib
import pandas as pd

from agrocebada.common import ARTIFACTS, ROOT, code_hash, sha256, write_json
from agrocebada.inference import Predictor

snapshot = ARTIFACTS / "versions/archive-2026-10-03"


def capture():
    snapshot.mkdir(parents=True, exist_ok=False)
    state = {"code_hash": code_hash(), "files": {}, "models": {}}
    for path in sorted((ROOT / "src/agrocebada").glob("*.py")):
        state["files"][path.name] = sha256(path)
    shutil.copy2(ROOT / "src/agrocebada/common.py", snapshot / "common.py")
    for name in ["selected", "official"]:
        predictor = Predictor(name)
        predictor.predict(predictor.master.ID_POLIGONO.tolist()).to_csv(snapshot / f"predictions_{name}.csv", index=False)
        for filename in [f"model_{name}.joblib", f"contract_{name}.json"]:
            shutil.copy2(ARTIFACTS / filename, snapshot / filename)
        state["models"][name] = sha256(ARTIFACTS / f"model_{name}.joblib")
    write_json(snapshot / "before.json", state)
    print("Versiones originales y predicciones de ambas rutas conservadas.")


def migrate():
    state = json.loads((snapshot / "before.json").read_text(encoding="utf-8"))
    current = {p.name: sha256(p) for p in (ROOT / "src/agrocebada").glob("*.py")}
    assert current.keys() == state["files"].keys()
    assert {key for key in current if current[key] != state["files"][key]} == {"common.py"}
    records = {}
    for name in ["selected", "official"]:
        model_path = ARTIFACTS / f"model_{name}.joblib"
        contract_path = ARTIFACTS / f"contract_{name}.json"
        assert sha256(model_path) == state["models"][name]
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        assert contract["code_hash"] == state["code_hash"]
        bundle = joblib.load(model_path)
        assert bundle["contract"]["code_hash"] == state["code_hash"]
        bundle["contract"]["code_hash"] = code_hash()
        contract["code_hash"] = code_hash()
        joblib.dump(bundle, model_path)
        contract["model_hash"] = sha256(model_path)
        write_json(contract_path, contract)
        predictor = Predictor(name)
        actual = predictor.predict(predictor.master.ID_POLIGONO.tolist())
        expected = pd.read_csv(snapshot / f"predictions_{name}.csv")
        pd.testing.assert_frame_equal(actual, expected, check_exact=False, rtol=0, atol=1e-10)
        records[name] = {"before_model_hash": state["models"][name], "after_model_hash": contract["model_hash"], "parcels_compared": len(actual), "prediction_and_interval_tolerance": 1e-10}
    write_json(ARTIFACTS / "archive-compatibility.json", {"date": "2026-10-03", "changed_source": "common.py", "reason": "Resolver la evidencia en el cambio activo o archivado", "before_code_hash": state["code_hash"], "after_code_hash": code_hash(), "retrained": False, "backup": str(snapshot.relative_to(ROOT)), "models": records})
    print("Contratos actualizados; ambas rutas conservan las predicciones e intervalos de las 197 parcelas.")


if __name__ == "__main__":
    {"capture": capture, "migrate": migrate}[sys.argv[1]]()
