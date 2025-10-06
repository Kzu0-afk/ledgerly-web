## Ads Planning and Implementation for Ledgerly

This document outlines a practical plan to introduce advertising as a core revenue stream for the Ledgerly web app, aligned with Infrastructure, Design, and Security requirements.

### Objectives and constraints

- **Infrastructure**: Integrate ads without disrupting the existing Next.js (frontend) and Django (backend) architecture. Avoid vendor lock-in; keep a path from simple programmatic ads to a full header bidding stack.
- **Design**: Professional, unobtrusive placements that do not degrade UX. Reserve space to avoid layout shift, cap ad density, and keep the UI brand-consistent.
- **Security**: Enforce strict CSP, sandboxed third-party iframes, rate limiting, WAF/CDN shielding, and privacy compliance. Minimize logs of ad-related requests.
- **Privacy**: Implement a TCF-compliant CMP and honor user choices for GDPR/CCPA/ePrivacy. No unnecessary tracking vendors.
- **Performance**: Lazy-load, defer non-critical scripts, preserve Core Web Vitals (LCP, CLS, INP). Explicit placeholder sizes for all ad slots.
- **Data policy**: No mock or placeholder production data. Use configuration and environment variables for any IDs.

---

## Network options (AdSense alternatives)

### Premium managed networks (higher RPM, eligibility)

- **Raptive (AdThrive)**: High RPMs, strong account management; usually 100k+ monthly pageviews.
- **Mediavine**: Excellent RPMs and site-speed tools; typically 50k+ sessions/month and quality bar.
- **SHE Media**: Lifestyle-focused; lower threshold than Raptive; variable performance.
- **Monumetric**: Lower traffic threshold with an onboarding fee at small tiers.

### General programmatic networks / optimization platforms

- **Media.net**: Contextual (Yahoo/Bing). Easy approval, decent fill; RPM varies by niche.
- **Ezoic**: Optimization + mediation. Fast to start; requires careful performance tuning.
- **Sovrn**: Header-bidding friendly; analytics and commerce tools.
- **Criteo**: Strong retail demand; prefers scale.

Note: Very low-quality networks (e.g., pop/redirect heavy) are excluded for brand safety.

### Native/content recommendation

- **Outbrain** / **Taboola**: High fill; must curate to maintain UX quality.
- **Sharethrough**: Higher-quality native formats.

### Developer/tech audience (privacy-friendly, contextual)

- **Carbon Ads**: Minimal, high-quality placements for dev/design audiences; manual approval.
- **EthicalAds**: Privacy-first text/image ads, strong for technical content.
- **BuySellAds**: Direct placements marketplace with manual control.

### Direct sponsorships (highest control/CPMs)

- **Paved**, **Passionfroot**, **Swapstack**: Marketplaces for direct deals across site and newsletter. Requires a media kit and rate card.

### Header bidding stack (max control/performance)

- **Prebid.js** for client-side header bidding.
- SSPs: Sovrn, PubMatic, Magnite, OpenX, Index Exchange (as applicable to scale and approval).
- **Ad Server**: Google Ad Manager (GAM) or Kevel (formerly Adzerk). Self-hosted fallback: Revive Adserver.
- **Amazon Publisher Services (APS/TAM)** for strong retail demand when eligible.

---

## Recommendation by stage

- **< 50k sessions/month**: Start with Media.net or Ezoic. If audience is dev/tech, apply to Carbon/EthicalAds. Build out direct sponsorships in parallel.
- **50k–100k sessions/month**: Apply to Mediavine. If not yet eligible, run Ezoic or a light Prebid setup with 2–3 SSPs + GAM.
- **100k+ sessions/month**: Raptive/Mediavine or a custom Prebid.js + GAM + APS stack.
- **Developer/design niche at any scale**: Carbon Ads or EthicalAds; layer in direct sponsorships via Paved/Passionfroot.

---

## Architecture fit for Ledgerly (Next.js + Django)

- **Frontend (Next.js)**
  - Ad components per placement: define fixed-size containers; lazy-load on viewport.
  - Optional Prebid.js boot when consent allows; pass targeting to the ad server.
  - Integrate a CMP; expose consent signals (TCF v2) to ads and bidders.
  - Fire viewability and click events to analytics with minimal payloads.

- **Backend (Django)**
  - No ad proxying by default (reduces liability). If a proxy is needed later, implement strict rate limiting, bot checks, and caching.
  - Serve `ads.txt` statically via Django/ASGI or CDN.
  - Enforce CSP, security headers, and logging minimization for ad-related traffic.

Data flow overview:

1) User loads page → 2) CMP renders and captures consent → 3) If consented, Prebid/GAM loads → 4) Header bidding auction → 5) Ad server renders creative in sandboxed iframe → 6) View/click events to analytics.

---

## Implementation plan

### Phase 1 — Foundation (1–2 weeks)

- **Select initial network(s)**: Media.net/Ezoic or niche network (Carbon/EthicalAds) based on audience.
- **CMP integration**: OneTrust/Sourcepoint/Cookiebot or an open-source TCF v2 compliant CMP. Configure regional enforcement (GDPR/CCPA).
- **Frontend slots**: Add top placements (e.g., top-of-content, in-content, sidebar). Reserve heights to avoid CLS.
- **Security & privacy**: Harden CSP, sandbox iframes, set `SameSite=None; Secure` for cross-site cookies (if any), and implement bot rate limiting.
- **Legal**: Update Privacy and Cookie policies; publish `ads.txt`.

### Phase 2 — Optimization (2–4 weeks)

- **Header bidding pilot**: Add Prebid.js with 2–3 bidders (e.g., Sovrn, Magnite, OpenX) and GAM as ad server.
- **Add APS/TAM** (if eligible) for retail demand.
- **Analytics**: Capture revenue, viewability, and Web Vitals. Establish weekly yield reports.
- **A/B tests**: Placement density, lazy thresholds, bidder lineup.

### Phase 3 — Scale and Direct Deals

- **Apply to Mediavine/Raptive** (when eligible) or expand the custom bidder set.
- **Direct sponsorships**: Create a media kit (audience, impressions, placements, pricing). Use Paved/Passionfroot for pipeline.
- **Ongoing compliance**: Quarterly creative audits, category blocklists, vendor risk reviews.

---

## Frontend integration details (Next.js)

- **Ad components**: Build a reusable `AdSlot` component that:
  - Reserves a fixed container size (desktop/mobile variants) to prevent CLS.
  - Lazy-loads when intersecting viewport.
  - Only initializes demand sources after CMP consent allows.
  - Emits lifecycle events (requested, rendered, viewable, clicked) for analytics.

- **Consent**:
  - Render CMP before any ad script.
  - Read TCF v2 consent string and pass to Prebid/GAM initialization.

- **Performance**:
  - Use dynamic imports for any ad or header-bidding scripts.
  - Stagger slot initialization to avoid main-thread contention.

- **CSP**:
  - Allow only known ad CDNs/bidders in `script-src`, `img-src`, `frame-src`. Keep lists tightly scoped and versioned.

---

## Backend integration details (Django)

- **Headers & cookies**:
  - Enable `SecurityMiddleware`; set `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`.
  - Use `django-csp` (or equivalent) to enforce CSP aligned with approved ad/bidder domains.

- **Rate limiting & bot protection**:
  - Apply rate limiting (e.g., `django-ratelimit`) to any optional reporting/proxy endpoints.
  - Prefer CDN/WAF protections (Cloudflare/AWS CloudFront) for challenge/mitigation.

- **Logging**:
  - Log only aggregate and essential operational metrics for ad endpoints.
  - Redact identifiers; avoid storing PII; honor retention limits.

- **Static assets**:
  - Serve `/.well-known/ads.txt` (or `/ads.txt`) via static files/CDN.

---

## Consent and compliance

- **CMP**: Implement a TCF v2 compliant CMP. Regions: auto-enforce GDPR (EEA/UK), CCPA/CPRA (California), LGPD (Brazil) as applicable.
- **Signals**: Pass consent string to Prebid and GAM. Block or restrict non-essential vendors until consent.
- **Policies**: Update Privacy, Cookie, and Ads Policies with vendor lists and purposes. Provide opt-out mechanisms.

---

## Security, privacy, and anti-DDoS

- **CSP**: Strict `default-src 'self'`; narrowly allowlisted `script-src`, `img-src`, `frame-src`, `connect-src` for ad vendors.
- **Sandboxing**: All creatives in sandboxed iframes; disallow top navigation.
- **WAF/CDN**: Use CDN shielding and bot management to throttle abusive traffic to ad endpoints.
- **Rate limiting**: Enforce server-side rate limits; consider per-IP and token buckets.
- **Transport security**: Enforce HTTPS (HSTS), secure cookies, and disable weak ciphers at the edge.

---

## Performance & UX guardrails

- **Ad density**: Keep content-to-ad ratio professional; avoid intrusive interstitials and auto-playing audio.
- **Web Vitals**: Reserve slot sizes to prevent CLS; lazy-load below-the-fold units to protect LCP/INP.
- **Scheduling**: Defer non-critical ad scripts; load bidders only when needed and permitted.

---

## Monitoring and analytics

- **Revenue & delivery**: Use GAM/Ezoic/Sovrn dashboards plus weekly internal summaries.
- **Viewability**: Track viewability rates; target 60%+ for above-the-fold.
- **Tech health**: Monitor script errors (Sentry), latency (RUM), and Web Vitals impacts.

---

## Governance

- **ads.txt**: Keep up to date with authorized sellers.
- **Creative audits**: Quarterly review of creatives and blocklists (categories, sensitive topics).
- **Vendor risk**: Annual vendor reviews; DPAs/SCCs as needed.

---

## Rollout plan (incremental)

1. Implement CMP and publish `ads.txt`.
2. Add 1–2 top placements with a single network; validate UX and vitals.
3. Introduce Prebid.js with 2–3 bidders; set floor prices conservatively.
4. Expand placements conservatively; A/B test density and thresholds.
5. Layer in direct sponsorships; iterate pricing and packages.

---

## Quick checklist

- [ ] CMP live and regionally enforced
- [ ] CSP hardened with allowlists for selected vendors
- [ ] Slots reserve fixed sizes (no CLS)
- [ ] Lazy loading with intersection observers
- [ ] Logging minimized; PII redaction in place
- [ ] `ads.txt` published and validated
- [ ] Rate limiting and WAF/CDN protections enabled
- [ ] Weekly yield and UX reports scheduled

---

## Next steps for Ledgerly

1) Confirm audience niche and approximate traffic levels.
2) Choose initial network(s) and CMP vendor.
3) Identify 2–3 initial placements in the existing layout.
4) Implement CMP, then integrate the first network, followed by a Prebid pilot.
5) Review results after two weeks and iterate (placements, bidders, or managed network application).


