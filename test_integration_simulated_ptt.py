import time
from pynput import keyboard
from audio_recorder import AudioRecorder
from hotkey_manager import PushToTalkListener


def run_integration_test():
    print("[TESTE INTEGRAÇÃO] Iniciando teste automatizado de ponta a ponta...")

    recorder = AudioRecorder(sample_rate=16000)
    recorder.start_stream()

    events_captured = []

    def on_start():
        recorder.start_recording()
        events_captured.append(("start", time.perf_counter()))
        print("  -> Listener detectou PRESSIONAMENTO de F8 (Iniciando gravação)")

    def on_stop(duration):
        res = recorder.stop_recording()
        events_captured.append(("stop", duration, res))
        print(f"  -> Listener detectou SOLTURA de F8 (Duração: {duration:.3f}s, Amostras: {res.total_samples})")

    def on_discard(duration):
        recorder.stop_recording()
        events_captured.append(("discard", duration))
        print(f"  -> Listener detectou DESCARTE anti-clique (Duração: {duration*1000:.1f}ms)")

    listener = PushToTalkListener(
        hotkey_name="f8",
        debounce_seconds=0.20,
        on_press_start=on_start,
        on_release_stop=on_stop,
        on_discard=on_discard
    )

    listener.start()
    time.sleep(0.2)  # Aguarda thread do listener estabilizar

    controller = keyboard.Controller()

    # CENÁRIO 1: Pressão válida sustentada de 1.0 segundo
    print("\n[CENÁRIO 1] Simulando segurar a tecla F8 por 1.0 segundo...")
    controller.press(keyboard.Key.f8)
    time.sleep(1.0)
    controller.release(keyboard.Key.f8)
    time.sleep(0.3)  # Aguarda processamento

    assert len(events_captured) >= 2, "Deveria ter capturado eventos de start e stop"
    assert events_captured[0][0] == "start"
    assert events_captured[1][0] == "stop"
    valid_res = events_captured[1][2]
    assert valid_res is not None
    assert valid_res.total_samples > 12000, f"Esperado > 12000 amostras, obteve {valid_res.total_samples}"
    print(f"  [SUCESSO] Cenário 1 validado: {valid_res.total_samples} amostras gravadas em {valid_res.duration_seconds:.3f}s")

    # CENÁRIO 2: Toque rápido acidental (70 ms)
    print("\n[CENÁRIO 2] Simulando clique rápido acidental em F8 (70 ms)...")
    controller.press(keyboard.Key.f8)
    time.sleep(0.07)
    controller.release(keyboard.Key.f8)
    time.sleep(0.2)

    assert len(events_captured) >= 3, "Deveria ter registrado o descarte"
    assert events_captured[2][0] == "discard"
    discard_time = events_captured[2][1]
    assert discard_time < 0.20
    print(f"  [SUCESSO] Cenário 2 validado: toque rápido de {discard_time*1000:.1f}ms descartado com precisão!")

    # Finalização limpa
    listener.stop()
    recorder.close()
    print("\n[✓] Todos os testes de integração do Push-To-Talk passaram com sucesso total!")


if __name__ == "__main__":
    run_integration_test()
