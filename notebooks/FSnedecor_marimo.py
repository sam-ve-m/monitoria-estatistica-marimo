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

# Curva F (assimétrica, dois graus de liberdade) + tabela de valores
# críticos que recalcula quando o dropdown de alfa muda, mesmo princípio
# do Qui2/tStudent.
#
# Os sliders F1/F2 usam uma faixa estática larga (0-30) que cobre
# confortavelmente o pior caso comum de sala de aula, em vez de reajustar
# o máximo dinamicamente conforme gl1/gl2 mudam; o aluno ainda escolhe
# qualquer F1/F2 válido dentro dela.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.stats import f as f_dist
    import anywidget
    import traitlets
    import json

    return mo, np, pd, f_dist, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("## Painel Interativo: Distribuição F-Snedecor")
    return


@app.cell
def _(mo):
    slider_gl1 = mo.ui.slider(start=1, stop=120, step=1, value=4, label="gl₁ (Numerador):", debounce=False)
    slider_gl2 = mo.ui.slider(start=1, stop=120, step=1, value=10, label="gl₂ (Denominador):", debounce=False)
    slider_x1 = mo.ui.slider(start=0.0, stop=30.0, step=0.05, value=0.5, label="F₁ (Início):", debounce=False)
    slider_x2 = mo.ui.slider(start=0.0, stop=30.0, step=0.05, value=3.5, label="F₂ (Fim):", debounce=False)
    seletor_alfa = mo.ui.dropdown(
        options={"α = 0.05 (5%)": 0.05, "α = 0.01 (1%)": 0.01, "α = 0.10 (10%)": 0.10},
        value="α = 0.05 (5%)", label="Signif. da Tabela (α):",
    )
    mo.vstack([slider_gl1, slider_gl2, slider_x1, slider_x2, seletor_alfa])
    return slider_gl1, slider_gl2, slider_x1, slider_x2, seletor_alfa


@app.cell
def _(anywidget, traitlets):
    class FSnedecorWidget(anywidget.AnyWidget):
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
                ctx.fillText("F₁=" + payload.x1.toFixed(2), xToPx(payload.a_plot), yToPx(-ymax * 0.05));
                ctx.fillText("F₂=" + payload.x2.toFixed(2), xToPx(payload.b_plot), yToPx(-ymax * 0.05));
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
                    ctx.fillText(xv.toFixed(1), px, padT + plotH + 6 * dpr);
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
                ctx.fillText("Valor de F", padL + plotW / 2, padT + plotH + 30 * dpr);
                ctx.save();
                ctx.translate(padL - 42 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Densidade de probabilidade", 0, 0);
                ctx.restore();
                ctx.restore();

                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.fillText(
                    "Distribuição F-Snedecor (gl₁ Numerador = " + payload.gl1 + " | gl₂ Denominador = " + payload.gl2 + ")",
                    padL + plotW / 2, padT - 22 * dpr
                );

                ctx.save();
                const legW = 190 * dpr, legH = 28 * dpr;
                const legX = padL + plotW - legW - 8 * dpr, legY = padT + 8 * dpr;
                ctx.fillStyle = "rgba(255,255,255,0.9)"; ctx.strokeStyle = "#999"; ctx.lineWidth = 1 * dpr;
                ctx.fillRect(legX, legY, legW, legH); ctx.strokeRect(legX, legY, legW, legH);
                ctx.fillStyle = "#274d4d"; ctx.globalAlpha = 0.5;
                ctx.fillRect(legX + 8 * dpr, legY + 8 * dpr, 20 * dpr, 12 * dpr);
                ctx.globalAlpha = 1;
                ctx.fillStyle = "#111"; ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "left"; ctx.textBaseline = "middle";
                ctx.fillText("F (gl₁=" + payload.gl1 + ", gl₂=" + payload.gl2 + ")", legX + 34 * dpr, legY + 14 * dpr);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (FSnedecorWidget,)


@app.cell
def _(FSnedecorWidget, mo):
    widget = mo.ui.anywidget(FSnedecorWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, f_dist, slider_gl1, slider_gl2, slider_x1, slider_x2, widget, json):
    gl1, gl2 = slider_gl1.value, slider_gl2.value
    x1, x2 = slider_x1.value, slider_x2.value
    limite_inferior, limite_superior = min(x1, x2), max(x1, x2)

    limite_x = max(5, float(f_dist.ppf(0.99, dfn=gl1, dfd=gl2)))
    x = np.linspace(0.001, limite_x, 1000)
    y = f_dist.pdf(x, dfn=gl1, dfd=gl2)
    ymax = min(2.0, float(y.max()) * 1.1)

    a_plot = min(limite_inferior, limite_x)
    b_plot = min(limite_superior, limite_x)
    prob_sel = float(f_dist.cdf(limite_superior, dfn=gl1, dfd=gl2) - f_dist.cdf(limite_inferior, dfn=gl1, dfd=gl2))

    payload = {
        "curve_x": x.tolist(), "curve_y": y.tolist(),
        "limite_x": limite_x, "ymax": ymax,
        "a_plot": float(a_plot), "b_plot": float(b_plot),
        "x1": float(x1), "x2": float(x2),
        "prob_sel": prob_sel * 100, "gl1": int(gl1), "gl2": int(gl2),
        "seq": f"{gl1}-{gl2}-{x1}-{x2}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return gl1, gl2


@app.cell
def _(np, pd, f_dist):
    valores_gl1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 20, 24, 30, 40, 60, 120]
    valores_gl2 = list(range(1, 31))
    colunas_f = [f"gl1 = {g}" for g in valores_gl1]

    def calcula_tabela_f(alfa):
        dados = np.zeros((len(valores_gl2), len(valores_gl1)))
        for i, g2 in enumerate(valores_gl2):
            for j, g1 in enumerate(valores_gl1):
                dados[i, j] = f_dist.ppf(1 - alfa, dfn=g1, dfd=g2)
        return pd.DataFrame(dados, index=valores_gl2, columns=colunas_f)

    return valores_gl1, valores_gl2, colunas_f, calcula_tabela_f


@app.cell
def _(mo, pd, gl1, gl2, seletor_alfa, valores_gl1, valores_gl2, colunas_f, calcula_tabela_f):
    tabela_f = calcula_tabela_f(seletor_alfa.value)
    col_destaque = f"gl1 = {gl1}"

    def estilo_intersecao(df):
        df_estilo = pd.DataFrame("", index=df.index, columns=df.columns)
        if gl2 in valores_gl2:
            df_estilo.loc[gl2, :] = "background-color: #FFFFE0;"
        if col_destaque in colunas_f:
            df_estilo.loc[:, col_destaque] = "background-color: #E0FFFF;"
        if gl2 in valores_gl2 and col_destaque in colunas_f:
            df_estilo.loc[gl2, col_destaque] = "background-color: #FF9999; font-weight: bold;"
        return df_estilo

    tabela_estilizada = (
        tabela_f.style
        .set_caption(f"Tabela de Valores Críticos F (Área à Direita, α = {seletor_alfa.value})")
        .format("{:.4f}")
        .set_table_styles([
            {"selector": "th, td", "props": [("border", "1px solid black"), ("text-align", "center"), ("font-size", "11px"), ("padding", "4px")]},
            {"selector": "caption", "props": [("font-weight", "bold"), ("font-size", "14px"), ("margin-bottom", "5px")]},
        ])
        .apply(estilo_intersecao, axis=None)
    )
    mo.show_code(tabela_estilizada, position="below")
    return


if __name__ == "__main__":
    app.run()
