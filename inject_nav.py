"""Inject a shared top navigation bar AND a full-page loading overlay into an
exported marimo html-wasm index.html, so each notebook page links back to the
site index/siblings and never shows a blank unfeedback gap while Pyodide
boots and the first chart renders, without touching marimo's own export
pipeline.

Usage:
    python inject_nav.py <path/to/index.html> <current_slug>

`current_slug` is one of the keys in NOTEBOOKS below (used to highlight the
active link and to skip adding a self-link).
"""
import re
import sys
from pathlib import Path

# Shared catalog of published notebooks -- add an entry here for each of the
# other 10 once migrated, and every page's nav bar picks it up automatically
# next time this script runs.
NOTEBOOKS = {
    "TLC": "Teorema Central do Limite",
    "tStudent": "Distribuição t-Student",
    "LeiGrandesNumeros": "Lei dos Grandes Números",
    "NormalPadrao": "Normal Padrão (Z)",
    "Logistico5Par": "Logístico 5 Parâmetros",
    "Gaussiana": "Normal (μ, σ ajustáveis)",
    "Qui2": "Qui-Quadrado (χ²)",
    "FSnedecor": "F-Snedecor",
    "DistribuicoesDiscretas": "Discretas (PMF/CDF)",
    "VariaveisAletorias": "Variáveis Aleatórias",
    "DistribuicoesContinuasPrincipais": "Contínuas Principais",
    "DistribuicoesPrincipais": "Discretas + Contínuas",
}

NAV_CSS = """
<style id="monitoria-nav-style">
  #monitoria-nav {
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    display: flex;
    align-items: center;
    gap: 4px;
    flex-wrap: wrap;
    padding: 10px 20px;
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    position: relative;
    z-index: 2147483000;
  }
  #monitoria-nav .brand {
    font-weight: 700;
    color: #1e293b;
    margin-right: 18px;
    text-decoration: none;
    font-size: 0.95rem;
    white-space: nowrap;
  }
  #monitoria-nav a.nb-link {
    text-decoration: none;
    color: #475569;
    font-size: 0.88rem;
    padding: 6px 12px;
    border-radius: 6px;
    transition: background 0.15s, color 0.15s;
  }
  #monitoria-nav a.nb-link:hover {
    background: #eef2ff;
    color: #2563eb;
  }
  #monitoria-nav a.nb-link.active {
    background: #2563eb;
    color: #ffffff;
    font-weight: 600;
  }
  #monitoria-nav .spacer { flex: 1 1 auto; }
  #monitoria-nav .hint {
    font-size: 0.78rem;
    color: #94a3b8;
    white-space: nowrap;
  }
</style>
"""


# Full-page loading overlay: masks marimo's native spinner and the blank gap
# after it, until the first real draw of the widget's canvas sets
# data-render-seq (a signal common to all 12 notebooks' anywidget JS).
LOADING_OVERLAY_HTML = """
<div id="monitoria-loading-overlay">
  <style id="monitoria-loading-overlay-style">
    #monitoria-loading-overlay {
      position: fixed;
      inset: 0;
      z-index: 2147483647;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 18px;
      background: #ffffff;
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      transition: opacity 0.25s ease;
    }
    #monitoria-loading-overlay .monitoria-spinner {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      border: 5px solid #e5e7eb;
      border-top-color: #2563eb;
      animation: monitoria-spin 0.9s linear infinite;
    }
    #monitoria-loading-overlay .monitoria-loading-text {
      color: #475569;
      font-size: 0.95rem;
    }
    @keyframes monitoria-spin {
      to { transform: rotate(360deg); }
    }
  </style>
  <div class="monitoria-spinner"></div>
  <div class="monitoria-loading-text">Carregando...</div>
</div>
<script id="monitoria-loading-overlay-script">
(function () {
  var overlay = document.getElementById("monitoria-loading-overlay");
  if (!overlay) return;
  var hidden = false;
  function hideOverlay() {
    if (hidden) return;
    hidden = true;
    overlay.style.opacity = "0";
    setTimeout(function () {
      if (overlay && overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
    }, 300);
    clearInterval(pollId);
    clearTimeout(fallbackId);
  }
  // The anywidget root carrying data-render-seq lives inside a shadow root
  // (marimo's own custom elements), so a plain document.querySelector never
  // finds it -- walk shadow roots too, same approach confirmed working in
  // visual_confirm.py's Playwright checks.
  function deepHasRenderSeq(root) {
    if (root.querySelector("[data-render-seq]")) return true;
    var all = root.querySelectorAll("*");
    for (var i = 0; i < all.length; i++) {
      if (all[i].shadowRoot && deepHasRenderSeq(all[i].shadowRoot)) return true;
    }
    return false;
  }
  var pollId = setInterval(function () {
    if (deepHasRenderSeq(document)) {
      hideOverlay();
    }
  }, 100);
  var fallbackId = setTimeout(hideOverlay, 25000);
})();
</script>
"""


def build_nav_html(current_slug: str) -> str:
    links = []
    for slug, label in NOTEBOOKS.items():
        cls = "nb-link active" if slug == current_slug else "nb-link"
        links.append(f'<a class="{cls}" href="../{slug}/">{label}</a>')
    return (
        NAV_CSS
        + '<nav id="monitoria-nav">'
        + '<a class="brand" href="../">📊 Monitoria de Estatística UTFPR</a>'
        + "".join(links)
        + '<span class="spacer"></span>'
        + '<span class="hint">roda 100% no seu navegador — sem servidor</span>'
        + "</nav>"
    )


def inject(index_html_path: Path, current_slug: str) -> None:
    html = index_html_path.read_text(encoding="utf-8")
    # Idempotent: strip a previously-injected nav and loading overlay before
    # re-adding either, so re-running this script after a re-export doesn't
    # duplicate them.
    html = re.sub(
        r'<style id="monitoria-nav-style">.*?</nav>',
        "",
        html,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<div id="monitoria-loading-overlay">.*?</script>',
        "",
        html,
        flags=re.DOTALL,
    )
    nav = build_nav_html(current_slug)
    # Overlay goes in first (so it visually sits on top and is present the
    # instant <body> parses), nav right after it.
    html = html.replace("<body>", "<body>" + LOADING_OVERLAY_HTML + nav, 1)
    index_html_path.write_text(html, encoding="utf-8")
    print(f"Nav + loading overlay injected into {index_html_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    inject(Path(sys.argv[1]), sys.argv[2])
