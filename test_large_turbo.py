import time
import os
import sys

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from transcriber import WhisperTranscriber
from audio_utils import load_audio_from_file_or_bytes

print("=" * 70)
print("  TESTANDO WHISPER LARGE-V3-TURBO NA GTX 1650 (CUDA float16)")
print("=" * 70)

t0 = time.perf_counter()
print("Baixando/Carregando modelo 'large-v3-turbo'...")
transcriber = WhisperTranscriber(
    model_name="large-v3-turbo",
    device="cuda",
    compute_type="float16",
    language="pt"
)
load_time = (time.perf_counter() - t0) * 1000
print(f"[✓] Carregado em {load_time:.1f} ms!")
print(f"    Dispositivo ativo: {transcriber.actual_device.upper()} ({transcriber.actual_compute_type})")

audio_path = os.path.join(os.path.dirname(__file__), "teste_curto.mp3")
audio_data = load_audio_from_file_or_bytes(audio_path)

print(f"\nTranscrevendo áudio de teste curto ({len(audio_data)/16000:.2f}s)...")
t_trans = time.perf_counter()
res = transcriber.transcribe(audio_data, sample_rate=16000, beam_size=1)
elapsed = (time.perf_counter() - t_trans) * 1000

print("-" * 70)
print(f"💬 TRANSCRIÇÃO: \"{res.text}\"")
print(f"⏱️  Tempo de Inferência: {elapsed:.1f} ms")
print(f"🌐 Idioma detectado: {res.language} (probabilidade: {res.language_probability:.2f})")
print("=" * 70)
