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

# Painel comparativo com 4 distribuições discretas (Bernoulli, Binomial,
# Poisson, Hipergeométrica), cada uma com seu próprio conjunto de
# controles e dois gráficos (PMF em barras + CDF em escada) desenhados no
# mesmo <canvas> lado a lado.
#
# Diferença de estrutura em relação aos notebooks anteriores: aqui existe
# um `mo.ui.radio` escolhendo QUAL distribuição está ativa, e cada
# distribuição tem seu próprio grupo de sliders -- todos os sliders de
# todas as distribuições continuam sempre montados (para preservar valor
# ao trocar de aba), mas só o grupo da distribuição selecionada é exibido
# via `mo.vstack` condicional, igual ao `ui_parameters.children = [...]`
# do original.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import bernoulli, binom, poisson, hypergeom
    import anywidget
    import traitlets
    import json

    return mo, np, bernoulli, binom, poisson, hypergeom, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("# Painel de Distribuições Discretas Comparativo")
    return


@app.cell
def _(mo):
    radio_dist = mo.ui.radio(
        options=["Bernoulli", "Binomial", "Poisson", "Hipergeométrica"],
        value="Bernoulli", label="Distribuição:",
    )
    radio_dist
    return (radio_dist,)


@app.cell
def _(mo):
    prob_bernoulli = mo.ui.slider(start=0.0, stop=1.0, step=0.01, value=0.5, label="θ (Bernoulli):", debounce=False)
    n_binomial = mo.ui.slider(start=1, stop=30, step=1, value=10, label="n (Ensaios):", debounce=False)
    prob_binomial = mo.ui.slider(start=0.0, stop=1.0, step=0.01, value=0.5, label="θ (Binomial):", debounce=False)
    n_poisson = mo.ui.slider(start=1, stop=30, step=1, value=15, label="X máx na tela:", debounce=False)
    lambda_poisson = mo.ui.slider(start=0.1, stop=30.0, step=0.1, value=5.0, label="λ (Taxa Média):", debounce=False)
    N_hyper = mo.ui.slider(start=1, stop=100, step=1, value=20, label="N (População):", debounce=False)
    k_hyper = mo.ui.slider(start=0, stop=100, step=1, value=10, label="k (Sucessos Pop):", debounce=False)
    n_hyper = mo.ui.slider(start=1, stop=100, step=1, value=5, label="n (Amostra):", debounce=False)
    return (
        prob_bernoulli, n_binomial, prob_binomial, n_poisson,
        lambda_poisson, N_hyper, k_hyper, n_hyper,
    )


@app.cell
def _(mo, radio_dist, prob_bernoulli, n_binomial, prob_binomial, n_poisson, lambda_poisson, N_hyper, k_hyper, n_hyper):
    _grupos = {
        "Bernoulli": [prob_bernoulli],
        "Binomial": [n_binomial, prob_binomial],
        "Poisson": [n_poisson, lambda_poisson],
        "Hipergeométrica": [N_hyper, k_hyper, n_hyper],
    }
    mo.vstack(_grupos[radio_dist.value])
    return


@app.cell
def _(anywidget, traitlets):
    class DiscretasWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 1180, cssH = 440;

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

            function drawPanel(ctx, ox, pw, H, xVals, yVals, kind, title, xlabel, ylabel, extraLabels) {
                const padL = 55 * dpr, padR = 15 * dpr, padT = 45 * dpr, padB = 50 * dpr;
                const plotW = pw - padL - padR;
                const plotH = H - padT - padB;
                const xlo = xVals[0], xhi = kind === "cdf" ? xVals[xVals.length - 1] + 1 : xVals[xVals.length - 1];
                const ylo = kind === "cdf" ? -0.05 : 0;
                const yhi = kind === "cdf" ? 1.1 : (Math.max(...yVals) * 1.15 || 1);

                function xToPx(x) { return ox + padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                // grade
                ctx.strokeStyle = "#e5e7eb"; ctx.lineWidth = 1 * dpr;
                ctx.fillStyle = "#555"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                for (let t = 0; t <= 5; t++) {
                    const yv = ylo + (yhi - ylo) * (t / 5);
                    const py = yToPx(yv);
                    ctx.beginPath(); ctx.moveTo(ox + padL, py); ctx.lineTo(ox + padL + plotW, py); ctx.stroke();
                    ctx.fillText(yv.toFixed(3), ox + padL - 6 * dpr, py);
                }

                if (kind === "pmf") {
                    ctx.strokeStyle = "steelblue"; ctx.lineWidth = 3 * dpr; ctx.globalAlpha = 0.8;
                    for (let i = 0; i < xVals.length; i++) {
                        const px = xToPx(xVals[i]);
                        ctx.beginPath(); ctx.moveTo(px, yToPx(0)); ctx.lineTo(px, yToPx(yVals[i])); ctx.stroke();
                    }
                    ctx.globalAlpha = 1;
                    ctx.fillStyle = "darkblue";
                    for (let i = 0; i < xVals.length; i++) {
                        const px = xToPx(xVals[i]), py = yToPx(yVals[i]);
                        ctx.beginPath(); ctx.arc(px, py, 4 * dpr, 0, 2 * Math.PI); ctx.fill();
                    }
                    ctx.font = (8 * dpr) + "px system-ui, sans-serif";
                    ctx.textAlign = "center"; ctx.textBaseline = "bottom";
                    const ymax = Math.max(...yVals) || 1;
                    for (let i = 0; i < xVals.length; i++) {
                        if (yVals[i] > 0.0001) {
                            ctx.fillText(yVals[i].toFixed(3), xToPx(xVals[i]), yToPx(yVals[i] + ymax * 0.02));
                        }
                    }
                } else {
                    ctx.strokeStyle = "darkorange"; ctx.lineWidth = 3 * dpr;
                    for (let i = 0; i < xVals.length; i++) {
                        const py = yToPx(yVals[i]);
                        ctx.beginPath(); ctx.moveTo(xToPx(xVals[i]), py); ctx.lineTo(xToPx(xVals[i] + 1), py); ctx.stroke();
                    }
                    ctx.fillStyle = "darkorange";
                    for (let i = 0; i < xVals.length; i++) {
                        const px = xToPx(xVals[i]), py = yToPx(yVals[i]);
                        ctx.beginPath(); ctx.arc(px, py, 3.5 * dpr, 0, 2 * Math.PI); ctx.fill();
                    }
                }

                // moldura
                ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(ox + padL, padT, plotW, plotH);

                // ticks x
                ctx.fillStyle = "#333"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "top";
                const xticks = kind === "cdf" ? [...xVals, xVals[xVals.length - 1] + 1] : xVals;
                xticks.forEach(xv => {
                    const px = xToPx(xv);
                    ctx.beginPath(); ctx.moveTo(px, padT + plotH); ctx.lineTo(px, padT + plotH + 4 * dpr); ctx.stroke();
                    ctx.fillText(xv.toFixed(0), px, padT + plotH + 6 * dpr);
                });

                ctx.font = (11 * dpr) + "px system-ui, sans-serif";
                ctx.fillText(xlabel, ox + padL + plotW / 2, padT + plotH + 26 * dpr);
                ctx.save();
                ctx.translate(ox + padL - 42 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText(ylabel, 0, 0);
                ctx.restore();

                ctx.font = "bold " + (12 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
                ctx.fillText(title, ox + padL + plotW / 2, padT - 16 * dpr);
            }

            function draw() {
                const payload = JSON.parse(model.get("payload_json") || "{}");
                if (!payload.x_vals) return;

                const ctx = canvas.getContext("2d");
                const W = canvas.width, H = canvas.height;
                ctx.clearRect(0, 0, W, H);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, W, H);

                if (payload.erro) {
                    ctx.fillStyle = "red";
                    ctx.font = "bold " + (16 * dpr) + "px system-ui, sans-serif";
                    ctx.textAlign = "center";
                    ctx.fillText(payload.erro, W / 2, H / 2);
                    root.setAttribute("data-render-seq", payload.seq);
                    return;
                }

                const half = W / 2;
                drawPanel(ctx, 0, half, H, payload.x_vals, payload.probs_pmf, "pmf", payload.titulo_pmf, "Número de Sucessos (x)", "P(X = x)");
                drawPanel(ctx, half, half, H, payload.x_vals, payload.probs_cdf, "cdf", "Distribuição Acumulada (CDF): " + payload.dist_type, "Número de Sucessos (x)", "F(x) = P(X <= x)");

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (DiscretasWidget,)


@app.cell
def _(DiscretasWidget, mo):
    widget = mo.ui.anywidget(DiscretasWidget())
    widget
    return (widget,)


@app.cell
def _(
    mo, np, bernoulli, binom, poisson, hypergeom, json, widget,
    radio_dist, prob_bernoulli, n_binomial, prob_binomial, n_poisson,
    lambda_poisson, N_hyper, k_hyper, n_hyper,
):
    dist_type = radio_dist.value
    erro = None

    if dist_type == "Bernoulli":
        x_vals = np.array([0, 1])
        probs_pmf = bernoulli.pmf(x_vals, p=prob_bernoulli.value)
        probs_cdf = bernoulli.cdf(x_vals, p=prob_bernoulli.value)
        titulo_pmf = f"Função de Massa (PMF): Bern({prob_bernoulli.value})"
    elif dist_type == "Binomial":
        x_vals = np.arange(0, n_binomial.value + 1)
        probs_pmf = binom.pmf(x_vals, n=n_binomial.value, p=prob_binomial.value)
        probs_cdf = binom.cdf(x_vals, n=n_binomial.value, p=prob_binomial.value)
        titulo_pmf = f"Função de Massa (PMF): Bin({n_binomial.value}, {prob_binomial.value})"
    elif dist_type == "Poisson":
        x_vals = np.arange(0, n_poisson.value + 1)
        probs_pmf = poisson.pmf(x_vals, mu=lambda_poisson.value)
        probs_cdf = poisson.cdf(x_vals, mu=lambda_poisson.value)
        titulo_pmf = f"Função de Massa (PMF): Poiss(λ={lambda_poisson.value})"
    else:
        if k_hyper.value > N_hyper.value or n_hyper.value > N_hyper.value:
            erro = "Erro: 'k' e 'n' não podem ser maiores do que a População total (N)."
            x_vals, probs_pmf, probs_cdf, titulo_pmf = np.array([0]), np.array([0.0]), np.array([0.0]), ""
        else:
            x_vals = np.arange(0, n_hyper.value + 1)
            probs_pmf = hypergeom.pmf(x_vals, M=N_hyper.value, n=k_hyper.value, N=n_hyper.value)
            probs_cdf = hypergeom.cdf(x_vals, M=N_hyper.value, n=k_hyper.value, N=n_hyper.value)
            titulo_pmf = f"Função de Massa (PMF): Hyper(N={N_hyper.value}, k={k_hyper.value}, n={n_hyper.value})"

    payload = {
        "x_vals": [float(v) for v in x_vals],
        "probs_pmf": [float(v) for v in probs_pmf],
        "probs_cdf": [float(v) for v in probs_cdf],
        "titulo_pmf": titulo_pmf,
        "dist_type": dist_type,
        "erro": erro,
        "seq": f"{dist_type}-{prob_bernoulli.value}-{n_binomial.value}-{prob_binomial.value}-{n_poisson.value}-{lambda_poisson.value}-{N_hyper.value}-{k_hyper.value}-{n_hyper.value}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
