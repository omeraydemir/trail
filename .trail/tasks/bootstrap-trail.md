---
id: bootstrap-trail
title: trail'i kendi üstünde kullan
level: T1
status: active
started: 2026-09-09
links: []
---
# trail'i kendi üstünde kullan

## Goal
<!-- One sentence: what makes this done. -->

## Out of Scope
<!-- An explicit boundary against scope creep. -->

## Decision Log
- 2026-09-09 · CLI v1 formatı 2 hafta elle kullanmadan yazıldı · why: elle kurulum istenmedi; tek kullanıcı olduğu için format değişikliği ucuz · dropped: spec'in önerdiği 2 haftalık elle kullanım fazı
- 2026-09-09 · Kurulum ayrı clone yerine çalışma reposuna symlink · why: tek kullanıcı; düzenleme anında canlı, iki kopya senkronu yok · dropped: ~/.local/share/trail'e ikinci clone (README'deki genel yol)
- 2026-09-09 · SKILL.md hedefi ajana göre ayrışıyor: .claude/skills vs .agents/skills · why: Claude Code .agents/skills okumuyor, belgeyle doğrulandı; tek evrensel yol yok · dropped: .agents/skills'i tek kaynak varsaymak

## Status
v0.1.0 push edildi, symlink kurulu. Sıradaki: gerçek işte kullan, format aksaklıklarını buraya yaz. Hook'lar henüz yok.

## Open Questions
