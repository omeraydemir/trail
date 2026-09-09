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
        assert t.missing_scaffold(tmp, cfg) == [cfg["backlog"], cfg["decisions"]]
        (tmp / cfg["backlog"]).write_text("# Backlog\n", "utf-8")
        assert t.missing_scaffold(tmp, cfg) == [cfg["decisions"]]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(cwd, *args, **kw):
    r = subprocess.run([sys.executable, str(BIN)] + list(args),
                       cwd=str(cwd), capture_output=True, text=True, env=kw.get("env"))
    assert r.returncode == kw.get("code", 0), (args, r.returncode, r.stdout, r.stderr)
    return r.stdout


def test_end_to_end():
    tmp = Path(tempfile.mkdtemp())
    try:
        subprocess.run(["git", "init", "-q"], cwd=str(tmp), check=True)
        run(tmp, "init")
        assert (tmp / ".trail/tasks").is_dir()
        assert (tmp / "DECISIONS.md").is_file()
        # the sink must be visible before first use, or nobody knows to empty it
        assert (tmp / ".trail/backlog.md").is_file()
        # no agent markers in a bare repo -> claude is the fallback
        assert (tmp / ".claude/skills/trail/SKILL.md").is_file()
        assert not (tmp / ".agents").exists()

        # DECISIONS.md is configurable at init and re-init respects it
        tmp2 = Path(tempfile.mkdtemp())
        try:
            subprocess.run(["git", "init", "-q"], cwd=str(tmp2), check=True)
            run(tmp2, "init", "--decisions", "docs/DECISIONS.md")
            assert (tmp2 / "docs/DECISIONS.md").is_file()
            assert not (tmp2 / "DECISIONS.md").exists()
            run(tmp2, "init")  # must not plant a second ledger at the root
            assert not (tmp2 / "DECISIONS.md").exists()
            run(tmp2, "start", "x")
            run(tmp2, "log", "keep me")
            run(tmp2, "done", "--no-edit")
            assert "keep me" in (tmp2 / "docs/DECISIONS.md").read_text("utf-8")
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
        assert "dropped: universal links" in f.read_text("utf-8")

        run(tmp, "handoff", "parser done")
        assert t.get_section(f.read_text("utf-8"), "Status") == "parser done"

        out = json.loads(run(tmp, "ls", "--json"))
        assert len(out) == 1 and out[0]["level"] == "T2"

        st = run(tmp, "status", "--inject")
        assert "===BEGIN TRAIL===" in st and "use applinks" in st

        # duplicate slug is refused
        run(tmp, "start", "deep-link", code=1)

        run(tmp, "done", "--no-edit")
        assert not f.exists()
        assert (tmp / ".trail/archive/deep-link.md").is_file()
        dec = (tmp / "DECISIONS.md").read_text("utf-8")
        assert "dropped: universal links" in dec and "## deep link" in dec
        assert t.parse_fm((tmp / ".trail/archive/deep-link.md").read_text("utf-8"))["status"] == "done"

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
        assert (tmp / ".trail/backlog.md").read_text("utf-8").count("\n- ") == 2
        assert "backlog: 2 items" in run(tmp, "status")

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
