---
name: trail
description: Task ledger for this repo. Use when starting multi-session work, when a design decision is made, when resuming work, or when closing a task. Records decisions at the moment they happen so no end-of-session summary is needed.
---

# trail

Tasks live as markdown files in `.trail/tasks/`. The valuable part is not the task
list — it is the `## Decision Log` inside each task, and specifically the `dropped:`
field, which records the alternative that was rejected and why.

Always work through the `trail` CLI. Never hand-edit frontmatter.

## When to use which command

| Situation | Command |
| --- | --- |
| Starting a session | `trail status` — read the active task before anything else |
| A decision was made | `trail log "<decision>" --why "<reason>" --dropped "<alternative>"` |
| Work is being paused | `trail handoff "<where you stopped + next step>"` |
| Task is finished | `trail done` |
| Starting work that spans sessions | `trail start <slug> [T1\|T2]` |
| Need an overview | `trail ls`, `trail ls --stale 7`, `trail board` |

## Rules

1. **Write the log entry when the decision happens, not at the end.** A decision
   recalled at session end is a lossy reconstruction. One line, immediately.
2. **`dropped:` is the point.** "What I did" is already in the code. What is lost is
   "what I rejected and why". Fill it whenever an alternative was considered.
3. **Do not create a task for small work.** Single-prompt, cheap-to-undo work is T0:
   no file, no command. Ceremony scales with task size.
4. **Never distill into `DECISIONS.md` yourself.** `trail done` appends the raw log
   and the human trims it. Getting this wrong is expensive.
5. `trail handoff` rewrites `## Status` only. Do not write a new summary of the
   session; the log already holds the reasoning.

Levels: **T0** no file · **T1** 2-3 sessions, one topic · **T2** multi-day, adds a
`## Plan` section. Upgrading T1 to T2 is one line: change `level:`, add the heading.
