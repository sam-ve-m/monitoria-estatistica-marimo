# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "anywidget",
#     "traitlets",
# ]
# ///

# Python só calcula os pontos das duas curvas (5PL e 4PL) e as retas de
# referência (EC50, assíntotas); o widget `anywidget` desenha tudo no
# <canvas>, com suporte a eixo X em escala log (base e) ou linear
# (controlado por `escala_ln`) feito na própria função de mapeamento
# x->pixel em JS.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import anywidget
    import traitlets
    import json

    return mo, np, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("# Modelo Logístico de 5 Parâmetros (5PL)")
    return


@app.cell
def _(mo):
    slider_b = mo.ui.slider(start=-10, stop=10, step=0.1, value=2, label="b (inclinação):", debounce=False)
    slider_c = mo.ui.slider(start=-2, stop=5, step=0.1, value=0, label="c (assíntota inf.):", debounce=False)
    slider_d = mo.ui.slider(start=1, stop=10, step=0.1, value=5, label="d (assíntota sup.):", debounce=False)
    slider_e = mo.ui.slider(start=0.1, stop=100, step=0.1, value=10, label="e (EC50):", debounce=False)
    slider_f = mo.ui.slider(start=0.1, stop=5, step=0.05, value=1, label="f (assimetria):", debounce=False)
    check_ln = mo.ui.checkbox(value=True, label="Habilitar escala ln")
    mo.vstack([slider_b, slider_c, slider_d, slider_e, slider_f, check_ln])
    return slider_b, slider_c, slider_d, slider_e, slider_f, check_ln


@app.cell
def _(anywidget, traitlets):
    class FivePLWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 760, cssH = 440;

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

            function draw() {
                const payload = JSON.parse(model.get("payload_json") || "{}");
                if (!payload.x) return;

                const ctx = canvas.getContext("2d");
                const W = canvas.width, H = canvas.height;
                ctx.clearRect(0, 0, W, H);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, W, H);

                const padL = 65 * dpr, padR = 20 * dpr, padT = 55 * dpr, padB = 55 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;

                const xArr = payload.x;
                const xlo = xArr[0], xhi = xArr[xArr.length - 1];
                const ylo = payload.ylo, yhi = payload.yhi;
                const useLog = payload.escala_ln;

                function xToPx(x) {
                    if (useLog) {
                        const lx = Math.log(x), llo = Math.log(xlo), lhi = Math.log(xhi);
                        return padL + ((lx - llo) / (lhi - llo)) * plotW;
                    }
                    return padL + ((x - xlo) / (xhi - xlo)) * plotW;
                }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                // grade leve
                ctx.strokeStyle = "#e5e7eb";
                ctx.lineWidth = 1 * dpr;
                ctx.fillStyle = "#555";
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                const yTicks = 5;
                for (let t = 0; t <= yTicks; t++) {
                    const yv = ylo + (yhi - ylo) * (t / yTicks);
                    const py = yToPx(yv);
                    ctx.beginPath();
                    ctx.moveTo(padL, py);
                    ctx.lineTo(padL + plotW, py);
                    ctx.stroke();
                    ctx.fillText(yv.toFixed(2), padL - 6 * dpr, py);
                }

                // assintotas (c, d) -- verde tracejado
                ctx.save();
                ctx.strokeStyle = "green";
                ctx.lineWidth = 1.5 * dpr;
                ctx.setLineDash([5 * dpr, 4 * dpr]);
                [payload.c, payload.d].forEach(yv => {
                    const py = yToPx(yv);
                    ctx.beginPath();
                    ctx.moveTo(padL, py);
                    ctx.lineTo(padL + plotW, py);
                    ctx.stroke();
                });
                ctx.restore();

                // EC50 -- vermelho pontilhado vertical
                ctx.save();
                ctx.strokeStyle = "red";
                ctx.lineWidth = 2 * dpr;
                ctx.setLineDash([2 * dpr, 3 * dpr]);
                const pxE = xToPx(payload.e);
                ctx.beginPath();
                ctx.moveTo(pxE, padT);
                ctx.lineTo(pxE, padT + plotH);
                ctx.stroke();
                ctx.restore();

                // curva 4PL (cinza tracejado)
                ctx.save();
                ctx.strokeStyle = "gray";
                ctx.lineWidth = 2 * dpr;
                ctx.setLineDash([6 * dpr, 4 * dpr]);
                ctx.beginPath();
                for (let i = 0; i < xArr.length; i++) {
                    const px = xToPx(xArr[i]), py = yToPx(payload.y4[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                // curva 5PL (azul royal, solida)
                ctx.save();
                ctx.strokeStyle = "royalblue";
                ctx.lineWidth = 3 * dpr;
                ctx.beginPath();
                for (let i = 0; i < xArr.length; i++) {
                    const px = xToPx(xArr[i]), py = yToPx(payload.y5[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                // moldura
                ctx.strokeStyle = "#333";
                ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                // ticks eixo x (valores "bonitos" dentro do range, formatados decimal)
                ctx.fillStyle = "#333";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                (payload.xticks || []).forEach(xv => {
                    if (xv < xlo || xv > xhi) return;
                    const px = xToPx(xv);
                    ctx.beginPath();
                    ctx.moveTo(px, padT + plotH);
                    ctx.lineTo(px, padT + plotH + 4 * dpr);
                    ctx.stroke();
                    const label = xv >= 1 ? xv.toFixed(0) : xv.toFixed(2);
                    ctx.fillText(label, px, padT + plotH + 6 * dpr);
                });

                ctx.font = (12 * dpr) + "px system-ui, sans-serif";
                ctx.fillText(payload.xlabel, padL + plotW / 2, padT + plotH + 32 * dpr);

                ctx.save();
                ctx.translate(padL - 48 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Resposta", 0, 0);
                ctx.restore();

                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.fillText("Modelo Logístico de 5 Parâmetros (Ajustado para ln)", padL + plotW / 2, padT - 22 * dpr);

                // legenda
                ctx.save();
                const legW = 150 * dpr, legH = 76 * dpr;
                const legX = padL + plotW - legW - 8 * dpr, legY = padT + 8 * dpr;
                ctx.fillStyle = "rgba(255,255,255,0.92)";
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1 * dpr;
                ctx.fillRect(legX, legY, legW, legH);
                ctx.strokeRect(legX, legY, legW, legH);
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";
                let ly = legY + 14 * dpr;
                ctx.strokeStyle = "royalblue"; ctx.setLineDash([]); ctx.lineWidth = 2.5 * dpr;
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.fillStyle = "#111"; ctx.fillText("5PL", legX + 34 * dpr, ly);
                ly += 18 * dpr;
                ctx.strokeStyle = "gray"; ctx.setLineDash([5 * dpr, 3 * dpr]); ctx.lineWidth = 2 * dpr;
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.fillStyle = "#111"; ctx.fillText("4PL (f=1)", legX + 34 * dpr, ly);
                ly += 18 * dpr;
                ctx.strokeStyle = "red"; ctx.setLineDash([2 * dpr, 2 * dpr]); ctx.lineWidth = 2 * dpr;
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.fillStyle = "#111"; ctx.fillText("EC50", legX + 34 * dpr, ly);
                ly += 18 * dpr;
                ctx.strokeStyle = "green"; ctx.setLineDash([5 * dpr, 3 * dpr]); ctx.lineWidth = 2 * dpr;
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.fillStyle = "#111"; ctx.fillText("Assíntotas", legX + 34 * dpr, ly);
                ctx.setLineDash([]);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (FivePLWidget,)


@app.cell
def _(FivePLWidget, mo):
    widget = mo.ui.anywidget(FivePLWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, slider_b, slider_c, slider_d, slider_e, slider_f, check_ln, widget, json):
    b, c, d, e, f = slider_b.value, slider_c.value, slider_d.value, slider_e.value, slider_f.value
    escala_ln = check_ln.value

    def fivePL(x, b, c, d, e, f):
        return c + (d - c) / ((1 + np.exp(b * (np.log(x) - np.log(e)))) ** f)

    ln_x = np.linspace(-5, 5, 800)
    x = np.exp(ln_x)
    y5 = fivePL(x, b, c, d, e, f)
    y4 = fivePL(x, b, c, d, e, 1)

    todos_y = np.concatenate([y5, y4, [c, d]])
    margem = (todos_y.max() - todos_y.min()) * 0.12 or 1.0
    ylo = float(todos_y.min() - margem)
    yhi = float(todos_y.max() + margem)

    xticks = [0.01, 0.1, 1, 10, 100, float(x.max())]
    xlabel = "Dose (Escala ln, valores em decimal)" if escala_ln else "Dose (Escala Linear)"

    payload = {
        "x": x.tolist(),
        "y5": y5.tolist(),
        "y4": y4.tolist(),
        "c": float(c), "d": float(d), "e": float(e),
        "ylo": ylo, "yhi": yhi,
        "escala_ln": bool(escala_ln),
        "xticks": xticks,
        "xlabel": xlabel,
        "seq": f"{b}-{c}-{d}-{e}-{f}-{escala_ln}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return b, c, d, e, f


@app.cell
def _(mo, np, b, c, d, e, f):
    if abs(f - 1) < 0.001:
        interpretacao = "O modelo coincide com um 4PL (curva simétrica)."
    elif f > 1:
        interpretacao = "A curva apresenta assimetria para a direita."
    else:
        interpretacao = "A curva apresenta assimetria para a esquerda."

    mo.md(f"""
    **Parâmetros do modelo**

    - Inclinação (b): {b:.3f}
    - Assíntota inferior (c): {c:.3f}
    - Assíntota superior (d): {d:.3f}
    - EC50 (e): {e:.3f}  (ln(e) = {np.log(e):.3f})
    - Assimetria (f): {f:.3f}

    {interpretacao}
    """)
    return


if __name__ == "__main__":
    app.run()
