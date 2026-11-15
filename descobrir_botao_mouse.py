"""
Wasper — Detector Interativo de Botão do Mouse
Clique no botão do seu mouse que você deseja usar para o Push-To-Talk!
"""

import sys
import os
import json
import time
from pynput import mouse

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(APP_DIR, "wasper_config.json")

print("=" * 70)
print("  WASPER — DETECTOR DE BOTÃO DO MOUSE")
print("=" * 70)
print("👉 Clique no botão do mouse que você quer usar para falar (ex: lateral)...")
print("   (Pressione Ctrl+C para cancelar)\n")

detected_name = None

def on_click(x, y, button, pressed):
    global detected_name
    if pressed:
        raw_name = getattr(button, "name", str(button)).lower()
        if raw_name in ("x1", "x2", "middle"):
            detected_name = f"mouse_{raw_name}"
        elif "button." in raw_name:
            detected_name = f"mouse_{raw_name.split('.')[-1]}"
        else:
            detected_name = f"mouse_{raw_name}"
        return False  # encerra o listener

with mouse.Listener(on_click=on_click) as listener:
    listener.join()

if detected_name:
    print(f"\n[✓] BOTÃO DETECTADO COM SUCESSO: [{detected_name}]")
    friendly_names = {
        "mouse_x1": "Botão Lateral de Trás (Voltar / Mouse 4)",
        "mouse_x2": "Botão Lateral da Frente (Avançar / Mouse 5)",
        "mouse_middle": "Clique da Rodinha do Mouse (Scroll / Mouse 3)"
    }
    print(f"    Função comum: {friendly_names.get(detected_name, 'Botão adicional')}\n")

    resposta = input(f"Deseja configurar [{detected_name}] como atalho permanente do Wasper? (S/N): ").strip().lower()
    if resposta in ("s", "sim", "y", "yes", ""):
        config = {}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = {}
        config["hotkey"] = detected_name
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"\n[✓] Configuração salva com sucesso no wasper_config.json!")

        # Reinicia o Wasper automaticamente para aplicar a nova tecla
        import subprocess
        try:
            subprocess.run(["powershell", "-Command", "Stop-Process -Name 'Wasper', 'pythonw' -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 1; Start-Process (Join-Path $PWD 'Wasper.exe')"], check=False)
            print("[✓] Wasper reiniciado automaticamente com o novo botão!\n")
        except Exception:
            print("(!) Por favor, feche e abra o Wasper.exe novamente para carregar o novo botão.\n")
    else:
        print("\nConfiguração mantida sem alterações.")
