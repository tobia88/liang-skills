# Grounding Protocol

Shared grounding gate for all liang-brainstorm-* skills. Before the model emits concrete options about a named artifact, it must have *read that artifact* and shown the evidence. Successor to `scout-rules.md`'s startup-scout step — scout says what is *safe* to read; this says what you *must* read and how you prove it.

## Principle

**Options about a named artifact are outputs of reading it, not substitutes for reading it.** No option set that names or depends on a concrete artifact may ship before that artifact is read — or the gap is declared out loud. Grounding is a precondition for option generation, never an afterthought.

## The Grounding Gate

The gate blocks the **first option set** of the session. Until it opens, do not emit ABCD options. It opens only when one of:

- **Grounded** — the seed's named artifacts and their direct neighbors have been read (see *Read depth*) and the evidence shown (see *Rendering*); or
- **Waived** — grounding is impossible or inapplicable, declared explicitly and acknowledged once (see *The Waiver*).

A scout summary is **not** a grounding receipt — paraphrasing injected context (CLAUDE.md, memories, prior reports) and calling it a scout does not open the gate. Only *files actually read this session* count.

## Read depth

Read the artifact(s) the seed names, **plus one hop out**:

- the header + implementation pair (both, not one);
- the base class it derives from;
- direct subclasses;
- same-folder siblings;
- a search of the named symbol's call sites / usages.

One hop, not the whole subsystem — honor `scout-rules.md`'s anti-dump stance. The hop catches the local idiom a single-file read misses.

## Source-of-truth hierarchy

Not all readable text is valid grounding.

- **Live source / live assets** — authoritative. Code, actual asset contents, real `SKILL.md` files. The only thing that can *back* an option.
- **Status / state records** — authoritative about execution state: what actually landed, built, or ran (quest-status dashboard, CI result, deployment state).
- **Plans / intent docs** — **leads only, never cited as truth.** Roadmaps, design docs, intel notes, campaign markdown, brainstorm reports. Read them to find *where to look* and *what was intended* — never to assert *what is*. They drift the moment code moves. (Liang's `.liang/phases/`, `.liang/intel/`, `.liang/brainstorm-reports/` are this tier — treating "planned, not executed" as a fact about current state is the exact drift this forbids; grep live source to confirm first.)

Those paths are *examples*, not the rule. Portable rule: prefer live source; accept factual state records; treat anything describing *intent or plan* as a lead to verify, not a fact to cite.

## The Waiver

When grounding is **impossible** (the host exposes no file-search/read tools) or **inapplicable** (the seed names no concrete artifact — a purely abstract topic), the gate is waived, but never silently:

1. **Say so plainly.** "No code artifact named — proceeding ungrounded," or "This host has no file search; paste the artifact and I'll ground on it."
2. **Get a one-time acknowledgement** before proceeding.
3. **Cap everything at `Low` / hypothesis** until the user supplies context (e.g. pastes the code), at which point normal grounding resumes.

Silent degradation is forbidden — an unannounced ungrounded session is the original failure in disguise.

## Just-in-time reads

The gate guards the opening; these keep every later turn honest.

- **Read on demand.** Before emitting any option set that names or depends on an artifact not yet read this session, read it first (same one-hop depth). Fires only when a *new* artifact enters — read-on-demand, not grep-every-turn.
- **Confidence is the trigger.** About to attach anything above `Low` to an option that rests on an unread artifact? That is the signal to read it now — or drop the option to `Low` and label it an explicit hypothesis. The Confidence field is precisely where ungrounded guesses get laundered; bind the read to it.

## Rendering

Grounding is shown, not claimed — in a form the user can spot-check against the real files.

**Opening read-receipt** — replaces any prose "scout summary," using this exact fenced template:

```text
Grounding:
- Named: <artifact(s) the seed referenced>
- Read: <file paths actually opened this session>
- Found:
  - <path> — <one-line FACTUAL finding, checkable against the file>
  - <path> — <…>
- Gate: GROUNDED   (or: WAIVED — <reason>)
```

The per-file *finding* line is load-bearing: a bare path list proves nothing (a file can be listed but skimmed) and free prose is the exact shape of a fabricated scout. One falsifiable fact per file ("`SoEEncounterMeterWidget.h` — only `SetMeter(float,float)` + one BIE; no bind/init ritual").

**Per-set footer** (full form only): every option set ends with one line —

```text
Grounded in: <file1>, <file2>
```

— so a skipped grounding renders as a visible `Grounded in: (nothing)` rather than hiding in silence.

## Forms — full vs collapsed

The host skill selects the form by its identity (mirrors `alignment-protocol.md`):

- **Full form** — hard gate at open with the read-receipt; a `Grounded in:` footer on *every* option set; just-in-time reads throughout; ungrounded options capped at `Low`/hypothesis. For depth-oriented sessions (`liang-brainstorm-relentless`).
- **Collapsed form** — ground **once** at open (read-receipt shown), keep the gate, the waiver, the source hierarchy, and on-demand just-in-time reads when a new artifact becomes load-bearing — but **drop the per-set footer** ritual. For fast/short sessions (`liang-brainstorm-quick`).

The **only** difference between the forms is the per-set footer: full emits it on every option set, collapsed omits it. Everything else — the gate, the opening read-receipt, the waiver, the source hierarchy, just-in-time reads, and the `Low`-cap on ungrounded options — is **shared by both**.

## Tool-agnostic note (Pi portability)

Phrase every grounding action in host-neutral terms — "search and read with whatever file tools the host exposes." Different models under Pi may lack a specific search/read tool; when none exists, the path is the Waiver (ask the user to paste the artifact), not a silent skip. Keep workspace-specific paths (`.liang/...`) as examples, never the rule, so the protocol holds for any project.

Source: authored for the grounding-gate redesign; trimmed for density (rationale condensed, rules and format blocks preserved verbatim). Relentless runs the full form, quick the collapsed form. Successor to `scout-rules.md`'s startup-scout step.
