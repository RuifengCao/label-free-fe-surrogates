"""Command line of gate G-C2.2. Run from the folder that holds fejoint, c2 and c22, with the repository at REPO
(python -I -m does not search the current folder, so the script is run by its path):

    python -I c22/__main__.py write-config --out c22_config.json --repo REPO   (prints the configuration hash, the
                                                                  code hashes, and checks the repository files)
    python -I c22/__main__.py generate --data DATA                 (exports, no solve)
    python -I c22/__main__.py label --data DATA --split eval --workers W   (exact solutions; also former, tested)
    python -I c22/__main__.py check-labels --data DATA             (files against manifest and ledger; residuals)
    python -I c22/__main__.py train --data DATA --runs RUNS --seed S --repo REPO --config-sha SHA
    python -I c22/__main__.py evaluate --data DATA --runs RUNS --config-sha SHA --workers W

train and evaluate refuse to run unless --config-sha equals the hash of the configuration in c22/config.py; train
and write-config --repo refuse to run unless the repository files have the SHA-256 the configuration pins.
c22/smoke.py checks a host on a reduced configuration before any of these is run there.
"""
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
CODE = ["c22/__init__.py", "c22/__main__.py", "c22/config.py", "c22/condense.py", "c22/data.py", "c22/train.py",
        "c22/evaluate.py", "c22/smoke.py",
        "c2/__init__.py", "c2/__main__.py", "c2/config.py", "c2/family.py", "c2/instance.py", "c2/data.py",
        "c2/model.py", "c2/train.py", "c2/evaluate.py", "c2/torch_energy.py",
        "fejoint/__init__.py", "fejoint/tstub.py", "fejoint/tstub_pl.py", "fejoint/joint.py", "fejoint/hex8i.py",
        "fejoint/contact.py", "fejoint/linsolve.py", "fejoint/plasticity.py", "fejoint/nlhex.py",
        "fejoint/nlsolve.py"]


def code_hashes() -> dict:
    return {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in CODE}


def main(argv=None):
    here = pathlib.Path(__file__).resolve().parent              # the script's own folder must not shadow modules
    sys.path[:] = [p for p in sys.path if not p or pathlib.Path(p).resolve() != here]
    sys.path.insert(0, str(ROOT))
    from c22.config import config, sha256
    ap = argparse.ArgumentParser(prog="c22")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("write-config"); p.add_argument("--out", required=True); p.add_argument("--repo")
    p = sub.add_parser("generate"); p.add_argument("--data", required=True); p.add_argument("--limit", type=int)
    p = sub.add_parser("label"); p.add_argument("--data", required=True)
    p.add_argument("--split", required=True, help="eval, former or tested")
    p.add_argument("--workers", type=int, default=1)
    p = sub.add_parser("check-labels"); p.add_argument("--data", required=True)
    p = sub.add_parser("train")
    for k in ("--data", "--runs", "--repo", "--config-sha"):
        p.add_argument(k, required=True)
    p.add_argument("--seed", type=int, required=True); p.add_argument("--device", default="cuda")
    p = sub.add_parser("evaluate")
    for k in ("--data", "--runs", "--config-sha"):
        p.add_argument(k, required=True)
    p.add_argument("--workers", type=int, default=1)
    a = ap.parse_args(argv)
    cfg = config()
    sha = sha256(cfg)
    if a.cmd == "write-config":
        with open(a.out, "w", encoding="ascii", newline="\n") as fh:     # the same bytes on every system
            fh.write(json.dumps(cfg, indent=1, sort_keys=True))
        print("config sha256", sha)
        for f, h in code_hashes().items():
            print(f, h)
        if a.repo:
            sys.path.insert(0, str(pathlib.Path(a.repo) / "src"))
            from c2.train import verify_repository
            verify_repository(cfg)
            for f, h in cfg["repository_code"].items():
                print("repository", f, h, "checked")
        return
    if a.cmd in ("train", "evaluate") and a.config_sha != sha:
        raise SystemExit(f"configuration hash {sha} differs from the stamped {a.config_sha}; refusing to run")
    from c22 import data
    if a.cmd == "generate":
        print(data.generate(cfg, a.data, limit=a.limit))
    elif a.cmd == "label":
        if a.split not in data.LABELLED_SPLITS:
            raise SystemExit(f"--split must be one of {data.LABELLED_SPLITS}")
        ids = [r["id"] for r in data.manifest(a.data)["instances"] if r["split"] == a.split]
        data.label(cfg, a.data, ids, workers=a.workers)
        print("labelled", len(ids))
    elif a.cmd == "check-labels":
        r = data.check_labels(cfg, a.data)
        print(json.dumps(r))
        if not r["ok"]:
            raise SystemExit("labels fail the checks; stop and report")
    elif a.cmd == "train":
        sys.path.insert(0, str(pathlib.Path(a.repo) / "src"))
        from c22.train import train
        hist = train(cfg, a.seed, a.data, a.runs, device=a.device)
        print(json.dumps({k: hist[k] for k in ("status", "steps") if k in hist}))
    elif a.cmd == "evaluate":
        from c22.evaluate import evaluate
        v = evaluate(cfg, a.data, a.runs, workers=a.workers)
        print(json.dumps({k: v[k] for k in ("verdict", "C1_value", "C2_value", "missing", "non_finite") if k in v}))


if __name__ == "__main__":
    main()
