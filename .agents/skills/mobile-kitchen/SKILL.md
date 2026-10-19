---
name: mobile-kitchen
description: Design and extend the Little Basket mobile grocery planner, its recipes, and its visual system. Use for UI, UX, recipe organization, and grocery-list changes in this repository.
---

# Little Basket mobile design

This is a project-specific skill written for this repository. It is not a copied preinstalled UI/UX skill. The installed visual-design reference is preserved verbatim in [references/installed-visual-design.md](references/installed-visual-design.md); see [references/PROVENANCE.md](references/PROVENANCE.md).

## Workflow

- Read `README.md` and the current standalone `little-basket.html` before making changes.
- Use the existing isolated checkout. Do not create a Git worktree unless explicitly requested.
- Keep the deliverable a self-contained HTML file that works without a network connection or build step.
- Preserve existing local-storage data. If its structure changes, supply a migration and retain import/export compatibility.

## Visual direction

- Rice-white background, olive-green actions, ink-green text, muted terracotta accents.
- Use roomy ingredient illustrations, clear Chinese labels, subtle rules, and restrained shadows. Avoid dense text, gratuitous gradients, or unrelated stock imagery.
- Use consistent inline SVG icons; food emoji supplement labels rather than replace them.
- Let recipes lead to groceries in one tap. Keep advanced recipe instructions and data management behind intentional actions.

## Mobile UX

- Start at 360–390 px; support 320 px through wide desktop layouts without horizontal page scrolling.
- Use touch targets of at least 44 px, 16 px form fields, safe-area padding, and a reachable bottom navigation.
- Keep checked purchases, ingredients already at home, and ingredients needing replenishment distinct.
- Merge shared ingredient identities. 排骨 and 煲汤骨 are interchangeable here. Do not add 山药汤.
- State serving assumptions. Do not silently invent the user's preferences or cupboard contents.
- Preserve user-provided recipes. Label supplementary cooking guidance as reference material.
- Keep new recipes maintained through conversation and built-in source data. Preserve readable methods, local method editing, and offline backups.
- Keep each shopping trip separate from persistent stock levels and dated purchase history. Resetting a trip must never reset either.
- Long-lasting supplies use manual remaining-level sliders. Recipe selection never invents consumption. Recent purchases need a clear confirmation before buying again.

## Verify

- Run `python3 tests/test_app.py` (requires Playwright and Chromium).
- Test recipe selection, merging, pantry exclusion, purchase progress, persistence, recipe editing, and export/import.
- Inspect mobile and desktop screenshots. Check keyboard focus, dialog dismissal, contrast, and reduced-motion behavior.
