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

# Três casos (Binomial discreta, Normal contínua simétrica, Gama contínua
# assimétrica) com PDF/PMF + CDF lado a lado. Todos os 7 controles ficam
# sempre visíveis, independente da distribuição escolhida (diferente do
# DistribuicoesDiscretas, que esconde controles por grupo).
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy import stats
    import anywidget
    import traitlets
    import json

    return mo, np, stats, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("# Painel Variáveis Aleatórias")
    return


@app.cell
def _(mo):
    tipo_dist = mo.ui.radio(
        options=["Discreta (Binomial)", "Contínua Simétrica (Normal)", "Contínua Assimétrica (Gama)"],
        value="Discreta (Binomial)", label="Distribuição:",
    )
    n_param = mo.ui.slider(start=1, stop=30, step=1, value=10, label="Eixo X máx / n:", debounce=False)
    prob_sucesso = mo.ui.slider(start=0.0, stop=1.0, step=0.05, value=0.5, label="Prob. (Binomial):", debounce=False)
    va_a_input = mo.ui.slider(start=-10.0, stop=10.0, step=0.1, value=0.0, label="Limite (a):", debounce=False)
    va_b_input = mo.ui.slider(start=-10.0, stop=10.0, step=0.1, value=2.0, label="Limite (b):", debounce=False)
    alfa = mo.ui.slider(start=0.1, stop=10.0, step=0.1, value=2.0, label="Alfa (Gama):", debounce=False)
    beta = mo.ui.slider(start=0.1, stop=10.0, step=0.1, value=2.0, label="Beta (Gama):", debounce=False)
    mo.vstack([tipo_dist, n_param, prob_sucesso, va_a_input, va_b_input, alfa, beta])
    return tipo_dist, n_param, prob_sucesso, va_a_input, va_b_input, alfa, beta


@app.cell
def _(anywidget, traitlets):
    class VAWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 1180, cssH = 460;

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

            function frame(ctx, ox, pw, H, xlo, xhi, ylo, yhi, title, xlabel, ylabel, xlabelColor) {
                const padL = 58 * dpr, padR = 15 * dpr, padT = 45 * dpr, padB = 56 * dpr;
                const plotW = pw - padL - padR;
                const plotH = H - padT - padB;
                function xToPx(x) { return ox + padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                ctx.strokeStyle = "#e5e7eb"; ctx.lineWidth = 1 * dpr;
                ctx.fillStyle = "#555"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                for (let t = 0; t <= 5; t++) {
                    const yv = ylo + (yhi - ylo) * (t / 5);
                    const py = yToPx(yv);
                    ctx.beginPath(); ctx.moveTo(ox + padL, py); ctx.lineTo(ox + padL + plotW, py); ctx.stroke();
                    ctx.fillText(yv.toFixed(2), ox + padL - 6 * dpr, py);
                }

                return { xToPx, yToPx, padL, padT, plotW, plotH,
                    finish: () => {
                        ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
                        ctx.strokeRect(ox + padL, padT, plotW, plotH);
                        ctx.fillStyle = "#333"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                        ctx.textAlign = "center"; ctx.textBaseline = "top";
                        for (let t = 0; t <= 6; t++) {
                            const xv = xlo + (xhi - xlo) * (t / 6);
                            const px = xToPx(xv);
                            ctx.beginPath(); ctx.moveTo(px, padT + plotH); ctx.lineTo(px, padT + plotH + 4 * dpr); ctx.stroke();
                            ctx.fillText(xv.toFixed(1), px, padT + plotH + 6 * dpr);
                        }
                        ctx.font = "bold " + (11 * dpr) + "px system-ui, sans-serif";
                        ctx.fillStyle = xlabelColor || "#333";
                        ctx.fillText(xlabel, ox + padL + plotW / 2, padT + plotH + 30 * dpr);
                        ctx.save();
                        ctx.translate(ox + padL - 44 * dpr, padT + plotH / 2);
                        ctx.rotate(-Math.PI / 2);
                        ctx.textAlign = "center"; ctx.fillStyle = "#333";
                        ctx.font = (11 * dpr) + "px system-ui, sans-serif";
                        ctx.fillText(ylabel, 0, 0);
                        ctx.restore();
                        ctx.font = "bold " + (13 * dpr) + "px system-ui, sans-serif";
                        ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                        ctx.fillStyle = "#111";
                        ctx.fillText(title, ox + padL + plotW / 2, padT - 16 * dpr);
                    }
                };
            }

            function drawBinomial(ctx, payload) {
                const half = canvas.width / 2, H = canvas.height;
                const x = payload.x, pmf = payload.y1, cdf = payload.y2;
                const xhi = x[x.length - 1] + 1;

                const f1 = frame(ctx, 0, half, H, 0, xhi, 0, Math.max(...pmf) * 1.15 || 1,
                    "Função de Probabilidade P(X = x)", "x", "P(X = x)");
                ctx.strokeStyle = "darkgray"; ctx.lineWidth = 3 * dpr;
                x.forEach((xv, i) => {
                    const px = f1.xToPx(xv);
                    ctx.beginPath(); ctx.moveTo(px, f1.yToPx(0)); ctx.lineTo(px, f1.yToPx(pmf[i])); ctx.stroke();
                });
                ctx.fillStyle = "royalblue";
                x.forEach((xv, i) => {
                    ctx.beginPath(); ctx.arc(f1.xToPx(xv), f1.yToPx(pmf[i]), 4.5 * dpr, 0, 2 * Math.PI); ctx.fill();
                });
                f1.finish();

                const f2 = frame(ctx, half, half, H, 0, xhi, -0.05, 1.05,
                    "Função de Distribuição F(X)", "x", "F(X)");
                ctx.strokeStyle = "royalblue"; ctx.lineWidth = 2 * dpr;
                for (let i = 0; i < x.length - 1; i++) {
                    const py = f2.yToPx(cdf[i]);
                    ctx.beginPath(); ctx.moveTo(f2.xToPx(x[i]), py); ctx.lineTo(f2.xToPx(x[i + 1]), py); ctx.stroke();
                }
                const lastPy = f2.yToPx(cdf[cdf.length - 1]);
                ctx.beginPath(); ctx.moveTo(f2.xToPx(x[x.length - 1]), lastPy); ctx.lineTo(f2.xToPx(x[x.length - 1] + 0.8), lastPy); ctx.stroke();
                ctx.fillStyle = "darkgray";
                x.forEach((xv, i) => {
                    const px = f2.xToPx(xv), py = f2.yToPx(cdf[i]);
                    ctx.save(); ctx.translate(px, py); ctx.rotate(Math.PI / 4);
                    ctx.fillRect(-3 * dpr, -3 * dpr, 6 * dpr, 6 * dpr); ctx.restore();
                });
                f2.finish();
            }

            function drawContinuous(ctx, payload) {
                const half = canvas.width / 2, H = canvas.height;
                const x = payload.x, pdf = payload.y1, cdf = payload.y2;
                const xlo = x[0], xhi = x[x.length - 1];
                const a = payload.va_a, b = payload.va_b;
                const xlabelColor = payload.case === "gama" ? "red" : "black";

                const f1 = frame(ctx, 0, half, H, xlo, xhi, 0, Math.max(...pdf) * 1.15 || 1,
                    "Função de Densidade f(x)",
                    `P(${a.toFixed(2)} < X < ${b.toFixed(2)}) = ${payload.prob_interv.toFixed(4)}`,
                    "f(x)", xlabelColor);
                ctx.strokeStyle = "black"; ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                x.forEach((xv, i) => { const px = f1.xToPx(xv), py = f1.yToPx(pdf[i]); if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py); });
                ctx.stroke();
                ctx.save();
                ctx.fillStyle = "lightcoral"; ctx.globalAlpha = 0.7;
                ctx.beginPath();
                payload.x_fill.forEach((xv, i) => {
                    const px = f1.xToPx(xv), py = f1.yToPx(payload.pdf_fill[i]);
                    if (i === 0) { ctx.moveTo(px, f1.yToPx(0)); ctx.lineTo(px, py); } else ctx.lineTo(px, py);
                });
                ctx.lineTo(f1.xToPx(payload.x_fill[payload.x_fill.length - 1]), f1.yToPx(0));
                ctx.closePath(); ctx.fill();
                ctx.restore();
                ctx.strokeStyle = "black"; ctx.lineWidth = 3 * dpr;
                ctx.beginPath(); ctx.moveTo(f1.xToPx(a), f1.yToPx(0)); ctx.lineTo(f1.xToPx(b), f1.yToPx(0)); ctx.stroke();
                f1.finish();

                const f2 = frame(ctx, half, half, H, xlo, xhi, -0.05, 1.05,
                    "Função de Distribuição F(x)", "x", "F(x)");
                ctx.strokeStyle = "black"; ctx.lineWidth = 2 * dpr;
                ctx.beginPath();
                x.forEach((xv, i) => { const px = f2.xToPx(xv), py = f2.yToPx(cdf[i]); if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py); });
                ctx.stroke();

                const yA = payload.y_a, yB = payload.y_b;
                ctx.save();
                ctx.strokeStyle = "gray"; ctx.setLineDash([5 * dpr, 4 * dpr]); ctx.lineWidth = 1.5 * dpr;
                ctx.beginPath(); ctx.moveTo(f2.xToPx(a), f2.yToPx(0)); ctx.lineTo(f2.xToPx(a), f2.yToPx(yA)); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(f2.xToPx(a), f2.yToPx(yA)); ctx.lineTo(f2.xToPx(0), f2.yToPx(yA)); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(f2.xToPx(b), f2.yToPx(0)); ctx.lineTo(f2.xToPx(b), f2.yToPx(yB)); ctx.stroke();
                ctx.beginPath(); ctx.moveTo(f2.xToPx(b), f2.yToPx(yB)); ctx.lineTo(f2.xToPx(0), f2.yToPx(yB)); ctx.stroke();
                ctx.restore();

                ctx.strokeStyle = "black"; ctx.lineWidth = 3 * dpr; ctx.setLineDash([]);
                ctx.beginPath(); ctx.moveTo(f2.xToPx(a), f2.yToPx(0)); ctx.lineTo(f2.xToPx(b), f2.yToPx(0)); ctx.stroke();

                ctx.save();
                ctx.strokeStyle = "lightcoral"; ctx.lineWidth = 4 * dpr;
                ctx.beginPath(); ctx.moveTo(f2.xToPx(0), f2.yToPx(yA)); ctx.lineTo(f2.xToPx(0), f2.yToPx(yB)); ctx.stroke();
                ctx.fillStyle = "lightcoral";
                [yA, yB].forEach(yv => { ctx.beginPath(); ctx.arc(f2.xToPx(0), f2.yToPx(yv), 4 * dpr, 0, 2 * Math.PI); ctx.fill(); });
                ctx.restore();

                ctx.save();
                ctx.strokeStyle = "blue"; ctx.lineWidth = 4 * dpr;
                ctx.beginPath();
                payload.x_seg.forEach((xv, i) => {
                    const px = f2.xToPx(xv), py = f2.yToPx(payload.cdf_seg[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                });
                ctx.stroke();
                ctx.restore();

                f2.finish();
            }

            function draw() {
                const payload = JSON.parse(model.get("payload_json") || "{}");
                if (!payload.x) return;
                const ctx = canvas.getContext("2d");
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, canvas.width, canvas.height);

                if (payload.case === "binomial") drawBinomial(ctx, payload);
                else drawContinuous(ctx, payload);

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (VAWidget,)


@app.cell
def _(VAWidget, mo):
    widget = mo.ui.anywidget(VAWidget())
    widget
    return (widget,)


@app.cell
def _(
    mo, np, stats, json, widget,
    tipo_dist, n_param, prob_sucesso, va_a_input, va_b_input, alfa, beta,
):
    va_a = min(va_a_input.value, va_b_input.value)
    va_b = max(va_a_input.value, va_b_input.value)

    if tipo_dist.value == "Discreta (Binomial)":
        x = np.arange(0, n_param.value + 1)
        pmf = stats.binom.pmf(x, n_param.value, prob_sucesso.value)
        cdf = stats.binom.cdf(x, n_param.value, prob_sucesso.value)
        payload = {
            "case": "binomial",
            "x": x.tolist(), "y1": pmf.tolist(), "y2": cdf.tolist(),
            "seq": f"bin-{n_param.value}-{prob_sucesso.value}",
        }
    elif tipo_dist.value == "Contínua Simétrica (Normal)":
        amp_normal = min(n_param.value, 10)
        x = np.linspace(-amp_normal, amp_normal, 300)
        pdf = stats.norm.pdf(x)
        cdf = stats.norm.cdf(x)
        prob_interv = float(stats.norm.cdf(va_b) - stats.norm.cdf(va_a))
        x_fill = np.linspace(va_a, va_b, 100)
        x_seg = np.linspace(va_a, va_b, 50)
        y_a, y_b = float(stats.norm.cdf(va_a)), float(stats.norm.cdf(va_b))
        payload = {
            "case": "normal",
            "x": x.tolist(), "y1": pdf.tolist(), "y2": cdf.tolist(),
            "va_a": float(va_a), "va_b": float(va_b), "prob_interv": prob_interv,
            "x_fill": x_fill.tolist(), "pdf_fill": stats.norm.pdf(x_fill).tolist(),
            "x_seg": x_seg.tolist(), "cdf_seg": stats.norm.cdf(x_seg).tolist(),
            "y_a": y_a, "y_b": y_b,
            "seq": f"norm-{n_param.value}-{va_a_input.value}-{va_b_input.value}",
        }
    else:
        x = np.linspace(0.01, n_param.value, 300)
        va_a_gama = max(0.0, va_a)
        va_b_gama = max(va_a_gama, va_b)
        pdf = stats.gamma.pdf(x, a=alfa.value, scale=beta.value)
        cdf = stats.gamma.cdf(x, a=alfa.value, scale=beta.value)
        prob_interv = float(
            stats.gamma.cdf(va_b_gama, a=alfa.value, scale=beta.value)
            - stats.gamma.cdf(va_a_gama, a=alfa.value, scale=beta.value)
        )
        x_fill = np.linspace(va_a_gama, va_b_gama, 100)
        x_seg = np.linspace(va_a_gama, va_b_gama, 50)
        y_a = float(stats.gamma.cdf(va_a_gama, a=alfa.value, scale=beta.value))
        y_b = float(stats.gamma.cdf(va_b_gama, a=alfa.value, scale=beta.value))
        payload = {
            "case": "gama",
            "x": x.tolist(), "y1": pdf.tolist(), "y2": cdf.tolist(),
            "va_a": float(va_a_gama), "va_b": float(va_b_gama), "prob_interv": prob_interv,
            "x_fill": x_fill.tolist(), "pdf_fill": stats.gamma.pdf(x_fill, a=alfa.value, scale=beta.value).tolist(),
            "x_seg": x_seg.tolist(), "cdf_seg": stats.gamma.cdf(x_seg, a=alfa.value, scale=beta.value).tolist(),
            "y_a": y_a, "y_b": y_b,
            "seq": f"gama-{n_param.value}-{va_a_input.value}-{va_b_input.value}-{alfa.value}-{beta.value}",
        }

    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
