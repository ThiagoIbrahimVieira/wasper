# WASPER — Guia Completo, Arquitetura e Execução

> Manual detalhado de instalação, configuração, arquitetura de módulos e testes do Wasper.

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/⬅️_VOLTAR_AO_README-README.md-2563eb?style=for-the-badge&labelColor=0a0a0c" alt="Voltar ao README" /></a>
  <a href="BENCHMARKS.md"><img src="https://img.shields.io/badge/📊_BENCHMARKS_DETALHADOS-BENCHMARKS.md-10b981?style=for-the-badge&labelColor=0a0a0c" alt="Ver Benchmarks" /></a>
</p>

---

## ⚡ Métricas de Desempenho & Telemetria

Os benchmarks de latência (~580 ms no modo rápido / ~3.2 s em `large-v3-turbo`), consumo de VRAM e acurácia foram auditados e homologados em hardware real (**AMD Ryzen 5 3600** + **NVIDIA GeForce GTX 1650 4GB**).

> 📊 **Matriz Completa de Benchmarks:** Para ver a tabela detalhada com consumo de VRAM de cada modelo, latência de cada etapa e tempos de inferência, consulte o documento dedicado: [BENCHMARKS.md](BENCHMARKS.md).

---

## 🏗️ Arquitetura e Estrutura de Arquivos

O projeto adota uma arquitetura modular limpa, isolando responsabilidades entre captura de áudio, inferência de IA, injeção Win32 e interface gráfica:

```
wasper/
├── src/                          # 📦 Núcleo de engenharia da aplicação
│   ├── __init__.py               # Pacote Python
│   ├── main.py                   # Loop assíncrono de orquestração geral
│   ├── audio_recorder.py         # Captura estrita em RAM via sounddevice (16kHz float32)
│   ├── audio_utils.py            # Utilitários de conversão e normalização de áudio
│   ├── hotkey_manager.py         # Hooks globais de teclado e botões laterais do mouse
│   ├── transcriber.py            # Engine faster-whisper com aceleração CUDA float16
│   ├── text_cleaner.py           # Filtro heurístico de gagueiras e disfluências (<1ms)
│   ├── refiner.py                # Pós-processador semântico local via Ollama (opcional)
│   ├── paste_injector.py         # Simulação de Ctrl+V via Win32 com preservação de clipboard
│   └── ui_overlay.py             # Pílula flutuante Liquid Glass em PySide6 + Tray Icon
│
├── tests/                        # 🧪 Suíte completa de testes automatizados (30 testes)
│   ├── __init__.py
│   ├── test_suite_phase1.py      # Testes de gravação em RAM, integridade e debounce
│   ├── test_suite_phase2.py      # Testes de transcrição em GPU CUDA e precisão PT-BR
│   ├── test_suite_phase3.py      # Testes de conexão com LLM local e timeout
│   ├── test_suite_phase4.py      # Testes de injeção Ctrl+V, clipboard e foco de janela
│   ├── test_suite_phase5_e2e.py  # Testes ponta a ponta e tolerância a falhas
│   ├── test_suite_phase6_gui.py  # Testes de comportamento de janela e sinais Qt
│   ├── test_cuda_setup.py        # Diagnóstico de DLLs NVIDIA e cuBLAS/cuDNN
│   └── test_my_voice.py          # Script de calibração rápida de microfone
│
├── tools/                        # 🛠️ Ferramentas de calibração e diagnóstico
│   ├── __init__.py
│   ├── benchmark_models.py       # Benchmark comparativo de latência entre modelos
│   ├── descobrir_botao_mouse.py  # Detector interativo de códigos de botões do mouse
│   ├── diagnose_mic.py           # Análise espectral de níveis de ruído do microfone
│   └── probe_devices.py          # Enumeração detalhada de placas e drivers de som
│
├── main.py                       # 🚀 Ponto de entrada CLI (encaminha para src.main)
├── Wasper.exe                    # ⚡ Executável compilado silencioso (1 clique)
├── WasperLauncher.cs             # Código-fonte C# do launcher Win32 com Mutex
├── build_launcher.bat            # Script de compilação do executável com csc.exe
├── run_wasper.bat                # Menu interativo em lote para console
├── requirements.txt              # Dependências Python pinadas e validadas
├── wasper_config.json            # Configuração persistente (atalho, microfone, modelo)
├── BENCHMARKS.md                 # 📊 Relatório técnico de desempenho e telemetria
├── GUIA.md                       # 📖 Este guia de arquitetura e instalação
└── .gitignore                    # Regras de proteção de repositório
```

---

## ⚡ Como Fazer Funcionar

Siga os passos abaixo para colocar o **Wasper** rodando na sua máquina em menos de 5 minutos:

### 1. Pré-Requisitos do Sistema
- **Sistema Operacional:** Windows 10 ou Windows 11 (64-bit).
- **Python:** Versão **3.10** ou **3.11** instalada e adicionada ao `PATH`.
- **Placa de Vídeo (Opcional, mas altamente recomendada):** Placa NVIDIA GeForce (GTX 1050+, GTX 1650, RTX 20/30/40) com drivers atualizados. *(Se não tiver GPU dedicada, o Wasper roda automaticamente em modo CPU int8).*

---

### 2. Clonando o Repositório
Abra o terminal (PowerShell ou Prompt de Comando) e clone o projeto:
```bash
git clone https://github.com/ThiagoIbrahimVieira/wasper.git
cd wasper
```

---

### 3. Criando o Ambiente Virtual
Isole as dependências criando uma pasta `.venv` na raiz do projeto:
```bash
python -m venv .venv
```

Ative o ambiente virtual:
```powershell
# No PowerShell:
.venv\Scripts\Activate.ps1

# No Prompt de Comando (CMD):
.venv\Scripts\activate.bat
```

---

### 4. Instalando as Dependências
Instale todas as bibliotecas necessárias com um único comando:
```bash
pip install -r requirements.txt
```

> **Nota para GPU NVIDIA (CUDA):** As bibliotecas `nvidia-cublas-cu12` e `nvidia-cudnn-cu12` já estão no `requirements.txt`. O Wasper detecta e vincula as DLLs dinamicamente sem necessidade de instalar o CUDA Toolkit completo do sistema.

---

### 5. Configurando o Microfone
Liste os dispositivos de áudio disponíveis para identificar o número do seu microfone físico:
```bash
python main.py --list-mics
```

Defina o seu microfone padrão (substitua pelo número listado):
```bash
python main.py --set-mic 1
```
*(Esta configuração fica salva permanentemente em `wasper_config.json`).*

---

### 6. Executando o Wasper

Você tem 3 maneiras fáceis de iniciar:

#### Opção A: Executável Silencioso (1 Clique)
Dê um duplo clique no arquivo **`Wasper.exe`**.  
Ele executa em segundo plano sem abrir nenhuma janela preta de terminal, adiciona um ícone na bandeja do sistema (perto do relógio) e exibe a pílula de boas-vindas na tela.

#### Opção B: Menu Interativo no Terminal
Dê um duplo clique em **`run_wasper.bat`** para ver o menu rápido com seleção de modos e testes de áudio.

#### Opção C: Linha de Comando Direta
Execute com parâmetros customizados:
```bash
# Execução padrão com Whisper base
python main.py --hotkey f8

# Execução com máxima precisão (large-v3-turbo)
python main.py --model large-v3-turbo

# Salvar modelo large-v3-turbo como padrão permanente
python main.py --set-model large-v3-turbo

# Usar botão lateral do mouse (Mouse 4 ou Mouse 5)
python main.py --set-hotkey mouse_x1
```

---

### 7. Como Usar no Dia a Dia
1. Abra qualquer janela (ex: Bloco de Notas, VS Code, Google Docs, WhatsApp Web).
2. **Segure a tecla `F8`** (ou o botão lateral configurado).
3. A pílula flutuante em Liquid Glass aparecerá dizendo **"Ouvindo..."**.
4. Fale naturalmente em português.
5. **Solte a tecla:** A pílula mostrará rapidamente **"Transcrevendo..."** e o texto será colado onde estava o seu cursor!

---

## 🧪 Executando os Testes Automatizados

Para certificar que todo o pipeline de áudio, IA e injeção Win32 está operacional no seu hardware:

```bash
# Executar a suíte completa de 30 testes:
.venv\Scripts\python.exe -m unittest discover -s tests -p "test_suite_*.py" -v
```

---

<p align="center">
  <a href="README.md"><b>⬅️ Voltar para a Página Principal do Wasper</b></a>
</p>
