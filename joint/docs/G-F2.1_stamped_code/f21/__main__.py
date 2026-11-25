"""Command line of gate G-F2.1. Run by its path from the work folder; the repository package is looked for in
../src next to the folder that holds fejoint, c2, c22, f2 and f21, or at --repo (python -I -m does not search the
current folder, so the script is run by its path):

    python -I f21/__main__.py write-config --out FILE [--config-sha SHA]
                                                        (prints the configuration hash, the pins, the hashes of the
                                                         stamped files, the library versions and the linear solver)
    python -I f21/__main__.py generate --what train|thin|sample --data DIR --config-sha SHA [--workers W]
                                                        (exports, each with its preload solve; the sample is drawn
                                                         with the configuration's seed)
    python -I f21/__main__.py label --what train|sample --data DIR --config-sha SHA [--workers W]
    python -I f21/__main__.py check-labels --what train|sample --data DIR --config-sha SHA [--workers W]
    python -I f21/__main__.py train --cycle first|second --seed S --data DATA --runs RUNS --config-sha SHA
                                    [--extra-data DATA_THIN] [--max-hours H] [--device cuda]
    python -I f21/__main__.py predict --seed S --runs RUNS --data-gate DATA_GATE --runs-gate RUNS_GATE
                                      --config-sha SHA [--device cuda]
    python -I f21/__main__.py evaluate --what dev --runs RUNS --data DATA --config-sha SHA [--workers W]
    python -I f21/__main__.py evaluate --what sample --runs RUNS_GATE --data DATA_GATE --config-sha SHA [--workers W]
    python -I f21/__main__.py verdict --runs RUNS --data DATA --data-gate DATA_GATE --runs-gate RUNS_GATE --out DIR
                                      --config-sha SHA [--final]
    python -I f21/__main__.py chain --do "COMMAND" --do "COMMAND"                 (one after another)
    python -I f21/__main__.py together --do "COMMAND" --do "COMMAND" --logs DIR   (at the same time)
    python -I f21/__main__.py smoke --out DIR [--device cuda] [--workers W]       (the host check, f21/smoke.py)

Refusals. Every command but write-config and smoke refuses to run unless --config-sha equals the hash of the
configuration in f21/config.py and unless the code is the stamped code: docs/G-F2.1_code.sha256, which is written
at the stamp, must lie beside the packages and hold the SHA-256 of every file of CODE and of DATA as it is now, and
no bytecode folder may lie in the stamped packages (Python would run a cached file in the place of a stamped
source). The repository holds no such file before the stamp, so that from a checkout of an earlier state nothing
of the gate can be drawn or trained by these commands. The check compares the files with the stamp file and no
more: that the stamp file is the one of the stamp's commit is checked when that commit is read back from the
repository (RUNBOOK_F21.md, 0a to 0c). The sample's seed is part of the configuration (f21/stamp_day.py), so that
the configuration hash refuses every other seed; the functions configure the gate's sample only while one of
these commands runs, after its stamp check (f21/config.py). What the commands refuse beyond that is said in
f21/gate.py: a second cycle without its seed's
finished first cycle, a training not yet started after a stop for good, predictions on the sample before every
training has ended, an evaluation of the sample before every seed has predictions or a record that it has none, an
evaluation on labels that fail their checks, a verdict on an evaluation whose inputs are not those on record, and
the commands that solve on a host whose linear solver is not the configured one. smoke checks a host on a reduced
configuration (f21/smoke.py); it draws nothing of the gate and needs no stamp. chain and together run commands of
this file, each under the same refusals; chain takes the data commands only, because its commands share a process.

Exit codes, for a queue that stops on a code other than 0. write-config with --config-sha: 0 only if the hash is
the given one, the code is the stamped code and the host's linear solver is the configured one. generate: 0 only if
every preload converged and is on target. check-labels: 0 only if the labels pass. train: 0 unless the run stopped
on a non-finite value (a paused run ends with 0 and goes on when the command is run again). predict: 0 unless the
predictions are not finite (a seed without a finished run, after a stop for good, gets its record and 0). evaluate:
0 only if the evaluation was written. verdict: 0 unless --final is given and the verdict is INCOMPLETE or, after a
stop for good, what the finished seeds gave is not on record yet; its files are written and its text is printed in
every case. smoke: 0 only if every check of the host check holds.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

sys.dont_write_bytecode = True            # also in a spawned worker process, which runs this file's top level first
ROOT = pathlib.Path(__file__).resolve().parents[1]
STAMP_FILE = ROOT / "docs" / "G-F2.1_code.sha256"
# every file of the packages that the gate imports (tests/test_f21.py compares this list with the imports)
CODE = ["f21/__init__.py", "f21/__main__.py", "f21/config.py", "f21/gate.py", "f21/smoke.py", "f21/stamp_day.py",
        "c2/__init__.py", "c2/config.py", "c2/data.py", "c2/evaluate.py", "c2/family.py", "c2/instance.py",
        "c2/model.py", "c2/torch_energy.py", "c2/train.py", "c22/__init__.py", "c22/condense.py",
        "c22/config.py", "c22/data.py", "c22/train.py", "f1/__init__.py", "f1/config.py", "f1/materials.py",
        "f2/config.py", "f2/data.py", "f2/devconfig.py", "f2/evaluate.py", "f2/family.py", "f2/instance.py",
        "f2/model.py", "f2/precond.py", "f2/prolong.py", "f2/torch_energy.py", "f2/train.py",
        "fejoint/__init__.py", "fejoint/chs.py", "fejoint/contact.py", "fejoint/hex8i.py", "fejoint/joint.py",
        "fejoint/linsolve.py", "fejoint/nlhex.py", "fejoint/nlsolve.py", "fejoint/plasticity.py",
        "fejoint/tstub.py", "fejoint/tstub_pl.py"]
# the data files that the family's laws are read from (the coupon curves of gate G-F1; f1/config.py, f2/family.py):
# stamped with the code, because a change of them changes every member
DATA = ["f1/data/material_bolt_eng.csv", "f1/data/material_chs_eng.csv", "f1/data/material_plate13_eng.csv"]
POOL_COMMANDS = ("generate", "label", "check-labels", "evaluate")     # they open pools of worker processes
THREAD_VARIABLES = ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
LIBRARIES = ("numpy", "scipy", "pypardiso", "mkl", "torch")


def code_hashes() -> dict:
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE + DATA}


def bytecode_folders() -> list:
    """The __pycache__ folders inside the stamped packages (none on a host that runs these commands only)."""
    return sorted(str(p.relative_to(ROOT)) for d in sorted({f.split("/")[0] for f in CODE})
                  for p in (ROOT / d).rglob("__pycache__"))


def not_stamped() -> str | None:
    """None if the code is the stamped code; otherwise what is wrong."""
    if not STAMP_FILE.is_file():
        return f"{STAMP_FILE.name} is not there: the gate is not stamped"
    want = {}
    for line in STAMP_FILE.read_text().splitlines():
        if line.strip():
            h, name = line.split(None, 1)
            want[name.strip()] = h
    have = code_hashes()
    if sorted(want) != sorted(have):
        return "the stamp file does not list the files of the code"
    bad = [f for f in have if want[f] != have[f]]
    if bad:
        return f"files differ from the stamped code: {bad}"
    cached = bytecode_folders()
    return f"bytecode folders lie in the stamped packages: {cached}; remove them" if cached else None


def library_versions() -> dict:
    from importlib import metadata

    out = {"python": sys.version.split()[0]}
    for name in LIBRARIES:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def verdict_text(v: dict) -> str:
    J = v["judged"]
    L = [f"Gate {v['gate']}: {v['verdict']}", v["why"], "",
         f"judged: {J['reading']} reading, {J['quantity']}, per cent; lines "
         + ", ".join(f"{k} {100 * x:g}" for k, x in J["lines"].items())]
    if not v.get("complete"):
        L.append("what is to be reported is not all on record yet")
    if "sample" in v:
        s = v["sample"]
        L.append(f"sample: seed {s['seed']}, {s['members']} members, {s['levels']} levels, {s['pairs']} pairs; "
                 f"{s['thin_members']} members in the thin band")
    for seed, st in v["per_seed"].items():
        nf = v["reported"][seed]["not_finite_pairs"]
        L.append(f"  seed {seed}: median {100 * st['median']:.3f}  p90 {100 * st['p90']:.3f}  largest "
                 f"{100 * st['max']:.2f}  pairs not finite {st['not_finite']}"
                 + (": " + ", ".join(f"{i} level {l + 1}" for i, l in nf[:20]) + (" ..." if len(nf) > 20 else "") if nf else ""))
    if "across_seeds" in v:
        L.append("  across seeds (median): " + "  ".join(f"{k} {100 * x:.3f}" for k, x in v["across_seeds"].items()))
    X = v.get("exact", {})
    if X.get("per_seed"):
        L += ["", f"reported, not judged: {X['quantity']} (the reference solved at the predicted rotation of the "
                  f"measuring ring), {X['reading']} reading"]
        for seed, st in X["per_seed"].items():
            d = v["reported"][seed].get("first_order_minus_exact", {})
            L.append(f"  seed {seed}: median {100 * st['median']:.3f}  p90 {100 * st['p90']:.3f}  largest "
                     f"{100 * st['max']:.2f}  pairs not finite {st['not_finite']}"
                     + (f"; |judged - exact| in percentage points: median {100 * d['median']:.3f}  p90 "
                        f"{100 * d['p90']:.3f}  largest {100 * d['max']:.2f} ({d['pairs']} pairs)" if d.get("pairs") else ""))
        if "across_seeds" in X:
            L.append("  across seeds (median): " + "  ".join(f"{k} {100 * x:.3f}" for k, x in X["across_seeds"].items())
                     + "; on the same side of each line as the judged value: "
                     + ", ".join(f"{k} {'yes' if b else 'NO'}" for k, b in X["same_side_of_each_line"].items()))
    L.append("")
    for seed, rec in v["runs"].items():
        L.append(f"  runs of seed {seed}: " + "; ".join(
            f"{c} {rec[c].get('status') or rec[c].get('state')}"
            + (f" ({rec[c]['training_seconds'] / 3600:.2f} h)" if rec[c].get("training_seconds") else "")
            for c in ("first", "second")) + f"; sample {rec['sample'].get('status')}")
    for seed, rep in v["reported"].items():
        tb = rep["thin_band"]
        L.append(f"  reported, seed {seed}: thin band " + (f"median {100 * tb['median']:.3f} p90 {100 * tb['p90']:.3f} "
                 f"largest {100 * tb['max']:.2f} ({tb['n']} pairs)" if tb.get("n") else "no member")
                 + "; by level (median) " + " ".join(f"{100 * b['median']:.2f}" for b in rep["by_level"])
                 + "; worst " + ", ".join(f"{i} {100 * x:.1f}" for i, x in rep["worst_members"][:3]))
    n_dev = (v.get("development") or {}).get("members")
    for seed, d in v.get("development_members", {}).items():
        L.append(f"  development's {n_dev} members, seed {seed}: " + "; ".join(
            f"{rd} median {100 * st['median']:.3f} p90 {100 * st['p90']:.3f} largest {100 * st['max']:.2f}"
            for rd, st in d.items() if st.get("n")))
    return "\n".join(L) + "\n"


def main(argv=None):
    here = pathlib.Path(__file__).resolve().parent              # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="f21")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, sha=True):
        p.add_argument("--repo")
        if sha:
            p.add_argument("--config-sha", required=True)

    p = sub.add_parser("write-config"); common(p, sha=False); p.add_argument("--out", required=True)
    p.add_argument("--config-sha")
    p = sub.add_parser("generate"); common(p); p.add_argument("--what", required=True, choices=("train", "thin", "sample"))
    p.add_argument("--data", required=True); p.add_argument("--workers", type=int, default=1)
    for name in ("label", "check-labels"):
        p = sub.add_parser(name); common(p); p.add_argument("--what", required=True, choices=("train", "sample"))
        p.add_argument("--data", required=True); p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("train"); common(p); p.add_argument("--cycle", required=True, choices=("first", "second"))
    p.add_argument("--seed", type=int, required=True); p.add_argument("--data", required=True)
    p.add_argument("--runs", required=True); p.add_argument("--extra-data"); p.add_argument("--max-hours", type=float)
    p.add_argument("--device", default="cuda")
    p = sub.add_parser("predict"); common(p); p.add_argument("--seed", type=int, required=True)
    p.add_argument("--runs", required=True); p.add_argument("--data-gate", required=True)
    p.add_argument("--runs-gate", required=True); p.add_argument("--device", default="cuda")
    p = sub.add_parser("evaluate"); common(p); p.add_argument("--what", required=True, choices=("dev", "sample"))
    p.add_argument("--runs", required=True); p.add_argument("--data", required=True)
    p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("verdict"); common(p); p.add_argument("--runs", required=True); p.add_argument("--data", required=True)
    p.add_argument("--data-gate", required=True); p.add_argument("--runs-gate", required=True)
    p.add_argument("--out", required=True); p.add_argument("--final", action="store_true")
    p = sub.add_parser("smoke"); p.add_argument("--out", required=True); p.add_argument("--repo")
    p.add_argument("--device", default="cuda"); p.add_argument("--workers", type=int, default=2)
    p = sub.add_parser("chain"); p.add_argument("--do", action="append", required=True)
    p = sub.add_parser("together"); p.add_argument("--do", action="append", required=True)
    p.add_argument("--logs", required=True)
    a = ap.parse_args(argv)

    me = [sys.executable, "-I", "-u", str(pathlib.Path(__file__).resolve())]
    if a.cmd == "chain":
        # the commands share this process, so only those that neither train nor predict: a pool of worker processes
        # must not be forked from a process that has used torch, and the linear solver is fixed at the first import
        cmds = [shlex.split(c) for c in a.do]
        other = [c[0] for c in cmds if not c or c[0] not in ("write-config",) + POOL_COMMANDS]
        if other:
            raise SystemExit(f"chain runs write-config, generate, label, check-labels and evaluate only, not {other}")
        for c in cmds:
            print(f"=== chain {time.strftime('%Y-%m-%d %H:%M:%S')}: {' '.join(c)}", flush=True)
            main(c)
        print(f"=== chain ended {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        return
    if a.cmd == "together":
        # several commands of this file at once, each in its own process (trainings that share the GPU); ends when
        # all have ended, with an error if one failed. A training started here stops when this process ends
        # (f2.train.launcher_gone), so that stopping this step stops them all; they resume.
        pathlib.Path(a.logs).mkdir(parents=True, exist_ok=True)
        procs = []
        for k, c in enumerate(a.do):
            fh = open(pathlib.Path(a.logs) / f"together_{k}.log", "ab")
            procs.append((c, subprocess.Popen(me + shlex.split(c), stdout=fh, stderr=subprocess.STDOUT,
                                              env=dict(os.environ, F2_PARENT_PID=str(os.getpid())))))
            print(f"started {k}: {c}", flush=True)
        bad = [c for c, p_ in procs if p_.wait() != 0]
        print(f"all ended; failed: {bad}", flush=True)
        if bad:
            raise SystemExit(1)
        return

    if a.cmd == "smoke":                                   # the host check: no stamp, nothing of the gate
        from f21 import smoke

        rc = smoke.main(["--out", a.out, "--device", a.device, "--workers", str(a.workers)]
                        + (["--repo", a.repo] if a.repo else []))
        if rc:
            raise SystemExit("the host check failed; stop and report")
        return
    repo = pathlib.Path(a.repo) if a.repo else ROOT.parent
    if (repo / "src").is_dir():
        sys.path.insert(1, str(repo / "src"))             # behind the stamped packages, which nothing there can shadow
    if a.cmd in POOL_COMMANDS:                             # one thread for linear algebra in each worker process
        for k in THREAD_VARIABLES:
            os.environ.setdefault(k, "1")
    solver_before = os.environ.get("FEJOINT_SOLVER")
    if a.cmd in ("train", "predict"):
        os.environ["FEJOINT_SOLVER"] = "legacy"            # as f2/__main__.py: these processes solve nothing
    try:
        _run(a)
    finally:
        stamped_config = sys.modules.get("f21.config")
        if stamped_config is not None:
            stamped_config._STAMP_VERIFIED = False         # the sample is configured only while a command runs
        if a.cmd in ("train", "predict"):
            os.environ.pop("FEJOINT_SOLVER", None)
            if solver_before is not None:
                os.environ["FEJOINT_SOLVER"] = solver_before


def _run(a) -> None:
    from f21 import gate
    from f21.config import PINS, config, sha256, verify_repository

    G = config()
    sha = sha256(G)
    why = not_stamped()
    verify_repository(G)
    if a.cmd == "write-config":
        pathlib.Path(a.out).resolve().parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="ascii", newline="\n") as fh:     # the same bytes on every system
            fh.write(json.dumps(G, indent=1, sort_keys=True))
        print("config sha256", sha)
        for k, v_ in PINS.items():
            print("pin", k, v_)
        for f, h in code_hashes().items():
            print(f, h)
        print("stamped code:", "yes" if why is None else f"no ({why})")
        for k, v_ in library_versions().items():
            print("library", k, v_)
        from f2.data import _solver

        solver, want = _solver(), G["reference"]["linear_solver"]
        print("linear solver:", solver)
        if a.config_sha is not None and (a.config_sha != sha or why is not None):
            raise SystemExit("the configuration or the code is not the stamped one; stop and report")
        if a.config_sha is not None and want is not None and solver != want:
            raise SystemExit(f"the linear solver of this host is {solver}, not the configured {want}; stop and report")
        return
    if a.config_sha != sha:
        raise SystemExit(f"configuration hash {sha} differs from the stamped {a.config_sha}; refusing to run")
    if why is not None:
        raise SystemExit(f"{why}; refusing to run")
    import f21.config as stamped_config

    stamped_config._STAMP_VERIFIED = True                  # until this command ends (main clears it again)
    if a.cmd == "generate":
        print(gate.generate(G, a.what, a.data, workers=a.workers))
    elif a.cmd == "label":
        print("labelled", gate.label(G, a.what, a.data, workers=a.workers))
    elif a.cmd == "check-labels":
        r = gate.check_labels(G, a.what, a.data, workers=a.workers)
        print(json.dumps(r))
        if not r["ok"]:
            raise SystemExit("labels fail the checks; stop and report")
    elif a.cmd == "train":
        hist = gate.train(G, a.cycle, a.seed, a.data, a.runs, device=a.device, max_hours=a.max_hours,
                          extra_dir=a.extra_data)
        print(json.dumps({k: hist[k] for k in ("status", "steps") if k in hist}))
        if str(hist.get("status", "")).startswith("non-finite"):
            raise SystemExit(hist["status"])
    elif a.cmd == "predict":
        hist = gate.predict_sample(G, a.seed, a.runs, a.data_gate, a.runs_gate, device=a.device)
        print(json.dumps({k: hist[k] for k in ("status", "predict_seconds") if k in hist}))
        if str(hist.get("status", "")).startswith("non-finite"):
            raise SystemExit("the predictions are not finite; stop and report")
    elif a.cmd == "evaluate":
        v = gate.evaluate(G, a.what, a.runs, a.data, workers=a.workers)
        print(json.dumps(v["status"]))
    elif a.cmd == "verdict":
        v = gate.verdict(G, a.runs, a.data, a.data_gate, a.runs_gate)
        v["code"] = code_hashes()
        v["libraries"] = library_versions()
        out = pathlib.Path(a.out)
        out.mkdir(parents=True, exist_ok=True)
        text = verdict_text(v)
        with open(out / "verdict.json", "w", encoding="ascii", newline="\n") as fh:
            fh.write(json.dumps(v, indent=1))
        with open(out / "verdict.txt", "w", encoding="ascii", newline="\n") as fh:
            fh.write(text)
        print(text, flush=True)
        if a.final and not v["complete"]:
            raise SystemExit("the verdict is incomplete; stop and report")


if __name__ == "__main__":
    main()
