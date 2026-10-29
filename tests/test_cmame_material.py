"""The manuscript (paper/cmame): its tables, figures and in-text numbers are
generated from the committed records only and reproduce byte for byte; the
numbers agree with the records when recomputed independently; the text carries
no hand-typed result; the design constants it states match the configurations
and the code; the statements of its Section 3 hold on assembled instances; it
names no journal to which it was submitted before; and the manuscript and its
supplementary material compile."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import statistics
import subprocess
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper" / "cmame"
OUT = PAPER / "generated"
TEXT = ("table_2d.tex", "table_2djuly.tex", "table_3d.tex", "table_label_efficiency.tex",
        "table_label_efficiency_july.tex", "table_transfer.tex", "table_criteria.tex",
        "table_cm2d.tex", "table_amplitude.tex", "table_remesh.tex", "table_e2.tex",
        "table_e1.tex", "table_cost.tex", "table_k3d.tex", "table_holdout.tex",
        "table_holdout_values.tex", "table_ritz_pairs.tex", "table_k3d_medians.tex",
        "table_k3d_comparisons.tex", "table_claims.tex", "numbers.tex", "hashes.tex",
        "material.md", "sources.json")
FIGS = ("fig_disp_vs_stress.pdf", "fig_energy_gap.pdf", "fig_label_efficiency.pdf",
        "fig_e2_cost_accuracy.pdf", "fig_spectra.pdf", "fig_field2d.pdf", "fig_field_worst.pdf",
        "fig_field_median.pdf", "fig_field_fine.pdf", "fig_norm_labels.pdf")
R2D = ROOT / "records" / "phase1" / "report_rec8_v2.json"
RDIAG = ROOT / "records" / "phase1" / "report_diag.json"
RWP2 = ROOT / "records" / "phase1" / "report_wp2_e2.json"
R3D = ROOT / "records" / "wp8" / "e2" / "baseline" / "report_phase2b.json"
RCM = ROOT / "records" / "cmame" / "cm2d" / "return" / "report.json"
VCM = ROOT / "records" / "cmame" / "cm2d" / "verdict.json"
SPEC = ROOT / "records" / "cmame" / "spectra" / "export"
FLD = ROOT / "records" / "cmame" / "timing" / "fields"
RK3 = ROOT / "records" / "cmame" / "k3d" / "return" / "report.json"
VK3 = ROOT / "records" / "cmame" / "k3d" / "verdict.json"
HOLD = ROOT / "records" / "cmame" / "holdout"
RITZ = ROOT / "records" / "cmame" / "ritz" / "return"
TAGS = {"ar": "Free", "labels": "Lab", "labels_knorm": "Knorm", "mgn": "Mgn"}


def _mod():
    spec = importlib.util.spec_from_file_location(
        "make_cmame_material", ROOT / "scripts" / "make_cmame_material.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def built():
    return _mod().build()


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _f(s: str) -> float:
    """A macro's numeric value (thousands separators, %, typographic minus removed)."""
    return float(s.replace(",", "").replace("%", "").replace("\u2212", "-"))


# ------------------------------------------------------------------ records
def test_phase1_records_match_their_provenance():
    readme = (ROOT / "records" / "phase1" / "README.md").read_text(encoding="utf-8")
    for p in (R2D, RDIAG, RWP2):
        assert f"`{p.name}` | `{_sha(p)}`" in readme, p.name
    # the deciding run's and the WP2/E2 run's reports are the ones the provenance note
    # attests (Runs 1 and 3)
    prov = re.sub(r"\s+", "", (ROOT / "PROVENANCE_NOTE.md").read_text(encoding="utf-8"))
    assert _sha(R2D) in prov and _sha(RWP2) in prov
    for p, cfg in ((R2D, "62b26ad868d424ef5527c8cb7d826c818aa1ba5cebbc76c7bfe665062781f0ce"),
                   (RDIAG, "1a85eeabf2646568e8ac17f3119abe980f56852cf44b05b684b72fa3d1619b78"),
                   (RWP2, "60088135b1fecb2768d882ad6fee37add0fc3463160decee98a34b511159cb2c")):
        assert json.loads(p.read_bytes())["provenance"]["config_sha256"] == cfg


# ------------------------------------------------------------------ regeneration
def test_material_regenerates_byte_for_byte(built):
    files = built["files"]
    assert set(files) == set(TEXT)
    for name, text in files.items():
        assert (OUT / name).read_text(encoding="utf-8") == text, name
    for name in FIGS:
        assert (OUT / name).stat().st_size > 1000, name


def test_sources_name_every_record_read(built):
    src = json.loads(built["files"]["sources.json"])["inputs_sha256"]
    for p in (R2D, RDIAG, RWP2, R3D, ROOT / "records" / "wp8" / "posthoc" / "amp_phase2b.json",
              ROOT / "DEVIATIONS_PHASE2.md", RCM, VCM, SPEC / "spectra.json",
              SPEC / "spectra_val.npz", SPEC / "fig2d.npz", FLD / "fields.json",
              FLD / "energies_val.npz", FLD / "fig5.npz", FLD / "fig6.npz", FLD / "fig7.npz",
              ROOT / "scripts" / "adjudicate_cm2d.py", RK3, VK3, HOLD / "verdict.json",
              *(HOLD / "return" / s / f for s in ("h3d", "h2d")
                for f in ("eval.json", "eval_arrays.npz", "manifest.json")),
              HOLD / "return" / "status.txt", RITZ / "status.txt", RITZ / "machine.txt",
              ROOT / "records" / "cmame" / "ritz" / "ritz_return_20261029-1150.tgz",
              *(RITZ / "baseline" / s / "summary.json"
                for s in ("val3d", "fine3d", "h3d", "val2d", "h2d")),
              *(RITZ / "timing" / f for f in ("timing_2d.json", "timing_3d.json",
                                               "ritz_timing_2d.json", "ritz_timing_3d.json")),
              ROOT / "records" / "cmame" / "timing" / "timing_3d.json",
              ROOT / "configs" / "holdout_v1.json", ROOT / "configs" / "k3d_v1.json",
              ROOT / "configs" / "ritz_v1.json"):
        rel = str(p.relative_to(ROOT))
        assert src[rel] == _sha(p), rel


# ------------------------------------------------------------------ numbers
def _cells(r):
    return r["results"]["e8"]["metrics"]["cells"]


def _seeds(r, arm, metric, b="1024"):
    c = _cells(r)[arm]
    return c[b if b in c else max(c, key=int)][metric]["per_seed"]


def _inst(r, arm, metric, b="1024"):
    c = _cells(r)[arm]
    return np.array([e["per_instance"][metric]
                     for e in c[b if b in c else max(c, key=int)]["per_seed_eval"]])


def test_numbers_agree_with_the_records(built):
    N = built["numbers"]
    r2, r3 = json.loads(R2D.read_bytes()), json.loads(R3D.read_bytes())
    rc = json.loads(RCM.read_bytes())
    for dim, r in (("Two", r2), ("Cm", rc), ("Three", r3)):
        for arm, tag in (("ar", "Free"), ("labels", "Lab"), ("labels_anchor", "Anc"),
                         ("labels_knorm", "Knorm"), ("mgn", "Mgn")):
            if arm not in _cells(r):
                continue
            for m, mt in (("disp_rel_l2", "Disp"), ("energy_gap_rel", "Gap"),
                          ("vm_rel_l2", "Vm"), ("peak_vm_rel_err", "Peak")):
                assert _f(N[f"num{dim}{tag}{mt}"]) == pytest.approx(
                    statistics.fmean(_seeds(r, arm, m)), rel=5e-3), (dim, arm, m)
            g = _inst(r, arm, "energy_gap_rel")
            assert _f(N[f"num{dim}{tag}Worse"]) == int((g > 1).sum())
    # the headline ratios and per-instance comparisons of Sections 6.1 and 7.1
    vm = statistics.fmean(_seeds(r3, "mgn", "vm_rel_l2")) / statistics.fmean(
        _seeds(r3, "ar", "vm_rel_l2"))
    assert _f(N["numThreeMgnOverFreeVm"]) == pytest.approx(vm, abs=0.05)
    # the ratio of relative energy gaps for the energy-norm error: the square root of
    # the ratio of the means of g over every seed and instance, which is the ratio of the
    # root-mean-square relative energy-norm errors (equal load cases per instance)
    rms = np.sqrt(_inst(r3, "labels_anchor", "energy_gap_rel").mean()
                  / _inst(r3, "ar", "energy_gap_rel").mean())
    assert _f(N["numThreeAncOverFreeGapRoot"]) == pytest.approx(rms, abs=0.05)
    assert _f(N["numThreeAncOverFreeGapRoot"]) ** 2 == pytest.approx(
        _f(N["numThreeAncOverFreeGap"]), rel=0.03)
    # Section 6.1, read after the run: the noise guard of the two-dimensional comparison
    # applied to the label-free transformer against the two supervised transformers
    within = []
    for arm in ("labels", "labels_anchor"):
        for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err",
                  "crit_recall"):
            a, b = np.array(_seeds(r3, "ar", m)), np.array(_seeds(r3, arm, m))
            rel = a.mean() / b.mean() - 1
            se = np.sqrt(a.var(ddof=1) / 3 + b.var(ddof=1) / 3) / b.mean()
            if abs(rel) <= max(0.1, 2 * se):
                within.append((arm, m))
    assert within == [("labels", "energy_gap_rel"), ("labels", "peak_vm_rel_err"),
                      ("labels_anchor", "crit_recall")]
    assert (N["numThreeGuardWithin"], N["numThreeGuardTotal"]) == ("three", "ten")
    assert _f(N["numMgnVmHigher"]) == int((_inst(r3, "mgn", "vm_rel_l2")
                                          > _inst(r3, "ar", "vm_rel_l2")).sum())
    lab = _inst(r3, "labels", "energy_gap_rel")
    assert int(N["numWorstIndex"]) == int(np.argmax(lab[0])) == int(np.argmax(lab[1]))
    assert _f(N["numThreeLabWorst"]) == pytest.approx(lab.max(), abs=0.5)
    # the 2D deciding run's kill records
    e7 = r2["results"]["e7"]["metrics"]["iterations_to_tol_mean"]
    assert _f(N["numKfiveZero"]) == pytest.approx(e7["zero"], abs=0.05)
    assert _f(N["numKfiveFree"]) == pytest.approx(e7["learned"], abs=0.05)


def _pct(s: str) -> float:
    return _f(s) / 100


def test_cm2d_numbers_agree_with_the_report_and_the_verdict(built):
    """The numbers of Sections 5.2 and 6.2: the pre-registered verdicts as the stamped adjudicator wrote
    them, and the pairs, counts and ratios recomputed from the report's arrays."""
    N, rc = built["numbers"], json.loads(RCM.read_bytes())
    v = json.loads(VCM.read_bytes())
    for h, H in (("H1", "One"), ("H2a", "TwoA"), ("H2b", "TwoB"), ("H3", "Three")):
        assert _pct(N[f"numH{H}Rel"]) == pytest.approx(abs(v[h]["rel_change"]), abs=5e-4)
        assert _pct(N[f"numH{H}Tau"]) == pytest.approx(v[h]["threshold"], abs=5e-4)
    assert [v[h]["verdict"] for h in ("H1", "H2a", "H2b")] == ["SUPPORTED"] * 3
    assert v["H3"]["reading"].startswith("no difference shown")
    mean = lambda arm, m: statistics.fmean(_seeds(rc, arm, m))          # noqa: E731
    assert v["H1"]["new_mean"] == pytest.approx(mean("ar", "energy_gap_rel"), rel=1e-12)
    assert v["H2b"]["new_mean"] == pytest.approx(mean("labels_knorm", "vm_rel_l2"), rel=1e-12)
    # per instance-seed pair
    for a, b, key, m in (("ar", "labels", "PairCmLabGap", "energy_gap_rel"),
                         ("ar", "labels", "PairCmLabDisp", "disp_rel_l2"),
                         ("labels_knorm", "labels", "PairCmKnormLabVm", "vm_rel_l2"),
                         ("labels_knorm", "labels", "PairCmKnormLabDisp", "disp_rel_l2")):
        share = float((_inst(rc, a, m) < _inst(rc, b, m)).mean())
        assert _pct(N[f"num{key}"]) == pytest.approx(share, abs=5e-4), key
    # opposite rankings by the two errors, in either order
    lab_vm, ar_vm = _inst(rc, "labels", "vm_rel_l2"), _inst(rc, "ar", "vm_rel_l2")
    lab_d, ar_d = _inst(rc, "labels", "disp_rel_l2"), _inst(rc, "ar", "disp_rel_l2")
    opp = ((ar_vm < lab_vm) & (lab_d < ar_d)) | ((lab_vm < ar_vm) & (ar_d < lab_d))
    assert _pct(N["numPairCmOpposite"]) == pytest.approx(float(opp.mean()), abs=5e-4)
    # the energy-norm-supervised transformer against the label-free one, and the graph network
    # against the supervised transformer, pair by pair ("none" when no pair)
    for a, b, key in (("labels_knorm", "ar", "KnormFree"), ("mgn", "labels", "MgnLab")):
        for m, mt in (("energy_gap_rel", "Gap"), ("vm_rel_l2", "Vm"), ("disp_rel_l2", "Disp")):
            share = float((_inst(rc, a, m) < _inst(rc, b, m)).mean())
            got = N[f"numPairCm{key}{mt}"]
            assert (share == 0) if got == "none" else (
                _pct(got) == pytest.approx(share, abs=5e-4)), (key, m)
    w256 = _inst(rc, "ar", "energy_gap_rel") < _inst(rc, "labels_knorm", "energy_gap_rel", "256")
    assert _pct(N["numPairCmFreeKnormGapTwoFiveSix"]) == pytest.approx(float(w256.mean()),
                                                                       abs=5e-4)
    for arm, A in (("labels", "Lab"), ("labels_knorm", "Knorm")):
        for b, B in (("16", "Sixteen"), ("64", "SixtyFour"), ("256", "TwoFiveSix")):
            assert int(N[f"numCm{A}Worse{B}"]) == int((_inst(rc, arm, "energy_gap_rel", b)
                                                       > 1).sum())
    assert _f(N["numCmLabOverFreeVm"]) == pytest.approx(
        mean("labels", "vm_rel_l2") / mean("ar", "vm_rel_l2"), abs=0.05)
    assert _pct(N["numCmFreeDispExcessAbs"]) == pytest.approx(
        mean("ar", "disp_rel_l2") / mean("labels", "disp_rel_l2") - 1, abs=5e-4)
    ex = [a / b - 1 for a, b in zip(_seeds(rc, "ar", "disp_rel_l2"),
                                    _seeds(rc, "labels", "disp_rel_l2"), strict=True)]
    assert (_pct(N["numCmFreeDispExcessMin"]), _pct(N["numCmFreeDispExcessMax"])) == (
        pytest.approx(min(ex), abs=5e-3), pytest.approx(max(ex), abs=5e-3))
    assert min(ex) > 0
    # the graph network: lowest displacement error, by little against the supervised one
    below = 1 - mean("mgn", "disp_rel_l2") / mean("labels", "disp_rel_l2")
    assert _pct(N["numCmMgnBelowLabDisp"]) == pytest.approx(below, abs=5e-3)
    assert 0 < below < 0.1
    # H3: seeds 0 and 2 alone; the instance-resampling interval of the verdict
    kg, fg = _seeds(rc, "labels_knorm", "energy_gap_rel"), _seeds(rc, "ar", "energy_gap_rel")
    z2 = statistics.fmean(kg[::2]) / statistics.fmean(fg[::2]) - 1
    assert _pct(N["numHThreeSeedsZeroTwo"]) == pytest.approx(-z2, abs=5e-4) and z2 < 0
    ir = v["H3"]["robustness"]["instance_resampling_95"]
    assert (_pct(N["numHThreeResLow"]), _pct(N["numHThreeResHigh"])) == (
        pytest.approx(-ir["high"], abs=5e-4), pytest.approx(-ir["low"], abs=5e-4))
    # H2a's ratio of the seed means, and the number of secondary readings (16 per metric)
    assert _f(N["numCmLabOverKnormGap"]) == pytest.approx(
        mean("labels", "energy_gap_rel") / mean("labels_knorm", "energy_gap_rel"), abs=5e-3)
    # the same comparisons for the root-mean-square relative energy-norm error
    assert _pct(N["numHTwoARootRel"]) == pytest.approx(
        1 - np.sqrt(mean("labels_knorm", "energy_gap_rel") / mean("labels", "energy_gap_rel")),
        abs=5e-4)
    assert _f(N["numCmLabOverFreeGapRoot"]) == pytest.approx(
        np.sqrt(mean("labels", "energy_gap_rel") / mean("ar", "energy_gap_rel")), abs=0.05)
    assert int(N["numCmSecondary"]) == 5 * (4 * 3 + 2 * 2)
    # the solves: 256 validation and 1,024 training instances, four load cases each
    assert (_f(N["numCmSolvesVal"]), _f(N["numCmSolvesTrain"]), _f(N["numCmSolves"])) == (
        1024, 4096, 5120)


def _spectral():
    z = np.load(SPEC / "spectra_val.npz")
    rows = [str(r) for r in z["rows"]]
    rho = (z["eK"] / z["e2"]) / (z["uK_star"] / z["u2_star"])[None, None]
    d2 = z["e2"] / z["u2_star"][None, None]
    g = z["eK"] / z["uK_star"][None, None]           # from the error norms, not the energies
    return z, rows, rho, d2, g


def test_spectral_readings_follow_from_the_per_load_arrays(built):
    """Section 5.3's readings recomputed from the export's per-load-case norms and
    binned spectra, independently of the generator (the shares from the bins of the
    eigenvalue over R(U*) on edges 10^(-2 + k/8): modes at or above 10^2 R(U*) are in
    bins 33 and above, at or above 10^4 in 49 and above)."""
    N = built["numbers"]
    z, rows, rho, d2, g = _spectral()
    assert np.allclose(g, z["rel"], rtol=1e-6, atol=0)        # Lemma 1, energies vs norms
    assert np.allclose(rho * d2, z["rel"], rtol=1e-8, atol=0)  # eq:factor, against the energies
    for i, r in enumerate(rows):
        assert _f(N[f"numSpecRq{TAGS[r]}"]) == pytest.approx(float(np.median(rho[i])), rel=5e-3)
        sk = z["SK_log"][i]
        share = np.median(sk[..., 33:].sum(-1) / sk.sum(-1))
        assert _pct(N[f"numSpecShareK{TAGS[r]}"]) == pytest.approx(share, abs=5e-3), r
        s2 = z["S2_log"][i]
        share2 = np.median(s2[..., 25:].sum(-1) / s2.sum(-1))
        assert _pct(N[f"numSpecShareEuc{TAGS[r]}"]) == pytest.approx(
            share2, abs=5e-4 if share2 < 0.095 else 5e-3), r
        assert int(N[f"numSpecLoadWorse{TAGS[r]}"]) == int((z["pi"][i] > 0).sum())
        assert np.array_equal(z["pi"][i] > 0, z["eK"][i] > z["uK_star"])   # Corollary 4
        assert not (z["rel_c"][i] > 1).any()
        tf = np.median(z["dK_tf32"][i] / z["eK"][i])
        assert _pct(N[f"numSpecTf{TAGS[r]}"]) == pytest.approx(tf, rel=0.05, abs=5e-5), r
    star = z["SK_log_star"]
    assert _pct(N["numSpecShareKStar"]) == pytest.approx(
        np.median(star[..., 33:].sum(-1) / star.sum(-1)), abs=5e-4)
    gm = lambda x: float(np.exp(np.mean(np.log(x))))                   # noqa: E731
    for a, b, key in (("labels", "labels_knorm", "LabKnorm"), ("labels_knorm", "ar", "KnormFree"),
                      ("mgn", "labels", "MgnLab")):
        ia, ib = rows.index(a), rows.index(b)
        assert _f(N[f"numSpec{key}Rq"]) == pytest.approx(gm(rho[ia] / rho[ib]), abs=6e-3)
        assert _f(N[f"numSpec{key}Disp"]) == pytest.approx(gm(d2[ia] / d2[ib]), abs=6e-3)
        assert _f(N[f"numSpec{key}Gap"]) == pytest.approx(gm(g[ia] / g[ib]), abs=6e-3)
        assert _pct(N[f"numSpec{key}Above"]) == pytest.approx(
            float((rho[ia] > rho[ib]).mean()), abs=5e-4)
    ia, ib = rows.index("labels"), rows.index("labels_knorm")
    per_seed = [gm(rho[ia][s] / rho[ib][s]) for s in range(3)]
    assert N["numSpecLabKnormRqSeeds"] == f"{per_seed[0]:.2f}, {per_seed[1]:.2f} and " \
                                          f"{per_seed[2]:.2f}"
    share = np.log(gm(rho[ia] / rho[ib])) / np.log(gm(g[ia] / g[ib]))
    assert _pct(N["numSpecSpectralShare"]) == pytest.approx(share, abs=5e-3)
    # the stress bound (plane stress, area-weighted) on every load case
    ratio = z["vm_area"] ** 2 / ((1 + z["gamma_star"])[None, None] * g)
    assert ratio.max() <= 1 and _f(N["numSpecBoundMax"]) == pytest.approx(ratio.max(), abs=5e-3)


def test_field_readings_follow_from_the_per_load_arrays(built):
    """The post hoc readings of Sections 5.3 and 7 recomputed from the three-dimensional export."""
    N = built["numbers"]
    z = np.load(FLD / "energies_val.npz")
    arms = [str(a) for a in z["arms"]]
    rho = (z["eK"] / z["e2"]) / (z["uK_star"] / z["u2_star"])[None, None]
    g = z["eK"] / z["uK_star"][None, None]
    assert np.allclose(g, z["rel"], rtol=1e-6, atol=0)
    for i, a in enumerate(arms):
        assert _f(N[f"numFieldRq{TAGS[a]}"]) == pytest.approx(float(np.median(rho[i])), rel=5e-3)
        assert int(N[f"numFieldLoadWorse{TAGS[a]}"]) == int((z["pi"][i] > 0).sum())
        assert np.array_equal(z["pi"][i] > 0, z["eK"][i] > z["uK_star"])  # Corollary 4
        assert not (z["rel_c"][i] > 1).any() and (z["rel_c"][i] <= z["rel"][i] * (1 + 1e-9)).all()
        for key, M in (("vm_vol", "VmVol"), ("vm_elem", "VmElem")):
            assert _f(N[f"numField{M}{TAGS[a]}"]) == pytest.approx(float(np.median(z[key][i])),
                                                                    rel=5e-3)
        if a != "ar":
            assert _pct(N[f"numFieldRqAbove{TAGS[a]}"]) == pytest.approx(
                float((rho[i] > rho[0]).mean()), abs=5e-4)
    assert int(N["numFieldLoadWorseFree"]) == int(N["numThreeFreeLoadWorse"])
    ratio = z["vm_vol"] ** 2 / ((1 + z["gamma_star"])[None, None] * g)
    assert ratio.max() <= 1 and _f(N["numFieldBoundMax"]) == pytest.approx(ratio.max(), abs=5e-3)


def test_field_plots_show_the_instances_and_load_cases_of_their_rules(built):
    """The instance of each field plot is the one its rule selects from the reports, and
    the load case the one the same rule selects within it (written independently here)."""
    N = built["numbers"]
    names3 = ("downward traction on the end face", "axial traction on the end face",
              "shear traction on the top face", "downward body force")
    names2 = ("downward traction on the end edge", "axial traction on the end edge",
              "shear traction on the top edge", "downward body force")
    lower_median = lambda v: int(sorted(range(len(v)), key=lambda k: (v[k], k))[(len(v) - 1) // 2])  # noqa: E731,E501
    f5, f6, f7 = (np.load(FLD / f"{f}.npz") for f in ("fig5", "fig6", "fig7"))
    f2 = np.load(SPEC / "fig2d.npz")
    assert N["numFigWorstLoad"] == names3[int(np.argmax(f5["rel_labels"]))]
    assert N["numFigMedianLoad"] == names3[lower_median(list(f6["rel_ar"]))]
    d7 = np.linalg.norm(f7["U_ar"] - f7["U_star"], axis=1) / np.linalg.norm(f7["U_star"], axis=1)
    assert N["numFigFineLoad"] == names3[lower_median(list(d7))]
    assert N["numFigTwoDLoad"] == names2[lower_median(list(f2["rel_labels"]))]
    # the instances: the 2D figure's from CM2D's report, the 3D worst one from Phase-2b's
    rc, r3 = json.loads(RCM.read_bytes()), json.loads(R3D.read_bytes())
    lab = _inst(rc, "labels", "energy_gap_rel")[0]
    assert int(N["numSpecFigIndex"]) == lower_median(list(lab))
    sj = json.loads((SPEC / "spectra.json").read_bytes())
    assert sj["selections"]["fig2d"]["index"] == int(N["numSpecFigIndex"])
    fj = json.loads((FLD / "fields.json").read_bytes())
    assert fj["selections"]["fig5"]["index"] == int(N["numWorstIndex"]) == int(
        np.argmax(_inst(r3, "labels", "energy_gap_rel")[0]))
    # the figure files carry those instances' per-load arrays (seed 0)
    sv, ev = np.load(SPEC / "spectra_val.npz"), np.load(FLD / "energies_val.npz")
    k2, k5 = int(N["numSpecFigIndex"]), int(N["numWorstIndex"])
    assert np.allclose(f2["rel_labels"],
                       sv["rel"][[str(r) for r in sv["rows"]].index("labels"), 0, k2], rtol=1e-12)
    assert np.allclose(f5["rel_labels"],
                       ev["rel"][[str(a) for a in ev["arms"]].index("labels"), 0, k5], rtol=1e-12)


def _nums(s: str) -> list:
    """The numbers of an 'a, b and c' macro."""
    return [_f(x) for x in re.split(r", | and ", s)]


def _gm(x) -> float:
    return float(np.exp(np.mean(np.log(np.asarray(x, dtype=float)))))


def test_every_quoted_spectral_reading_is_recomputed(built):
    """The spectral readings not recomputed above: TF32 off, the rounding in the stiff
    modes, per seed, on the seed geometric means, the counts, the solution's quotient and
    the area- and element-weighted von Mises errors."""
    N = built["numbers"]
    z, rows, rho, d2, g = _spectral()
    i = {r: rows.index(r) for r in rows}
    assert int(_f(N["numSpecLoads"])) == rho[i["ar"]].size == 3 * 256 * 4
    assert int(_f(N["numSpecLoadCases"])) == 256 * 4
    rq = z["uK_star"] / z["u2_star"]
    assert _f(N["numSpecRqStarOverMin"]) == pytest.approx(
        float(np.median(rq / z["lam_min"][:, None])), abs=5e-3)
    assert (int(_f(N["numSpecFreeMin"])), int(_f(N["numSpecFreeMax"]))) == (
        int(z["n_free"].min()), int(z["n_free"].max()))
    # TF32 off
    rho_i = (z["eK_ieee"] / z["e2_ieee"]) / rq[None, None]
    g_i = z["eK_ieee"] / z["uK_star"][None, None]
    for r in rows:
        assert _f(N[f"numSpecIeeeRq{TAGS[r]}"]) == pytest.approx(
            float(np.median(rho_i[i[r]])), rel=5e-3), r
    a, b, k = i["labels"], i["labels_knorm"], i["ar"]
    assert _f(N["numSpecIeeeLabKnormRq"]) == pytest.approx(_gm(rho_i[a] / rho_i[b]), abs=6e-3)
    assert _f(N["numSpecIeeeLabKnormGap"]) == pytest.approx(_gm(g_i[a] / g_i[b]), abs=0.06)
    # the rounding in the modes at or above 10^4 R(U*) (bins 49 and above), on the
    # triples that reach them: the same 670 load cases in every row and seed
    reach = z["SK_log_star"][..., 49:].sum(-1) > 0
    assert int(_f(N["numSpecTfStiffLoads"])) == int(reach.sum())
    stiff = {}
    for r in rows:
        den = z["SK_log"][i[r]][..., 49:].sum(-1)
        stiff[r] = (z["SK_log_tf32"][i[r]][..., 49:].sum(-1), den, den > 0)
        assert np.array_equal(stiff[r][2], np.broadcast_to(reach, den.shape)), r
        assert int(_f(N["numSpecTfStiffN"])) == int(stiff[r][2].sum()), r
    for r in ("ar", "labels_knorm"):
        num_, den, ok = stiff[r]
        assert _pct(N[f"numSpecTfStiff{TAGS[r]}"]) == pytest.approx(
            float(np.median(num_[ok] / den[ok])), abs=5e-3), r
    # per seed, the factorisation's shares, and the seed geometric means
    q = [_gm(rho[a][s] / rho[b][s]) for s in range(3)]
    dd = [_gm(d2[a][s] / d2[b][s]) for s in range(3)]
    gg = [_gm(g[a][s] / g[b][s]) for s in range(3)]
    assert _nums(N["numSpecLabKnormDispSeeds"]) == pytest.approx(dd, abs=6e-3)
    sh = [np.log(x) / np.log(y) for x, y in zip(q, gg, strict=True)]
    assert (_pct(N["numSpecSpectralShareMin"]), _pct(N["numSpecSpectralShareMax"])) == (
        pytest.approx(min(sh), abs=5e-3), pytest.approx(max(sh), abs=5e-3))
    assert sum(x > 1 for x in sh) == 1 and all(x > 1 for x in gg)
    kd = [_gm(d2[b][s] / d2[k][s]) for s in range(3)]
    assert _nums(N["numSpecKnormFreeDispSeeds"]) == pytest.approx(kd, abs=6e-3)
    assert max(kd) < 1 and int(np.argmin(kd)) == 1         # the smaller, by far in seed 1
    assert _pct(N["numSpecLabKnormDispLower"]) == pytest.approx(
        float((d2[a] < d2[b]).mean()), abs=5e-4)
    sa, sb = (np.exp(np.log(x).mean(axis=0)) for x in (rho[a], rho[b]))
    assert _pct(N["numSpecLabKnormAboveSeedGm"]) == pytest.approx(float((sa > sb).mean()),
                                                                  abs=5e-4)
    # "... for the label-free transformer, ... for the supervised transformer"
    assert N["numSpecLoadWorseFree"] == N["numSpecLoadWorseLab"]
    # the area- and element-weighted von Mises errors (Section 5.2), and H2b's ratio
    for r in rows:
        for key, M in (("vm_area", "VmArea"), ("vm_elem", "VmElem")):
            assert _f(N[f"numSpec{M}{TAGS[r]}"]) == pytest.approx(
                float(np.median(z[key][i[r]])), rel=5e-3), (r, key)
    rc = json.loads(RCM.read_bytes())
    elem = z["vm_elem"][a].mean() / z["vm_elem"][b].mean()
    assert elem == pytest.approx(statistics.fmean(_seeds(rc, "labels", "vm_rel_l2"))
                                 / statistics.fmean(_seeds(rc, "labels_knorm", "vm_rel_l2")),
                                 rel=1e-9)
    assert _f(N["numSpecVmElemRatio"]) == pytest.approx(elem, abs=5e-3)
    assert _f(N["numSpecVmAreaRatio"]) == pytest.approx(
        z["vm_area"][a].mean() / z["vm_area"][b].mean(), abs=5e-3)


def test_every_quoted_cm2d_reading_is_recomputed(built):
    """The ratios, per-seed lists and label-efficiency readings of Sections 5 and 6, from the
    report alone (the verdict is not read, except for H3's exchanged reading)."""
    N = built["numbers"]
    rc, r2 = json.loads(RCM.read_bytes()), json.loads(R2D.read_bytes())

    def mean(r, arm, m, b="1024"):
        return statistics.fmean(_seeds(r, arm, m, b))

    assert _nums(N["numCmKnormGapSeeds"]) == pytest.approx(
        _seeds(rc, "labels_knorm", "energy_gap_rel"), rel=5e-3)
    assert _nums(N["numCmFreeGapSeeds"]) == pytest.approx(
        _seeds(rc, "ar", "energy_gap_rel"), rel=5e-3)
    assert [x / 100 for x in _nums(N["numHThreeSeedRel"])] == pytest.approx(
        [abs(a / b - 1) for a, b in zip(_seeds(rc, "labels_knorm", "energy_gap_rel"),
                                        _seeds(rc, "ar", "energy_gap_rel"), strict=True)],
        abs=5e-3)
    for key, a, b, m in (("LabOverFreeGap", "labels", "ar", "energy_gap_rel"),
                         ("MgnOverLabGap", "mgn", "labels", "energy_gap_rel"),
                         ("MgnOverFreeVm", "mgn", "ar", "vm_rel_l2")):
        assert _f(N[f"numCm{key}"]) == pytest.approx(mean(rc, a, m) / mean(rc, b, m), abs=0.05)
    adv = {b: 1 - mean(rc, "ar", "energy_gap_rel") / mean(rc, "labels", "energy_gap_rel", b)
           for b in ("16", "64", "256", "1024")}
    assert (_pct(N["numCmAdvMax"]), _pct(N["numCmAdvMin"])) == (
        pytest.approx(adv["16"], abs=5e-4), pytest.approx(adv["1024"], abs=5e-4))
    assert adv["16"] == max(adv.values()) and adv["1024"] == min(adv.values())
    # the label-free gap below the graph network's at every budget it was trained at
    assert all(mean(rc, "mgn", "energy_gap_rel", b) > mean(rc, "ar", "energy_gap_rel")
               for b in ("64", "1024"))
    drop = [mean(r2, a, "disp_rel_l2") / mean(rc, a, "disp_rel_l2")
            for a in ("ar", "labels", "mgn")]
    assert (_f(N["numJulyOverCmDispMin"]), _f(N["numJulyOverCmDispMax"])) == (
        pytest.approx(min(drop), abs=0.05), pytest.approx(max(drop), abs=0.05))
    cm = [mean(rc, a, "disp_rel_l2") for a in ("ar", "labels", "labels_knorm", "mgn")]
    jl = [mean(r2, a, "disp_rel_l2") for a in ("ar", "labels", "labels_anchor", "ar_ft", "mgn")]
    assert _f(N["numCmDispSpread"]) == pytest.approx(max(cm) / min(cm), abs=5e-3)
    assert _f(N["numTwoDispSpread"]) == pytest.approx(max(jl) / min(jl), abs=5e-3)
    assert _f(N["numCmLabGapSixteen"]) == pytest.approx(
        mean(rc, "labels", "energy_gap_rel", "16"), rel=5e-3)
    assert _f(N["numTwoLabGapSixteen"]) == pytest.approx(
        mean(r2, "labels", "energy_gap_rel", "16"), rel=5e-3)
    # the lower relative energy gap and the lower von Mises error on the same pairs
    for a, key in (("ar", "Lab"), ("labels_knorm", "KnormLab")):
        gap = _inst(rc, a, "energy_gap_rel") < _inst(rc, "labels", "energy_gap_rel")
        vm = _inst(rc, a, "vm_rel_l2") < _inst(rc, "labels", "vm_rel_l2")
        assert _pct(N[f"numPairCm{key}Gap"]) == pytest.approx(float((gap & vm).mean()),
                                                              abs=5e-4)
        assert _pct(N[f"numPairCm{key}Vm"]) == pytest.approx(float(vm.mean()), abs=5e-4)
    v = json.loads(VCM.read_bytes())["H3"]["roles_exchanged"]
    assert (_pct(N["numHThreeExRel"]), _pct(N["numHThreeExTau"])) == (
        pytest.approx(v["rel_change"], abs=5e-4), pytest.approx(v["threshold"], abs=5e-4))


def test_criteria_table_states_the_cm2d_verdicts(built):
    """The rows of PREREG_CM2D in the criteria table: each reading as the adjudicator
    recorded it, and the bound of the reuse check as the adjudicator applied it."""
    v = json.loads(VCM.read_bytes())
    tab = built["files"]["table_criteria.tex"]
    for h in ("H1", "H2a", "H2b", "H3"):
        row = next(ln for ln in tab.splitlines() if re.search(rf"(^| & ){h}[ ,:(]", ln))
        measured = row.split(" & ")[2]
        rel, tau = (float(x) / 100 for x in re.findall(r"(\d+\.\d)\\%", measured))
        assert measured.startswith("$-$") == (v[h]["rel_change"] < 0), h
        assert (rel, tau) == (pytest.approx(abs(v[h]["rel_change"]), abs=5e-4),
                              pytest.approx(v[h]["threshold"], abs=5e-4)), h
    adj = (ROOT / "scripts" / "adjudicate_cm2d.py").read_text(encoding="utf-8")
    assert re.search(r"^REPRO_MAX = 1e-4$", adj, re.M)
    assert "deviation at most $10^{-4}$)" in tab


def _signed(cell: str) -> list:
    """The signed percentages of a table cell, as fractions."""
    return [float(t) / 100 for t in re.findall(r"([+\-]?\d+(?:\.\d+)?)\\%",
                                               cell.replace("$-$", "-"))]


def _guard(a, b) -> tuple:
    """PREREG_CM2D Sec. 4 on per-seed values: rel, SE_rel and the guard."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    rel = a.mean() / b.mean() - 1
    se = np.sqrt(a.var(ddof=1) / a.size + b.var(ddof=1) / b.size) / b.mean()
    return rel, se, max(0.1, 2 * se)


def test_hypothesis_table_is_recomputed_from_the_report(built):
    """Table A.2, every cell recomputed from the report's per-seed and per-instance values
    (the verdict file is not read): the seeds, rel, SE_rel, the guard and the reading; the
    guard on the seeds' medians; Welch's interval; a resampling of the instances; and the
    reading with the roles of H3 exchanged."""
    from scipy.stats import t as student_t

    rc = json.loads(RCM.read_bytes())
    tab = built["files"]["table_cm2d.tex"]
    hyp = {ln.split(" & ")[0]: ln.rstrip(" \\").split(" & ")[1:]
           for ln in tab.splitlines() if " & " in ln}
    assert hyp[""] == ["H1", "H2a", "H2b", "H3"]
    rng = np.random.default_rng(20261010)
    idx = rng.integers(0, 256, size=(2000, 256))
    for col, (h, a, b, m) in enumerate((("H1", "ar", "labels", "energy_gap_rel"),
                                        ("H2a", "labels_knorm", "labels", "energy_gap_rel"),
                                        ("H2b", "labels_knorm", "labels", "vm_rel_l2"),
                                        ("H3", "labels_knorm", "ar", "energy_gap_rel"))):
        sa, sb = _seeds(rc, a, m), _seeds(rc, b, m)
        assert _nums(hyp["A, seeds 0, 1, 2"][col]) == pytest.approx(sa, rel=5e-3), h
        assert _nums(hyp["B, seeds 0, 1, 2"][col]) == pytest.approx(sb, rel=5e-3), h
        rel, se, guard = _guard(sa, sb)
        assert _signed(hyp["rel"][col]) == [pytest.approx(rel, abs=5e-4)], h
        assert _signed(hyp["SE$_\\mathrm{rel}$"][col]) == [pytest.approx(se, abs=5e-4)], h
        assert _signed(hyp["Guard"][col]) == [pytest.approx(guard, abs=5e-4)], h
        want = ("supported" if rel < -guard else "not supported") if h != "H3" else (
            "no difference shown" if abs(rel) <= guard else "a difference")
        assert hyp["Reading"][col] == want, h
        # the guard on each seed's median over the instances
        ia, ib = _inst(rc, a, m), _inst(rc, b, m)
        mrel, _, mguard = _guard(np.median(ia, axis=1), np.median(ib, axis=1))
        assert _signed(hyp["Medians: rel (guard)"][col]) == [
            pytest.approx(mrel, abs=5e-4), pytest.approx(mguard, abs=5e-4)], h
        # Welch: rel +/- t(df) SE_rel, Welch-Satterthwaite degrees of freedom
        va, vb = np.var(sa, ddof=1) / 3, np.var(sb, ddof=1) / 3
        df = (va + vb) ** 2 / (va ** 2 / 2 + vb ** 2 / 2)
        half = student_t.ppf(0.975, df) * se
        assert _signed(hyp["Welch 95\\% interval"][col]) == [
            pytest.approx(rel - half, abs=5e-3), pytest.approx(rel + half, abs=5e-3)], h
        # resampling the instances (the same draws for both networks and every seed): an
        # independent draw agrees to within a point
        ra = ia[:, idx].mean(axis=2).mean(axis=0) / ib[:, idx].mean(axis=2).mean(axis=0) - 1
        lo, hi = np.percentile(ra, [2.5, 97.5])
        assert _signed(hyp["Instance resampling 95\\%"][col]) == [
            pytest.approx(lo, abs=0.01), pytest.approx(hi, abs=0.01)], h
    # the note: H3 with the roles of the two networks exchanged
    rel, _, guard = _guard(_seeds(rc, "ar", "energy_gap_rel"),
                           _seeds(rc, "labels_knorm", "energy_gap_rel"))
    note = re.search(r"With the roles of A and B exchanged, rel was (\S+) against a guard of "
                     r"([\d.]+\\%)", tab)
    assert _signed(note.group(1)) == [pytest.approx(rel, abs=5e-4)]
    assert _signed(note.group(2)) == [pytest.approx(guard, abs=5e-4)]
    assert abs(rel) <= guard


def test_field_plot_readings_follow_from_the_figure_files(built):
    """The readings the text quotes on the plotted load cases, and the figure files
    tied to the other records (fig6 to the energies, fig7 to Phase-2b's P3 arrays)."""
    N = built["numbers"]
    names2 = ("downward traction on the end edge", "axial traction on the end edge",
              "shear traction on the top edge", "downward body force")
    names3 = ("downward traction on the end face", "axial traction on the end face",
              "shear traction on the top face", "downward body force")
    f2 = np.load(SPEC / "fig2d.npz")
    j = names2.index(N["numFigTwoDLoad"])
    us = f2["U_star"][j]
    d = [np.linalg.norm(f2[f"U_{r}"][j] - us) / np.linalg.norm(us) for r in TAGS]
    g = [float(f2[f"rel_{r}"][j]) for r in TAGS]
    for key, val in (("DispMin", min(d)), ("DispMax", max(d)), ("GapMin", min(g)),
                     ("GapMax", max(g))):
        assert _f(N[f"numFigTwoD{key}"]) == pytest.approx(val, rel=0.02), key
    f5 = np.load(FLD / "fig5.npz")
    j = names3.index(N["numFigWorstLoad"])
    for r in ("ar", "labels", "mgn"):
        over = f5[f"vm_{r}"][j].astype(float) > 2 * f5["vm_ref"][j].astype(float)
        assert _pct(N[f"numFigWorstTwice{TAGS[r]}"]) == pytest.approx(
            float(f5["vol"][over].sum() / f5["vol"].sum()), abs=5e-3), r
    # the label-free prediction there: too large an amplitude, the reference's shape
    us, u = f5["U_star"][j], f5["U_ar"][j]
    fu = float(f5["F"][j] @ u)
    c = fu / (2 * (float(f5["pi_ar"][j]) + fu))                 # F.u / u'Ku from the energy
    assert c == pytest.approx(float(f5["c_ar"][j]), rel=1e-9)
    d5, d5c = (np.linalg.norm(t * u - us) / np.linalg.norm(us) for t in (1.0, c))
    assert (_f(N["numFigWorstFreeDisp"]), _f(N["numFigWorstFreeC"]),
            _f(N["numFigWorstFreeDispC"])) == (pytest.approx(d5, abs=5e-3),
                                               pytest.approx(c, abs=5e-3),
                                               pytest.approx(d5c, abs=5e-4))
    assert c < 1 and d5c < 0.25 * d5
    # the median instance: its per-load arrays are the energies' (seed 0), its load case
    # is better than the zero field for both supervised networks (Section 7.1)
    f6, ev = np.load(FLD / "fig6.npz"), np.load(FLD / "energies_val.npz")
    r3 = json.loads(R3D.read_bytes())
    ar = _inst(r3, "ar", "energy_gap_rel")[0]
    k6 = int(np.argsort(ar, kind="stable")[(ar.size - 1) // 2])
    arms = [str(a) for a in ev["arms"]]
    assert np.array_equal(f6["rel_ar"], ev["rel"][arms.index("ar"), 0, k6])
    j = names3.index(N["numFigMedianLoad"])
    assert f6["rel_labels"][j] < 1 and f6["rel_mgn"][j] < 1
    # the fine-mesh instance: its mean displacement error is the P3 array's (seed 0), and
    # c* is F.u / u'Ku with u'Ku = 2 (Pi_h(u) + F.u) from the stored energy
    f7 = np.load(FLD / "fig7.npz")
    fine = r3["results"]["p3_transfer"]["metrics"]["ar"]["fine"]["per_seed_eval"][0][
        "per_instance"]["disp_rel_l2"]
    k7 = int(np.argsort(fine, kind="stable")[(len(fine) - 1) // 2])
    d7 = (np.linalg.norm(f7["U_ar"] - f7["U_star"], axis=1)
          / np.linalg.norm(f7["U_star"], axis=1))
    assert float(d7.mean()) == pytest.approx(fine[k7], rel=1e-9)
    fu = np.einsum("ld,ld->l", f7["F"], f7["U_ar"])
    assert np.allclose(f7["c_ar"], fu / (2 * (f7["pi_ar"] + fu)), rtol=1e-9, atol=0)
    j = names3.index(N["numFigFineLoad"])
    c = float(f7["c_ar"][j])
    dc = np.linalg.norm(c * f7["U_ar"][j] - f7["U_star"][j]) / np.linalg.norm(f7["U_star"][j])
    assert c > 1 and dc < 0.25 * d7[j]                  # too small, and the shape kept


def test_field_numbers_count_one_network(built):
    N = built["numbers"]
    ev = np.load(FLD / "energies_val.npz")
    assert int(_f(N["numFieldLoads"])) == ev["pi"][0].size == 3 * 256 * 4


def test_field_plot_faces_are_the_visible_ones_of_a_right_handed_view():
    """The three faces drawn are those a viewer on the +z side sees with x to the right and
    y up (no mirror image): depth recedes up and to the right, the front face is z = max;
    their owner tetrahedra contain them, and they tile the projected box exactly once."""
    from matplotlib.path import Path as MPath
    from scipy.spatial import ConvexHull, Delaunay

    gen = _mod()
    step = gen._cabinet(np.array([0.0, 0.0, 1.0])) - gen._cabinet(np.zeros(3))
    assert step[0] < 0 and step[1] < 0                 # +z comes towards the viewer
    assert np.allclose(gen._cabinet(np.array([1.0, 2.0, 0.0])), [1.0, 2.0])
    for f in ("fig5", "fig6", "fig7"):
        with np.load(FLD / f"{f}.npz") as z:
            nodes, tets = z["nodes"], z["tets"]
        vis = gen._visible_faces(nodes, tets)
        lo, hi = vis["lo"], vis["hi"]
        for name, ax, val in (("front", 2, hi[2]), ("top", 1, hi[1]), ("end", 0, hi[0])):
            tri = vis["faces"][name][0]
            assert np.allclose(nodes[tri][..., ax], val), (f, name)
        area = 0.0
        for tri, own in vis["faces"].values():
            assert (tri[:, :, None] == tets[own][:, None, :]).any(-1).all()      # owner tets
            p = gen._cabinet(nodes[tri])
            e1, e2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
            area += float(np.abs(e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]).sum() / 2)
        corners = gen._cabinet(np.array([[x, y, w] for x in (lo[0], hi[0])
                                         for y in (lo[1], hi[1]) for w in (lo[2], hi[2])]))
        assert area == pytest.approx(ConvexHull(corners).volume, rel=1e-9), f
        # every point of the projected box lies on exactly one drawn face
        g = np.stack(np.meshgrid(np.linspace(0, 1, 211)[1:-1] + 1e-3 * np.sqrt(2),
                                 np.linspace(0, 1, 197)[1:-1] + 1e-3 * np.sqrt(3)),
                     -1).reshape(-1, 2)
        pts = corners.min(0) + g * (corners.max(0) - corners.min(0))
        pts = pts[Delaunay(corners).find_simplex(pts) >= 0]
        cover = np.zeros(len(pts), int)
        for tri, _ in vis["faces"].values():
            xyz = nodes[np.unique(tri)]
            ax = int(np.argmin(np.ptp(xyz, axis=0)))           # the face's normal axis
            a, b = [k for k in range(3) if k != ax]
            q = np.zeros((4, 3))
            q[:, ax] = xyz[0, ax]
            q[:, a] = (lo[a], hi[a], hi[a], lo[a])
            q[:, b] = (lo[b], lo[b], hi[b], hi[b])
            cover += MPath(gen._cabinet(q)).contains_points(pts)
        assert (cover == 1).all(), (f, np.bincount(cover))


def test_field_plots_annotate_and_scale_as_stated(tmp_path, monkeypatch):
    """Each panel's annotation carries its network's relative displacement error, relative
    energy gap and stored energy on the plotted load case, and each colour scale runs from 0
    to the reference's largest value on that load case (displacement magnitude per node,
    von Mises per element)."""
    import sys

    import matplotlib.colors as mc

    gen, seen, notes = _mod(), [], []

    class Rec(mc.Normalize):
        def __init__(self, vmin=None, vmax=None, clip=False):
            if sys._getframe(1).f_code.co_filename.endswith("make_cmame_material.py"):
                seen.append((vmin, vmax))                  # the generator's own scales
            super().__init__(vmin, vmax, clip)

    real = gen._gap_line

    def rec_gap(d, g, pi):
        notes.append((d, g, pi))
        return real(d, g, pi)

    monkeypatch.setattr(mc, "Normalize", Rec)
    monkeypatch.setattr(gen, "_gap_line", rec_gap)
    figs = {f: dict(np.load(FLD / f"{f}.npz")) for f in ("fig5", "fig6", "fig7")}
    gen.fig_fields3d(figs, tmp_path)
    f2 = dict(np.load(SPEC / "fig2d.npz"))
    gen.fig_field2d(f2, tmp_path)
    want, want_notes = [], []
    for f, qs in (("fig5", ("disp", "vm")), ("fig6", ("vm",)), ("fig7", ("disp",))):
        z, j = figs[f], gen.field_load(f, figs[f])
        for q in qs:
            ref = (np.linalg.norm(z["U_star"][j].reshape(-1, 3), axis=1) if q == "disp"
                   else z["vm_ref"][j])
            want.append((0.0, float(ref.max())))
        if f != "fig7":
            want_notes += [(z, j, r) for r in ("ar", "labels", "mgn")]
    j2 = gen.field_load("fig2d", f2)
    want.append((0.0, float(f2["vm_ref"][j2].max())))
    want_notes += [(f2, j2, r) for r in ("ar", "labels_knorm", "labels", "mgn")]
    assert seen == want
    assert len(notes) == len(want_notes)
    for (d, g, pi), (z, j, r) in zip(notes, want_notes, strict=True):
        us = z["U_star"][j]
        assert d == pytest.approx(np.linalg.norm(z[f"U_{r}"][j] - us) / np.linalg.norm(us),
                                  rel=1e-12), r
        assert (g, pi) == (float(z[f"rel_{r}"][j]), float(z[f"pi_{r}"][j])), r
        assert (pi > 0) == (g > 1)


def test_the_functional_check_is_described_as_recorded():
    """Supplementary Section S1's description of the functional check run before CM2D's stamp."""
    fc = json.loads((ROOT / "records" / "cmame" / "cm2d_funccheck.json").read_bytes())
    st, co = fc["settings"], fc["corpus"]
    text = " ".join((PAPER / "sections" / "appendix_prereg.tex").read_text("utf-8").split())
    assert (f"width {st['model']['dim']} and depth {st['model']['depth']} for {st['epochs']} "
            f"epochs on {co['n_train']} instances of another two-dimensional corpus, with "
            f"{['zero', 'one', 'two', 'three'][len(st['seeds'])]} seeds") in text
    assert co["seed"] != 0                       # another corpus than the runs' (seed 0)
    # what it showed: H2a's and H2b's reductions, H1's direction, H3's split between seeds
    val = {arm: [fc["runs"][arm][str(s)]["val"] for s in st["seeds"]]
           for arm in ("disp", "knorm", "ar")}
    for m in ("energy_gap_rel", "vm_rel_l2"):
        assert all(k[m] < d[m] for k, d in zip(val["knorm"], val["disp"], strict=True))
    assert all(a["energy_gap_rel"] < d["energy_gap_rel"]
               for a, d in zip(val["ar"], val["disp"], strict=True))
    order = [k["energy_gap_rel"] < a["energy_gap_rel"]
             for k, a in zip(val["knorm"], val["ar"], strict=True)]
    assert len(set(order)) == 2



def _secs(cell: str) -> tuple:
    """A cost-table time in seconds, with half its last shown digit (the rounding)."""
    v, unit = cell.split()
    scale = {"ms": 1e-3, "s": 1.0}[unit]
    dec = len(v.split(".")[1]) if "." in v else 0
    return float(v.replace(",", "")) * scale, 0.5 * 10 ** -dec * scale


def _shown(cell: str) -> tuple:
    v = cell.replace(",", "").replace("%", "")
    dec = len(v.split(".")[1]) if "." in v else 0
    return float(v), 0.5 * 10 ** -dec


def _span(cell: str) -> tuple:
    """A cost-table range of two times in one unit, each with half its last digit."""
    v, unit = cell.split()
    lo, hi = v.split("--")
    return _secs(f"{lo} {unit}"), _secs(f"{hi} {unit}")


def test_the_cost_table_follows_from_the_timing_records(built):
    """Section 9.2: every cell and number of the cost table recomputed from the
    per-instance timing records of 28 October 2026 with numpy (the generator uses
    statistics), the script's own summary medians agreeing; the rows of the assembly and
    of the Ritz projection from their own records, timed on the same instances and the
    same machine; the readings of the threads, and of the earlier timing on another
    machine, which the supplementary material gives, likewise."""
    tab, N = built["files"]["table_cost.tex"], built["numbers"]
    T, H = RITZ / "timing", ROOT / "records" / "cmame" / "threads"
    rec = {f: json.loads((T / f).read_text()) for f in ("timing_2d.json", "timing_3d.json")}
    sets = {"2D": rec["timing_2d.json"]["results"]["val"],
            "3D": rec["timing_3d.json"]["results"]["val"],
            "3D, fine mesh": rec["timing_3d.json"]["results"]["fine"]}
    head = next(ln for ln in tab.splitlines() if ln.startswith(" & 2D"))
    assert head == r" & 2D & 3D & 3D, fine mesh \\"

    def row(label):
        found = [ln for ln in tab.splitlines() if ln.startswith(label + " &")]
        assert len(found) == 1, label
        return [c.strip() for c in found[0].rstrip("\\ ").split("&")[1:]]

    def med(res, key):
        # over the instances on which the value was measured (the fine mesh's direct solve
        # left its last instance, and the ratios that use it, unmeasured)
        return float(np.median([r[key] for r in res["per_instance"]
                                if r.get(key) is not None]))

    # the direct solve missed only the fine mesh's last instance, on its time budget
    budget = rec["timing_3d.json"]["settings"]["solve_budget_s"]
    for name, res in sets.items():
        pi = res["per_instance"]
        miss = [i for i, r in enumerate(pi) if r["direct_s"] is None]
        if name == "3D, fine mesh":
            assert miss == [len(pi) - 1] and pi[-1]["direct_skipped"] == "budget"
            assert sum(sum(r["direct_runs"]) for r in pi[:-1]) >= budget == 900
            assert res["summary"]["direct_n_solved"] == len(pi) - 1 == 7
        else:
            assert miss == []
        assert res["summary"]["complete"]
    for key, label in (("surrogate_cold_s", "Surrogate, first call"),
                       ("surrogate_warm_s", "Surrogate, repeated call"),
                       ("direct_s", "Sparse direct solve"), ("cg_s", "CG from the zero field"),
                       ("cg_warm_s", "CG from the prediction"),
                       ("cg_match_s", "CG to the prediction's accuracy"),
                       ("cg_match_cstar_s", "the same, after rescaling by $c^*$")):
        for cell, res in zip(row(label), sets.values(), strict=True):
            v, half = _secs(cell)
            m = med(res, key)
            assert m == pytest.approx(res["summary"][key]["median"], rel=1e-12)
            assert abs(v - m) <= half * 1.0001, (label, cell, m)
    for cell, res in zip(row("Instances (load cases)"), sets.values(), strict=True):
        n = len(res["per_instance"])
        assert cell == f"{n} ({sum(r['n_loads'] for r in res['per_instance'])})"
    for cell, res in zip(row("Nodes, median"), sets.values(), strict=True):
        assert cell == f"{round(med(res, 'n_nodes')):,}"

    def per_load(res, key):
        return float(np.median([x for r in res["per_instance"] for x in r[key]]))

    for cell, res in zip(row("CG iterations per load case"), sets.values(), strict=True):
        assert cell == (f"{per_load(res, 'cg_iters'):,.0f} / "
                        f"{per_load(res, 'cg_match_iters'):,.0f}")
    for key, label in (("energy_gap_rel", "Surrogate's relative energy gap"),
                       ("disp_rel_l2", "Surrogate's displacement error"),
                       ("energy_gap_rel_cstar", "Energy gap after rescaling by $c^*$"),
                       ("disp_rel_l2_cstar", "Displacement error after rescaling by $c^*$")):
        for cell, res in zip(row(label), sets.values(), strict=True):
            v, half = _shown(cell)
            assert abs(v - med(res, key)) <= half * 1.0001, label
    for cell, res in zip(row("CG's displacement error at that accuracy"), sets.values(),
                         strict=True):
        v, half = _shown(cell)
        assert abs(v - per_load(res, "cg_match_disp_at_match")) <= half * 1.0001
    # every other solve complete, none fell back, every match reached
    for res in sets.values():
        for r in res["per_instance"]:
            assert not (r["cg_fallback"] or r["cg_warm_fallback"] or r["cg_match_unreached"]
                        or r["cg_match_cstar_unreached"])
    # the assembly and the Ritz projection: the same instances, the same machine; the
    # projection's time is that of the free block, the basis, the projected matrix and
    # loads, the small solve and the reconstruction, from the lowest degree to the highest
    rt = {"2D": json.loads((T / "ritz_timing_2d.json").read_text())["results"]["val"],
          "3D": json.loads((T / "ritz_timing_3d.json").read_text())["results"]["val"],
          "3D, fine mesh": json.loads((T / "ritz_timing_3d.json").read_text())["results"]["fine"]}
    ladder = {"2D": ("6", "8"), "3D": ("6", "7", "8", "9"), "3D, fine mesh": ("6", "7", "8", "9")}
    for f in ("ritz_timing_2d.json", "ritz_timing_3d.json"):
        m = json.loads((T / f).read_text())["machine"]
        assert m["cpu"] == "Intel(R) Xeon(R) Platinum 8470Q"
        assert {p_["num_threads"] for p_ in m["threadpools"]} == {25}
    mach = (RITZ / "machine.txt").read_text()
    assert re.search(r"^Model name:\s+Intel\(R\) Xeon\(R\) Platinum 8470Q$", mach, re.M)
    assert re.search(r"^nproc 25$", mach, re.M)
    for (name, res), a_cell, r_cell in zip(sets.items(), row("Assembly of $K$, the "
                                                              "repository's assembler"),
                                           row("Ritz projection after assembly"), strict=True):
        rows = rt[name]["rows"]
        assert [x["file"] for x in rows] == [r["file"] for r in res["per_instance"]]
        assert all(x["K_max_rel_diff"] == 0.0 for x in rows)
        asm = float(np.median([x["assembly_s"] for x in rows]))
        v, half = _secs(a_cell)
        assert abs(v - asm) <= half * 1.0001, (name, a_cell)
        times = []
        for p in ladder[name]:
            for x in rows:
                q = x["p"][p]
                assert q["dropped"] == 0
                assert q["ritz_s"] == pytest.approx(
                    x["free_s"] + q["basis_s"] + q["kp_s"] + q["solve_s"] + q["recon_s"],
                    rel=1e-9)
            times.append(float(np.median([x["p"][p]["ritz_s"] for x in rows])))
        assert times == sorted(times)
        (lo, hlo), (hi, hhi) = _span(r_cell)
        assert abs(lo - times[0]) <= hlo * 1.0001 and abs(hi - times[-1]) <= hhi * 1.0001
        if name != "2D":
            tag = "Val" if name == "3D" else "Fine"
            for macro, x in ((f"numCostRitz{tag}Min", times[0]),
                             (f"numCostRitz{tag}Max", times[-1]), (f"numCostAsm{tag}", asm),
                             (f"numCostSurr{tag}", med(res, "surrogate_cold_s"))):
                v, half = _secs(N[macro])
                assert abs(v - x) <= half * 1.0001, macro
    over = [float(np.median([x["assembly_s"] for x in rt[n]["rows"]]))
            / float(np.median([x["p"][p]["ritz_s"] for x in rt[n]["rows"]]))
            for n in ("3D", "3D, fine mesh") for p in ladder[n]]
    assert (N["numCostAsmOverRitzMin"], N["numCostAsmOverRitzMax"]) == (
        f"{min(over):.0f}", f"{max(over):.0f}")
    # the text's numbers
    for tag, res in zip(("Two", "ThreeVal", "ThreeFine"), sets.values(), strict=True):
        solved = [r for r in res["per_instance"] if r["direct_s"] is not None]
        ratio = float(np.median([r["direct_s"] / r["surrogate_cold_s"] for r in solved]))
        assert ratio == pytest.approx(med(res, "direct_over_surrogate_cold"), rel=1e-9)
        assert ratio == pytest.approx(res["summary"]["direct_over_surrogate_cold"]["median"],
                                      rel=1e-12)
        v, half = _shown(N[f"numCost{tag}DirectRatio"])
        assert abs(v - ratio) <= half * 1.0001
        match = float(np.median([r["cg_match_s"] / r["surrogate_cold_s"]
                                 for r in res["per_instance"]]))
        v, half = _shown(N[f"numCost{tag}MatchRatio"])
        assert abs(v - match) <= half * 1.0001
        v, half = _shown(N[f"numCost{tag}Gap"])
        assert abs(v - med(res, "energy_gap_rel")) <= half * 1.0001
    assert (N["numCostFineDirectSolved"], N["numCostFineDirectTotal"]) == ("seven", "eight")
    assert N["numCostThreads"] == "25"
    saving = [float(np.median([1 - sum(r["cg_warm_iters"]) / sum(r["cg_iters"])
                               for r in res["per_instance"]])) for res in sets.values()]
    for macro, x in (("numCostWarmMore", -min(saving)), ("numCostWarmFewer", max(saving))):
        v, half = _shown(N[macro])
        assert x > 0 and abs(v - 100 * x) <= half * 1.0001, macro
    # the fine mesh's failures, which its medians hide
    fine = sets["3D, fine mesh"]["per_instance"]
    worse = sorted(x for r in fine for x in r["cg_match_targets"] if x > 1)
    assert all(it == 0 for r in fine for x, it in zip(r["cg_match_targets"], r["cg_match_iters"])
               if x > 1)
    note = " ".join(tab.split())
    n_inst = sum(1 for r in fine if r["energy_gap_rel"] > 1)
    words = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
    assert (f"On the fine mesh, {words[len(worse)]} of the {4 * len(fine)} load cases had a "
            "relative energy gap above 1") in note
    assert f"and {words[n_inst]} of the {words[len(fine)]} instances a mean above 1" in note
    assert "2D: the first 32 validation instances" in note
    assert ("(Xeon Platinum 8470Q, 25 CPUs, the thread environment set to 25)" in note
            and "with the machine's 25 BLAS threads" in note)
    assert ("The fine-mesh direct solve used up its budget of 900 s after seven of the eight "
            "instances; its median, and the ratios that use it, are over those seven.") in note
    assert r"Threads: \cref{sec:cost:inference} and the supplementary material." in note
    # the threads, on another host of the same type: one thread against the environment's,
    # and the repeat (supplementary material, S3)
    hm = (H / "machine.txt").read_text()
    assert re.search(r"^Model name:\s+Intel\(R\) Xeon\(R\) Platinum 8470Q$", hm, re.M)
    # another host: its GPU ran another driver than the cost table's
    drv = [re.search(r"^NVIDIA GeForce RTX 5090, ([\d.]+),", x, re.M).group(1)
           for x in (hm, mach)]
    assert drv[0] != drv[1]
    thr = {k: json.loads((H / f"timing_3d_{k}.json").read_text()) for k in ("env", "one", "env2")}
    tm = {k: {s: {q: float(np.median([r[q] for r in thr[k]["results"][s]["per_instance"]]))
                  for q in ("direct_s", "cg_s")} for s in ("val", "fine")} for k in thr}
    direct_dev = max(abs(tm["one"][s]["direct_s"] / tm["env"][s]["direct_s"] - 1)
                     for s in ("val", "fine"))
    gain = [1 - tm["one"][s]["cg_s"] / tm["env"][s]["cg_s"] for s in ("val", "fine")]
    drift = max(abs(tm["env2"][s][q] / tm["env"][s][q] - 1) for s in ("val", "fine")
                for q in ("direct_s", "cg_s"))
    for macro, x in (("numThreadsDirectDev", direct_dev), ("numThreadsCgGainMin", min(gain)),
                     ("numThreadsCgGainMax", max(gain)), ("numThreadsDrift", drift)):
        v, half = _shown(N[macro])
        assert abs(v - 100 * x) <= half * 1.0001, macro
    assert (N["numThreadsValN"], N["numThreadsFineN"]) == tuple(
        str(len(thr["env"]["results"][s]["per_instance"])) for s in ("val", "fine"))
    pools = {k: json.loads((H / f"blas_{k}.log").read_text())["pools"] for k in ("env", "one")}
    assert {p_["num_threads"] for p_ in pools["env"]} == {int(N["numThreadsHost"])} == {25}
    assert {p_["num_threads"] for p_ in pools["one"]} == {1}
    t2 = {k: json.loads((H / f"timing_2d_{k}.json").read_text()) for k in ("env", "one")}
    g2 = {q: 1 - float(np.median([r[q] for r in t2["one"]["results"]["val"]["per_instance"]]))
          / float(np.median([r[q] for r in t2["env"]["results"]["val"]["per_instance"]]))
          for q in ("direct_s", "cg_s")}
    for macro, q in (("numThreadsTwoDirect", "direct_s"), ("numThreadsTwoCg", "cg_s")):
        v, half = _shown(N[macro])
        assert abs(v - 100 * g2[q]) <= half * 1.0001, macro
    assert N["numThreadsTwoN"] == str(len(t2["env"]["results"]["val"]["per_instance"]))
    supp = " ".join((PAPER / "sections" / "supp_timing.tex").read_text(encoding="utf-8").split())
    assert ("measured on another host of the same type, with \\numThreadsHost{} threads"
            in supp)
    # the earlier timing of the same instances and networks, on another machine
    old_dir = ROOT / "records" / "cmame" / "timing"
    om = (old_dir / "machine.txt").read_text()
    assert re.search(r"^Model name:\s+Intel\(R\) Xeon\(R\) Gold 6459C$", om, re.M)
    assert (N["numRerunCpu"], N["numRerunThreads"]) == (
        "Xeon Gold 6459C", re.search(r"^nproc (\d+)$", om, re.M).group(1))
    worst, iters = 0.0, 0
    for f, ss in (("timing_2d.json", ("val",)), ("timing_3d.json", ("val", "fine"))):
        old = json.loads((old_dir / f).read_text())
        assert old["state_sha256"] == rec[f]["state_sha256"]
        for s in ss:
            for a, b in zip(old["results"][s]["per_instance"],
                            rec[f]["results"][s]["per_instance"], strict=True):
                assert a["file"] == b["file"]
                for k in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err",
                          "crit_recall", "energy_gap_rel_cstar", "disp_rel_l2_cstar", "cstar"):
                    x, y = np.asarray(a[k], float), np.asarray(b[k], float)
                    worst = max(worst, float(np.max(np.abs(y - x) / np.abs(x))))
                for k in ("cg_iters", "cg_warm_iters", "cg_match_iters"):
                    iters = max(iters, int(np.max(np.abs(np.subtract(a[k], b[k])))))
    m_, e_ = re.fullmatch(r"\$(\d) \\times 10\^\{(-\d+)\}\$", N["numRerunAccDev"]).groups()
    assert abs(worst - float(f"{m_}e{e_}")) <= 0.5 * 10 ** int(e_) * 1.0001
    assert N["numRerunIters"] == words[iters]
    assert "on 8 October 2026 on another machine" in supp
    # no pending box is left in the section, and supplementary Section S8 no longer excepts the table
    sec = (PAPER / "sections" / "cost.tex").read_text(encoding="utf-8")
    assert r"\pending" not in sec and r"\input{generated/table_cost}" in sec
    assert "pending cost table" not in (PAPER / "sections" / "appendix_repro.tex").read_text()


# ------------------------------------------------------------------ the follow-up runs
METRICS5 = ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall")


def _k3d(k: dict, arm: str, metric: str) -> np.ndarray:
    """(seeds, instances) values of the energy-norm run's report, whose cells sit at
    its top level."""
    return np.array([e["per_instance"][metric] for e in k["cells"][arm]["1024"]["per_seed_eval"]])


def _close(N: dict, macro: str, x: float, scale: float = 1.0) -> None:
    """A macro shows x (times scale) to its last digit."""
    v, half = _shown(N[macro].replace("−", "-").replace("+", ""))
    assert abs(v - scale * x) <= half * 1.0001, (macro, N[macro], x)


def _row_cells(tab: str, label: str) -> list:
    found = [ln for ln in tab.splitlines() if ln.startswith(label + " & ")]
    assert len(found) == 1, label
    return [c.strip() for c in found[0].rstrip("\\ ").split(" & ")[1:]]


def test_k3d_numbers_and_table_follow_from_the_report(built):
    """Section 5.1 and its supplementary tables (the three-dimensional energy-norm run), recomputed from
    the report's per-instance values without the verdict: the pre-registered statistic, each
    seed's median over the 256 validation instances, with the noise guard; beside it the
    seed means, Welch's interval, the pairs and the predictions worse than the zero field;
    the same readings on the 686 held-out instances, from the run's holdout arrays; and the
    stored networks of the three-dimensional comparison reproducing its values exactly."""
    from scipy.stats import t as student_t

    N, tab = built["numbers"], built["files"]["table_k3d.tex"]
    k, r3 = json.loads(RK3.read_bytes()), json.loads(R3D.read_bytes())
    for arm in ("ar", "labels"):
        for m in METRICS5:
            assert np.array_equal(_k3d(k, arm, m), _inst(r3, arm, m)), (arm, m)
    z = np.load(ROOT / "records" / "cmame" / "k3d" / "return" / "holdout_arrays.npz",
                allow_pickle=False)
    assert z["values"].shape[2] == 686

    def held(row, m):
        return z["values"][list(z["rows"]).index(row), :, :, list(z["metrics"]).index(m)]

    hyp = (("Gap", "labels_knorm", "labels", "energy_gap_rel"),
           ("Vm", "labels_knorm", "labels", "vm_rel_l2"),
           ("Free", "labels_knorm", "ar", "energy_gap_rel"))
    rel_row, guard_row = _row_cells(tab, "rel"), _row_cells(tab, "Guard")
    for col, (tag, a, b, m) in enumerate(hyp):
        sa, sb = np.median(_k3d(k, a, m), axis=1), np.median(_k3d(k, b, m), axis=1)
        rel, se, guard = _guard(sa, sb)
        assert rel < -guard and (tag == "Free" or (sa < sb).all()), tag
        _close(N, f"numKd{tag}Rel", -rel, 100)
        _close(N, f"numKd{tag}Tau", guard, 100)
        assert _signed(rel_row[col]) == [pytest.approx(rel, abs=5e-4)], tag
        assert _signed(guard_row[col]) == [pytest.approx(guard, abs=5e-4)], tag
        hrel, _, hguard = _guard(np.median(held(a, m), axis=1), np.median(held(b, m), axis=1))
        assert hrel < -hguard, tag                       # the same direction, held out
        _close(N, f"numKdHold{tag}Rel", -hrel, 100)
        _close(N, f"numKdHold{tag}Tau", hguard, 100)
        if tag == "Free":
            # a reading without a criterion: beyond the guard, but Welch's interval spans zero
            va, vb = np.var(sa, ddof=1) / 3, np.var(sb, ddof=1) / 3
            df = (va + vb) ** 2 / (va ** 2 / 2 + vb ** 2 / 2)
            half = student_t.ppf(0.975, df) * se
            assert rel - half < 0 < rel + half
            _close(N, "numKdFreeWelchLow", rel - half, 100)
            _close(N, "numKdFreeWelchHigh", rel + half, 100)
    assert _row_cells(tab, "Reading") == ["supported", "supported", "A lower"]
    # the seed means: the von Mises error lower beyond the guard; the energy gap's guard
    # exceeds 100%, so that its seed means cannot show the reduction
    for tag, m in (("Vm", "vm_rel_l2"), ("Gap", "energy_gap_rel")):
        rel, _, guard = _guard(_k3d(k, "labels_knorm", m).mean(axis=1),
                               _k3d(k, "labels", m).mean(axis=1))
        _close(N, f"numKdMeans{tag}Rel", -rel, 100)
        _close(N, f"numKdMeans{tag}Tau", guard, 100)
        assert (rel < -guard) if tag == "Vm" else (guard > 1 and rel < 0)
        if tag == "Vm":
            # beyond the guard, but with three seeds Welch's interval spans zero (Section 5.1)
            sa = _k3d(k, "labels_knorm", "vm_rel_l2").mean(axis=1)
            sb = _k3d(k, "labels", "vm_rel_l2").mean(axis=1)
            va, vb = np.var(sa, ddof=1) / 3, np.var(sb, ddof=1) / 3
            df = (va + vb) ** 2 / (va ** 2 / 2 + vb ** 2 / 2)
            half = student_t.ppf(0.975, df) * np.sqrt(va + vb) / sb.mean()
            assert rel - half < 0 < rel + half
            _close(N, "numKdMeansVmWelchLow", rel - half, 100)
            _close(N, "numKdMeansVmWelchHigh", rel + half, 100)
    # the share of the supervised transformer's excess over the label-free transformer that
    # the change of norm removes, on the seed-averaged medians (descriptive): all of it
    for m, tag in (("vm_rel_l2", "Vm"), ("energy_gap_rel", "Gap")):
        md = {a: np.median(_k3d(k, a, m), axis=1).mean() for a in ("ar", "labels", "labels_knorm")}
        closure = (md["labels"] - md["labels_knorm"]) / (md["labels"] - md["ar"])
        assert closure > 1, m
        _close(N, f"numKdClosure{tag}", closure, 100)
    med = {a: np.median(_k3d(k, a, "energy_gap_rel"), axis=1)
           for a in ("ar", "labels", "labels_knorm")}
    for macro, x in (("numKdKnormGapMedian", med["labels_knorm"].mean()),
                     ("numKdLabGapMedian", med["labels"].mean()),
                     ("numKdFreeGapMedian", med["ar"].mean()),
                     ("numKdFreeMedMin", med["ar"].min()), ("numKdFreeMedMax", med["ar"].max())):
        _close(N, macro, x)
    gap = {a: _k3d(k, a, "energy_gap_rel") for a in ("ar", "labels_knorm")}
    assert N["numKdFreePairs"] == f"{int((gap['labels_knorm'] < gap['ar']).sum()):,}"
    assert gap["ar"].size == 768
    assert N["numThreeKnormWorse"] == "0" and not (gap["labels_knorm"] > 1).any()
    for m, tag in zip(METRICS5, ("Disp", "Gap", "Vm", "Peak", "Recall"), strict=True):
        assert _f(N[f"numThreeKnorm{tag}"]) == pytest.approx(
            _k3d(k, "labels_knorm", m).mean(), rel=5e-3), m
    # the energy-norm-supervised transformer against the label-free one on the seeds' medians, as
    # the text reads the secondary comparisons: more accurate on four metrics
    for m, tag in (("disp_rel_l2", "Disp"), ("vm_rel_l2", "Vm"), ("peak_vm_rel_err", "Peak")):
        rel, _, guard = _guard(np.median(_k3d(k, "labels_knorm", m), axis=1),
                               np.median(_k3d(k, "ar", m), axis=1))
        assert rel < -guard, m
        _close(N, f"numKdFree{tag}Rel", -rel, 100)
    sup = " ".join(built["files"]["table_k3d_comparisons.tex"].split())
    assert sup.count(" & ") >= 30 and N["numKdSecondary"] == "30"


def test_holdout_numbers_follow_from_the_arrays(built):
    """The held-out instances (Section 8 and its tables), recomputed from the evaluation's
    arrays and labels manifests without the verdict: the sets; T2 and T3 in three
    dimensions; H1, H2a, H2b and H3 in two, with the readings beside H2a; and the values of
    both sets."""
    N = built["numbers"]
    rc = json.loads(RCM.read_bytes())
    z = {s: np.load(HOLD / "return" / s / "eval_arrays.npz", allow_pickle=False)
         for s in ("h3d", "h2d")}

    def val(s, row, m, key="values"):
        return z[s][key][list(z[s]["rows"]).index(row), :, :, list(z[s]["metrics"]).index(m)]

    for s, tag in (("h3d", "Three"), ("h2d", "Two")):
        mf = json.loads((HOLD / "return" / s / "manifest.json").read_text())
        tail = mf["n_corpus"] - mf["split"]["n_val"] - mf["used_prefix"]
        assert mf["n"] == tail - len(mf["excluded"]) == len(z[s]["files"])
        assert not set(z[s]["files"]) & set(z[s]["val_files"])
        assert (N[f"numHold{tag}N"], N[f"numHold{tag}Tail"], N[f"numHold{tag}Excl"],
                N[f"numHold{tag}Solves"]) == (f"{mf['n']:,}", f"{tail:,}",
                                              f"{len(mf['excluded']):,}", f"{4 * mf['n']:,}")
        assert mf["ledger"]["total"] == 4 * mf["n"] and mf["method"] == "direct"
    # T2: the graph network's lower displacement error, per seed; its higher von Mises error
    share = (val("h3d", "mgn", "disp_rel_l2") < val("h3d", "ar", "disp_rel_l2")).mean(axis=1)
    _close(N, "numHoldTTwoMin", share.min(), 100)
    _close(N, "numHoldTTwoMax", share.max(), 100)
    assert (val("h3d", "mgn", "vm_rel_l2") > val("h3d", "ar", "vm_rel_l2")).all()
    # T3: load cases worse than the zero field, each with a positive energy and no other
    g = z["h3d"]["gap_load"]
    pi = z["h3d"]["pi_load"]
    rows3 = list(z["h3d"]["rows"])
    for row, macro in (("labels", "numHoldTThreeLab"), ("mgn", "numHoldTThreeMgn")):
        gr, pr = g[rows3.index(row)], pi[rows3.index(row)]
        assert np.isfinite(gr).all() and ((pr > 0) == (gr > 1)).all()
        assert N[macro] == f"{int((gr > 1).sum()):,}"
    assert N["numHoldTThreeLoads"] == f"{g[0].size:,}" == "8,232"
    # H1, H2a, H2b and H3 in two dimensions: the seeds' means over the held-out instances
    for tag, a, b, m in (("One", "ar", "labels", "energy_gap_rel"),
                         ("TwoA", "labels_knorm", "labels", "energy_gap_rel"),
                         ("TwoB", "labels_knorm", "labels", "vm_rel_l2")):
        rel, _, guard = _guard(val("h2d", a, m).mean(axis=1), val("h2d", b, m).mean(axis=1))
        assert (rel < -guard) == (tag != "TwoA"), tag       # H2a alone did not replicate
        _close(N, f"numHoldH{tag}Rel", -rel, 100)
        _close(N, f"numHoldH{tag}Tau", guard, 100)
    kn, lb = val("h2d", "labels_knorm", "energy_gap_rel"), val("h2d", "labels", "energy_gap_rel")
    for macro, x in (("numHoldHTwoANewSeeds", kn.mean(axis=1)),
                     ("numHoldHTwoABaseSeeds", lb.mean(axis=1))):
        assert _nums(N[macro]) == pytest.approx(list(x), rel=5e-3), macro
    _close(N, "numHoldHTwoASeedZero", 1 - kn[0].mean() / lb[0].mean(), 100)
    assert 0 < kn[0].mean() < lb[0].mean()
    # the readings beside H2a: the guard on the medians, the largest gaps, the ratio of the
    # means to the validation instances', the medians of both sets
    rel, _, guard = _guard(np.median(kn, axis=1), np.median(lb, axis=1))
    assert rel < -guard
    _close(N, "numHoldHTwoAMedRel", -rel, 100)
    _close(N, "numHoldHTwoAMedTau", guard, 100)
    top = kn.max(axis=1)
    assert _nums(N["numHoldHTwoATopSeeds"]) == pytest.approx(list(top), abs=0.051)
    assert N["numHoldHTwoATop"] == f"{top.max():.0f}" and int(np.argmin(top)) == 1
    kv = _inst(rc, "labels_knorm", "energy_gap_rel")
    assert np.allclose(val("h2d", "labels_knorm", "energy_gap_rel", "val_values"), kv,
                       rtol=1e-12, atol=0)
    hold, vali = kn.mean(axis=0), kv.mean(axis=0)
    _close(N, "numHoldHTwoARatio", hold.mean() / vali.mean())
    _close(N, "numHoldHTwoAMedHold", np.median(hold))
    _close(N, "numHoldHTwoAMedVal", np.median(vali))
    assert _f(N["numHoldHTwoARatioLow"]) > 1
    # H3: no difference shown; on the seed means the label-free transformer is now the lower
    fr = val("h2d", "ar", "energy_gap_rel")
    rel, _, guard = _guard(kn.mean(axis=1), fr.mean(axis=1))
    assert 0 < rel <= guard
    _close(N, "numHoldHThreeRel", rel, 100)
    _close(N, "numHoldHThreeTau", guard, 100)
    _close(N, "numHoldTwoFreeGap", fr.mean())
    _close(N, "numHoldTwoKnormGap", kn.mean())
    # the values of both sets (the supplementary table of the means and medians)
    tv = " ".join(built["files"]["table_holdout_values.tex"].split())
    n_q = sum(len(z_["rows"]) * len(z_["metrics"]) for z_ in z.values())
    assert N["numHoldVQuantities"] == str(n_q) == "35"
    for s, head in (("h3d", "Three dimensions, 686 held-out instances"),
                    ("h2d", "Two dimensions, 4,111 held-out instances")):
        assert head in tv
    body = [ln for ln in built["files"]["table_holdout_values.tex"].splitlines()
            if ln.count(" & ") == 4 and not ln.startswith("Network")]
    assert len(body) == n_q and all(ln.count(" / ") == 2 for ln in body)
    # every cell: the mean and the median over the instances of each instance's value
    # averaged over the seeds, on both sets, and the ratio of the means inside its interval
    names = {"Label-free": "ar", "Supervised, displacement": "labels",
             "Supervised, energy norm": "labels_knorm", "Graph network": "mgn"}
    order = [(s, r, m) for s in ("h3d", "h2d") for r in z[s]["rows"] for m in z[s]["metrics"]]
    net = None
    for ln, (s, r, m) in zip(body, order, strict=True):
        cells = [c.strip() for c in ln.rstrip("\\ ").split(" & ")]
        net = names.get(cells[0], net) if cells[0] else net
        assert net == r, (ln, r)
        for cell, key in ((cells[2], "val_values"), (cells[3], "values")):
            x = val(s, r, m, key).mean(axis=0)
            for shown, want in zip(cell.split(" / "), (x.mean(), np.median(x)), strict=True):
                v, half = _shown(shown)
                assert abs(v - want) <= half * 1.0001, (s, r, m, key, shown, want)
        ratio = val(s, r, m).mean(axis=0).mean() / val(s, r, m, "val_values").mean(axis=0).mean()
        rv, lo, hi = (float(x) for x in re.fullmatch(r"([\d.]+) \(([\d.]+)--([\d.]+)\)",
                                                      cells[4]).groups())
        assert abs(rv - ratio) <= 0.005 * 1.0001 and lo <= rv <= hi, (s, r, m, cells[4])
    # the pre-registered readings of the predictions worse than the zero field, held out in
    # two dimensions: per row, the instance-seed predictions with a mean gap above one and
    # the load cases with a gap above one, each with a positive energy and no other
    for row, R in (("ar", "Free"), ("labels", "Lab"), ("labels_knorm", "Knorm"), ("mgn", "Mgn")):
        inst = int((val("h2d", row, "energy_gap_rel") > 1).sum())
        i_ = list(z["h2d"]["rows"]).index(row)
        g, pi = z["h2d"]["gap_load"][i_], z["h2d"]["pi_load"][i_]
        assert ((pi > 0) == (g > 1)).all()
        assert N[f"numHoldTwoWorseInst{R}"] == (f"{inst:,}" if inst else "none")
        assert N[f"numHoldTwoWorseLoad{R}"] == f"{int((g > 1).sum()):,}"
        assert not (val("h2d", row, "energy_gap_rel", "val_values") > 1).sum() or row == "mgn"
    assert N["numHoldTwoPairs"] == f"{val('h2d', 'ar', 'energy_gap_rel').size:,}"
    assert N["numHoldTwoLoads"] == f"{z['h2d']['gap_load'][0].size:,}"


def _ritz(s: str) -> dict:
    return json.loads((RITZ / "baseline" / s / "summary.json").read_text())


def test_ritz_numbers_follow_from_the_summaries(built):
    """Every number the text and the abstract quote of the Ritz projection, recomputed from
    the summaries of its return (which tests/test_ritz_return.py rebuilds from the
    per-instance rows): the shares of the instances on which it, or a network, is strictly
    the more accurate; its medians; its unknowns; and its rows of the accuracy tables."""
    N = built["numbers"]
    R = {s: _ritz(s) for s in ("val3d", "fine3d", "h3d", "val2d", "h2d")}

    def ritz(s, model, p, m):
        return [e[m]["ritz_better_share"] for e in R[s]["ladder"][str(p)]["paired"][model]]

    def net(s, model, p, m):
        return [1 - e[m]["ritz_better_share"] - e[m]["ties"] / e[m]["n"]
                for e in R[s]["ladder"][str(p)]["paired"][model]]

    def unit(macro, x):
        """A share shown to the unit, or to more digits where the unit would show 0 or 100."""
        v, half = _shown(N[macro])
        assert abs(v - 100 * x) <= half * 1.0001, (macro, N[macro], x)
        if 0 < x < 1:
            assert v not in (0.0, 100.0), macro

    def bound(macro, x, lower=True):
        """'at least' (rounded down) or 'at most' (rounded up) to one decimal."""
        v = _f(N[macro])
        assert (v <= 100 * x + 1e-9 < v + 0.1) if lower else (v - 0.1 < 100 * x - 1e-9 <= v), \
            (macro, N[macro], x)

    k3 = [R["val3d"]["ladder"][str(p)]["k"] for p in (6, 7, 8, 9)]
    assert k3 == [3 * (p * (p + 1) * (p + 2) // 6) for p in (6, 7, 8, 9)] == [168, 252, 360, 495]
    assert N["numRitzThreeK"] == "168, 252, 360 and 495"
    assert [R["val2d"]["ladder"][str(p)]["k"] for p in (6, 8)] == [42, 72]
    assert N["numRitzTwoK"] == "42 and 72"
    free3, free2 = "phase2b:ar@1024", "cm2d:ar@1024"
    hfree = [m for m in R["h3d"]["ladder"]["6"]["paired"] if m.split(":")[1].startswith("ar")]
    assert len(hfree) == 1
    for p, P in ((6, "Six"), (9, "Nine")):
        x = ritz("val3d", free3, p, "disp_rel_l2")
        unit(f"numRitzValFreeDisp{P}Min", min(x))
        unit(f"numRitzValFreeDisp{P}Max", max(x))
        x = ritz("h3d", hfree[0], p, "disp_rel_l2")
        unit(f"numRitzHoldFreeDisp{P}Min", min(x))
        unit(f"numRitzHoldFreeDisp{P}Max", max(x))
        for s, macro in (("val3d", "numRitzValGap"), ("fine3d", "numRitzFineGap")):
            _close(N, macro + P, R[s]["ladder"][str(p)]["median"]["energy_gap_rel"])
        _close(N, "numRitzValPeak" + P, R["val3d"]["ladder"][str(p)]["median"]["peak_vm_rel_err"])
    assert all(min(ritz("val3d", free3, p, "disp_rel_l2")) > 0.5 for p in (6, 7, 8, 9))
    ratios = [R["val3d"]["ladder"][str(p)]["median"]["peak_vm_rel_err"]
              / e["peak_vm_rel_err"]["model_median"]
              for p in (6, 7, 8, 9) for e in R["val3d"]["ladder"][str(p)]["paired"][free3]]
    _close(N, "numRitzValPeakRatioMin", min(ratios))
    # the abstract: at the top of the ladder, more than twice the label-free transformer's
    # median peak stress error, in each seed
    top9 = [R["val3d"]["ladder"]["9"]["median"]["peak_vm_rel_err"]
            / e["peak_vm_rel_err"]["model_median"] for e in R["val3d"]["ladder"]["9"]["paired"][free3]]
    assert min(top9) > 2
    _close(N, "numRitzValPeakRatioMax", max(ratios))
    bound("numRitzValFreePeakMin",
          min(s for p in (6, 7, 8, 9) for s in net("val3d", free3, p, "peak_vm_rel_err")))
    bound("numRitzHoldFreePeakMin",
          min(s for p in (6, 7, 8, 9) for s in net("h3d", hfree[0], p, "peak_vm_rel_err")))
    trained = [m for m in R["val3d"]["ladder"]["6"]["paired"]
               if m.split(":")[1].split("@")[0].split(" ")[0]
               not in ("zero", "scale_aware_poly", "knn_field")]
    assert {"phase2b:ar@1024", "phase2b:labels@1024", "k3d:labels_knorm@1024",
            "phase2b:mgn@1024"} <= set(trained)
    bound("numRitzValNineDispAll", min(s for m in trained for s in ritz("val3d", m, 9,
                                                                         "disp_rel_l2")))
    kn = "k3d:labels_knorm@1024"
    bound("numRitzValKnormGapMin",
          min(s for p in (6, 7, 8, 9) for s in net("val3d", kn, p, "energy_gap_rel")))
    assert all(s == 1.0 for p in (6, 7, 8, 9) for s in net("val3d", kn, p, "peak_vm_rel_err"))
    # held out: the energy-norm-supervised transformer's lower gap and, but for a few, lower peak
    bound("numRitzHoldKnormGapMin",
          min(s for p in (6, 7, 8, 9) for s in net("h3d", "k3d:labels_knorm", p,
                                                    "energy_gap_rel")))
    miss = [round((1 - s) * R["h3d"]["n"]) for p in (6, 7, 8, 9)
            for s in net("h3d", "k3d:labels_knorm", p, "peak_vm_rel_err")]
    words_ = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")
    assert 0 < max(miss) and N["numRitzHoldKnormPeakMiss"] == words_[max(miss)]
    # on the finer mesh the projection's displacement, energy and von Mises errors stay close
    # to their in-band values, and its peak stress error does not (supplementary Section S4)
    for p in (6, 7, 8, 9):
        ratio = {m: R["fine3d"]["ladder"][str(p)]["mean"][m] / R["val3d"]["ladder"][str(p)]["mean"][m]
                 for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err")}
        assert max(ratio["disp_rel_l2"], ratio["energy_gap_rel"], ratio["vm_rel_l2"]) < 1.2
        assert ratio["peak_vm_rel_err"] > 1.3
    fm = [e["energy_gap_rel"]["model_median"] for e in R["val3d"]["ladder"]["9"]["paired"][free3]]
    assert min(fm) <= R["val3d"]["ladder"]["9"]["median"]["energy_gap_rel"] <= max(fm)
    # the abstract and Section 9.1: at the top of its ladder the projection's means are the
    # better than the label-free transformer's on every metric but the peak stress error, in
    # both dimensions, and the energy-norm-supervised transformer's are the better than the
    # projection's in relative energy gap, von Mises error and peak stress error (3D)
    r3, rc, k = (json.loads(q.read_bytes()) for q in (R3D, RCM, RK3))
    for s, rep, top in (("val3d", r3, "9"), ("val2d", rc, "8")):
        rz = R[s]["ladder"][top]["mean"]
        for m in METRICS5:
            free = statistics.fmean(_seeds(rep, "ar", m))
            better = rz[m] > free if m == "crit_recall" else rz[m] < free
            assert better == (m != "peak_vm_rel_err"), (s, m)
    rz = R["val3d"]["ladder"]["9"]["mean"]
    for m in METRICS5:
        kn = _k3d(k, "labels_knorm", m).mean()
        better = kn > rz[m] if m == "crit_recall" else kn < rz[m]
        assert better == (m in ("energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err")), m
    # two dimensions
    d2 = [s for p in (6, 8) for s in ritz("val2d", free2, p, "disp_rel_l2")]
    unit("numRitzTwoFreeDispMin", min(d2))
    unit("numRitzTwoFreeDispMax", max(d2))
    for p, P in ((6, "Six"), (8, "Eight")):
        x = ritz("val2d", free2, p, "energy_gap_rel")
        unit(f"numRitzTwoFreeGap{P}Min", min(x))
        unit(f"numRitzTwoFreeGap{P}Max", max(x))
    bound("numRitzTwoFreePeakMin",
          min(s for p in (6, 8) for s in net("val2d", free2, p, "peak_vm_rel_err")))
    # the finer mesh: every network, the fine-tuned ones included
    ftrained = [m for m in R["fine3d"]["ladder"]["6"]["paired"]
                if m.split(":")[1].split("@")[0].split(" ")[0]
                not in ("zero", "scale_aware_poly", "knn_field")]
    assert "phase2b:finetune@64" in ftrained and "phase2b:mgn@max (zero-shot)" in ftrained
    bound("numRitzFineGapAll", min(s for m in ftrained for p in (6, 7, 8, 9)
                                   for s in ritz("fine3d", m, p, "energy_gap_rel")))

    def fine_peak(models):
        x = [s for m in models for p in (6, 7, 8, 9)
             for s in net("fine3d", m, p, "peak_vm_rel_err")]
        return min(x), max(x)

    for models, tag in ((["phase2b:ar (zero-shot)"], "Free"),
                        (["e2_m512:ar (zero-shot)", "e2_m1024:ar (zero-shot)"], "Bn"),
                        (["phase2b:finetune@64"], "Ft")):
        lo, hi = fine_peak(models)
        unit(f"numRitzFine{tag}PeakMin", lo)
        unit(f"numRitzFine{tag}PeakMax", hi)
    bound("numRitzFineLabPeakMax", fine_peak(["phase2b:labels@max (zero-shot)"])[1],
          lower=False)
    assert fine_peak(["phase2b:mgn@max (zero-shot)"])[1] == 0
    # the rows of the accuracy tables: the projection's instance means, every degree
    for s, name in (("val3d", "table_3d.tex"), ("val2d", "table_2d.tex"),
                    ("fine3d", "table_transfer.tex")):
        tab = built["files"][name]
        for p in R[s]["ladder_p"]:
            cells = _row_cells(tab, f"Ritz projection, $p = {p}$")
            means = R[s]["ladder"][str(p)]["mean"]
            for cell, m in zip(cells, METRICS5, strict=False):
                v, half = _shown(cell)
                assert abs(v - means[m]) <= half * 1.0001, (s, p, m)
            if s != "fine3d":
                assert cells[-1] == f"0/{R[s]['n']}"
    # the supplementary table of the shares: every set, model and degree
    pairs = built["files"]["table_ritz_pairs.tex"]
    n_rows = sum(len(R[s]["ladder_p"]) * len(models) for s, models in (
        ("val3d", range(10)), ("val2d", range(7)),
        *((s, R[s]["ladder"][str(R[s]["ladder_p"][0])]["paired"]) for s in ("fine3d", "h3d",
                                                                             "h2d"))))
    body = [ln for ln in pairs.splitlines() if ln.count(" & ") == 7 and not ln.startswith("Set")]
    assert len(body) == n_rows


def test_no_earlier_journal_is_named(built):
    """The manuscript, its supplementary material, the graphical abstract, the highlights and
    the comments of its sources name no journal to which the paper was submitted before, no
    tag or file named after one, and nothing that speaks of an earlier submission or version
    (a revision, a resubmission, a new version of an archive), but for the one directory of
    the October records that the list of hashes prints; the references name journals only in
    their journal fields."""
    bad = re.compile(r"cmame|CMAME|Computer Methods in Applied|Comput\. Methods Appl")
    earlier = re.compile(r"\brevision|\brevised\b|resubmi|re-submi|previous(ly)? submi|"
                         r"earlier submi|first submi|declined|desk[- ]reject|"
                         r"-v\d\b|new version of|transferred to this", re.I)
    files = [*PAPER.glob("*.tex"), *(PAPER / "sections").glob("*.tex"),
             *OUT.glob("*.tex"), PAPER / "highlights.txt"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        hits = bad.findall(text)
        if f.name == "hashes.tex":
            assert text.count(r"\path{records/cmame/}") == 1 and hits == ["cmame"], hits
        else:
            assert not hits, (f.name, hits)
        assert not earlier.search(text), (f.name, earlier.search(text).group(0))
    assert r"\journal{Journal of Computational Physics}" in (PAPER / "main.tex").read_text()
    bib = (PAPER / "references.bib").read_text(encoding="utf-8")
    for line in bib.splitlines():
        if bad.search(line):
            assert re.match(r"\s*journal\s*=", line), line
        if line.lstrip().startswith("%"):
            assert not earlier.search(line), line


def test_highlights_match_the_numbers(built):
    """The Guide for Authors' highlights: three to five bullets of at most 85 characters,
    spaces included; each claim as the records state it."""
    lines = (PAPER / "highlights.txt").read_text(encoding="utf-8").splitlines()
    assert 3 <= len(lines) <= 5 and all(0 < len(x) <= 85 and x.isascii() for x in lines)
    # Corollary 1, which the tests of Section 3 check on assembled instances
    assert lines[0] == ("Minimising the discrete energy is regression in the energy norm, "
                        "with no labels")
    # the energy-norm run: the median von Mises error of the displacement-supervised
    # transformer over that of the energy-norm-supervised one, seed-averaged medians over the
    # instances, sixfold to the nearest integer
    k = json.loads(RK3.read_bytes())
    med = {a: np.median(_k3d(k, a, "vm_rel_l2"), axis=1).mean() for a in ("labels", "labels_knorm")}
    assert round(med["labels"] / med["labels_knorm"]) == 6
    assert lines[1] == "With the same labels, an energy-norm loss cut 3D von Mises errors sixfold"
    # T1: the label-free transformer better than the displacement-supervised one on all five
    # metrics, in each seed, from the report of the three-dimensional comparison
    r3 = json.loads(R3D.read_bytes())
    for m in ("disp_rel_l2", "energy_gap_rel", "vm_rel_l2", "peak_vm_rel_err", "crit_recall"):
        a, b = np.array(_seeds(r3, "ar", m)), np.array(_seeds(r3, "labels", m))
        assert ((a > b) if m == "crit_recall" else (a < b)).all(), m
    assert lines[2] == ("Same 3D network: energy-only training beat displacement supervision "
                        "on all metrics")
    # the graph network: the lower displacement error and the higher von Mises error than the
    # label-free transformer, on the seed means and on most instance-seed pairs
    d = (_inst(r3, "mgn", "disp_rel_l2") < _inst(r3, "ar", "disp_rel_l2")).mean()
    v = (_inst(r3, "mgn", "vm_rel_l2") > _inst(r3, "ar", "vm_rel_l2")).mean()
    assert d > 0.5 and v > 0.95
    assert statistics.fmean(_seeds(r3, "mgn", "disp_rel_l2")) < statistics.fmean(
        _seeds(r3, "ar", "disp_rel_l2"))
    assert lines[3] == "Displacement errors can rank surrogates opposite to their stress errors"
    # Corollary 4, which the field records bear out on every load case (test above)
    assert lines[4] == ("The sign of the energy flags predictions worse than the zero field, "
                        "without solutions")


def test_norm_label_numbers_follow_from_the_reports(built):
    """Fig. 1 and the numbers the abstract, the introduction and Sections 6 and 10 quote from
    it, recomputed from the reports' per-instance values: per network and seed, the median
    (and the mean) over the validation instances of the relative energy-norm error, the square
    root of each instance's relative energy gap, and of the von Mises error, averaged over the
    seeds; in three dimensions from the energy-norm run's report, in two from the
    two-dimensional comparison's."""
    N = built["numbers"]
    k, rc = json.loads(RK3.read_bytes()), json.loads(RCM.read_bytes())
    tags = {"labels": "Lab", "labels_knorm": "Knorm", "ar": "Free"}
    for dim, get in (("Three", lambda a, m: _k3d(k, a, m)), ("Cm", lambda a, m: _inst(rc, a, m))):
        stat = {}
        for a in tags:
            e, v = np.sqrt(get(a, "energy_gap_rel")), get(a, "vm_rel_l2")
            assert e.shape == (3, 256)
            stat[a] = {"E": np.median(e, axis=1).mean(), "Vm": np.median(v, axis=1).mean(),
                       "Em": e.mean(axis=1).mean(), "Vmm": v.mean(axis=1).mean()}
            _close(N, f"numNl{dim}E{tags[a]}", stat[a]["E"])
            _close(N, f"numNl{dim}Vm{tags[a]}", stat[a]["Vm"])
        for q in ("E", "Vm"):
            rn = stat["labels"][q] / stat["labels_knorm"][q]
            rl = stat["ar"][q] / stat["labels_knorm"][q]
            _close(N, f"numNl{dim}Norm{q}", rn)
            _close(N, f"numNl{dim}Label{q}", rl)
            _close(N, f"numNl{dim}Norm{q}Mean", stat["labels"][q + "m"] / stat["labels_knorm"][q + "m"]
                   if q == "Vm" else stat["labels"]["Em"] / stat["labels_knorm"]["Em"])
            # changing the norm moves the error far more than removing the labels
            assert rn > 2 and 1 < rl < 1.35, (dim, q)
    # "within a factor of 1.3" (abstract, Section 10): both median ratios, 3D, at most 1.3
    assert N["numNlThreeLabelWithin"] == "1.3"
    assert all(_f(N[f"numNlThreeLabel{q}"]) <= 1.3 for q in ("E", "Vm"))
    assert N["numNlThreeNormVmWord"] == "six"


def test_abstract_has_no_numbers_and_at_most_250_words():
    text = (PAPER / "sections" / "abstract.tex").read_text(encoding="utf-8")
    assert not re.search(r"\d", text)
    assert len(text.split()) <= 250


def _prose(tex: str) -> str:
    """The text of a section without comments, macro names, labels, references,
    graphics paths, TikZ options and table column widths."""
    tex = "\n".join(line.split("%")[0] if not line.lstrip().startswith("%") else ""
                    for line in tex.replace("\\%", "PCT").splitlines())
    tex = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", "", tex, flags=re.S)
    tex = re.sub(r"\{[0-9.]+\\(?:line|text)width\}", "", tex)    # column widths of a table
    tex = re.sub(r"\\(ref|cref|Cref|label|eqref|cite|input|includegraphics|path)"
                 r"(\[[^\]]*\])?\{[^}]*\}", "", tex)
    return re.sub(r"\\[A-Za-z]+", " ", tex)


# decimals and percentages the text may state: design constants of the problems,
# networks and protocol, each checked against the configurations and code below
ALLOWED_DECIMALS = {"0.05", "0.5", "1.5", "0.25", "0.38", "0.8", "0.06", "0.16", "0.12", "0.6",
                    "1.2", "0.08", "0.0579", "0.0906", "0.0374", "1.8", "2.5"}
ALLOWED_PERCENT = {"5", "10", "20", "30", "40", "95"}
# names that contain version numbers, not results: the AI models named in the
# generative-AI declaration and in supplementary Section S8, the tag of the version described, and the
# licences and the archive's DOI
# named in the Data availability statement
NAMES_WITH_VERSIONS = ("Claude Fable 5.1", "Claude Opus 5.5", "statics-paper-1.0",
                       "PolyForm Noncommercial License 1.0.0", "CC BY 4.0",
                       "10.5281/zenodo.23298799")


def test_the_text_carries_no_hand_typed_result():
    bad = []
    for f in [*sorted((PAPER / "sections").glob("*.tex")), PAPER / "supplementary.tex"]:
        prose = _prose(f.read_text(encoding="utf-8"))
        for name in NAMES_WITH_VERSIONS:
            prose = prose.replace(name, "")
        for m in re.finditer(r"(?<![\w.])(\d+\.\d+)(?![\w.])", prose):
            if m.group(1) not in ALLOWED_DECIMALS:
                bad.append(f"{f.name}: {m.group(1)}")
        for m in re.finditer(r"(?<![\w.])(\d+(?:\.\d+)?)PCT", prose):
            if m.group(1) not in ALLOWED_PERCENT:
                bad.append(f"{f.name}: {m.group(1)}%")
    assert not bad, "numbers typed by hand (use generated/numbers.tex):\n" + "\n".join(bad)


def test_design_constants_match_the_configurations_and_code():
    c2 = json.loads((ROOT / "configs" / "phase1_rec8_v2.json").read_text())
    c3 = json.loads((ROOT / "configs" / "phase2b_v1.json").read_text())
    assert (c2["data"]["n"], c2["split"]["n_val"]) == (30000, 256)
    assert (c3["data"]["n"], c3["split"]["n_val"]) == (2000, 256)
    assert c3["data"]["lc_range"] == [0.0579, 0.0906] and c3["data_transfer"]["lc"] == 0.0374
    assert c3["data_transfer"]["n"] == 320 and c3["data_transfer"]["split"] == {
        "n_eval": 256, "n_fewshot_prefix": 64}
    # every label is a sparse direct solve: the corpora are generated without labels
    # and labelled by the runner's direct path; no code reads the labels' cg_tol key
    assert c3["data"]["labelled_policy"] == c3["data_transfer"]["labelled_policy"] == "economy"
    run = (ROOT / "src" / "fejepa" / "experiments" / "runner.py").read_text(encoding="utf-8")
    assert 'labelled = "all" if dcfg.get("labelled_policy") == "all" else "none"' in run
    assert 'solve_fe_displacement(arch.K, arch.F, arch.free_mask, method="direct")' in run
    assert not [q for q in (ROOT / "src").rglob("*.py") if "cg_tol" in q.read_text("utf-8")]
    gen2 = (ROOT / "src" / "fejepa" / "fe" / "generator.py").read_text(encoding="utf-8")
    assert 'method="direct", ledger=ledger,' in gen2
    for c in (c2, c3):
        m = c["model"]
        assert (m["dim"], m["depth"], m["heads"], m["mgn_dim"], m["mgn_depth"]) == (256, 8, 8,
                                                                                   256, 8)
        e8 = c["experiments"]["e8"]
        assert e8["budgets"] == [16, 64, 256, 1024] and e8["pool_sizes"] == [1024]
        assert (e8["seeds"] if "seeds" in e8 else len(c["seeds"])) == 3
        assert (e8["ar_epochs"], e8["sup_epochs"]) == (200, 200)
        assert (c["pretrain"]["lr"], c["sup"]["lr"]) == (1e-3, 1.5e-3)
    assert c3["experiments"]["e8"]["mgn_budgets"] == [64, 1024]
    p3 = c3["experiments"]["p3_transfer"]
    assert (p3["fewshot_epochs"], p3["fewshot_lr"], p3["fewshot_budgets"]) == (50, 1.5e-3,
                                                                              [16, 64])
    e7, e4 = c2["experiments"]["e7"], c2["experiments"]["e4"]
    assert (e7["pre_epochs"], e7["n_eval"], e7["tol"]) == (100, 64, 1e-6)
    assert (e4["coarsens"], e4["n_train"], e4["n_val"]) == ([1.8, 2.5], 512, 128)
    # the settings of the warm-start and cross-resolution tests (supplementary Sections S5 and S7), as run
    r2 = json.loads(R2D.read_bytes())["results"]
    pre = r2["e4"]["protocol"]["pretrain"]
    assert (pre["epochs"], pre["lr"], pre["seed"]) == (100, 1e-3, 0)
    assert all((row["n_train"], row["n_val"]) == (512, 128)
               for row in r2["e4"]["metrics"]["per_coarsen"])
    assert "seed" not in e7 and "seed" not in e4
    e7src = (ROOT / "src" / "fejepa" / "experiments" / "e7_polish.py").read_text("utf-8")
    assert 'seeded_factory(model_factory, int(cfg.get("seed", 0)))' in e7src
    assert (r2["e7"]["protocol"]["tol"], r2["e7"]["protocol"]["n_eval"]) == (1e-6, 64)
    g = c3["gate_g2"]
    assert (g["parity_band"], g["egap_adv_min"], g["sanity_x"]) == (0.1, 0.4, 3.0)
    pilot = json.loads((ROOT / "configs" / "phase2b_pilot.json").read_text())
    assert pilot["experiments"]["e8"]["ar_epochs"] == 20
    # the code behind the methods section
    src = {n: (ROOT / "src" / "fejepa" / n).read_text(encoding="utf-8") for n in (
        "fe/generator.py", "fe/gmsh3d.py", "train/schedule.py", "train/pretrain.py",
        "train/supervised.py", "experiments/e8_regimes.py")}
    for lit in ("rng.uniform(1.5, 3.0)", "rng.uniform(0.8, 1.5)", "rng.uniform(0.25, 0.38)",
                "rng.integers(0, 4)", "rng.uniform(0.06, 0.16)", "rng.uniform(0.05, 0.12)",
                "0.05 * rng.uniform(0.5, 1.5, size=4)"):
        assert lit in src["fe/generator.py"], lit
    for lit in ("rng.uniform(0.6, 1.2)", "rng.uniform(0.08, 0.16)",
                "0.05 * rng.uniform(0.5, 1.5, size=4)"):
        assert lit in src["fe/gmsh3d.py"], lit
    assert "warmup_frac: float = 0.05" in src["train/schedule.py"]
    for n in ("train/pretrain.py", "train/supervised.py"):
        assert "weight_decay: float = 1e-4" in src[n] and "clip: float = 1.0" in src[n]
    assert "POLICY_BALANCED_FROM = 64" in src["experiments/e8_regimes.py"]
    # stated thresholds of the pre-registered kills
    kills = {k["condition"] for e in r_kills() for k in e}
    assert any("> 30% worse" in k for k in kills) and any("< 40%" in k for k in kills)
    assert any(k.startswith("K5") and "< 20%" in k for k in kills)
    led = (ROOT / "DEVIATIONS_PHASE2.md").read_text(encoding="utf-8")
    assert "1,744" in led and "720 in-band instances" in led
    # the intervals of the run of 9 October 2026 that the text quotes are at 95%
    v = json.loads(VCM.read_bytes())
    for h in ("H1", "H2a", "H2b", "H3"):
        rb = v[h]["robustness"]
        assert rb["welch_95"]["level"] == rb["instance_resampling_95"]["level"] == 0.95
        assert rb["instance_resampling_95"]["resamples"] == 2000
    pre = (ROOT / "PREREG_PHASE2.md").read_text(encoding="utf-8")
    assert "10k-30k dof" in pre and "100,182" in pre


def r_kills():
    r2 = json.loads(R2D.read_bytes())
    return [v["kills"] for v in r2["results"].values()]


def test_network_sizes_match_the_modules(built):
    """The parameter counts of Section 4 (by formula in the generator) are those of
    the torch modules the runs built, in both dimensions."""
    pytest.importorskip("torch")
    from fejepa.models.fejepa import FEJEPAConfig, build_fejepa
    from fejepa.models.gnn import build_mesh_gnn

    gen, N = _mod(), built["numbers"]
    n = lambda mod: sum(q.numel() for q in mod.parameters())                  # noqa: E731
    for cfg_name in ("phase1_rec8_v2", "phase2b_v1"):
        c = json.loads((ROOT / "configs" / f"{cfg_name}.json").read_text())["model"]
        cfg = FEJEPAConfig.from_dict(c)
        f, sd = cfg.features.dim, int(cfg.features.spatial_dim)
        m = build_fejepa(cfg)
        used, aux = gen._params_transformer(f=f, sd=sd)
        assert (n(m.encoder) + n(m.decoder), n(m.predictor) + n(m.proj)) == (used, aux)
        assert n(m) == used + aux
        g = build_mesh_gnn(dim=c["mgn_dim"], depth=c["mgn_depth"], features=cfg.features)
        assert n(g) == gen._params_graph(f=f, sd=sd)
        # the text states one value for both dimensions
        assert (f"{used / 1e6:.1f}", f"{aux / 1e6:.1f}", f"{n(g) / 1e6:.1f}") == (
            N["numParamsTransformer"], N["numParamsAux"], N["numParamsGraph"])


# ------------------------------------------------------------------ theory
def _instances():
    from fejepa.fe.synthetic import synthetic_instance
    from fejepa.fe.tet3d import tet_instance

    rng = np.random.default_rng(7)
    return [synthetic_instance(rng, labelled=True), tet_instance(rng, labelled=True)]


def _stresses(a, u):
    m = a.meta["material"]
    if a.nodes.shape[1] == 3:
        from fejepa.fe.tet3d import _tet_geometry, tet_stresses, tet_von_mises

        vol, _ = _tet_geometry(a.nodes, a.elements)
        s = tet_stresses(a.nodes, a.elements, u, m)
        return vol, tet_von_mises(a.nodes, a.elements, u, m), s[:, :3].sum(axis=1) / 3
    from fejepa.fe.stress import _geometry, element_stresses, element_von_mises

    area, _, _ = _geometry(a.nodes, a.elements)
    s = element_stresses(a.nodes, a.elements, u, m)
    return area, element_von_mises(a.nodes, a.elements, u, m), (s[:, 0] + s[:, 1]) / 3


def test_proposition_1_energy_gap_and_stress_error():
    rng = np.random.default_rng(1)
    for a in _instances():
        E, nu = a.meta["material"]["E"], a.meta["material"]["nu"]
        G, B = E / (2 * (1 + nu)), E / (3 * (1 - 2 * nu))
        free = ~a.dirichlet_mask
        for j in range(a.n_loads):
            us = a.U_star[j]
            for scale in (1e-3, 0.1, 1.0):
                v = rng.normal(size=us.size) * free * np.abs(us).max() * scale
                meas, vm_v, p_v = _stresses(a, v)
                # (eq:stressnorm): v'Kv = int vm^2/(3G) + p^2/B
                assert v @ (a.K @ v) == pytest.approx(
                    float(np.sum(meas * (vm_v ** 2 / (3 * G) + p_v ** 2 / B))), rel=1e-10)
                u = us + v
                _, vm_u, _ = _stresses(a, u)
                _, vm_s, p_s = _stresses(a, us)
                lhs = float(np.sum(meas * (vm_u - vm_s) ** 2))
                assert lhs <= 3 * G * (v @ (a.K @ v)) * (1 + 1e-12)          # (eq:vmbound)
                gamma = 3 * G * float(np.sum(meas * p_s ** 2)) / (B * float(np.sum(meas * vm_s ** 2)))
                g = (v @ (a.K @ v)) / (us @ (a.K @ us))
                assert lhs / float(np.sum(meas * vm_s ** 2)) <= (1 + gamma) * g * (1 + 1e-12)


def test_proposition_2_and_corollaries_3_and_4_amplitude_ranking_and_zero_field():
    rng = np.random.default_rng(2)
    for a in _instances():
        free = ~a.dirichlet_mask
        for j in range(a.n_loads):
            us, F = a.U_star[j], a.F[j] * free
            pi = lambda w: 0.5 * w @ (a.K @ w) - F @ w                        # noqa: E731
            nus = us @ (a.K @ us)
            for scale in (0.05, 0.7, 1.3, 3.0):
                u = (us * rng.uniform(0.2, 2.0)
                     + scale * rng.normal(size=us.size) * free * np.abs(us).max())
                ku = u @ (a.K @ u)
                c = (F @ u) / ku
                assert pi(c * u) == pytest.approx(-(F @ u) ** 2 / (2 * ku), rel=1e-9)
                assert pi(c * u) <= min(pi(u), 0.0) + 1e-15 * abs(pi(us))
                cos = (u @ (a.K @ us)) / np.sqrt(ku * nus)
                g_c = ((c * u - us) @ (a.K @ (c * u - us))) / nus
                assert g_c == pytest.approx(1 - cos ** 2, abs=1e-10)
                g = ((u - us) @ (a.K @ (u - us))) / nus
                assert (pi(u) > 0) == (g > 1)                                 # Corollary 4
                w = us + rng.normal(size=us.size) * free * np.abs(us).max() * 0.1
                g_w = ((w - us) @ (a.K @ (w - us))) / nus
                # Corollary 3: energy differences are differences of the energy gaps
                assert (pi(u) - pi(w)) == pytest.approx(0.5 * nus * (g - g_w), rel=1e-8)


def test_corollary_5_warm_start_iteration_bound():
    """Conjugate gradients from a warm start with relative energy gap g0 reach the
    target g_bar within the iterations that the corollary of the supplementary material
    (cor:warm) states, the Chebyshev bound holds along the way, and the bound's saving is
    the fraction of eq:warm."""
    rng = np.random.default_rng(4)
    g_bar, tested = 1e-4, 0
    for a in _instances():
        free = ~a.dirichlet_mask
        K = a.K[free][:, free].toarray()
        lam = np.linalg.eigvalsh(K)
        rho = (np.sqrt(lam[-1] / lam[0]) - 1) / (np.sqrt(lam[-1] / lam[0]) + 1)
        for j in range(a.n_loads):
            us = a.U_star[j][free]
            F = K @ us
            nus = us @ F
            for scale in (1e-3, 1e-2, 3e-2):
                x = us + scale * rng.normal(size=us.size) * np.abs(us).max()
                g0 = ((x - us) @ K @ (x - us)) / nus
                if not g_bar < g0 <= 1:
                    continue
                k_warm = np.log(4 * g0 / g_bar) / (2 * np.log(1 / rho))
                k_zero = np.log(4 / g_bar) / (2 * np.log(1 / rho))
                assert (k_zero - k_warm) / k_zero == pytest.approx(
                    np.log(1 / g0) / np.log(4 / g_bar), rel=1e-12)            # eq:warm
                r = F - K @ x
                d, rr = r.copy(), r @ r
                for k in range(1, int(np.ceil(k_warm)) + 1):
                    if np.sqrt(rr) < 1e-14 * np.linalg.norm(F):
                        break
                    Kd = K @ d
                    alpha = rr / (d @ Kd)
                    x, r = x + alpha * d, r - alpha * Kd
                    rr, rr_old = r @ r, rr
                    d = r + (rr / rr_old) * d
                    g = ((x - us) @ K @ (x - us)) / nus
                    assert g <= 4 * g0 * rho ** (2 * k) * (1 + 1e-6) + 1e-14    # eq:cheb
                assert ((x - us) @ K @ (x - us)) / nus <= g_bar * (1 + 1e-6)
                tested += 1
    assert tested >= 4


def test_remarks_3_and_4_rank_and_residual_bounds():
    rng = np.random.default_rng(3)
    for a in _instances():
        free = ~a.dirichlet_mask
        K = a.K[free][:, free].toarray()
        lam = np.linalg.eigvalsh(K)
        kappa = lam[-1] / lam[0]
        for _ in range(20):
            ea, eb = rng.normal(size=(2, K.shape[0])) * rng.uniform(0.01, 1, size=(2, 1))
            ratio = (np.sqrt(ea @ K @ ea / (eb @ K @ eb))
                     / (np.linalg.norm(ea) / np.linalg.norm(eb)))
            assert kappa ** -0.5 * (1 - 1e-12) <= ratio <= kappa ** 0.5 * (1 + 1e-12)
        for j in range(a.n_loads):
            us = a.U_star[j][free]
            F = K @ us
            e0 = rng.normal(size=us.size) * np.abs(us).max() * 0.1
            g0 = (e0 @ K @ e0) / (us @ K @ us)
            r0 = K @ e0
            assert np.linalg.norm(r0) / np.linalg.norm(F) <= np.sqrt(kappa * g0) * (1 + 1e-12)


# ------------------------------------------------------------------ compile
@pytest.mark.skipif(shutil.which("latexmk") is None or shutil.which("pdflatex") is None,
                    reason="no LaTeX toolchain")
def test_manuscript_compiles(tmp_path):
    kpse = shutil.which("kpsewhich")
    if kpse is None or not subprocess.run([kpse, "elsarticle.cls"], capture_output=True,
                                          text=True).stdout.strip():
        pytest.skip("elsarticle not installed")
    work = tmp_path / "cmame"
    shutil.copytree(PAPER, work, ignore=shutil.ignore_patterns(
        "*.aux", "*.log", "*.fls", "*.fdb_latexmk", "*.out", "*.bbl", "*.blg", "*.pdf.tmp"))
    for f in (*work.glob("main.pdf"), *work.glob("graphical_abstract.pdf")):
        f.unlink()
    res = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                          "main.tex"], cwd=work, capture_output=True, text=True, timeout=600)
    log = (work / "main.log").read_text(encoding="latin-1")
    assert res.returncode == 0, log[-3000:]
    assert (work / "main.pdf").stat().st_size > 100_000
    assert not re.search(r"(Reference|Citation) .* undefined", log)
    assert "Float too large" not in log
    # the graphical abstract, a separate file at submission: 13 x 5.2 cm, the 2.5:1 of
    # the Guide for Authors' 1328 x 531 pixels
    res = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                          "graphical_abstract.tex"], cwd=work, capture_output=True, text=True,
                         timeout=300)
    glog = (work / "graphical_abstract.log").read_text(encoding="latin-1")
    assert res.returncode == 0, glog[-3000:]
    assert "Overfull" not in glog and "Underfull" not in glog
    pdfinfo = shutil.which("pdfinfo")
    if pdfinfo:
        info = subprocess.run([pdfinfo, str(work / "graphical_abstract.pdf")],
                              capture_output=True, text=True).stdout
        w, h = (float(x) for x in re.search(r"Page size:\s+([\d.]+) x ([\d.]+) pts",
                                            info).groups())
        assert w / h == pytest.approx(2.5, abs=0.01)
    # the text at its foot ends on the page: text that a box pushes off the page is clipped
    # without a warning, and pdftotext leaves it out
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        shown = " ".join(subprocess.run([pdftotext, str(work / "graphical_abstract.pdf"), "-"],
                                        capture_output=True, text=True).stdout.split())
        assert "Held out: seven of eight claims replicated." in shown
    # the supplementary material, a separate file at submission
    res = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                          "supplementary.tex"], cwd=work, capture_output=True, text=True,
                         timeout=300)
    slog = (work / "supplementary.log").read_text(encoding="latin-1")
    assert res.returncode == 0, slog[-3000:]
    assert not re.search(r"(Reference|Citation) .* undefined", slog)
    assert "Overfull" not in slog and "Float too large" not in slog
