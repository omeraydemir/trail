# Format contract

Everything trail does is defined by these files. The CLI is replaceable; the format
is the product.

## Layout

```
.trail/
  config.yml          optional; defaults apply when absent
  _template.md        task template, user-editable
  backlog.md          small items; a flat list, no frontmatter, no lifecycle
  tasks/<slug>.md     every task, open through done — files never move
```

`trail init` also drops two skills where the repo's agents look for project skills:
`trail/SKILL.md` (`/trail` — resume, work, log, close, start one task) and
`trail-plan/SKILL.md` (`/trail-plan` — a document or brain dump into tasks and backlog
lines), under `.claude/skills/` for Claude Code and `.agents/skills/` for Codex,
Cursor and Gemini CLI. There is no single path every agent reads, and no single skill
either: each file is complete for its own scenario, so a session loads one of them.

trail keeps no second, repo-lifetime record. A decision log belongs to its task and
stays in its file, which is now permanent; four closes across two real repos produced
four untrimmed copies of the same content in a `DECISIONS.md` nobody ever distilled.
What deserves to outlive the task is a document the user asks for, under the repo's
own `docs/`, and that is theirs to decide — trail may point at the candidate, never
file it.

`.trail/` is committed by default. Solo users who want tasks off git add it to
`.gitignore`; the two-lifetime split survives either choice.

## Task file

```markdown
---
id: push-notification-deeplink
title: "push notification: deeplink"
level: T1
status: active
created: 2026-08-25
started: 2026-08-27
completed:
group: notifications
links:
  - src/Notifications/DeepLinkHandler.cs:120
---
# push notification deeplink

## Goal
## Steps
## Out of Scope
## Status
## Notes
## Decision Log
## Open Questions
```

The order is the reading order. A person opening this file asks "what is this, what
is left, where am I" — in that sequence, and the answer to each has to be above the
fold. Goal and Steps sit together because they are the same question at two
resolutions. `## Out of Scope` is a guardrail you consult, not a thing you act on, so
it follows them. The decision log is long and archival, so it sits below everything
you came for.

### Core fields

`id` · `title` · `level` · `status` · `created` · `started` · `completed` · `group` ·
`links` are the only fields the CLI reads. Everything else is free — add fields to
`_template.md` and nothing breaks.

- `title` is **always written quoted**. Titles carry colons ("Report: pivot matrix")
  and a bare colon makes the whole block invalid YAML — which is how two of the five
  files in the first real ledger stopped opening in every other tool.

- `status` is one of `open` · `active` · `blocked` · `done`. The set is closed:
  board columns derive from it.
- `level` is `T1` or `T2`. T0 has no task file and no representation anywhere:
  small work being done now leaves no trace. `backlog.md` holds the other case,
  small work that is deferred.
- `created` is the day the task file was made. `trail start` writes it once, and
  nothing changes it afterwards.
- `started` is the first day the task became `active`, written by whichever of
  `trail start`, `trail resume` or `trail set status active` gets it there first and
  never overwritten — parking the task again keeps it. It is not the creation date: a
  task a planning run parks as `open` can wait weeks before anyone picks it up, and a
  `started` that meant "created" put it weeks into its work on the day it began.
  `resume` on a task already `active` with no `started` writes nothing; the real day
  is unknown, and today would be false data.
- `completed` is the day the task was closed, written by `trail done`. Closing a task
  that is already done keeps the recorded date; `trail set status` moving it out of
  `done` clears it. A `completed` on a task that is not done is reported; a closed
  task without one is not — closes from before the field have no known date, and
  inventing one is false data.
- `group` is an optional slug shared by the tasks one `plan` run produced. It is a
  label, not a list of children: nothing points at anything, so nothing goes stale.
  `ls` sections by it, and anything reading frontmatter from outside — a Dataview
  query in an Obsidian vault, a script — can select on it.
- `links` is a flat list of repo paths, optionally `path:line`. Not validated.
  It is how a task points at the design or plan document or the code it concerns;
  `trail done` lists the `.md` ones (see *What belongs in a task file*).

There is still no parent task, no subtask, no dependency graph and no index file
listing children. `group` carries the only relation that survived contact with real
use: *these came from the same plan*.

### Steps are checkboxes

```markdown
- [x] measure the run shape on device [id:: ap-3f1k] [completion:: 2026-09-11]
- [/] classify ErrorCode into messages [id:: ap-k4m2]
- [ ] wire the audio player [id:: ap-9zzz] [blocked:: 2026-09-15] [blocked-reason:: audio file not ready]
- [-] landscape mode — portrait-locked natively on both platforms [id:: ap-x7q9]
```

| | |
| --- | --- |
| `[ ]` | not started |
| `[/]` | written, not verified — the state that has no name in prose and therefore gets lost |
| `[x]` | verified. Not "I wrote it": verified. `trail check` dates it with `[completion:: YYYY-MM-DD]`, and the validator wants the date on every `[x]` |
| `[-]` | cancelled — the item stays, with why it fell out of scope as prose after the text (`— reason`). No field for it, by decision: new syntax only when something has to query it |

The box is progress and nothing else. Blocked is not a fifth state but metadata on
the line, independent of the box: `[/]` + blocked is legal — written, waiting on
something before it can be verified — while `[x]` or `[-]` + blocked is a
contradiction the CLI refuses to create and the validator reports.

The bracketed fields are Dataview's inline-field syntax, `[key:: value]`, so an
Obsidian vault queries them without a plugin. trail owns exactly four:

| Field | Written by | Present when |
| --- | --- | --- |
| `id` | `trail write steps`, or an item command that rewrites an id-less line | always, once the CLI has seen the line; the validator reports a line without one |
| `completion` | `trail check`; removed by `check --partial`, `uncheck`, `cancel` | the item is `[x]` |
| `blocked` | `trail block`; removed by `trail unblock` | the item is waiting; the value is the date it started waiting |
| `blocked-reason` | `trail block`, alongside `blocked` | whenever `blocked` is. One line, no `]` — an inline field cannot nest a bracket |

An id is `<initials of the slug's parts>-<four random [a-z0-9]>`: the task
`auth-provider` gets `ap-k4m2`, `user-1-profile` gets `u1p-9x7b`. `trail write steps`
assigns one to every checkbox line that has none, and an item command that rewrites
an id-less line assigns one on the way (its report says `· id assigned`). Once written
an id never changes — the prefix is not checked against the slug afterwards, so a
task can be renamed or its steps copied without touching them — and it is unique
within one file, nowhere else. Never write one by hand: the validator reports a
malformed or duplicated id, and the CLI regenerates nothing.

Ids exist so that a step can be addressed from the CLI without opening the file.
The text is what a person reads, and it changes — reworded, translated, given a
reason — while the id is what a command and a `status` line point at, and it does
not.

The fields are read from anywhere on the line and written back after the text;
fields already on the line keep their order, new ones are appended — except an id
assigned on the way, which leads them, as `write steps` writes it. Any other
`[key:: value]`, a `[[wikilink]]`, an HTML comment — all text, preserved byte for
byte. Only `- ` bullets are items (`* [ ]` is a list to Markdown and nothing to
trail); indented checkboxes are items too; a fenced code block inside `## Steps`, and
inline code on an item's line, are opaque whatever they contain; `X` reads as `x`.

Nothing else goes between the box and the text. `- [ ] 1. Measure first` opens an
ordered list *inside* the task item, which is not what it looks like and breaks
checkbox rendering; if an item needs a number, write it as text — `- [ ] **1.**
Measure first`.

This is the whole set. The next session reads the boxes instead of re-reading the
code, and the reader learns what is left without cross-referencing `## Status`
against a prose list. `ls` reports `verified / live` per task, where `[-]` leaves the
denominator — cancelled is resolved, not pending.

### Step commands

```bash
trail check <item>              # [x] + [completion:: today]
trail check <item> --partial    # [/]; drops the completion date
trail uncheck <item>            # [ ]; drops the completion date
trail cancel <item> ["<why>"]   # [-]; the reason lands after the text
trail block <item> "<why>"      # [blocked:: today] [blocked-reason:: why]; box untouched
trail unblock <item>            # removes the two blocked fields, nothing else
```

`<item>` is an id or a piece of the text, resolved in that order: an exact id first,
then a case-insensitive substring of the item text with trail's fields stripped. One
hit acts. None, or several, is refused with the candidates listed as `[id] [s] text`
and nothing written — picking one would be a guess dressed as a command. Resolved
items are candidates too, because filtering them out would be a guess as well. The
commands take `--task <slug>` like every other writer and otherwise target the task
in progress. A change is reported as
`<task>: [<id>] [<old>] -> [<new>] <text> · <detail>`.

A box change never clears a block as a side effect, and a block never resolves a
box. `check` and `cancel` refuse a blocked item — unblock it first — and `block`
refuses a resolved one. `check --partial` and `uncheck` are allowed on a blocked
item; that is the `[/]` + blocked case above.

What already holds is a no-op; what would overwrite a record is a refusal; the two
look different on purpose. `check` on an `[x]`, `unblock` on an unblocked item,
`cancel` without a reason on a `[-]`: exit 0, "nothing changed", the recorded date
stays. `block` on a blocked item, `cancel` with a reason on a `[-]`: exit 1, the
recorded value shown, the file untouched — a completion date or a reason someone
wrote down is not replaced by a command that did not know it was there. There is no
`--force`. Replacing a reason is two explicit steps —
`trail unblock <id> && trail block <id> "<reason>"` — and the refusal prints them.

`trail status` derives its view from the boxes and the fields. **Next** is the first
unresolved item that is not blocked. When Next is `[/]` — written, waiting on
verification — **Can continue with** offers the first non-blocked `[ ]` after it:
work that can go on meanwhile, not a claim that Next is done. **Blocked** lists every
unresolved blocked item with its date and reason; a blocked item is never Next. When
nothing is open the line says which kind of nothing:
`Next: none - every remaining item is blocked` holds the steps open,
`Next: none - every step is resolved` means it is time for `trail done`.

### Writes are serialised

The log only ever grows, and that is a guarantee, not a description. Every writer
re-reads the file under an exclusive lock (`.trail/.lock`) and replaces it atomically.
Without that, two agents in one checkout silently lose entries while both commands
report success — fifty concurrent writes landed forty.

### Decision log entry

```markdown
- **2026-09-11** · fullscreen is a pushed page, not a modal
  - **why:** nothing in the repo uses PushModalAsync; a pushed page gets the
    hardware back button for free
  - **dropped:** the plan document's "(modal)" note — a second navigation pattern
    with no precedent in the module
```

One scannable title line, the reasons indented under it. The old one-line form put
`why:` and `dropped:` inside a 600-character sentence, where finding either meant
reading all of it. `dropped:` is still the reason the format exists.

A reason may run to several lines: the first sits after its label, the rest continue
indented four spaces, as above, and blank lines inside a reason are dropped — an
entry is a block, not an essay. `search` and `status --full` read the block as one
entry. Reasons that long do not survive a shell argument, so `trail log` also takes
them from stdin:

```bash
trail log "styled_surface resolve" --stdin <<'EOF'
--why
first line of the reason
second line
--dropped
the alternative that was rejected
EOF
```

A line that is exactly `--why` or `--dropped` opens that field; everything up to the
next label is its body. The labels are the flags themselves, so there is nothing new
to learn and no line of prose looks like one, and the quoted `'EOF'` keeps the shell
out of the text. Inline and stdin mix for different fields — `--why "short" --stdin`
with only `--dropped` on stdin. Refused, because the split has to be deterministic:
non-blank text before the first label, a label given twice, no label at all, an empty
body under a label, and a field given both inline and on stdin.

### `## Notes`

Free-form, append-only, dated by `trail note`. Nothing prescribes its shape.

It exists because the first real ledger pushed twenty-eight lines of measurements and
findings into the backlog for want of anywhere else to put them. A measurement is not
deferred work and it is not a decision; without a home it lands in whichever section
is nearest.

`trail notes` prints the last five entries verbatim, a multi-line entry whole (`-n N`
for more, `--all` for everything). `status` counts them and never prints them, so the
reading ladder is `trail status` → `trail notes` → `trail status --full` →
`trail show`: each step buys more of the file, and a session stops at the first one
that answers.

## What belongs in a task file

The task file is what every session starts by reading — through `trail status`, which
prints a digest of it rather than the file itself. Nothing is injected automatically;
trail ships no hook, on purpose. A session-start injection would put task context in
front of off-task work too, and the cure for a forgotten handoff is not poisoning
every unrelated session with it.

That constraint — read once per session, cheaply — is what divides the material:

| | Lives in | Read at session start |
| --- | --- | --- |
| What you must hold in your head each session — goal, boundary, position, decisions | the task file | yes, as a digest |
| What you consult when you reach that part — designs, specs, long plans | a reference document | no, linked |

`links:` is that bridge. A two-week design poured into `## Steps` breaks both halves:
the file stops answering "where am I", and the detail is re-read every session.

A reference document lives under the repo's own docs convention, never inside
`.trail/` — a different lifetime. trail links such a document; it does not own it.

Whether the two drift depends on the document. A design document does not overlap the
task file: it holds the design and changes rarely, the task file holds the position
and changes constantly, and a design change is one `trail log` line (why) plus a
document edit (what it now is). A plan document does overlap it — it says what is
done and what comes next, which is the task file's status — and it drifts: in a real
repo one still read "analysis, no code written" after the nine tasks that carried it
out had closed. The status a plan document records changes when a task closes, so
that is the moment to bring it back in line: `trail done` lists the task's linked
`.md` documents (linked code and prototypes carry no status) as a reminder to update
whichever one states that status. It writes nothing to them; trail links a document,
it does not own it.

## Splitting work across task files

The test is not size and not phase count:

> When you sit down to phase 3, do you need phase 1's status and decisions in your
> head?

- **Yes** → one T2 task, phases as checkboxes under `## Steps`.
- **No** → separate tasks sharing one `group:`.

Neither answer is the default, because both errors are real and they are opposite.
Splitting work that shares its reasoning fragments the context the file exists to
carry. Merging work that does not gives you one `## Status` for three independent
fronts — it can describe none of them — and a file heavy enough that the small
entries stop being written, which is the material worth keeping.

So the failure is not a count, it is skipping the question. **A document's sections
are a hypothesis, not task boundaries**: a plan document is organised for reading, a
ledger around what has to be in your head at once. They sometimes coincide. Test it
rather than assuming either way.

Splitting is cheap only because `group:` exists. Order still lives in the slug prefix
(`auth-1-provider`, `auth-2-session`) — tasks sort by `(status, id)`, so the prefix
carries it for free — and the relation lives in `group:`, which the readers use to
narrow themselves: `ls` and `board` show the active task's group and take `--all` or
`--group <g>` to widen. Without it a ledger of forty tasks prints forty rows at every
glance, which is the opposite of what this format is for.

Still no `after:`, no parent, no subtask, and no index file listing children. An index
is a cache of a view: `ls` and `board` derive it on read and cannot be wrong, while a
stored copy has a second source of truth and task files are hand-editable.

## Template placeholders

`trail start` substitutes `{{id}}` `{{title}}` `{{level}}` `{{status}}` `{{date}}`.
**Unrecognized placeholders are left untouched**, so custom fields are safe.

The three dates are not placeholders. The CLI writes `created`, `started` and
`completed` itself, the way `start` writes `title` and `group`, so the template only
says where they sit — and an older template's `started: {{date}}` still comes out
right. `{{date}}` remains a placeholder for the body.

## Config

Flat YAML. Keys: `backlog` `dir` `template` `stale_days`, plus the legacy `archive`,
still read. Unknown keys are ignored.

`archive` is retired. Closing a task sets `status: done` and leaves the file where it
is: paths stay valid for everything that links to them, and the closed task — the one
file that records what was verified and what was deliberately left undone — stays
visible. Readers still load a legacy `archive/` directory if one exists; nothing new
is ever written there. `ls` hides `done` unless you pass `--all` or ask for it by
status.

## Parsing rules

trail reads a controlled subset of the file and passes everything else through: the
frontmatter, the known `##` sections (found by heading), the checkbox lines inside
`## Steps`, and on those lines the four inline fields. Prose under a heading, a `###`
sub-heading, an HTML comment, a wikilink, an inline field trail does not own, a
fenced code block — opaque, and preserved byte for byte. The file is hand-editable,
so the CLI has to be a guest in it.

Frontmatter is read with a flat YAML subset: scalars, `- item` lists, `#` comments.
A key with an empty value reads as an empty list.

**Writes are surgical.** A command replaces a single frontmatter line by regex, one
section body, or a single step line — never a file reserialised from what the parser
understood, which would drop every comment and normalise every line it had merely
read. Comments, ordering and fields it does not understand survive untouched.

## Validation

`trail validate` checks every file in `.trail/tasks/` (a legacy `archive/` is
skipped; `--task <slug>` narrows to one) against this contract and nothing more: the
frontmatter, the required sections, the steps and their fields. It is not a
Markdown linter. `## Notes` has no rules, the decision log and the backlog are not
checked, and a section or field the CLI does not read is not its business.

Every finding is an error — one severity, because a file either round-trips through
the CLI or it does not:

| Where | Findings |
| --- | --- |
| frontmatter | block missing; `id` `title` `level` `status` `created` missing or empty; `id` not the file name; an unquoted `title` that is not valid YAML; `level` not T1/T2; `status` outside the set; `created`, `started` or `completed` not a date; `completed` on a task that is not done; `links` not a list |
| sections | one of the seven required headings missing or repeated — order is not checked, the CLI does not depend on it |
| steps | a `*`/`+` checkbox bullet; an unknown box state; empty text; the `1.` ordered-list trap; a trail field twice on a line; an empty field value; an id missing, malformed or duplicated; `[x]` without `completion`; `completion` on a non-`[x]`; a date that is not `YYYY-MM-DD`; `blocked` without a reason, or a reason without `blocked`; blocked on a resolved item |

Output is grouped per file, each finding with its line and the command that fixes
it; exit 1 when anything is found, `ok: N task files valid` otherwise:

```
.trail/tasks/auth-provider.md
  line 18: [x] has no [completion:: ] date
           fix: trail uncheck <id> && trail check <id> re-dates it, or add [completion:: YYYY-MM-DD]
  line 21: step has no [id:: ]
           fix: `trail write steps` assigns ids to lines without one (re-pipe the section); do not invent ids by hand
2 problems in 1 of 3 task files
```

Nothing is repaired and there is no legacy migration: a file from before ids is
brought up by hand — re-pipe its steps through `trail write steps` — and the validator
describes the target format rather than guessing at the origin. A live task that
fails is also one line in `trail status`; see Nudges.

## Nudges

Derived from disk state at session start, not from lifecycle events — nothing has
to have fired for the state to be correct.

| Condition | Signal |
| --- | --- |
| Abandoned task | task file mtime older than `stale_days` |
| Steps finished, task not | every item `[x]` or `[-]`, none blocked, and the task still `active` — one of the two is stale, and only a person knows which. Trail data only: not git, not the clock |
| Format problems in a live task | `trail validate` finds anything in an active or blocked task file; one line, naming the command |

trail never runs git — no commits, no `HEAD`, no history, and no freshness derived
from it — so no nudge can say "you worked and did not log". That is the model's job:
it keeps the task's records current within the same piece of work, which is the only
place a missing log line can still be caught.

Nudges only remind. Nothing is written automatically.

`TRAIL_DISABLED=1` makes every command a no-op, so a one-off session in someone
else's repo is never hijacked.

## Backlog

```markdown
- [ ] ask backend whether AppPageType=18 is empty #report-api
- [x] archive the temporary PoC checklist #report-api
```

`backlog.md` holds deferred small work — never work in progress. It is a sink, not a
tracker: a flat markdown list, no frontmatter, no ids, no lifecycle beyond the box.
`trail status` reports the open count and never the contents; injecting them would
turn the file into a graveyard that rots in every prompt.

Each line is a checkbox and carries the `#<task-slug>` of the task it came out of, so
a line can be traced back to its work and queried from outside. `trail backlog` tags
with the active task unless you pass `--untagged`.

`trail done` **reads** the backlog and changes nothing in it: it reports how many
tagged lines are open and how many are ticked, and names the open ones. Closing a
task is not a reason to delete what someone wrote down — the first real close left
two open items behind on purpose ("error path untested", "never tried on Android"),
and a sink that empties itself is not a sink.

The tag must match a whole token: `#auth-1` does not match `#auth-1-extra`.

Growth is expected; the failure signal is the opposite. Backlog lines describing work
that was already done mean the boundary leaked and T0 started paying a tax. Lines
describing *measurements* mean `## Notes` is not being used.

## Not in scope

Note ids, dependency graphs, event history, automatic promotion of a note into a
decision, and a `--force` that overwrites a recorded date or reason. Each is a
task-manager feature, and trail is not one: it carries context to the next session;
it does not manage the project. What a manager would store, `status` derives on
read; what it would automate, the human still decides.
