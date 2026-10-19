# Cooking / Little Basket

For UI, UX, recipe, or grocery-list work, read `.agents/skills/mobile-kitchen/SKILL.md`.

Project-installed design capabilities are documented in `design/capabilities/README.md`, with exact commits and file checksums in `design/capabilities/capabilities.lock.json`. Read the selected skill's full instructions before using it. Use `design-taste-frontend` (app-screen route) and `frontend-design` as the main design workflow for this application. Other styles are alternatives, not cumulative requirements. Do not combine incompatible visual styles or automatically invoke every installed skill.

The 10 selected Agency design roles are explicitly registered in `.codex/config.toml`; converted role files are in `.codex/agents/`. Original Markdown in `.agents/design-agent-sources/` is source material, not a native Claude agent installation. Follow the host's supported agent tools; registration on disk does not establish live availability in this chat. Do not spawn agents unless the user or governing instructions authorize delegation.

To check installation integrity, run `python3 scripts/verify_design_capabilities.py`. Never overwrite an existing capability to upgrade it without comparing its pinned contents and preserving local changes.

The deliverable is `little-basket.html`, a single offline-capable, mobile-first HTML file with no build step. Use the existing checkout; no additional worktree is needed.

Respect the user's recipe notes. Do not add yam soup. Use a shared ingredient identity for pork ribs / soup bones. Keep pantry inventory, planned ingredients, and purchased groceries distinct.

Treat this as a phone app. Main navigation is market, recipes, current list, and kitchen (stock levels / fresh inventory / 30-day history). A trip reset clears the current plan only. Buying is recorded on check, not on adding to the cart. Long-lasting levels are manual and persistent; selecting recipes never decrements them. New recipes can be added and edited in the app or maintained through conversation and stable built-in IDs, preserving browser data during upgrades.

Run `python3 tests/test_app.py` for material interaction changes. Test narrow mobile widths and keyboard access. Do not overwrite or reset saved user data during development.
