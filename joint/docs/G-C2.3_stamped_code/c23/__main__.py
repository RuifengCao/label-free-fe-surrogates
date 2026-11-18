"""Command line of gate G-C2.3. Run from the folder that holds fejoint, c2, c22 and c23, with the repository at REPO
(python -I -m does not search the current folder, so the script is run by its path):

    python -I c23/__main__.py write-config --out c23_config.json --repo REPO [--config-sha SHA]   (prints the
                                                                  configuration hash and the code hashes, and
                                                                  checks the repository files)
    python -I c23/__main__.py generate --data DATA --config-sha SHA   (exports, no solve; draws the held-out sample)
    python -I c23/__main__.py label --data DATA --split third --workers W   (exact solutions; also eval, tested
                                                                  and train)
    python -I c23/__main__.py check-labels --data DATA [--splits third eval tested]
    python -I c23/__main__.py predict-label-free --data DATA --runs RUNS --seed S --state FILE --repo REPO
                                                                  --config-sha SHA
    python -I c23/__main__.py train --data DATA --runs RUNS --seed S --repo REPO --config-sha SHA   (supervised arm)
    python -I c23/__main__.py evaluate --data DATA --runs RUNS --config-sha SHA --arm label_free --workers W
                                                                  (the metrics of one arm's runs; the long step)
    python -I c23/__main__.py verdict --data DATA --runs RUNS --config-sha SHA [--final]   (from the arms evaluated
                                                                  so far; the first one fixes part 1 in
                                                                  verdict_part1.json)

Refusals. generate, predict-label-free, train, evaluate and verdict refuse to run unless --config-sha equals the
hash of the configuration in c23/config.py, so that the sample is not drawn under another configuration than the
stamped one. Every command but write-config refuses to run unless the code is the stamped code:
docs/G-C2.3_code.sha256, which is written at the stamp, must lie beside the package and hold the SHA-256 of every
file of CODE as it is now. Before the stamp there is no such file, so that nothing of the gate can be drawn by these
commands. predict-label-free, train and write-config --repo refuse to run unless the repository files have the
SHA-256 the configuration pins. c23/smoke.py checks a host on a reduced configuration before any of these is run
there; it draws nothing of the gate and needs no stamp. This file and c23/smoke.py tell Python to write no bytecode,
so that the tree they run from holds the sources only.

Exit codes, for a queue that stops on a code other than 0. write-config with --config-sha: 0 only if the hash is
the given one, the state files are pinned and the code is the stamped code. predict-label-free: 0 only if the
predictions are finite. evaluate: 0 only if every run of the label-free arm has predictions, or no run of the
supervised arm is missing. verdict: 0 only if the identity check is OK and part 1 is the one first written; with
--final also only if both arms are evaluated and no run is missing. The verdict's files are written and its line is
printed in every case.
"""
import argparse
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True            # also in a spawned worker process, which runs this file's top level first
ROOT = pathlib.Path(__file__).resolve().parents[1]
STAMP_FILE = ROOT / "docs" / "G-C2.3_code.sha256"
CODE = ["c23/__init__.py", "c23/__main__.py", "c23/config.py", "c23/data.py", "c23/train.py", "c23/evaluate.py",
        "c23/smoke.py",
        "c22/__init__.py", "c22/__main__.py", "c22/config.py", "c22/condense.py", "c22/data.py", "c22/train.py",
        "c22/evaluate.py", "c22/smoke.py",
        "c2/__init__.py", "c2/__main__.py", "c2/config.py", "c2/family.py", "c2/instance.py", "c2/data.py",
        "c2/model.py", "c2/train.py", "c2/evaluate.py", "c2/torch_energy.py",
        "fejoint/__init__.py", "fejoint/tstub.py", "fejoint/tstub_pl.py", "fejoint/joint.py", "fejoint/hex8i.py",
        "fejoint/contact.py", "fejoint/linsolve.py", "fejoint/plasticity.py", "fejoint/nlhex.py",
        "fejoint/nlsolve.py"]


def code_hashes() -> dict:
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE}


def states_filled(cfg: dict) -> bool:
    return all(len(h) == 64 and all(c in "0123456789abcdef" for c in h)
               for h in cfg["arms"]["label_free"]["state_sha256"].values())


def not_stamped() -> str | None:
    """None if the code beside this file is the stamped code; otherwise the reason."""
    if not STAMP_FILE.exists():
        return f"{STAMP_FILE.name} is not beside the code: the gate is not stamped"
    want = {}
    for line in STAMP_FILE.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2:
            want[parts[1]] = parts[0]
        elif parts:
            return f"{STAMP_FILE.name} has a line that is not a hash and a file name"
    now = code_hashes()
    differ = [f for f in CODE if want.get(f) != now[f]]
    return f"these files are not those of {STAMP_FILE.name}: {differ}" if differ else None


def main(argv=None):
    here = pathlib.Path(__file__).resolve().parent              # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    from c23.config import config, sha256
    ap = argparse.ArgumentParser(prog="c23")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("write-config"); p.add_argument("--out", required=True); p.add_argument("--repo")
    p.add_argument("--config-sha")
    p = sub.add_parser("generate"); p.add_argument("--data", required=True)
    p.add_argument("--config-sha", required=True)
    p = sub.add_parser("label"); p.add_argument("--data", required=True)
    p.add_argument("--split", required=True, help="third, eval, tested or train")
    p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("check-labels"); p.add_argument("--data", required=True)
    p.add_argument("--splits", nargs="+")
    p = sub.add_parser("predict-label-free")
    for k in ("--data", "--runs", "--repo", "--config-sha", "--state"):
        p.add_argument(k, required=True)
    p.add_argument("--seed", type=int, required=True); p.add_argument("--device", default="cuda")
    p = sub.add_parser("train")
    for k in ("--data", "--runs", "--repo", "--config-sha"):
        p.add_argument(k, required=True)
    p.add_argument("--seed", type=int, required=True); p.add_argument("--device", default="cuda")
    p = sub.add_parser("evaluate")
    for k in ("--data", "--runs", "--config-sha"):
        p.add_argument(k, required=True)
    p.add_argument("--arm", required=True, choices=("label_free", "supervised_512"))
    p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("verdict")
    for k in ("--data", "--runs", "--config-sha"):
        p.add_argument(k, required=True)
    p.add_argument("--final", action="store_true")
    a = ap.parse_args(argv)
    cfg = config()
    sha = sha256(cfg)
    if a.cmd == "write-config":
        with open(a.out, "w", encoding="ascii", newline="\n") as fh:     # the same bytes on every system
            fh.write(json.dumps(cfg, indent=1, sort_keys=True))
        print("config sha256", sha)
        print("state files pinned:", states_filled(cfg))
        print("code as stamped:", not_stamped() is None)
        for f, h in code_hashes().items():
            print(f, h)
        if a.repo:
            sys.path.insert(0, str(pathlib.Path(a.repo) / "src"))
            from c2.train import verify_repository
            verify_repository(cfg)
            for f, h in cfg["repository_code"].items():
                print("repository", f, h, "checked")
        if a.config_sha and not (a.config_sha == sha and states_filled(cfg) and not_stamped() is None):
            raise SystemExit("the configuration or the code is not the stamped one; stop and report")
        return
    if not states_filled(cfg):
        raise SystemExit("the SHA-256 of the label-free state files is not filled in; the gate is not stamped")
    if a.cmd in ("generate", "predict-label-free", "train", "evaluate", "verdict") and a.config_sha != sha:
        raise SystemExit(f"configuration hash {sha} differs from the stamped {a.config_sha}; refusing to run")
    why = not_stamped()
    if why:
        raise SystemExit(f"{why}; refusing to run")
    from c23 import data
    if a.cmd == "generate":
        print(data.generate(cfg, a.data))
    elif a.cmd == "label":
        if a.split not in data.LABELLED_SPLITS:
            raise SystemExit(f"--split must be one of {data.LABELLED_SPLITS}")
        ids = data.labelled_ids(cfg, a.data, (a.split,))
        data.label(cfg, a.data, ids, workers=a.workers)
        print("labelled", len(ids))
    elif a.cmd == "check-labels":
        r = data.check_labels(cfg, a.data, tuple(a.splits) if a.splits else data.LABELLED_SPLITS)
        print(json.dumps(r))
        if not r["ok"]:
            raise SystemExit("labels fail the checks; stop and report")
    elif a.cmd == "predict-label-free":
        sys.path.insert(0, str(pathlib.Path(a.repo) / "src"))
        from c23.train import predict_label_free
        hist = predict_label_free(cfg, a.seed, a.state, a.data, a.runs, device=a.device)
        print(json.dumps({k: hist[k] for k in ("status", "predict_seconds") if k in hist}))
        if hist.get("status") != "finished":
            raise SystemExit("the predictions are not finite; stop and report")
    elif a.cmd == "train":
        sys.path.insert(0, str(pathlib.Path(a.repo) / "src"))
        from c23.train import train
        hist = train(cfg, a.seed, a.data, a.runs, device=a.device)
        print(json.dumps({k: hist[k] for k in ("status", "steps") if k in hist}))
    elif a.cmd == "evaluate":
        from c23.evaluate import evaluate_arm
        r = evaluate_arm(cfg, a.data, a.runs, a.arm, workers=a.workers)
        st = {name: x["status"] for name, x in r["inputs"]["runs"].items()}
        print(json.dumps(st))
        if any(x == "missing" or (x != "finished" and a.arm == "label_free") for x in st.values()):
            raise SystemExit("a run of the arm has no predictions; stop and report")
    elif a.cmd == "verdict":
        from c23.evaluate import verdict
        v = verdict(cfg, a.data, a.runs)
        print(json.dumps({"verdict": v["verdict"], "not_evaluated": v["not_evaluated"], "missing": v["missing"],
                          "non_finite": v["non_finite"], "part1_same_as_first": v.get("part1_same_as_first")}))
        ok = v["verdict"]["identity"] == "OK" and v.get("part1_same_as_first") is True
        if a.final:
            ok = ok and not v["not_evaluated"] and not v["missing"]
        if not ok:
            raise SystemExit("the verdict is written; it does not allow the next step: stop and report")


if __name__ == "__main__":
    main()
