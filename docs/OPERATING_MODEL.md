# TEN International Hiring Watch — EU27
## Operating Model v2 & Issue #0 (Rebuilt)

**What changed and why:** v1 validated that the research methodology works — the A/B/C/D evidence tiers reflect real, observable differences in how EU employers talk about sponsorship. It did not validate that anyone wants this, that it can survive against existing players, or that it can fund itself past a few manual issues. This rebuild keeps every piece of v1 that held up (the evidence gates, the ATS-over-aggregator rule, the ban on fake sponsorship scoring) and adds the five things v1 was missing: a stated competitive position, a distribution plan, a monetization model, legal-mechanism precision, and a freshness protocol.

---

## Part I — Positioning: Where TEN Actually Sits

The space is not empty. As of this pull, at least three players occupy adjacent ground:

| Player | Model | Where it's strong | Where it's thin |
|---|---|---|---|
| VisaJobs.xyz | Curated job board + weekly newsletter, 8,000+ subscribers | Discovery volume, SEO presence | No visible evidence tiering — "sponsorship" is binary |
| IFMOSA | Job board, claims manual cross-check against registries | Trust framing similar to TEN's | Skews toward volume/global, not EU27-specific depth |
| Arbeitnow | Content + listings | Already publishes the "sponsorship ≠ fee-paid" explainer TEN treats as an insight | Not newsletter-native, less curatorial voice |

**TEN's actual edge is not "we verify sponsorship."** Others claim that too. TEN's edge is the thing v1 already built by accident: the willingness to say *"this employer only asks the question, it doesn't answer it"* and to publish restrictions as prominently as wins. That's a harder position to copy because it requires admitting most vacancies don't qualify — a volume-driven competitor won't do that.

**Revised one-line promise:**
> We tell you which European job postings actually answer the sponsorship question — and flag the ones that only ask it.

---

## Part II — Canonical Operating Template v2

### 1. Research window & country weighting — unchanged
Previous 7–10 days, 12–25 verified vacancies target, Big 5 priority-not-boundary weighting. This held up under review; no change needed.

### 2. Discovery hierarchy — unchanged tiers, phased automation layered on top
Tier 1 (employer/ATS) → Tier 2 (EURES, LinkedIn, specialist DBs) → Tier 3 (aggregators, discovery-only). See **Part VI** for what gets automated at each tier and what stays manual.

### 3. Mandatory vacancy record — three fields added

| Field | Status |
|---|---|
| *(all v1 fields retained)* | Unchanged |
| **Access mechanism** | NEW — see glossary, Part VII |
| **Re-verification date** | NEW — see Part V(b) below |
| **Language of evidence** | Expanded — now records whether the ATS/site itself is English-only, flagging structural bias (Part IX, About section) |

### 4. Classification decision tree — unchanged logic, one addition
The A/B/C/D questions from v1 stand. Add a **sub-tag at the A tier only**: which legal route the evidence points to (Blue Card / national skilled-worker permit / Opportunity-Card-style self-search route / unspecified employer sponsorship). If the vacancy text doesn't specify, the sub-tag is `Unspecified — verify before publish`, not a guess. Conflating these routes was the single biggest accuracy risk in v1 — "visa sponsorship" and "EU Blue Card eligible" are not interchangeable claims.

### 5. Editorial gates — one added
Gates 1–7 unchanged. **Gate 8 — Mechanism resolved:** an A-tier role cannot ship without either a resolved access-mechanism sub-tag or an explicit "unspecified, verify directly" note visible to the reader. No silent guessing.

### 6. Internal confidence status — unchanged

### 7. Freshness & re-verification protocol — NEW
- Every vacancy carries a **re-verification date**, separate from first-verification date.
- A-tier roles are re-pinged (URL still resolves, still accepting applications) at minimum once per week they appear, including repeat weeks.
- If a role drops from "open" between verification and send, it is pulled — never published on stale status.
- Roles held over from a prior issue are marked **"Carried, re-verified [date]"** rather than re-presented as new.

### 8. Editorial dedup rule — NEW, no longer a judgment call
> Maximum one listing per employer per issue, unless a second role differs in seniority band **and** carries independently distinct access evidence. Ties are broken by whichever role has the stronger evidence tier; if tied, whichever is more senior.

This replaces the "I would probably cut one of these" language in v1 with a rule an editor (or eventually a script) can apply without re-litigating it every week.

### 9. Canonical newsletter structure v2 — reordered

```
TEN International Hiring Watch — EU27
Issue #X | [DATE]

THIS WEEK'S REALITY CHECK          ← moved up from bottom
[Lead with 1-2 of the sharpest D-tier or "question≠commitment" B-tier catches]

🟢 STRONG INTERNATIONAL-ACCESS OPPORTUNITIES
🟡 WORTH INVESTIGATING
🟠 VERIFY BEFORE INVESTING TIME
🔴 RESTRICTIONS TO NOTICE
🇪🇺 OUTSIDE THE BIG 5
JOB SEARCH INTELLIGENCE
ACCESS-MECHANISM GLOSSARY          ← new, short, links to full version
ABOUT THIS WATCH
  — methodology + English-source bias disclosure + re-verification note
CTA
```

The reality-check lead is the actual product differentiation from Part I; it should not be buried as the seventh bullet of an internal gate list the reader never sees.

---

## Part III — Scope Commitment (instead of a caveat)

v1 buried "we over-index on tech" as an apology inside the validation section. Rebuilt as a stated position:

**Issues #0–#5: explicitly tech/data/software-first**, because that's where ATS discovery is cheapest and evidence density is highest. **Starting Issue #6:** one non-tech profession actively sourced per issue (finance, healthcare, engineering, logistics — rotating), tracked as its own line in the validation scorecard (Part VIII) rather than left as an aspiration.

---

## Part IV — Distribution & Growth Plan (previously absent entirely)

v1 had zero acquisition plan. A weekly-cadence product loses the discovery-moment race to SEO-indexed job boards by default, so growth has to come from somewhere other than search:

- **Seed in communities where the reality-check framing is native:** r/IWantOut, r/germany, r/eupersonalfinance, EU Blue Card and relocation Facebook/Discord groups — post the D-tier "restrictions" catches specifically, since negative evidence is the most shareable content type and the rarest.
- **One evergreen page per issue**, not just an email: a static, indexable page per vacancy with its evidence quote and tier, so search traffic can land on individual verified roles even between newsletter sends. This is the direct counter to losing the SEO race to volume competitors.
- **Partner, don't compete, with immigration lawyers/relocation consultants** as a referral and credibility channel — they see the "question ≠ commitment" confusion constantly and have audiences already.
- **Track one number weekly starting Issue #1:** open-rate or click-through by tier (do readers act on A-tier more than they engage with D-tier?). This is the audience-side validation v1 never collected.

---

## Part V — Monetization Model (previously unaddressed)

The reality-check/restrictions framing is the trust asset — anything that looks like pay-to-list breaks it immediately, so employer-paid placement is ruled out for the A–D tiers.

**Proposed model:**
- Newsletter itself stays free and ad-free of listing bias — this is the trust foundation.
- Revenue from a **paid tier**: full searchable archive access, saved-search alerts by country/profession, and the access-mechanism glossary as a standalone reference guide.
- Optional **non-listing sponsorship** (e.g., a relocation-services or immigration-law sponsor's name in a clearly labeled banner, with zero influence over classification) — kept structurally separate from the editorial gates so it can't be perceived as buying an A-tier.

This needs real-world testing, not a launch-day requirement — but it has to be *decided* before scaling volume, because retrofitting monetization onto an established "no bias" reputation is much harder than starting with the boundary drawn.

---

## Part VI — Automation Architecture (Phased)

**Never automated, at any phase:** the A/B/C/D judgment call itself. This is the product.

**Phase 1 — Issues #1–6, discovery only:**
- Scheduled pulls against Greenhouse/Lever/Ashby/Workday public job-list endpoints for a maintained target-company list, filtered by EU27 country.
- Keyword-flag postings containing sponsor/visa/relocation/work permit/right to work — flags queue for human review, doesn't classify.
- Auto-dedupe by company + title + location hash before a human sees it.

**Phase 2 — after ~6 issues, once the target-company list is proven out:**
- Expand the seed list past tech via company-registry and LinkedIn company-search pulls per country.
- Auto-extract the literal application-form field text (Greenhouse/Lever expose form labels in their JSON) so the *evidence sentence* — "Do you require sponsorship?" — is captured automatically. The A/B/C/D call still requires a human read.
- Auto-expire postings that 404 or return closed status, feeding the freshness protocol in Part II.7.

---

## Part VII — Access-Mechanism Glossary (NEW — first version)

| Term | What it actually means | Common confusion |
|---|---|---|
| **Employer-sponsored work visa** | Employer supports a national work-permit application tied to that specific job | Often assumed to mean an EU Blue Card; frequently isn't |
| **EU Blue Card** | EU-wide route for skilled workers with a qualifying job offer and salary threshold; portable rights vary by member state | Treated as identical to "generic sponsorship" — it isn't, and eligibility/salary thresholds differ by country |
| **National skilled-worker visa** (e.g., Germany's Skilled Worker visa) | Country-specific route, often paired with qualification-recognition steps for regulated professions | Conflated with Blue Card in casual listing language |
| **Opportunity/self-search route** (e.g., Germany's Chancenkarte) | Lets a candidate enter and search for work without a job offer first — the opposite of employer sponsorship | Sometimes appears in vacancy text as "relocation support" when it's really pointing candidates to a self-search visa, not employer sponsorship |
| **Relocation assistance (no visa component)** | Moving costs/housing only; assumes candidate already has the right to work | The single most common false positive in raw listing language |

*This table is a starting draft, not a legal reference — TEN should have it reviewed by an immigration-law contact before publishing it externally.*

---

## Part VIII — Revised Validation / Kill–Continue Framework

v1's scorecard was entirely supply-side. Rebuilt to require both sides:

| Question | v1 (supply) | v2 addition (demand) |
|---|---|---|
| Can we find enough vacancies? | 🟢 Yes | — |
| Does A/B/C/D reflect real differences? | 🟢 Strongly yes | — |
| Is negative evidence useful? | 🟢 Yes | Do readers click/share D-tier more than A-tier? *(track from Issue #1)* |
| Is Big 5 coverage achievable? | 🟢 Yes | — |
| Is non-tech coverage proven? | 🟡 Partially | Is at least one non-tech role sourced from Issue #6 on, per Part III? |
| Does TEN have differentiated value? | 🟢 Yes (claimed) | Do subscribers reference the reality-check framing unprompted, in replies/shares? |
| **NEW: Is there a distribution channel producing net-new subscribers weekly?** | — | Track raw number, source-attributed, from Issue #1 |
| **NEW: Is the monetization boundary (Part V) holding without compromise?** | — | Binary check each issue |

**Kill/continue threshold, rebuilt:** reproduce 12–20 verified roles for 4 consecutive issues **while also** growing subscribers from a channel outside the founder's own network **and** landing at least one non-tech role by Issue #6. Supply-side repeatability alone is no longer sufficient to continue.

---

## Part IX — Issue #0, Rebuilt

*Underlying vacancy evidence reused from the original v1 research pass (Sept 7, 2026 pull). Re-verification dates below are placeholders — every role needs a live re-check against Gate 6/Part II.7 before this actually sends.*

```
TEN International Hiring Watch — EU27
Issue #0 | September 7, 2026 (re-verify before send)
```

### 🔍 This Week's Reality Check

**Storio Group — Principal iOS Engineer (Netherlands).** The application asks whether you'd relocate from outside the Netherlands and need sponsorship — then adds that visa *transfers* can be supported only if you're already based in the Netherlands. Read the full sentence, not just the keyword: this is far less useful to someone applying from abroad than it first appears.

**Fiducial — System Integration Engineer, UAV Robotics (Delft).** States plainly: "WE CANNOT PROVIDE VISA SPONSORSHIP." Included precisely because negative evidence saves more time than another maybe.

*(Full restrictions list below in the 🔴 section — leading with these two because they're the sharpest examples of question-vs-commitment and remote-eligibility-vs-immigration-access, the two confusions this Watch exists to catch.)*

### 🟢 Strong International-Access Opportunities
*(Same seven roles as v1: QuantCo Software/Cloud Engineer, Clera AI & Backend / Customer / Forward Deployed / Founding Product Engineer, GenPeach AI Research Engineer, Clera Head of Growth — each now requires an Access Mechanism sub-tag before publish.)*

**Access mechanism status for this batch: `Unspecified in evidence — verify before publish` across all seven roles.** None of the original vacancy text specified Blue Card vs. national permit vs. generic employer sponsorship — v1 didn't distinguish these, and per Gate 8 that means none of these seven ship in a live issue until that's resolved directly with each employer/ATS listing.

*GenPeach AI dedup: per the Part II.8 rule, only the AI Research Engineer role ships — Founding AI Research Scientist is a distinct-enough seniority band to also qualify, so both are retained, matching v1's own instinct but now backed by a stated rule rather than a one-off call.*

### 🟡 Worth Investigating
*(Unchanged from v1: Qonto Senior/Staff Frontend Engineer, Catapult Sports Senior Software Engineer, NavVis Senior Full-Stack Engineer, IDnow Senior Software Engineer, Qonto Staff Product Marketing Manager, Insify Data Analyst, CFGI Finance & Accounting Advisory Manager and Senior Manager — dedup rule keeps both CFGI roles, distinct seniority.)*

### 🟠 Verify Before Investing Time
*(Unchanged: Workwize Product Engineer, Storio Group Principal iOS Engineer — led above in Reality Check.)*

### 🔴 Restrictions International Candidates Should Notice
*(Unchanged: CAI Senior CQV Utilities Engineer, AccountsIQ Senior .NET Engineer, Oomnitza UX Design Engineer, Fiducial UAV Robotics Engineer — led above, Overstory Engineering Manager ML, Ketryx DevSecOps Engineer.)*

### 🇪🇺 Outside the Big 5
Kept deliberately short per v1's own rule — no padding.

### Job Search Intelligence
Unchanged core technique (search inside ATS pages for sponsorship/relocation/work-authorization phrases and read the full sentence, not the keyword) — now paired with the mechanism glossary link.

### Access-Mechanism Glossary (short form)
Link to Part VII table.

### About This Watch
Evidence methodology, plus two disclosures v1 omitted:
- *Every source in this issue is an English-language ATS or careers page. This structurally favors employers already targeting international/English-speaking hires and is a known bias, not a neutral sample.*
- *This issue skews toward software/AI/data roles (6 of 7 A-tier listings). See Part III for the non-tech sourcing commitment.*

### CTA
Subscribe / share — reframed around the reality-check hook: *"Forward this to someone who's about to apply somewhere that only asks the sponsorship question."*
