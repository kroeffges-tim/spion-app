"""Baut aus spion.html die installierbare Web-App in docs/ (für GitHub Pages).

Aufruf:  python3 build.py
"""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
NAME, SHORT = "Spion & Imposter", "Spion"
BG, BRASS = "#0d1720", "#e2a948"

HEAD = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="theme-color" content="{BG}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="{SHORT}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
<style>
:root {{ padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }}
body {{ margin: 0; }}
html, body {{ touch-action: manipulation; -webkit-text-size-adjust: 100%; }}
img {{ max-width: 100%; }}
[hidden] {{ display: none !important; }}
</style>
"""

SW_REGISTER = """
<script>
// kein Zoomen: iOS ignoriert user-scalable=no, daher die Gesten selbst abfangen
const stop = e => e.preventDefault();
for (const g of ["gesturestart", "gesturechange", "gestureend"]) document.addEventListener(g, stop, { passive: false });
document.addEventListener("touchmove", e => { if (e.touches.length > 1 || (e.scale && e.scale !== 1)) e.preventDefault(); }, { passive: false });
let lastTouch = 0;
document.addEventListener("touchend", e => {
  const now = Date.now();
  // Doppeltipp: zweiten Tipp nicht als Zoom werten, Klick trotzdem auslösen
  if (now - lastTouch < 350 && !e.target.closest("input, textarea")) { e.preventDefault(); e.target.closest("button")?.click(); }
  lastTouch = now;
}, { passive: false });
if ("serviceWorker" in navigator) addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
</script>
</body>
</html>
"""

SW = """const CACHE = "spion-__VERSION__";
const CORE = ["./", "index.html", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png", "icons/apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  // Seite: erst Netz (für Updates), offline aus dem Cache
  if (req.mode === "navigate") {
    e.respondWith(fetch(req, { cache: "no-cache" }).then(res => {
      const copy = res.clone(); caches.open(CACHE).then(c => c.put("index.html", copy)); return res;
    }).catch(() => caches.match("index.html")));
    return;
  }
  // Icons, Schriften usw.: erst Cache, sonst Netz und merken
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(res => {
    if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  })));
});
"""


def draw_icon(size, pad=0.0):
    """Hut + Brille in Messing auf Nachtblau. pad = Rand für maskierbare Icons."""
    s = size
    img = Image.new("RGB", (s, s), BG)
    d = ImageDraw.Draw(img)
    k = s * (1 - 2 * pad) / 512
    o = s * pad
    P = lambda x, y: (o + x * k, o + y * k)
    # Hutkrone
    d.polygon([P(156, 250), P(184, 120), P(256, 140), P(328, 120), P(356, 250)], fill=BRASS)
    # Hutband
    d.rectangle([P(140, 222), P(372, 250)], fill=BG)
    # Krempe
    d.ellipse([P(80, 236), P(432, 300)], fill=BRASS)
    # Brille
    w = max(2, round(18 * k))
    d.ellipse([P(150, 318), P(240, 402)], outline=BRASS, width=w)
    d.ellipse([P(272, 318), P(362, 402)], outline=BRASS, width=w)
    d.line([P(238, 352), P(274, 352)], fill=BRASS, width=w)
    return img


def main():
    src = (ROOT / "spion.html").read_text(encoding="utf-8")
    version = hashlib.sha1((src + SW_REGISTER + HEAD).encode()).hexdigest()[:7]
    ver = f'<p style="text-align:center;font:11px ui-monospace,Menlo,monospace;color:#8ea3b3;opacity:.6;margin:0 0 16px">Version {version}</p>\n'
    html = HEAD + src.replace('<div id="app" class="wrap"></div>', '</head>\n<body>\n<div id="app" class="wrap"></div>\n' + ver, 1) + SW_REGISTER
    # <title>, Fonts und <style> aus spion.html landen im <head>, der Rest im <body>
    (OUT / "icons").mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")

    draw_icon(192).save(OUT / "icons/icon-192.png")
    draw_icon(512).save(OUT / "icons/icon-512.png")
    draw_icon(512, pad=0.1).save(OUT / "icons/icon-maskable-512.png")
    draw_icon(180, pad=0.04).save(OUT / "icons/apple-touch-icon.png")

    manifest = {
        "name": NAME, "short_name": SHORT, "lang": "de",
        "start_url": "./", "scope": "./", "display": "standalone", "orientation": "portrait",
        "background_color": BG, "theme_color": BG,
        "icons": [
            {"src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    (OUT / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    (OUT / "sw.js").write_text(SW.replace("__VERSION__", version), encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    print(f"docs/ gebaut, Version {version}")


if __name__ == "__main__":
    main()
