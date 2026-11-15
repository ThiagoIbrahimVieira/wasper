@echo off
chcp 65001 >nul
title WASPER — Ditado por Voz Push-to-Talk 100%% Local

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] Ambiente virtual .venv não encontrado em %~dp0
    echo Por favor, crie o ambiente virtual com 'python -m venv .venv' e instale os pacotes.
    pause
    exit /b 1
)

echo ======================================================================
echo   WASPER — Ditado por Voz Local Push-to-Talk
echo   Whisper (GPU CUDA) + Refinador Ollama + Injetor de Clipboard
echo ======================================================================
echo.
echo   [1] Modo Rápido (Whisper CUDA puro — Latência ~580ms) [PADRÃO]
echo   [2] Modo Refinado (Whisper + Ollama qwen3.5:2b — Pontuação Avançada)
echo   [3] Modo Teste (Sem colar texto — Apenas exibe no terminal)
echo   [4] Executar com parâmetros customizados
echo   [5] Configurar Microfone (Listar e definir microfone)
echo   [6] Teste de Diagnóstico de Voz (Grava 3s e transcreve)
echo.

set /p OPTION="Escolha uma opção [1-6] (pressione ENTER para opção 1): "

if "%OPTION%"=="" set OPTION=1
if "%OPTION%"=="1" goto FAST
if "%OPTION%"=="2" goto REFINED
if "%OPTION%"=="3" goto TEST_MODE
if "%OPTION%"=="4" goto CUSTOM
if "%OPTION%"=="5" goto CONFIG_MIC
if "%OPTION%"=="6" goto TEST_VOICE

:FAST
echo.
echo Iniciando WASPER em Modo Rápido (Whisper base CUDA)...
echo Segure [F8] para ditar em qualquer aplicativo e solte para colar.
echo.
.venv\Scripts\python.exe main.py --hotkey f8
goto END

:REFINED
echo.
echo Iniciando WASPER com Refinamento Ollama (qwen3.5:2b)...
echo Segure [F8] para ditar em qualquer aplicativo e solte para colar.
echo.
.venv\Scripts\python.exe main.py --hotkey f8 --refine
goto END

:TEST_MODE
echo.
echo Iniciando WASPER em Modo Teste (sem simular Ctrl+V)...
echo.
.venv\Scripts\python.exe main.py --hotkey f8 --no-paste
goto END

:CUSTOM
echo.
set /p CUSTOM_ARGS="Digite os parâmetros desejados (ex: --hotkey f9 --model small): "
.venv\Scripts\python.exe main.py %CUSTOM_ARGS%
goto END

:CONFIG_MIC
echo.
.venv\Scripts\python.exe main.py --list-mics
set /p CHOSEN_MIC="Digite o número do seu microfone físico real (ex: 4 ou 16): "
if not "%CHOSEN_MIC%"=="" (
    .venv\Scripts\python.exe main.py --set-mic %CHOSEN_MIC%
)
goto END

:TEST_VOICE
echo.
.venv\Scripts\python.exe test_my_voice.py
goto END

:END
pause
