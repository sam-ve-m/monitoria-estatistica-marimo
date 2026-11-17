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

# Mesma técnica de canvas JS + live-drag usada no TLC_marimo.py, aplicada
# aqui ao painel de t-Student (1 gráfico em vez de 9, mesmo princípio):
# Python só calcula os NÚMEROS -- curva de densidade, pontos tracejados,
# região selecionada -- e um widget anywidget desenha tudo num <canvas> via
# JavaScript, sem pagar rasterização+encode de PNG matplotlib a cada
# arrasto do slider.
#
# debounce=False nos três sliders: o marimo sincroniza o valor
# continuamente DURANTE o arrasto (não só ao soltar), então a célula
# reativa roda a cada passo do drag -- viável porque o replot no canvas é
# barato.
#
# A tabela de valores críticos (última célula) não desenha a curva --
# segue como estava, só com mo.show_code(tabela_estilizada, ...) de uma
# tabela pandas estilizada, sem o custo de rasterização que afetava o
# gráfico; não precisou da mudança pra canvas.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import pandas as pd
    from scipy.stats import t as t_dist
    import anywidget
    import traitlets
    import json

    return mo, np, pd, t_dist, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("## Painel Interativo: Distribuição t-Student")
    return


@app.cell
def _(mo):
    # debounce=False (ver nota no topo do arquivo): o gráfico recalcula a
    # cada passo do arrasto, não só ao soltar.
    slider_gl = mo.ui.slider(start=1, stop=120, step=1, value=10, label="Graus de Lib. (gl):", debounce=False)
    slider_x1 = mo.ui.slider(start=-4.0, stop=4.0, step=0.01, value=-1.0, label="t₁", debounce=False)
    slider_x2 = mo.ui.slider(start=-4.0, stop=4.0, step=0.01, value=1.0, label="t₂", debounce=False)
    mo.vstack([slider_gl, slider_x1, slider_x2])
    return slider_gl, slider_x1, slider_x2


@app.cell
def _(anywidget, traitlets):
    # Widget criado UMA VEZ, igual ao TLCGridWidget -- a célula reativa
    # abaixo só muta o trait `payload_json`, nunca recria o DOM do canvas.
    class TStudentWidget(anywidget.AnyWidget):
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

            // Constrói o caminho de preenchimento "fill_between(x_in_range,
            // 0, y_in_range)" igual ao matplotlib: sobe pela curva dentro do
            // intervalo [lo, hi] e desce de volta pela linha de base (y=0).
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

                // fig.patch / ax facecolor = "#FFF5EE"
                ctx.fillStyle = "#FFF5EE";
                ctx.fillRect(0, 0, W, H);

                const padL = 55 * dpr, padR = 20 * dpr, padT = 56 * dpr, padB = 50 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;
                const xlo = -4, xhi = 4, ylo = -0.03, yhi = 0.45;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                const curveX = payload.curve_x;
                const curveY = payload.curve_y;

                // 1) bandas de cor sob a curva (camadas, mais estreita por
                // cima -- mesma ordem do cores_camadas original).
                BANDS.forEach(([lo, hi, color]) => {
                    fillBetween(ctx, lo, hi, curveX, curveY, xToPx, yToPx, color, 0.9);
                });

                // 2) curva principal (cyan)
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

                // 3) linhas verticais tracejadas nos pontos inteiros -3..3
                ctx.save();
                ctx.strokeStyle = "#3b6f6f";
                ctx.lineWidth = 1 * dpr;
                ctx.setLineDash([4 * dpr, 4 * dpr]);
                (payload.dashed || []).forEach(pt => {
                    const px = xToPx(pt.x);
                    ctx.beginPath();
                    ctx.moveTo(px, yToPx(0));
                    ctx.lineTo(px, yToPx(pt.y));
                    ctx.stroke();
                });
                ctx.restore();

                // 4) região selecionada (amarelo, por cima de tudo até aqui)
                fillBetween(ctx, payload.sel_lo, payload.sel_hi, curveX, curveY, xToPx, yToPx, "yellow", 0.7);

                // 5) textos: probabilidade da região selecionada + rótulos t1/t2
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
                ctx.fillText("t₁=" + payload.x1.toFixed(2), xToPx(payload.x1), yToPx(-0.015));
                ctx.fillText("t₂=" + payload.x2.toFixed(2), xToPx(payload.x2), yToPx(-0.015));
                ctx.restore();

                // 6) eixos: moldura, ticks x inteiros -4..4, ticks y
                ctx.save();
                ctx.strokeStyle = "#333";
                ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                ctx.fillStyle = "#333";
                ctx.font = (11 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                for (let xv = -4; xv <= 4; xv++) {
                    const px = xToPx(xv);
                    ctx.beginPath();
                    ctx.moveTo(px, padT + plotH);
                    ctx.lineTo(px, padT + plotH + 4 * dpr);
                    ctx.stroke();
                    ctx.fillText(xv, px, padT + plotH + 6 * dpr);
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
                ctx.fillText("Valor t", padL + plotW / 2, padT + plotH + 30 * dpr);

                ctx.save();
                ctx.translate(padL - 38 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Densidade de probabilidade", 0, 0);
                ctx.restore();
                ctx.restore();

                // 7) titulo
                ctx.save();
                ctx.fillStyle = "#111";
                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.fillText(
                    "Distribuição t-Student (Graus de Liberdade = " + payload.gl + ")",
                    padL + plotW / 2, padT - 28 * dpr
                );
                ctx.restore();

                // 8) legenda (canto superior direito)
                ctx.save();
                const legX = padL + plotW - 150 * dpr, legY = padT + 10 * dpr;
                ctx.fillStyle = "rgba(255,255,255,0.85)";
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1 * dpr;
                ctx.fillRect(legX, legY, 150 * dpr, 24 * dpr);
                ctx.strokeRect(legX, legY, 150 * dpr, 24 * dpr);
                ctx.strokeStyle = "cyan";
                ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                ctx.moveTo(legX + 8 * dpr, legY + 12 * dpr);
                ctx.lineTo(legX + 28 * dpr, legY + 12 * dpr);
                ctx.stroke();
                ctx.fillStyle = "#111";
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";
                ctx.fillText("t-Student (gl=" + payload.gl + ")", legX + 34 * dpr, legY + 12 * dpr);
                ctx.restore();

                // Sinaliza pro lado Python/medição que o redesenho terminou
                // (equivalente ao data-render-seq do TLCGridWidget) -- muda
                // a cada replot, inclusive os intermediários durante um
                // arrasto em live-drag.
                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (TStudentWidget,)


@app.cell
def _(TStudentWidget, mo):
    widget = mo.ui.anywidget(TStudentWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, t_dist, slider_gl, slider_x1, slider_x2, widget, json):
    gl = slider_gl.value
    x1 = slider_x1.value
    x2 = slider_x2.value

    sel_lo, sel_hi = min(x1, x2), max(x1, x2)

    x = np.linspace(-4, 4, 801)
    y_t = t_dist.pdf(x, df=gl)

    prob_sel = (t_dist.cdf(sel_hi, df=gl) - t_dist.cdf(sel_lo, df=gl)) * 100

    dashed = [
        {"x": float(ponto), "y": float(t_dist.pdf(ponto, df=gl))}
        for ponto in range(-3, 4)
    ]

    payload = {
        "curve_x": x.tolist(),
        "curve_y": y_t.tolist(),
        "dashed": dashed,
        "sel_lo": float(sel_lo),
        "sel_hi": float(sel_hi),
        "prob_sel": float(prob_sel),
        "x1": float(x1),
        "x2": float(x2),
        "gl": int(gl),
        "seq": f"{gl}-{x1}-{x2}",
    }
    widget.payload_json = json.dumps(payload)
    # mo.show_code(..., position="below"): gráfico primeiro, código desta
    # célula abaixo dele -- sem argumento de output, já que não existe mais
    # Figure nenhuma (mesmo padrão do TLC_marimo.py canvas).
    mo.show_code(position="below")
    return


@app.cell
def _(np, pd, t_dist):
    probabilidades_cauda = [0.10, 0.05, 0.025, 0.01, 0.005]
    colunas_t = [f"α = {p}" for p in probabilidades_cauda]
    linhas_gl = list(range(1, 31)) + [40, 60, 120]

    def calcula_tabela_t():
        dados = np.zeros((len(linhas_gl), len(probabilidades_cauda)))
        for i, gl_lin in enumerate(linhas_gl):
            for j, alpha in enumerate(probabilidades_cauda):
                dados[i, j] = t_dist.ppf(1 - alpha, df=gl_lin)
        return pd.DataFrame(dados, index=linhas_gl, columns=colunas_t)

    tabela_t = calcula_tabela_t()
    return colunas_t, linhas_gl, tabela_t


@app.cell
def _(mo, pd, slider_gl, linhas_gl, tabela_t):
    gl_atual = slider_gl.value

    def destaca_linha_do_gl_escolhido(valor):
        if gl_atual in linhas_gl:
            return "background-color: #FFFF99;"
        return ""

    tabela_estilizada = tabela_t.style.set_caption("Tabela de Valores Críticos t (Cauda Superior)").format("{:.4f}").set_table_styles(
        [
            {"selector": "th, td", "props": [("border", "1px solid black"), ("text-align", "center"), ("padding", "5px")]},
            {"selector": "caption", "props": [("font-weight", "bold"), ("font-size", "14px")]},
        ]
    ).map(
        destaca_linha_do_gl_escolhido,
        subset=pd.IndexSlice[[gl_atual] if gl_atual in linhas_gl else [], :],
    )
    mo.show_code(tabela_estilizada, position="below")
    return


if __name__ == "__main__":
    app.run()
