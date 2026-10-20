# Little Basket

For UI, UX, recipe, or grocery-list work, read `.agents/skills/mobile-kitchen/SKILL.md`.

Project-installed design capabilities are documented in `design/capabilities/README.md`, with exact commits and file checksums in `design/capabilities/capabilities.lock.json`. Read the selected skill's full instructions before using it. Use `design-taste-frontend` (app-screen route) and `frontend-design` as the main design workflow for this application. Other styles are alternatives, not cumulative requirements. Do not combine incompatible visual styles or automatically invoke every installed skill.

The 10 selected Agency design roles are explicitly registered in `.codex/config.toml`; converted role files are in `.codex/agents/`. Original Markdown in `.agents/design-agent-sources/` is source material, not a native Claude agent installation. Follow the host's supported agent tools; registration on disk does not establish live availability in this chat. Do not spawn agents unless the user or governing instructions authorize delegation.

To check installation integrity, run `python3 scripts/verify_design_capabilities.py`. Never overwrite an existing capability to upgrade it without comparing its pinned contents and preserving local changes.

The deliverable is `little-basket.html`, a single offline-capable, mobile-first HTML file with no build step. Production builds add the manifest, icons and service worker from `pwa/` for installation; run `python3 scripts/build_site.py --require-cloud` and `python3 tests/test_pwa.py` for that path. Use the existing checkout; no additional worktree is needed.

Respect the user's recipe notes. Do not add yam soup. Keep pork ribs (bones) and soup bones (soup-bones) as separate ingredient identities. Old combined records stay with bones; never duplicate their stock/history into soup-bones. Keep pantry inventory, planned ingredients, and purchased groceries distinct.

Treat this as a phone app. Main navigation is market, current list, recipes, and kitchen (stock levels / fresh inventory / 30-day history). A trip reset clears the current plan only. Buying is recorded on check, not on adding to the cart. Long-lasting levels are manual and persistent; selecting recipes never decrements them. New recipes can be added and edited in the app or maintained through conversation and stable built-in IDs, preserving browser data during upgrades.

Run `python3 tests/test_app.py` for material interaction changes. Test narrow mobile widths and keyboard access. Do not overwrite or reset saved user data during development.

Kitchen tabs survive refresh in the current window; leaving and re-entering kitchen starts at lasting supplies. Market basket preview is limited to pending items and removal; purchase checks stay in the full list. Per-trip omitted ingredient IDs are optional `trip.omitted`, must survive sync/import, and disappear with trip reset. Never use pantry stock to fake removal from a trip.

Per-item procurement notes (`trip.itemNotes`) and the trip note (`trip.note`) are optional, shared by preview/full list, and clear only with trip reset. Persist typing without replacing focused inputs; defer remote pulls and automatic resets while editing notes.

Basket artwork reflects unique items in the current list, including purchased items; its badge counts pending items. Reuse the eight embedded WebP frames for the full list and floating basket. Motion never writes household data; respect reduced motion and clean up flights on navigation. A second tap on an already-added market item or selected recipe confirms removal and stays on the current screen.
