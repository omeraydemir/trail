---
name: trail
description: Repo-local task ledger driven by the `trail` CLI — markdown task files in `.trail/tasks/` that carry work across sessions, and whose decision log records what was rejected and why. Use when resuming or continuing work that spans sessions, when a design decision with a rejected alternative is made, when handing off, or when closing a task. Turning a document, spec, backlog or brain dump into tasks is `/trail-plan`. Not for single-prompt work.
argument-hint: <slug> | status | notes | check <item> | block <item> "<why>" | log "<what>" --why <why> --dropped <alt> | note <finding> | write <section> | handoff | done | validate
---

# trail

**trail records why. Git records what.**

**Resuming:** `/trail <slug>`, then `trail resume <slug>`. That marks the task
active and prints its status in one step; passing the slug also names the session
after the work, where a bare `/trail` leaves every resumed chat titled the same.

Every writer targets whatever is in progress, so once you have resumed, nothing else
needs `--task`. Tasks are parked as `open` by planning, and `blocked` still counts as
in progress: with one active and one blocked task the writers take the active one.
Two of the same status and they refuse rather than guess — park one with
`trail set status open --task <id>`.

A task file exists to carry one piece of work across the sessions it takes to
finish. Git already holds every line that shipped; what it cannot hold is the
alternative that was considered and rejected, because rejected code is never
written. That is the `dropped:` field, and it is why the format exists.

Both halves imply the same test for everything below: **does this make the next
session cheaper to start?** A rule that adds ceremony without carrying context is a
bug in this tool, not a rule to obey harder.

trail sets no commit strategy and never reads git. What it asks is narrower: keep the
task's records current within the same piece of work you are doing, so the tick, the
log entry and the handoff travel with the change they describe. No separate "ledger
commit" ritual is prescribed.

## What goes where

| | |
| --- | --- |
| Must be in your head every session — goal, boundary, where you stopped, decisions | the **task file**; `trail status` digests it |
| What you consult when you get to that part — designs, specs, long plans | a **reference document**, linked with `trail link` |
| Small work you are **not** doing now | `.trail/backlog.md`, one line each |

Putting a two-week design inside a task file breaks the first row: the file stops
answering "where am I" and starts being something you scroll past.

## The CLI first, your hands second

Every field has a command that writes it, and the command is the better path: it
dates things, it never leaves a section half-written, it keeps `level:` honest.

| To write | Command |
| --- | --- |
| a decision | `trail log "<what>" --why "<why>" --dropped "<rejected alternative>"` |
| a finding, a measurement, anything worth carrying | `trail note "<what>"` → `## Notes` |
| `## Goal`, `## Out of Scope`, `## Plan`, `## Open Questions` | `trail write <section>` — body on stdin |
| a plan item's state | `trail check <item>` → `[x]`, dated · `trail check <item> --partial` → `[/]` · `trail uncheck <item>` → `[ ]` · `trail cancel <item> "<why>"` → `[-]` |
| a plan item that cannot move | `trail block <item> "<why>"` · `trail unblock <item>` |
| `## Status` | `trail handoff "<where you stopped + next step>"` |
| a reference doc or code path | `trail link <path…>` |
| `status`, `level`, `title`, `group` | `trail set <field> <value>` |
| a new task | `trail start <slug> [T1\|T2] [--status open] [--group <g>]` |
| picking one back up | `trail resume <slug>` — makes it active, prints its status |
| a small item you are deferring | `trail backlog "<item>"` — tagged `#<active task>` |
| closing | `trail done` — marks the task done, lists what is still open, reports the backlog around it |

`<item>` is an id — `ap-k4m2`, as `status` prints it — or a piece of the item's
text. One match acts. Zero or several are refused with the candidates listed, never
guessed: say which, by id. Ids come from `trail write plan`, which gives every
`- [ ]` line without one an `[id:: …]`. Never invent an id by hand and never change
one: the id is what keeps a reworded line the same item.

A long `--why` or `--dropped` goes on stdin, where `$` and quotes stop needing escapes:

```bash
trail log "styled_surface resolve" --stdin <<'EOF'
--why
first line of the reason
second line
--dropped
the alternative that was rejected
EOF
```

A line that is exactly `--why` or `--dropped` opens that field and runs to the next
label. Inline and stdin may mix for different fields, never for the same one.

**When the CLI cannot say what you mean, edit the file.** Fix a line, add a heading
the format does not have. The obligations are the ones that keep the file readable by
the tool: frontmatter stays valid YAML, section headings keep their names, the
decision log only ever grows, ids stay exactly as they are. Then `trail validate`: it
lists each problem with its fix, and `status` warns when the live task does not pass.
A rule you have to break to get work done is worse than no rule — and the previous
version of this file had one.

## Reading costs tokens. Climb, do not jump

Nothing is injected automatically — there is no hook. `trail status` is a **digest**
of the task file, not the file, and that is the point: it is the cheapest complete
answer to "where am I". Reading the file instead costs ten to forty times more, every
session, for detail you almost never need. So climb:

| You need | Run | Roughly |
| --- | --- | --- |
| where am I, what is next, what is blocked | `trail status` | ~15 lines |
| what the last session left in `## Notes` | `trail notes [-n N]` — last 5 by default, `--all` for every one | the entries, not the file |
| why a recent decision went that way | `trail status --full` | + the why/dropped bodies |
| the boundary, the open questions, the whole plan | `trail show <slug>` | the file |
| to edit a section by hand | read the file | the file |
| where a task you are *not* on stands | `trail status --task <slug>` | ~15 lines |
| which tasks exist, in what shape | `trail ls`, `trail board` — both narrow to the active task's group; `--all` or `--group <g>` to widen | a few lines |
| whether something was already decided, tried or rejected | `trail search <text>` — every task, the archive included | the matching entries |

`status` prints plan items as `[ap-k4m2] [/] text`, then picks for you. **Next** is
the first unresolved, unblocked item. **Can continue with** appears only when Next is
`[/]` — written, waiting on verification — and names the first `[ ]` after it:
parallel work while the check is pending, not a claim that Next is done. **Blocked**
lists every blocked item with its date and reason; a blocked item is never Next, and
when nothing else remains status says so rather than choosing one. It also nudges
when every item is resolved but the task is still active (`trail done`, or add what
remains to the plan) and when the file no longer passes `trail validate`.

Search with `trail search`, not with `rg`: this format's unit is an entry, not a
line. A decision's `why:` and `dropped:` are indented under a title line, so a
line-based match hands you the rejected alternative without the decision it belongs
to — and "have we already ruled this out?" is the question the decision log exists to
answer.

`status` prints decision **titles** only; a title plus `--full` on demand is the
difference between a 15-line session start and a 4,000-character one. It ends with a
`Not shown:` line counting the notes, open questions and older decisions it left out,
so nothing is invisible — you always know what you are choosing not to read. `trail
notes` sits before `--full` on the ladder because decision titles are already in the
digest and notes are not: that is the blind spot, and it is why notes used to be
written every session and read by nobody. Do not open the task file to "get more
context": name what you are missing and take the step that answers it.

## Rules

1. **Write the log entry when the decision happens, not at the end.** A decision
   recalled at session end is a lossy reconstruction. One line, immediately.
2. **`dropped:` is the point.** "What I did" is already in the code. What is lost is
   "what I rejected and why". Fill it whenever an alternative was considered — and
   only then; an invented alternative is worse than an empty field.
3. **While you are doing small work, write nothing.** That is T0 and it has no
   home by design: no file, no line, no command. The one promise this tool makes
   is that using it does not tax the 80% of work that is small — T0 acquiring any
   obligation breaks it. What goes to `trail backlog` is small work you are *not*
   doing: deferred, not finished.
4. **One task, not the repo.** The decision log carries a task's reasoning across
   the sessions that task takes. trail does **not** manage a repo-lifetime decision
   record: there is no `DECISIONS.md`, no distillation, and `done` files nothing
   anywhere. If something looks bigger than the task — a dependency added, an
   invariant someone will break later — **say so and offer**; whether it earns a
   permanent document under `docs/` is the user's call, and they will ask.
5. **Never summarize the session.** `trail handoff` rewrites `## Status`: where you
   stopped, what is next. The reasoning is already in the log.
6. **Tick the box when it is true.** `## Plan` items have four states: `[ ]` not
   started · `[/]` written but not verified · `[x]` **verified** · `[-]` cancelled,
   with why it fell out of scope in the text. `[x]` is not "I wrote the code";
   `trail check` writes it and dates it, so the next session reads the boxes instead
   of re-reading the code. Blocked is not a fifth box but metadata on the line,
   independent of the box — `[/]` + blocked is the normal shape of "written, waiting
   on something". So a blocked item is `trail block <item> "<why>"`: not `[-]`, which
   says it left the scope, and not a note repeating the plan line, which goes stale
   on its own. Never write `- [ ] 1. …`: a digit and a dot after the box start an
   ordered list inside the item and the checkbox stops rendering. A numbered step is
   `- [ ] **1.** …`.
7. **Decision or note?** Did you reject an alternative? → `trail log`. Anything else
   worth carrying — a measurement, a discovery, a thing you tried that failed, a
   detail from the conversation the next session would miss — → `trail note`.
   `## Notes` has no format and no rules; use it freely.

## Levels, and starting one task

**T0** small work — nothing, anywhere · **T1** 2-3 sessions · **T2** multi-day, and
its file carries a `## Plan`. Size decides whether there is a file; deferral decides
whether there is a trace, which for small work is one backlog line. One task starts
like this:

```bash
trail start <slug> [T1|T2]                 # active at once; --status open parks it
printf '%s\n' "<goal>"                   | trail write goal
printf '%s\n' "<boundary>"               | trail write scope
printf -- '- [ ] %s\n' "<step>" "<step>" | trail write plan    # assigns the ids
```

Several tasks from one source — a document, a spec, a backlog, a brain dump — is
`/trail-plan`. The splitting test, `group:`, ordering and the check of the document
against the code live there; do not improvise them here.
