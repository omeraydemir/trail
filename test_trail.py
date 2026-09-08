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


def test_slugify():
    assert t.slugify("Push Notification  Deeplink!") == "push-notification-deeplink"


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
        assert (tmp / ".agents/skills/trail/SKILL.md").is_file()

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
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok  %s" % fn.__name__)
    print("\n%d passed" % len(fns))
