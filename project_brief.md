# My agent: Loopy
One-liner: A conversational agent that helps tech professionals get a personalized news briefing of up to 5 relevant items based on their role or custom description with a catalog of curated tech news sources.

Tool coverage:
- Memory: Remembers the user's role (e.g. chip selection or custom description) across sessions so future visits remember it automatically.
- Tools: Single news fetch tool querying curated sources stored in Firestore (Hacker News free API, RSS feeds for design blogs, product newsletter RSS, Product Hunt). Validates feeds, enforces a 30-day cutoff, and sorts by relevance and recency.
- Catalog/UI: Curated tech news articles rendered as up to 5 A2UI cards (headline, source name, date, link to real article, and personalized "why it matters" line).
- Image gen: n/a (out of scope for 2-3 hour lab)
- Sandbox: n/a (out of scope for 2-3 hour lab)

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch (pick what fits): Firestore for source catalog tagged by role, Hacker News API + RSS feed parser tool, newspaper aesthetic for frontend (custom styling later).

## Scope & Constraints
- In scope:
  - Role chips (Product Designer, Design Engineer, PM, Frontend, Backend, FDE) and free-text role description.
  - Curated sources stored in Firestore, tagged by role.
  - Unified fetch tool for Hacker News and RSS feeds with failure dropping.
  - Up to 5 A2UI cards with headline, source, date, real link, and personalized "why it matters" line.
  - Role memory across sessions.
  - Deployed frontend.
- Out of scope:
  - Image generation
  - Code sandbox
  - Feedback buttons & shareable cards
  - Additional roles beyond the starter set
- Guardrails & Rules:
  - Strict grounding: only show items actually fetched with real links and dates. Never hallucinate or synthesize fake news.
  - Recency: only items from the last 30 days.
  - Ranking: balanced blend of relevance to role and recency.
  - Graceful degradation: if fewer than 5 items are found, display only what was found without padding.
  - Visual direction: vintage/classic newspaper aesthetic (applied at the frontend step).
