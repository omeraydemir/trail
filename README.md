# trail

A task ledger that lives in your repo. One markdown file per task, one CLI, no
dependencies. Works with any AI coding agent — the logic is in the CLI, not in a
provider's hooks.

The point is not the task list. It is the **decision log** inside each task, and
specifically the `dropped:` field: what you rejected, and why. "What I did" is
already in the code. What is lost three months later is what you decided *not* to do.

## Why not a session handoff

Sessions are a technical boundary — context filled up, laptop slept. A task is the
semantic one: you have a goal and a definition of done. Systems that tie a summary
to session end break from both ends: they tax one-prompt work into abandonment, and
they produce five disconnected summaries for work that spans five sessions.

So the unit is the task, ceremony scales with size, and the log is written at the
moment a decision is made — which makes handoff nearly free instead of a
lossy end-of-session reconstruction.

| Level | When | Ceremony |
| --- | --- | --- |
| T0 | single session, cheap to undo | **nothing** — no file, no command |
| T1 | 2-3 sessions, one topic | task file + close |
| T2 | multi-day, architectural | + `## Plan` + handoff each session |

T0 must stay free. A process system dies from taxing trivial work.

## Install

```bash
git clone https://github.com/omeraydemir/trail.git ~/.local/share/trail
ln -s ~/.local/share/trail/bin/trail ~/.local/bin/trail
```

Requires Python 3.9+ (preinstalled on macOS and most Linux). No pip, no venv.

Then, in any repo:

```bash
trail init
```

This creates `.trail/`, `DECISIONS.md`, and a `SKILL.md` for whichever agents the
repo already uses. Agents disagree about where project skills live — Claude Code
reads `.claude/skills/`, while Codex, Cursor and Gemini CLI read `.agents/skills/` —
so `init` detects the marker directories present and writes to the right ones.
Force it with `trail init --agent claude|codex|cursor|gemini|all`.

## Use

```bash
trail start deeplink-handling T1        # new task
trail log "route via AppLinks" \
     --why "Universal Links needs an AASA host we don't control" \
     --dropped "Universal Links"        # write it the moment you decide
trail handoff "parser done, wiring the receiver next"
trail status                            # what am I doing, what went stale
trail ls --stale 7                      # untouched for a week
trail board                             # terminal kanban
trail done                              # distill into DECISIONS.md, archive
```

Every read command takes `--json`.

`trail done` appends the raw log to `DECISIONS.md` and hands it to you to trim.
The distillation is deliberately not automatic — it is the one place where being
wrong is expensive.

## Layout

```
.trail/
  config.yml          optional
  _template.md        yours to edit
  tasks/<slug>.md     scaffolding — dies with the task
  archive/<slug>.md
DECISIONS.md          permanent, versioned with the code
```

Two artifacts, two lifetimes. `DECISIONS.md` sits outside `.trail/` so it stays
committed even if you gitignore the task files.

`.trail/` is committed by default. Working solo and want tasks off git? Add it to
`.gitignore` — `DECISIONS.md` survives either way.

Because tasks are committed by default, they are readable by anyone with repo
access: no credentials, customer identifiers or private notes in task files.

See [spec/FORMAT.md](spec/FORMAT.md) for the full format contract.

## Configuration

`.trail/config.yml` is optional; defaults apply when absent.

```yaml
dir: .trail/tasks
archive: .trail/archive
decisions: DECISIONS.md
template: .trail/_template.md
stale_days: 7
```

Custom frontmatter fields go in `_template.md`, not in config. The CLI reads only
`id` `title` `level` `status`; everything else is yours and is preserved on write.

## Nudges

`trail status` derives state from disk, not from lifecycle events — nothing has to
have fired for the answer to be right.

- task file untouched for `stale_days` → *still active? close it or continue*
- code changed more recently than the task file → *you worked, you didn't log*

Nudges only remind. Nothing is ever written automatically.

`TRAIL_DISABLED=1` turns every command into a no-op.

## Tests

```bash
python3 test_trail.py
```

## Not in scope

Assignees, priorities, due dates, dependency graphs, label taxonomies, search.
The read commands exist for visibility, not for management. Automatic decision
summarization is deliberately absent: the human stays in the loop.

## License

MIT
