"""Point an exported notebook's index.html at the shared _pyodide-assets
folder instead of its own per-notebook copies of pyodide/packages/assets/
icons, so publishing N notebooks doesn't duplicate the ~78MB Pyodide+wheels
payload N times. Every asset reference in a fresh html-wasm export is a
plain relative `="./..."` attribute (favicon, assets/*, manifest, and the
<marimo-wasm data-pyodide-index-url/-lockfile-url/-pypi-index-url> trio) --
confirmed by grepping the generated index.html before running this, so a
blanket replace is safe here (would NOT be safe on a hand-written page).
"""
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
html = path.read_text(encoding="utf-8")
new_html, n = re.subn(r'="\./', '="../_pyodide-assets/', html)
path.write_text(new_html, encoding="utf-8")
print(f"{path}: rewrote {n} relative asset references to ../_pyodide-assets/")
