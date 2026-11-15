import sounddevice as sd
import numpy as np
import wave

device_idx = 2  # AudioRelay
print(f"Testando gravação de 2 segundos do AudioRelay (Dispositivo {device_idx})...")

try:
    # Testa gravação a 16000 Hz direto
    rec16 = sd.rec(int(16000 * 2), samplerate=16000, channels=1, dtype='float32', device=device_idx)
    sd.wait()
    rms = float(np.sqrt(np.mean(rec16**2)))
    peak = float(np.max(np.abs(rec16)))
    print(f"Gravado a 16kHz direto: Amostras={len(rec16)}, RMS={rms:.5f}, Pico={peak:.5f}")

    # Salva em test_audiorelay_16k.wav
    int16_data = (np.clip(rec16, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open("test_audiorelay_16k.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(int16_data.tobytes())
    print("Salvo com sucesso em test_audiorelay_16k.wav")

except Exception as e:
    print(f"Erro ao gravar do AudioRelay: {e}")
