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

# Painel comparativo com 8 distribuições contínuas (Uniforme, Gama,
# Normal Padrão, t-Student, Qui-Quadrado, F-Snedecor, Weibull, Cauchy),
# cada uma com PDF (curva + preenchimento leve) e CDF lado a lado -- mesma
# estrutura de "radio + grupo de sliders visível por distribuição" do
# DistribuicoesDiscretas.
import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import uniform, gamma, norm, t, chi2, f, weibull_min, cauchy
    import anywidget
    import traitlets
    import json

    return mo, np, uniform, gamma, norm, t, chi2, f, weibull_min, cauchy, anywidget, traitlets, json


@app.cell
def _(mo):
    mo.md("# Painel de Distribuições Contínuas Comparativo")
    return


@app.cell
def _(mo):
    radio_dist = mo.ui.radio(
        options=[
            "Uniforme Contínua", "Gama", "Normal Padrão", "t-Student",
            "Qui-Quadrado", "F-Snedecor", "Weibull (2 parâmetros)", "Cauchy",
        ],
        value="Uniforme Contínua", label="Distribuição:",
    )
    radio_dist
    return (radio_dist,)


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
    mo, radio_dist, unif_a, unif_b, gamma_shape, gamma_rate, t_df, chi_df,
    f_df1, f_df2, weibull_shape, weibull_scale, cauchy_location, cauchy_scale,
):
    _grupos = {
        "Uniforme Contínua": [unif_a, unif_b],
        "Gama": [gamma_shape, gamma_rate],
        "Normal Padrão": [mo.md("*Parâmetros fixos: Média = 0, Desvio Padrão = 1*")],
        "t-Student": [t_df],
        "Qui-Quadrado": [chi_df],
        "F-Snedecor": [f_df1, f_df2],
        "Weibull (2 parâmetros)": [weibull_shape, weibull_scale],
        "Cauchy": [cauchy_location, cauchy_scale],
    }
    mo.vstack(_grupos[radio_dist.value])
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
    widget = mo.ui.anywidget(ContinuasWidget())
    widget
    return (widget,)


@app.cell
def _(
    mo, np, json, widget, radio_dist,
    uniform, gamma, norm, t, chi2, f, weibull_min, cauchy,
    unif_a, unif_b, gamma_shape, gamma_rate, t_df, chi_df, f_df1, f_df2,
    weibull_shape, weibull_scale, cauchy_location, cauchy_scale,
):
    dist_type = radio_dist.value
    erro = None
    cor_pdf = cor_cdf = "#1f77b4"

    if dist_type == "Uniforme Contínua":
        if unif_a.value >= unif_b.value:
            erro = "Erro: O limite inferior (a) deve ser menor que o superior (b)."
            x_vals, y_pdf, y_cdf, titulo_pdf = np.array([0.0, 1.0]), np.array([0.0, 0.0]), np.array([0.0, 0.0]), ""
        else:
            margem = (unif_b.value - unif_a.value) * 0.2
            x_vals = np.linspace(unif_a.value - margem, unif_b.value + margem, 1000)
            y_pdf = uniform.pdf(x_vals, loc=unif_a.value, scale=unif_b.value - unif_a.value)
            y_cdf = uniform.cdf(x_vals, loc=unif_a.value, scale=unif_b.value - unif_a.value)
            titulo_pdf = f"Função de Densidade (PDF): U({unif_a.value}, {unif_b.value})"
            cor_pdf, cor_cdf = "steelblue", "darkorange"
    elif dist_type == "Gama":
        scale_gamma = 1.0 / max(gamma_rate.value, 0.001)
        x_max = float(gamma.ppf(0.999, a=gamma_shape.value, scale=scale_gamma))
        x_vals = np.linspace(0, x_max, 1000)
        y_pdf = gamma.pdf(x_vals, a=gamma_shape.value, scale=scale_gamma)
        y_cdf = gamma.cdf(x_vals, a=gamma_shape.value, scale=scale_gamma)
        titulo_pdf = f"Função de Densidade (PDF): Gama(shape={gamma_shape.value}, rate={gamma_rate.value})"
        cor_pdf, cor_cdf = "#2ca02c", "#9467bd"
    elif dist_type == "Normal Padrão":
        x_vals = np.linspace(-4, 4, 1000)
        y_pdf = norm.pdf(x_vals, loc=0, scale=1)
        y_cdf = norm.cdf(x_vals, loc=0, scale=1)
        titulo_pdf = "Função de Densidade (PDF): Normal Padrão Z ~ N(0, 1)"
        cor_pdf, cor_cdf = "#d62728", "#bcbd22"
    elif dist_type == "t-Student":
        x_vals = np.linspace(-4, 4, 1000)
        y_pdf = t.pdf(x_vals, df=t_df.value)
        y_cdf = t.cdf(x_vals, df=t_df.value)
        titulo_pdf = f"Função de Densidade (PDF): t-Student(df={t_df.value})"
        cor_pdf, cor_cdf = "#17becf", "#e377c2"
    elif dist_type == "Qui-Quadrado":
        x_max = float(chi2.ppf(0.999, df=chi_df.value))
        x_vals = np.linspace(0, x_max, 1000)
        y_pdf = chi2.pdf(x_vals, df=chi_df.value)
        y_cdf = chi2.cdf(x_vals, df=chi_df.value)
        titulo_pdf = f"Função de Densidade (PDF): χ²(df={chi_df.value})"
        cor_pdf, cor_cdf = "#7f7f7f", "#8c564b"
    elif dist_type == "F-Snedecor":
        x_max = float(f.ppf(0.99, dfn=f_df1.value, dfd=f_df2.value))
        x_vals = np.linspace(0.001, x_max, 1000)
        y_pdf = f.pdf(x_vals, dfn=f_df1.value, dfd=f_df2.value)
        y_cdf = f.cdf(x_vals, dfn=f_df1.value, dfd=f_df2.value)
        titulo_pdf = f"Função de Densidade (PDF): F(df1={f_df1.value}, df2={f_df2.value})"
        cor_pdf, cor_cdf = "#393b79", "#e7ba52"
    elif dist_type == "Weibull (2 parâmetros)":
        x_max = float(weibull_min.ppf(0.999, c=weibull_shape.value, scale=weibull_scale.value))
        x_vals = np.linspace(0, x_max, 1000)
        y_pdf = weibull_min.pdf(x_vals, c=weibull_shape.value, scale=weibull_scale.value)
        y_cdf = weibull_min.cdf(x_vals, c=weibull_shape.value, scale=weibull_scale.value)
        titulo_pdf = f"Função de Densidade (PDF): Weibull(shape={weibull_shape.value}, scale={weibull_scale.value})"
        cor_pdf, cor_cdf = "#1f77b4", "#ff7f0e"
    else:
        x_min = float(cauchy.ppf(0.01, loc=cauchy_location.value, scale=cauchy_scale.value))
        x_max = float(cauchy.ppf(0.99, loc=cauchy_location.value, scale=cauchy_scale.value))
        x_vals = np.linspace(x_min, x_max, 1000)
        y_pdf = cauchy.pdf(x_vals, loc=cauchy_location.value, scale=cauchy_scale.value)
        y_cdf = cauchy.cdf(x_vals, loc=cauchy_location.value, scale=cauchy_scale.value)
        titulo_pdf = f"Função de Densidade (PDF): Cauchy(loc={cauchy_location.value}, scale={cauchy_scale.value})"
        cor_pdf, cor_cdf = "#9c9ede", "#cedb9c"

    payload = {
        "x_vals": x_vals.tolist(), "y_pdf": y_pdf.tolist(), "y_cdf": y_cdf.tolist(),
        "titulo_pdf": titulo_pdf, "dist_type": dist_type,
        "cor_pdf": cor_pdf, "cor_cdf": cor_cdf, "erro": erro,
        "seq": (
            f"{dist_type}-{unif_a.value}-{unif_b.value}-{gamma_shape.value}-{gamma_rate.value}-"
            f"{t_df.value}-{chi_df.value}-{f_df1.value}-{f_df2.value}-{weibull_shape.value}-"
            f"{weibull_scale.value}-{cauchy_location.value}-{cauchy_scale.value}"
        ),
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
