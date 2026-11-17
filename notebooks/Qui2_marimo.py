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

# Curva assimétrica (fill_between inteiro + região selecionada em amarelo)
# + tabela de valores críticos, mesmo princípio do FSnedecor/tStudent.
#
# Os sliders χ²₁/χ²₂ usam uma faixa estática larga (0-150) que cobre o
# pior caso (gl até 50 -> limite_x ~100), em vez de reajustar
# dinamicamente o máximo conforme o gl muda.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.stats import chi2
    import anywidget
    import traitlets
    import json

    return mo, np, pd, chi2, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("## Painel Interativo: Distribuição Qui-Quadrado")
    return


@app.cell
def _(mo):
    slider_gl = mo.ui.slider(start=1, stop=50, step=1, value=4, label="Graus de Lib. (gl):", debounce=False)
    slider_x1 = mo.ui.slider(start=0.0, stop=150.0, step=0.1, value=1.0, label="χ²₁ (Início):", debounce=False)
    slider_x2 = mo.ui.slider(start=0.0, stop=150.0, step=0.1, value=7.0, label="χ²₂ (Fim):", debounce=False)
    mo.vstack([slider_gl, slider_x1, slider_x2])
    return slider_gl, slider_x1, slider_x2


@app.cell
def _(anywidget, traitlets):
    class Chi2Widget(anywidget.AnyWidget):
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

            function fillUnder(ctx, curveX, curveY, xToPx, yToPx, style, alpha, lo, hi) {
                ctx.save();
                ctx.globalAlpha = alpha;
                ctx.fillStyle = style;
                ctx.beginPath();
                let started = false, lastPx = null;
                for (let i = 0; i < curveX.length; i++) {
                    const xv = curveX[i];
                    if (lo !== undefined && (xv < lo || xv > hi)) continue;
                    const px = xToPx(xv), py = yToPx(curveY[i]);
                    if (!started) { ctx.moveTo(px, yToPx(0)); ctx.lineTo(px, py); started = true; }
                    else ctx.lineTo(px, py);
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

                const padL = 60 * dpr, padR = 20 * dpr, padT = 55 * dpr, padB = 55 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;
                const xlo = 0, xhi = payload.limite_x;
                const ymax = payload.ymax;
                const ylo = -ymax * 0.08, yhi = ymax * 1.1;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                const curveX = payload.curve_x, curveY = payload.curve_y;

                fillUnder(ctx, curveX, curveY, xToPx, yToPx, "#274d4d", 0.3);

                ctx.save();
                ctx.strokeStyle = "darkslategray"; ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                for (let i = 0; i < curveX.length; i++) {
                    const px = xToPx(curveX[i]), py = yToPx(curveY[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                fillUnder(ctx, curveX, curveY, xToPx, yToPx, "yellow", 0.7, payload.a_plot, payload.b_plot);

                ctx.save();
                ctx.fillStyle = "red"; ctx.font = "bold " + (16 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "middle";
                ctx.fillText(payload.prob_sel.toFixed(2) + "%", xToPx((payload.a_plot + payload.b_plot) / 2), yToPx(ymax * 0.4));
                ctx.fillStyle = "blue"; ctx.font = "bold " + (11 * dpr) + "px system-ui, sans-serif";
                ctx.fillText("χ²₁=" + payload.x1.toFixed(2), xToPx(payload.a_plot), yToPx(-ymax * 0.05));
                ctx.fillText("χ²₂=" + payload.x2.toFixed(2), xToPx(payload.b_plot), yToPx(-ymax * 0.05));
                ctx.restore();

                ctx.save();
                ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                ctx.fillStyle = "#333"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "top";
                const nTicks = 6;
                for (let t = 0; t <= nTicks; t++) {
                    const xv = xlo + (xhi - xlo) * (t / nTicks);
                    const px = xToPx(xv);
                    ctx.beginPath(); ctx.moveTo(px, padT + plotH); ctx.lineTo(px, padT + plotH + 4 * dpr); ctx.stroke();
                    ctx.fillText(xv.toFixed(0), px, padT + plotH + 6 * dpr);
                }
                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                for (let t = 0; t <= 4; t++) {
                    const yv = ymax * (t / 4);
                    const py = yToPx(yv);
                    ctx.beginPath(); ctx.moveTo(padL - 4 * dpr, py); ctx.lineTo(padL, py); ctx.stroke();
                    ctx.fillText(yv.toFixed(3), padL - 7 * dpr, py);
                }

                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.font = (12 * dpr) + "px system-ui, sans-serif";
                ctx.fillText("Valor de χ²", padL + plotW / 2, padT + plotH + 30 * dpr);
                ctx.save();
                ctx.translate(padL - 42 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Densidade de probabilidade", 0, 0);
                ctx.restore();
                ctx.restore();

                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.fillText("Distribuição Qui-Quadrado (Graus de Liberdade = " + payload.gl + ")", padL + plotW / 2, padT - 22 * dpr);

                ctx.save();
                const legW = 170 * dpr, legH = 28 * dpr;
                const legX = padL + plotW - legW - 8 * dpr, legY = padT + 8 * dpr;
                ctx.fillStyle = "rgba(255,255,255,0.9)"; ctx.strokeStyle = "#999"; ctx.lineWidth = 1 * dpr;
                ctx.fillRect(legX, legY, legW, legH); ctx.strokeRect(legX, legY, legW, legH);
                ctx.fillStyle = "#274d4d"; ctx.globalAlpha = 0.5;
                ctx.fillRect(legX + 8 * dpr, legY + 8 * dpr, 20 * dpr, 12 * dpr);
                ctx.globalAlpha = 1;
                ctx.fillStyle = "#111"; ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "left"; ctx.textBaseline = "middle";
                ctx.fillText("Qui-Quadrado (gl=" + payload.gl + ")", legX + 34 * dpr, legY + 14 * dpr);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (Chi2Widget,)


@app.cell
def _(Chi2Widget, mo):
    widget = mo.ui.anywidget(Chi2Widget())
    widget
    return (widget,)


@app.cell
def _(mo, np, chi2, slider_gl, slider_x1, slider_x2, widget, json):
    gl = slider_gl.value
    x1 = slider_x1.value
    x2 = slider_x2.value
    limite_inferior, limite_superior = min(x1, x2), max(x1, x2)

    limite_x = max(20, gl + 4 * np.sqrt(2 * gl))
    x = np.linspace(0.001, limite_x, 1000)
    y = chi2.pdf(x, df=gl)

    a_plot = min(limite_inferior, limite_x)
    b_plot = min(limite_superior, limite_x)
    prob_sel = float(chi2.cdf(limite_superior, df=gl) - chi2.cdf(limite_inferior, df=gl))

    payload = {
        "curve_x": x.tolist(), "curve_y": y.tolist(),
        "limite_x": float(limite_x), "ymax": float(y.max()),
        "a_plot": float(a_plot), "b_plot": float(b_plot),
        "x1": float(x1), "x2": float(x2),
        "prob_sel": prob_sel * 100, "gl": int(gl),
        "seq": f"{gl}-{x1}-{x2}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return (gl,)


@app.cell
def _(np, pd, chi2):
    probabilidades_alfa = [0.99, 0.975, 0.95, 0.90, 0.10, 0.05, 0.025, 0.01]
    colunas_chi = [f"α = {p}" for p in probabilidades_alfa]
    linhas_gl_chi = list(range(1, 31))

    def calcula_tabela_chi():
        dados = np.zeros((len(linhas_gl_chi), len(probabilidades_alfa)))
        for i, g in enumerate(linhas_gl_chi):
            for j, alpha in enumerate(probabilidades_alfa):
                dados[i, j] = chi2.ppf(1 - alpha, df=g)
        return pd.DataFrame(dados, index=linhas_gl_chi, columns=colunas_chi)

    tabela_chi = calcula_tabela_chi()
    return linhas_gl_chi, tabela_chi


@app.cell
def _(mo, pd, gl, linhas_gl_chi, tabela_chi):
    def destaca_linha(valor):
        return "background-color: #FFFF99;" if gl in linhas_gl_chi else ""

    tabela_estilizada = tabela_chi.style.set_caption(
        "Tabela de Valores Críticos de Qui-Quadrado (Área à Direita)"
    ).format("{:.4f}").set_table_styles(
        [
            {"selector": "th, td", "props": [("border", "1px solid black"), ("text-align", "center"), ("padding", "5px")]},
            {"selector": "caption", "props": [("font-weight", "bold"), ("font-size", "14px")]},
        ]
    ).map(destaca_linha, subset=pd.IndexSlice[[gl] if gl in linhas_gl_chi else [], :])
    mo.show_code(tabela_estilizada, position="below")
    return


if __name__ == "__main__":
    app.run()
