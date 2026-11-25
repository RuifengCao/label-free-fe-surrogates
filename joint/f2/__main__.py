"""Command line of the development runs of the CHS surrogate (exploratory, not a gate). Run by its path from any
folder; the repository package is looked for in ../src next to the folder that holds fejoint, c2, c22 and f2, or at
--repo (python -I -m does not search the current folder, so the script is run by its path):

    python -I f2/__main__.py presets
    python -I f2/__main__.py write-config --preset P --out FILE
    python -I f2/__main__.py generate --preset P --data DATA [--splits train,eval,dev,tested] [--limit N]
                                      [--only ID,ID] [--workers W]     (exports, each with its preload solve)
    python -I f2/__main__.py generate --preset P --data DATA_X --extra [--workers W]
                                      (the preset's extra training members, in a data directory of their own)
    python -I f2/__main__.py label --preset P --data DATA [--splits eval,dev,tested] [--only ID,ID] [--workers W]
    python -I f2/__main__.py check-labels --preset P --data DATA
    python -I f2/__main__.py train --preset P --data DATA --runs RUNS --seed S [--device cuda] [--max-hours H]
                                   [--init-from STATE.pt]   (a new run starts from another run's weights)
                                   [--companion DATA_DIR]   (the same family on the preset's companion mesh)
                                   [--under-data DATA_DIR --under-state STATE]   (a field underneath)
                                   [--extra-data DATA_DIR]  (the preset's extra training members)
                                   [--other-seed]           (a seed the preset does not list; same configuration)
        (a preset with averages of the weights also writes RUNS_ema<digits of the decay>/, one for each decay)
    python -I f2/__main__.py evaluate --preset P --data DATA --runs RUNS [--workers W] [--exact] [--only ID,ID]
                                      [--seeds S,S]   (other seeds of the same configuration; their own file)
        (RUNS may be an average's directory, RUNS_ema<digits>, with the preset of the run it belongs to)
    python -I f2/__main__.py quicklook --data DATA --runs RUNS --seed S
    python -I f2/__main__.py chain --do "generate --preset P --data DATA" --do "label ..."   (one after another)
    python -I f2/__main__.py together --do "train ..." --do "train ..." --logs DIR             (at the same time)
    python -I f2/__main__.py probe --script probes/f2_cost/step_cost.py -- --out FILE ...       (a script of probes/,
                                      run by its path with the arguments after "--"; for a queue that runs this file)

All presets share one data directory (f2/devconfig.py). --mesh NAME replaces the family's mesh (for example tiny,
for dry runs of the code); data made with another mesh need their own directory.

train --side "COMMAND" [--side "COMMAND" ...] --side-log FILE starts, next to the training, one more process that
runs the given commands of this file one after another (processor work such as exports and labels, while the
training uses the GPU). That process is not stopped with the training and ends by itself; its commands resume.
Write paths in the commands with forward slashes.
"""
import argparse
import json
import os
import pathlib
import shlex
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]


def main(argv=None):
    here = pathlib.Path(__file__).resolve().parent              # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    ap = argparse.ArgumentParser(prog="f2")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("presets")

    def common(p, data=True, runs=False, preset=True):
        if preset:
            p.add_argument("--preset", required=True)
        p.add_argument("--mesh")
        p.add_argument("--repo")
        if data:
            p.add_argument("--data", required=True)
        if runs:
            p.add_argument("--runs", required=True)

    p = sub.add_parser("write-config"); common(p, data=False); p.add_argument("--out", required=True)
    p = sub.add_parser("generate"); common(p)
    p.add_argument("--splits", default="train,eval,dev,tested"); p.add_argument("--limit", type=int)
    p.add_argument("--only"); p.add_argument("--workers", type=int, default=1)
    p.add_argument("--extra", action="store_true")
    p = sub.add_parser("label"); common(p)
    p.add_argument("--splits", default="eval,dev,tested"); p.add_argument("--only")
    p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("check-labels"); common(p)
    p = sub.add_parser("train"); common(p, runs=True)
    p.add_argument("--seed", type=int, required=True); p.add_argument("--device", default="cuda")
    p.add_argument("--max-hours", type=float); p.add_argument("--stop-after-epoch", type=int)
    p.add_argument("--checkpoint-minutes", type=float, default=10.0)
    p.add_argument("--init-from"); p.add_argument("--companion"); p.add_argument("--other-seed", action="store_true")
    p.add_argument("--extra-data")
    p.add_argument("--under-data"); p.add_argument("--under-state")
    p.add_argument("--side", action="append", default=[]); p.add_argument("--side-log")
    p = sub.add_parser("chain"); p.add_argument("--do", action="append", required=True)
    p = sub.add_parser("together"); p.add_argument("--do", action="append", required=True)
    p.add_argument("--logs", required=True)
    p = sub.add_parser("evaluate"); common(p, runs=True)
    p.add_argument("--workers", type=int, default=1); p.add_argument("--exact", action="store_true")
    p.add_argument("--only"); p.add_argument("--seeds")
    p = sub.add_parser("quicklook"); common(p, runs=True, preset=False); p.add_argument("--seed", type=int, required=True)
    p = sub.add_parser("probe"); p.add_argument("--script", required=True)
    p.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)

    solver_before = os.environ.get("FEJOINT_SOLVER")
    if a.cmd == "train":
        # The training process solves nothing. Keeping the sparse direct solver's libraries (MKL with its own
        # OpenMP runtime) out of it avoids two OpenMP runtimes in the process that also holds torch.
        os.environ["FEJOINT_SOLVER"] = "legacy"
    if a.cmd == "probe":
        # one of the repository's probe scripts, in a process of its own; nothing else can be started this way
        script = (ROOT / a.script).resolve()
        if ROOT / "probes" not in script.parents or script.suffix != ".py" or not script.is_file():
            raise SystemExit("--script must be a Python file below probes/")
        rest = a.rest[1:] if a.rest[:1] == ["--"] else a.rest
        raise SystemExit(subprocess.call([sys.executable, "-I", "-u", str(script), *rest]))
    if a.cmd == "chain":
        for c in a.do:
            print(f"=== chain {time.strftime('%Y-%m-%d %H:%M:%S')}: {c}", flush=True)
            main(shlex.split(c))
        print(f"=== chain ended {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        return
    if a.cmd == "together":
        # several commands of this file at once, each in its own process (for instance trainings that share the
        # GPU); ends when all have ended, with an error if one failed. A training started here stops when this
        # process ends (f2.train.launcher_gone), so that stopping this job stops them all; they resume.
        pathlib.Path(a.logs).mkdir(parents=True, exist_ok=True)
        procs = []
        for k, c in enumerate(a.do):
            fh = open(pathlib.Path(a.logs) / f"together_{k}.log", "ab")
            procs.append((c, subprocess.Popen([sys.executable, "-I", "-u", str(pathlib.Path(__file__).resolve()),
                                               *shlex.split(c)], stdout=fh, stderr=subprocess.STDOUT,
                                              env=dict(os.environ, F2_PARENT_PID=str(os.getpid())))))
            print(f"started {k}: {c}", flush=True)
        bad = [c for c, p_ in procs if p_.wait() != 0]
        print(f"all ended; failed: {bad}", flush=True)
        if bad:
            raise SystemExit(1)
        return
    from f2 import devconfig
    if a.cmd == "presets":
        for name, p in devconfig.PRESETS.items():
            print(name, json.dumps(p))
        return
    repo = pathlib.Path(a.repo) if a.repo else ROOT.parent
    if (repo / "src").is_dir():
        sys.path.insert(0, str(repo / "src"))
    from f2 import data
    only = [s for s in a.only.split(",") if s] if getattr(a, "only", None) else None
    if a.cmd == "quicklook":
        from f2.evaluate import quicklook
        run = pathlib.Path(a.runs) / f"label_free_s{a.seed}"
        q = quicklook(json.loads((pathlib.Path(a.data) / "labels" / "summary.json").read_text()),
                      json.loads((run / "snapshots.json").read_text()))
        (run / "quicklook.json").write_text(json.dumps(q, indent=1))
        for epoch, r in q.items():
            print(epoch, json.dumps(r["summary"]))
        return
    cfg = devconfig.config(a.preset)
    if a.mesh:
        cfg["data"]["mesh"] = a.mesh
    sha = devconfig.sha256(cfg)
    if a.cmd == "write-config":
        with open(a.out, "w", encoding="ascii", newline="\n") as fh:
            fh.write(json.dumps(cfg, indent=1, sort_keys=True))
        print("config sha256", sha, "data sha256", data.data_sha256(cfg))
    elif a.cmd == "generate":
        splits = tuple(s for s in a.splits.split(",") if s)
        if a.extra:                                            # the preset's extra training members, in --data
            cfg = data.extra_config(cfg)
            if cfg is None:
                raise SystemExit("the preset has no extra members")
            splits = ("train",)
            print("extra members; data sha256", data.data_sha256(cfg))
        print(data.generate(cfg, a.data, splits=splits, limit=a.limit, workers=a.workers, only=only))
        if a.extra:                                            # training members only: nothing else checks them
            log = json.loads((pathlib.Path(a.data) / "generate_log.json").read_text())
            bad = [e["id"] for e in log if not (e["preload"]["converged"] and e["preload"]["on_target"])]
            if bad:
                raise SystemExit(f"the preload of {len(bad)} extra members is not on target (first {bad[0]}); stop")
    elif a.cmd == "label":
        splits = tuple(s for s in a.splits.split(",") if s)
        bad = [s for s in splits if s not in data.LABELLED_SPLITS]
        if bad:
            raise SystemExit(f"--splits must be among {data.LABELLED_SPLITS}")
        ids = [r["id"] for r in data.manifest(a.data)["instances"] if r["split"] in splits
               and (only is None or r["id"] in only)]
        data.label(cfg, a.data, ids, workers=a.workers)
        from f2.evaluate import label_summary
        label_summary(a.data)
        print("labelled", len(ids))
    elif a.cmd == "check-labels":
        r = data.check_labels(cfg, a.data)
        print(json.dumps(r))
        if not r["ok"]:
            raise SystemExit("labels fail the checks; stop and report")
    elif a.cmd == "train":
        if a.side:
            if not a.side_log:
                raise SystemExit("--side needs --side-log")
            cmd = [sys.executable, "-I", "-u", str(pathlib.Path(__file__).resolve()), "chain"]
            for c in a.side:
                cmd += ["--do", c]
            env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
            env.pop("FEJOINT_SOLVER", None)                    # the side process chooses its solver itself
            if solver_before is not None:
                env["FEJOINT_SOLVER"] = solver_before
            pathlib.Path(a.side_log).parent.mkdir(parents=True, exist_ok=True)
            with open(a.side_log, "ab") as fh:                 # the process keeps its own handle of the log
                side = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, env=env)
            print(f"side process {side.pid}: {len(a.side)} commands, log {a.side_log}", flush=True)
        from f2.train import train
        hist = train(cfg, a.seed, a.data, a.runs, device=a.device, max_hours=a.max_hours,
                     stop_after_epoch=a.stop_after_epoch, checkpoint_minutes=a.checkpoint_minutes,
                     init_from=a.init_from, companion_dir=a.companion, other_seed=a.other_seed,
                     extra_dir=a.extra_data, under_dir=a.under_data, under_state=a.under_state)
        print(json.dumps({k: hist[k] for k in ("status", "steps") if k in hist}))
        if str(hist.get("status", "")).startswith("non-finite"):
            raise SystemExit(hist["status"])
    elif a.cmd == "evaluate":
        from f2.evaluate import evaluate
        seeds = [int(x) for x in a.seeds.split(",") if x] if a.seeds else None
        v = evaluate(cfg, a.data, a.runs, workers=a.workers, exact=a.exact, only=only, seeds=seeds)
        for key, s in v["summary"].items():
            for name, r in s.items():
                print(key, name, json.dumps({k: {q: round(r[k][q], 5) for q in ("median", "p90", "max")}
                                             for k in ("abs_curve_err", "abs_curveD_err", "abs_M_err") if r[k].get("n")}))


if __name__ == "__main__":
    main()
