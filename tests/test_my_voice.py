"""
Wasper — Teste Direto de Voz e Microfone (Diagnóstico AudioRelay)
Grava 3 segundos do dispositivo configurado, mede volume real e transcreve com o Whisper.
"""

import os
import sys
import json
import time
import wave
import numpy as np
import sounddevice as sd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from transcriber import WhisperTranscriber

# Lê o microfone e modelo configurados
cfg_path = os.path.join(os.path.dirname(__file__), "wasper_config.json")
mic_idx = 2  # AudioRelay por padrão
model_name = "small"
if os.path.exists(cfg_path):
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            mic_idx = cfg.get("mic", 2)
            model_name = cfg.get("model", "small")
    except Exception:
        pass

dev_info = sd.query_devices(mic_idx)

print("=" * 70)
print("  WASPER — DIAGNÓSTICO DO MICROFONE (AUDIORELAY)")
print("=" * 70)
print(f"Dispositivo selecionado: [{mic_idx}] {dev_info['name']}")
print("Taxa nativa:", dev_info['default_samplerate'], "Hz")
print("-" * 70)
print("👉 Fale no seu celular pelo AudioRelay agora...")
print("   Gravando 3 segundos a partir de AGORA...\n")

t0 = time.time()
audio = sd.rec(int(16000 * 3.5), samplerate=16000, channels=1, dtype='float32', device=mic_idx)
sd.wait()
print("[✓] Gravação concluída!")

# Métricas de áudio
rms = float(np.sqrt(np.mean(audio**2)))
peak = float(np.max(np.abs(audio)))

print(f"\n📊 Análise do Sinal Recebido:")
print(f"   ├─ Nível de Energia (RMS): {rms:.5f}")
print(f"   └─ Pico Máximo:            {peak:.5f}")

# Salva WAV para inspeção
clamped = np.clip(audio, -1.0, 1.0)
int16_data = (clamped * 32767.0).astype(np.int16)
with wave.open("minha_voz.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(int16_data.tobytes())
print("   └─ Cópia salva em:         minha_voz.wav")

if rms < 0.0005:
    print("\n⚠️  ATENÇÃO: O sinal de áudio está PRATICAMENTE ZERADO (MUDO)!")
    print("   Possíveis causas:")
    print("   1. O microfone no app do AudioRelay no celular está mutado.")
    print("   2. O AudioRelay no PC não está conectado ao celular.")
    print("   3. O Windows mutou o dispositivo 'Virtual Mic for AudioRelay' nas configurações de som.")
else:
    print(f"\n🎙️  Áudio audível detectado! Transcrevendo com Whisper '{model_name}' (CUDA)...")
    t_whisper = time.perf_counter()
    transcriber = WhisperTranscriber(model_name=model_name, device="auto", language="pt")
    res = transcriber.transcribe(audio.reshape(-1), sample_rate=16000)
    elapsed = (time.perf_counter() - t_whisper) * 1000

    print("=" * 70)
    print(f"💬 TRANSCRIÇÃO: \"{res.text}\"")
    print(f"⏱️  Tempo de Inferência: {elapsed:.1f} ms")
    print("=" * 70)
