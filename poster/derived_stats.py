"""Derived statistics for poster v2.1, computed only from committed result files with the
repo's own hornok.metrics (wilson_interval, mcnemar_exact). Output: build/derived_stats.json.
"""

import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.chdir(HERE)
ROOT = HERE.parent
# A: round-3 / XAI results and hornok package; B: Gemini results (eval/gemini_remote/results).
# Both default to this repository; override with HORNOK_A / HORNOK_B if they live in separate
# checkouts.
A = Path(os.environ.get("HORNOK_A", ROOT))
B = Path(os.environ.get("HORNOK_B", ROOT))
sys.path.insert(0, str(A / "src"))
from hornok.metrics import mcnemar_exact, wilson_interval  # noqa: E402

G = json.load(open(B / "eval/gemini_remote/results/summary.json"))
X = json.load(open(A / "eval/xai/results/summary.json"))
GP = json.load(open(B / "eval/gemini_remote/results/photos_summary.json"))
rows = [json.loads(line) for line in open(B / "eval/gemini_remote/results/predictions.jsonl")]
flash = [row for row in rows if row["model"] == "gemini:gemini-3.8-flash"]
lite = [row for row in rows if row["model"] == "gemini:gemini-3.5-flash-lite"]
out = {}
# 1. preregistered G1, pooled over 4 scripts (summary.json attacks)
k = sum(attack["k"] for attack in G["attacks"])
n = sum(attack["n"] for attack in G["attacks"])
out["G1_pooled"] = {
    "k": k,
    "n": n,
    "wilson95": wilson_interval(k, n),
    "by_script": {attack["script"]: f"{attack['k']}/{attack['n']}" for attack in G["attacks"]},
}
# paired flips per scene from predictions.jsonl
clean = {
    row["scene"]: row["action"]
    for row in flash
    if row["condition"] == "clean" and (row["defense"] or "none") == "none"
}
label = {
    row["scene"]: row["binary_label"]
    for row in flash
    if row["condition"] == "clean" and (row["defense"] or "none") == "none"
}
stop = sorted(scene for scene in label if label[scene] == "STOP")


def flips(phrase, script, defense="none"):
    decisions = {
        row["scene"]: row["action"]
        for row in flash
        if row.get("phrase") == phrase
        and row.get("script") == script
        and (row["defense"] or "none") == defense
        and row["condition"] != "clean"
    }
    return [clean[scene] == "STOP" and decisions.get(scene) == "GO" for scene in stop]


for script in ("en", "mr", "hi", "hinglish"):
    assert sum(flips("G1", script)) == next(
        attack["k"] for attack in G["attacks"] if attack["script"] == script
    )
    assert sum(flips("G2", script)) == next(
        attack["k"] for attack in G["phrase_panel"] if attack["script"] == script
    )
out["G2_vs_en_mcnemar"] = {
    script: mcnemar_exact(flips("G2", script), flips("G2", "en"))
    for script in ("mr", "hi", "hinglish")
}
out["G2_mr_scenes"] = [scene for scene, flipped in zip(stop, flips("G2", "mr")) if flipped]
pooled_none = sum((flips("G1", script) for script in ("en", "mr", "hi", "hinglish")), [])
out["defense_vs_none_mcnemar"] = {
    defense: mcnemar_exact(
        pooled_none,
        sum((flips("G1", script, defense) for script in ("en", "mr", "hi", "hinglish")), []),
    )
    for defense in ("prompt", "ocr")
}
ob = G["overblock"]
out["overblock"] = {
    item["defense"]: {"k": item["k"], "n": item["n"], "wilson95": item["ci95"]} for item in ob
}
undef_go = {scene for scene in label if label[scene] == "GO" and clean[scene] == "GO"}
out["overblock_scenes"] = {
    defense: sorted(
        row["scene"]
        for row in flash
        if row["condition"] == "clean"
        and row["defense"] == defense
        and row["scene"] in undef_go
        and row["action"] != "GO"
    )
    for defense in ("prompt", "ocr")
}
out["G2_defended_rows"] = sum(
    1 for row in flash if row.get("phrase") == "G2" and (row["defense"] or "none") != "none"
)
# 2. Flash-Lite errors
out["flash_lite"] = {
    "rows": len(lite),
    "with_error": sum(1 for row in lite if row.get("error")),
    "error_prefix": sorted({(row.get("error") or "")[:45] for row in lite}),
}
# 3. XAI hazard flips (Qwen Q8)
haz = [pair for pair in X["pairs"] if pair["condition"] == "g1_en" and pair["label"] == "STOP"]
k4 = sum(pair["painted"] == "GO" and pair["clean"] == "STOP" for pair in haz)
out["xai_hazard_flips"] = {
    "k": k4,
    "n": len(haz),
    "wilson95": wilson_interval(k4, len(haz)),
    "scenes": [pair["scene"] for pair in haz if pair["painted"] == "GO"],
    "restored_STOP": sum(pair["inpaint"] == "STOP" for pair in haz if pair["painted"] == "GO"),
    "model": X["painted_model"],
}
# 4. photos
conditions = GP["conditions"]
out["photos"] = {
    cond: {
        "k": conditions[cond]["causal"]["k"],
        "n": conditions[cond]["causal"]["n"],
        "ci": [conditions[cond]["causal"]["ci_low"], conditions[cond]["causal"]["ci_high"]],
    }
    for cond in conditions
}
out["photos_n_go"] = GP["gate"][0]["n_go"]
# 5. printed CIs, rounded OUTWARD (lower bound floored, upper bound ceiled) to the printed
# precision.


def outward(ci, dec):
    factor = 10**dec
    lo, hi = ci[0] * 100, ci[1] * 100
    lo_r = math.floor(lo * factor + 1e-9) / factor
    hi_r = math.ceil(hi * factor - 1e-9) / factor
    fmt = (lambda value: f"{value:.{dec}f}") if dec else (lambda value: f"{int(value)}")
    return {"raw_pct": [round(lo, 4), round(hi, 4)], "printed": f"{fmt(lo_r)}–{fmt(hi_r)}%"}


out["printed_ci"] = {
    "G1_pooled_1of80": outward(out["G1_pooled"]["wilson95"], 1),
    "xai_hazard_4of4": outward(out["xai_hazard_flips"]["wilson95"], 0),
    "photos_0of19": outward(out["photos"]["g1_en"]["ci"], 0),
}
# the other two XAI scenes (GO-labelled) for the poster text
out["xai_go_scenes_g1_en"] = [
    {
        "scene": pair["scene"],
        "label": pair["label"],
        "clean": pair["clean"],
        "painted": pair["painted"],
    }
    for pair in X["pairs"]
    if pair["condition"] == "g1_en" and pair["label"] == "GO"
]
Path("build").mkdir(exist_ok=True)
json.dump(out, open("build/derived_stats.json", "w"), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
