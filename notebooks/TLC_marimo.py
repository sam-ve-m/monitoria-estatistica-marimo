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

# Canvas JS + atualização em tempo real durante o arrasto do slider: não
# existe uma Figure matplotlib real aqui -- o widget `anywidget` abaixo
# recebe só os números (bordas/contagens de cada histograma + pontos da
# curva normal) via um trait `payload_json` e desenha os 9 painéis num grid
# de <canvas> em JavaScript puro (sem CDN, 100% offline). O código Python
# mostrado abaixo (`mo.show_code(position="below")`, sem argumento de
# output) é o cálculo desses números, não o código que desenha os pixels.
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
    mo.md("# Teorema Central do Limite — piloto marimo")
    return


@app.cell
def _(mo):
    w_dist = mo.ui.radio(
        options=["Exponencial", "Binomial", "Poisson"],
        value="Exponencial",
        label="Distribuição:",
    )
    # debounce=False: o marimo sincroniza o valor do slider continuamente
    # DURANTE o arrasto (não só ao soltar) -- a célula reativa abaixo roda a
    # cada passo do drag, recalculando e redesenhando no <canvas> a cada
    # novo N. Isso é viável porque o replot no canvas é muito barato (não
    # paga o custo de rasterizar/codificar um PNG matplotlib a cada passo).
    w_N = mo.ui.slider(
        start=50, stop=1000, step=50, value=200,
        label="Repetições (N):", debounce=False,
    )
    mo.hstack([w_dist, w_N])
    return w_dist, w_N


@app.cell
def _(anywidget, traitlets):
    # Widget criado UMA VEZ (célula sem dependência dos widgets de controle)
    # -- a célula reativa abaixo só MUTA o trait `payload_json`, nunca
    # recria o widget, pra não pagar destruição+remontagem de DOM a cada
    # replot (importante ainda mais agora que o replot pode acontecer várias
    # vezes por segundo durante um arrasto rápido).
    class TLCGridWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const N_PANELS = 9;
            const grid = document.createElement("div");
            grid.style.display = "grid";
            grid.style.gridTemplateColumns = "repeat(3, 1fr)";
            grid.style.gap = "4px";
            grid.style.maxWidth = "700px";
            grid.style.fontFamily = "system-ui, -apple-system, sans-serif";

            const header = document.createElement("div");
            header.style.textAlign = "center";
            header.style.marginBottom = "4px";
            const h1 = document.createElement("div");
            h1.style.fontWeight = "bold";
            h1.style.fontSize = "16px";
            const h2 = document.createElement("div");
            h2.style.fontSize = "11px";
            h2.style.color = "gray";
            header.appendChild(h1);
            header.appendChild(h2);

            const canvases = [];
            for (let i = 0; i < N_PANELS; i++) {
                const wrap = document.createElement("div");
                const c = document.createElement("canvas");
                const cssW = 220, cssH = 170;
                const dpr = window.devicePixelRatio || 1;
                c.style.width = cssW + "px";
                c.style.height = cssH + "px";
                c.width = cssW * dpr;
                c.height = cssH * dpr;
                wrap.appendChild(c);
                grid.appendChild(wrap);
                canvases.push(c);
            }

            const root = document.createElement("div");
            root.appendChild(header);
            root.appendChild(grid);
            el.appendChild(root);

            function drawPanel(canvas, panel) {
                const dpr = window.devicePixelRatio || 1;
                const ctx = canvas.getContext("2d");
                const W = canvas.width, H = canvas.height;
                ctx.save();
                ctx.clearRect(0, 0, W, H);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, W, H);

                const padL = 32 * dpr, padR = 8 * dpr, padT = 22 * dpr, padB = 22 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;

                const [xlo, xhi] = panel.xlim;
                const counts = panel.counts;
                const edges = panel.edges;
                const curveY = panel.curve_y;
                const yMax = Math.max(Math.max(...counts), Math.max(...curveY)) * 1.12 || 1;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - (y / yMax) * plotH; }

                // grade estilo "whitegrid": linhas horizontais cinza claras
                ctx.strokeStyle = "#e5e7eb";
                ctx.lineWidth = 1 * dpr;
                const yTicks = 3;
                ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.fillStyle = "#555";
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                for (let t = 0; t <= yTicks; t++) {
                    const yVal = (yMax / yTicks) * t;
                    const py = yToPx(yVal);
                    ctx.beginPath();
                    ctx.moveTo(padL, py);
                    ctx.lineTo(padL + plotW, py);
                    ctx.stroke();
                    ctx.fillText(yVal.toFixed(yMax < 1 ? 2 : 1), padL - 4 * dpr, py);
                }

                // barras do histograma
                ctx.fillStyle = "#3498db";
                ctx.strokeStyle = "#ffffff";
                ctx.lineWidth = 1 * dpr;
                for (let i = 0; i < counts.length; i++) {
                    const x0 = xToPx(edges[i]);
                    const x1 = xToPx(edges[i + 1]);
                    const yTop = yToPx(counts[i]);
                    const yBase = yToPx(0);
                    ctx.globalAlpha = 0.75;
                    ctx.fillRect(x0, yTop, Math.max(x1 - x0, 1), yBase - yTop);
                    ctx.strokeRect(x0, yTop, Math.max(x1 - x0, 1), yBase - yTop);
                }
                ctx.globalAlpha = 1;

                // curva normal teorica
                ctx.strokeStyle = "#e74c3c";
                ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                const curveX = panel.curve_x;
                for (let i = 0; i < curveX.length; i++) {
                    const px = xToPx(curveX[i]);
                    const py = yToPx(curveY[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();

                // eixo x (ticks simples: lo, meio, hi)
                ctx.fillStyle = "#333";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                const xMid = (xlo + xhi) / 2;
                [xlo, xMid, xhi].forEach(xv => {
                    const px = xToPx(xv);
                    ctx.fillText(Math.round(xv), px, padT + plotH + 4 * dpr);
                });

                // borda do painel
                ctx.strokeStyle = "#d1d5db";
                ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                // titulo "n = X"
                ctx.fillStyle = "#111";
                ctx.font = "bold " + (12 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.fillText("n = " + panel.n, W / 2, padT - 6 * dpr);

                ctx.restore();
            }

            function drawAll() {
                const payload = JSON.parse(model.get("payload_json") || "{}");
                if (!payload.panels) return;
                h1.textContent = payload.title || "";
                h2.textContent = payload.subtitle || "";
                payload.panels.forEach((panel, i) => {
                    if (canvases[i]) drawPanel(canvases[i], panel);
                });
                // Sinaliza pro lado Python/medição que o redesenho terminou
                // (equivalente ao MutationObserver no src da <img> da
                // versão matplotlib antiga) -- usa um atributo no próprio
                // root, que muda a cada replot (inclusive os intermediários
                // durante um arrasto em live-drag).
                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", drawAll);
            drawAll();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (TLCGridWidget,)


@app.cell
def _(TLCGridWidget, mo):
    widget = mo.ui.anywidget(TLCGridWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, norm, w_dist, w_N, widget, json):
    distribuicao = w_dist.value
    num_repeticoes = w_N.value
    tamanhos_n = [1, 2, 3, 4, 5, 6, 10, 15, 20]

    if distribuicao == "Exponencial":
        media_teorica = 3
        variancia_teorica = 3 ** 2
        limite_x = (-1, 10)
    elif distribuicao == "Binomial":
        n_bi, p_bi = 10, 0.4
        media_teorica = n_bi * p_bi
        variancia_teorica = n_bi * p_bi * (1 - p_bi)
        limite_x = (-0.5, 9.5)
    else:
        lambda_poi = 4
        media_teorica = lambda_poi
        variancia_teorica = lambda_poi
        limite_x = (-0.5, 9.5)

    panels = []
    for i, n in enumerate(tamanhos_n):
        np.random.seed(42 + n)
        if distribuicao == "Exponencial":
            matriz = np.random.exponential(scale=media_teorica, size=(num_repeticoes, n))
        elif distribuicao == "Binomial":
            matriz = np.random.binomial(n=n_bi, p=p_bi, size=(num_repeticoes, n))
        else:
            matriz = np.random.poisson(lam=lambda_poi, size=(num_repeticoes, n))

        medias = np.mean(matriz, axis=1)
        counts, edges = np.histogram(medias, bins=15, density=True)

        sd_teorico = np.sqrt(variancia_teorica / n)
        x_eixo = np.linspace(limite_x[0], limite_x[1], 80)
        y_normal = norm.pdf(x_eixo, loc=media_teorica, scale=sd_teorico)

        panels.append({
            "n": int(n),
            "counts": counts.tolist(),
            "edges": edges.tolist(),
            "curve_x": x_eixo.tolist(),
            "curve_y": y_normal.tolist(),
            "xlim": list(limite_x),
        })

    payload = {
        "panels": panels,
        "title": f"Teorema do Limite Central (Distribuição {distribuicao})",
        "subtitle": "Conforme 'n' aumenta, a distribuição das médias se aproxima da Normal (linha vermelha)",
        "seq": f"{distribuicao}-{num_repeticoes}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
