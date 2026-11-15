import sounddevice as sd
import numpy as np

print("Testando níveis de áudio dos microfones candidatos (fale algo agora por 2 segundos)...")

candidates = []
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0:
        name = d['name']
        if any(k in name.lower() for k in ['voicemod', 'lef', 'definition', 'droidcam']):
            candidates.append((i, name, d['hostapi']))

print(f"Candidatos encontrados: {len(candidates)}")
for idx, name, hostapi in candidates:
    try:
        data = sd.rec(int(16000 * 1.5), samplerate=16000, channels=1, dtype='float32', device=idx)
        sd.wait()
        rms = float(np.sqrt(np.mean(data**2)))
        peak = float(np.max(np.abs(data)))
        print(f"Dispositivo [{idx}] '{name}' (HostAPI {hostapi}): RMS={rms:.5f}, Pico={peak:.5f}")
    except Exception as e:
        print(f"Dispositivo [{idx}] '{name}': ERRO ({e})")
