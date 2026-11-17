# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "scipy",
#     "anywidget",
#     "traitlets",
# ]
# ///

# Versão generalizada do NormalPadrao_marimo.py (mu/sigma ajustáveis em vez
# de fixos em 0/1).
#
# Nota técnica: recriar um `mo.ui.slider` com bounds dependentes de outro
# slider é possível em marimo mas reconstrói o elemento (perde a posição
# "fina" do drag) -- em vez disso, X1/X2 usam uma faixa estática larga o
# bastante pra cobrir o pior caso (mu em ±50, sigma até 20 -> ±170); o aluno
# ainda escolhe qualquer X1/X2 válido, só com um slider mais longo.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import norm
    import anywidget
    import traitlets
    import json

    return mo, np, norm, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("## Distribuição Normal (Gaussiana) — Geral")
    return


@app.cell
def _(mo):
    slider_mu = mo.ui.slider(start=-50, stop=50, step=0.5, value=0, label="μ (média):", debounce=False)
    slider_sigma = mo.ui.slider(start=0.1, stop=20, step=0.1, value=1, label="σ (desvio):", debounce=False)
    slider_x1 = mo.ui.slider(start=-200, stop=200, step=0.1, value=-1, label="X₁:", debounce=False)
    slider_x2 = mo.ui.slider(start=-200, stop=200, step=0.1, value=1, label="X₂:", debounce=False)
    mo.vstack([slider_mu, slider_sigma, slider_x1, slider_x2])
    return slider_mu, slider_sigma, slider_x1, slider_x2


@app.cell
def _(anywidget, traitlets):
    class GaussianWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 700, cssH = 400;

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
                [0, 4, "#274d4d"], [0, 3, "#3b6f6f"], [0, 2, "#5a9b9b"], [0, 1, "#9fd6d6"],
            ];

            function fillBetween(ctx, lo, hi, curveX, curveY, xToPx, yToPx, style, alpha) {
                let started = false, lastPx = null;
                ctx.save();
                ctx.globalAlpha = alpha;
                ctx.fillStyle = style;
                ctx.beginPath();
                for (let i = 0; i < curveX.length; i++) {
                    const xv = curveX[i];
                    if (xv < lo - 1e-9 || xv > hi + 1e-9) continue;
                    const px = xToPx(xv), py = yToPx(curveY[i]);
                    if (!started) { ctx.moveTo(px, yToPx(0)); ctx.lineTo(px, py); started = true; }
                    else { ctx.lineTo(px, py); }
                    lastPx = px;
                }
                if (started) { ctx.lineTo(lastPx, yToPx(0)); ctx.closePath(); ctx.fill(); }
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

                const padL = 55 * dpr, padR = 20 * dpr, padT = 50 * dpr, padB = 60 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;
                const mu = payload.mu, sigma = payload.sigma;
                const xlo = mu - 4 * sigma, xhi = mu + 4 * sigma;
                const ylo = 0, yhi = payload.yhi;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                const curveX = payload.curve_x, curveY = payload.curve_y;

                BANDS.forEach(([_, k, color]) => {
                    fillBetween(ctx, mu - k * sigma, mu + k * sigma, curveX, curveY, xToPx, yToPx, color, 0.9);
                });

                ctx.save();
                ctx.strokeStyle = "cyan"; ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                for (let i = 0; i < curveX.length; i++) {
                    const px = xToPx(curveX[i]), py = yToPx(curveY[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                ctx.save();
                ctx.strokeStyle = "#3b6f6f"; ctx.lineWidth = 1 * dpr;
                (payload.refs || []).forEach(pt => {
                    const px = xToPx(pt.x);
                    ctx.beginPath(); ctx.moveTo(px, yToPx(0)); ctx.lineTo(px, yToPx(pt.y)); ctx.stroke();
                });
                ctx.restore();

                fillBetween(ctx, payload.sel_lo, payload.sel_hi, curveX, curveY, xToPx, yToPx, "yellow", 0.85);

                ctx.save();
                ctx.fillStyle = "#111"; ctx.font = (11 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "middle";
                (payload.percentuais || []).forEach(p => ctx.fillText(p.label, xToPx(p.x), yToPx(payload.ymax_ref * 0.12)));
                ctx.restore();

                ctx.save();
                ctx.fillStyle = "red"; ctx.font = "bold " + (16 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "middle";
                ctx.fillText(payload.prob_sel.toFixed(2) + "%", xToPx((payload.sel_lo + payload.sel_hi) / 2), yToPx(payload.ymax_ref * 0.25));
                ctx.fillStyle = "blue"; ctx.font = "bold " + (11 * dpr) + "px system-ui, sans-serif";
                ctx.fillText(payload.x1.toFixed(2), xToPx(payload.x1), yToPx(payload.ymax_ref * 0.01));
                ctx.fillText(payload.x2.toFixed(2), xToPx(payload.x2), yToPx(payload.ymax_ref * 0.01));
                ctx.restore();

                ctx.save();
                ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                ctx.fillStyle = "#333"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                (payload.xticks || []).forEach(t => {
                    const px = xToPx(t.v);
                    ctx.save();
                    ctx.translate(px, padT + plotH + 14 * dpr);
                    ctx.rotate(-Math.PI / 4);
                    ctx.fillText(t.label, 0, 0);
                    ctx.restore();
                    ctx.beginPath();
                    ctx.moveTo(px, padT + plotH); ctx.lineTo(px, padT + plotH + 4 * dpr); ctx.stroke();
                });

                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                for (let t = 0; t <= 4; t++) {
                    const yv = yhi * (t / 4);
                    const py = yToPx(yv);
                    ctx.beginPath(); ctx.moveTo(padL - 4 * dpr, py); ctx.lineTo(padL, py); ctx.stroke();
                    ctx.fillText(yv.toFixed(3), padL - 7 * dpr, py);
                }

                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.font = (12 * dpr) + "px system-ui, sans-serif";
                ctx.fillText("X", padL + plotW / 2, padT + plotH + 44 * dpr);
                ctx.save();
                ctx.translate(padL - 42 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Densidade de probabilidade", 0, 0);
                ctx.restore();
                ctx.restore();

                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.fillText(payload.title, padL + plotW / 2, padT - 20 * dpr);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (GaussianWidget,)


@app.cell
def _(GaussianWidget, mo):
    widget = mo.ui.anywidget(GaussianWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, norm, slider_mu, slider_sigma, slider_x1, slider_x2, widget, json):
    mu = slider_mu.value
    sigma = slider_sigma.value
    x1 = slider_x1.value
    x2 = slider_x2.value
    sel_lo, sel_hi = min(x1, x2), max(x1, x2)

    x = np.linspace(mu - 4 * sigma, mu + 4 * sigma, 801)
    y = norm.pdf(x, loc=mu, scale=sigma)
    ymax_ref = float(norm.pdf(mu, loc=mu, scale=sigma))

    refs = [{"x": float(mu + n * sigma), "y": float(norm.pdf(mu + n * sigma, loc=mu, scale=sigma))} for n in range(-3, 4)]
    percentuais = [
        {"x": mu - 3.5 * sigma, "label": "0.13%"}, {"x": mu - 2.5 * sigma, "label": "2.14%"},
        {"x": mu - 1.5 * sigma, "label": "13.59%"}, {"x": mu - 0.5 * sigma, "label": "34.13%"},
        {"x": mu + 0.5 * sigma, "label": "34.13%"}, {"x": mu + 1.5 * sigma, "label": "13.59%"},
        {"x": mu + 2.5 * sigma, "label": "2.14%"}, {"x": mu + 3.5 * sigma, "label": "0.13%"},
    ]
    xticks = [{"v": float(mu + k * sigma), "label": f"{mu + k * sigma:.2f}"} for k in range(-4, 5)]
    prob_sel = float((norm.cdf(sel_hi, loc=mu, scale=sigma) - norm.cdf(sel_lo, loc=mu, scale=sigma)) * 100)

    payload = {
        "curve_x": x.tolist(), "curve_y": y.tolist(),
        "mu": float(mu), "sigma": float(sigma),
        "ymax_ref": ymax_ref, "yhi": ymax_ref * 1.15,
        "refs": refs, "percentuais": percentuais, "xticks": xticks,
        "sel_lo": float(sel_lo), "sel_hi": float(sel_hi), "prob_sel": prob_sel,
        "x1": float(x1), "x2": float(x2),
        "title": f"Distribuição Normal (μ={mu:.2f}, σ={sigma:.2f})",
        "seq": f"{mu}-{sigma}-{x1}-{x2}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
