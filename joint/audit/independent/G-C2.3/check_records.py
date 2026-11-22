# Independent audit of gate G-C2.3: the returned records against the pre-specification and the runbook.
#
# What it checks, with the auditor's own code (the stamped library is imported only for the configuration, the
# family's draws and the export of an instance):
#   1. the returned configuration: its canonical SHA-256, and its equality with the configuration that the stamped
#      c23/config.py builds;
#   2. the code hashes: the stamped hash list against the stamped files, and against the lines that the
#      configuration command printed on the host;
#   3. the samples: the parameters of all 644 members of the manifest against the configured draws, no member
#      shared between two sets, the instance files against the manifest's SHA-256, and a few instances exported
#      again and compared array by array;
#   4. the ledger: one entry a member, the levels of its split, convergence, the configured limits, the label files
#      of the package against the ledger's SHA-256, the times of the entries against the times of the label jobs;
#   5. the supervised runs: status, steps, epochs, the recorded settings against those of the label-free runs of
#      the base gate, the hash of the training labels, the logs against the histories;
#   6. the queue: every job's command against the runbook's command lines, exit codes, the order and the gaps;
#   7. the order of events: part 1 kept before any training label; nothing read by a training job but data, labels
#      and the stamped tree (from the job files);
#   8. the prediction files and the inputs that the verdict records (the manifest's hash is that of the host's file,
#      with CR LF line ends: the file is accepted with these or with LF line ends);
#   9. every log line that is not one of the expected kinds.
# It prints its findings; nothing is written but the JSON summary given as the last argument.
#
# Usage: python -I check_records.py <stamped joint folder> <unpacked return package (gate3_records)>
#            <instances folder> <records of the base gate (records/c22/return)> <summary.json>
import glob
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True      # the stamped tree is read, never written: no bytecode folders in it
from datetime import datetime, timedelta


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    repo, R, inst, base_ret, outp = sys.argv[1:6]
    sys.path.insert(0, os.path.abspath(repo))
    import numpy as np
    out = {}
    J = lambda p: json.load(open(os.path.join(R, p), encoding="utf-8"))  # noqa: E731
    cfg = J("c23_config.json")
    prespec = open(os.path.join(repo, "docs", "PRESPEC_G-C2.3.md"), encoding="utf-8").read()
    stamped_sha = re.search(r"canonical SHA-256 is `([0-9a-f]{64})`", prespec).group(1)

    # 1. configuration
    canon = hashlib.sha256(json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    from c23.config import config as stamped_config
    out["config"] = {"canonical_sha256": canon, "equals_prespec": canon == stamped_sha,
                     "equals_stamped_code": stamped_config() == cfg}
    print("1. configuration:", out["config"])

    # 2. code hashes
    lines = [l.split() for l in open(os.path.join(repo, "docs", "G-C2.3_code.sha256"), encoding="utf-8").read().splitlines() if l.strip()]
    bad = [n for h, n in lines if not os.path.exists(os.path.join(repo, n)) or sha_file(os.path.join(repo, n)) != h]
    in_repo_cfg = cfg.get("repository_code", {})
    log86 = open(os.path.join(R, "queue", "86_c23_config.log"), encoding="utf-8", errors="replace").read()
    printed = dict((n.replace("\\", "/"), h) for n, h in re.findall(r"^(\S+) ([0-9a-f]{64})\s*$", log86, re.M))
    listed = {n: h for h, n in lines}
    same = sum(1 for n, h in printed.items() if listed.get(n) == h)
    out["code"] = {"listed": len(lines), "not_matching_stamped_files": bad, "hash_lines_printed_on_host": len(printed),
                   "of_them_equal_to_list": same, "repository_checked_lines": len(re.findall(r"^repository .* checked", log86, re.M)),
                   "repository_code_entries_in_config": len(in_repo_cfg)}
    print("2. code:", out["code"])
    print("   head of the configuration job's log:", [l for l in log86.splitlines()[1:4]])

    # 3. samples
    man = J("manifest.json")
    from c2.family import sample, Params
    from dataclasses import asdict
    d = cfg["data"]
    draws = {"train": sample(d["n_train"], seed=d["train_seed"])[0], "third": sample(d["n_third"], seed=d["third_eval_seed"])[0],
             "eval": sample(d["n_eval"], seed=d["eval_seed"])[0]}
    want = {}
    for split, qs in draws.items():
        for i, q in enumerate(qs):
            want[f"{split}_{i:04d}"] = (split, asdict(q))
    for name, p in d["tested"].items():
        want[f"tested_{name}"] = ("tested", asdict(Params(**p)))
    recs = {r["id"]: r for r in man["instances"]}
    wrong = [i for i in want if i not in recs or recs[i]["split"] != want[i][0] or recs[i]["params"] != want[i][1]]
    keys = {}
    for i, r in recs.items():
        keys.setdefault(json.dumps(r["params"], sort_keys=True), []).append(i)
    shared = [v for v in keys.values() if len(v) > 1]
    sha_bad = [i for i, r in recs.items() if not os.path.exists(os.path.join(inst, i + ".npz"))
               or sha_file(os.path.join(inst, i + ".npz")) != r["sha256"]]
    out["samples"] = {"members": len(recs), "n": man["n"], "manifest_config": man["config_sha256"] == stamped_sha,
                      "not_the_configured_draw": wrong, "extra_members": sorted(set(recs) - set(want)),
                      "identical_parameters": shared, "instance_files_not_matching_manifest": len(sha_bad),
                      "seeds": {k: d[k] for k in ("train_seed", "third_eval_seed", "eval_seed", "former_eval_seed")},
                      "third_seed_in_seen_list": d["third_eval_seed"] in d["seeds_seen_before_stamp"]}
    print("3. samples:", out["samples"])
    # a few instances exported again by the auditor and compared array by array
    from c2.data import export_member
    again = {}
    for iid in ("third_0034", "third_0001", "eval_0063", "train_0076", "tested_BJ_T1_preloaded"):
        q = Params(**recs[iid]["params"])
        ex = export_member(cfg, q)
        with np.load(os.path.join(inst, iid + ".npz"), allow_pickle=False) as z:
            diff = [k for k in ex if not (np.asarray(ex[k]).shape == z[k].shape and np.array_equal(np.asarray(ex[k]), z[k]))]
            extra = sorted(set(z.files) - set(ex) - {"params_json", "config_sha256"})
            pj = json.loads(bytes(z["params_json"].tobytes()).decode()) == recs[iid]["params"]
            cs = bytes(z["config_sha256"]).decode() == stamped_sha
        again[iid] = {"arrays": len(ex), "arrays_differing": diff, "other_keys": extra, "params_stored": pj, "config_stored": cs}
    out["exported_again"] = again
    print("   exported again:", again)

    # 4. ledger
    led = J("ledger.json")
    ids = [e["id"] for e in led]
    lim = d["kkt_limits"]
    lv_of = lambda s: sorted(d["train_label_levels_mm"] if s == "train" else d["eval_levels_mm"])  # noqa: E731
    prob = []
    for e in led:
        s = recs[e["id"]]["split"]
        if e["levels"] != lv_of(s):
            prob.append((e["id"], "levels"))
        if not all(e["converged"]):
            prob.append((e["id"], "not converged"))
        if max(e["iterations"]) > d["label_solver"]["max_it"]:
            prob.append((e["id"], "iterations"))
        for k, (op, v) in lim.items():
            if not (e["kkt_worst"][k] >= v if op == ">=" else e["kkt_worst"][k] <= v):
                prob.append((e["id"], k))
        if e["F_vs_F_sigma"] > 1e-6:
            prob.append((e["id"], "F_vs_F_sigma"))
        if e["inst_sha256"] != recs[e["id"]]["sha256"]:
            prob.append((e["id"], "instance sha"))
        if e["solver"] != "scipy":
            prob.append((e["id"], "solver " + e["solver"]))
    lab_bad, lab_n = [], 0
    for p in sorted(glob.glob(os.path.join(R, "labels", "*.npz"))):
        iid = os.path.basename(p)[:-4]
        lab_n += 1
        e = next(x for x in led if x["id"] == iid)
        if sha_file(p) != e["label_sha256"]:
            lab_bad.append(iid)
    t_of = lambda e: datetime.strptime(e["time"][:19], "%Y-%m-%d %H:%M:%S")  # noqa: E731
    tr = [e for e in led if recs[e["id"]]["split"] == "train"]
    ho = [e for e in led if recs[e["id"]]["split"] != "train"]
    out["ledger"] = {"entries": len(led), "distinct": len(set(ids)), "members_without_entry": sorted(set(recs) - set(ids)),
                     "levels_total": sum(len(e["levels"]) for e in led), "problems": prob,
                     "label_files_in_package": lab_n, "label_files_not_matching": lab_bad,
                     "held_out_times": [str(min(map(t_of, ho))), str(max(map(t_of, ho)))],
                     "training_times": [str(min(map(t_of, tr))), str(max(map(t_of, tr)))],
                     "training_seconds_summed": round(sum(e["seconds"] for e in tr), 2),
                     "training_levels": sum(len(e["levels"]) for e in tr),
                     "worst": {k: (min if op == ">=" else max)(e["kkt_worst"][k] for e in led) for k, (op, _) in lim.items()},
                     "limits": lim, "max_iterations": max(max(e["iterations"]) for e in led),
                     "max_F_vs_F_sigma": max(e["F_vs_F_sigma"] for e in led),
                     "time_zone_strings": sorted(set(e["time"][20:] for e in led))[:3]}
    print("4. ledger:", {k: v for k, v in out["ledger"].items() if k != "time_zone_strings"})
    tr_sorted = sorted(tr, key=lambda e: e["id"])
    tr_sha = hashlib.sha256(json.dumps(tr_sorted, sort_keys=True).encode("ascii")).hexdigest()
    ho_sorted = sorted(ho, key=lambda e: e["id"])
    ho_sha = hashlib.sha256(json.dumps(ho_sorted, sort_keys=True).encode("ascii")).hexdigest()

    # 5. supervised runs, and the label-free runs' records
    V, V1 = J("verdict.json"), J("verdict_part1.json")
    runs = {}
    for seed in (5, 6, 7):
        h = J(f"run_files/supervised_512_s{seed}/history.json")
        hb = json.load(open(os.path.join(base_ret, f"run_files/label_free_s{seed}/history.json"), encoding="utf-8"))
        log = open(os.path.join(R, "queue", f"{95 + seed - 5}_c23_train_s{seed}.log"), encoding="utf-8", errors="replace").read()
        ep = re.findall(r"^epoch (\d+) loss (\S+) (\S+) s; cap events (\d+), bursts (\d+)", log, re.M)
        log_ok = len(ep) == 200 and all(int(a) == i + 1 for i, (a, *_r) in enumerate(ep)) and \
            all(float(f"{h['loss'][i]:.6g}") == float(ep[i][1]) and round(h["epoch_seconds"][i], 2) == float(ep[i][2]) for i in range(200))
        att = open(os.path.join(R, f"run_files/supervised_512_s{seed}/attempts.log"), encoding="utf-8").read().splitlines()
        runs[seed] = {"status": h["status"], "steps": h["steps"], "total_steps": h["total_steps"], "epochs": len(h["loss"]),
                      "seed": h["seed"], "arm": h["arm"], "config": h["config_sha256"] == stamped_sha,
                      "settings_equal_base_run": all(h[k] == hb[k] for k in ("betas", "cap", "total_steps", "matmul_precision", "torch", "gpu", "device")),
                      "resumes": h["resumes"], "resumed_from_epoch": h["resumed_from_epoch"],
                      "reference_solutions": h["reference_solutions"],
                      "training_labels_sha256_is_ledger": h["training_labels_sha256"] == tr_sha,
                      "labels_hash": h["training_labels_sha256"][:12],
                      "cap_events": len(h["cap_events"]), "bursts": len(h["bursts"]),
                      "base_cap_events": len(hb["cap_events"]), "base_hours": round(sum(hb["epoch_seconds"]) / 3600, 2),
                      "base_peak_GiB": round(hb["peak_memory_GiB"], 2), "base_resumes": hb["resumes"],
                      "hours": round(sum(h["epoch_seconds"]) / 3600, 3), "peak_GiB": round(h["peak_memory_GiB"], 3),
                      "loss_first": h["loss"][0], "loss_last10": sum(h["loss"][-10:]) / 10, "loss_max": max(h["loss"]),
                      "loss_finite": all(np.isfinite(h["loss"])),
                      "step_seconds_min_med_max": [round(min(h["epoch_seconds"]) / 512, 3), round(float(np.median(h["epoch_seconds"])) / 512, 3), round(max(h["epoch_seconds"]) / 512, 3)],
                      "log_equals_history": log_ok, "attempts": att,
                      "cap_last_in_log": int(ep[-1][3]) if ep else None, "bursts_last_in_log": int(ep[-1][4]) if ep else None}
        hl = J(f"run_files/label_free_s{seed}/history.json")
        runs[f"lf{seed}"] = {"state_sha_pinned": hl["trained_in"]["state_sha256"] == cfg["arms"]["label_free"]["state_sha256"][str(seed)],
                             "base_config": hl["trained_in"]["config_sha256"] == cfg["base"]["config_sha256"],
                             "epoch": hl["trained_in"]["epoch"], "step": hl["trained_in"]["step"],
                             "predict_seconds": hl["predict_seconds"], "status": hl["status"],
                             "attempts": open(os.path.join(R, f"run_files/label_free_s{seed}/attempts.log"), encoding="utf-8").read().splitlines()}
    out["runs"] = runs
    print("5. runs:")
    for k, v in runs.items():
        print("   ", k, v)

    # 6. queue
    runbook = open(os.path.join(repo, "RUNBOOK_C23.md"), encoding="utf-8").read()
    cmds = [l[3:].strip() for l in runbook.splitlines() if l.startswith("PY ")]
    jobs = []
    for p in sorted(glob.glob(os.path.join(R, "queue", "*.job.json"))):
        name = os.path.basename(p)[:-9]
        j = json.load(open(p, encoding="utf-8"))
        dn = json.load(open(p[:-9] + ".done.json", encoding="utf-8"))
        jobs.append({"name": name, "cmd": " ".join([j["script"]] + [str(a) for a in j["args"]]), "rc": dn["returncode"],
                     "killed": dn["killed"], "started": dn["started"], "ended": dn["ended"], "seconds": dn["seconds"],
                     "has_log": os.path.exists(p[:-9] + ".log"), "keys": sorted(j), "done_keys": sorted(dn)})
    gate = [j for j in jobs if "_c23_" in j["name"] and "pre" not in j["name"].split("_")[1]]
    pre = [j for j in jobs if j not in gate]
    non_guard = [j for j in gate if "guard" not in j["name"]]
    not_in_runbook = [j["name"] for j in non_guard if j["cmd"] not in cmds]
    runbook_not_run = [c for c in cmds if c not in [j["cmd"] for j in non_guard]]
    order_ok = [j["cmd"] for j in non_guard] == cmds
    ts = lambda s: datetime.fromisoformat(s)  # noqa: E731
    by_start = sorted(gate, key=lambda j: (ts(j["started"]), j["name"]))
    gaps = [(by_start[i]["name"], (ts(by_start[i]["started"]) - ts(by_start[i - 1]["ended"])).total_seconds()) for i in range(1, len(by_start))]
    guard_ok = all(j["cmd"].split()[1] == by_start[i - 1]["name"] for i, j in enumerate(by_start) if "guard" in j["name"])
    out["queue"] = {"jobs": len(jobs), "gate_jobs": len(gate), "before_stamp_jobs": len(pre),
                    "exit_codes_not_zero": [j["name"] for j in jobs if j["rc"] != 0], "killed": [j["name"] for j in jobs if j["killed"]],
                    "names_twice": len(jobs) - len(set(j["name"] for j in jobs)),
                    "runbook_commands": len(cmds), "gate_commands": len(non_guard), "commands_in_runbook_order": order_ok,
                    "jobs_not_in_runbook": not_in_runbook, "runbook_commands_not_run": runbook_not_run,
                    "name_order_is_start_order": [j["name"] for j in by_start] == [j["name"] for j in sorted(gate, key=lambda j: j["name"])],
                    "each_guard_reads_the_job_before_it": guard_ok,
                    "gaps_over_2s": [g for g in gaps if g[1] > 2], "negative_gaps": [g for g in gaps if g[1] < 0],
                    "largest_gap_otherwise": max(g[1] for g in gaps if g[1] <= 2),
                    "without_log": [j["name"] for j in jobs if not j["has_log"]],
                    "times": {j["name"]: [j["started"][5:19], j["ended"][5:19], j["seconds"]] for j in jobs}}
    print("6. queue:", {k: v for k, v in out["queue"].items() if k != "times"})
    for n, t in out["queue"]["times"].items():
        print("     ", n, t)

    # 7. order of events
    t = out["queue"]["times"]
    first_train_label = min(map(t_of, tr))
    j93 = next(j for j in jobs if j["name"].startswith("93_"))
    out["order"] = {"part1_verdict_job": [j93["started"], j93["ended"]],
                    "first_training_label_entry": str(first_train_label),
                    "kept_part1_not_evaluated": V1["not_evaluated"], "kept_part1_training_members_labelled": V1["cost"]["training_members_labelled"],
                    "kept_part1_comparison": V1["verdict"]["comparison"], "kept_part1_missing": V1["missing"],
                    "final_part1_same_as_first": V["part1_same_as_first"],
                    "third_generated": next(j for j in jobs if j["name"].startswith("87_"))["started"],
                    "jobs_naming_rows_or_verdict_in_training": [j["name"] for j in jobs if " train " in " " + j["cmd"] + " " and ("rows" in j["cmd"] or "verdict" in j["cmd"])]}
    print("7. order:", out["order"])

    # 8. prediction files and the verdict's inputs
    pf = {}
    for arm in ("label_free", "supervised_512"):
        for seed in (5, 6, 7):
            name = f"{arm}_s{seed}"
            rec = V["inputs"][arm]["runs"][name]
            okf = {}
            for f in ("preds.npz", "preds_condensed.npz", "preds_base.npz"):
                p = os.path.join(R, "run_files", name, f)
                with np.load(p) as z:
                    shapes = {z[k].shape for k in z.files}
                    okf[f] = [sha_file(p) == rec.get(f), len(z.files), sorted(shapes)[:2], all(np.isfinite(z[k]).all() for k in z.files)]
            pf[name] = okf
    out["predictions"] = pf
    print("8. predictions (sha as in the verdict, members, shapes, finite):")
    for k, v in pf.items():
        print("    ", k, v)
    out["inputs"] = {"evaluated_labels_sha256_is_ledger": V["inputs"]["label_free"]["evaluated_labels_sha256"] == ho_sha,
                     "evaluated_labels": V["inputs"]["label_free"]["evaluated_labels"],
                     "same_for_supervised": V["inputs"]["supervised_512"]["evaluated_labels_sha256"] == ho_sha,
                     "manifest_sha": V["inputs"]["label_free"]["manifest_sha256"] in (
                         sha_file(os.path.join(R, "manifest.json")),
                         hashlib.sha256(open(os.path.join(R, "manifest.json"), "rb").read().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")).hexdigest())}
    print("   inputs:", out["inputs"])

    # 9. log lines of unexpected kinds
    kinds = {}
    for p in sorted(glob.glob(os.path.join(R, "queue", "*.log"))):
        name = os.path.basename(p)
        for line in open(p, encoding="utf-8", errors="replace").read().splitlines():
            s = line.strip()
            if not s or s.startswith("=== ") or re.match(r"^epoch \d+ loss", s) or re.match(r"^(train|third|eval|tested)_\S+ [\d.]+ s converged$", s) \
                    or re.match(r"^\S+ [0-9a-f]{64}$", s) or s.startswith("repository ") or s.startswith("guard: "):
                continue
            key = "warning" if "Warning" in s or "torch.sparse_coo_tensor" in s else ("traceback" if "Traceback" in s or "Error" in s else "other")
            kinds.setdefault(key, {}).setdefault(name, []).append(s[:160])
    out["log_lines"] = {k: {n: len(v) for n, v in d2.items()} for k, d2 in kinds.items()}
    lab = {}
    for name in ("88a_c23_label_third", "88b_c23_label_eval", "88c_c23_label_tested", "94a_c23_label_train"):
        t = open(os.path.join(R, "queue", name + ".log"), encoding="utf-8", errors="replace").read()
        lab[name] = {"converged_lines": len(re.findall(r" s converged\s*$", t, re.M)), "not_converged_lines": len(re.findall(r"NOT CONVERGED", t)),
                     "last_line_before_the_end": [l for l in t.splitlines() if l.strip() and not l.startswith("=== ")][-1][:40]}
    out["label_logs"] = lab
    print("   label logs:", lab)
    print("9. log lines by kind:", out["log_lines"].get("warning"), "| tracebacks:", out["log_lines"].get("traceback"))
    json.dump(out, open(outp, "w", encoding="utf-8"), indent=1, default=str)
    other = kinds.get("other", {})
    out["other_lines"] = {n: len(v) for n, v in other.items()}
    print("   other lines by log (count):", out["other_lines"])


if __name__ == "__main__":
    main()
