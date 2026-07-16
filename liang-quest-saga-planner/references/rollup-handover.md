# Phase 7 — Handover View

Load when running --handover; source of truth for this mode.

**Presentation layer only.** Renders the two saga-level rollups — `uat-checklist.md` (Phase 5) and
`walkthrough.md` (Phase 6) — into a single self-contained `<saga-dir>/handover.html` the user reads
in a browser. The two markdown files stay the source of truth: agents parse them, checkbox state
lives in them, executor re-runs regenerate them. The HTML is a disposable view — regenerated whole
from the markdown every time, never edited by hand, never a state surface (checked/unchecked
renders as static text), never collected or parsed by any downstream skill.

1. **Ensure fresh sources.** If `<saga-dir>/uat-checklist.md` is missing, run Phase 5 first; if
   `<saga-dir>/walkthrough.md` is missing, run Phase 6 first. If the user says either is stale,
   re-run that phase before rendering — never patch the HTML around stale markdown.
2. **Render with the planner's Phase 2c machinery** — same body-drafter pattern, same
   class contract, same `assemble_plan.py` + the saga `skin` (the page joins the `saga.html` /
   `plan.html` visual family). No bespoke CSS. The handover-shaped mapping onto the contract:
   - One `section.quest` per **tour stop** (campaign), topological order, `id="c01"`…; TOC heading
     "Tour Stops"; eyebrow "Stop NN · <passed>/<total>"; `diff-badge` = the campaign's saga-level
     difficulty; `dep-state` = `<passed>/<total> · depends: <ids>`.
   - Per stop: purpose = the walkthrough's stop summary; steps = its highlight and see-it-run
     observation items (static text — no live checkboxes); footer deps col = campaign
     dependencies, second col heading "Outstanding debt" = the UAT sessions gating this stop, each
     linking `uat-checklist.md` § that session. Fully-passed stops say "none".
   - Exactly one `diagram-section` between TOC and main: the **UAT session unlock chain** (nodes =
     sessions in order, `.is-active` = next actionable, `.is-muted` = blocked, plain = done;
     legend names each session's `[MANUAL]`/`[AGENT]` tag).
   - Notes section: cards for shared Blockers and the walkthrough's quick-start tour (if present);
     the `notes-wide` table = session index — one row per session, pill = its state
     (`pill-recommended` done / `pill-deferred` next / `pill-rejected` blocked), plus the wrap-up
     reminders from the checklist's final section.
   - Depth is LEAN: summaries and links into the two markdown files — never the full checklist
     item text duplicated into the page.
3. **Assemble** with `assemble_plan.py` to `<saga-dir>/handover.html` (title "<Saga Title> —
   Handover"), delete `_body.html`, auto-open in the browser, announce the path.
4. **Regenerate on demand** — after any `--uat`/`--tour` re-run, offer a one-line "re-render
   handover.html?"; regeneration is cheap and the file is safe to delete at any time. **Never**
   flip quest statuses, edit campaign folders, or write anything but `handover.html` from this
   mode.
