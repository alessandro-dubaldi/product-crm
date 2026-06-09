# Roadmap

## v1 — Hackathon MVP

End-to-end working pipeline from HubSpot to Notion digest.

### Phase 1 — Data layer
- [ ] HubSpot MCP connection
- [ ] Company filter: `arr_live ≠ 0`, `nature`, `tier_company`, `macro_category`, `beginning_date` range, `arr_live` range
- [ ] Deal traversal: pipeline = `593165758`, select most recent per company
- [ ] Contact traversal: filter by non-empty `engagement_score_v2`
- [ ] Random sample of N companies → one deal + one contact per company

### Phase 2 — Outreach
- [ ] Claude-generated personalized email per contact
- [ ] Calendly link embedded in email (PM provides their own link)
- [ ] Send via Gmail MCP

### Phase 3 — Scheduling
- [ ] Google Calendar MCP: view confirmed calls on PM's calendar
- [ ] Slot deduplication handled natively by Calendly

### Phase 4 — Capture
- [ ] Granola MCP: fetch transcript after call
- [ ] Claude: generate exec summary from transcript
- [ ] Store (company, contact, transcript, summary) locally

### Phase 5 — Synthesis
- [ ] Notion MCP: create per-interview page (transcript + exec summary)
- [ ] Claude: aggregate all interviews from past 7 days → trends + key insights
- [ ] Notion MCP: post weekly digest page

---

## v2 — Post-Hackathon

### Filtering
- [ ] NPS score filter on contacts
- [ ] Per-deal ARR filtering (v1 uses company-level `arr_live`)
- [ ] Additional HubSpot filters (churn risk, product tier, last contacted date)
- [ ] Saved filter presets

### Scheduling
- [ ] Push scheduling with slot inventory management
- [ ] Slot deduplication: mark slots as soft-reserved on email send, hard-reserved on confirmation
- [ ] Reminder emails to customers who haven't booked

### Insights
- [ ] Structured insight tagging: pain points, feature requests, compliments, churn signals
- [ ] Sentiment scoring per product area
- [ ] Verbatim quote extraction with topic tags
- [ ] Cross-interview pattern detection (recurring themes across cohorts)

### HubSpot writeback
- [ ] Update `last_interviewed` on contact after call
- [ ] Write `key_pain_point` and `interview_summary` back to contact properties
- [ ] Exclude recently interviewed contacts from future sampling pools

### Reporting
- [ ] Roadmap linkage: tag insights to backlog items / epics
- [ ] Executive digest: monthly "voice of customer" summary for leadership
- [ ] Interview history per company: avoid re-contacting same company within N months

### Infrastructure
- [ ] Scheduled weekly digest (no manual trigger)
- [ ] Email open/reply tracking
- [ ] Multi-PM support

---

## Known Constraints (v1)

- ARR used as company-level `arr_live`, not per-deal breakdown
- Scheduling via Calendly pull (push with slot management deferred to v2)
- Interview insights are transcript + exec summary only (no structured tagging)
- Weekly digest is manually triggered from the UI
- No HubSpot writeback after interviews
