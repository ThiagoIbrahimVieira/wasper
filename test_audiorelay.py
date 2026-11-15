import sounddevice as sd

print("=== PROCURANDO DISPOSITIVOS AUDIORELAY ===")
for idx, d in enumerate(sd.query_devices()):
    name = d['name'].lower()
    if 'audiorelay' in name or 'virtual mic' in name:
        print(f"[{idx}] {d['name']} | HostAPI: {d['hostapi']} | In: {d['max_input_channels']} | Rate: {d['default_samplerate']}")
