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
| T0 | single session, cheap to undo | **nothing** — unless deferred, then one backlog line |
| T1 | 2-3 sessions, one topic | task file + close |
| T2 | multi-day, architectural | + a checkbox `## Plan` + handoff each session |

T0 must stay free. A process system dies from taxing trivial work, so small work
you are actually doing leaves no trace at all. `trail backlog` is for the other
case — small work you are *not* doing — and keeps it in the repo without giving it
a status, a board card or any lifecycle. Size decides whether there is a
file; deferral decides whether there is a trace.

Phases of one big task are not separate tasks unless they are worked separately.
The test is whether phase 3 needs phase 1's decisions in your head; if it does,
splitting only splits the context. Ordering between tasks that really are separate
goes in the slug — `auth-1-provider`, `auth-2-session` — which `ls` sorts for
free.

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

This creates `.trail/` (including an empty `backlog.md`) and two skills for whichever
agents the repo already uses: `/trail` resumes a task, works it, logs, hands off and
closes it — one task at a time — and `/trail-plan` turns a document or a brain dump
into tasks and backlog lines. Each is complete on its own, so a session loads one of
them. Agents disagree about where project skills live — Claude Code reads
`.claude/skills/`, while Codex, Cursor and Gemini CLI read `.agents/skills/` — so
`init` detects the marker directories present and writes to the right ones.

`init` never overwrites what is already there — `--force` refreshes a drifted skill
copy, and leaves your `config.yml` and `_template.md` alone.
Force it with `trail init --agent claude|codex|cursor|gemini|all`.

## Use

```bash
trail start deeplink-handling T1        # new task (--status open parks it for later)
trail resume deeplink-handling          # pick a parked task up: active + its status
trail backlog "android smoke test"      # small items, no ceremony
trail link docs/deeplink-design.md      # point the task at the design
trail log "route via AppLinks" \
     --why "Universal Links needs an AASA host we don't control" \
     --dropped "Universal Links"        # write it the moment you decide
trail log "route via AppLinks" --stdin <<'EOF'   # same entry, reasons too long to quote
--why
Universal Links needs an AASA host we don't control
--dropped
Universal Links
EOF
trail note "12 widgets, 9.6s cold, phases are serial"   # findings, free-form
trail notes                             # the last five of them (-n N, --all)
trail handoff "parser done, wiring the receiver next"
trail check "parse the URL"             # [x] + completion date; id or a piece of the text
trail check dh-k4m2 --partial           # [/] written, not verified
trail uncheck dh-k4m2                   # back to [ ]
trail cancel dh-k4m2 "handled upstream" # [-], reason after the text
trail block dh-k4m2 "AASA host not up"  # dated; the box stays as it is
trail unblock dh-k4m2
trail set status blocked                # status | level | title | group
printf 'one sentence\n' | trail write goal   # prose sections come from stdin
trail status                            # what am I doing, what went stale
trail status --task other-thing         # a task you are not on
trail ls --stale 7                      # untouched for a week
trail board                             # kanban, narrowed to the active group
trail board --all                       # every group
trail validate                          # every task file against the format
trail done                              # mark done, report the backlog around it
```

`## Plan` items are checkboxes — `[ ]` not started, `[/]` written but not verified,
`[x]` verified, `[-]` cancelled — and each carries an id that `trail write plan`
assigns (`[id:: dh-k4m2]`; never write one by hand). `status` prints
`[dh-k4m2] [/] …` and the item commands take the id or a piece of the text, so an
item is addressed without opening the file; `ls` reports the count, so "where did we
stop" is answered without opening anything. Prefer the commands, but the files are
yours: when the CLI cannot express what you mean, edit them, just keep the format
intact — `trail validate` says when you did not.

`trail ls`, `trail show` and `trail status` take `--json`.

`trail done` flips the status and prints a closing report. It copies nothing, moves
nothing and deletes nothing: the decision log is already permanent where it was
written, and the backlog's one promise is that an item you mentioned is still there
tomorrow.

**trail does not manage repo-lifetime decisions.** A task's log carries that task
across its sessions and then stops being the point. When a decision is too big for a
sentence — a dependency added, an invariant the next person will break — it wants a
real document under your own `docs/`, written when you ask for one. trail will point
at the candidate; it will not file it for you.

## One task or several

The task file is what every session starts by reading — as a `trail status` digest,
not the file itself — so it holds only what you need in your head: goal, boundary,
position, decisions. Anything you *consult* rather than
remember — a design, a spec, a long plan — lives in its own document under `docs/`
and is attached with `trail link`. Pouring a two-week design into `## Plan` breaks
the file and pollutes every session with detail you are not using yet.

When work has phases, the test for splitting is not size:

> When you sit down to phase 3, do you need phase 1's status and decisions in your
> head?

**Yes** → one T2 task, phases as checkboxes under `## Plan`. Ten phases still means
one file — splitting it splits the context you were trying to carry. **No** →
separate tasks, with order in the slug prefix (`auth-1-provider`, `auth-2-session`)
and a shared `group:` in the frontmatter. Tasks sort by `(status, id)`, so the prefix
orders them for free, and `ls` sections by group.

Neither answer is a default: splitting shared reasoning fragments the context the
file exists to carry, and merging independent work gives you one `## Status` for
three fronts plus a file too heavy to keep logging small things into. A plan
document's sections are a hypothesis, not task boundaries — test them.

`group:` is a label, not a parent: there is still no index file and no dependency
field. A hand-written cross-reference between tasks is stale within the hour.

## Layout

```
.trail/
  config.yml          optional
  _template.md        yours to edit
  backlog.md          deferred small work — a flat list, no lifecycle
  tasks/<slug>.md     every task, open through done — files never move
```

One artifact, one lifetime. A task file is written while the work happens and kept
afterwards; nothing is distilled out of it into a second place.

`.trail/` is committed by default. Working solo and want tasks off git? Add it to
`.gitignore` — but then nothing survives the session but the code.

Because tasks are committed by default, they are readable by anyone with repo
access: no credentials, customer identifiers or private notes in task files.

See [spec/FORMAT.md](spec/FORMAT.md) for the full format contract.

## Configuration

`.trail/config.yml` is optional; defaults apply when absent.

```yaml
backlog: .trail/backlog.md
dir: .trail/tasks
template: .trail/_template.md
stale_days: 7
```

Custom frontmatter fields go in `_template.md`, not in config. The CLI reads only
`id` `title` `level` `status` `started` `group` `links`; everything else is yours
and is preserved on write.

## Nudges

`trail status` derives state from disk, not from lifecycle events — nothing has to
have fired for the answer to be right.

- task file untouched for `stale_days` → *still active? close it or continue*
- every plan item resolved but the task still active → *close it, or add what is left*
- format problems in a live task file → *`trail validate --task <id>` lists them*
- a scaffold file this repo predates is missing → *run `trail init`*

Nudges only remind. Nothing is ever written automatically, and nothing is read from
git: trail runs no git command, so no nudge compares the code against the task file.
Keeping the records current while the work happens is the model's job, not a diff's.

`TRAIL_DISABLED=1` turns every command into a no-op.

## Tests

```bash
python3 test_trail.py
```

## Not in scope

Assignees, priorities, due dates, label taxonomies. Note ids, dependency graphs,
event history, automatic promotion of a note into a decision, a `--force` that
overwrites a recorded date or reason. The read commands exist for visibility, not
for management: trail carries context to the next session; it does not manage the
project. Automatic decision summarization is deliberately absent: the human stays in
the loop.

## License

MIT
