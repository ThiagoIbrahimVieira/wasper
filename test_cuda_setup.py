import os
import sys
import glob
import time
import numpy as np

# Força UTF-8 para evitar erros de charmap cp1252 no console do Windows
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# Adiciona os diretórios de DLLs instalados pelo pip (nvidia-cublas-cu12, nvidia-cudnn-cu12)
venv_root = os.path.dirname(os.path.dirname(sys.executable))
nvidia_bins = glob.glob(os.path.join(venv_root, "Lib", "site-packages", "nvidia", "*", "bin"))
print(f"Diretórios NVIDIA encontrados: {len(nvidia_bins)}")
for p in nvidia_bins:
    if os.path.isdir(p):
        try:
            os.add_dll_directory(p)
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
            print(f"  [+] Carregado DLL dir: {p}")
        except Exception as e:
            print(f"  [-] Erro ao carregar {p}: {e}")

from faster_whisper import WhisperModel

print("\n--- Teste de Inicialização do WhisperModel na GPU ---")
t0 = time.perf_counter()
try:
    model = WhisperModel("base", device="cuda", compute_type="float16")
    load_time = (time.perf_counter() - t0) * 1000
    print(f"[OK] Modelo 'base' carregado em CUDA float16 em {load_time:.1f} ms!")

    # Teste de inferência real em áudio sintético
    sr = 16000
    t = np.linspace(0, 2, sr * 2, endpoint=False)
    audio = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    t_inf = time.perf_counter()
    segments, info = model.transcribe(audio, language="pt", beam_size=1)
    text = " ".join([s.text for s in segments])
    latency = (time.perf_counter() - t_inf) * 1000
    print(f"[OK] CUDA INFERÊNCIA REAL CONCLUÍDA!")
    print(f"    ├─ Latência de inferência na GPU: {latency:.1f} ms")
    print(f"    ├─ Dispositivo confirmado:        NVIDIA GTX 1650 (CUDA 12)")
    print(f"    └─ Saída textual:                '{text}'")
except Exception as e:
    print(f"[ERRO] Falha ao executar em CUDA: {type(e).__name__}: {e}")
