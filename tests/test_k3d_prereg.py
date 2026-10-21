"""cmame-paper Stage 12 (PREREG_K3D): the configuration names the records it
copies from and passes the run's own checks; the stamp script accepts only
the approved draft and verifies what it writes; the committed PREREG_K3D.md
is that draft or a verified stamp of the committed configuration; the
simulation record is the script's output, and every number the
pre-registration quotes from it, from Phase-2b's report, from CM2D's
verdict and return, and from the regression records is the record's; the
adjudicator's constants are the text's."""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "PREREG_K3D.md"
CONFIG = ROOT / "configs" / "k3d_v1.json"
SOURCE = ROOT / "records" / "wp8" / "e2" / "baseline" / "report_phase2b.json"
SIMS = ROOT / "records" / "cmame" / "k3d_sims.json"
sys.path.insert(0, str(ROOT / "src"))


def _script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


st = _script("stamp_prereg_k3d")


def _text() -> str:
    return " ".join(PREREG.read_text(encoding="utf-8").split())


def _sha(p) -> str:
    import hashlib

    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _pct(x: float, digits: int | None = None) -> str:
    """A share as the text writes it: one decimal when asked, else whole
    percent, with as many decimals as keep a share below 1 from reading 100%."""
    v = 100 * x
    if digits is not None:
        return f"{v:.{digits}f}%"
    d = 0
    while d < 3 and v < 100 and float(f"{v:.{d}f}") >= 100:
        d += 1
    return f"{v:.{d}f}%"


# --------------------------------------------------------- configuration --

def test_the_configuration_names_its_records_and_passes_the_runs_checks():
    from fejepa.analysis.holdout import load_spec

    cfg = json.loads(CONFIG.read_text())
    k3d = _script("k3d_train")
    assert cfg["source"] == {"report": "records/wp8/e2/baseline/report_phase2b.json",
                             "report_sha256": _sha(SOURCE),
                             "states_dir": "runs/phase2/e8_states"}
    rep = json.loads(SOURCE.read_text())
    d9 = rep["results"]["e8"]["metrics"]["d9_restart"]["ar_states"]
    assert cfg["reused"]["ar"]["sha256"] == {k[1:]: v["sha256"] for k, v in d9.items()}
    side = json.loads((ROOT / "records/wp9/phase2_supervised_states.json").read_text())["sha256"]
    assert cfg["reused"]["labels"]["sha256"] == {
        str(s): side[f"labels_b1024_s{s}.pt"] for s in (0, 1, 2)}
    assert cfg["train"] == {"row": "labels_knorm", "loss": "knorm", "budget": 1024,
                            "epochs": 200, "lr": 0.0015, "weight_decay": 0.0001, "clip": 1.0,
                            "warmup_frac": 0.05, "activation_checkpointing": False}
    assert cfg["seeds"] == [0, 1, 2] and cfg["content_tol"] == 0.001
    assert (cfg["out"], cfg["prereg_file"], cfg["prereg_guard"], cfg["device"]) == \
        ("runs/k3d/report.json", "PREREG_K3D.md", True, "cuda")
    assert cfg["holdout"] == {"spec": "configs/holdout_v1.json", "set": "h3d",
                              "dir": "runs/holdout/h3d"}
    h3d = load_spec(ROOT / cfg["holdout"]["spec"])["sets"]["h3d"]
    assert h3d["report_sha256"] == cfg["source"]["report_sha256"] and h3d["n_holdout"] == 686
    for r in ("ar", "labels"):
        assert h3d["rows"][r]["sha256"] == cfg["reused"][r]["sha256"]
        assert h3d["rows"][r]["state"] == f"{cfg['source']['states_dir']}/" \
                                          f"{cfg['reused'][r]['state']}"
    # the run's own checks, apart from the guard
    k3d.check_config(cfg)
    src = k3d.check_source(rep, cfg)
    k3d.check_records(rep, cfg)
    assert (src["budget"], src["epochs"], src["lr"], src["tf32"]) == (1024, 200, 0.0015, True)
    # the corpus the text names is the report's in-band corpus
    ds = rep["provenance"]["datasets"][0]
    assert f"manifest SHA-256 `{ds['manifest_sha256']}`" in _text()
    assert ds["n_instances"] == 2000 and rep["config"]["split"] == {"n_val": 256, "seed": 1}


# ---------------------------------------------------------------- stamp --

def _draft_text() -> str:
    text = PREREG.read_text(encoding="utf-8")
    m = re.search(r"\*\*Status:\*\* r1, stamped (.+?) before the run:", text)
    if m:
        text = text.replace(st.stamped_status(m.group(1)), st.DRAFT_STATUS)
    text = re.sub(r"^CONFIG_SHA256\[k3d_v1\] = [0-9a-f]{64}$",
                  "CONFIG_SHA256[k3d_v1] = <fill before tagging>", text, flags=re.M)
    return re.sub(r"^PREREG_K3D_SHA256 = [0-9a-f]{64}$", st.FOOTER_OPEN, text, flags=re.M)


def test_the_committed_file_is_the_draft_or_a_verified_stamp():
    from fejepa.report import config_sha256, read_prereg_entries

    text = PREREG.read_text(encoding="utf-8")
    entries = read_prereg_entries(PREREG)
    assert [lab for lab, _ in entries] == ["k3d_v1"]
    if entries[0][1] == "<fill before tagging>":
        assert text.count(st.DRAFT_STATUS) == 1 and text.rstrip("\n").endswith(st.FOOTER_OPEN)
    else:
        assert entries[0][1] == config_sha256(json.loads(CONFIG.read_text()))
        assert st.self_hash_ok(text) and st.DRAFT_STATUS not in text
        draft = _draft_text()
        assert draft != text and draft.count(st.DRAFT_STATUS) == 1
    # the draft the stamp script accepts is the revision the text names last
    rev = re.search(r"\*\*Status:\*\* (r\d+) DRAFT", st.DRAFT_STATUS).group(1)
    assert re.findall(r"\b(r\d+) \(\d+ \w+ 2026\)", text.split("Revision:", 1)[1])[-1] == rev
    assert f"this {rev} draft's" in text


def test_the_stamp_fills_the_draft_and_verifies(tmp_path):
    from fejepa.report import config_sha256, read_prereg_entries, verify_prereg

    p = tmp_path / "PREREG_K3D.md"
    p.write_text(_draft_text(), encoding="utf-8")
    res = st.stamp(p, CONFIG, "21 October 2026")
    cfg = json.loads(CONFIG.read_text())
    assert res["config_sha256"]["k3d_v1"] == config_sha256(cfg)
    text = p.read_text(encoding="utf-8")
    assert dict(read_prereg_entries(p))["k3d_v1"] == config_sha256(cfg)
    assert st.self_hash_ok(text) and st.stamped_status("21 October 2026") in text
    assert verify_prereg(cfg, p, label="k3d_v1") == config_sha256(cfg)
    a, b = _draft_text().splitlines(), text.splitlines()
    assert len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 3
    with pytest.raises(SystemExit, match="already stamped"):
        st.stamp(p, CONFIG, "21 October 2026")
    assert not st.self_hash_ok(text.replace("tau", "t"))


def test_the_stamp_refuses(tmp_path, capsys):
    p = tmp_path / "PREREG_K3D.md"
    for bad in ("08 October 2026", "October 21, 2026", "21 Oct 2026"):
        p.write_text(_draft_text(), encoding="utf-8")
        with pytest.raises(SystemExit, match="--date"):
            st.stamp(p, CONFIG, bad)
    p.write_text(_draft_text().replace("r1 DRAFT (20 October 2026)", "r0 DRAFT (19 October 2026)"),
                 encoding="utf-8")
    with pytest.raises(SystemExit, match="status line"):
        st.stamp(p, CONFIG, "21 October 2026")
    p.write_text(_draft_text() + "\nmore\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="last line"):
        st.stamp(p, CONFIG, "21 October 2026")
    p.write_text(_draft_text().replace("CONFIG_SHA256[k3d_v1]", "CONFIG_SHA256[k3d_v2]"),
                 encoding="utf-8")
    with pytest.raises(SystemExit, match="CONFIG_SHA256 lines"):
        st.stamp(p, CONFIG, "21 October 2026")
    # a configuration that fails the run's own checks: nothing written
    p.write_text(_draft_text(), encoding="utf-8")
    for edit in (("train", "lr", 0.001), ("train", "activation_checkpointing", None),
                 ("source", "report_sha256", "0" * 64), ("seeds", None, [0, 1, 7])):
        cfg = json.loads(CONFIG.read_text())
        if edit[1] is None:
            cfg[edit[0]] = edit[2]
        else:
            cfg[edit[0]][edit[1]] = edit[2]
        cp = tmp_path / "k3d_v1.json"
        cp.write_text(json.dumps(cfg))
        with pytest.raises(SystemExit) as ex:
            st.stamp(p, cp, "21 October 2026")
        assert ex.value.code == 3 and "STOP:" in capsys.readouterr().out, edit
        assert p.read_text(encoding="utf-8") == _draft_text()


# ------------------------------------------------------- quoted numbers --

def test_the_simulation_record_is_the_scripts_output():
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "k3d_sims.py"), "--check",
                          str(SIMS)], capture_output=True, text=True, cwd=ROOT, timeout=600)
    assert res.returncode == 0, res.stderr[-2000:]


def _seed_stats(cells, row, m):
    arrs = [np.asarray(e["per_instance"][m], float) for e in cells[row]["1024"]["per_seed_eval"]]
    means = [float(a.mean()) for a in arrs]
    meds = [float(np.median(a)) for a in arrs]
    cv = lambda v: float(np.std(v, ddof=1) / np.mean(v))          # noqa: E731
    return arrs, means, meds, cv(meds)


def test_the_simulation_constants_are_the_records():
    sims = _script("k3d_sims")
    cells = json.loads(SOURCE.read_text())["results"]["e8"]["metrics"]["cells"]
    for h, (row, m) in {"H2a-3D": ("labels", "energy_gap_rel"),
                        "H2b-3D": ("labels", "vm_rel_l2"),
                        "H3-3D": ("ar", "energy_gap_rel")}.items():
        assert round(_seed_stats(cells, row, m)[3], 2) == sims.REFS[h], h
    for m, vals in sims.MEANS.items():
        assert list(vals) == [float(f"{v:.5g}") for v in _seed_stats(cells, "labels", m)[1]], m
    cm2d = json.loads((ROOT / "records/cmame/cm2d/return/report.json").read_text())
    c2 = cm2d["results"]["e8"]["metrics"]["cells"]
    for h, m in (("H2a-3D", "energy_gap_rel"), ("H2b-3D", "vm_rel_l2")):
        assert round(_seed_stats(c2, "labels_knorm", m)[3], 2) == sims.LK_2D[h], h


def test_the_quoted_operating_characteristics_are_the_records():
    rec = json.loads(SIMS.read_text())
    med = rec["medians"]
    text = _text()
    news = (0.05, 0.10, 0.20, 0.30, 0.50)
    a = med["H2a-3D"]
    ka = [f"c_ref=0.10,c_new={c:.2f}" for c in news]
    assert ("a new arm reads lower beyond the guard in "
            + " / ".join(_pct(a[k]["r=1"]["lower"], 1) for k in ka)
            + " of trials at new-arm spreads of 5% / 10% / 20% / 30% / 50%") in text
    assert ("a true ratio of the arms' expected values of 0.8 is detected in "
            + " / ".join(_pct(a[k]["r=0.8"]["lower"]) for k in ka) + ", of 0.7 in "
            + " / ".join(_pct(a[k]["r=0.7"]["lower"]) for k in ka) + ", of 0.5 in "
            + " / ".join(_pct(a[k]["r=0.5"]["lower"]) for k in ka) + ".") in text
    b = med["H2b-3D"]
    kb = [f"c_ref=0.06,c_new={c:.2f}" for c in news]
    assert ("at the same new-arm spreads: "
            + " / ".join(_pct(b[k]["r=1"]["lower"], 1) for k in kb)
            + " without a true difference; "
            + " / ".join(_pct(b[k]["r=0.8"]["lower"]) for k in kb) + " at 0.8, "
            + " / ".join(_pct(b[k]["r=0.7"]["lower"]) for k in kb) + " at 0.7, "
            + " / ".join(_pct(b[k]["r=0.5"]["lower"]) for k in kb) + " at 0.5.") in text
    h3 = med["H3-3D"]
    k3 = [f"c_ref=0.23,c_new={c:.2f}" for c in news]
    assert ("the stiffness-norm transformer reads lower beyond the guard in "
            + " / ".join(_pct(h3[k]["r=1"]["lower"], 1) for k in k3)
            + " of trials and the label-free transformer lower in "
            + " / ".join(_pct(h3[k]["r=1"]["worse"], 1) for k in k3)) in text
    assert ("a ratio of 0.5 reads lower in "
            + " / ".join(_pct(h3[k]["r=0.5"]["lower"]) for k in k3)
            + ", a ratio of 2 reads the label-free transformer lower in "
            + " / ".join(_pct(h3[k]["r=2"]["worse"]) for k in k3)) in text
    lk = rec["medians_at_lk_2d_spread"]
    la, lb = lk["H2a-3D"]["c_ref=0.10,c_new=0.37"], lk["H2b-3D"]["c_ref=0.06,c_new=0.19"]
    assert (f"reads lower beyond the guard in {_pct(la['r=1']['lower'], 1)} (H2a-3D) and "
            f"{_pct(lb['r=1']['lower'], 1)} (H2b-3D) of trials") in text
    assert ("true ratios of 0.8 / 0.7 / 0.5 are detected in "
            + " / ".join(_pct(la[f"r={r}"]["lower"]) for r in ("0.8", "0.7", "0.5"))
            + " (H2a-3D) and "
            + " / ".join(_pct(lb[f"r={r}"]["lower"]) for r in ("0.8", "0.7", "0.5"))
            + " (H2b-3D)") in text
    sm = rec["seed_means_at_the_recorded_reference"]
    eg, vm = sm["energy_gap_rel"], sm["vm_rel_l2"]
    assert all(c["lower"] == 0 for row in eg["cells"].values() for c in row.values())
    assert f"SE_rel of the L_D reference alone is {eg['se_rel_of_the_reference_alone']:.3f}" \
        in text
    assert f"tau >= {eg['smallest_tau']:.2f}" in text and \
        f"tau >= {vm['smallest_tau']:.3f}" in text
    ranges = []
    for r in ("0.7", "0.6", "0.5"):
        v = [c[f"r={r}"]["lower"] for c in vm["cells"].values()]
        ranges.append(f"{100 * min(v):.0f}-{100 * max(v):.0f}%")
    assert ("reads lower in " + " / ".join(ranges) + " of trials over the same new-arm "
            "spreads") in text
    # the exploratory comparisons' chance rates span the cells quoted above
    fp = [x["r=1"][w] for h in ("H2a-3D", "H2b-3D", "H3-3D") for x in med[h].values()
          for w in ("lower", "worse")]
    assert (round(100 * min(fp)), round(100 * max(fp))) == (1, 17)
    assert "in about 1-17% of cases at the spreads of Sec. 4" in text


def test_the_reference_values_quoted_are_the_reports():
    cells = json.loads(SOURCE.read_text())["results"]["e8"]["metrics"]["cells"]
    text = _text()
    _, ar_g, ar_gmed, ar_cv = _seed_stats(cells, "ar", "energy_gap_rel")
    _, ar_v, _, _ = _seed_stats(cells, "ar", "vm_rel_l2")
    ld_arr, ld_g, ld_gmed, ld_gcv = _seed_stats(cells, "labels", "energy_gap_rel")
    ld_varr, ld_v, ld_vmed, ld_vcv = _seed_stats(cells, "labels", "vm_rel_l2")
    f = lambda v, d: " / ".join(f"{x:.{d}f}" for x in v)                # noqa: E731
    assert (f"seed means are {f(ar_g, 4)} in the relative energy gap (mean "
            f"{np.mean(ar_g):.4f}) and {f(ar_v, 4)} in the relative L2 von Mises error "
            f"({np.mean(ar_v):.4f})") in text
    assert (f"the L_D transformer's are {ld_g[0]:.3f} / {ld_g[1]:.2f} / {ld_g[2]:.3f} "
            f"({np.mean(ld_g):.1f}) and {f(ld_v, 3)} ({np.mean(ld_v):.3f})") in text
    i = int(np.argmax(ld_arr[1]))
    perm = np.random.default_rng(1).permutation(2000)
    assert (f"instance {i} of the split (`instance_{perm[i]:05d}.npz`), on which seed 1 has a "
            f"relative energy gap of {ld_arr[1][i]:,.0f} and a von Mises error of "
            f"{ld_varr[1][i]:.1f}; without it that seed's means are "
            f"{np.delete(ld_arr[1], i).mean():.3f} and {np.delete(ld_varr[1], i).mean():.3f}") \
        in text
    assert (f"{f(ld_gmed, 3)} for L_D's relative energy gap (coefficient of variation, sample "
            f"standard deviation over mean, {100 * ld_gcv:.1f}%), {f(ld_vmed, 3)} for its von "
            f"Mises error ({100 * ld_vcv:.1f}%), and {f(ar_gmed, 4)} for the label-free "
            f"transformer's relative energy gap ({100 * ar_cv:.1f}%)") in text
    n_ld = int(sum((a > 1).sum() for a in ld_arr))
    n_ar = int(sum((a > 1).sum() for a in _seed_stats(cells, "ar", "energy_gap_rel")[0]))
    assert n_ar == 0 and f"On {n_ld} of the 768 instance-seed pairs" in text
    _, le_g, _, _ = _seed_stats(cells, "labels_anchor", "energy_gap_rel")
    _, le_v, _, _ = _seed_stats(cells, "labels_anchor", "vm_rel_l2")
    g = lambda v: " / ".join(f"{x:.3g}" for x in v)                       # noqa: E731
    assert (f"seed means {g(le_g)} in the relative energy gap and {g(le_v)} in the von Mises "
            "error") in text


def test_the_two_dimensional_results_quoted_are_cm2ds():
    v = json.loads((ROOT / "records/cmame/cm2d/verdict.json").read_text())
    text = _text()
    a, b, h3 = v["H2a"], v["H2b"], v["H3"]
    assert a["verdict"] == b["verdict"] == "SUPPORTED"
    assert (f"seed means of the relative energy gap {a['new_mean']:.4f} against "
            f"{a['base_mean']:.4f}, rel = {100 * a['rel_change']:.1f}% with tau = "
            f"{100 * a['threshold']:.1f}%") in text
    assert (f"von Mises error {b['new_mean']:.3f} against {b['base_mean']:.3f}, "
            f"{100 * b['rel_change']:.1f}% with tau = {100 * b['threshold']:.1f}%") in text
    assert h3["reading"] == "no difference shown (within the guard)"
    assert f"(H3: {100 * h3['rel_change']:.1f}%, tau = {100 * h3['threshold']:.1f}%)" in text
    assert (f"lowered L_D's seed means by {-100 * a['rel_change']:.0f}% and "
            f"{-100 * b['rel_change']:.0f}% (Sec. 1), ratios of {1 + a['rel_change']:.2f} and "
            f"{1 + b['rel_change']:.2f}") in text


def test_the_regression_records_are_identical_and_name_their_trees():
    readme = (ROOT / "records/cmame/README.md").read_text()
    this = re.search(r"\| this side \| [^|]*`src` = tree `([0-9a-f]{40})` \|", readme).group(1)
    for commit in ("e672110", "99d3674"):
        rec = json.loads((ROOT / f"records/cmame/k3d/regression_phase2_{commit}.json")
                         .read_text())
        assert rec["identical"] is True and rec["config"] == "configs/phase2_v1.json"
        assert rec["this_src_tree"] == this
        for p in ("fresh", "restart"):
            rows = rec["rows"][p]
            assert set(rows) == {"labels", "labels_anchor", "mgn", "zero", "scale_aware_poly",
                                 "knn_field"}
            assert all(r["present"] and r["floats"] > 0 and r["differences"] == 0
                       for r in rows.values())
            assert rec["other_differences"][p]["outside_label_free_paths"] == []
        assert len(rec["state_files_identical"]) == 4 and \
            all(rec["state_files_identical"].values())
        assert not re.search(r"/(home|tmp|root)/", json.dumps(rec))
        got = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--verify", "--quiet",
                              f"{commit}^{{commit}}"], capture_output=True, text=True)
        if got.returncode == 0:
            tree = subprocess.run(["git", "-C", str(ROOT), "rev-parse", f"{commit}:src"],
                                  capture_output=True, text=True).stdout.strip()
            assert rec["other_src_tree"] == tree, commit
        assert f"`{commit}`" in _text()


def test_the_prereg_names_the_adjudicators_constants():
    adj = _script("adjudicate_k3d")
    text = _text()
    assert adj.TAG == "prereg-k3d" and "tag `prereg-k3d`" in text
    assert adj.LABEL == "k3d_v1" and "CONFIG_SHA256[k3d_v1]" in text
    assert adj.HYPOTHESES["H2a-3D"][:3] == ("labels_knorm", "labels", "energy_gap_rel")
    assert adj.HYPOTHESES["H2b-3D"][:3] == ("labels_knorm", "labels", "vm_rel_l2")
    assert adj.H3[:3] == ("labels_knorm", "ar", "energy_gap_rel")
    assert adj.TORCH == "2.12.1+cu130" and "other than 2.12.1+cu130" in text
    assert adj.GPU.endswith("RTX 5090") and "other than the RTX 5090" in text
    assert adj.BOOT_N == 2000 and "(2,000 resamples" in text
    assert str(adj.HOLDOUT_MANIFEST) == "records/cmame/holdout/return/h3d/manifest.json"
    assert f"`{adj.HOLDOUT_MANIFEST}`" in text
    from fejepa.analysis.adjudicate_w9 import GUARD_BAND, GUARD_K

    assert (GUARD_BAND, GUARD_K) == (0.10, 2.0) and "tau = max(10%, 2 x SE_rel)" in text
    k3d = _script("k3d_train")
    assert k3d.TAG == adj.TAG and k3d.GPU_FREE == 0.9 and "free (90% of its memory)" in text


def test_the_figures_added_after_the_first_reviews_are_the_records():
    from scipy import stats

    text = _text()
    rec = json.loads(SIMS.read_text())
    j = rec["joint_null_at_lk_2d_spread"]
    rhos = ("rho=0.95", "rho=0.5", "rho=0")
    assert ("correlated at 0.95 / 0.5 / 0 within an arm, a new arm at those spreads without a "
            "true difference in either reads at least one of the two lower beyond the guard in "
            + " / ".join(_pct(j[r]["either"], 1) for r in rhos) + " of trials and both in "
            + " / ".join(_pct(j[r]["both"], 1) for r in rhos)) in text
    w = rec["medians_at_wide_new_arm_spreads"]
    a = [w["H2a-3D"][f"c_ref=0.10,c_new={c}"]["r=1"]["lower"] for c in ("0.75", "1.00")]
    b = [w["H2b-3D"][f"c_ref=0.06,c_new={c}"]["r=1"]["lower"] for c in ("0.75", "1.00")]
    assert (f"reads lower beyond the guard in {_pct(a[0], 1)} and {_pct(a[1], 1)} of trials "
            f"(H2a-3D) and {_pct(b[0], 1)} and {_pct(b[1], 1)} (H2b-3D)") in text
    lo = stats.chi2.ppf(0.975, 2)
    hi = stats.chi2.ppf(0.025, 2)
    assert f"from about {np.sqrt(2 / lo):.2f} to {np.sqrt(2 / hi):.1f} times" in text
    # the robust statistics of the reference, and instance 107 in every stored row
    cells = json.loads(SOURCE.read_text())["results"]["e8"]["metrics"]["cells"]
    cv = lambda v: float(np.std(v, ddof=1) / np.mean(v))                 # noqa: E731
    got = {}
    for m in ("energy_gap_rel", "vm_rel_l2"):
        arrs, _, meds, _ = _seed_stats(cells, "labels", m)
        got[m] = (cv([stats.trim_mean(x, 0.1) for x in arrs]),
                  cv([float(np.exp(np.log(x).mean())) for x in arrs]),
                  cv([float(np.delete(x, 107).mean()) for x in arrs]), cv(meds))
    g, v = got["energy_gap_rel"], got["vm_rel_l2"]
    assert (f"10%-trimmed means {100 * g[0]:.1f}% and {100 * v[0]:.1f}%, geometric means "
            f"{100 * g[1]:.1f}% and {100 * v[1]:.1f}%, seed means without instance 107 "
            f"{100 * g[2]:.1f}% and {100 * v[2]:.1f}% (relative energy gap and von Mises "
            f"error), against the medians' {100 * g[3]:.1f}% and {100 * v[3]:.1f}%") in text
    i = int(np.argmax(_seed_stats(cells, "labels", "energy_gap_rel")[0][1]))
    assert i == 107
    for row, name, fmt in (("ar", "label-free", "{:.3f}"), ("labels_anchor", "labels+energy",
                                                              "{:.2f}"),
                           ("mgn", "graph network", "{:.2g}")):
        arrs = _seed_stats(cells, row, "energy_gap_rel")[0]
        assert all(int((x > x[107]).sum()) < 3 for x in arrs), row
        vals = " / ".join(fmt.format(float(x[107])) for x in arrs)
        assert f"{name} {vals}" in text, (row, vals)
    # CM2D's median reading
    v2 = json.loads((ROOT / "records/cmame/cm2d/verdict.json").read_text())
    med = {h: v2[h]["robustness"]["medians"] for h in ("H2a", "H2b", "H3")}
    assert (f"{100 * med['H2a']['rel_change']:.1f}% (tau {100 * med['H2a']['threshold']:.1f}%) "
            f"for H2a, {100 * med['H2b']['rel_change']:.1f}% "
            f"({100 * med['H2b']['threshold']:.1f}%) for H2b and "
            f"{100 * med['H3']['rel_change']:.1f}% ({100 * med['H3']['threshold']:.1f}%) "
            "for H3") in text
    # the share of the gap closed in two dimensions
    c2 = json.loads((ROOT / "records/cmame/cm2d/return/report.json").read_text())
    c2 = c2["results"]["e8"]["metrics"]["cells"]
    mean = lambda r: float(np.mean([e["vm_rel_l2"] for e in c2[r]["1024"]["per_seed_eval"]]))  # noqa: E731
    share = (mean("labels") - mean("labels_knorm")) / (mean("labels") - mean("ar"))
    assert f"on CM2D's seed means, {100 * share:.0f}% in the von Mises error" in text
