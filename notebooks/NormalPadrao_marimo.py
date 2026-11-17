# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pandas",
#     "scipy",
#     "anywidget",
#     "traitlets",
#     "jinja2",
# ]
# ///

# Canvas JS + live-drag, mesmo padrão usado em TLC_marimo.py /
# tStudent_marimo.py / LeiGrandesNumeros_marimo.py. Estrutura quase
# idêntica ao tStudent (curva + bandas de desvio-padrão + região
# selecionada + tabela), só que com a Normal padrão fixa (sem slider de
# graus de liberdade) e a tabela trocada pela tabela Z clássica (dois
# tipos, escolhidos por um radio).
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.stats import norm
    import anywidget
    import traitlets
    import json

    return mo, np, pd, norm, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("## Painel Interativo: Distribuição Normal Padrão")
    return


@app.cell
def _(mo):
    dist_radio = mo.ui.radio(
        options={
            "Tipo 1: P(-∞ < Z ≤ zc)": "T1",
            "Tipo 2: P(0 ≤ Z ≤ zc)": "T2",
        },
        value="Tipo 1: P(-∞ < Z ≤ zc)",
        label="Tipo de Tabela:",
    )
    slider_x1 = mo.ui.slider(start=-4.0, stop=4.0, step=0.01, value=-1.0, label="Z₁", debounce=False)
    slider_x2 = mo.ui.slider(start=-4.0, stop=4.0, step=0.01, value=1.0, label="Z₂", debounce=False)
    mo.vstack([dist_radio, slider_x1, slider_x2])
    return dist_radio, slider_x1, slider_x2


@app.cell
def _(anywidget, traitlets):
    # Widget criado UMA VEZ -- mesmo princípio do TLCGridWidget/TStudentWidget.
    class NormalWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 700, cssH = 380;

            const root = document.createElement("div");
            root.style.fontFamily = "system-ui, -apple-system, sans-serif";
            root.style.maxWidth = cssW + "px";

            const canvas = document.createElement("canvas");
            canvas.style.width = cssW + "px";
            canvas.style.height = cssH + "px";
            canvas.width = cssW * dpr;
            canvas.height = cssH * dpr;
            root.appendChild(canvas);
            el.appendChild(root);

            const BANDS = [
                [-4, 4, "#274d4d"],
                [-3, 3, "#3b6f6f"],
                [-2, 2, "#5a9b9b"],
                [-1, 1, "#9fd6d6"],
            ];

            function fillBetween(ctx, lo, hi, curveX, curveY, xToPx, yToPx, style, alpha) {
                let started = false;
                let lastPx = null;
                ctx.save();
                ctx.globalAlpha = alpha;
                ctx.fillStyle = style;
                ctx.beginPath();
                for (let i = 0; i < curveX.length; i++) {
                    const xv = curveX[i];
                    if (xv < lo - 1e-9 || xv > hi + 1e-9) continue;
                    const px = xToPx(xv), py = yToPx(curveY[i]);
                    if (!started) {
                        ctx.moveTo(px, yToPx(0));
                        ctx.lineTo(px, py);
                        started = true;
                    } else {
                        ctx.lineTo(px, py);
                    }
                    lastPx = px;
                }
                if (started) {
                    ctx.lineTo(lastPx, yToPx(0));
                    ctx.closePath();
                    ctx.fill();
                }
                ctx.restore();
            }

            function draw() {
                const payload = JSON.parse(model.get("payload_json") || "{}");
                if (!payload.curve_x) return;

                const ctx = canvas.getContext("2d");
                const W = canvas.width, H = canvas.height;
                ctx.clearRect(0, 0, W, H);
                ctx.fillStyle = "#FFF5EE";
                ctx.fillRect(0, 0, W, H);

                const padL = 55 * dpr, padR = 20 * dpr, padT = 50 * dpr, padB = 50 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;
                const xlo = -4, xhi = 4, ylo = 0, yhi = 0.45;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                const curveX = payload.curve_x;
                const curveY = payload.curve_y;

                BANDS.forEach(([lo, hi, color]) => {
                    fillBetween(ctx, lo, hi, curveX, curveY, xToPx, yToPx, color, 0.9);
                });

                ctx.save();
                ctx.strokeStyle = "cyan";
                ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                for (let i = 0; i < curveX.length; i++) {
                    const px = xToPx(curveX[i]), py = yToPx(curveY[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                // linhas verticais de referência -3..3 (sólidas, não tracejadas --
                // o original não usa linestyle pontilhado aqui)
                ctx.save();
                ctx.strokeStyle = "#3b6f6f";
                ctx.lineWidth = 1 * dpr;
                (payload.refs || []).forEach(pt => {
                    const px = xToPx(pt.x);
                    ctx.beginPath();
                    ctx.moveTo(px, yToPx(0));
                    ctx.lineTo(px, yToPx(pt.y));
                    ctx.stroke();
                });
                ctx.restore();

                fillBetween(ctx, payload.sel_lo, payload.sel_hi, curveX, curveY, xToPx, yToPx, "yellow", 0.85);

                // rótulos de percentual fixos (regra 68-95-99.7)
                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = (11 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                (payload.percentuais || []).forEach(p => {
                    ctx.fillText(p.label, xToPx(p.x), yToPx(0.05));
                });
                ctx.restore();

                ctx.save();
                ctx.fillStyle = "red";
                ctx.font = "bold " + (16 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(
                    payload.prob_sel.toFixed(2) + "%",
                    xToPx((payload.sel_lo + payload.sel_hi) / 2),
                    yToPx(0.10)
                );
                ctx.fillStyle = "blue";
                ctx.font = "bold " + (11 * dpr) + "px system-ui, sans-serif";
                ctx.fillText(payload.x1.toFixed(2), xToPx(payload.x1), yToPx(0.004));
                ctx.fillText(payload.x2.toFixed(2), xToPx(payload.x2), yToPx(0.004));
                ctx.restore();

                ctx.save();
                ctx.strokeStyle = "#333";
                ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                ctx.fillStyle = "#333";
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                for (let xv = -4; xv <= 4; xv++) {
                    const px = xToPx(xv);
                    ctx.beginPath();
                    ctx.moveTo(px, padT + plotH);
                    ctx.lineTo(px, padT + plotH + 4 * dpr);
                    ctx.stroke();
                    ctx.fillText(xv + "σ", px, padT + plotH + 6 * dpr);
                }
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                for (let yv = 0; yv <= 0.4 + 1e-9; yv += 0.1) {
                    const py = yToPx(yv);
                    ctx.beginPath();
                    ctx.moveTo(padL - 4 * dpr, py);
                    ctx.lineTo(padL, py);
                    ctx.stroke();
                    ctx.fillText(yv.toFixed(1), padL - 7 * dpr, py);
                }

                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.font = (12 * dpr) + "px system-ui, sans-serif";
                ctx.fillText("Z-score", padL + plotW / 2, padT + plotH + 30 * dpr);

                ctx.save();
                ctx.translate(padL - 38 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Densidade de probabilidade", 0, 0);
                ctx.restore();
                ctx.restore();

                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.fillText("Distribuição Z-Score", padL + plotW / 2, padT - 20 * dpr);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (NormalWidget,)


@app.cell
def _(NormalWidget, mo):
    widget = mo.ui.anywidget(NormalWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, norm, slider_x1, slider_x2, widget, json):
    x1 = slider_x1.value
    x2 = slider_x2.value
    sel_lo, sel_hi = min(x1, x2), max(x1, x2)

    x = np.linspace(-4, 4, 801)
    y = norm.pdf(x)

    refs = [{"x": float(z), "y": float(norm.pdf(z))} for z in range(-3, 4)]
    percentuais = [
        {"x": -3.5, "label": "0.13%"}, {"x": -2.5, "label": "2.14%"},
        {"x": -1.5, "label": "13.59%"}, {"x": -0.5, "label": "34.13%"},
        {"x": 0.5, "label": "34.13%"}, {"x": 1.5, "label": "13.59%"},
        {"x": 2.5, "label": "2.14%"}, {"x": 3.5, "label": "0.13%"},
    ]
    prob_sel = (norm.cdf(sel_hi) - norm.cdf(sel_lo)) * 100

    payload = {
        "curve_x": x.tolist(),
        "curve_y": y.tolist(),
        "refs": refs,
        "percentuais": percentuais,
        "sel_lo": float(sel_lo),
        "sel_hi": float(sel_hi),
        "prob_sel": float(prob_sel),
        "x1": float(x1),
        "x2": float(x2),
        "seq": f"{x1}-{x2}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


@app.cell
def _(np, pd, norm):
    coluna_z = np.round(np.arange(0, 0.10, 0.01), 2)
    linha_z = np.round(np.arange(0, 3.6, 0.1), 1)

    def calcula_tabela_z(tipo: str) -> "pd.DataFrame":
        dados = np.zeros((len(linha_z), len(coluna_z)))
        for i, li in enumerate(linha_z):
            for j, co in enumerate(coluna_z):
                zc = li + co
                prob = norm.cdf(zc)
                if tipo == "T2":
                    prob -= 0.5
                dados[i, j] = round(prob, 4)
        return pd.DataFrame(dados, index=linha_z, columns=coluna_z)

    return (calcula_tabela_z,)


@app.cell
def _(mo, dist_radio, calcula_tabela_z):
    tabela_z = calcula_tabela_z(dist_radio.value)
    tabela_estilizada = tabela_z.style.set_caption("Tabela Z-Score").format("{:.4f}").set_table_styles(
        [{"selector": "th, td", "props": [("border", "1px solid black"), ("text-align", "center"), ("padding", "5px")]}]
    )
    mo.show_code(tabela_estilizada, position="below")
    return


if __name__ == "__main__":
    app.run()
