"""R2b: RUNBOOK_R2B.md names only scripts and configurations that exist and
options they accept, fetches the branch and the tag directly with a bundle
route, checks the code with the string every report records, states the
suite's count, and runs scripts/r2b_session.sh; the session script is
scripts/fine3d_session.sh's mechanics, which the box ran, for R2b's steps
(its functions compared line by line); run here with stand-ins for git,
python, nvidia-smi and the steps, it runs the four steps in order (S first), skips
finished ones, restarts an interrupted arm from its states or its
checkpoints, moves an unreadable report aside, runs a step again until its
output is complete, stops before any step when the code is not the tag alone
and unmodified or the GPU cannot be used, records each start's host and GPU
driver, stops on Ctrl-C, and refuses a second copy."""

import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUNBOOK = ROOT / "RUNBOOK_R2B.md"
SESSION = ROOT / "scripts" / "r2b_session.sh"
REFS = "+refs/heads/wp9-pool:refs/remotes/origin/wp9-pool +refs/tags/prereg-r2b:refs/tags/prereg-r2b"
ENV = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"}
STEPS = ["r2b_s", "amp_r2b_s", "r2b_b", "amp_r2b_b"]


def _text():
    return RUNBOOK.read_text(encoding="utf-8")


def _section(num):
    t = _text()
    start = t.index(f"\n## {num}. ")
    nxt = t.find("\n## ", start + 1)
    return t[start:] if nxt < 0 else t[start:nxt]


def _blocks(text):
    return re.findall(r"```bash\n(.*?)```", text, re.S)


def test_ascii():
    assert _text().isascii() and SESSION.read_text().isascii()


def test_the_runbook_names_existing_scripts_configs_and_options():
    text = "\n".join(_blocks(_text())).replace("\\\n", " ")
    scripts = re.findall(r"python (scripts/\S+\.py)([^\n]*)", text)
    assert {s for s, _ in scripts} == {"scripts/adjudicate_r2b.py"}
    for script, rest in scripts:
        res = subprocess.run([sys.executable, str(ROOT / script), "--help"], capture_output=True,
                             text=True, cwd=ROOT, env=ENV)
        assert res.returncode == 0, res.stderr[-2000:]
        for o in re.findall(r"(--[a-z][a-z0-9-]*)", rest):
            assert o in res.stdout, (script, o)
    for c in re.findall(r"configs/(\S+?)\.json", text):
        assert (ROOT / "configs" / f"{c}.json").is_file() or c == "$c", c
    assert "bash scripts/r2b_session.sh" in text and SESSION.is_file()
    sess = SESSION.read_text()
    for opt in ("--report", "--states-dir", "--remesh", "--out", "--label-workers",
                "--reuse-states"):
        assert opt in sess
    res = subprocess.run([sys.executable, str(ROOT / "scripts" / "posthoc_amplitude.py"), "--help"],
                         capture_output=True, text=True, cwd=ROOT, env=ENV)
    assert all(o in res.stdout for o in ("--report", "--states-dir", "--remesh", "--out"))
    assert "for c in r2b_s r2b_b; do" in text


def test_the_session_is_fine3ds_mechanics():
    """The functions both scripts share are the same line for line (R2b's
    rehearsal variable and paths in place of fine3d's); the arm step is
    fine3d's R2a step with fine3d's R3 gate for the baseline (R2b needs both
    arms), and every start line also records the host and GPU driver."""
    def funcs(path):
        body = path.read_text()
        out = {}
        for m in re.finditer(r"^(\w+)\(\) \{\n(.*?)\n\}\n", body, re.S | re.M):
            out[m.group(1)] = m.group(2)
        return body, out
    fb, f = funcs(ROOT / "scripts" / "fine3d_session.sh")
    rb, r = funcs(SESSION)

    def ported(a):
        return a.replace("FINE3D_REHEARSAL", "R2B_REHEARSAL").replace("runs/fine3d", "runs/r2b") \
            .replace("an R2a arm run again", "an arm run again")
    for name in ("gpu_probe", "code_ok", "gpu_ok", "amp"):
        assert ported(f[name]) == r[name], name
    end = 'echo "$log start $now host $host driver $drv" >> "$P/status.txt"'
    block = r["run"][r["run"].index("  # the host, the first GPU's driver and the time"):
                     r["run"].index(end) + len(end)]
    assert ported(f["run"]).replace(
        "  echo \"$log start $(date '+%F %T')\" >> \"$P/status.txt\"", block) == r["run"]
    # all three read before the start line; the host and driver in subshells that close
    # the lock (gpu_probe's way)
    assert block.splitlines()[-5:-1] == [
        "  host=$(exec 9>&-; hostname 2>/dev/null)",
        "  drv=$(exec 9>&-; timeout -k 5 --foreground 60 nvidia-smi --query-gpu=driver_version \\",
        "    --format=csv,noheader 2>/dev/null | head -n 1)",
        "  now=$(date '+%F %T')"]
    gate = r["arm"][r["arm"].index('  if [ -n "$need" ]; then'):r["arm"].index("  gpu_ok")]
    assert ported(f["r2a"]) == r["arm"].replace(gate, "").replace(
        "  # $1 the arm; $2 (optional) the arm whose complete report it needs first\n", "").replace(
        "need=${2:-} ", "")
    assert "R2b needs both arms" in gate and "report_state \"$need\"" in gate
    assert gate.count('echo "$name: $need has a complete report" | tee -a "$P/status.txt"') == 1
    assert set(r) == {"gpu_probe", "run", "code_ok", "gpu_ok", "report_state", "arm", "amp"}
    head = fb[:fb.index("gpu_probe() {")]
    tail = rb[:rb.index("gpu_probe() {")]
    assert head.split("set -u", 1)[1].replace("prereg-fine3d", "prereg-r2b") \
        .replace("runs/fine3d", "runs/r2b").replace("|r3_finetune", "") == tail.split("set -u", 1)[1]
    assert rb.rstrip().splitlines()[-5:] == ["arm r2b_s", "amp r2b_s", "arm r2b_b r2b_s",
                                             "amp r2b_b", 'cat "$P/status.txt"']


def test_0c_finds_no_r2b_run_and_can_be_repeated(tmp_path):
    line = next(l for l in _blocks(_text())[3].splitlines() if "runs/r2b" in l
                and "mkdir" not in l)
    cmd, want = line.split("#")[0].strip(), line.split("must print exactly: ")[1].strip()

    def out():
        return subprocess.run(["bash", "-c", cmd], cwd=tmp_path, capture_output=True, text=True,
                              env=ENV).stdout
    (tmp_path / "runs" / "fine3d" / "r2a_b_m1024").mkdir(parents=True)   # other runs on the box
    assert out() == want + "\n"
    (tmp_path / "runs" / "r2b" / "session").mkdir(parents=True)
    (tmp_path / "runs" / "r2b" / "session" / "pytest.log").write_text("x")
    assert out() == want + "\n"
    (tmp_path / "runs" / "r2b" / "r2b_s").mkdir()
    assert out() == "r2b_s\n"


def test_the_fetch_is_direct_with_a_bundle_route():
    b = _blocks(_section("0"))
    fetch = [x.split("#")[0].rstrip() for x in b[1].splitlines()]
    assert fetch == ["cd ~/autodl-tmp/FE-JEPA",
                     f"git fetch origin {REFS} && echo FETCH-OK || echo FETCH-FAILED",
                     "git rev-parse --short origin/wp9-pool",
                     "git rev-parse --short 'prereg-r2b^{commit}'"]
    bundle = [x.split("#")[0].rstrip() for x in b[2].splitlines()]
    assert bundle == ["cd ~/autodl-tmp/FE-JEPA", "sha256sum ~/wp9-pool.bundle",
                      f"git fetch ~/wp9-pool.bundle {REFS} && echo FETCH-OK || echo FETCH-FAILED",
                      "git rev-parse --short origin/wp9-pool",
                      "git rev-parse --short 'prereg-r2b^{commit}'"]
    check = [x.split("#") for x in b[3].splitlines()]
    lines = {c[0].rstrip(): c[1].strip() if len(c) > 1 else "" for c in check}
    assert lines["git describe --always --dirty --tags"] == "must print exactly: prereg-r2b"
    assert lines["git tag --points-at HEAD"] == "must print exactly: prereg-r2b"
    assert lines["git status --porcelain --untracked-files=no"] == "must print nothing"
    sess = SESSION.read_text()
    for cmd in ("git describe --always --dirty --tags", "git tag --points-at HEAD",
                "git status --porcelain --untracked-files=no"):
        assert cmd in sess
    assert "WANT=prereg-r2b" in sess
    # the bundle's base: the commit the box holds since the fine3d session
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short=7", "prereg-fine3d^{commit}"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        assert f"git bundle\ncreate wp9-pool.bundle {r.stdout.strip()}..wp9-pool prereg-r2b" in _text()


def test_the_runbook_states_the_suite_count():
    """Sec. 0c states this checkout's suite, the count the branch notes' latest
    entry records (the stamp changes no test)."""
    res = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q",
                          "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=ROOT)
    m = re.search(r"(\d+) tests? collected", res.stdout)
    assert m, res.stdout[-2000:]
    n = int(m.group(1))
    notes = (ROOT / "BRANCH_NOTES_wp9-pool.md").read_text(encoding="utf-8")
    assert int(re.findall(r"^- Suite (\d+)", notes, re.M)[-1]) == n
    sec = _section("0")
    assert sec.count(f'"{n - 1} passed, 1 skipped"') == 1
    assert sec.count(f"`{n - 1} passed, 1 skipped`") == 1
    assert sec.count(f"`{n} passed`") == 1


# ------------------------------------------------------- the session script --

_GIT = """#!/usr/bin/env bash
# stand-in for git: only the session's exact checks read the stub's files
case "$*" in
  "describe --always --dirty --tags") cat "$STUB_DIR/describe"; exit 0;;
  "tag --points-at HEAD") cat "$STUB_DIR/tags"; exit 0;;
  "status --porcelain --untracked-files=no") cat "$STUB_DIR/status"; exit 0;;
esac
[ "$1" = describe ] && { echo prereg-r2b-1-gabcdef; exit 0; }
exit 1
"""

_PY = r"""#!/usr/bin/env bash
# stand-in for python: checks run the real interpreter; the steps write their outputs
if [ "$1" = "-" ]; then
  body=$(cat)
  if printf '%s' "$body" | grep -q "torch.version.cuda"; then    # the session's version line
    echo "torch stub | CUDA build stub"; exit 0; fi
  if printf '%s' "$body" | grep -q "torch.cuda.is_available"; then   # the GPU probe
    n=$(( $(cat "$STUB_DIR/gpu_checks" 2>/dev/null || echo 0) + 1 )); echo $n > "$STUB_DIR/gpu_checks"
    if [ -n "${STUB_GPU_SLEEP:-}" ] && [ "$n" -ge "${STUB_GPU_SLEEP_FROM:-1}" ]; then
      echo $$ > "$STUB_DIR/probe_pid"; sleep "$STUB_GPU_SLEEP"; echo $$ > "$STUB_DIR/probe_done"; fi
    [ -n "${STUB_NOGPU:-}" ] && { echo "no GPU"; exit 1; }
    [ -n "${STUB_NOGPU_AFTER:-}" ] && [ "$n" -gt "$STUB_NOGPU_AFTER" ] && { echo "no GPU"; exit 1; }
    [ -n "${STUB_BUSY_AFTER:-}" ] && [ "$n" -gt "$STUB_BUSY_AFTER" ] && {
      echo "the GPU is in use (20.0 of 31.4 GiB taken)"; exit 1; }
    exit 0; fi
  [ -n "${STUB_CHECK_KILLED:-}" ] && printf '%s %s' "$body" "$*" | grep -q "$STUB_CHECK_KILLED" && exit 137
  if [ -n "${STUB_CHECK_EIO:-}" ] && printf '%s %s' "$body" "$*" | grep -q "$STUB_CHECK_EIO"; then
    body="import builtins, errno
def _eio(*a, **k):
    raise OSError(errno.EIO, 'simulated I/O error')
builtins.open = _eio
$body"; fi
  printf '%s' "$body" | "$REAL_PY" - "${@:2}"; exit $?
fi
if [ "$1" = "-c" ]; then exec "$REAL_PY" "$@"; fi
echo "CALL $*" >> "$STUB_DIR/calls"
if [ "$1" = "-m" ]; then                               # run-config configs/<name>.json ...
  name=$(basename "$4" .json)
  [ "${SLEEP_IN:-}" = "$name" ] && { echo $$ > "$STUB_DIR/step_pid"; sleep "${SLEEP_SECS:-30}"; }
  [ "${FAIL:-}" = "$name" ] && { mkdir -p runs/r2b/$name/e8_states; : > runs/r2b/$name/e8_states/${FAIL_FILE:-ar_p1024_s3.pt}; exit 3; }
  mkdir -p runs/r2b/$name/e8_states; echo '{"provenance": {}}' > runs/r2b/$name/report.json
  [ "${CHANGE_AFTER:-}" = "$name" ] && echo prereg-r2b-dirty > "$STUB_DIR/describe"
  exit 0
fi
case "$1" in
  scripts/posthoc_amplitude.py)
    out=""; rep=""; while [ $# -gt 0 ]; do [ "$1" = --out ] && out=$2; [ "$1" = --report ] && rep=$2; shift; done
    mkdir -p "$(dirname "$out")"
    "$REAL_PY" -c 'import hashlib,json,os,sys; f=int(os.environ.get("AMP_FAILED", "0")); s={"inband":{"summary":{"complete":True}},"fine":{"summary":{"complete":True}},"remesh":{"rows":[{}]*16,"n_geometries":16-f,"n_failed":f}}; json.dump({"report_sha256":hashlib.sha256(open(sys.argv[2],"rb").read()).hexdigest(),"seeds":{"s3":s,"s4":s,"s5":s}}, open(sys.argv[1],"w"))' "$out" "$rep"; exit 0;;
esac
exit 9
"""

_FLOCK = """#!/usr/bin/env bash
# stand-in for flock: slow when asked (to interrupt the session before it holds the lock)
[ -n "${STUB_FLOCK_SLEEP:-}" ] && sleep "$STUB_FLOCK_SLEEP"
exec {real} "$@"
"""


_SMI = """#!/usr/bin/env bash
# stand-in for nvidia-smi, ahead of the box's own on PATH: the driver, one line per GPU
# (two); or a query that hangs, when asked
echo "SMI $*" >> "$STUB_DIR/smi_calls"
[ -n "${STUB_SMI_HANG:-}" ] && { echo $$ > "$STUB_DIR/smi_pid"; exec sleep "$STUB_SMI_HANG"; }
echo 575.64.03; echo 575.64.03
"""
DRIVER = "575.64.03"


@pytest.fixture
def box(tmp_path):
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "r2b_session.sh").write_text(SESSION.read_text())
    stub = tmp_path / "stub"
    stub.mkdir()
    real_flock = shutil.which("flock", path="/usr/bin:/bin:/usr/local/bin") or "flock"
    for name, body in (("git", _GIT), ("python", _PY), ("nvidia-smi", _SMI),
                       ("flock", _FLOCK.replace("{real}", real_flock))):
        p = stub / name
        p.write_text(body)
        p.chmod(p.stat().st_mode | stat.S_IEXEC)
    (stub / "describe").write_text("prereg-r2b\n")
    (stub / "tags").write_text("prereg-r2b\n")
    (stub / "status").write_text("")
    env = {"PATH": f"{stub}:/usr/bin:/bin", "STUB_DIR": str(stub), "REAL_PY": sys.executable,
           "HOME": str(tmp_path)}
    return tmp_path, stub, env


def _run(box, **extra):
    tmp, _, env = box
    return subprocess.run(["bash", "scripts/r2b_session.sh"], cwd=tmp, capture_output=True,
                          text=True, env={**env, **extra}, timeout=120)


def _status(tmp):
    return (tmp / "runs" / "r2b" / "session" / "status.txt").read_text()


def _calls(stub):
    return (stub / "calls").read_text().splitlines()


def test_session_runs_the_steps_in_order_then_skips_them(box):
    tmp, stub, _ = box
    r = _run(box)
    assert r.returncode == 0, r.stdout + r.stderr
    calls = _calls(stub)
    assert [c.split()[4] if c.split()[1] == "-m" else c.split()[1] for c in calls] == [
        "configs/r2b_s.json", "scripts/posthoc_amplitude.py", "configs/r2b_b.json",
        "scripts/posthoc_amplitude.py"]
    assert all("--reuse-states" not in c for c in calls)
    assert "--label-workers 1" in calls[0] and "--remesh 16" in calls[1]
    assert "runs/r2b/r2b_s/report.json" in calls[1] and "runs/r2b/r2b_s/e8_states" in calls[1]
    assert "runs/r2b/posthoc/amp_r2b_b.json" in calls[3]
    st = _status(tmp)
    assert [ln.split()[0] for ln in st.splitlines() if "exit=0" in ln] == \
        [f"{s}.log" for s in STEPS]
    (stub / "calls").unlink()
    _run(box)
    assert not (stub / "calls").exists()                    # nothing ran again
    st = _status(tmp)
    assert st.count("report exists, skipped") == 2 and st.count("record complete, skipped") == 2


@pytest.mark.parametrize("left", ["ar_p1024_s3.pt", "ar_p1024_s3.ckpt"])
def test_session_restarts_an_interrupted_arm_from_its_states(box, left):
    tmp, stub, _ = box
    _run(box, FAIL="r2b_s", FAIL_FILE=left)
    assert "r2b_s.log exit=3" in _status(tmp)
    assert "amp_r2b_s: no report of r2b_s, skipped" in _status(tmp)
    assert "r2b_b: not run, r2b_s has no complete report (R2b needs both arms)" in _status(tmp)
    assert len(_calls(stub)) == 1                             # the baseline's time is not spent
    (stub / "calls").unlink()
    r = _run(box)
    assert r.returncode == 0, r.stdout + r.stderr
    calls = _calls(stub)
    assert "--reuse-states" in calls[0] and "configs/r2b_s.json" in calls[0]
    assert len(calls) == 4 and "posthoc_amplitude.py" in calls[1] and "r2b_s" in calls[1]
    assert "configs/r2b_b.json" in calls[2] and "--reuse-states" not in calls[2]
    assert "r2b_s: restarting from its states" in _status(tmp)
    assert len(list((tmp / "runs" / "r2b" / "session").glob("r2b_s.log.*"))) == 1
    assert len(re.findall(r"^r2b_s\.log start", _status(tmp), re.M)) == 2


def test_session_runs_the_baseline_only_after_a_complete_s_report(box):
    """S first: when S's arm fails, the baseline does not start (R2b needs
    both arms); a baseline already finished is still skipped; once S's report
    is complete the baseline runs."""
    tmp, stub, _ = box
    _run(box, FAIL="r2b_s")
    st = _status(tmp)
    assert "r2b_b: not run, r2b_s has no complete report (R2b needs both arms)" in st
    assert "amp_r2b_b: no report of r2b_b, skipped" in st
    assert "r2b_b: r2b_s has a complete report" not in st
    assert not any("r2b_b" in c for c in _calls(stub))
    (stub / "calls").unlink()
    _run(box)
    assert [c.split()[4] if c.split()[1] == "-m" else c.split()[1] for c in _calls(stub)] == [
        "configs/r2b_s.json", "scripts/posthoc_amplitude.py", "configs/r2b_b.json",
        "scripts/posthoc_amplitude.py"]
    lines = _status(tmp).splitlines()               # the gate's line, just before the baseline
    i = lines.index("r2b_b: r2b_s has a complete report")
    assert lines.count("r2b_b: r2b_s has a complete report") == 1
    assert lines[i + 1].startswith("r2b_b.log start ") and lines[i - 1].startswith("amp_r2b_s.log")
    (tmp / "runs" / "r2b" / "r2b_s" / "report.json").unlink()   # S run again, the baseline kept
    (stub / "calls").unlink()
    _run(box, FAIL="r2b_s")
    assert "r2b_b: report exists, skipped" in _status(tmp).split("r2b_s.log exit=3")[-1]


def test_a_failed_check_of_s_report_does_not_read_as_an_incomplete_one(box):
    """The baseline's check of S's report, killed on its own, is not "R2b
    needs both arms": STOP before the baseline, which does not start."""
    tmp, stub, _ = box
    _run(box)
    (tmp / "runs" / "r2b" / "r2b_b" / "report.json").unlink()
    (stub / "calls").unlink()
    _run(box, STUB_CHECK_KILLED="r2b_s/report.json")
    assert not (stub / "calls").exists()
    st = _status(tmp)
    assert "STOP before r2b_b: the check of r2b_s's report failed (exit 137)" in st
    assert "not run" not in st


def test_every_start_line_records_the_host_and_driver(box):
    """The host, and the first GPU's driver (the stand-in's, which the box's
    own nvidia-smi cannot replace: the stub directory is first on PATH)."""
    tmp, stub, _ = box
    _run(box)
    assert len((stub / "smi_calls").read_text().splitlines()) == 4
    starts = [ln for ln in _status(tmp).splitlines() if ".log start " in ln]
    assert len(starts) == 4
    J = _adjudicator()
    m = J.machines(_status(tmp))
    assert sorted(m) == sorted(STEPS) and all(len(v) == 1 for v in m.values())
    host = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
    assert {v[0][0] for v in m.values()} == {host} and {v[0][1] for v in m.values()} == {DRIVER}
    assert J.machine_deviations(m) == []
    assert J.session_deviations(_status(tmp))[3] == []


def test_session_runs_the_amplitude_pass_again_for_a_new_report(box):
    tmp, stub, _ = box
    _run(box)
    (tmp / "runs" / "r2b" / "r2b_b" / "report.json").write_text('{"provenance": {"again": true}}')
    (stub / "calls").unlink()
    _run(box)
    calls = _calls(stub)
    assert [c.split()[1] for c in calls] == ["scripts/posthoc_amplitude.py"]
    assert "amp_r2b_b.json" in calls[0]
    assert "amp_r2b_s: record complete, skipped" in _status(tmp)


def test_session_moves_an_unreadable_report_aside(box):
    tmp, stub, _ = box
    d = tmp / "runs" / "r2b" / "r2b_s"
    d.mkdir(parents=True)
    (d / "report.json").write_text('{"results": ')
    _run(box)
    assert "r2b_s: unreadable report moved aside" in _status(tmp)
    assert [p.read_text() for p in d.glob("report.json.unreadable.*")] == ['{"results": ']
    calls = _calls(stub)
    assert "configs/r2b_s.json" in calls[0] and "--reuse-states" not in calls[0]


def test_session_runs_a_step_again_until_its_output_is_complete(box):
    tmp, stub, _ = box
    _run(box)
    ph = tmp / "runs" / "r2b" / "posthoc"
    amp = json.loads((ph / "amp_r2b_s.json").read_text())
    amp["seeds"]["s4"]["fine"]["summary"]["complete"] = False
    (ph / "amp_r2b_s.json").write_text(json.dumps(amp))
    amp = json.loads((ph / "amp_r2b_b.json").read_text())
    amp["seeds"]["s5"]["remesh"]["rows"] = [{}] * 15
    (ph / "amp_r2b_b.json").write_text(json.dumps(amp))
    (stub / "calls").unlink()
    _run(box)
    calls = _calls(stub)
    assert [c.split()[1] for c in calls] == ["scripts/posthoc_amplitude.py",
                                             "scripts/posthoc_amplitude.py"]
    assert "amp_r2b_s.json" in calls[0] and "amp_r2b_b.json" in calls[1]
    assert _status(tmp).count("report exists, skipped") == 2


@pytest.mark.parametrize("what,content", [("describe", "prereg-r2b-1-gabcdef\n"),
                                          ("describe", "prereg-r2b-dirty\n"),
                                          ("describe", "prereg-fine3d\n"),
                                          ("tags", "prereg-r2b\nprereg-r2b-old\n"),
                                          ("tags", ""),
                                          ("status", " M src/fejepa/metrics.py\n")])
def test_session_stops_when_the_code_is_not_the_tag(box, what, content):
    tmp, stub, _ = box
    (stub / what).write_text(content)
    _run(box)
    assert not (stub / "calls").exists()
    assert _status(tmp).count("STOP before") == 4


def test_session_checks_the_code_before_every_step(box):
    tmp, stub, _ = box
    _run(box, CHANGE_AFTER="r2b_s")
    calls = _calls(stub)
    assert len(calls) == 1 and "configs/r2b_s.json" in calls[0]
    st = _status(tmp)
    assert re.findall(r"STOP before (\S+): the code is prereg-r2b-dirty", st) == STEPS[1:]
    assert "r2b_s.log exit=0" in st


def test_session_refuses_a_second_copy(box):
    tmp, _, _ = box
    lock = tmp / "runs" / "r2b" / "session"
    lock.mkdir(parents=True)
    holder = subprocess.Popen(["flock", str(lock / ".lock"), "sleep", "30"])
    try:
        for _ in range(200):
            if subprocess.run(["flock", "-n", str(lock / ".lock"), "true"]).returncode != 0:
                break
            time.sleep(0.05)
        else:
            pytest.fail("the lock holder did not take the lock within 10 s")
        r = _run(box)
        assert r.returncode == 1 and "already running" in r.stdout
        assert "pgrep -af 'run-config|posthoc_amplitude'" in r.stdout          # RUNBOOK 1c's
        assert 'pgrep -af "run-config|posthoc_amplitude"' in _text()
    finally:
        holder.kill()


def test_session_checks_the_gpu_before_every_step_it_runs(box):
    tmp, stub, _ = box
    r = _run(box, STUB_NOGPU_AFTER="2")        # the session's own check and the first step's
    assert r.returncode == 0
    st = _status(tmp)
    assert "r2b_s.log exit=0" in st
    assert re.findall(r"STOP before (\S+): no GPU", st) == ["amp_r2b_s", "r2b_b"]
    assert "amp_r2b_b: no report of r2b_b, skipped" in st
    assert len(_calls(stub)) == 1
    assert int((stub / "gpu_checks").read_text()) == 4


def test_session_restarts_nothing_without_the_gpu(box):
    tmp, stub, _ = box
    _run(box, FAIL="r2b_s")
    before = _status(tmp)
    (stub / "gpu_checks").write_text("0")
    _run(box, STUB_NOGPU_AFTER="1")
    new = _status(tmp)[len(before):]
    assert "STOP before r2b_s: no GPU" in new and "restarting from its states" not in new
    assert "r2b_b: not run, r2b_s has no complete report" in new and "STOP before r2b_b" not in new


def test_session_needs_a_gpu_unless_rehearsing(box):
    tmp, stub, _ = box
    r = _run(box, STUB_NOGPU="1")
    assert r.returncode == 1 and "STOP: no GPU" in _status(tmp)
    assert not (stub / "calls").exists()
    r = _run(box, STUB_NOGPU="1", R2B_REHEARSAL="1")
    assert r.returncode == 0 and "rehearsal: no GPU check" in _status(tmp)
    assert len(_calls(stub)) == 4
    assert "R2B_REHEARSAL" not in _text()


def test_session_says_why_the_gpu_cannot_be_used(box):
    tmp, stub, _ = box
    _run(box, STUB_BUSY_AFTER="1")
    assert "STOP before r2b_s: the GPU is in use (20.0 of 31.4 GiB taken)" in _status(tmp)
    assert not (stub / "calls").exists()


def test_session_keeps_an_amplitude_record_with_a_geometry_that_could_not_be_meshed(box):
    tmp, stub, _ = box
    _run(box, AMP_FAILED="1")
    (stub / "calls").unlink()
    _run(box)
    assert not (stub / "calls").exists()
    assert _status(tmp).count("record complete, skipped") == 2


@pytest.mark.parametrize("word,stop", [
    ("provenance", ["r2b_s: the check of its report failed (exit 137)",
                    "r2b_b: the check of its report failed (exit 137)"]),
    ("report_sha256", ["amp_r2b_s: the check of its record failed (exit 137)",
                       "amp_r2b_b: the check of its record failed (exit 137)"])])
def test_a_check_that_dies_stops_its_step_and_moves_nothing(box, word, stop):
    tmp, stub, _ = box
    _run(box)
    before = sorted(p.name for p in (tmp / "runs" / "r2b").rglob("*") if p.is_file())
    (stub / "calls").unlink()
    _run(box, STUB_CHECK_KILLED=word)
    assert not (stub / "calls").exists()
    st = _status(tmp)
    assert re.findall(r"STOP before (.+)", st) == stop
    assert "moved aside" not in st
    assert sorted(p.name for p in (tmp / "runs" / "r2b").rglob("*") if p.is_file()) == before


@pytest.mark.parametrize("word,stop", [
    ("provenance", "r2b_s: the check of its report failed (exit 1)"),
    ("report_sha256", "amp_r2b_s: the check of its record failed (exit 1)")])
def test_an_io_error_in_a_check_is_not_an_incomplete_output(box, word, stop):
    tmp, stub, _ = box
    _run(box)
    before = sorted(p.name for p in (tmp / "runs" / "r2b").rglob("*") if p.is_file())
    (stub / "calls").unlink()
    _run(box, STUB_CHECK_EIO=word)
    assert not (stub / "calls").exists()
    st = _status(tmp)
    assert f"STOP before {stop}" in st and "moved aside" not in st
    assert sorted(p.name for p in (tmp / "runs" / "r2b").rglob("*") if p.is_file()) == before


def _start(box, **extra):
    tmp, _, env = box
    return subprocess.Popen(["bash", "scripts/r2b_session.sh"], cwd=tmp, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            env={**env, **extra}, start_new_session=True)


def _wait_for(pred, what, timeout=20.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if pred():
            return
        time.sleep(0.05)
    pytest.fail(f"{what} did not happen within {timeout:g} s")


def _gone(pid, timeout=5.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.05)
    return False


def test_ctrl_c_before_the_lock_ends_the_session(box):
    tmp, stub, _ = box
    p = _start(box, STUB_FLOCK_SLEEP="10")
    try:
        _wait_for(lambda: (tmp / "runs" / "r2b" / "session" / ".lock").exists(), "the lock file")
        time.sleep(0.5)
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=20) == 130
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
    assert not (stub / "calls").exists()
    assert not (tmp / "runs" / "r2b" / "session" / "status.txt").exists()


def test_ctrl_c_during_a_step_stops_the_session(box):
    tmp, stub, _ = box
    p = _start(box, SLEEP_IN="r2b_s")
    try:
        _wait_for(lambda: (stub / "calls").exists(), "the first step")
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=20) == 130
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
    assert len(_calls(stub)) == 1
    st = _status(tmp)
    assert "r2b_s.log start" in st and "r2b_s.log exit=" not in st
    assert "session interrupted" in st


def test_ctrl_c_during_a_gpu_check_stops_the_session(box):
    tmp, stub, _ = box
    p = _start(box, STUB_GPU_SLEEP="10", STUB_GPU_SLEEP_FROM="2")
    try:
        _wait_for(lambda: (stub / "gpu_checks").exists()
                  and (stub / "gpu_checks").read_text().strip() == "2", "the step's GPU probe")
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=20) == 130
        assert _gone(int((stub / "probe_pid").read_text()))
        assert not (stub / "probe_done").exists()
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
    assert not (stub / "calls").exists()
    st = _status(tmp)
    assert "session interrupted" in st and "STOP" not in st
    r = _run(box)
    assert r.returncode == 0 and len(_calls(stub)) == 4


def test_a_killed_session_leaves_no_lock_behind(box):
    tmp, stub, _ = box
    p = _start(box, STUB_GPU_SLEEP="10", STUB_GPU_SLEEP_FROM="2")
    try:
        _wait_for(lambda: (stub / "gpu_checks").exists()
                  and (stub / "gpu_checks").read_text().strip() == "2", "the step's GPU probe")
        os.killpg(p.pid, signal.SIGKILL)
        p.wait(timeout=20)
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
    r = _run(box)
    assert r.returncode == 0, r.stdout + r.stderr
    assert len(_calls(stub)) == 4


def test_a_probe_left_running_does_not_hold_the_lock(box):
    tmp, stub, _ = box
    p = _start(box, STUB_GPU_SLEEP="10", STUB_GPU_SLEEP_FROM="2")
    try:
        _wait_for(lambda: (stub / "gpu_checks").exists()
                  and (stub / "gpu_checks").read_text().strip() == "2", "the step's GPU probe")
        os.kill(p.pid, signal.SIGKILL)                        # the shell only
        p.wait(timeout=20)
        assert not _gone(int((stub / "probe_pid").read_text()), timeout=0.5)
        r = _run(box)
        assert "already running" not in r.stdout, r.stdout
        assert r.returncode == 0 and len(_calls(stub)) == 4
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _adjudicator():
    import importlib.util

    spec = importlib.util.spec_from_file_location("adjudicate_r2b",
                                                  ROOT / "scripts" / "adjudicate_r2b.py")
    J = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(J)
    return J


def test_ctrl_c_while_the_driver_is_read_writes_no_start_line(box):
    """Ctrl-C while a step's host and driver are read (nvidia-smi hanging)
    stops the session before that step's start line: the status file holds no
    attempt that never ran, and the next run makes one attempt per step."""
    tmp, stub, _ = box
    p = _start(box, STUB_SMI_HANG="30")
    try:
        _wait_for(lambda: (stub / "smi_pid").exists(), "the driver query")
        time.sleep(0.5)
        os.killpg(p.pid, signal.SIGINT)
        assert p.wait(timeout=20) == 130
        assert _gone(int((stub / "smi_pid").read_text()))
    finally:
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
    assert not (stub / "calls").exists()
    st = _status(tmp)
    assert "session interrupted" in st and ".log start" not in st and "STOP" not in st
    r = _run(box)
    assert r.returncode == 0, r.stdout + r.stderr
    att, _, _, dev = _adjudicator().session_deviations(_status(tmp))
    assert att == {k: 1 for k in STEPS} and dev == []


def test_a_driver_query_left_running_does_not_hold_the_lock(box):
    """The session's shell killed while nvidia-smi hangs: the query left
    running does not hold the session's lock, so a restart is not refused."""
    tmp, stub, _ = box
    p = _start(box, STUB_SMI_HANG="30")
    try:
        _wait_for(lambda: (stub / "smi_pid").exists(), "the driver query")
        time.sleep(0.5)
        os.kill(p.pid, signal.SIGKILL)                        # the shell only
        p.wait(timeout=20)
        assert not _gone(int((stub / "smi_pid").read_text()), timeout=0.5)
        r = _run(box)
        assert "already running" not in r.stdout, r.stdout
        assert r.returncode == 0 and len(_calls(stub)) == 4
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def test_a_restart_after_s_finished_without_its_exit_line_is_in_order(box):
    """The session's shell killed while S's step runs on and writes S's
    complete report (as a killed tmux pane leaves it): the restart skips S, its
    gate finds the report complete and the baseline runs; the adjudication
    records S's missing exit line and no order deviation."""
    import fcntl

    tmp, stub, _ = box
    p = _start(box, SLEEP_IN="r2b_s", SLEEP_SECS="3")
    try:
        _wait_for(lambda: (stub / "step_pid").exists(), "S's step")
        os.kill(p.pid, signal.SIGKILL)                        # the shell only
        p.wait(timeout=20)
        _wait_for(lambda: (tmp / "runs" / "r2b" / "r2b_s" / "report.json").exists(),
                  "S's report from the step left running")
        assert _gone(int((stub / "step_pid").read_text()), timeout=20)
        with open(tmp / "runs" / "r2b" / "session" / ".lock", "a") as lk:   # the lock freed
            _wait_for(lambda: _try_lock(lk, fcntl), "the session's lock to be free")
            fcntl.flock(lk, fcntl.LOCK_UN)
    finally:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    r = _run(box)
    assert r.returncode == 0, r.stdout + r.stderr
    st = _status(tmp)
    assert "r2b_s: report exists, skipped" in st and "r2b_b: r2b_s has a complete report" in st
    att, ends, _, dev = _adjudicator().session_deviations(st)
    assert att == {k: 1 for k in STEPS} and ends["r2b_s"] is None
    assert dev == ["r2b_s: its last attempt has no exit line (interrupted)"]


def _try_lock(f, fcntl):
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except BlockingIOError:
        return False
