# WASPER — Métricas de Desempenho & Benchmarks Reais

> Relatório técnico de telemetria, consumo de VRAM e latência ponta a ponta medidos em hardware real.

[![Voltar ao README](https://img.shields.io/badge/⬅️_VOLTAR_AO_README-README.md-2563eb?style=for-the-badge&labelColor=0a0a0c)](README.md)

---

## 🖥️ Ambiente de Hardware Homologado

Todos os testes e medições de latência foram executados e auditados na máquina física local:

- **Processador (CPU):** AMD Ryzen 5 3600 (6 núcleos, 12 threads @ 3.6 GHz)
- **Memória RAM:** 16 GB DDR4 (Dual Channel @ 2666 MHz)
- **Placa de Vídeo (GPU):** NVIDIA GeForce GTX 1650 (4 GB GDDR5 VRAM)
- **Armazenamento:** SSD NVMe M.2 (gravação em RAM sem tocar no disco)
- **Sistema Operacional:** Windows 11 Pro 64-bit
- **Driver Gráfico:** NVIDIA Game Ready Driver (com suporte a CUDA 12.x)

---

## 📊 Matriz Comparativa de Modelos

| Modo de Operação | Modelo Whisper | Dispositivo | Precisão Numérica | Latência de Inferência | Latência Ponta a Ponta | Uso de VRAM | Acurácia em Português (PT-BR) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Modo Rápido** *(Padrão)* | `base` | CUDA (GTX 1650) | `float16` | **~460 ms** | **~580 ms** | ~450 MB | Alta (pontuação básica nativa) |
| **Modo Produção** *(Recomendado)* | `large-v3-turbo` | CUDA (GTX 1650) | `float16` | **~3.2 s** | **~3.6 s** | ~1.8 GB | **Nível Humano (Zero alucinações de idioma)** |
| **Modo Balanceado** | `small` | CUDA (GTX 1650) | `float16` | **~980 ms** | **~1.1 s** | ~900 MB | Média/Alta (rápido com boa precisão) |
| **Modo Médio** | `medium` | CUDA (GTX 1650) | `float16` | **~2.4 s** | **~2.8 s** | ~1.5 GB | Alta |
| **Modo Refinado (LLM)** | `base` + Ollama `qwen3.5:2b` | CUDA + Ollama | `float16` | **~4.5 s** | **~4.7 s** | ~2.4 GB | Muito Alta (capitalização e pontuação formal) |
| **Modo CPU (Fallback)** | `base` | CPU (Ryzen 5 3600) | `int8` | **~950 ms** | **~1.1 s** | 0 MB | Alta (resiliente para máquinas sem GPU) |

---

## 🔍 Detalhamento das Etapas de Latência

O fluxo ponta a ponta do Wasper é dividido em 4 fases atômicas:

```
[ PTT Release ] ─(1)─> [ Stop Stream ] ─(2)─> [ Faster-Whisper GPU ] ─(3)─> [ Paste Injekt ] ─(4)─> [ Text Injected ]
      0ms                    ~5ms                       ~460ms                     ~115ms                  ~580ms
```

1. **Encerramento de Buffer em RAM (~5 ms):** Desconexão do stream do `sounddevice` e conversão do array NumPy `float32` sem escrita em disco.
2. **Inferência Whisper CUDA (~460 ms no modo base / ~3.2s no turbo):** Processamento direto na VRAM da GTX 1650 via engine `faster-whisper` (CTranslate2).
3. **Limpador Heurístico de Disfluências (< 1 ms):** Remoção de hesitações e gagueiras em tempo constante (`text_cleaner.py`).
4. **Backup, Injeção e Restauração de Clipboard (~115 ms):** Cópia do texto transcrito para o clipboard, disparo de `keybd_event` para simular `Ctrl+V` nativo do Windows e restauração do conteúdo prévio da área de transferência após 120 ms.

---

## 🔬 Arquitetura Two-Pass Streaming

Para garantir feedback visual instantâneo sem sacrificar a precisão final, o Wasper adota uma estratégia de dois tempos:

- **Passo 1 — Prévia em Tempo Real (Enquanto fala):**  
  O modelo Whisper `tiny` roda com janela deslizante a cada ~500 ms de áudio capturado. A latência de inferência é de apenas **~5 a 12 ms** em CUDA, permitindo que as palavras surjam dinamicamente na pílula flutuante enquanto você ainda está falando.
- **Passo 2 — Consolidação Definitiva (Ao soltar a tecla):**  
  Ao soltar a tecla ou botão do mouse, a gravação é congelada e o modelo homologado (`large-v3-turbo` ou `base`) executa a passada completa com contexto semântico total, aplicando pontuação rigorosa, acentuação e formatação numérica.

---

## 🧪 Como Executar os Benchmarks na Sua Máquina

Você pode reproduzir estas medições no seu próprio hardware utilizando os scripts de diagnóstico incluídos na pasta `tools/`:

```bash
# Ativar o ambiente virtual
.venv\Scripts\activate

# 1. Benchmark comparativo de modelos Whisper
python tools/benchmark_models.py

# 2. Diagnóstico de microfone e níveis de ruído
python tools/diagnose_mic.py

# 3. Teste de conformidade de DLLs e aceleração CUDA
python tests/test_cuda_setup.py
```

---

<p align="center">
  <a href="README.md"><b>⬅️ Voltar para a Página Principal do Wasper</b></a>
</p>
