help_chat_roadmap_v1 (2025-08-20)

Goal: Finish core filing app first; in parallel, lay the groundwork for a contextual, low-friction help experience. MVP is rule-based (no LLM), then evolve to RAG + task guides.

Do-now (developer actions)
- Create resources/help/glossary.yml and resources/help/faq.yml with 5–10 seed entries (desc/ example / source URL)
- Add app/help/ blueprint with GET /help/context and GET /help/suggest (dummy data ok)
- Add help FAB + modal placeholder to base.html (controlled by HELP_ENABLED=false)
- Log anonymous events on 1–2 key pages (validation_error, abandonment, long_stay)
- Document page/year/company_type naming rules in docs

Phased plan
- Phase 0: unify naming/flags (HELP_ENABLED, HELP_CHAT_MVP, HELP_RAG_ENABLED)
- Phase 1 (1–2w): rule-based suggests + glossary (YAML), zero hallucinations, sources required
- Phase 2 (2–3w): RAG over handovers/specs; POST /help/chat with page/year context; show citations
- Phase 3 (+1w): task guides (required-only, diff causes)

Minimum API
- GET /help/context -> {page, year, company_type}
- GET /help/suggest?page=... -> suggestions[]
- GET /help/glossary?q=... -> {term, desc, links[]}

Safety
- No tax advice; cite sources; include year; mask PII

MVP definition
- Help UI toggles on; suggests + glossary respond; 5–10 entries live; 1 page logs anonymous events
