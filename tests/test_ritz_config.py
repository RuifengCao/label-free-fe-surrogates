"""cmame-paper Stage 14: configs/ritz_v1.json against the records. Every
record and report it names has the SHA-256 it gives; the holdout sets are
PREREG_HOLDOUT's, with the labels manifests its return carries (and that
PREREG_K3D's run read); the states it lists are the ones the records list
(Phase-2's supervised states in records/wp9/phase2_supervised_states.json and
configs/holdout_v1.json, PREREG_K3D's in its return); the sets' instance
lists are the records' (the validation splits by the split rule, the fine
set's first 256, the holdout sets by their names); every source the
baseline pairs with is on the set's corpus manifest and split, its
deterministic rows agree across reports and K3D's instance order is
Phase-2b's; and every record the enriched reading reads on this branch
resolves to three seeds' arrays of the set's length. The two wp9 reports
are read on the box (their SHA-256 are those of wp9-pool's records)."""

import importlib.util
import json
import re
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "ritz_v1.json"


def _script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cfg():
    from fejepa.analysis import ritz as R

    return R.load_config(CFG)


def _sha(p) -> str:
    from fejepa.analysis.ritz import sha256

    return sha256(ROOT / p)


def _paths(o, key_path="path", key_sha="sha256"):
    """Every (path, sha256) pair of a configuration block, recursively."""
    out = []
    if isinstance(o, dict):
        for kp, ks in (("path", "sha256"), ("report", "report_sha256"),
                       ("records_report", "records_report_sha256"), ("spec", "spec_sha256")):
            if kp in o and ks in o and isinstance(o[kp], str):
                out.append((o[kp], o[ks]))
        for v in o.values():
            out += _paths(v)
    elif isinstance(o, list):
        for v in o:
            out += _paths(v)
    return out


def test_every_record_has_its_sha256(cfg):
    pairs = _paths(cfg)
    assert len(pairs) >= 30
    for p, sha in pairs:
        if p.startswith("runs/"):                          # read on the box
            assert re.fullmatch(r"[0-9a-f]{64}", sha), p
            continue
        assert (ROOT / p).is_file(), p
        assert _sha(p) == sha, p
    assert cfg["out"] == "runs/ritz"


def test_the_holdout_sets_are_prereg_holdouts(cfg):
    from fejepa.analysis.holdout import holdout_names, load_spec

    hold = load_spec(ROOT / "configs" / "holdout_v1.json")
    k3d = json.loads((ROOT / "records/cmame/k3d/return/report.json").read_text())
    for name in ("h3d", "h2d"):
        s = cfg["baseline"]["sets"][name]
        assert s["set"] == name and s["n"] == hold["sets"][name]["n_holdout"]
        assert s["labels_dir"] == f"{hold['out']}/{name}"
        ev = json.loads((ROOT / f"records/cmame/holdout/return/{name}/eval.json").read_text())
        assert s["labels_manifest_sha256"] == ev["labels_manifest_sha256"]
        assert _sha(f"records/cmame/holdout/return/{name}/manifest.json") == \
            s["labels_manifest_sha256"]
        assert s["identity"]["manifest"] == f"records/cmame/holdout/return/{name}/manifest.json"
        with np.load(ROOT / s["identity"]["path"]) as z:
            assert [str(f) for f in z["files"]] == holdout_names(hold["sets"][name])
            assert np.all(z["pi_star"] < 0)
    assert k3d["holdout"]["labels_manifest_sha256"] == \
        cfg["baseline"]["sets"]["h3d"]["labels_manifest_sha256"]
    assert k3d["holdout"]["arrays_sha256"] == cfg["baseline"]["sets"]["h3d"]["paired"][1]["sha256"]


def test_the_states_are_the_records(cfg):
    arms = cfg["enriched"]["arms"]
    sup = json.loads((ROOT / "records/wp9/phase2_supervised_states.json").read_text())["sha256"]
    hold = json.loads((ROOT / "configs/holdout_v1.json").read_text())["sets"]["h3d"]["rows"]
    for arm, row in (("phase2b_labels", "labels"), ("phase2b_mgn", "mgn")):
        st = arms[arm]["states"]
        assert st["pattern"] == hold[row]["state"]
        for s, sha in st["sha256"].items():
            assert sha == sup[f"{row}_b1024_s{s}.pt"] == hold[row]["sha256"][s]
        assert arms[arm]["kind"] == hold[row]["kind"]
    k3d = json.loads((ROOT / "records/cmame/k3d/return/report.json").read_text())
    prov = (ROOT / "records/cmame/k3d/return/provenance.txt").read_text()
    st = arms["k3d_labels_knorm"]["states"]
    for s, sha in st["sha256"].items():
        assert k3d["per_seed"][f"s{s}"]["state"]["sha256"] == sha
        assert f"{sha}  {st['pattern'].format(seed=s)}" in prov
    rep = json.loads((ROOT / arms["phase2b"]["report"]).read_text())
    assert arms["phase2b"]["states"] == {"from": "d9", "dir": "runs/phase2/e8_states"}
    assert sorted(rep["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]) == \
        ["s0", "s1", "s2"]
    for arm in ("b_n1024", "s_n1024"):
        a = arms[arm]
        assert a["report"] == f"runs/w9/{arm}/report.json" and "2f35f2d" in a["report_source"]
        assert a["states"] == {"from": "d9", "dir": f"runs/w9/{arm}/e8_states"}
        assert a["sets"] == ["IB", "F2", "F5"] and a["appendix"] is True
    assert [k for k, v in arms.items() if v["appendix"]] == ["b_n1024", "s_n1024", "phase2b"]


def test_the_sets_are_the_records_instances(cfg):
    rb = _script("ritz_baseline")
    split = lambda n: [f"instance_{i:05d}.npz"                      # noqa: E731
                       for i in np.random.default_rng(1).permutation(n)[:256]]
    want = {"val3d": split(2000), "fine3d": [f"instance_{i:05d}.npz" for i in range(256)],
            "val2d": split(30000)}
    fields = json.loads((ROOT / "records/cmame/timing/fields/fields.json").read_text())
    assert [str(f).split("/")[-1] for f in fields["val"]["files"]] == want["val3d"]
    for name in rb.SETS:
        names = rb.set_names(cfg, name)
        assert len(names) == cfg["baseline"]["sets"][name]["n"] == len(set(names))
        if name in want:
            assert names == want[name], name


def test_the_paired_sources_are_on_each_sets_instances(cfg):
    rb = _script("ritz_baseline")
    counts = {}
    for name in rb.SETS:
        rec, checks = rb.paired_records(cfg, name)
        n = cfg["baseline"]["sets"][name]["n"]
        for label, seeds in rec.items():
            assert seeds and all(len(sd[f]) == n for _, sd in seeds for f in rb.R.FIELDS), label
        counts[name] = (sorted(rec), checks)
    v3, c3 = counts["val3d"]
    assert "k3d:labels_knorm@1024" in v3 and "phase2b:ar@1024" in v3
    assert set(c3) == {"identity_order", "k3d:order_row:ar"}
    assert c3["k3d:order_row:ar"]["max_rel_diff"] == 0.0
    assert c3["identity_order"] == {"against": "cells:ar:1024", "seeds": [0, 1, 2],
                                    "max_rel_diff": 0.0}
    assert len(v3) == 26                                     # E2's reports carry ar only
    f3, cf = counts["fine3d"]
    assert "phase2b:ar (zero-shot)" in f3 and "phase2b:labels@max (zero-shot)" in f3
    assert len(f3) == 11                                    # the naive rows: Phase-2b's only
    assert cf == {"identity_order": {"against": "p3:ar", "seeds": [0, 1, 2],
                                     "max_rel_diff": 0.0}}
    assert counts["h3d"][0] == ["k3d:labels_knorm", "r1:ar", "r1:labels", "r1:mgn"]
    assert counts["h2d"][0] == ["r1:ar", "r1:labels", "r1:labels_knorm", "r1:mgn"]
    v2, c2 = counts["val2d"]
    assert {"cm2d:labels_knorm@1024", "e1_base:ar@1024", "july:ar@1024"} <= set(v2)
    assert not any(k.startswith(("b_n", "s_n", "c1_")) for k in v2)
    assert c2["zero@16"]["reports"] == ["cm2d", "july", "diag"]
    assert all(c["max_rel_diff"] <= 1e-9 for c in c2.values()) and len(c2) >= 8
    assert c2["e1_base:order_row:ar"] == {"max_rel_diff": 0.0}    # E1's states, CM2D's split


def test_the_enriched_records_resolve(cfg):
    ec = _script("enriched_cstar")
    for arm in ("phase2b", "phase2b_labels", "phase2b_mgn", "k3d_labels_knorm"):
        rep = json.loads((ROOT / cfg["enriched"]["arms"][arm]["report"]).read_text())
        assert ec.arm_seeds(rep) == [0, 1, 2]
        for sname in cfg["enriched"]["arms"][arm]["sets"]:
            cells = ec.record_cells(cfg, arm, rep, sname)
            target = ec.precheck_target(cfg, arm, sname)
            if cells is None:
                assert (arm, sname, target) == ("k3d_labels_knorm", "fine3d", "val3d")
                cells = ec.record_cells(cfg, arm, rep, target)
            else:
                assert target == sname
            n = cfg["enriched"]["sets"][target]["n"]
            assert len(cells) == 3 and all(len(c["metrics"][f]) == n for c in cells
                                           for f in ec.R.FIELDS), (arm, sname)
    sets = cfg["enriched"]["sets"]
    assert [k for k, v in sets.items() if v["inband"]] == ["IB", "val3d"]
    assert {k: v["n"] for k, v in sets.items()} == {"IB": 2048, "F2": 256, "F5": 256,
                                                     "val3d": 256, "fine3d": 256}
