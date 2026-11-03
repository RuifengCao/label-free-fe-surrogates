#!/usr/bin/env bash
# R2b session (PREREG_R2B Sec. 7; RUNBOOK_R2B Sec. 1). From the repository root:
#   bash scripts/r2b_session.sh
# Steps, in order: the transformer with S (run-config), the post-hoc amplitude pass
# on its report (wp8 4e, --remesh 16), the fresh baseline (run-config), the
# post-hoc pass on its report. S first, and the baseline only once S's report is
# complete (R2b needs both arms): the new path fails, if it fails, before the
# baseline's time is spent. A step whose output is complete is skipped; a run with
# states but no report restarts with --reuse-states (D9, recorded in its report).
# Otherwise a failed step does not stop the next one. Every attempt keeps its log
# (<step>.log.<time>), and status.txt time-stamps each attempt with the host and
# GPU driver it starts on. Before every step
# the checkout must still be the tag, unmodified: `git describe --always --dirty
# --tags` (what every report records) prints exactly the tag, and it is the only
# tag on HEAD; and before every step that runs, the GPU must still be there, work
# and be free (a step started without it would run on the CPU; one started on a
# failing or busy GPU could fail while it restores what an earlier attempt left).
# Ctrl-C stops the session once the command it interrupts has ended, and nothing
# reads an interrupted check as an incomplete output. A completeness check exits 0
# (complete) or 3 (not complete: the step runs); any other exit means the check
# itself failed (killed, out of memory, an I/O error): nothing is moved or run, and
# the status file says STOP before that step. (scripts/fine3d_session.sh's
# mechanics, which the box ran, for R2b's four steps; its R3 gate for the baseline.)
set -u
trap 'exit 130' INT                    # until the session holds its lock (below)
WANT=prereg-r2b
P=runs/r2b/session
mkdir -p "$P"
exec 9>"$P/.lock"
if ! flock -n 9; then
  echo "STOP: the session is already running (tmux ls; pgrep -af 'run-config|posthoc_amplitude')"
  exit 1
fi
trap 'echo "session interrupted $(date "+%F %T")" | tee -a "$P/status.txt"; exit 130' INT
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

gpu_probe() {
  # nothing printed and success when the GPU is there, works (an allocation and a
  # synchronisation) and is free (90% of its memory); otherwise one line saying why.
  # Run only inside $(...), a subshell: there it closes the session's lock (so that
  # no probe holds it after the session is killed), and --foreground keeps the probe
  # in the session's process group (Ctrl-C and a kill of the group reach it)
  [ "$BASHPID" != "$$" ] || { echo "gpu_probe outside \$(...)"; return 2; }
  exec 9>&-
  local why
  why=$(timeout --foreground 300 python - 2>/dev/null <<'PY'
import sys
import warnings
try:
    import torch
    with warnings.catch_warnings(record=True) as seen:
        warnings.simplefilter("always")
        ok = torch.cuda.is_available()
    if not ok:
        said = [str(w.message).strip() for w in seen if str(w.message).strip()]
        print("no GPU" + (f" ({said[0].splitlines()[0][:120]})" if said else ""))
        sys.exit(1)
    torch.zeros(1, device="cuda").add_(1)
    torch.cuda.synchronize()
    free, total = torch.cuda.mem_get_info()
except Exception as exc:                                   # noqa: BLE001
    msg = (str(exc).splitlines() or [""])[0][:120]
    print(f"the GPU does not work ({type(exc).__name__}: {msg})")
    sys.exit(1)
if free < 0.9 * total:
    print(f"the GPU is in use ({(total - free) / 2**30:.1f} of {total / 2**30:.1f} GiB taken)")
    sys.exit(1)
PY
) && return 0
  echo "${why:-no GPU (the check gave no answer)}"
  return 1
}

if [ "${R2B_REHEARSAL:-}" = 1 ]; then
  # the sandbox's CPU rehearsal of this script (BRANCH_NOTES Stage 4); the runbook never sets it
  echo "rehearsal: no GPU check" | tee -a "$P/status.txt"
else
  python - <<'PY'
import torch
print("torch", torch.__version__, "| CUDA build", torch.version.cuda)
PY
  why=$(gpu_probe) || { echo "STOP: $why" | tee -a "$P/status.txt"; exit 1; }
fi

run() {
  local log=$1; shift
  [ -e "$P/$log" ] && mv "$P/$log" "$P/$log.$(date +%Y%m%d-%H%M%S)"
  echo "$log start $(date '+%F %T') host $(hostname 2>/dev/null) driver $(timeout --foreground 60 \
    nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n 1)" \
    >> "$P/status.txt"
  "$@" 2>&1 | tee "$P/$log"; local rc=${PIPESTATUS[0]}
  echo "$log exit=$rc $(date '+%F %T')" | tee -a "$P/status.txt"
}

code_ok() {
  # the string every report records (fejepa.report._git_describe), and the tag alone on HEAD
  local code tags
  code=$(git describe --always --dirty --tags 2>/dev/null)
  tags=$(git tag --points-at HEAD 2>/dev/null)
  if [ "$code" != "$WANT" ] || [ "$tags" != "$WANT" ] \
      || [ -n "$(git status --porcelain --untracked-files=no)" ]; then
    echo "STOP before $1: the code is ${code:-unknown} (tags on HEAD: ${tags:-none}), or modified, not $WANT" \
      | tee -a "$P/status.txt"
    return 1
  fi
}

gpu_ok() {
  # before every step that runs, as before the session
  [ "${R2B_REHEARSAL:-}" = 1 ] && return 0
  local why
  why=$(gpu_probe) && return 0
  echo "STOP before $1: $why" | tee -a "$P/status.txt"
  return 1
}

report_state() {
  # an arm's report: 0 finished (with its provenance); 3 missing, unreadable or unfinished
  [ -f "runs/r2b/$1/report.json" ] || return 3
  python - "runs/r2b/$1/report.json" 2>/dev/null <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except ValueError:                     # not JSON: unreadable (an I/O error is not caught)
    sys.exit(3)
sys.exit(0 if isinstance(d, dict) and "provenance" in d else 3)
PY
}

arm() {
  # $1 the arm; $2 (optional) the arm whose complete report it needs first
  local name=$1 need=${2:-} rep="runs/r2b/$1/report.json" extra="" rc
  code_ok "$name" || return 1
  if [ -f "$rep" ]; then
    # 0: a report with its provenance (finished); 3: unreadable or unfinished
    python - "$rep" 2>/dev/null <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except ValueError:                     # not JSON: unreadable (an I/O error is not caught)
    sys.exit(3)
sys.exit(0 if isinstance(d, dict) and "provenance" in d else 3)
PY
    rc=$?
    if [ "$rc" = 0 ]; then
      echo "$name: report exists, skipped" | tee -a "$P/status.txt"; return 0
    elif [ "$rc" != 3 ]; then
      echo "STOP before $name: the check of its report failed (exit $rc)" | tee -a "$P/status.txt"
      return 1
    fi
    mv "$rep" "$rep.unreadable.$(date +%Y%m%d-%H%M%S)"
    echo "$name: unreadable report moved aside" | tee -a "$P/status.txt"
  fi
  if [ -n "$need" ]; then
    report_state "$need"; rc=$?
    if [ "$rc" = 3 ]; then
      echo "$name: not run, $need has no complete report (R2b needs both arms)" \
        | tee -a "$P/status.txt"; return 1
    elif [ "$rc" != 0 ]; then
      echo "STOP before $name: the check of $need's report failed (exit $rc)" \
        | tee -a "$P/status.txt"; return 1
    fi
  fi
  gpu_ok "$name" || return 1
  if ls "runs/r2b/$name/e8_states/"*.pt >/dev/null 2>&1 \
      || ls "runs/r2b/$name/e8_states/"*.ckpt >/dev/null 2>&1; then
    extra="--reuse-states"; echo "$name: restarting from its states" | tee -a "$P/status.txt"
  fi
  run "$name.log" python -m fejepa.cli run-config "configs/$name.json" --label-workers 1 $extra
}

amp() {
  local name=$1 rep="runs/r2b/$1/report.json" out="runs/r2b/posthoc/amp_$1.json" rc
  code_ok "amp_$name" || return 1
  if [ ! -f "$rep" ]; then
    echo "amp_$name: no report of $name, skipped" | tee -a "$P/status.txt"; return 1
  fi
  if [ -f "$out" ]; then
    # 0: complete -- its in-band and fine passes, its 16 remesh geometries (one that
    # could not be meshed is not meshed by a second pass either), measured on this
    # report (an arm run again leaves a record of the old one); 3: not
    python - "$out" "$rep" 2>/dev/null <<'PY'
import hashlib, json, sys
try:
    d = json.load(open(sys.argv[1]))
    seeds = list(d["seeds"].values())
    ok = bool(seeds) and all((v.get(s) or {}).get("summary", {}).get("complete")
                             for v in seeds for s in ("inband", "fine"))
    ok = ok and all(len((v.get("remesh") or {}).get("rows", [])) == 16 for v in seeds)
    ok = ok and d.get("report_sha256") == hashlib.sha256(open(sys.argv[2], "rb").read()).hexdigest()
except (ValueError, KeyError, TypeError, AttributeError):   # not an I/O error
    ok = False
sys.exit(0 if ok else 3)
PY
    rc=$?
    if [ "$rc" = 0 ]; then
      echo "amp_$name: record complete, skipped" | tee -a "$P/status.txt"; return 0
    elif [ "$rc" != 3 ]; then
      echo "STOP before amp_$name: the check of its record failed (exit $rc)" | tee -a "$P/status.txt"
      return 1
    fi
  fi
  gpu_ok "amp_$name" || return 1
  run "amp_$name.log" python scripts/posthoc_amplitude.py --report "$rep" \
      --states-dir "runs/r2b/$name/e8_states" --remesh 16 --out "$out"
}

arm r2b_s
amp r2b_s
arm r2b_b r2b_s
amp r2b_b
cat "$P/status.txt"
