// Pump it — share-link worker (Cloudflare Workers)
//
// https://<worker>/c/<id>  → for Threads / X / Telegram link previews: a page with the record card
//                            as a big preview image (Open Graph + Twitter Card tags).
//                            A person who taps the link is sent straight to the game in Telegram
//                            with the sharer's referral nick.
// https://<worker>/        → the game.
//
// Deploy: Cloudflare dashboard → Workers & Pages → Create → Worker → "Hello World" → Edit code →
//         paste this file → Deploy. Then send the worker URL (e.g. https://pumpit.<you>.workers.dev).

const API = "https://dlnvgtvpgiquwrjcijzg.supabase.co/functions/v1/api";
const GAME = "https://t.me/PumpItGameBot/play";

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const money = (v) => "$" + (v >= 1000 ? Math.round(v).toLocaleString("en-US") : Number(v).toFixed(2));

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const m = url.pathname.match(/^\/c\/(\d{1,12})\/?$/);
    if (!m) return Response.redirect(GAME, 302);

    let card = null;
    try {
      const r = await fetch(`${API}?card=${m[1]}`, { cf: { cacheTtl: 3600, cacheEverything: true } });
      if (r.ok) card = await r.json();
    } catch (e) {}
    if (!card || !card.img) return Response.redirect(GAME, 302);

    // only links to our own game are allowed as the destination
    const dest = /^https:\/\/t\.me\/PumpItGameBot\/play(\?startapp=ref_[A-Za-z0-9_]{1,32})?$/.test(card.link) ? card.link : GAME;
    const pct = Math.round((Number(card.score) - 1) * 100);
    const title = `@${card.nick}: ATH ${money(Number(card.score))} (${pct >= 0 ? "+" : ""}${pct}%) у Pump it`;
    const desc = "Голосова крипто-гра в Telegram від Kraken Ukraine. Спробуй побити рекорд 👇";

    const html = `<!DOCTYPE html><html lang="uk"><head><meta charset="utf-8">
<title>${esc(title)}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Pump it">
<meta property="og:title" content="${esc(title)}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:image" content="${esc(card.img)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:url" content="${esc(url.href)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="${esc(title)}">
<meta name="twitter:description" content="${esc(desc)}">
<meta name="twitter:image" content="${esc(card.img)}">
<meta http-equiv="refresh" content="0; url=${esc(dest)}">
<style>body{margin:0;background:#07060d;color:#f4f2ff;font-family:system-ui,sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center}a{color:#b18cff}</style>
</head><body><div><p>Відкриваємо гру…</p><p><a href="${esc(dest)}">Грати в Pump it</a></p></div>
<script>location.replace(${JSON.stringify(dest)});</script></body></html>`;

    return new Response(html, { headers: { "content-type": "text/html; charset=utf-8", "cache-control": "public, max-age=3600" } });
  },
};
