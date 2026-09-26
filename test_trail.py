#!/usr/bin/env python3
"""Run: python3 test_trail.py   (no pytest, no deps)"""
import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
BIN = HERE / "bin" / "trail"

spec = importlib.util.spec_from_loader("trail", importlib.machinery.SourceFileLoader("trail", str(BIN)))
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


def test_yaml():
    d = t.parse_yaml("# c\na: 1   # trailing\nb: 'two'\nlinks:\n  - x.cs:1\n  - y.md\nempty:\n")
    assert d["a"] == "1", d
    assert d["b"] == "two", d
    assert d["links"] == ["x.cs:1", "y.md"], d
    assert d["empty"] == [], d


def test_title_is_always_quoted():
    """A colon in an unquoted scalar invalidates the whole block. Two of the five
    files in the first real ledger were unreadable to every other tool this way."""
    assert t.yaml_quote('Report: pivot') == '"Report: pivot"'
    src = '---\nid: a\ntitle: a\n---\n# a\n'
    out = t.set_field(src, "title", t.yaml_quote('Report: pivot "matrix"'))
    assert t.parse_fm(out)["title"] == 'Report: pivot "matrix"', t.parse_fm(out)


def test_set_field_preserves_unknown():
    src = "---\nid: a\nstatus: active\nmine: keep-me\nlinks:\n  - x\n---\n# a\n"
    out = t.set_field(src, "status", "done")
    assert "status: done" in out
    assert "mine: keep-me" in out
    assert "  - x" in out
    assert t.parse_fm(out)["id"] == "a"
    # a missing key is appended, not dropped
    out2 = t.set_field(src, "color", "red")
    assert "color: red" in out2 and "mine: keep-me" in out2


def test_sections():
    src = "---\nid: a\n---\n# a\n\n## Decision Log\n<!-- hint -->\n\n## Status\nold\n"
    out = t.append_section(src, "Decision Log", "- 2026-01-01 · x")
    assert "- 2026-01-01 · x" in out
    assert "<!-- hint -->" not in t.get_section(out, "Decision Log")
    assert t.get_section(out, "Status") == "old"
    out = t.append_section(out, "Decision Log", "- 2026-01-02 · y")
    assert t.get_section(out, "Decision Log").count("\n") == 1
    out = t.set_section(out, "Status", "new note")
    assert t.get_section(out, "Status") == "new note"
    assert "- 2026-01-02 · y" in out  # replacing one section must not eat another


def test_work_order_is_status_then_id_not_mtime():
    """The file you touched last is not the work that comes first. Order between
    related tasks lives in the slug prefix, so sorting by id is enough."""
    def task(i, status="open"):
        return {"id": i, "status": status}
    ts = [task("auth-3-migration"), task("auth-1-provider"), task("auth-2-session")]
    assert [x["id"] for x in sorted(ts, key=t.work_order(ts))] == [
        "auth-1-provider", "auth-2-session", "auth-3-migration"]
    # status still wins over the slug
    ts = [task("a-1", status="blocked"), task("b-2")]
    assert [x["id"] for x in sorted(ts, key=t.work_order(ts))] == ["b-2", "a-1"]


def test_slugify():
    assert t.slugify("Push Notification  Deeplink!") == "push-notification-deeplink"


def test_own_skill_copy_is_in_sync():
    """This repo dogfoods trail, so it holds two copies of each SKILL.md.
    They must not drift; the source of truth is skills/<name>/."""
    for name in t.SKILLS:
        src = HERE / "skills" / name / "SKILL.md"
        dest = HERE / ".claude" / "skills" / name / "SKILL.md"
        if dest.exists():
            assert src.read_text("utf-8") == dest.read_text("utf-8"), \
                "%s SKILL.md kopyalari ayrismis: 'trail init --force' ile tazele" % name


def test_missing_scaffold_is_nudged_not_broken():
    """A repo initialised by an older trail keeps working; status says what to run."""
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / ".trail" / "tasks").mkdir(parents=True)
        cfg = t.load_config(tmp)
        assert t.missing_scaffold(tmp, cfg) == [cfg["backlog"]]
        (tmp / cfg["backlog"]).write_text("# Backlog\n", "utf-8")
        assert t.missing_scaffold(tmp, cfg) == []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(cwd, *args, **kw):
    r = subprocess.run([sys.executable, str(BIN)] + list(args),
                       cwd=str(cwd), capture_output=True, text=True, env=kw.get("env"))
    assert r.returncode == kw.get("code", 0), (args, r.returncode, r.stdout, r.stderr)
    return r.stdout


def run_full(cwd, *args, **kw):
    """run() with the whole result and an `input=` pipe. A refusal is only useful
    if it says what to do instead, so the message on stderr is the thing under
    test, not just the exit code."""
    r = subprocess.run([sys.executable, str(BIN)] + list(args), cwd=str(cwd),
                       capture_output=True, text=True,
                       input=kw.get("input"), env=kw.get("env"))
    assert r.returncode == kw.get("code", 0), (args, r.returncode, r.stdout, r.stderr)
    return r


def test_a_new_session_can_resume_from_the_reading_path_alone():
    """The product promise, not the CLI: a session that runs only what the skill
    tells it to run must land on the right work, inside the right boundary, knowing
    that earlier findings exist. Both bugs this test was written for - a status that
    hid the scope and a resume command that did not exist - survived nine passing
    CLI tests."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        # a plan run parks its tasks; nothing is active afterwards
        run(tmp, "start", "rapor-2-tablo", "T2", "--group", "rapor", "--status", "open")
        run(tmp, "start", "rapor-3-sayfa", "T1", "--group", "rapor", "--status", "open")
        for section, body in (("goal", "Tablo gercek veriyle ciziliyor.\n"),
                              ("scope", "- Pivot MODULE DISI, rapor-5'e ait.\n"),
                              ("steps", "- [x] kolon cozumu\n- [ ] sayfa hata yolu\n"),
                              ("questions", "Cursor son satiri neden dusuruyor?\n")):
            r = subprocess.run([sys.executable, str(BIN), "write", section,
                                "--task", "rapor-2-tablo"],
                               cwd=str(tmp), input=body, capture_output=True, text=True)
            assert r.returncode == 0, r.stderr
        run(tmp, "note", "olcum: 12 widget 9.6sn cold", "--task", "rapor-2-tablo")
        run(tmp, "log", "cursor sayfalama", "--why", "sunucu 500'de kesiyor",
            "--dropped", "istemci tarafi sayfalama", "--task", "rapor-2-tablo")

        # --- a new session starts here, running only what the skill prescribes ---
        out = run(tmp, "resume", "rapor-2-tablo")
        assert "open -> active" in out                      # it was parked
        assert "Tablo gercek veriyle" in out                # what is this
        assert "[ ] sayfa hata yolu" in out                 # what is next
        assert "Pivot MODULE DISI" in out                   # the boundary, not lost
        assert "Notes 1" in out and "Open Questions 1" in out   # findings are visible
        assert "cursor sayfalama" in out                    # last decisions

        # and the flow completes: writers need no --task once something is resumed
        run(tmp, "note", "devam")
        run(tmp, "handoff", "kaldigim yer")
        # blocked is still the task you are on
        run(tmp, "set", "status", "blocked")
        run(tmp, "log", "engel")
        assert "engel" in (tmp / ".trail/tasks/rapor-2-tablo.md").read_text("utf-8")
        # and a task you are not on can still be inspected
        assert "rapor-3-sayfa" in run(tmp, "status", "--task", "rapor-3-sayfa")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_concurrent_writes_do_not_lose_entries():
    """The one absolute promise is that the decision log only grows. Before the
    lock, fifty parallel writes landed forty - and all fifty reported success."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "x")
        procs = [subprocess.Popen([sys.executable, str(BIN), "log", "karar-%d" % i],
                                  cwd=str(tmp), stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL) for i in range(20)]
        assert all(p.wait() == 0 for p in procs)
        text = (tmp / ".trail/tasks/x.md").read_text("utf-8")
        assert len(t.decision_entries(text)) == 20, len(t.decision_entries(text))
        assert not list((tmp / ".trail/tasks").glob("*.tmp"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


RACE_CHILD = """
import importlib.machinery, importlib.util, pathlib, sys, time
loader = importlib.machinery.SourceFileLoader("trail", %r)
spec = importlib.util.spec_from_loader("trail", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
orig = pathlib.Path.read_text
def slow(self, *a, **k):          # stall between the template read and the write
    if self.name == "_template.md":
        time.sleep(2)
    return orig(self, *a, **k)
pathlib.Path.read_text = slow
sys.exit(m.main(["start", "x"]))
"""


def test_start_never_overwrites_an_existing_task():
    """`start` used to check exists() and write in two steps. In the gap a second
    process created the task and had a decision logged against it; the first
    process's write then erased the decision - and all three commands exited 0."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        child = subprocess.Popen([sys.executable, "-c", RACE_CHILD % str(BIN)],
                                 cwd=str(tmp), stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        time.sleep(0.5)                       # child is now stalled mid-start
        run(tmp, "start", "x")
        run(tmp, "log", "karar", "--why", "neden", "--dropped", "alternatif")
        assert child.wait() == 1               # the loser fails, loudly
        text = (tmp / ".trail/tasks/x.md").read_text("utf-8")
        assert len(t.decision_entries(text)) == 1, text
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


VISIBILITY_CHILD = ("""
import builtins, importlib.machinery, importlib.util, os, sys, time
loader = importlib.machinery.SourceFileLoader("trail", %r)
spec = importlib.util.spec_from_loader("trail", loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
# stall at whichever call makes the task visible, so the parent gets a full window
orig_open, orig_link = builtins.open, os.link
def slow_open(f, mode="r", *a, **k):
    fh = orig_open(f, mode, *a, **k)
    if "x" in mode:
        time.sleep(2)
    return fh
def slow_link(src, dst, *a, **k):
    orig_link(src, dst, *a, **k)
    time.sleep(2)
builtins.open, os.link = slow_open, slow_link
sys.exit(m.main(["start", "same"]))
""" % str(BIN))


def test_a_task_is_never_visible_half_written():
    """`start` wrote the template into a file that was already visible and empty.
    A `log` that landed in that window replaced the file, start's own write went to
    the unlinked inode, and the task that survived had no frontmatter and no
    sections - `handoff` then failed with `no '## Status' section`."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        dest = tmp / ".trail/tasks/same.md"
        child = subprocess.Popen([sys.executable, "-c", VISIBILITY_CHILD],
                                 cwd=str(tmp), stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
        deadline = time.time() + 10
        while not dest.exists() and time.time() < deadline:
            time.sleep(0.02)
        assert dest.exists(), "start never created the task"
        run(tmp, "log", "karar", "--task", "same", "--why", "neden",
            "--dropped", "alternatif")
        assert child.wait() == 0
        text = dest.read_text("utf-8")
        assert t.parse_fm(text).get("id") == "same", text   # frontmatter survived
        assert t.section_bounds(text, "Status"), text       # and so did the sections
        assert len(t.decision_entries(text)) == 1, text     # the decision too
        assert not list((tmp / ".trail/tasks").glob("*.tmp"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_search_returns_the_whole_decision_entry():
    """`rg` matches a line; this format's unit is an entry. A hit inside a
    `dropped:` body has to bring the decision it belongs to back with it, or the
    answer to "have we already ruled this out?" is a fragment with no subject."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "auth")
        run(tmp, "log", "JWT secildi", "--why", "stateless",
            "--dropped", "imzali cerez - oturum tablosu gerekiyor")
        run(tmp, "note", "olcum: dogrulama 40ms")
        out = run(tmp, "search", "oturum tablosu")
        assert "JWT secildi" in out, out            # the title came with the match
        assert "imzali cerez" in out, out
        assert "Decision Log" in out, out
        assert "olcum" not in out, out              # and nothing else did
        assert "Notes" in run(tmp, "search", "40ms")
        assert "no match" in run(tmp, "search", "boyle-bir-sey-yok")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_backlog_tags_are_exact_and_never_guessed():
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "auth-1")
        bl = tmp / ".trail/backlog.md"
        bl.write_text(bl.read_text("utf-8") + "- [x] baska is #auth-1-extra\n", "utf-8")
        out = run(tmp, "done")
        assert "#auth-1-extra" not in out          # a longer slug is a different task
        assert "backlog:" not in out               # so the close sees no tagged line
        assert "baska is #auth-1-extra" in bl.read_text("utf-8")   # and nothing is deleted
        # two things in progress: refuse rather than tag by guess
        run(tmp, "start", "a")
        run(tmp, "start", "b")
        run(tmp, "backlog", "belirsiz", code=1)
        # nothing in progress at all is fine - the line lands untagged
        run(tmp, "set", "status", "open", "--task", "a")
        run(tmp, "set", "status", "open", "--task", "b")
        run(tmp, "backlog", "sahipsiz")
        assert "- [ ] sahipsiz\n" in bl.read_text("utf-8")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_find_root_stops_at_the_repo_boundary():
    """A nested checkout must not reach the outer repo's ledger."""
    tmp = Path(tempfile.mkdtemp())
    try:
        (tmp / ".git").mkdir()
        (tmp / ".trail" / "tasks").mkdir(parents=True)
        inner = tmp / "vendor" / "lib"
        (inner / ".git").mkdir(parents=True)
        assert t.find_root(inner) == inner.resolve()
        assert t.find_root(tmp) == tmp.resolve()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_end_to_end():
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        assert (tmp / ".trail/tasks").is_dir()
        # trail no longer plants a decision record at the repo root: it does not
        # manage repo-lifetime decisions, and the log is permanent where it is
        assert not (tmp / "DECISIONS.md").exists()
        # the sink must be visible before first use, or nobody knows to empty it
        assert (tmp / ".trail/backlog.md").is_file()
        # no agent markers in a bare repo -> claude is the fallback
        assert (tmp / ".claude/skills/trail/SKILL.md").is_file()
        assert (tmp / ".claude/skills/trail-plan/SKILL.md").is_file()   # both entry points
        assert not (tmp / ".agents").exists()

        tmp2 = Path(tempfile.mkdtemp())
        try:
            subprocess.run(["git", "init", "-q"], cwd=str(tmp2), check=True)
            run(tmp2, "init")
            run(tmp2, "start", "x")
            run(tmp2, "log", "keep me")
            run(tmp2, "done")
            # the log stays in the task file; nothing is copied anywhere
            assert "keep me" in (tmp2 / ".trail/tasks/x.md").read_text("utf-8")
            assert not (tmp2 / "DECISIONS.md").exists()
            # a hand-edited config.yml is user content: no drift warning, no clobber
            conf = tmp2 / ".trail/config.yml"
            conf.write_text(conf.read_text("utf-8") + "stale_days: 3\n", "utf-8")
            assert "differs" not in run(tmp2, "init", "--force")
            assert "stale_days: 3" in conf.read_text("utf-8")
        finally:
            shutil.rmtree(tmp2, ignore_errors=True)

        # init never clobbers a drifted copy; it warns, and --force refreshes
        skill = tmp / ".claude/skills/trail/SKILL.md"
        skill.write_text("stale\n", "utf-8")
        assert "differs" in run(tmp, "init")
        assert skill.read_text("utf-8") == "stale\n"
        run(tmp, "init", "--force")
        assert skill.read_text("utf-8").startswith("---")

        # an existing .codex marker routes the skill to the shared .agents path
        (tmp / ".codex").mkdir()
        run(tmp, "init")
        assert (tmp / ".agents/skills/trail/SKILL.md").is_file()
        # explicit override still works
        run(tmp, "init", "--agent", "gemini")

        run(tmp, "start", "Deep Link", "T2", "--title", "deep link")
        f = tmp / ".trail/tasks/deep-link.md"
        assert f.is_file()
        fm = t.parse_fm(f.read_text("utf-8"))
        assert fm["level"] == "T2" and fm["status"] == "active" and fm["id"] == "deep-link"
        assert "{{" not in f.read_text("utf-8")

        run(tmp, "log", "use applinks", "--why", "no aasa host", "--dropped", "universal links")
        # the entry is scannable: a title line, then the reasons indented under it
        assert "  - **dropped:** universal links" in f.read_text("utf-8")
        assert len(t.decision_entries(f.read_text("utf-8"))) == 1

        run(tmp, "handoff", "parser done")
        assert t.get_section(f.read_text("utf-8"), "Status") == "parser done"

        out = json.loads(run(tmp, "ls", "--json"))
        assert len(out) == 1 and out[0]["level"] == "T2"

        st = run(tmp, "status", "--inject")
        assert "===BEGIN TRAIL===" in st and "use applinks" in st

        # duplicate slug is refused
        run(tmp, "start", "deep-link", code=1)

        run(tmp, "done")
        # closing does not move the file: a closed task is the one that says what
        # was verified and what was left, and archiving hid it from every reader
        assert f.is_file()
        assert not (tmp / ".trail/archive/deep-link.md").exists()
        assert t.parse_fm(f.read_text("utf-8"))["status"] == "done"
        assert "**dropped:** universal links" in f.read_text("utf-8")
        assert "deep-link" not in run(tmp, "ls")          # done is out of the way
        assert "deep-link" in run(tmp, "ls", "--all")     # but never gone

        # no active task left -> log must fail loudly, not silently pick one
        run(tmp, "log", "x", code=1)

        env = dict(os.environ, TRAIL_DISABLED="1")
        assert run(tmp, "log", "x", env=env) == ""

        # bulk planning parks tasks as open so `trail status` stays meaningful.
        # T0 is refused a file on purpose; the message has to say where it goes.
        r = subprocess.run([sys.executable, str(BIN), "start", "small", "T0"],
                           cwd=str(tmp), capture_output=True, text=True)
        assert r.returncode == 1 and "backlog" in r.stderr, r.stderr
        run(tmp, "start", "planned-item", "--status", "open")
        f2 = tmp / ".trail/tasks/planned-item.md"
        assert t.parse_fm(f2.read_text("utf-8"))["status"] == "open"
        run(tmp, "log", "x", code=1)  # open != active, still no target

        # every frontmatter field has a writer; hand-editing is never required
        run(tmp, "set", "status", "blocked", "--task", "planned-item")
        assert t.parse_fm(f2.read_text("utf-8"))["status"] == "blocked"
        run(tmp, "set", "level", "T2", "--task", "planned-item")
        assert t.parse_fm(f2.read_text("utf-8"))["level"] == "T2"
        run(tmp, "set", "status", "active", "--task", "planned-item")
        run(tmp, "log", "now resolvable")  # single active task -> no --task needed
        assert "now resolvable" in f2.read_text("utf-8")
        run(tmp, "set", "status", "done", "--task", "planned-item", code=1)  # use `trail done`
        # links: the field the spec documents, with the writer it was missing
        run(tmp, "link", "docs/plan.md", "src/A.cs:12", "--task", "planned-item")
        assert t.parse_fm(f2.read_text("utf-8"))["links"] == ["docs/plan.md", "src/A.cs:12"]
        run(tmp, "link", "docs/plan.md", "--task", "planned-item")  # idempotent
        assert t.parse_fm(f2.read_text("utf-8"))["links"] == ["docs/plan.md", "src/A.cs:12"]

        # backlog is a sink: a line, no lifecycle, and status shows only the count
        run(tmp, "backlog", "android smoke", "ask backend 3 questions")
        bl = tmp / ".trail/backlog.md"
        assert bl.read_text("utf-8").count("\n- [ ] ") == 2
        assert bl.read_text("utf-8").count("#planned-item") == 2   # tagged with the active task
        assert "backlog: 2 open items" in run(tmp, "status")
        run(tmp, "backlog", "unrelated", "--untagged")
        assert "- [ ] unrelated\n" in bl.read_text("utf-8")

        # ## Notes: free-form, dated, append-only - the section the CLI could not
        # write to, which is why measurements ended up in the backlog instead
        run(tmp, "note", "12 widgets, 9.6s cold")
        assert "12 widgets, 9.6s cold" in t.get_section(f2.read_text("utf-8"), "Notes")

        # group: the relation field, queryable from outside; no index file
        run(tmp, "set", "group", "Report Module", "--task", "planned-item")
        assert t.parse_fm(f2.read_text("utf-8"))["group"] == "report-module"
        assert "report-module" in run(tmp, "ls")

        # readers narrow to the group being worked on: a forty-task board stops
        # compressing context and starts being a project-management surface
        run(tmp, "start", "other-1", "--group", "other", "--status", "open")
        assert "group report-module" in run(tmp, "ls")
        assert "other-1" not in run(tmp, "ls")
        assert "other-1" in run(tmp, "ls", "--all")
        assert "other-1" in run(tmp, "ls", "--group", "other")
        assert "other-1" in run(tmp, "board", "--group", "other")
        # an explicit filter asks a global question; narrowing it answers another one
        assert "other-1" in run(tmp, "ls", "--status", "open")

        # two active tasks: every writer already refuses, and status now says so
        run(tmp, "set", "status", "active", "--task", "other-1")
        assert "2 tasks are active" in run(tmp, "status")
        run(tmp, "log", "ambiguous", code=1)
        run(tmp, "set", "status", "open", "--task", "other-1")

        # write replaces a section, and creates one the template lacks
        f2.write_text(f2.read_text("utf-8"), "utf-8")
        r = subprocess.run([sys.executable, str(BIN), "write", "goal", "--task", "planned-item"],
                           cwd=str(tmp), input="tek cumle\n", capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert t.get_section(f2.read_text("utf-8"), "Goal") == "tek cumle"
        r = subprocess.run([sys.executable, str(BIN), "write", "steps", "--task", "planned-item"],
                           cwd=str(tmp), input="adim 1\nadim 2\n", capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert t.get_section(f2.read_text("utf-8"), "Steps") == "adim 1\nadim 2"

        # step progress: [x] counts, [-] leaves the denominator, [/] is not done yet
        r = subprocess.run([sys.executable, str(BIN), "write", "steps", "--task", "planned-item"],
                           cwd=str(tmp),
                           input="- [x] one [completion:: 2026-09-12]\n- [/] two\n- [ ] three\n- [-] four\n",
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert t.step_progress(f2.read_text("utf-8")) == (1, 3)
        assert t.steps_view(t.parse_steps(f2.read_text("utf-8")))["next"].text == "two"
        assert "1/3" in run(tmp, "ls")

        # closing reports the backlog around the task and changes nothing in it
        before = bl.read_text("utf-8")
        bl.write_text(before
                      + "- [x] finished thing #planned-item\n"
                      + "- [ ] left open on purpose #planned-item\n", "utf-8")
        out = run(tmp, "done", "--task", "planned-item")
        assert "finished thing" in bl.read_text("utf-8")        # nothing deleted
        assert "left open on purpose" in bl.read_text("utf-8")
        assert "#planned-item -> 3 open, 1 done" in out   # two tagged earlier
        assert "still open: - [ ] left open on purpose" in out
        # an empty body is a mistake, not an erasure
        r = subprocess.run([sys.executable, str(BIN), "write", "goal", "--task", "planned-item"],
                           cwd=str(tmp), input="  \n", capture_output=True, text=True)
        assert r.returncode == 1
        assert t.get_section(f2.read_text("utf-8"), "Goal") == "tek cumle"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# the step line: the only Markdown trail parses instead of passing through
# --------------------------------------------------------------------------

def test_step_line_round_trip():
    """The line is the format. A line the CLI wrote has to survive parse -> render
    byte for byte, and everything trail does not own - a wikilink, a foreign inline
    field, an indent - has to come back untouched, or hand-edited steps rot the
    moment a command runs."""
    # inline code is opaque, like a fenced block: an item about the format mentions
    # `[completion:: YYYY-MM-DD]` in backticks, and that must not read as a field
    it = t.parse_step_line("- [x] rule: `[completion:: YYYY-MM-DD]` on [x] [id:: a-bbbb] [completion:: 2026-09-12]")
    assert it.fields == {"id": "a-bbbb", "completion": "2026-09-12"}, it.fields
    assert it.dupes == [] and it.text == "rule: `[completion:: YYYY-MM-DD]` on [x]", it
    assert it.render() == "- [x] rule: `[completion:: YYYY-MM-DD]` on [x] [id:: a-bbbb] [completion:: 2026-09-12]"

    line = "- [x] classify ErrorCode [id:: ap-k4m2] [completion:: 2026-09-17]"
    assert t.parse_step_line(line, 1).render() == line

    assert t.parse_step_line("- [X] upper", 1).state == "x"       # `X` reads as `x`

    # trail's fields are read from anywhere on the line and written back after the
    # text, keeping the order they already had
    it = t.parse_step_line(
        "- [ ] before [completion:: 2026-09-17] middle [id:: ab-1234] after", 1)
    assert it.text == "before middle after", it.text
    assert list(it.fields) == ["completion", "id"], it.fields
    assert it.render() == "- [ ] before middle after [completion:: 2026-09-17] [id:: ab-1234]"

    # not trail's: text, byte for byte
    src = "- [/] see [[Design Doc]] and [priority:: high] rest [id:: ab-1234]"
    it = t.parse_step_line(src, 1)
    assert it.text == "see [[Design Doc]] and [priority:: high] rest", it.text
    assert it.render() == src

    assert t.parse_step_line("* [ ] x", 1) is None              # only `- ` bullets
    assert t.parse_step_line("- [x](http://u) x", 1) is None    # a link, not a box
    sub = t.parse_step_line("  - [ ] sub", 1)
    assert sub is not None and sub.indent == "  ", sub
    assert sub.render() == "  - [ ] sub"

    # a line carrying one of trail's fields twice cannot be rendered without
    # losing one of them, so every mutation refuses it by name
    dup = t.parse_step_line("- [ ] x [id:: a-aaaa] [id:: b-bbbb]", 7)
    assert dup.dupes == ["id"], dup.dupes
    try:
        t.touch(dup)
        assert False, "touch rewrote a line carrying [id:: ] twice"
    except t.TrailError as e:
        assert "twice" in str(e) and "line 7" in str(e), e


HAND_EDITED_STEPS = (
    '---\nid: demo\ntitle: "Demo"\nlevel: T2\nstatus: active\n---\n'
    "# demo\n"
    "\n## Steps\n"
    "<!-- `- [ ]` todo · `- [x]` verified -->\n"
    "### A. parser\n"
    "- [ ] alfa [id:: d-aaaa]\n"
    "  parser notu, madde degil   \n"
    "  - [ ] nested [id:: d-bbbb]\n"
    "- [/] beta [priority:: high] [[Design]] [id:: d-cccc]\n"
    "\n"
    "```\n"
    "- [ ] not an item\n"
    "```\n"
    "\n## Status\n"
    "kaldigim yer\n"
)


def test_hand_edited_steps_survive_a_mutation():
    """Rebuilding `## Steps` from the parsed items would drop the template comment,
    the `###` sub-heading and the note under an item, and normalise every line it
    touched. A mutation is allowed to change exactly the one line it changed."""
    assert [it.text for it in t.parse_steps(HAND_EDITED_STEPS)] == [
        "alfa", "nested", "beta [priority:: high] [[Design]]"]   # the fence is opaque
    assert len(t.parse_steps(HAND_EDITED_STEPS.replace("```", "~~~"))) == 3   # ~~~ too

    new = t.mutate_steps(HAND_EDITED_STEPS,
                        lambda items: t.transition(items[0], "x", "2026-09-17"))
    old_lines, new_lines = HAND_EDITED_STEPS.splitlines(), new.splitlines()
    assert len(old_lines) == len(new_lines), (len(old_lines), len(new_lines))
    diff = [i for i, (o, n) in enumerate(zip(old_lines, new_lines)) if o != n]
    assert len(diff) == 1, [(old_lines[i], new_lines[i]) for i in diff]
    assert old_lines[diff[0]] == "- [ ] alfa [id:: d-aaaa]"
    assert new_lines[diff[0]] == "- [x] alfa [id:: d-aaaa] [completion:: 2026-09-17]"
    assert "- [ ] not an item" in new                    # never parsed, never changed
    assert "  parser notu, madde degil   " in new        # prose and its trailing space
    assert "<!-- `- [ ]` todo · `- [x]` verified -->" in new
    assert "### A. parser" in new
    # nothing dirty -> the file is returned, not rewritten
    assert t.mutate_steps(HAND_EDITED_STEPS, lambda items: None) == HAND_EDITED_STEPS


class _FixedRng:
    """`random.choice` is called once per id character; a fixed cycle makes the
    collision path testable without seeding the global generator."""

    def __init__(self, seq):
        self.seq, self.i = list(seq), 0

    def choice(self, alphabet):
        ch = self.seq[self.i % len(self.seq)]
        self.i += 1
        return ch


def test_item_ids():
    """An id is written once and never changes, so everything about making one has
    to be settled before it lands: the prefix, the Turkish slug it comes from, the
    collision retry, and the rule that an id already on the line is never touched."""
    assert t.id_prefix("auth-provider") == "ap"
    assert t.id_prefix("user-1-profile") == "u1p"
    # ids come from the slug, and the slug transliterates before lowercasing:
    # 'İ'.lower() is 'i' plus a combining dot, and 'ı' has nothing to decompose
    assert t.slugify("Görsel Doğrulama") == "gorsel-dogrulama"
    assert t.slugify("İSTANBUL ışık") == "istanbul-isik"

    assert t.new_item_id("ap", set(), _FixedRng("aaaabbbb")) == "ap-aaaa"
    assert t.new_item_id("ap", {"ap-aaaa"}, _FixedRng("aaaabbbb")) == "ap-bbbb"

    items = [t.parse_step_line("- [ ] bir [id:: keep-me]", 1),
             t.parse_step_line("- [ ] iki", 2)]
    given = t.assign_ids(items, "ap", _FixedRng("cccc"))
    assert items[0].fields["id"] == "keep-me" and not items[0].dirty   # malformed, kept
    assert [it.id for it in given] == ["ap-cccc"] and items[1].dirty

    body, n = t.with_step_ids("- [ ] bir [id:: ap-k4m2]\n- [ ] iki", "ap")
    assert n == 1
    lines = body.splitlines()
    assert lines[0] == "- [ ] bir [id:: ap-k4m2]", lines        # only id-less lines move
    new_id = t.parse_step_line(lines[1], 2).id
    assert new_id.startswith("ap-") and t.ITEM_ID_RE.match(new_id), new_id

    try:
        t.with_step_ids("- [ ] bir [id:: ap-k4m2]\n- [ ] iki [id:: ap-k4m2]", "ap")
        assert False, "a piped body with two identical ids was accepted"
    except t.TrailError as e:
        assert "duplicate step id ap-k4m2" in str(e), e


def _item(line):
    return t.parse_step_line(line, 1)


def test_transitions_and_blocked_rules():
    """The box is progress; blocked is a separate fact about the same line. The
    one rule that ties them is that a blocked item cannot be resolved, because
    clearing someone's block as a side effect of `check` loses why it was there."""
    it = _item("- [ ] adim [id:: d-aaaa]")
    t.transition(it, "x", "2026-09-17")
    assert it.state == "x" and it.fields["completion"] == "2026-09-17" and it.dirty

    for out_state in ("/", " "):        # the date is cleared on the way out of [x]
        it = _item("- [x] adim [id:: d-aaaa] [completion:: 2026-09-17]")
        t.transition(it, out_state, "2026-09-18")
        assert it.state == out_state and "completion" not in it.fields, it.fields

    it = _item("- [ ] adim [id:: d-aaaa]")
    t.transition(it, "-", "2026-09-17", "kapsam disi")
    assert it.text == "adim — kapsam disi", it.text     # the reason is prose, not a field
    assert "completion" not in it.fields

    for state in ("x", "-"):
        it = _item("- [/] adim [id:: d-aaaa] [blocked:: 2026-09-15] [blocked-reason:: ses yok]")
        try:
            t.transition(it, state, "2026-09-17")
            assert False, "a blocked item was resolved to [%s]" % state
        except t.TrailError as e:
            assert "unblock it first" in str(e), e
        assert it.state == "/" and not it.dirty
        assert list(it.fields) == ["id", "blocked", "blocked-reason"], it.fields

    it = _item("- [ ] adim [id:: d-aaaa] [blocked:: 2026-09-15] [blocked-reason:: ses yok]")
    t.transition(it, "/", "2026-09-17")                 # [/] + blocked is legal
    assert it.state == "/" and it.blocked
    it = _item("- [/] adim [id:: d-aaaa] [blocked:: 2026-09-15] [blocked-reason:: ses yok]")
    t.transition(it, " ", "2026-09-17")
    assert it.state == " " and it.blocked

    for line in ("- [x] adim [id:: d-aaaa] [completion:: 2026-09-17]",
                 "- [-] adim [id:: d-aaaa]"):
        it = _item(line)
        try:
            t.set_blocked(it, "2026-09-17", "sebep")
            assert False, "a resolved item was blocked: %s" % line
        except t.TrailError as e:
            assert "only an unfinished item can be blocked" in str(e), e
        assert not it.blocked and not it.dirty

    it = _item("- [ ] adim [id:: d-aaaa]")
    t.set_blocked(it, "2026-09-15", "ses dosyasi yok")
    try:
        t.set_blocked(it, "2026-09-17", "baska sebep")
        assert False, "block silently replaced an existing block"
    except t.TrailError as e:
        assert "already blocked" in str(e) and "trail unblock" in str(e), e
    assert it.fields["blocked"] == "2026-09-15"
    assert it.fields["blocked-reason"] == "ses dosyasi yok"

    it = _item("- [/] adim [priority:: high] [id:: d-aaaa] "
               "[blocked:: 2026-09-15] [blocked-reason:: ses yok]")
    assert t.clear_blocked(it) == "2026-09-15: ses yok"
    assert list(it.fields) == ["id"], it.fields         # exactly the two, nothing else
    assert it.render() == "- [/] adim [priority:: high] [id:: d-aaaa]"
    try:
        t.clear_blocked(it)
        assert False, "unblocking an unblocked item was not a no-op"
    except t.Unchanged as e:
        assert "not blocked" in str(e), e

    it = _item("- [x] adim [id:: d-aaaa] [completion:: 2026-09-10]")
    try:
        t.transition(it, "x", "2026-09-17")
        assert False, "re-checking re-dated a verified item"
    except t.Unchanged as e:
        assert "already [x]" in str(e) and "2026-09-10" in str(e), e
    assert it.fields["completion"] == "2026-09-10" and not it.dirty

    it = _item("- [-] adim — eski sebep [id:: d-aaaa]")
    try:
        t.transition(it, "-", "2026-09-17", "yeni sebep")
        assert False, "cancel overwrote a cancelled item's reason"
    except t.TrailError as e:
        assert "already cancelled" in str(e), e
    try:
        t.transition(it, "-", "2026-09-17")      # no reason: a no-op, not an error
        assert False, "cancelling a cancelled item was not a no-op"
    except t.Unchanged as e:
        assert "already [-]" in str(e), e
    assert it.text == "adim — eski sebep" and not it.dirty

    for bad in ("", "   ", "iki\nsatir", "koseli ] parantez"):
        try:
            t.clean_reason(bad, "block")
            assert False, "clean_reason accepted %r" % bad
        except t.TrailError:
            pass
    assert t.clean_reason("  ses dosyasi yok  ", "block") == "ses dosyasi yok"


def test_resolve_item():
    """Picking one of several matches would be a guess dressed as a command, so
    the refusal has to carry the steps with it - an agent that cannot see the ids
    cannot name the item on the second try."""
    items = [_item("- [ ] Değer seti hazirla [id:: dg-k4m2]"),
             _item("- [x] eski dg-k4m2 notunu temizle [id:: dg-x7q9]"),
             _item("- [-] seti iptal et [id:: dg-9zzz]")]

    # an exact id wins even when the id string is also text on another line
    assert t.resolve_item(items, "dg-k4m2") is items[0]
    assert t.resolve_item(items, "DG-K4M2") is items[0]
    # substring, case-insensitive, Turkish included
    assert t.resolve_item(items, "değer") is items[0]
    assert t.resolve_item(items, "DEĞER") is items[0]
    # resolved items are candidates too; filtering them would be guessing
    assert t.resolve_item(items, "temizle") is items[1]
    assert t.resolve_item(items, "iptal") is items[2]

    try:
        t.resolve_item(items, "yokbunyok")
        assert False, "a query that matches nothing resolved to an item"
    except t.TrailError as e:
        assert "no step matches 'yokbunyok'" in str(e), e
        for line in ("  [dg-k4m2] [ ] Değer seti hazirla",
                     "  [dg-x7q9] [x] eski dg-k4m2 notunu temizle",
                     "  [dg-9zzz] [-] seti iptal et"):
            assert line in str(e), (line, str(e))

    try:
        t.resolve_item(items, "seti")
        assert False, "an ambiguous query resolved to one item"
    except t.TrailError as e:
        assert "2 steps match 'seti' - say which, by id:" in str(e), e
        assert "[dg-k4m2]" in str(e) and "[dg-9zzz]" in str(e), e
        assert "dg-x7q9" not in str(e), e         # only the candidates are listed


def _view(*lines):
    return t.steps_view([t.parse_step_line(l, i + 1) for i, l in enumerate(lines)])


BLOCKED = "[blocked:: 2026-09-15] [blocked-reason:: ses yok]"


def test_steps_view_selection():
    """What `status` answers: what is next, what can run beside it, what is stuck.
    A blocked item is never offered as work, and `[/]` next does not mean the item
    is done - the `[ ]` after it is parallel work, not the successor."""
    v = _view("- [ ] bir [id:: a-aaaa] " + BLOCKED, "- [ ] iki [id:: a-bbbb]")
    assert v["next"].text == "iki"                      # blocked is skipped for Next
    assert [it.text for it in v["blocked"]] == ["bir"]

    v = _view("- [/] bir [id:: a-aaaa]",
              "- [ ] iki [id:: a-bbbb] " + BLOCKED,
              "- [ ] uc [id:: a-cccc]")
    assert v["next"].text == "bir" and v["continue_with"].text == "uc"

    v = _view("- [/] bir [id:: a-aaaa]", "- [/] iki [id:: a-bbbb]", "- [ ] uc [id:: a-cccc]")
    assert v["next"].text == "bir" and v["continue_with"].text == "uc"

    v = _view("- [ ] bir [id:: a-aaaa]", "- [ ] iki [id:: a-bbbb]")
    assert v["next"].text == "bir" and v["continue_with"] is None

    v = _view("- [ ] bir [id:: a-aaaa] " + BLOCKED, "- [/] iki [id:: a-bbbb] " + BLOCKED)
    assert v["next"] is None and len(v["blocked"]) == 2
    assert v["complete"] is False                       # blocked holds the steps open

    v = _view("- [x] bir [id:: a-aaaa] [completion:: 2026-09-17]", "- [-] iki [id:: a-bbbb]")
    assert v["complete"] is True and v["next"] is None and v["blocked"] == []

    v = _view()
    assert v["complete"] is False and v["next"] is None


# --------------------------------------------------------------------------
# the validator
# --------------------------------------------------------------------------

VALID_FM = ('---\nid: demo\ntitle: "Demo"\nlevel: T1\nstatus: active\n'
            'created: 2026-09-01\n---\n')
VALID_SECTIONS = ("Goal", "Steps", "Out of Scope", "Status", "Notes",
                  "Decision Log", "Open Questions")


def vtask(steps="- [ ] adim [id:: d-aaaa]\n", fm=VALID_FM, sections=VALID_SECTIONS):
    """A minimal valid task file. Frontmatter keys land on lines 2-6 and the steps
    body starts on line 14, which is what the line numbers below are about."""
    body = "# demo\n"
    for s in sections:
        body += "\n## %s\n" % s
        if s == "Steps":
            body += steps
        elif s == "Goal":
            body += "tek cumle\n"
    return fm + body


def test_validate_rules():
    """One fixture per rule. The validator's whole value is that it names the line
    to open, so a rule that fires on the wrong line is as useless as one that does
    not fire; and it is the thing you run on a broken file, so it never raises."""
    assert t.validate_task(vtask(), "demo") == []

    missing_notes = vtask(sections=[s for s in VALID_SECTIONS if s != "Notes"])
    dup_section = vtask(sections=list(VALID_SECTIONS) + ["Status"])
    dup_line = len(dup_section.splitlines()) - dup_section.splitlines()[::-1].index("## Status")

    cases = [
        ("no frontmatter", vtask(fm=""), 1, "no frontmatter block"),
        ("empty id", vtask(fm='---\nid:\ntitle: "D"\nlevel: T1\nstatus: active\n---\n'),
         2, "frontmatter: `id` is missing or empty"),
        ("empty status", vtask(fm='---\nid: demo\ntitle: "D"\nlevel: T1\nstatus:\n---\n'),
         5, "frontmatter: `status` is missing or empty"),
        ("unquoted title", vtask(fm='---\nid: demo\ntitle: Rapor: pivot\nlevel: T1\n'
                                    'status: active\n---\n'),
         3, "title is not quoted"),
        ("bad level", vtask(fm='---\nid: demo\ntitle: "D"\nlevel: T5\nstatus: active\n---\n'),
         4, "level 'T5' is not T1 or T2"),
        ("bad status", vtask(fm='---\nid: demo\ntitle: "D"\nlevel: T1\nstatus: paused\n---\n'),
         5, "status 'paused' is not one of"),
        ("bad started", vtask(fm='---\nid: demo\ntitle: "D"\nlevel: T1\nstatus: active\n'
                                 'started: dun\n---\n'),
         6, "started 'dun' is not a YYYY-MM-DD date"),
        ("links not a list", vtask(fm='---\nid: demo\ntitle: "D"\nlevel: T1\nstatus: active\n'
                                      'links: x.md\n---\n'),
         6, "links is not a list"),
        ("missing section", missing_notes, len(missing_notes.splitlines()),
         "missing `## Notes` section"),
        ("duplicated section", dup_section, dup_line, "`## Status` appears more than once"),
        ("`*` checkbox", vtask(steps="* [ ] adim\n- [ ] ok [id:: d-aaaa]\n"),
         14, "checkbox with a `*`/`+` bullet"),
        ("unknown state", vtask(steps="- [?] adim [id:: d-aaaa]\n"),
         14, "unknown checkbox state [?]"),
        ("empty text", vtask(steps="- [ ] [id:: d-aaaa]\n"), 14, "step has no text"),
        ("ordered-list trap", vtask(steps="- [ ] 1. adim [id:: d-aaaa]\n"),
         14, "`1.` after the box starts an ordered list"),
        ("field twice", vtask(steps="- [ ] adim [id:: d-aaaa] [id:: d-bbbb]\n"),
         14, "[id:: ] appears twice on the line"),
        ("empty field value", vtask(steps="- [ ] adim [id::]\n"), 14, "[id:: ] is empty"),
        ("missing id", vtask(steps="- [ ] adim\n"), 14, "step has no [id:: ]"),
        ("malformed id", vtask(steps="- [ ] adim [id:: NOPE]\n"),
         14, "[id:: NOPE] is not a trail id"),
        ("duplicate id", vtask(steps="- [ ] bir [id:: d-aaaa]\n- [ ] iki [id:: d-aaaa]\n"),
         15, "duplicate id d-aaaa (also on line 14)"),
        ("[x] without completion", vtask(steps="- [x] adim [id:: d-aaaa]\n"),
         14, "[x] has no [completion:: ] date"),
        ("completion on [ ]", vtask(steps="- [ ] adim [id:: d-aaaa] [completion:: 2026-09-17]\n"),
         14, "[completion:: ] on a [ ] item"),
        ("bad completion date", vtask(steps="- [x] adim [id:: d-aaaa] [completion:: dun]\n"),
         14, "[completion:: dun] is not a YYYY-MM-DD date"),
        ("blocked without reason", vtask(steps="- [ ] adim [id:: d-aaaa] [blocked:: 2026-09-17]\n"),
         14, "[blocked:: ] without [blocked-reason:: ]"),
        ("reason without blocked",
         vtask(steps="- [ ] adim [id:: d-aaaa] [blocked-reason:: ses yok]\n"),
         14, "[blocked-reason:: ] without [blocked:: ]"),
        ("bad blocked date",
         vtask(steps="- [ ] adim [id:: d-aaaa] [blocked:: dun] [blocked-reason:: ses yok]\n"),
         14, "[blocked:: dun] is not a YYYY-MM-DD date"),
        ("blocked on [x]",
         vtask(steps="- [x] adim [id:: d-aaaa] [completion:: 2026-09-17] "
                    "[blocked:: 2026-09-17] [blocked-reason:: ses yok]\n"),
         14, "a resolved item cannot be waiting"),
    ]
    for label, text, line, needle in cases:
        found = t.validate_task(text, "demo")
        assert any(n == line and needle in problem for n, problem, _ in found), \
            (label, line, needle, found)

    # the id is checked against the file name, not against itself
    found = t.validate_task(vtask(), "baska")
    assert [(n, "does not match the file name" in p) for n, p, _ in found] == [(2, True)], found

    # every section is required; their order is not, because the file is a
    # document people rearrange and the CLI finds each heading by name
    assert t.validate_task(vtask(sections=tuple(reversed(VALID_SECTIONS))), "demo") == []

    # a file with nothing in it is the case you most want an answer for
    assert t.validate_task("", "demo")[0][0] == 1
    assert len(t.validate_task("bir satir\n", "demo")) == 8   # frontmatter + 7 sections

    # and a file the CLI itself wrote, end to end, is clean
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "gecerli", "T2")
        run_full(tmp, "write", "steps", input="- [ ] bir\n- [ ] iki\n")
        run(tmp, "check", "bir")
        run(tmp, "block", "iki", "ses dosyasi hazir degil")
        f = tmp / ".trail/tasks/gecerli.md"
        assert t.validate_task(f.read_text("utf-8"), "gecerli") == []
        assert "ok: 1 task file valid" in run(tmp, "validate")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_validate_task_dates():
    """`created` is required and only `trail start` knows it, so its fix is not a
    `trail set`. What goes unreported is as deliberate as what is reported: a task
    closed before `completed` existed has no known close date, and a parked task
    keeps the day it started."""
    def fm(status, **dates):
        lines = ["id: demo", 'title: "Demo"', "level: T1", "status: %s" % status]
        lines += ["%s: %s" % (k, v) if v else "%s:" % k for k, v in dates.items()]
        return "---\n%s\n---\n" % "\n".join(lines)

    hint = "add `created: YYYY-MM-DD` (the day the file was made)"
    found = t.validate_task(vtask(fm=fm("active", started="2026-09-02")), "demo")
    assert found == [(1, "frontmatter: `created` is missing or empty", hint)], found
    found = t.validate_task(vtask(fm=fm("active", created="")), "demo")
    assert found == [(6, "frontmatter: `created` is missing or empty", hint)], found

    for key, line in (("created", 6), ("started", 7), ("completed", 8)):
        dates = {"created": "2026-09-01", "started": "2026-09-02", "completed": "2026-09-03"}
        dates[key] = "dun"
        found = t.validate_task(vtask(fm=fm("done", **dates)), "demo")
        assert [(n, p) for n, p, _ in found] == [
            (line, "%s 'dun' is not a YYYY-MM-DD date" % key)], (key, found)

    for status in ("open", "active", "blocked"):
        found = t.validate_task(vtask(fm=fm(status, created="2026-09-01", started="2026-09-02",
                                            completed="2026-09-03")), "demo")
        assert found == [(8, "completed is set but the task is not done",
                          "delete the `completed:` line, or close the task with `trail done`")], found

    assert t.validate_task(vtask(fm=fm("done", created="2026-09-01", started="2026-09-02",
                                       completed="")), "demo") == []
    assert t.validate_task(vtask(fm=fm("open", created="2026-09-01",
                                       started="2026-09-02")), "demo") == []


def test_task_dates():
    """Three different days that `started: {{date}}` used to collapse into one: the
    file was made, work first began, the task closed. Each is written once, by the
    move that makes it true, and a day nobody knows is left empty, not made up."""
    # an empty value is `key:`, the way the template writes it
    assert t.set_field("---\na: x\n---\n", "a", "") == "---\na:\n---\n"
    assert t.set_field("---\na: x\n---\n", "b", "") == "---\na: x\nb:\n---\n"

    tmp = Path(tempfile.mkdtemp())
    today = date.today().isoformat()
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")

        def line(slug, key):
            text = (tmp / (".trail/tasks/%s.md" % slug)).read_text("utf-8")
            return next(l for l in text.splitlines() if l.split(":")[0] == key)

        def edit(slug, key, value):          # a hand edit, or a file an older trail wrote
            f = tmp / (".trail/tasks/%s.md" % slug)
            f.write_text(t.set_field(f.read_text("utf-8"), key, value), "utf-8")

        run(tmp, "start", "aktif")
        assert line("aktif", "created") == "created: " + today
        assert line("aktif", "started") == "started: " + today
        assert line("aktif", "completed") == "completed:"      # no trailing space
        for status in ("open", "blocked"):
            run(tmp, "start", "park-" + status, "--status", status)
            assert line("park-" + status, "created") == "created: " + today
            assert line("park-" + status, "started") == "started:", status
            assert line("park-" + status, "completed") == "completed:", status

        # the first move into active writes `started`; a later one keeps it
        run(tmp, "resume", "park-open")
        assert line("park-open", "started") == "started: " + today
        run(tmp, "set", "status", "open", "--task", "park-open")
        edit("park-open", "started", "2026-01-02")
        run(tmp, "resume", "park-open")
        assert line("park-open", "started") == "started: 2026-01-02"
        run(tmp, "start", "planli", "--status", "open")
        run(tmp, "set", "status", "active", "--task", "planli")
        assert line("planli", "started") == "started: " + today

        # already active with no `started`: the real day is unknown, so nothing is written
        edit("aktif", "started", "")
        run(tmp, "resume", "aktif")
        run(tmp, "set", "status", "active", "--task", "aktif")
        assert line("aktif", "started") == "started:"

        # closing dates the task once; closing it again keeps the recorded day
        run(tmp, "done", "--task", "aktif")
        assert line("aktif", "completed") == "completed: " + today
        edit("aktif", "completed", "2026-01-03")
        run(tmp, "done", "--task", "aktif")
        assert line("aktif", "completed") == "completed: 2026-01-03"
        edit("aktif", "completed", "")      # a close from before `completed` existed
        run(tmp, "done", "--task", "aktif")
        assert line("aktif", "completed") == "completed:"
        # reopening clears it; `started` is history and stays
        run(tmp, "done", "--task", "planli")
        assert line("planli", "completed") == "completed: " + today
        run(tmp, "set", "status", "open", "--task", "planli")
        assert line("planli", "completed") == "completed:"
        assert line("planli", "started") == "started: " + today
        shown = json.loads(run(tmp, "show", "planli", "--json"))
        assert (shown["created"], shown["started"], shown["completed"]) == (today, today, "")

        # the digest header carries each date only when it is set
        out = run(tmp, "status", "--task", "park-open")
        assert "Task: park-open (T1, active, created %s, started 2026-01-02)" % today in out, out
        out = run(tmp, "status", "--task", "park-blocked")
        assert "Task: park-blocked (T1, blocked, created %s)\n" % today in out, out

        # a template from before `created`: the CLI writes the dates, not {{date}}
        tpl = tmp / ".trail/_template.md"
        old = tpl.read_text("utf-8").replace("created:\nstarted:\ncompleted:\n", "started: {{date}}\n")
        assert "started: {{date}}" in old and "created:" not in old
        tpl.write_text(old, "utf-8")
        run(tmp, "start", "eski")
        run(tmp, "start", "eski-park", "--status", "open")
        assert line("eski", "created") == "created: " + today
        assert line("eski", "started") == "started: " + today
        assert line("eski-park", "created") == "created: " + today
        assert line("eski-park", "started") == "started:"

        # everything the CLI wrote above is a valid file
        out = run(tmp, "validate")
        assert "ok: 6 task files valid" in out, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------------
# the reading ladder and the writers
# --------------------------------------------------------------------------

def test_notes_ladder():
    """`status` says a count, `notes` hands the findings over whole. An entry that
    spans lines is one entry: truncating it mid-measurement is how the digest lost
    the number somebody wrote down."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "bulgu")
        run(tmp, "start", "bos", "--status", "open")
        for n in ("bir", "iki", "uc"):
            run(tmp, "note", "olcum %s" % n, "--task", "bulgu")
        # a continuation line added by hand: `## Notes` has no rules
        f = tmp / ".trail/tasks/bulgu.md"
        f.write_text(f.read_text("utf-8").replace(
            "· olcum iki\n", "· olcum iki\n  devam satiri: 9.6sn cold\n"), "utf-8")

        out = run(tmp, "notes", "-n", "2", "--task", "bulgu")
        assert out.splitlines()[0] == "bulgu: last 2 of 3 notes (trail notes --all)", out
        assert "· olcum bir" not in out, out
        assert "· olcum iki\n  devam satiri: 9.6sn cold\n" in out, out
        assert "· olcum uc" in out, out

        out = run(tmp, "notes", "--all", "--task", "bulgu")
        assert "of 3 notes" not in out, out       # no header when nothing is hidden
        assert out.count("· olcum ") == 3, out
        assert "  devam satiri: 9.6sn cold" in out, out

        assert run(tmp, "notes", "--task", "bos").strip() == "bos: no notes"
        assert "Notes 3 (trail notes)" in run(tmp, "status", "--task", "bulgu")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_log_stdin_contract():
    """A reason worth writing down is longer than a shell argument, and a shell
    argument mangles `$x` and quotes on the way in. The split between the two
    fields has to be deterministic, so anything ambiguous is refused untouched."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "karar")
        f = tmp / ".trail/tasks/karar.md"

        run_full(tmp, "log", "styled_surface resolve", "--stdin",
                 input='--why\nilk satir $dollar ve "quote"\nikinci satir\n'
                       '--dropped\nelenen yol\n')
        text = f.read_text("utf-8")
        assert '  - **why:** ilk satir $dollar ve "quote"\n    ikinci satir\n' in text, text
        assert "  - **dropped:** elenen yol" in text, text
        entries = t.decision_entries(text)
        assert len(entries) == 1, entries
        assert entries[0][0].endswith("· styled_surface resolve"), entries
        assert entries[0][1] == ['  - **why:** ilk satir $dollar ve "quote"',
                                 "    ikinci satir",
                                 "  - **dropped:** elenen yol"], entries

        out = run(tmp, "search", "ikinci satir")
        assert "styled_surface resolve" in out, out    # the title came with the match

        # an entry is a block, not an essay: a blank line inside a body is dropped,
        # and an inline value with newlines renders exactly like a stdin one
        run_full(tmp, "log", "bosluk", "--stdin", input="--why\nbir\n\niki\n")
        run(tmp, "log", "satirli", "--why", "bir\niki")
        assert f.read_text("utf-8").count("  - **why:** bir\n    iki\n") == 2, f.read_text("utf-8")

        # inline and stdin mix, as long as they carry different fields
        run_full(tmp, "log", "karma", "--why", "kisa", "--stdin",
                 input="--dropped\nsadece elenen\n")
        assert "  - **why:** kisa\n  - **dropped:** sadece elenen" in f.read_text("utf-8")

        before = f.read_text("utf-8")
        for label, argv, body, needle in (
                ("text before the first label", [], "once prose\n--why\nx\n", "must start with"),
                ("a label twice", [], "--why\na\n--why\nb\n", "--why appears twice"),
                ("no label at all", [], "sadece govde\n", "must start with"),
                ("empty stdin", [], "", "no --why or --dropped line found"),
                ("empty body", [], "--why\n\n--dropped\nx\n", "--why has an empty body"),
                ("both inline and on stdin", ["--why", "inline"], "--why\nx\n",
                 "given both inline and on stdin")):
            r = run_full(tmp, "log", "reddedilen", "--stdin", *argv, input=body, code=1)
            assert needle in r.stderr, (label, r.stderr)
            assert f.read_text("utf-8") == before, label
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_item_commands_end_to_end():
    """The steps stopped being a hand-edited blob: every box is now a command, and
    the reason a session trusts the result is that a refusal writes nothing and a
    report says exactly which line moved, by id."""
    tmp = Path(tempfile.mkdtemp())
    today = date.today().isoformat()
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "demo-task", "T2")
        f = tmp / ".trail/tasks/demo-task.md"
        out = run_full(tmp, "write", "steps",
                       input="- [ ] alfa adimi\n- [ ] beta adimi\n"
                             "- [ ] gama adimi\n- [ ] delta adimi\n").stdout
        assert "4 ids assigned" in out, out
        ids = [it.id for it in t.parse_steps(f.read_text("utf-8"))]
        assert len(ids) == 4 and len(set(ids)) == 4, ids
        for i in ids:
            assert i.startswith("dt-") and t.ITEM_ID_RE.match(i), i

        assert "Next:\n  [%s] [ ] alfa adimi" % ids[0] in run(tmp, "status")

        out = run(tmp, "check", "alfa")
        assert out.strip() == "demo-task: [%s] [ ] -> [x] alfa adimi · completion %s" % (
            ids[0], today), out
        assert "- [x] alfa adimi [id:: %s] [completion:: %s]" % (ids[0], today) \
            in f.read_text("utf-8")

        before = f.read_text("utf-8")
        out = run(tmp, "check", "alfa")             # the end state already holds
        assert out.strip() == "demo-task: [%s] is already [x] (completion %s); " \
            "nothing changed" % (ids[0], today), out
        assert f.read_text("utf-8") == before

        run(tmp, "check", "beta", "--partial")
        out = run(tmp, "status")
        assert "Next:\n  [%s] [/] beta adimi" % ids[1] in out, out
        assert "Can continue with:\n  [%s] [ ] gama adimi" % ids[2] in out, out

        out = run(tmp, "block", "gama", "ses dosyasi hazir degil")
        assert out.strip() == "demo-task: [%s] [ ] gama adimi · blocked %s: " \
            "ses dosyasi hazir degil" % (ids[2], today), out     # the box is not touched
        out = run(tmp, "status")
        assert "Blocked:\n  [%s] [ ] gama adimi · blocked since %s: ses dosyasi hazir degil" % (
            ids[2], today) in out, out
        assert "Next:\n  [%s] [/] beta adimi" % ids[1] in out, out
        assert "Can continue with:\n  [%s] [ ] delta adimi" % ids[3] in out, out

        before = f.read_text("utf-8")
        r = run_full(tmp, "check", "gama", code=1)
        assert "is blocked" in r.stderr and "trail unblock %s" % ids[2] in r.stderr, r.stderr
        assert f.read_text("utf-8") == before
        r = run_full(tmp, "block", "gama", "baska sebep", code=1)
        assert "already blocked" in r.stderr, r.stderr
        assert "trail unblock %s && trail block %s" % (ids[2], ids[2]) in r.stderr, r.stderr
        assert f.read_text("utf-8") == before

        # the reason is written as an inline field, so it has to survive being one
        for reason, needle in (("kose ] parantez", "cannot contain ']'"),
                               ("", "needs a reason")):
            r = run_full(tmp, "block", "delta", reason, code=1)
            assert needle in r.stderr, r.stderr
            assert f.read_text("utf-8") == before

        # blocked is independent of the box: it may still move, just not to resolved
        run(tmp, "check", "gama", "--partial")
        run(tmp, "uncheck", "gama")
        assert "[blocked-reason:: ses dosyasi hazir degil]" in f.read_text("utf-8")

        before = f.read_text("utf-8")
        for argv in (["check", "beta", "--partial"], ["unblock", "beta"]):
            out = run(tmp, *argv)                   # the end state already holds
            assert "nothing changed" in out, (argv, out)
            assert f.read_text("utf-8") == before, argv

        out = run(tmp, "unblock", "gama")
        assert "unblocked (was %s: ses dosyasi hazir degil)" % today in out, out
        gama = [it for it in t.parse_steps(f.read_text("utf-8")) if it.id == ids[2]][0]
        assert not gama.blocked and gama.state == " ", gama
        assert "- [ ] gama adimi [id:: %s]\n" % ids[2] in f.read_text("utf-8")

        run(tmp, "cancel", "delta", "kapsam disi")
        assert "- [-] delta adimi — kapsam disi [id:: %s]" % ids[3] in f.read_text("utf-8")

        before = f.read_text("utf-8")
        r = run_full(tmp, "check", "adimi", code=1)
        assert "4 steps match 'adimi' - say which, by id:" in r.stderr, r.stderr
        assert f.read_text("utf-8") == before
        r = run_full(tmp, "check", "yokbunyok", code=1)
        assert "no step matches 'yokbunyok'. The steps:" in r.stderr, r.stderr
        assert "[%s] [x] alfa adimi" % ids[0] in r.stderr, r.stderr
        assert f.read_text("utf-8") == before

        # a parked task is still addressable: --task, like every other writer
        run(tmp, "start", "park", "--status", "open")
        run_full(tmp, "write", "steps", "--task", "park", input="- [ ] park adimi\n")
        park = tmp / ".trail/tasks/park.md"

        # re-piping a body that already carries its ids assigns none, and says so
        # by leaving the count out rather than reporting zero
        body = t.get_section(park.read_text("utf-8"), "Steps")
        out = run_full(tmp, "write", "steps", "--task", "park", input=body + "\n").stdout
        assert out.strip() == "park: ## Steps written (1 line)", out

        # two lines carrying the same id: refuse the whole body, write nothing
        before = park.read_text("utf-8")
        r = run_full(tmp, "write", "steps", "--task", "park", code=1,
                     input="- [ ] bir [id:: p-aaaa]\n- [ ] iki [id:: p-aaaa]\n")
        assert "duplicate step id p-aaaa" in r.stderr, r.stderr
        assert park.read_text("utf-8") == before

        out = run(tmp, "check", "park adimi", "--task", "park")
        assert "-> [x] park adimi · completion %s" % today in out, out
        assert out.startswith("park: [p-"), out

        # an id-less line added by hand is rewritten anyway, so it earns an id
        f.write_text(f.read_text("utf-8").replace(
            "- [-] delta", "- [/] elle eklendi\n- [-] delta"), "utf-8")
        out = run(tmp, "uncheck", "elle eklendi")
        assert "· id assigned" in out, out
        new_id = [it.id for it in t.parse_steps(f.read_text("utf-8"))
                  if it.text == "elle eklendi"][0]
        assert new_id.startswith("dt-") and t.ITEM_ID_RE.match(new_id), new_id
        assert "- [ ] elle eklendi [id:: %s]\n" % new_id in f.read_text("utf-8")

        run(tmp, "block", "gama", "beklemede")
        steps = json.loads(run(tmp, "status", "--json"))["tasks"][0]["steps"]
        assert [p["id"] for p in steps] == ids[:3] + [new_id, ids[3]], steps
        assert set(steps[0]) == {"id", "state", "text", "line", "completion",
                                 "blocked", "blocked_reason"}, steps[0]
        by_id = {p["id"]: p for p in steps}
        assert by_id[ids[0]]["state"] == "x" and by_id[ids[0]]["completion"] == today
        assert by_id[ids[2]]["blocked"] == today
        assert by_id[ids[2]]["blocked_reason"] == "beklemede"
        assert by_id[ids[3]]["state"] == "-" and by_id[ids[3]]["completion"] is None
        assert json.loads(run(tmp, "show", "demo-task", "--json"))["steps"] == steps

        out = run(tmp, "done")
        assert "closing with steps open - deliberate?" in out, out
        assert "[%s] [/] beta adimi" % ids[1] in out, out
        assert "[%s] [ ] gama adimi · blocked since %s: beklemede" % (ids[2], today) in out, out
        assert "[%s] [ ] elle eklendi" % new_id in out, out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_steps_complete_nudge():
    """The steps say nothing is left, the status says work is on: one of them is
    stale and only a person knows which. A blocked item is not 'left', so the
    nudge has to stay quiet while anything is still waiting."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "bitti", "T2")
        run_full(tmp, "write", "steps", input="- [ ] bir\n- [ ] iki\n")
        run(tmp, "check", "bir")
        run(tmp, "cancel", "iki", "gereksiz")
        nudge = "bitti: every step is resolved but the task is still active"
        out = run(tmp, "status")
        assert "Next: none - every step is resolved" in out, out
        assert nudge in out, out

        f = tmp / ".trail/tasks/bitti.md"
        resolved = f.read_text("utf-8")
        f.write_text(resolved.replace(
            "- [-] iki", "- [ ] uc [id:: b-zzzz] [blocked:: 2026-09-15] "
                         "[blocked-reason:: bekliyor]\n- [-] iki"), "utf-8")
        out = run(tmp, "status")
        assert "Next: none - every remaining item is blocked" in out, out
        assert nudge not in out, out
        f.write_text(resolved, "utf-8")

        # a task with no steps at all is not nudged either
        run(tmp, "set", "status", "open", "--task", "bitti")
        run(tmp, "start", "adimsiz")
        out = run(tmp, "status")
        assert "Task: adimsiz" in out and "every step is resolved" not in out, out

        run(tmp, "set", "status", "active", "--task", "bitti")
        run(tmp, "set", "status", "open", "--task", "adimsiz")
        assert nudge in run(tmp, "status")
        run(tmp, "done", "--task", "bitti")
        assert "every step is resolved" not in run(tmp, "status")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_format_nudge():
    """A file only trail reads is a file nobody checks. The nudge is the only way
    a session learns that the steps it is about to act on has a line the CLI cannot
    name - and it has to say which command lists them."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "bicim", "T2")
        run_full(tmp, "write", "steps", input="- [ ] bir\n")
        f = tmp / ".trail/tasks/bicim.md"
        f.write_text(f.read_text("utf-8").replace(
            "## Out of Scope", "- [ ] elle eklendi\n\n## Out of Scope"), "utf-8")

        out = run(tmp, "status")
        assert "bicim: 1 format problem in the task file" in out, out
        assert "trail validate --task bicim" in out, out
        # the finding names the line and the fix sits under it, aligned
        r = run_full(tmp, "validate", "--task", "bicim", code=1)
        lines = r.stdout.splitlines()
        assert lines[0] == ".trail/tasks/bicim.md", lines
        assert lines[1].startswith("  line ") and "step has no [id:: ]" in lines[1], lines
        head = lines[1].index(": ") + 2
        assert lines[2].startswith(" " * head + "fix: "), lines
        assert "trail write steps" in lines[2], lines
        assert lines[3] == "1 problem in 1 of 1 task file", lines
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_write_plan_is_refused_and_names_steps():
    """`## Plan` became `## Steps` with no alias: an alias is a second name that every
    reader and every doc would have to carry for good. The old name fails the way any
    unknown section does, and the list it prints is where the new name is found."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "eski-ad", "T2")
        f = tmp / ".trail/tasks/eski-ad.md"
        before = f.read_text("utf-8")
        r = run_full(tmp, "write", "plan", code=1, input="- [ ] bir\n")
        assert "section must be one of: " in r.stderr and "Steps" in r.stderr, r.stderr
        assert "Plan" not in r.stderr, r.stderr
        assert f.read_text("utf-8") == before                  # refused, nothing written
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_a_plan_heading_is_not_read_as_steps():
    """A file that still says `## Plan` is not quietly read under the old name. The
    validator names the missing section, and `status` shows no steps rather than
    guessing that the old heading meant the new one."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        run(tmp, "start", "eski-bicim", "T2")
        run_full(tmp, "write", "steps", input="- [ ] bir\n- [ ] iki\n")
        f = tmp / ".trail/tasks/eski-bicim.md"
        f.write_text(f.read_text("utf-8").replace("\n## Steps\n", "\n## Plan\n"), "utf-8")
        assert "\n## Plan\n" in f.read_text("utf-8")

        r = run_full(tmp, "validate", "--task", "eski-bicim", code=1)
        assert "missing `## Steps` section" in r.stdout, r.stdout
        out = run(tmp, "status", "--task", "eski-bicim")
        assert "Steps:" not in out and "Next:" not in out and "bir" not in out, out
        assert json.loads(run(tmp, "status", "--json"))["tasks"][0]["steps"] == []
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_init_installs_both_skills():
    """Two entry points, one install step: a repo that got only /trail never learns
    that /trail-plan exists, and a drifted copy is the user's edit, not trail's."""
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        for name in t.SKILLS:
            assert (tmp / ".claude/skills" / name / "SKILL.md").is_file(), name
        assert not (tmp / ".agents").exists()

        planned = tmp / ".claude/skills/trail-plan/SKILL.md"
        planned.write_text("stale\n", "utf-8")
        assert ".claude/skills/trail-plan/SKILL.md differs" in run(tmp, "init")
        assert planned.read_text("utf-8") == "stale\n"          # warned, never clobbered
        assert "(refreshed)" in run(tmp, "init", "--force")
        assert planned.read_text("utf-8") == (HERE / "skills" / "trail-plan"
                                              / "SKILL.md").read_text("utf-8")

        # a .codex marker routes both files to the shared .agents path
        (tmp / ".codex").mkdir()
        run(tmp, "init")
        for name in t.SKILLS:
            assert (tmp / ".agents/skills" / name / "SKILL.md").is_file(), name
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  %s" % fn.__name__)
    print("\n%d passed" % len(fns))
