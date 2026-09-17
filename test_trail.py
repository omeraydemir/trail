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
    """This repo dogfoods trail, so it holds two copies of SKILL.md.
    They must not drift; the source of truth is skills/trail/."""
    src = HERE / "skills" / "trail" / "SKILL.md"
    dest = HERE / ".claude" / "skills" / "trail" / "SKILL.md"
    if dest.exists():
        assert src.read_text("utf-8") == dest.read_text("utf-8"), \
            "SKILL.md kopyalari ayrismis: 'trail init --force' ile tazele"


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
                              ("plan", "- [x] kolon cozumu\n- [ ] sayfa hata yolu\n"),
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
        assert "- [ ] sayfa hata yolu" in out               # what is next
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
        r = subprocess.run([sys.executable, str(BIN), "write", "plan", "--task", "planned-item"],
                           cwd=str(tmp), input="adim 1\nadim 2\n", capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert t.get_section(f2.read_text("utf-8"), "Plan") == "adim 1\nadim 2"

        # plan progress: [x] counts, [-] leaves the denominator, [/] is not done yet
        r = subprocess.run([sys.executable, str(BIN), "write", "plan", "--task", "planned-item"],
                           cwd=str(tmp),
                           input="- [x] one [completion:: 2026-09-12]\n- [/] two\n- [ ] three\n- [-] four\n",
                           capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert t.plan_progress(f2.read_text("utf-8")) == (1, 3)
        assert t.next_plan_item(f2.read_text("utf-8")) == "- [/] two"
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


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  %s" % fn.__name__)
    print("\n%d passed" % len(fns))
