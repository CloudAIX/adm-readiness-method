/**
 * ADM readiness checker — Cloudflare Worker.
 * JS port of scanner/scan.py. Measures preparedness for APPs 1.7-1.9
 * (commence 10 Dec 2026). Reports "not yet addressed", never "non-compliant".
 *
 * GET  /check?domain=example.com.au  -> ScanResult JSON
 * POST /lead {email, domain, gap}    -> stores lead in KV
 */

const POLICY_PATHS = [
  "privacy-policy", "privacy", "privacy-statement", "privacy-policy.html",
  "about/privacy", "privacy-notice", "our-privacy-policy", "legal/privacy",
];

const DATE_RE = /(current as of|last updated|last reviewed|updated|effective(?: from)?|reviewed)[^.\n]{0,45}((?:19|20)\d{2})/i;
const ADM_RE = /automated decision|automated processing|computer program|artificial intelligence|\bAI\b|algorithm|machine learning|automated system/gi;
const SCRIBE_RE = /ai scribe|scribe|transcribe|record(?:ing)? (?:of |your )?(?:the )?consultation|dictation|clinical note/i;
const DECISION_RE = /automated decision|substantially assist|decision[- ]making (?:process|by)|decisions (?:are |that are )?made (?:by|using) (?:a |an )?(?:computer|program|system|algorithm)|automated processing of your personal information/i;
const AUTOMATION_RE = /hotdoc|automed|healthengine|appointuit|online booking|automated reminder|recall system|sms reminder|patient portal|triage/gi;

const RACGP_TEMPLATE_MARKERS = [
  "this privacy policy is to provide information to you, our patient",
  "why and when your consent is necessary",
  "our practice will need to collect your personal information",
  "only staff who need to see your personal information will have access",
  "we will not share your personal information with anyone outside australia",
];

// Public hostnames only — blocks IPs, localhost, internal names (SSRF guard).
const DOMAIN_RE = /^(?!-)(?:[a-z0-9-]{1,63}\.)+[a-z]{2,12}$/;

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

async function fetchText(url) {
  try {
    const r = await fetch(url, {
      redirect: "follow",
      headers: { "User-Agent": "Mozilla/5.0 (compatible; GVRN-AI ADM checker)" },
      signal: AbortSignal.timeout(12000),
    });
    if (!r.ok) return "";
    const ct = r.headers.get("content-type") || "";
    if (ct.includes("pdf")) return "%PDF";
    return await r.text();
  } catch {
    return "";
  }
}

function stripHtml(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ");
}

function discoverPolicyLinks(domain, html) {
  const links = [];
  const re = /<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m;
  while ((m = re.exec(html)) !== null) {
    let href = m[1];
    const label = m[2].replace(/<[^>]+>/g, "");
    if (!/privacy/i.test(href + " " + label)) continue;
    if (href.startsWith("//")) href = "https:" + href;
    else if (href.startsWith("/")) href = `https://${domain}${href}`;
    else if (!href.startsWith("http")) href = `https://${domain}/${href.replace(/^\.?\//, "")}`;
    links.push(href);
  }
  return [...new Set(links)].slice(0, 5);
}

async function scan(domain) {
  const res = {
    domain, policy_url: null, policy_found: false, last_updated: null,
    policy_year: null, adm_mentions: 0, scribe_language: false,
    racgp_template_markers: 0, decision_language: false,
    automation_signals: [], gap: false, notes: [],
  };

  const homeRaw = await fetchText(`https://${domain}/`);
  const candidates = [
    ...discoverPolicyLinks(domain, homeRaw),
    ...POLICY_PATHS.map((p) => `https://${domain}/${p}/`),
  ];

  for (const url of candidates) {
    const html = await fetchText(url);
    if (html.length < 2000) {
      if (html.startsWith("%PDF")) res.notes.push("Policy published as PDF - not parsed.");
      continue;
    }
    if (url.toLowerCase().endsWith(".pdf") || html.slice(0, 200).includes("%PDF")) {
      res.notes.push("Policy published as PDF - not parsed.");
      continue;
    }
    const text = stripHtml(html);
    if ((text.toLowerCase().match(/privacy/g) || []).length < 3) continue;

    res.policy_found = true;
    res.policy_url = url;

    const dm = DATE_RE.exec(text);
    if (dm) {
      res.last_updated = dm[0].trim().slice(0, 80);
      res.policy_year = parseInt(dm[2], 10);
    }
    res.adm_mentions = (text.match(ADM_RE) || []).length;
    res.scribe_language = SCRIBE_RE.test(text);
    const low = text.toLowerCase();
    res.racgp_template_markers = RACGP_TEMPLATE_MARKERS.filter((p) => low.includes(p)).length;
    res.decision_language = DECISION_RE.test(text);
    break;
  }

  if (!res.policy_found) {
    res.notes.push("No privacy policy located at common paths.");
    return res;
  }

  res.automation_signals = [...new Set((homeRaw.match(AUTOMATION_RE) || []).map((s) => s.toLowerCase()))].sort();

  res.gap = !res.decision_language;
  if (res.gap && res.scribe_language) {
    res.notes.push(
      "Policy addresses AI scribes and consent, but contains no automated-decision disclosure. " +
      "These are different obligations - scribe consent follows RACGP guidance; APPs 1.7-1.9 " +
      "require disclosing which decisions a program makes or assists.");
  } else if (res.gap) {
    res.notes.push(
      "Privacy policy contains no automated-decision language. APPs 1.7-1.9 commence 10 December 2026.");
  }
  if (res.racgp_template_markers >= 3) {
    res.notes.push(
      `Policy derives from the RACGP template (${res.racgp_template_markers}/5 marker phrases). ` +
      "The RACGP template itself contains no automated-decision language, so the gap is inherited rather than introduced.");
  }
  if (res.policy_year && res.policy_year < 2026) {
    res.notes.push(`Policy appears last updated ${res.policy_year}, before the 2024 amendments were made.`);
  }
  if (res.automation_signals.length && res.gap) {
    res.notes.push(
      "Automated patient-facing processing detected on the website " +
      `(${res.automation_signals.join(", ")}) with no corresponding disclosure.`);
  }
  return res;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });

    if (url.pathname === "/check" && request.method === "GET") {
      const domain = (url.searchParams.get("domain") || "")
        .trim().toLowerCase()
        .replace(/^https?:\/\//, "").replace(/\/.*$/, "");
      if (!DOMAIN_RE.test(domain)) {
        return json({ error: "Enter a valid website domain, e.g. example-clinic.com.au" }, 400);
      }
      // ponytail: per-domain edge cache (1h) is the rate limit; add KV counters if abused
      const cache = caches.default;
      const cacheKey = new Request(`https://cache.local/check/${domain}`);
      const hit = await cache.match(cacheKey);
      if (hit) return withCors(hit);

      const result = await scan(domain);
      const resp = json(result, 200, { "Cache-Control": "public, max-age=3600" });
      await cache.put(cacheKey, resp.clone());
      return resp;
    }

    if (url.pathname === "/lead" && request.method === "POST") {
      let body;
      try { body = await request.json(); } catch { return json({ error: "Bad JSON" }, 400); }
      const email = (body.email || "").trim().toLowerCase();
      const domain = (body.domain || "").trim().toLowerCase();
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return json({ error: "Enter a valid email" }, 400);
      const key = `${Date.now()}:${email}`;
      await env.ADM_LEADS.put(key, JSON.stringify({
        email, domain, gap: !!body.gap, ts: new Date().toISOString(),
        ua: request.headers.get("user-agent") || "",
      }));
      return json({ ok: true });
    }

    return json({ error: "Not found" }, 404);
  },
};

function json(data, status = 200, extra = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...CORS, ...extra },
  });
}

function withCors(resp) {
  const r = new Response(resp.body, resp);
  for (const [k, v] of Object.entries(CORS)) r.headers.set(k, v);
  return r;
}
