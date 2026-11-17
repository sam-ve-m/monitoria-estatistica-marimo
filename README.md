# Monitoria de Estatística UTFPR — notebooks interativos

Notebooks interativos de Estatística para a disciplina, construídos com [marimo](https://marimo.io/) e
publicados como site estático que roda inteiramente no navegador (WebAssembly), via GitHub Pages.

## Tecnologias usadas

- **Python** — cálculo dos dados de cada gráfico (distribuições, amostragens, curvas teóricas).
- **[marimo](https://marimo.io/)** — notebook reativo em Python que vira os controles (sliders, radios) e o
  layout da página.
- **anywidget + JavaScript puro (canvas)** — o Python só calcula os números; um widget `anywidget` passa
  esses números para um `<canvas>` que desenha o gráfico direto no navegador, sem depender de nenhuma
  biblioteca de plotagem em tempo de execução.
- **Pyodide** — runtime que roda o próprio Python dentro do navegador (via WebAssembly), o que permite exportar
  cada notebook como uma página HTML autossuficiente, sem servidor.
- **GitHub Pages** — hospedagem estática gratuita, servindo a pasta `docs/` deste repositório.

## Para os alunos

Basta abrir o link do site, sem instalar nada:

**https://sam-ve-m.github.io/monitoria-estatistica-marimo/**

Mexa nos sliders e controles — o gráfico atualiza em tempo real, já durante o arrasto. No primeiro acesso a
página baixa o runtime Python (alguns segundos); depois disso fica em cache no navegador e os próximos
acessos são rápidos.

## Para quem mantém o repositório (professor ou monitor)

### Requisitos

Python 3.11+ e as dependências:

```
pip install marimo anywidget traitlets numpy scipy
```

(recomendado usar um virtualenv.)

### Editar um notebook existente

Abre um editor local, ao vivo, no navegador:

```
marimo edit notebooks/<Nome>_marimo.py
```

### Exportar para uma página estática (WASM)

No **Windows**:

```
python offline_export_windows.py html-wasm notebooks/<Nome>_marimo.py -o /tmp/export_<Nome> --offline --no-sandbox -f
```

(o wrapper é necessário porque a exportação offline do marimo usa subprocessos do Playwright, que a política
padrão de asyncio do Windows bloqueia — o script só contorna essa política para essa chamada.)

No **Mac/Linux**, o comando direto do marimo já funciona, sem o wrapper:

```
marimo export html-wasm notebooks/<Nome>_marimo.py -o /tmp/export_<Nome> --offline -f
```

### Publicar a página exportada

1. Copie o `index.html` exportado (mais um arquivo vazio `.nojekyll`) para `docs/<Nome>/`.
2. Rode `python rewrite_shared_paths.py docs/<Nome>/index.html` para a página reaproveitar os arquivos
   compartilhados do Pyodide (`docs/_pyodide-assets/`) em vez de duplicar esse runtime em cada notebook.
3. Se for um notebook novo, adicione uma entrada no dicionário `NOTEBOOKS` em `inject_nav.py`. Depois rode
   `python inject_nav.py docs/<slug>/index.html <slug>` para **cada** slug já publicado (não só o novo), para
   que a barra de navegação compartilhada apareça atualizada em todas as páginas (esse mesmo passo também
   mantém a tela de carregamento de cada página correta, então rode-o mesmo que só a navegação tenha mudado).
4. Se for um notebook novo, adicione também um link em `docs/index.html`.
5. `git add -A && git commit -m "..." && git push` — o GitHub Pages republica automaticamente em cerca de 1
   minuto a partir da pasta `docs/` na branch `main`.

### Hospedar sua própria cópia

Qualquer pessoa (por exemplo, o professor) pode fazer um fork ou clone deste repositório exato e hospedar sua
própria cópia, em sua própria conta do GitHub — o GitHub Pages é gratuito e a configuração é só
**Settings → Pages → Deploy from a branch → `main` / `/docs`**.

## Referências

- marimo: https://marimo.io/
- Repositório: https://github.com/sam-ve-m/monitoria-estatistica-marimo
