from pynput import mouse

def on_click(x, y, button, pressed):
    state = "PRESSIONADO" if pressed else "LIBERADO"
    print(f"Botão: {button} (name={getattr(button, 'name', str(button))}) -> {state}")
    if not pressed:
        return False  # encerra após 1 clique de teste

print("Clique em qualquer botão do mouse (inclusive laterais) para testar:")
with mouse.Listener(on_click=on_click) as listener:
    listener.join()
