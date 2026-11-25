"""Check a host for gate G-F2.1 on a reduced configuration: the tiny mesh, two small development presets in the
place of the two cycles, four of the development's members, two extra training members and a sample of two drawn
with a day of the past (20260102, which the gate's configuration lists among the used seeds, so that it can never
be the gate's). Nothing of the gate is drawn or trained, and no stamp is needed.

    python -I f21/smoke.py --out DIR [--repo REPO] [--device cuda] [--workers 2] [--stage-minutes 45]
    python -I f21/__main__.py smoke --out DIR [--device cuda] [--workers 2]      (the same, as a command of the gate)

Every step of the gate runs once, in the gate's order, in three stages:
    data        the three data folders with their labels and checks; a sample whose seed is a used seed, lies before
                or after the configured days or is a day that has not come is refused, and so is another
                configuration in the sample's folder;
    train       the two cycles of the three seeds (the first cycle of one seed is interrupted after an epoch and
                resumed); a second cycle without its first, a seed that is not the gate's, a cycle whose
                end-of-cycle predictions are missing, predictions on the sample before every training has ended and
                an evaluation of the sample before every seed has its record are refused; the predictions of each
                finished run on the sample, which are not made twice; the verdict is INCOMPLETE before the last
                prediction and before the evaluation;
    evaluate    the two evaluations and the verdict; the exact reference at the predicted rotation of the measuring
                ring is solved for the judged reading and for no other; the evaluations record what they read.
Writes DIR/smoke.json with the machine, the seconds of each stage and the verdict (of stand-in networks: its value
means nothing).

Each stage runs in a process of its own, started afresh (spawned), as each command of the gate is a process of its
own, with the settings the commands give themselves: one thread for linear algebra in the stages that open pools of
worker processes, and the training stage without the sparse solver's libraries (FEJOINT_SOLVER=legacy, as the
commands train and predict). The pools, which are forked where the system can (c22.data.pool), are then forked from
processes that have not used torch. A pool forked from a process that has trained with torch can wait for ever on a
lock that another thread held at the fork: the first form of this check, which ran everything in one process, did so
on 25 November 2026. A stage that has not ended after --stage-minutes is ended with its worker processes, and the
check fails: a host on which a stage waits is reported, not waited for.

The reduced configuration accepts days of January 2026 only as its sample's seed, so that no call with it can draw
with a day that the stamp of the gate could fall on.
"""
import argparse
import copy
import json
import os
import platform
import signal
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True            # also in a spawned process, which runs this file's top level first
ROOT = Path(__file__).resolve().parents[1]
SAMPLE_SEED = 20260102
STAGES = ("data", "train", "evaluate")
THREAD_VARIABLES = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")


def reduced() -> dict:
    from f2 import data, devconfig
    from f21.config import config, sha256

    G = copy.deepcopy(config())
    G["gate"] = "G-F2.1 host check (reduced)"
    r = G["recipe"]
    r["mesh"], r["only"] = "tiny", ["train_0000", "train_0001", "eval_0000", "tested_B-13_nominal"]
    cfgs = {}
    for cyc, name in (("first", "dry"), ("second", "dry_more_ux")):
        c = devconfig.config(name)
        c["data"]["mesh"] = "tiny"
        r[cyc]["preset"], r[cyc]["config_sha256"] = name, sha256(c)
        cfgs[cyc] = c
    r["data_sha256"] = data.data_sha256(cfgs["first"])
    r["second"]["extra_data_sha256"] = data.data_sha256(data.extra_config(cfgs["second"]))
    s = G["sample"]
    s["n"], s["seed"], s["not_before"], s["not_after"] = 2, SAMPLE_SEED, 20260101, 20260131
    s["family_seeds_used_before_stamp"] = [x for x in s["family_seeds_used_before_stamp"] if x != SAMPLE_SEED]
    G["reference"]["linear_solver"] = None                      # the host check runs with the solver the host has
    return G


def _with_seed(G: dict, seed: int, used: bool | None = None) -> dict:
    """The reduced configuration with another seed of the sample; used: whether that seed is on the copy's list of
    used seeds (None: the list as it is)."""
    G2 = copy.deepcopy(G)
    G2["sample"]["seed"] = seed
    if used is not None:
        rest = [x for x in G2["sample"]["family_seeds_used_before_stamp"] if x != seed]
        G2["sample"]["family_seeds_used_before_stamp"] = rest + ([seed] if used else [])
    return G2


def _folders(out: Path):
    return out / "data", out / "data_thin", out / "data_gate", out / "runs", out / "runs_gate"


def _refused(fn, *a, match: str, **k) -> bool:
    """True if the call is refused with an error whose text holds match (another error is not the refusal meant)."""
    try:
        fn(*a, **k)
    except (RuntimeError, ValueError) as err:
        return match in str(err)
    return False


def stage_data(G: dict, out: Path, device: str, workers: int) -> dict:
    from f21 import gate
    from f21.config import check_sample_seed

    d, dx, dg, runs, rg = _folders(out)
    checks, seconds = {}, {}
    t = time.time()
    gate.generate(G, "train", d, workers=workers)
    gate.generate(G, "thin", dx, workers=workers)
    gate.label(G, "train", d, workers=workers)
    assert gate.check_labels(G, "train", d, workers=workers)["ok"]
    seconds["development_data"] = round(time.time() - t, 1); t = time.time()
    checks["used_seed_refused"] = _refused(gate.generate, _with_seed(G, 20260103, used=True), "sample", dg,
                                           match="drew members of the family before the stamp")
    checks["early_seed_refused"] = _refused(gate.generate, _with_seed(G, 20251231), "sample", dg, match="lies before")
    checks["late_seed_refused"] = _refused(gate.generate, _with_seed(G, 20260201), "sample", dg, match="lies after")
    checks["day_that_has_not_come_refused"] = _refused(check_sample_seed, G, today=20260101, match="has not come")
    checks["nothing_written_by_a_refused_sample"] = not dg.exists()
    gate.generate(G, "sample", dg, workers=workers)
    checks["other_configuration_refused_in_the_sample_folder"] = _refused(
        gate.generate, _with_seed(G, 20260103, used=False), "sample", dg, match="another gate configuration")
    gate.generate(G, "sample", dg, workers=workers)                                 # again: nothing changes
    assert gate.label(G, "sample", dg, workers=workers) == G["sample"]["n"]
    assert gate.check_labels(G, "sample", dg, workers=workers)["ok"]
    seconds["sample"] = round(time.time() - t, 1)
    return {"checks": checks, "seconds": seconds}


def stage_train(G: dict, out: Path, device: str, workers: int) -> dict:
    import numpy as np
    import scipy
    import torch

    from f21 import gate

    d, dx, dg, runs, rg = _folders(out)
    cuda = device == "cuda"
    machine = {"numpy": np.__version__, "scipy": scipy.__version__, "torch": torch.__version__,
               "gpu": torch.cuda.get_device_name(0) if cuda else None,
               "gpu_memory_GiB": round(torch.cuda.mem_get_info()[1] / 2 ** 30, 2) if cuda else None}
    checks, seconds = {}, {}
    seeds = G["recipe"]["seeds"]
    t = time.time()
    checks["second_cycle_without_first_refused"] = _refused(gate.train, G, "second", seeds[0], d, runs, device=device,
                                                            extra_dir=dx, match="has not finished")
    checks["other_seed_refused"] = _refused(gate.train, G, "first", 0, d, runs, device=device,
                                            match="not one of the gate's")
    h = gate.train(G, "first", seeds[0], d, runs, device=device, stop_after_epoch=1)
    assert h["status"] == "paused", h["status"]
    assert gate.cycle_state(G, runs, "first", seeds[0]) == "under way"
    assert gate.train(G, "first", seeds[0], d, runs, device=device)["status"] == "finished"
    first = gate.run_dir(G, runs, "first", seeds[0])
    (first / "condense.json").rename(first / "condense.json.aside")          # as if cut off in its predictions
    checks["a_cycle_without_its_predictions_is_not_finished"] = (
        gate.cycle_state(G, runs, "first", seeds[0]) == "under way"
        and _refused(gate.train, G, "second", seeds[0], d, runs, device=device, extra_dir=dx, match="has not finished"))
    (first / "condense.json.aside").rename(first / "condense.json")
    assert gate.train(G, "second", seeds[0], d, runs, device=device, extra_dir=dx)["status"] == "finished"
    checks["no_prediction_on_the_sample_before_every_training_has_ended"] = _refused(
        gate.predict_sample, G, seeds[0], runs, dg, rg, device=device, match="before every training of the gate has ended")
    for s in seeds[1:]:
        h1 = gate.train(G, "first", s, d, runs, device=device)
        h2 = gate.train(G, "second", s, d, runs, device=device, extra_dir=dx)
        assert h1["status"] == "finished" and h2["status"] == "finished", (h1["status"], h2["status"])
    assert json.loads((first / "history.json").read_text())["resumes"] == [1]
    seconds["training"] = round(time.time() - t, 1); t = time.time()
    for s in seeds[:-1]:
        assert gate.predict_sample(G, s, runs, dg, rg, device=device)["status"] == "finished"
    checks["no_evaluation_of_the_sample_before_every_seed_has_its_record"] = _refused(
        gate.evaluate, G, "sample", rg, dg, workers=workers, match="neither predictions on the sample nor a record")
    v = gate.verdict(G, runs, d, dg, rg)
    checks["incomplete_before_the_last_prediction"] = v["verdict"] == "INCOMPLETE" and v["waiting_seeds"] == [seeds[-1]]
    h = gate.predict_sample(G, seeds[-1], runs, dg, rg, device=device)
    assert h["status"] == "finished"
    checks["a_prediction_is_not_made_twice"] = gate.predict_sample(G, seeds[-1], runs, dg, rg, device=device) == h
    checks["incomplete_before_the_evaluation"] = gate.verdict(G, runs, d, dg, rg)["verdict"] == "INCOMPLETE"
    checks["sparse_solver_not_loaded_where_torch_ran"] = "pypardiso" not in sys.modules
    seconds["predictions"] = round(time.time() - t, 1)
    return {"checks": checks, "seconds": seconds, "machine": machine}


def stage_evaluate(G: dict, out: Path, device: str, workers: int) -> dict:
    from f21 import gate

    d, dx, dg, runs, rg = _folders(out)
    checks, seeds = {}, G["recipe"]["seeds"]
    t = time.time()
    dv = gate.evaluate(G, "dev", runs, d, workers=workers)
    ev = gate.evaluate(G, "sample", rg, dg, workers=workers)
    seconds = {"evaluations": round(time.time() - t, 1)}
    checks["torch_not_loaded_where_the_pools_were_forked"] = "torch" not in sys.modules
    exact = G["reported"]["exact"]
    checks["exact_for_the_judged_reading_only"] = (
        ev.get("exact_readings") == sorted(exact["readings"]) == [G["judged"]["reading"]]
        and not any(exact["quantity"] in row for key, x in ev["rows"].items() if key.split("|")[1] not in exact["readings"]
                    for rows in x["members"].values() for row in rows))
    checks["the_evaluations_record_what_they_read"] = all(
        sorted(e["inputs"]["predictions"]) == [str(s) for s in seeds] and all(e["inputs"]["predictions"].values())
        and e["inputs"]["manifest_sha256"] and e["inputs"]["ledger_sha256"] for e in (dv, ev))
    v = gate.verdict(G, runs, d, dg, rg)
    n = G["sample"]["n"] * 7
    checks["verdict_is_complete"] = (v["verdict"] in ("PASS", "FAIL") and v["complete"]
                                     and sorted(v["per_seed"]) == [str(s) for s in seeds]
                                     and all(st["n"] == n for st in v["per_seed"].values())
                                     and sorted(v["exact"]["per_seed"]) == [str(s) for s in seeds]
                                     and sorted(v.get("development_members", {})) == [str(s) for s in seeds])
    return {"checks": checks, "seconds": seconds,
            "verdict": {k: v.get(k) for k in ("verdict", "why", "complete", "per_seed", "across_seeds", "sample", "exact")}}


def _stage(name: str, out: str, repo: str, device: str, workers: int) -> None:
    """One stage, in a process of its own: its result goes to DIR/stage_<name>.json."""
    if hasattr(os, "setsid"):                                   # a group of its own, so that it can be ended with its workers
        try:
            os.setsid()
        except OSError:
            pass
    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    if (Path(repo) / "src").is_dir():
        sys.path.insert(1, str(Path(repo) / "src"))             # behind the gate's packages
    if name == "train":                                         # as the commands train and predict (f21/__main__.py)
        os.environ["FEJOINT_SOLVER"] = "legacy"
    r = {"data": stage_data, "train": stage_train, "evaluate": stage_evaluate}[name](reduced(), Path(out), device, workers)
    tmp = Path(out) / f"stage_{name}.json.tmp"
    with open(tmp, "w", encoding="ascii", newline="\n") as fh:
        fh.write(json.dumps(r, indent=1))
    os.replace(tmp, Path(out) / f"stage_{name}.json")


def main(argv=None) -> int:
    import multiprocessing as mp

    here = Path(__file__).resolve().parent                      # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="f21-smoke")
    ap.add_argument("--out", required=True)
    ap.add_argument("--repo")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--stage-minutes", type=float, default=45.0)
    args = ap.parse_args(argv)
    repo = Path(args.repo) if args.repo else ROOT.parent
    if (repo / "src").is_dir():
        sys.path.insert(1, str(repo / "src"))
    from f21.config import sha256

    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} is not empty; give a new folder (nothing is deleted)")
    out.mkdir(parents=True, exist_ok=True)
    G = reduced()
    rep = {"what": G["gate"], "config_sha256": sha256(G), "sample_seed": G["sample"]["seed"], "device": args.device,
           "workers": args.workers,
           "machine": {"platform": platform.platform(), "python": platform.python_version(), "processors": os.cpu_count()},
           "seconds": {}, "checks": {}, "stages": {}}
    ctx = mp.get_context("spawn")
    for name in STAGES:
        before = {k: os.environ.get(k) for k in THREAD_VARIABLES}
        if name != "train":                                     # one thread for linear algebra, as a processor step
            for k in THREAD_VARIABLES:
                os.environ[k] = "1"
        try:
            p = ctx.Process(target=_stage, args=(name, str(out), str(repo), args.device, args.workers))
            p.start()
            p.join(args.stage_minutes * 60.0)
            if p.is_alive():                                    # a stage that waits: ended, with its workers
                rep["checks"][f"stage_{name}_ended_within_{args.stage_minutes:g}_minutes"] = False
                try:
                    os.killpg(p.pid, signal.SIGKILL) if hasattr(os, "killpg") else p.terminate()
                except OSError:
                    p.terminate()
                p.join(60)
        finally:
            for k, v in before.items():
                os.environ.pop(k, None)
                if v is not None:
                    os.environ[k] = v
        rep["stages"][name] = "ended with exit code " + str(p.exitcode)
        fp = out / f"stage_{name}.json"
        if p.exitcode != 0 or not fp.exists():
            rep["checks"][f"stage_{name}_ended_without_error"] = False
            break
        r = json.loads(fp.read_text())
        rep["checks"].update(r["checks"]); rep["seconds"].update(r["seconds"])
        rep["machine"].update(r.get("machine", {}))
        if "verdict" in r:
            rep["verdict"] = r["verdict"]
    rep["ok"] = "verdict" in rep and all(rep["checks"].values())
    with open(out / "smoke.json", "w", encoding="ascii", newline="\n") as fh:
        fh.write(json.dumps(rep, indent=1))
    print(json.dumps({"ok": rep["ok"], "checks": rep["checks"], "seconds": rep["seconds"], "stages": rep["stages"],
                      "verdict": rep.get("verdict", {}).get("verdict")}))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
