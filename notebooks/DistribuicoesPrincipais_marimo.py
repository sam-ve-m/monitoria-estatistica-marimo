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

# Combina dois painéis num só notebook: painel Discretas (igual ao
# DistribuicoesDiscretas_marimo.py, mas com 2 distribuições a mais --
# Uniforme Discreta e Binomial Negativa, 6 no total) empilhado em cima do
# painel Contínuas (idêntico ao DistribuicoesContinuasPrincipais_marimo.py,
# 8 distribuições), cada um com seu próprio radio + canvas independentes
# e sem ligação entre si -- são duas seções sequenciais na mesma página.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import (
        bernoulli, binom, poisson, hypergeom, randint, nbinom,
        uniform, gamma, norm, t, chi2, f, weibull_min, cauchy,
    )
    import anywidget
    import traitlets
    import json

    return (
        mo, np, bernoulli, binom, poisson, hypergeom, randint, nbinom,
        uniform, gamma, norm, t, chi2, f, weibull_min, cauchy,
        anywidget, traitlets, json,
    )


@app.cell
def _(mo):
    mo.md("# Painel de Distribuições Discretas Comparativo")
    return


@app.cell
def _(mo):
    radio_disc = mo.ui.radio(
        options=["Bernoulli", "Binomial", "Poisson", "Hipergeométrica", "Uniforme Discreta", "Binomial Negativa"],
        value="Bernoulli", label="Distribuição:",
    )
    radio_disc
    return (radio_disc,)


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
    a_uniform = mo.ui.slider(start=0, stop=10, step=1, value=1, label="a (Mínimo):", debounce=False)
    b_uniform = mo.ui.slider(start=1, stop=20, step=1, value=6, label="b (Máximo):", debounce=False)
    r_nbinom = mo.ui.slider(start=1, stop=20, step=1, value=3, label="r (Nº Sucessos):", debounce=False)
    prob_nbinom = mo.ui.slider(start=0.01, stop=1.0, step=0.01, value=0.5, label="p (Probabilidade):", debounce=False)
    xmax_nbinom = mo.ui.slider(start=5, stop=50, step=1, value=15, label="X máx (Fracassos):", debounce=False)
    return (
        prob_bernoulli, n_binomial, prob_binomial, n_poisson, lambda_poisson,
        N_hyper, k_hyper, n_hyper, a_uniform, b_uniform, r_nbinom, prob_nbinom, xmax_nbinom,
    )


@app.cell
def _(
    mo, radio_disc, prob_bernoulli, n_binomial, prob_binomial, n_poisson,
    lambda_poisson, N_hyper, k_hyper, n_hyper, a_uniform, b_uniform,
    r_nbinom, prob_nbinom, xmax_nbinom,
):
    _grupos = {
        "Bernoulli": [prob_bernoulli],
        "Binomial": [n_binomial, prob_binomial],
        "Poisson": [n_poisson, lambda_poisson],
        "Hipergeométrica": [N_hyper, k_hyper, n_hyper],
        "Uniforme Discreta": [a_uniform, b_uniform],
        "Binomial Negativa": [r_nbinom, prob_nbinom, xmax_nbinom],
    }
    mo.vstack(_grupos[radio_disc.value])
    return


@app.cell
def _(anywidget, traitlets):
    _DISCRETE_PANEL_JS = r"""
        function drawPanel(ctx, ox, pw, H, xVals, yVals, kind, title, xlabel, ylabel, dpr) {
            const padL = 55 * dpr, padR = 15 * dpr, padT = 45 * dpr, padB = 50 * dpr;
            const plotW = pw - padL - padR;
            const plotH = H - padT - padB;
            const xlo = xVals[0], xhi = kind === "cdf" ? xVals[xVals.length - 1] + 1 : xVals[xVals.length - 1];
            const ylo = kind === "cdf" ? -0.05 : 0;
            const yhi = kind === "cdf" ? 1.1 : (Math.max(...yVals) * 1.15 || 1);

            function xToPx(x) { return ox + padL + ((x - xlo) / (xhi - xlo)) * plotW; }
            function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

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

            ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
            ctx.strokeRect(ox + padL, padT, plotW, plotH);

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
    """

    class DiscretasWidget(anywidget.AnyWidget):
        _esm = (
            r"""
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
            """
            + _DISCRETE_PANEL_JS
            + r"""
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
                drawPanel(ctx, 0, half, H, payload.x_vals, payload.probs_pmf, "pmf", payload.titulo_pmf, "Variável Aleatória (x)", "P(X = x)", dpr);
                drawPanel(ctx, half, half, H, payload.x_vals, payload.probs_cdf, "cdf", "Distribuição Acumulada (CDF): " + payload.dist_type, "Variável Aleatória (x)", "F(x) = P(X <= x)", dpr);

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        )
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (DiscretasWidget,)


@app.cell
def _(DiscretasWidget, mo):
    widget_disc = mo.ui.anywidget(DiscretasWidget())
    widget_disc
    return (widget_disc,)


@app.cell
def _(
    mo, np, bernoulli, binom, poisson, hypergeom, randint, nbinom, json, widget_disc,
    radio_disc, prob_bernoulli, n_binomial, prob_binomial, n_poisson,
    lambda_poisson, N_hyper, k_hyper, n_hyper, a_uniform, b_uniform,
    r_nbinom, prob_nbinom, xmax_nbinom,
):
    dist_disc = radio_disc.value
    erro_disc = None

    if dist_disc == "Bernoulli":
        x_d = np.array([0, 1])
        pmf_d = bernoulli.pmf(x_d, p=prob_bernoulli.value)
        cdf_d = bernoulli.cdf(x_d, p=prob_bernoulli.value)
        titulo_d = f"Função de Massa (PMF): Bern({prob_bernoulli.value})"
    elif dist_disc == "Binomial":
        x_d = np.arange(0, n_binomial.value + 1)
        pmf_d = binom.pmf(x_d, n=n_binomial.value, p=prob_binomial.value)
        cdf_d = binom.cdf(x_d, n=n_binomial.value, p=prob_binomial.value)
        titulo_d = f"Função de Massa (PMF): Bin({n_binomial.value}, {prob_binomial.value})"
    elif dist_disc == "Poisson":
        x_d = np.arange(0, n_poisson.value + 1)
        pmf_d = poisson.pmf(x_d, mu=lambda_poisson.value)
        cdf_d = poisson.cdf(x_d, mu=lambda_poisson.value)
        titulo_d = f"Função de Massa (PMF): Poiss(λ={lambda_poisson.value})"
    elif dist_disc == "Hipergeométrica":
        if k_hyper.value > N_hyper.value or n_hyper.value > N_hyper.value:
            erro_disc = "Erro: 'k' e 'n' não podem ser maiores do que a População total (N)."
            x_d, pmf_d, cdf_d, titulo_d = np.array([0]), np.array([0.0]), np.array([0.0]), ""
        else:
            x_d = np.arange(0, n_hyper.value + 1)
            pmf_d = hypergeom.pmf(x_d, M=N_hyper.value, n=k_hyper.value, N=n_hyper.value)
            cdf_d = hypergeom.cdf(x_d, M=N_hyper.value, n=k_hyper.value, N=n_hyper.value)
            titulo_d = f"Função de Massa (PMF): Hyper(N={N_hyper.value}, k={k_hyper.value}, n={n_hyper.value})"
    elif dist_disc == "Uniforme Discreta":
        if a_uniform.value > b_uniform.value:
            erro_disc = "Erro: O limite inferior (a) não pode ser maior que o superior (b)."
            x_d, pmf_d, cdf_d, titulo_d = np.array([0]), np.array([0.0]), np.array([0.0]), ""
        else:
            x_d = np.arange(a_uniform.value - 1, b_uniform.value + 2)
            pmf_d = randint.pmf(x_d, a_uniform.value, b_uniform.value + 1)
            cdf_d = randint.cdf(x_d, a_uniform.value, b_uniform.value + 1)
            titulo_d = f"Função de Massa (PMF): Uniforme({a_uniform.value}, {b_uniform.value})"
    else:
        x_d = np.arange(0, xmax_nbinom.value + 1)
        pmf_d = nbinom.pmf(x_d, n=r_nbinom.value, p=prob_nbinom.value)
        cdf_d = nbinom.cdf(x_d, n=r_nbinom.value, p=prob_nbinom.value)
        titulo_d = f"Função de Massa (PMF): NBin(r={r_nbinom.value}, p={prob_nbinom.value})"

    payload_disc = {
        "x_vals": [float(v) for v in x_d],
        "probs_pmf": [float(v) for v in pmf_d],
        "probs_cdf": [float(v) for v in cdf_d],
        "titulo_pmf": titulo_d,
        "dist_type": dist_disc,
        "erro": erro_disc,
        "seq": f"{dist_disc}-{prob_bernoulli.value}-{n_binomial.value}-{prob_binomial.value}-{n_poisson.value}-{lambda_poisson.value}-{N_hyper.value}-{k_hyper.value}-{n_hyper.value}-{a_uniform.value}-{b_uniform.value}-{r_nbinom.value}-{prob_nbinom.value}-{xmax_nbinom.value}",
    }
    widget_disc.payload_json = json.dumps(payload_disc)
    mo.show_code(position="below")
    return


@app.cell
def _(mo):
    mo.md("# Painel de Distribuições Contínuas Comparativo")
    return


@app.cell
def _(mo):
    radio_cont = mo.ui.radio(
        options=[
            "Uniforme Contínua", "Gama", "Normal Padrão", "t-Student",
            "Qui-Quadrado", "F-Snedecor", "Weibull (2 parâmetros)", "Cauchy",
        ],
        value="Uniforme Contínua", label="Distribuição:",
    )
    radio_cont
    return (radio_cont,)


@app.cell
def _(mo):
    unif_a = mo.ui.slider(start=-10.0, stop=10.0, step=0.5, value=2.0, label="a (Mínimo):", debounce=False)
    unif_b = mo.ui.slider(start=-10.0, stop=20.0, step=0.5, value=8.0, label="b (Máximo):", debounce=False)
    gamma_shape = mo.ui.slider(start=0.1, stop=10.0, step=0.1, value=2.0, label="Shape (k):", debounce=False)
    gamma_rate = mo.ui.slider(start=0.1, stop=5.0, step=0.1, value=0.5, label="Rate (beta):", debounce=False)
    t_df = mo.ui.slider(start=1, stop=100, step=1, value=4, label="df (Graus L.):", debounce=False)
    chi_df = mo.ui.slider(start=1, stop=50, step=1, value=5, label="df (Graus L.):", debounce=False)
    f_df1 = mo.ui.slider(start=1, stop=50, step=1, value=5, label="df1 (Num.):", debounce=False)
    f_df2 = mo.ui.slider(start=1, stop=50, step=1, value=10, label="df2 (Den.):", debounce=False)
    weibull_shape = mo.ui.slider(start=0.1, stop=10.0, step=0.1, value=1.5, label="Shape (c):", debounce=False)
    weibull_scale = mo.ui.slider(start=0.1, stop=10.0, step=0.1, value=3.0, label="Scale (lambda):", debounce=False)
    cauchy_location = mo.ui.slider(start=-10.0, stop=10.0, step=0.5, value=0.0, label="Location (x0):", debounce=False)
    cauchy_scale = mo.ui.slider(start=0.1, stop=5.0, step=0.1, value=1.0, label="Scale (gamma):", debounce=False)
    return (
        unif_a, unif_b, gamma_shape, gamma_rate, t_df, chi_df, f_df1, f_df2,
        weibull_shape, weibull_scale, cauchy_location, cauchy_scale,
    )


@app.cell
def _(
    mo, radio_cont, unif_a, unif_b, gamma_shape, gamma_rate, t_df, chi_df,
    f_df1, f_df2, weibull_shape, weibull_scale, cauchy_location, cauchy_scale,
):
    _grupos_cont = {
        "Uniforme Contínua": [unif_a, unif_b],
        "Gama": [gamma_shape, gamma_rate],
        "Normal Padrão": [mo.md("*Parâmetros fixos: Média = 0, Desvio Padrão = 1*")],
        "t-Student": [t_df],
        "Qui-Quadrado": [chi_df],
        "F-Snedecor": [f_df1, f_df2],
        "Weibull (2 parâmetros)": [weibull_shape, weibull_scale],
        "Cauchy": [cauchy_location, cauchy_scale],
    }
    mo.vstack(_grupos_cont[radio_cont.value])
    return


@app.cell
def _(anywidget, traitlets):
    class ContinuasWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 1180, cssH = 420;

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

            function drawPanel(ctx, ox, pw, H, xVals, yVals, color, fillAlpha, ylo, yhi, title, xlabel, ylabel) {
                const padL = 55 * dpr, padR = 15 * dpr, padT = 45 * dpr, padB = 50 * dpr;
                const plotW = pw - padL - padR;
                const plotH = H - padT - padB;
                const xlo = xVals[0], xhi = xVals[xVals.length - 1];

                function xToPx(x) { return ox + padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                ctx.strokeStyle = "#e5e7eb"; ctx.lineWidth = 1 * dpr;
                ctx.fillStyle = "#555"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right"; ctx.textBaseline = "middle";
                for (let t2 = 0; t2 <= 5; t2++) {
                    const yv = ylo + (yhi - ylo) * (t2 / 5);
                    const py = yToPx(yv);
                    ctx.beginPath(); ctx.moveTo(ox + padL, py); ctx.lineTo(ox + padL + plotW, py); ctx.stroke();
                    ctx.fillText(yv.toFixed(3), ox + padL - 6 * dpr, py);
                }

                if (fillAlpha > 0) {
                    ctx.save();
                    ctx.globalAlpha = fillAlpha;
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.moveTo(xToPx(xVals[0]), yToPx(0));
                    for (let i = 0; i < xVals.length; i++) ctx.lineTo(xToPx(xVals[i]), yToPx(yVals[i]));
                    ctx.lineTo(xToPx(xVals[xVals.length - 1]), yToPx(0));
                    ctx.closePath(); ctx.fill();
                    ctx.restore();
                }

                ctx.strokeStyle = color; ctx.lineWidth = 2.5 * dpr;
                ctx.beginPath();
                for (let i = 0; i < xVals.length; i++) {
                    const px = xToPx(xVals[i]), py = yToPx(yVals[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();

                ctx.strokeStyle = "#333"; ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(ox + padL, padT, plotW, plotH);

                ctx.fillStyle = "#333"; ctx.font = (9 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "top";
                for (let t2 = 0; t2 <= 6; t2++) {
                    const xv = xlo + (xhi - xlo) * (t2 / 6);
                    const px = xToPx(xv);
                    ctx.beginPath(); ctx.moveTo(px, padT + plotH); ctx.lineTo(px, padT + plotH + 4 * dpr); ctx.stroke();
                    ctx.fillText(xv.toFixed(1), px, padT + plotH + 6 * dpr);
                }
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
                ctx.fillStyle = "#111";
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
                const ymaxPdf = Math.max(...payload.y_pdf) * 1.1 || 1;
                drawPanel(ctx, 0, half, H, payload.x_vals, payload.y_pdf, payload.cor_pdf, 0.15, 0, ymaxPdf,
                    payload.titulo_pdf, "Variável Aleatória (x)", "f(x)");
                drawPanel(ctx, half, half, H, payload.x_vals, payload.y_cdf, payload.cor_cdf, 0, -0.05, 1.05,
                    "Distribuição Acumulada (CDF): " + payload.dist_type, "Variável Aleatória (x)", "F(x) = P(X <= x)");

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (ContinuasWidget,)


@app.cell
def _(ContinuasWidget, mo):
    widget_cont = mo.ui.anywidget(ContinuasWidget())
    widget_cont
    return (widget_cont,)


@app.cell
def _(
    mo, np, json, widget_cont, radio_cont,
    uniform, gamma, norm, t, chi2, f, weibull_min, cauchy,
    unif_a, unif_b, gamma_shape, gamma_rate, t_df, chi_df, f_df1, f_df2,
    weibull_shape, weibull_scale, cauchy_location, cauchy_scale,
):
    dist_cont = radio_cont.value
    erro_cont = None
    cor_pdf = cor_cdf = "#1f77b4"

    if dist_cont == "Uniforme Contínua":
        if unif_a.value >= unif_b.value:
            erro_cont = "Erro: O limite inferior (a) deve ser menor que o superior (b)."
            x_c, y_pdf, y_cdf, titulo_c = np.array([0.0, 1.0]), np.array([0.0, 0.0]), np.array([0.0, 0.0]), ""
        else:
            margem = (unif_b.value - unif_a.value) * 0.2
            x_c = np.linspace(unif_a.value - margem, unif_b.value + margem, 1000)
            y_pdf = uniform.pdf(x_c, loc=unif_a.value, scale=unif_b.value - unif_a.value)
            y_cdf = uniform.cdf(x_c, loc=unif_a.value, scale=unif_b.value - unif_a.value)
            titulo_c = f"Função de Densidade (PDF): U({unif_a.value}, {unif_b.value})"
            cor_pdf, cor_cdf = "steelblue", "darkorange"
    elif dist_cont == "Gama":
        scale_gamma = 1.0 / max(gamma_rate.value, 0.001)
        x_max = float(gamma.ppf(0.999, a=gamma_shape.value, scale=scale_gamma))
        x_c = np.linspace(0, x_max, 1000)
        y_pdf = gamma.pdf(x_c, a=gamma_shape.value, scale=scale_gamma)
        y_cdf = gamma.cdf(x_c, a=gamma_shape.value, scale=scale_gamma)
        titulo_c = f"Função de Densidade (PDF): Gama(shape={gamma_shape.value}, rate={gamma_rate.value})"
        cor_pdf, cor_cdf = "#2ca02c", "#9467bd"
    elif dist_cont == "Normal Padrão":
        x_c = np.linspace(-4, 4, 1000)
        y_pdf = norm.pdf(x_c, loc=0, scale=1)
        y_cdf = norm.cdf(x_c, loc=0, scale=1)
        titulo_c = "Função de Densidade (PDF): Normal Padrão Z ~ N(0, 1)"
        cor_pdf, cor_cdf = "#d62728", "#bcbd22"
    elif dist_cont == "t-Student":
        x_c = np.linspace(-4, 4, 1000)
        y_pdf = t.pdf(x_c, df=t_df.value)
        y_cdf = t.cdf(x_c, df=t_df.value)
        titulo_c = f"Função de Densidade (PDF): t-Student(df={t_df.value})"
        cor_pdf, cor_cdf = "#17becf", "#e377c2"
    elif dist_cont == "Qui-Quadrado":
        x_max = float(chi2.ppf(0.999, df=chi_df.value))
        x_c = np.linspace(0, x_max, 1000)
        y_pdf = chi2.pdf(x_c, df=chi_df.value)
        y_cdf = chi2.cdf(x_c, df=chi_df.value)
        titulo_c = f"Função de Densidade (PDF): χ²(df={chi_df.value})"
        cor_pdf, cor_cdf = "#7f7f7f", "#8c564b"
    elif dist_cont == "F-Snedecor":
        x_max = float(f.ppf(0.99, dfn=f_df1.value, dfd=f_df2.value))
        x_c = np.linspace(0.001, x_max, 1000)
        y_pdf = f.pdf(x_c, dfn=f_df1.value, dfd=f_df2.value)
        y_cdf = f.cdf(x_c, dfn=f_df1.value, dfd=f_df2.value)
        titulo_c = f"Função de Densidade (PDF): F(df1={f_df1.value}, df2={f_df2.value})"
        cor_pdf, cor_cdf = "#393b79", "#e7ba52"
    elif dist_cont == "Weibull (2 parâmetros)":
        x_max = float(weibull_min.ppf(0.999, c=weibull_shape.value, scale=weibull_scale.value))
        x_c = np.linspace(0, x_max, 1000)
        y_pdf = weibull_min.pdf(x_c, c=weibull_shape.value, scale=weibull_scale.value)
        y_cdf = weibull_min.cdf(x_c, c=weibull_shape.value, scale=weibull_scale.value)
        titulo_c = f"Função de Densidade (PDF): Weibull(shape={weibull_shape.value}, scale={weibull_scale.value})"
        cor_pdf, cor_cdf = "#1f77b4", "#ff7f0e"
    else:
        x_min = float(cauchy.ppf(0.01, loc=cauchy_location.value, scale=cauchy_scale.value))
        x_max = float(cauchy.ppf(0.99, loc=cauchy_location.value, scale=cauchy_scale.value))
        x_c = np.linspace(x_min, x_max, 1000)
        y_pdf = cauchy.pdf(x_c, loc=cauchy_location.value, scale=cauchy_scale.value)
        y_cdf = cauchy.cdf(x_c, loc=cauchy_location.value, scale=cauchy_scale.value)
        titulo_c = f"Função de Densidade (PDF): Cauchy(loc={cauchy_location.value}, scale={cauchy_scale.value})"
        cor_pdf, cor_cdf = "#9c9ede", "#cedb9c"

    payload_cont = {
        "x_vals": x_c.tolist(), "y_pdf": y_pdf.tolist(), "y_cdf": y_cdf.tolist(),
        "titulo_pdf": titulo_c, "dist_type": dist_cont,
        "cor_pdf": cor_pdf, "cor_cdf": cor_cdf, "erro": erro_cont,
        "seq": (
            f"{dist_cont}-{unif_a.value}-{unif_b.value}-{gamma_shape.value}-{gamma_rate.value}-"
            f"{t_df.value}-{chi_df.value}-{f_df1.value}-{f_df2.value}-{weibull_shape.value}-"
            f"{weibull_scale.value}-{cauchy_location.value}-{cauchy_scale.value}"
        ),
    }
    widget_cont.payload_json = json.dumps(payload_cont)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
