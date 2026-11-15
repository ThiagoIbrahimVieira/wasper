# WASPER — Ditado por Voz Push-to-Talk 100% Local

> Reprodução fiel, leve e totalmente offline do fluxo do **Wispr Flow**, desenvolvida a partir de engenharia reversa clean-room via **REA (Reverse Engineer Anything)**.

---

## 🎯 Visão Geral

O **Wasper** permite ditar por voz no Windows com o mesmo comportamento do Wispr Flow:
1. Segure a tecla de atalho (**F8** por padrão) em qualquer janela ou aplicativo (Notepad, VS Code, Navegador, Slack, etc.).
2. Fale naturalmente em português.
3. Solte a tecla: o áudio acumulado em RAM é transcrito localmente na GPU e inserido imediatamente no campo ativo via `Ctrl+V`.
4. O conteúdo que você já tinha copiado na área de transferência é preservado e restaurado automaticamente.

**Zero nuvem. Zero envio de dados. Zero custos de API.**

---

## ⚡ Métricas de Desempenho Medidas (Hardware Real)

Testado e validado em **AMD Ryzen 5 3600 (6c/12t)**, **16 GB RAM** e **NVIDIA GeForce GTX 1650 (4 GB VRAM)**:

| Modo de Operação | Componentes | Latência Ponta a Ponta | Uso de VRAM | Precisão em PT-BR |
| :--- | :--- | :--- | :--- | :--- |
| **Modo Rápido** *(Padrão)* | Whisper `base` (CUDA float16) + Paste | **~580 ms** | ~450 MB | Alta (pontuação básica nativa) |
| **Modo Refinado** | Whisper + Ollama `qwen3.5:2b` + Paste | **~4.7 s** | ~2.4 GB | Muito Alta (capitalização e pontuação LLM) |
| **Modo CPU (Fallback)** | Whisper `base` (CPU int8) + Paste | **~1.1 s** | 0 MB VRAM | Alta |

---

## 🏗️ Arquitetura dos Módulos

```
[ Teclado Global (F8) ] ──────> [ AudioRecorder (RAM) ]
         │                                │
         │ (Solta F8)                     │ (Array NumPy float32)
         ▼                                ▼
[ PushToTalkListener ] ───────> [ WhisperTranscriber (faster-whisper CUDA) ]
                                          │
                                          │ (Texto Bruto)
                                          ▼
                               [ OllamaRefiner (Opcional: qwen3.5:2b) ]
                                          │
                                          │ (Texto Final Formatado)
                                          ▼
                               [ PasteInjector (Win32 keybd_event) ]
                                          │
                                  (Backup Clipboard)
                                    (Simula Ctrl+V)
                                  (Restaura Clipboard)
                                          ▼
                                [ Campo de Texto Ativo ]
```

- **`audio_recorder.py`**: Captura contínua de áudio a 16.000 Hz, mono, float32 diretamente em memória RAM via `sounddevice`. Nenhum arquivo WAV é gravado em disco durante a operação normal.
- **`hotkey_manager.py`**: Monitoramento global de teclado em segundo plano com supressão de auto-repeat do Windows e descarte de toques acidentais (< 200 ms).
- **`transcriber.py`**: Integração com `faster-whisper` em CUDA float16 com registro dinâmico de DLLs cuBLAS/cuDNN e fallback resiliente para CPU int8.
- **`refiner.py`**: Pós-processador semântico local via Ollama (`qwen3.5:2b`). Utiliza prompt few-shot anti-diálogo e parâmetro `think: False` para evitar deriva conversacional ou respostas a perguntas ditadas.
- **`paste_injector.py`**: Salva o conteúdo anterior da área de transferência, copia o texto transcrito, simula `Ctrl+V` nativo via Win32 `keybd_event` e restaura o conteúdo original após 120 ms. O foco da janela ativa é estritamente preservado.
- **`ui_overlay.py`**: Pílula flutuante nativa (PySide6) em estilo Liquid Glass Dark Minimalista, sem bordas, com sombra suave, pulso em Verde Esmeralda e `WindowDoesNotAcceptFocus` (zero roubo de foco).
- **`main.py`**: Loop assíncrono de orquestração unindo áudio, IA, injeção e interface gráfica.

---

## 🚀 Como Executar

### 1. Início Rápido (1 Clique)
Basta clicar duas vezes em **`run_wasper.bat`** e escolher a opção desejada:
- `[1]` Modo Rápido (Whisper CUDA — Latência ~580ms)
- `[2]` Modo Refinado (Whisper + Ollama qwen3.5:2b)
- `[3]` Modo Teste (Sem colar — Apenas visualização no terminal)

### 2. Linha de Comando Direta
```bash
# Modo Rápido (Padrão)
.venv\Scripts\python.exe main.py --hotkey f8

# Modo com Refinamento Ollama
.venv\Scripts\python.exe main.py --hotkey f8 --refine

# Modo com Modelo Whisper Small
.venv\Scripts\python.exe main.py --hotkey f8 --model small

# Modo Apenas Log (sem colar no campo ativo)
.venv\Scripts\python.exe main.py --hotkey f8 --no-paste
```

---

## 🧪 Suíte de Testes Automatizados

O projeto conta com **30 testes automatizados** cobrindo todas as fases:

```bash
.venv\Scripts\python.exe -m unittest discover -s . -p "test_suite_*.py" -v
```

- `test_suite_phase1.py` (7 testes): Áudio em RAM, integridade de amostras, debounce <200ms e supressão de auto-repeat.
- `test_suite_phase2.py` (5 testes): Transcrição em GPU CUDA float16, fallback CPU, precisão em PT-BR e ausência de I/O em disco.
- `test_suite_phase3.py` (6 testes): Conexão Ollama, formatação semântica, anti-diálogo, timeouts e fallback seguro.
- `test_suite_phase4.py` (5 testes): Injeção via `Ctrl+V`, preservação rigorosa do clipboard anterior, suporte a Unicode/emojis e preservação de foco HWND.
- `test_suite_phase5_e2e.py` (4 testes): Pipelines completos ponta a ponta (modo rápido e refinado), rejeição de silêncio e tolerância à queda do Ollama.
- `test_suite_phase6_gui.py` (3 testes): Janela sem foco (`WindowDoesNotAcceptFocus`), estados visuais e despacho thread-safe de sinais Qt.

**Resultado da validação:** `30 tests in 23.9s — OK (100% de aprovação)`.
