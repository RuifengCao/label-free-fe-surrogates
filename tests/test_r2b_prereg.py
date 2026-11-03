"""R2b: every number PREREG_R2B.md quotes is recomputed from the records it
names; its lines are the two configurations' in the generator's order; it is
ASCII; the simulation record is the script's output; and stamping a copy of
the draft does what Sec. 7 says, refusing anything else. Every test holds on
the draft and on the stamped file."""

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
PRE = ROOT / "PREREG_R2B.md"
W8 = ROOT / "records" / "wp8"
F3 = ROOT / "records" / "wp9" / "fine3d"
SIMS = ROOT / "records" / "wp9" / "r2b" / "simulations.json"


def _j(p):
    return json.loads(Path(p).read_text())


def _text():
    return re.sub(r"\s+", " ", PRE.read_text(encoding="utf-8"))


def _has(*phrases):
    t = _text()
    for p in phrases:
        assert p in t, p


def _pct(x, nd=0):
    return f"{100 * x:.{nd}f}%"


def _mod(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ascii_and_lines():
    from fejepa.report import PREREG_PLACEHOLDER, read_prereg_entries

    raw = PRE.read_text(encoding="utf-8")
    assert raw.isascii()
    entries = read_prereg_entries(PRE)
    assert [lab for lab, _ in entries] == list(_mod("make_r2b_configs").ARMS)
    st = _mod("stamp_prereg_r2b")
    tail = raw.rstrip("\n").splitlines()[-1]
    if tail == st.FOOTER_OPEN:                                  # the draft
        assert all(v == PREREG_PLACEHOLDER for _, v in entries)
    else:                                                       # the stamped file
        assert re.fullmatch(r"PREREG_R2B_SHA256 = [0-9a-f]{64}", tail) and st.self_hash_ok(raw)
        from fejepa.report import config_sha256

        for lab, v in entries:
            assert v == config_sha256(_j(ROOT / "configs" / f"{lab}.json"))


def test_section_1_numbers():
    p2b = _j(W8 / "e2" / "baseline" / "report_phase2b.json")
    m = p2b["results"]["p3_transfer"]["metrics"]
    f = np.mean(m["ar"]["fine"]["disp_rel_l2"]["per_seed"])
    i = np.mean(m["ar"]["inband"]["disp_rel_l2"]["per_seed"])
    _has(f"its displacement error is {m['ratio_fine_over_inband']:.2f} times its in-band error "
         f"(seed means {f:.3f} and {i:.4f}; the Phase-2b report's KP4)")
    assert m["ratio_fine_over_inband"] == pytest.approx(f / i)
    amp = _j(W8 / "posthoc" / "amp_phase2b.json")
    sm = amp["seed_means"]
    cs = [amp["seeds"][s]["fine"]["summary"]["c_star_median"] for s in ("s0", "s1", "s2")]
    assert sm["fine"]["c_star_median"] == pytest.approx(np.mean(cs))      # the "median" defined
    _has(f"is {sm['fine']['c_star_median']:.2f} on the fine set against "
         f"{sm['inband']['c_star_median']:.2f} in band",
         f"lowers the fine displacement error by {_pct(1 - sm['fine']['disp_c'] / sm['fine']['disp'])} "
         f"(and the in-band one by {_pct(1 - sm['inband']['disp_c'] / sm['inband']['disp'])})")
    rem = [amp["seeds"][s]["remesh"] for s in ("s0", "s1", "s2")]

    def by_lc(k, lc):
        return float(np.mean([r[k][lc] for r in rem]))
    _has(f"its c_b rises from {by_lc('c_battery_median_by_lc', '0.0906'):.2f} at lc 0.0906 to "
         f"{by_lc('c_battery_median_by_lc', '0.0374'):.2f} at 0.0374, and its predicted energy "
         f"norm falls to {by_lc('u_norm_K_ratio_median_by_lc', '0.0374'):.2f} of its "
         "coarsest-mesh value")
    r2a = _j(F3 / "fine3d_verdict.json")["R2a"]
    c = r2a["conditions"]
    fd, ra = c["fine_displacement"], c["fine_over_inband_ratio"]
    _has(f"S lowered the fine displacement error by {_pct(-fd['rel_change'], 1)} "
         f"({fd['base_mean']:.3f} to {fd['new_mean']:.4f}; tau {_pct(fd['threshold'], 1)})",
         f"the fine / in-band ratio by {_pct(-ra['rel_change'], 1)} ({ra['base_mean']:.2f} to "
         f"{ra['new_mean']:.2f}; tau {_pct(ra['threshold'], 1)})",
         f"the in-band energy gap and displacement error by "
         f"{_pct(-c['K1_inband_energy_gap']['rel_change'], 1)} and "
         f"{_pct(-c['K1_inband_displacement']['rel_change'], 1)}")
    mb, ms = r2a["mechanism"]["b"], r2a["mechanism"]["s"]
    _has(f"its median c* on the fine set was {ms['fine']['c_star_median']['seed_mean']:.2f} (the "
         f"fresh baseline's {mb['fine']['c_star_median']['seed_mean']:.2f})")
    cb_s = ms["remesh"]["c_battery_median_by_lc"]
    un_s = ms["remesh"]["u_norm_K_ratio_median_by_lc"]
    assert f"{max(cb_s.values()):.2f}" == "1.00" and f"{min(cb_s.values()):.2f}" == "0.99"
    assert f"{min(un_s.values()):.2f}" == "1.00" and f"{max(un_s.values()):.2f}" == "1.02"
    _has("its c_b stayed between 1.00 and 0.99 and its predicted energy norm between 1.00 and 1.02")
    cb_b = mb["remesh"]["c_battery_median_by_lc"]
    un_b = mb["remesh"]["u_norm_K_ratio_median_by_lc"]
    _has(f"(the fresh baseline's: c_b {cb_b['0.0906']:.2f} to {cb_b['0.0374']:.2f}, the energy "
         f"norm down to {un_b['0.0374']:.2f})")
    assert min(un_b.values()) == un_b["0.0374"] and max(cb_b.values()) == cb_b["0.0374"]
    assert r2a["r2b"]["recommended"] is True
    _has(f"R2b was recommended (S's fine rel {100 * fd['rel_change']:+.2f}% <= -45%)")
    assert r2a["verdict"] == "SUPPORTED"


def test_section_2_numbers():
    p2b = _j(W8 / "e2" / "baseline" / "report_phase2b.json")
    _has(f"CONFIG_SHA256 `{p2b['provenance']['config_sha256'][:8]}...` in PREREG_PHASE2B")
    for d in p2b["provenance"]["datasets"]:
        _has(f"`{d['dir']}` (manifest `{d['manifest_sha256'][:12]}...`)"
             if d["dir"].endswith("phase2") else f"`{d['dir']}` (`{d['manifest_sha256'][:12]}...`)")
    cfg = _j(ROOT / "configs" / "r2b_s.json")
    e8 = cfg["experiments"]["e8"]
    assert e8["ar_epochs"] * 1024 == 204800 and cfg["pretrain"]["lr"] == 1e-3
    _has("200 epochs at lr 1e-3 (204,800 AR steps per seed), dims 256 / 8 / 8")
    rec = _j(F3 / "scale_factor_3d.json")["sample"]
    _has(f"max|F| / sum|F| on 256 fresh instances of the training family, {rec['median']:.5f}",
         f"on the median instance ({rec['median_over_factor']:.2f} times)")
    assert rec["factor"] == 2.0 ** -10 == _mod("make_fine3d_configs").S3_FACTOR
    _has("Five per arm (ten runs: four more, about 110 h)")
    assert round(4 * 27.3, -1) == 110


def test_section_5_numbers():
    sims = _j(SIMS)
    assert sims["trials"] == 200_000
    _has("200,000 trials per case")
    cv = sims["cv"]
    _has(f"coefficients of variation {_pct(cv['fine'])} for the fine displacement error, "
         f"{_pct(cv['inband_disp'])} and {_pct(cv['inband_egap'])} for the in-band displacement "
         "error and energy gap")
    pw = sims["power"]

    def p(din, d, nd=0):
        return _pct(pw[f"in band {din}"][f"fine -{d}%"], nd)
    _has(f"a support without a true effect occurs in {p('+0%', 0, 1)} of trials, and one without a "
         "true change of the growth -- S lowering the fine and in-band errors alike, by 10% / 30% / "
         "50% / 70% -- in " + " / ".join(p(f"-{d}%", d, 1) for d in (10, 30, 50, 70)))
    _has("With the in-band errors unchanged, a true fine reduction of 30% / 50% / 70% / 90% is "
         "supported in " + " / ".join(p("+0%", d) for d in (30, 50, 70, 90)) + " of trials")
    k1 = 1 - pw["in band +0%"]["fine -90%"]
    assert 0.08 < k1 < 0.12                                     # "about one trial in ten"
    _has(f"with the in-band errors 30% lower, a fine reduction of 50% / 70% is supported in "
         f"{p('-30%', 50)} / {p('-30%', 70, 1)} of trials",
         f"with them 50% lower, one of 50% / 70% / 80% in {p('-50%', 50, 1)} / {p('-50%', 70)} / "
         f"{p('-50%', 80, 1)}",
         f"If S raises them by 10%, K1 fires more often, and a fine reduction of 50% / 70% is "
         f"supported in {p('+10%', 50)} / {p('+10%', 70)}")
    p2b = _j(W8 / "e2" / "baseline" / "report_phase2b.json")["results"]["p3_transfer"]["metrics"]
    rat = [f / i for f, i in zip(p2b["ar"]["fine"]["disp_rel_l2"]["per_seed"],
                                 p2b["ar"]["inband"]["disp_rel_l2"]["per_seed"], strict=True)]
    s2 = sum(np.log1p(cv[k] ** 2) for k in ("fine", "inband_disp"))
    assert round(100 * float(np.sqrt(np.expm1(s2))), -1) == 20          # "about 20%"
    _has("Drawn independently, a seed's fine and in-band errors spread its ratio by about 20%, "
         f"while the Phase-2b seeds' ratios spread by {_pct(_mod('r2b_sims').F3.cv(rat))} ("
         + " / ".join(f"{x:.2f}" for x in rat) + ")")
    an = sims["anchors"]

    def q(name, case="S's spreads the baseline's", nd=0):
        return _pct(an[name]["cases"][case]["p_supported"], nd)
    ct = an["c* on the transformer"]["effect"]
    _has(f"what c* does to the Phase-2b states (the fine error {-100 * ct['fine']:.0f}%, the "
         f"in-band displacement error {100 * ct['inband_disp']:.0f}% and energy gap "
         f"{100 * ct['inband_egap']:.0f}%) is supported in {q('c* on the transformer')} of trials",
         f"({q('c* on the transformer', 'rho 0.5')} with a correlation of 0.5 within a seed",
         f"; {q('c* on the transformer', 'spreads drawn')} with the spreads drawn in every trial",
         "at most 4 times their estimates)",
         f"the same fine reduction with the in-band errors unchanged in "
         f"{q('c* on the transformer, in band unchanged')}")
    cs = an["c* on the transformer"]["cases"]["S's spreads the baseline's"]
    assert cs["p_i"] > 0.999 and cs["p_iii"] > 0.99 and 1 - cs["p_ii"] > 0.98 * (
        1 - cs["p_supported"])                               # "(ii) failing in nearly all the rest"
    sb = an["S on the bottleneck (R2a)"]["effect"]
    _has(f"what S did to the bottleneck ({-100 * sb['fine']:.0f}%, in band "
         f"{100 * sb['inband_disp']:.0f}% and {100 * sb['inband_egap']:.0f}%) in "
         f"{q('S on the bottleneck (R2a)')} ({q('S on the bottleneck (R2a)', 'spreads drawn')} "
         "with the spreads drawn)")
    amp_t, amp_b = _j(W8 / "posthoc" / "amp_phase2b.json"), _j(W8 / "posthoc" / "amp_e2_m1024.json")
    cut = [1 - a["seed_means"]["fine"]["disp_c"] / a["seed_means"]["fine"]["disp"]
           for a in (amp_t, amp_b)]
    assert sims["k"] == pytest.approx(cut[0] / cut[1])
    kk = an["S on the bottleneck times k"]["effect"]
    _has(f"{sims['k']:.2f} times each of those three changes (fine {-100 * kk['fine']:.0f}%, in band "
         f"{100 * kk['inband_disp']:.0f}% and {100 * kk['inband_egap']:.0f}%; {sims['k']:.2f} is the "
         f"ratio of c*'s fine reductions on the transformer and the bottleneck, {_pct(cut[0])} and "
         f"{_pct(cut[1])}) in "
         f"{q('S on the bottleneck times k')} ({q('S on the bottleneck times k', 'spreads drawn')} "
         f"with the spreads drawn, {q('S on the bottleneck times k', 'both arms' + chr(39) + ' spreads twice')} "
         "with both arms' spreads twice their estimates)",
         f"half of S's effect on the bottleneck in {q('half of S on the bottleneck')}",
         f"c* on the bottleneck, for reference, in {q('c* on the bottleneck (for reference)')}")
    fo = "S on the bottleneck times k on the fine set only"
    eo = an[fo]["effect"]
    assert eo["fine"] == pytest.approx(kk["fine"]) and eo["inband_disp"] == sb["inband_disp"]
    _has(f"with its fine error {sims['k']:.2f} times S's on the bottleneck "
         f"({-100 * eo['fine']:.0f}%) but its in-band errors lowered as the bottleneck's were "
         f"({100 * eo['inband_disp']:.0f}% and {100 * eo['inband_egap']:.0f}%), the support falls "
         f"to {q(fo)} ({q(fo, 'spreads drawn')} with the spreads drawn, {q(fo, 'rho 0.5')} with the "
         "correlation of 0.5)")
    assert an["S on the bottleneck times k"]["effect"]["fine"] == pytest.approx(
        sims["k"] * sb["fine"])
    sd = sims["seeds"]["in band -30%; fine -30%"]
    _has(f"(c* on the Phase-2b states: {q('c* on the transformer')} to "
         f"{q('c* on the transformer', 'five seeds per arm')}; {sims['k']:.2f} times S's effect on "
         f"the bottleneck: {q('S on the bottleneck times k')} to "
         f"{q('S on the bottleneck times k', 'five seeds per arm', 1)}; the case of the lower fine "
         f"reduction alone: {q(fo)} to {q(fo, 'five seeds per arm')}) and falls where it does not "
         f"(the fine and in-band errors both 30% lower: {_pct(sd['3'], 1)} to {_pct(sd['5'], 1)})")
    val = sims["value"]["by_anchor"]
    assert len(val) == 7 == len(an)
    for name, modes in val.items():
        assert set(modes) == {"estimates", "spreads drawn"}
        for v in modes.values():
            assert set(v) == {"1.5", "2", "3"} and all(x["5"] < x["3"] for x in v.values()), name
    _has("the expected value of five seeds is below that of three at each of the seven effects "
         "of `anchors`, with the spreads at their estimates and drawn")


def test_section_6_and_8_numbers():
    p2b = _j(W8 / "e2" / "baseline" / "report_phase2b.json")
    eg = p2b["results"]["p3_transfer"]["metrics"]["ar"]["fine"]["energy_gap_rel"]["per_seed"]
    sims = _mod("r2b_sims")
    _has(f"spread by {_pct(sims.F3.cv(eg))} across seeds, " + " / ".join(f"{v:.3f}" for v in eg))
    amp_b = _j(F3 / "return" / "posthoc" / "amp_r2a_b_m1024.json")
    r2a = _j(F3 / "fine3d_verdict.json")["R2a"]
    _has(f"on the bottleneck it did: {r2a['conditions']['fine_displacement']['new_mean']:.4f} "
         f"against {amp_b['seed_means']['fine']['disp_c']:.3f}")
    assert hashlib.sha256((F3 / "return" / "r2a_b_m1024" / "report.json").read_bytes()
                          ).hexdigest() == amp_b["report_sha256"]
    vals = r2a["values"]
    p3m = _j(W8 / "e2" / "baseline" / "report_phase2b.json")["results"]["p3_transfer"]["metrics"]
    _has(f"against KP4's line of {p2b['config']['kills']['KP4_transfer_ratio']:g} (PREREG_PHASE2B; "
         f"the Phase-2b transformer's {p3m['ratio_fine_over_inband']:.2f} retired its transfer zone)",
         f"({vals['s']['ratio_of_seed_means']:.2f} against {vals['b']['ratio_of_seed_means']:.2f}, "
         "the ratios of the seed means)")
    amp = _j(W8 / "posthoc" / "amp_phase2b.json")
    s0 = amp["seeds"]["s0"]
    _has(f"{s0['inband']['summary']['seconds']:.0f} s in band, "
         f"{s0['fine']['summary']['seconds']:,.0f} s fine, {s0['remesh']['seconds']:.0f} s for the "
         "remesh pass")
    assert "AR 3 x 27.3 h" in (ROOT / "DEVIATIONS_PHASE2.md").read_text()
    r3 = _j(F3 / "return" / "r3_eft_b16" / "report.json")
    ev = [v["seconds"]["evaluate"] for v in r3["per_seed"].values()]
    _has(f"the transformer on the same two sets in {np.mean(ev) / 60:.0f} min per seed")
    st = (F3 / "return" / "session" / "status.txt").read_text()
    prov = (F3 / "return" / "provenance.txt").read_text()
    from datetime import datetime

    def at(pattern, text):
        return datetime.strptime(re.search(pattern, text).group(1), "%Y-%m-%d %H:%M:%S")
    span = {}
    for arm in ("b", "s"):
        start = at(rf"r2a_{arm}_m1024\.log start (\S+ \S+)", st)
        end = at(rf"r2a_{arm}_m1024\.log exit=0 (\S+ \S+)", st)
        s5 = at(r"(\S+ \S+)\.\d+ \+0800 ar_p1024_s5\.pt", prov.split(
            f"runs/fine3d/r2a_{arm}_m1024/e8_states/:")[1])
        span[arm] = {"all": end - start, "train": s5 - start, "p3": end - s5}
    extra = {k: (span["s"][k] - span["b"][k]).total_seconds() / 60 for k in span["b"]}
    _has(f"on the bottleneck S's arm took {extra['all']:.0f} min longer than its baseline, "
         f"{extra['train']:.0f} min in training and {extra['p3']:.0f} min in P3; fine3d's status file")
    per_arm = 3 * 27.3 + 1.5
    total = 2 * per_arm + 2 * 0.75
    _has(f"about {per_arm:.0f} h per arm", f"about {round(total, -1):.0f} h, seven days, in all")
    assert 6.5 < total / 24 < 7.5
    assert _text().count("83 h") == 2                           # Sec. 7 and Sec. 8


def test_simulations_record_is_the_scripts_output(tmp_path):
    out = tmp_path / "sims.json"
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "r2b_sims.py"), "--out", str(out)],
                       capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr[-2000:]
    assert out.read_text() == SIMS.read_text()


def test_the_simulation_reuses_fine3ds_draws():
    """r2b_sims imports fine3d_sims' draw, guard and spread draws (one model
    for both records) and reads the same records."""
    s, f = _mod("r2b_sims"), _mod("fine3d_sims")
    assert s.F3.P2B == f.P2B and s.F3.AMP_T == f.AMP_T and s.F3.AMP_B == f.AMP_B
    assert (s.F3.GUARD_BAND, s.F3.GUARD_K) == (f.GUARD_BAND, f.GUARD_K) == (0.10, 2.0)
    f3 = _j(F3 / "simulations.json")
    sims = _j(SIMS)
    assert sims["cv"] == f3["r2b"]["cv"] and sims["k"] == f3["r2b"]["k"]


# ------------------------------------------------------------- the stamp --

def _draft_of(text, mod):
    """The draft a file came from: the file itself, or the stamped file with
    its lines, status and footer opened again (and the stamp date)."""
    from fejepa.report import PREREG_PLACEHOLDER

    pre, post = mod.stamped_status("\0").split("\0")         # the script's own wording
    m = re.search(re.escape(pre) + "(.+?)" + re.escape(post), text)
    if m is None:
        return text, None
    text = text.replace(m.group(0), mod.DRAFT_STATUS)
    text = re.sub(r"^(CONFIG_SHA256\[[^\]]+\] = )[0-9a-f]{64}$", rf"\g<1>{PREREG_PLACEHOLDER}",
                  text, flags=re.M)
    text = re.sub(r"^PREREG_R2B_SHA256 = [0-9a-f]{64}$", mod.FOOTER_OPEN, text, flags=re.M)
    return text, m.group(1)


def test_the_approved_draft_is_pinned():
    mod = _mod("stamp_prereg_r2b")
    draft, _ = _draft_of(PRE.read_text(encoding="utf-8"), mod)
    assert hashlib.sha256(draft.encode("utf-8")).hexdigest() == mod.DRAFT_SHA256
    assert draft.count(mod.DRAFT_STATUS) == 1


def test_stamping_the_draft(tmp_path):
    from fejepa.report import config_sha256, read_prereg_entries, verify_prereg

    mod = _mod("stamp_prereg_r2b")
    committed = PRE.read_text(encoding="utf-8")
    draft, date = _draft_of(committed, mod)
    pf = tmp_path / "PREREG_R2B.md"
    pf.write_text(draft, encoding="utf-8")
    ok, here, want = mod.src_tree_ok()
    assert ok, (f"src is tree {here}, not the regression's {want}: run "
                "scripts/regress_against_branch.py again and update records/wp9/README.md")
    res = mod.stamp(pf, ROOT / "configs", date or "4 November 2026")
    text = pf.read_text(encoding="utf-8")
    for label, value in read_prereg_entries(pf):
        assert value == config_sha256(_j(ROOT / "configs" / f"{label}.json")) == \
            res["config_sha256"][label]
    assert mod.self_hash_ok(text) and text.rstrip("\n").endswith(res["prereg_sha256"])
    assert mod.stamped_status(date or "4 November 2026") in text and mod.DRAFT_STATUS not in text
    assert len(text.splitlines()) == len(draft.splitlines())
    if date is not None:
        assert text == committed
    with pytest.raises(SystemExit, match="not the approved draft"):
        mod.stamp(pf, ROOT / "configs", "4 November 2026")
    for label in res["config_sha256"]:                          # the runner's guard accepts
        assert verify_prereg(_j(ROOT / "configs" / f"{label}.json"), pf, label=label) == \
            res["config_sha256"][label]


def test_stamping_refuses_anything_but_the_draft(tmp_path, monkeypatch):
    mod = _mod("stamp_prereg_r2b")
    draft, _ = _draft_of(PRE.read_text(encoding="utf-8"), mod)
    pf = tmp_path / "PREREG_R2B.md"
    pf.write_text(draft, encoding="utf-8")
    with pytest.raises(SystemExit, match="--date"):
        mod.stamp(pf, ROOT / "configs", "2026-11-04")
    monkeypatch.setattr(mod, "src_tree_ok", lambda: (True, "a" * 40, "a" * 40))
    cfgs = tmp_path / "configs"
    shutil.copytree(ROOT / "configs", cfgs)
    c = _j(cfgs / "r2b_s.json")
    c["experiments"]["e8"]["ar_epochs"] = 100
    (cfgs / "r2b_s.json").write_text(json.dumps(c, indent=1) + "\n")
    with pytest.raises(SystemExit, match="not the generator's output"):
        mod.stamp(pf, cfgs, "4 November 2026")
    edited = draft.replace("tau = max(10%, 2 x SE_rel)", "tau = max(5%, 2 x SE_rel)")
    assert edited != draft
    pf.write_text(edited, encoding="utf-8")
    with pytest.raises(SystemExit, match="not the approved draft"):
        mod.stamp(pf, ROOT / "configs", "4 November 2026")
    pf.write_text(draft, encoding="utf-8")
    monkeypatch.setattr(mod, "src_tree_ok", lambda: (False, "b" * 40, "a" * 40))
    with pytest.raises(SystemExit, match="not the tree the regression ran"):
        mod.stamp(pf, ROOT / "configs", "4 November 2026")
    assert pf.read_text(encoding="utf-8").count("<fill before tagging>") == 2   # untouched


def test_the_runner_refuses_the_draft(tmp_path):
    """A run-config of either arm against the draft refuses to start (its lines
    are open), on the draft as on the stamped file (whose draft is rebuilt
    here); against the committed file it is verified once that is stamped."""
    pytest.importorskip("torch")
    from fejepa.experiments.runner import run_config
    from fejepa.report import PREREG_PLACEHOLDER, read_prereg_entries

    draft, _ = _draft_of(PRE.read_text(encoding="utf-8"), _mod("stamp_prereg_r2b"))
    pf = tmp_path / "PREREG_R2B.md"
    pf.write_text(draft, encoding="utf-8")
    stamped = all(v != PREREG_PLACEHOLDER for _, v in read_prereg_entries(PRE))
    for name in ("r2b_b", "r2b_s"):
        cfg = dict(_j(ROOT / "configs" / f"{name}.json"), prereg_file=str(pf))
        p = tmp_path / f"{name}.json"
        p.write_text(json.dumps(cfg))
        out = run_config(p, dry_run=True)
        assert out["prereg_status"].startswith("would refuse") and "unstamped" in out["prereg_status"]
        own = run_config(ROOT / "configs" / f"{name}.json", dry_run=True)["prereg_status"]
        assert (own == "verified") if stamped else own.startswith("would refuse")
