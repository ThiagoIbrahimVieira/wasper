import sys
import time
import numpy as np

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from audio_utils import load_audio_from_file_or_bytes
from transcriber import WhisperTranscriber

def run_benchmark():
    print("=" * 70)
    print("  WASPER — Benchmark de Transcrição Whisper Local (Fase 2)")
    print("=" * 70)

    curto_audio = load_audio_from_file_or_bytes("c:/Users/thiag/Documents/REA/Wasper/teste_curto.mp3")
    longo_audio = load_audio_from_file_or_bytes("c:/Users/thiag/Documents/REA/Wasper/teste_longo.mp3")

    print(f"[Áudio 1] Duração: {len(curto_audio)/16000:.2f}s | Amostras: {len(curto_audio):,}")
    print(f"[Áudio 2] Duração: {len(longo_audio)/16000:.2f}s | Amostras: {len(longo_audio):,}")

    configurations = [
        {"model": "base", "device": "cuda", "compute": "float16"},
        {"model": "base", "device": "cpu",  "compute": "int8"},
        {"model": "small", "device": "cuda", "compute": "float16"},
        {"model": "small", "device": "cpu",  "compute": "int8"},
    ]

    results = []

    for cfg in configurations:
        m_name = cfg["model"]
        dev = cfg["device"]
        comp = cfg["compute"]
        print(f"\n>>> Avaliando: Modelo='{m_name}' | Device='{dev}' | Compute='{comp}'...")

        try:
            t0 = time.perf_counter()
            transcriber = WhisperTranscriber(model_name=m_name, device=dev, compute_type=comp, language="pt")
            load_ms = (time.perf_counter() - t0) * 1000
            print(f"    ├─ Carregamento do modelo: {load_ms:.1f} ms")

            # Warmup / Áudio curto
            t1 = time.perf_counter()
            r_curto = transcriber.transcribe(curto_audio, language="pt")
            lat_curto_ms = (time.perf_counter() - t1) * 1000
            rtf_curto = (lat_curto_ms / 1000) / (len(curto_audio)/16000)
            print(f"    ├─ [ÁUDIO CURTO - {len(curto_audio)/16000:.2f}s]:")
            print(f"    │   ├─ Latência de inferência: {lat_curto_ms:.1f} ms (RTF: {rtf_curto:.3f}x)")
            print(f"    │   └─ Transcrição: '{r_curto.text}'")

            # Áudio longo
            t2 = time.perf_counter()
            r_longo = transcriber.transcribe(longo_audio, language="pt")
            lat_longo_ms = (time.perf_counter() - t2) * 1000
            rtf_longo = (lat_longo_ms / 1000) / (len(longo_audio)/16000)
            print(f"    └─ [ÁUDIO LONGO - {len(longo_audio)/16000:.2f}s]:")
            print(f"        ├─ Latência de inferência: {lat_longo_ms:.1f} ms (RTF: {rtf_longo:.3f}x)")
            print(f"        └─ Transcrição: '{r_longo.text}'")

            results.append({
                "model": m_name,
                "device": transcriber.actual_device,
                "compute": transcriber.actual_compute_type,
                "load_ms": load_ms,
                "curto_ms": lat_curto_ms,
                "curto_rtf": rtf_curto,
                "curto_text": r_curto.text,
                "longo_ms": lat_longo_ms,
                "longo_rtf": rtf_longo,
                "longo_text": r_longo.text,
            })
        except Exception as e:
            print(f"    [FALHA] Erro na configuração {cfg}: {e}")

    print("\n" + "=" * 70)
    print("  RESUMO COMPARATIVO DE LATÊNCIA REAL (MENOR É MELHOR)")
    print("=" * 70)
    print(f"{'Modelo':<8} | {'Dispositivo':<6} | {'Compute':<8} | {'Áudio Curto (4.4s)':<18} | {'Áudio Longo (14.1s)':<19}")
    print("-" * 70)
    for r in results:
        curto_str = f"{r['curto_ms']:.0f} ms ({r['curto_rtf']:.2f}x)"
        longo_str = f"{r['longo_ms']:.0f} ms ({r['longo_rtf']:.2f}x)"
        print(f"{r['model']:<8} | {r['device']:<6} | {r['compute']:<8} | {curto_str:<18} | {longo_str:<19}")
    print("=" * 70)

if __name__ == "__main__":
    run_benchmark()
