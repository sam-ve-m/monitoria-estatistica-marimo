# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "numpy",
#     "pandas",
#     "anywidget",
#     "traitlets",
# ]
# ///

# Canvas JS + live-drag, mesmo padrão usado em TLC_marimo.py /
# tStudent_marimo.py: Python só calcula os números (a trajetória da média
# cumulativa); um widget `anywidget` desenha a linha + pontos + a linha de
# referência no <canvas>, sem passar por matplotlib/PNG. `debounce=False`
# no slider de amostra: o gráfico recalcula a cada passo do arrasto, não
# só ao soltar.
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
    mo.md("# Lei dos Grandes Números — painel interativo")
    return


@app.cell
def _(mo):
    w_amostra = mo.ui.slider(
        start=100, stop=10000, step=100, value=2000,
        label="Amostra (nº de lançamentos):", debounce=False,
    )
    w_semente = mo.ui.number(value=42, start=0, stop=99999, step=1, label="Semente:")
    w_cor = mo.ui.dropdown(
        options={
            "Azul-escuro": "#2c3e50",
            "Verde-petróleo": "#16a085",
            "Roxo": "#8e44ad",
            "Verde": "#27ae60",
        },
        value="Azul-escuro",
        label="Cor da linha:",
    )
    w_pontos = mo.ui.checkbox(value=True, label="Mostrar pontos")
    mo.vstack([
        mo.hstack([w_amostra, w_semente]),
        mo.hstack([w_cor, w_pontos]),
    ])
    return w_amostra, w_semente, w_cor, w_pontos


@app.cell
def _(anywidget, traitlets):
    # Widget criado UMA VEZ -- a célula reativa abaixo só muta o trait
    # `payload_json`, nunca recria o DOM (mesmo princípio do TLCGridWidget).
    class LGNWidget(anywidget.AnyWidget):
        _esm = r"""
        function render({ model, el }) {
            const dpr = window.devicePixelRatio || 1;
            const cssW = 760, cssH = 420;

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
                if (!payload.n_total) return;

                const ctx = canvas.getContext("2d");
                const W = canvas.width, H = canvas.height;
                ctx.clearRect(0, 0, W, H);
                ctx.fillStyle = "#ffffff";
                ctx.fillRect(0, 0, W, H);

                const padL = 60 * dpr, padR = 20 * dpr, padT = 50 * dpr, padB = 50 * dpr;
                const plotW = W - padL - padR;
                const plotH = H - padT - padB;
                const xlo = 1, xhi = payload.n_total;
                const ylo = -0.05, yhi = 1.05;

                function xToPx(x) { return padL + ((x - xlo) / (xhi - xlo)) * plotW; }
                function yToPx(y) { return padT + plotH - ((y - ylo) / (yhi - ylo)) * plotH; }

                // fundo whitegrid: grade horizontal clara
                ctx.strokeStyle = "#e5e7eb";
                ctx.lineWidth = 1 * dpr;
                ctx.fillStyle = "#555";
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "right";
                ctx.textBaseline = "middle";
                for (let yv = 0; yv <= 1.0001; yv += 0.25) {
                    const py = yToPx(yv);
                    ctx.beginPath();
                    ctx.moveTo(padL, py);
                    ctx.lineTo(padL + plotW, py);
                    ctx.stroke();
                    ctx.fillText(yv.toFixed(2), padL - 6 * dpr, py);
                }

                // linha de evolução da média (alpha 0.5, igual ao original)
                ctx.save();
                ctx.globalAlpha = 0.5;
                ctx.strokeStyle = payload.cor;
                ctx.lineWidth = 1.5 * dpr;
                ctx.beginPath();
                const n = payload.n_vals;
                const media = payload.media_vals;
                for (let i = 0; i < n.length; i++) {
                    const px = xToPx(n[i]), py = yToPx(media[i]);
                    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
                }
                ctx.stroke();
                ctx.restore();

                // pontos da média amostral (subamostrados pra não sobrecarregar
                // o canvas com milhares de pontos -- efeito visual equivalente)
                if (payload.mostrar_pontos) {
                    ctx.save();
                    ctx.globalAlpha = 0.6;
                    ctx.fillStyle = "#3498db";
                    const step = Math.max(1, Math.floor(n.length / 600));
                    for (let i = 0; i < n.length; i += step) {
                        const px = xToPx(n[i]), py = yToPx(media[i]);
                        ctx.beginPath();
                        ctx.arc(px, py, 2 * dpr, 0, 2 * Math.PI);
                        ctx.fill();
                    }
                    ctx.restore();
                }

                // valor esperado (0.5), linha tracejada vermelha
                ctx.save();
                ctx.strokeStyle = "#e74c3c";
                ctx.lineWidth = 2 * dpr;
                ctx.setLineDash([6 * dpr, 4 * dpr]);
                const py5 = yToPx(0.5);
                ctx.beginPath();
                ctx.moveTo(padL, py5);
                ctx.lineTo(padL + plotW, py5);
                ctx.stroke();
                ctx.restore();

                // moldura
                ctx.strokeStyle = "#333";
                ctx.lineWidth = 1 * dpr;
                ctx.strokeRect(padL, padT, plotW, plotH);

                // eixo x: ticks em 0, metade, cheio
                ctx.fillStyle = "#333";
                ctx.textAlign = "center";
                ctx.textBaseline = "top";
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                [xlo, Math.round(xhi / 2), xhi].forEach(xv => {
                    const px = xToPx(xv);
                    ctx.fillText(Math.round(xv), px, padT + plotH + 6 * dpr);
                });

                ctx.font = (12 * dpr) + "px system-ui, sans-serif";
                ctx.fillText("Número de Simulações (n)", padL + plotW / 2, padT + plotH + 28 * dpr);

                ctx.save();
                ctx.translate(padL - 42 * dpr, padT + plotH / 2);
                ctx.rotate(-Math.PI / 2);
                ctx.textAlign = "center";
                ctx.fillText("Média Cumulativa", 0, 0);
                ctx.restore();

                // titulo
                ctx.font = "bold " + (15 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "center";
                ctx.textBaseline = "alphabetic";
                ctx.fillText("Lei dos Grandes Números (Simulação Dinâmica)", padL + plotW / 2, padT - 20 * dpr);

                // legenda
                ctx.save();
                const legW = 190 * dpr;
                const legH = (payload.mostrar_pontos ? 62 : 44) * dpr;
                const legX = padL + plotW - legW - 8 * dpr, legY = padT + 8 * dpr;
                ctx.fillStyle = "rgba(255,255,255,0.9)";
                ctx.strokeStyle = "#999";
                ctx.lineWidth = 1 * dpr;
                ctx.fillRect(legX, legY, legW, legH);
                ctx.strokeRect(legX, legY, legW, legH);
                ctx.font = (10 * dpr) + "px system-ui, sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "middle";
                let ly = legY + 14 * dpr;
                ctx.strokeStyle = payload.cor;
                ctx.lineWidth = 2 * dpr;
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.fillStyle = "#111";
                ctx.fillText("Evolução da Média", legX + 34 * dpr, ly);
                if (payload.mostrar_pontos) {
                    ly += 18 * dpr;
                    ctx.fillStyle = "#3498db";
                    ctx.beginPath(); ctx.arc(legX + 18 * dpr, ly, 3 * dpr, 0, 2 * Math.PI); ctx.fill();
                    ctx.fillStyle = "#111";
                    ctx.fillText("Média Amostral", legX + 34 * dpr, ly);
                }
                ly += 18 * dpr;
                ctx.strokeStyle = "#e74c3c";
                ctx.setLineDash([4 * dpr, 3 * dpr]);
                ctx.beginPath(); ctx.moveTo(legX + 8 * dpr, ly); ctx.lineTo(legX + 28 * dpr, ly); ctx.stroke();
                ctx.setLineDash([]);
                ctx.fillStyle = "#111";
                ctx.fillText("Valor Esperado (0.5)", legX + 34 * dpr, ly);
                ctx.restore();

                root.setAttribute("data-render-seq", payload.seq);
            }

            model.on("change:payload_json", draw);
            draw();
        }
        export default { render };
        """
        payload_json = traitlets.Unicode("{}").tag(sync=True)

    return (LGNWidget,)


@app.cell
def _(LGNWidget, mo):
    widget = mo.ui.anywidget(LGNWidget())
    widget
    return (widget,)


@app.cell
def _(mo, np, w_amostra, w_semente, w_cor, w_pontos, widget, json):
    tamanho_amostra = w_amostra.value
    semente_aleatoria = int(w_semente.value)
    cor_da_linha = w_cor.value
    mostrar_pontos = w_pontos.value

    np.random.seed(semente_aleatoria)
    lancamentos = np.random.choice([0, 1], size=tamanho_amostra, replace=True)
    n_vals = np.arange(1, tamanho_amostra + 1)
    sn = np.cumsum(lancamentos)
    media_cumulativa = sn / n_vals

    payload = {
        "n_vals": n_vals.tolist(),
        "media_vals": media_cumulativa.tolist(),
        "n_total": int(tamanho_amostra),
        "cor": cor_da_linha,
        "mostrar_pontos": bool(mostrar_pontos),
        "seq": f"{tamanho_amostra}-{semente_aleatoria}-{cor_da_linha}-{mostrar_pontos}",
    }
    widget.payload_json = json.dumps(payload)
    mo.show_code(position="below")
    return


if __name__ == "__main__":
    app.run()
