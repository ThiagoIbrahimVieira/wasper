import sounddevice as sd

print("Default device:", sd.default.device)
print("\nDispositivos de Entrada Disponíveis:")
for i, d in enumerate(sd.query_devices()):
    if d['max_input_channels'] > 0:
        print(f"  [{i}] {d['name']} (Canais: {d['max_input_channels']}, Taxa Padrão: {d['default_samplerate']} Hz)")
