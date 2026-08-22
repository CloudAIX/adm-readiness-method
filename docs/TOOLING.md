# Crawling tooling — what we actually need, and what it costs
Tested 22 Aug 2026 against real Australian health-provider sites.

## Verdict: buy nothing yet

The 40-domain scan runs on **plain `curl`** at 82% policy discovery. The automation-detection failure that looked like a tooling gap was **a bug in our own regex** — it ran against stripped text while booking widgets live in `<script src=...>` attributes. Fixed in one line; detection went from 0 to 26 of 33.

**Before buying a scraper, check whether the parser is pointed at the right thing.**

## What was tested

| Tool | Cost | Result on our sites |
|---|---|---|
| **curl** | free | 82% policy discovery. Finds HotDoc in raw HTML. Currently sufficient. |
| **Chrome headless** | free, already installed | 253,904 DOM chars vs curl on the same page; 3 automation signals vs 2. Handles JS rendering. **This is the upgrade path — no signup, no bill.** |
| **Jina Reader** (`r.jina.ai/<url>`) | free, no signup | Works immediately. Correctly diagnosed one site as returning a **PHP 500** — a dead site, not a scraping failure. Good for one-off lookups. Token-billed at volume. |
| **Firecrawl** | from **$83/month** | Already connected. Strong at full-site crawls and structured extraction. Not required for this job. |

## The 7 unlocated domains — diagnosis, not tooling

Checking them individually showed the misses are mostly **not** scraper limitations:
- one site returns HTTP 500
- two publish policies as **PDF**
- one hosts its policy on a **different domain**

Fixes needed: a PDF parser and cross-domain link following. Neither requires a paid service.

## Recommendation

1. **Now** — stay on curl. Add Chrome headless for the JS-rendered minority. Both free.
2. **Add a PDF parser** — `pypdf` is already installed and used elsewhere in this stack.
3. **Follow cross-domain policy links** — practice groups often centralise the policy.
4. **Only if scaling past ~10,000 pages/month** — reassess. At that point the honest comparison is Spider.cloud or self-hosted Crawl4AI (free, wraps Playwright) before Firecrawl's $83/month.

Firecrawl remains worth keeping for **discovery** — finding the domains in the first place, which is genuinely hard — rather than for fetching them, which is not.

## Cost of the current pipeline
**$0.** Chrome and curl are on the machine. The only spend so far is Firecrawl search credits already in the account.
