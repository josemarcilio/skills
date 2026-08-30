<!-- feed-second-brain:begin -->
## Second brain (soft reminder)

When this session produced **durable** knowledge worth keeping, briefly suggest capturing it with **`/feed-second-brain`** (or `feed-second-brain`). Offer **1–3 short bullets** the user could save. **Never write to the vault** unless the user invokes that skill.

**Suggest after (any one is enough):**
- A non-trivial task is done (feature, fix, refactor, integration)
- A bug is resolved and the root cause or fix pattern is clear
- A design, architecture, or workflow decision was made
- You are naturally wrapping up and something reusable emerged

**Skip when:**
- The work was trivial (formatting, one-liners, pure navigation)
- Nothing durable was learned
- You already suggested feeding the second brain in this session
- The user declined or ignored a recent suggestion

The vault lives at `SECOND_BRAIN_PATH`. To capture, the **feed-second-brain** skill reads that repo's `AGENTS.md` / `CLAUDE.md` and follows its conventions — do not assume layout.
<!-- feed-second-brain:end -->
