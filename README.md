# WASPER

> **Ditado por voz Push-to-Talk 100% local e offline no Windows com Whisper (CUDA float16) e PySide6.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![CUDA float16](https://img.shields.io/badge/CUDA-float16-76B900?style=flat-square&logo=nvidia&logoColor=white)](https://developer.nvidia.com/cuda-toolkit)
[![PySide6](https://img.shields.io/badge/PySide6-Liquid_Glass-41CD52?style=flat-square&logo=qt&logoColor=white)](https://doc.qt.io/qtforpython-6/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](LICENSE)

[📖 Guia Completo & Instalação](GUIA.md) • [📊 Métricas & Telemetria](BENCHMARKS.md)

---

## 🎯 Apresentação & Proposta de Valor

O **Wasper** é um sistema de ditado por voz universal para Windows, construído sob a filosofia **Local-First**: zero envio de dados para servidores externos, zero telemetria invasiva e zero custos recorrentes de APIs.

Desenvolvido a partir de engenharia reversa clean-room via metodologia **REA (Reverse Engineer Anything)**, ele reproduz com precisão cirúrgica a experiência tátil e imediata de softwares comerciais como o *Wispr Flow*:

1. **Ativação Instantânea Push-to-Talk:** Segure a tecla de atalho (**`F8`** por padrão) ou os botões laterais do mouse (**`mouse_x1`** / **`mouse_x2`**) em qualquer aplicativo aberto (VS Code, Cursor, Obsidian, navegadores, Slack, terminal ou Word).
2. **Gravação Exclusiva em Memória RAM:** O áudio é capturado e bufferizado em tempo real na memória (16.000 Hz, mono, float32). **Nenhum arquivo WAV é escrito em disco** no fluxo operacional normal, garantindo latência mínima e privacidade total.
3. **Transcrição de Alta Precisão na GPU:** Ao soltar o atalho, o modelo **`large-v3-turbo`** (ou `small`/`base`) roda em CUDA `float16` na sua placa de vídeo com acurácia a nível humano em português do Brasil.
4. **Injeção Atômica sem Roubo de Foco:** O texto transcrito é injetado no campo ativo via simulação segura de `Ctrl+V`. **O conteúdo anterior da sua área de transferência é preservado e restaurado automaticamente após 120 ms.**

---

## ✨ Destaques de Engenharia

- 💎 **Pílula Flutuante em Liquid Glass (PySide6):** Interface moderna em formato squircle, dark minimalista (`#0a0a0c`), com sombras difusas, pulso suave em verde esmeralda e a flag `Qt.WindowDoesNotAcceptFocus` (a janela flutua sobre seus apps sem jamais roubar o cursor de digitação).
- 🔄 **Two-Pass Streaming:** Durante o pressionamento, uma amostragem preliminar ultrarrápida do Whisper `tiny` (~5ms de latência) exibe as palavras em tempo real na pílula flutuante (que se expande dinamicamente de 220px a 520px). Ao soltar, o modelo `large-v3-turbo` consolida a sentença com pontuação e gramática perfeitas.
- 🖱️ **Interceptação de Mouse com Supressão Win32:** Hook de baixo nível (`WH_MOUSE_LL`) para botões laterais do mouse (Mouse 4 e Mouse 5) com `suppress_event()`, permitindo usar o polegar para ditar sem disparar o comando nativo de "Voltar Página" no navegador.
- 🧹 **Limpador Heurístico de Disfluências (`text_cleaner.py`):** Filtra gagueiras, repetições acidentais e hesitações prolongadas ("ééé", "hum", "tipo assim") em tempo constante (< 1 ms), sem consumir VRAM extra e preservando contrações naturais de diálogo ("né?", "sabe?").
- 📱 **Integração com Celular via AudioRelay:** Suporte verificado a microfones sem fio virtuais via Wi-Fi/USB, permitindo usar o microfone de alta fidelidade do smartphone diretamente no PC.
- 🛡️ **Launcher Nativo em C# (`Wasper.exe`):** Inicializador leve com `Mutex` de instância única e trava a nível de kernel (`msvcrt.locking`), garantindo que apenas uma instância acesse o driver de áudio e hooks por vez.

---

## 🚀 Documentação & Guias Técnicos

Toda a documentação operacional, passos de instalação e análises de desempenho estão organizados em documentos dedicados:

<p align="center">
  <a href="GUIA.md">
    <img src="https://img.shields.io/badge/📖_COMO_FAZER_FUNCIONAR-GUIA_DE_INSTALAÇÃO_&_ARQUITETURA-fbbf24?style=for-the-badge&labelColor=0a0a0c" alt="Guia Completo e Instalação" />
  </a>
  <br /><br />
  <a href="BENCHMARKS.md">
    <img src="https://img.shields.io/badge/📊_BENCHMARKS_&_TELEMETRIA-MÉTRICAS_EM_HARDWARE_REAL-10b981?style=for-the-badge&labelColor=0a0a0c" alt="Benchmarks e Telemetria" />
  </a>
</p>

---

## 📄 Licença

Este projeto é disponibilizado sob a licença **MIT**. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<p align="center">
  <b>Desenvolvido por Thiago Ibrahim Vieira (Thiago TT)</b><br />
  <sub>Engenharia Web de Alta Performance · Sistemas Locais & IA · Estilização Brutalista</sub><br />
  <a href="https://portifolio-thiago-ibrahim.vercel.app">Portfólio Pessoal</a> · <a href="https://github.com/ThiagoIbrahimVieira">GitHub</a>
</p>
