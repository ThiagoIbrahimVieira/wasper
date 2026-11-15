"""
WASPER — Ditado por Voz Local Push-To-Talk
Reprodução fiel e 100% offline do fluxo do Wispr Flow investigado via REA.
Integrando: Captura RAM + Whisper GPU + Refinador Ollama + Injetor Clipboard + Pílula Flutuante Liquid Glass.
"""

import os
import sys
import io
import argparse
import threading
import time
import wave
import winsound
import numpy as np

# Garante que o diretório do projeto está no sys.path mesmo se iniciado de outro local
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
elif hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")
elif hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

def log_step(msg):
    try:
        with open(os.path.join(APP_DIR, "wasper_boot.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


log_step("Importando audio_recorder")
from audio_recorder import AudioRecorder, AudioRecordingResult
log_step("Importando hotkey_manager")
from hotkey_manager import PushToTalkListener
log_step("Importando transcriber")
from transcriber import WhisperTranscriber, TranscriptionResult
log_step("Importando refiner")
from refiner import OllamaRefiner, RefinementResult
log_step("Importando paste_injector")
from paste_injector import PasteInjector, PasteResult
log_step("Importando text_cleaner")
from text_cleaner import clean_speech_disfluencies
log_step("Todos os módulos base importados")


def play_cue(sound_type: str):
    """Emite feedback sonoro nativo do Windows (similar aos chimes do Wispr Flow)."""
    try:
        if sound_type == "start":
            winsound.Beep(880, 70)   # Tom agudo curto (A5)
        elif sound_type == "stop":
            winsound.Beep(659, 90)   # Tom médio curto (E5)
        elif sound_type == "success":
            winsound.Beep(1046, 80)  # Tom agudo de conclusão (C6)
        elif sound_type == "discard":
            winsound.Beep(440, 50)   # Tom baixo indicando descarte rápido
        elif sound_type == "silent":
            winsound.Beep(523, 60)   # Tom indicando silêncio
    except Exception:
        pass


def save_wav_file(filename: str, audio_data: np.ndarray, sample_rate: int = 16000):
    """Salva áudio float32 em arquivo WAV PCM 16-bit para depuração opcional."""
    clamped = np.clip(audio_data, -1.0, 1.0)
    int16_data = (clamped * 32767.0).astype(np.int16)
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int16_data.tobytes())


def main():
    log_step("Entrou em def main()")
    parser = argparse.ArgumentParser(description="WASPER — Ditado por Voz Local Push-To-Talk")
    parser.add_argument("--hotkey", type=str, default=None, help="Tecla ou botão do mouse Push-to-Talk (padrão: f8 ou mouse_x1/mouse_x2)")
    parser.add_argument("--set-hotkey", type=str, default=None, help="Salva o atalho/botão permanentemente no wasper_config.json")
    parser.add_argument("--model", type=str, default=None, choices=["base", "small", "medium", "large-v3-turbo", "large-v3"], help="Modelo Whisper local")
    parser.add_argument("--set-model", type=str, default=None, choices=["base", "small", "medium", "large-v3-turbo", "large-v3"], help="Salva o modelo padrão permanentemente no wasper_config.json")
    parser.add_argument("--device", type=str, default="auto", choices=["auto", "cuda", "cpu"], help="Dispositivo Whisper (padrão: auto)")
    parser.add_argument("--compute", type=str, default=None, help="Precisão (float16 para cuda, int8 para cpu)")
    parser.add_argument("--debounce", type=float, default=0.20, help="Tempo mínimo em segundos contra toques acidentais (padrão: 0.20)")
    parser.add_argument("--refine", action="store_true", help="Ativa refinamento e pontuação por LLM local via Ollama")
    parser.add_argument("--ollama-model", type=str, default="qwen3.5:2b", help="Modelo Ollama para refinamento (padrão: qwen3.5:2b)")
    parser.add_argument("--ollama-timeout", type=float, default=5.0, help="Timeout em segundos para o Ollama (padrão: 5.0)")
    parser.add_argument("--no-paste", action="store_true", help="Desativa colagem automática (modo somente terminal)")
    parser.add_argument("--paste-delay", type=float, default=0.03, help="Intervalo pré-colagem em segundos (padrão: 0.03)")
    parser.add_argument("--restore-delay", type=float, default=0.12, help="Intervalo de restauração do clipboard (padrão: 0.12)")
    parser.add_argument("--no-gui", action="store_true", help="Desativa a pílula flutuante (modo console puro)")
    parser.add_argument("--mic", type=int, default=None, help="Índice do microfone de entrada (veja com --list-mics)")
    parser.add_argument("--set-mic", type=int, default=None, help="Salva o índice do microfone padrão de forma permanente")
    parser.add_argument("--list-mics", action="store_true", help="Lista todos os microfones disponíveis no sistema e sai")
    parser.add_argument("--save-test-wav", action="store_true", help="Salva a última gravação em gravacao_teste.wav")
    args = parser.parse_args()

    import json
    CONFIG_FILE = os.path.join(APP_DIR, "wasper_config.json")
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception:
            config = {}

    if args.set_mic is not None:
        import sounddevice as sd
        config["mic"] = args.set_mic
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        dev_info = sd.query_devices(args.set_mic)
        print(f"\n[✓] Microfone [{args.set_mic}] '{dev_info['name']}' salvo permanentemente no wasper_config.json!\n")
        sys.exit(0)

    if args.set_model is not None:
        config["model"] = args.set_model
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"\n[✓] Modelo Whisper '{args.set_model}' salvo permanentemente no wasper_config.json!\n")
        sys.exit(0)

    if args.set_hotkey is not None:
        config["hotkey"] = args.set_hotkey.lower().strip()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print(f"\n[✓] Atalho Push-to-Talk '{args.set_hotkey}' salvo permanentemente no wasper_config.json!\n")
        sys.exit(0)

    if args.list_mics:
        import sounddevice as sd
        print("\n=== MICROFONES DISPONÍVEIS NO SISTEMA ===")
        default_in = sd.default.device[0]
        saved_mic = config.get("mic", None)
        for idx, d in enumerate(sd.query_devices()):
            if d['max_input_channels'] > 0:
                tags = []
                if idx == default_in:
                    tags.append("PADRÃO WINDOWS")
                if idx == saved_mic:
                    tags.append("CONFIGURADO NO WASPER")
                tag_str = f" [{' | '.join(tags)}]" if tags else ""
                print(f"  [{idx}] {d['name']} (Taxa: {int(d['default_samplerate'])} Hz){tag_str}")
        print("\nPara definir seu microfone permanente, digite:")
        print("  python main.py --set-mic <NÚMERO>\n")
        sys.exit(0)

    active_mic = args.mic if args.mic is not None else config.get("mic", None)
    active_model = args.model if args.model is not None else config.get("model", "large-v3-turbo")
    active_hotkey = args.hotkey if args.hotkey is not None else config.get("hotkey", "f8")
    log_step(f"Args parsed. active_mic={active_mic}, active_model={active_model}, active_hotkey={active_hotkey}")

    # Trava de instância única nativa para evitar que múltiplas instâncias briguem por microfone e hooks
    import msvcrt
    lock_path = os.path.join(APP_DIR, "wasper.lock")
    try:
        lock_file = open(lock_path, "w")
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except (OSError, IOError):
        print("\n[!] Outra instância do Wasper já está em execução. Encerrando esta para evitar conflitos.\n")
        log_step("Instância duplicada detectada. Encerrando.")
        sys.exit(0)

    print("=" * 72)
    print("  WASPER — Ditado por Voz Push-To-Talk 100% Local (Whisper + Ollama + GUI)")
    print("  Engenharia Reversa Clean-Room do Wispr Flow via REA")
    print("=" * 72)

    # 1. Carrega o Whisper ASR
    print(f"\n[1/4] Inicializando Whisper '{active_model}' (Dispositivo: {args.device})...")
    t0_whisper = time.perf_counter()
    try:
        transcriber = WhisperTranscriber(
            model_name=active_model,
            device=args.device,
            compute_type=args.compute,
            language="pt",
        )
        load_ms = (time.perf_counter() - t0_whisper) * 1000
        print(f" [✓] Whisper pronto em {load_ms:.1f} ms!")
        print(f"     ├─ Dispositivo: {transcriber.actual_device.upper()} ({transcriber.actual_compute_type})")
        print(f"     └─ Idioma: Português (pt)")
        log_step(f"Whisper pronto ({transcriber.actual_device})")
    except Exception as e:
        log_step(f"Falha Whisper: {e}")
        print(f" [✗] Falha ao carregar Whisper: {e}")
        sys.exit(1)

    # 1.1 Carrega o Whisper ASR de Streaming Ao Vivo (tiny)
    preview_transcriber = None
    try:
        if active_model == "tiny":
            preview_transcriber = transcriber
        else:
            log_step("Inicializando Whisper Streaming tiny")
            print(f"\n[1.1/4] Inicializando Whisper Streaming 'tiny' (Preview ao Vivo)...")
            t0_tiny = time.perf_counter()
            preview_transcriber = WhisperTranscriber(
                model_name="tiny",
                device=args.device,
                compute_type=args.compute,
                language="pt",
            )
            load_tiny_ms = (time.perf_counter() - t0_tiny) * 1000
            print(f" [✓] Whisper Streaming 'tiny' pronto em {load_tiny_ms:.1f} ms!")
            # Warmup na GPU para compilar grafos CUDA e eliminar atraso na 1ª fala
            preview_transcriber.transcribe(np.zeros(4000, dtype=np.float32), beam_size=1, vad_filter=False, initial_prompt="")
            log_step("Whisper Streaming tiny pronto e aquecido na GPU")
    except Exception as e:
        log_step(f"Aviso streaming tiny: {e}")
        print(f" [!] Aviso: Streaming de preview desativado: {e}")
        preview_transcriber = None

    # 2. Inicializa o Refinador Ollama
    refiner = OllamaRefiner(
        model=args.ollama_model,
        timeout=args.ollama_timeout,
        enabled=args.refine,
    )
    if args.refine:
        print(f"\n[2/4] Verificando Ollama ('{args.ollama_model}')...")
        if refiner.is_available():
            print(f" [✓] Ollama conectado e modelo '{args.ollama_model}' verificado!")
        else:
            print(f" [!] AVISO: Ollama ou modelo '{args.ollama_model}' não encontrado no momento.")
            print(f"     O sistema funcionará normalmente usando a transcrição Whisper como fallback.")
    else:
        print(f"\n[2/4] Refinamento Ollama: DESATIVADO (Modo ultra-rápido ~580ms)")

    # 3. Inicializa o Injetor de Paste
    injector = PasteInjector(
        enabled=not args.no_paste,
        paste_delay=args.paste_delay,
        restore_delay=args.restore_delay,
    )
    paste_status = "ATIVADA (Ctrl+V com backup do clipboard)" if not args.no_paste else "DESATIVADA (--no-paste)"
    print(f"\n[3/4] Injeção no Campo Ativo: {paste_status}")

    # 4. Inicializa a Interface Gráfica Flutuante (PySide6)
    use_gui = not args.no_gui
    app = None
    pill = None
    signals = None

    tray = None
    if use_gui:
        try:
            from PySide6.QtWidgets import QApplication
            from ui_overlay import FloatingPillWidget, OverlaySignals, create_tray_icon

            app = QApplication.instance() or QApplication(sys.argv)
            app.setQuitOnLastWindowClosed(False)
            pill = FloatingPillWidget()
            tray = create_tray_icon(app, on_exit_callback=lambda: app.quit(), hotkey_str=active_hotkey.upper())
            signals = OverlaySignals()

            signals.recording_started.connect(pill.show_listening)
            signals.transcribing_started.connect(pill.show_transcribing)
            signals.completed.connect(pill.show_completed)
            signals.discarded.connect(pill.show_discarded)
            signals.partial_preview.connect(pill.show_partial_preview)
            print(f"\n[4/4] Interface Flutuante: ATIVADA (Pílula Liquid Glass + Ícone na Bandeja)")
            log_step("Interface GUI inicializada com sucesso")
        except Exception as e:
            log_step(f"Falha na interface GUI: {e}")
            print(f"\n[4/4] Interface Flutuante: Falha ao carregar ({e}). Rodando em modo console.")
            use_gui = False
    else:
        print(f"\n[4/4] Interface Flutuante: DESATIVADA (--no-gui)")

    # 5. Inicializa o Gravador de Microfone
    import sounddevice as sd
    target_dev_idx = active_mic if active_mic is not None else sd.default.device[0]
    dev_info = sd.query_devices(target_dev_idx)
    recorder = AudioRecorder(sample_rate=16000, device=active_mic)
    try:
        recorder.start_stream()
        log_step(f"Microfone [{target_dev_idx}] iniciado com sucesso")
        print(f" [✓] Microfone conectado: [{target_dev_idx}] {dev_info['name']} (16.000 Hz, Float32).")
        if any(v in dev_info['name'].lower() for v in ['voicemod', 'virtual', 'cable']):
            print(f"     ⚠️  ATENÇÃO: Você está usando um dispositivo virtual ({dev_info['name']}).")
            print(f"         Se o som falhar ou sair distorcido, use seu microfone físico com '--mic <NÚMERO>'.")
    except Exception as e:
        log_step(f"Falha no microfone [{target_dev_idx}]: {e}")
        print(f" [✗] Erro no microfone [{target_dev_idx}]: {e}")
        sys.exit(1)

    is_processing = False
    processing_lock = threading.Lock()

    def process_pipeline_async(audio_result: AudioRecordingResult, release_time: float):
        """Pipeline assíncrono: Transcrição -> Refinamento -> Injeção -> UI."""
        nonlocal is_processing
        with processing_lock:
            is_processing = True

        try:
            print(f"\n⏳ [PROCESSANDO...] Áudio capturado: {audio_result.duration_seconds:.2f}s", flush=True)

            # 1. Transcrição Whisper
            trans_result = transcriber.transcribe(
                audio_result.audio_data,
                sample_rate=audio_result.sample_rate,
                beam_size=1,
                vad_filter=True,
            )
            raw_text = trans_result.text.strip()
            whisper_ms = trans_result.inference_time_seconds * 1000

            # 2. Tratamento de silêncio ou fala inaudível
            if not raw_text:
                play_cue("silent")
                if signals:
                    signals.completed.emit("Silêncio...")
                print("⚠️  [SILÊNCIO] Nenhuma fala audível detectada. Nenhuma injeção realizada.\n")
                return

            # 3. Limpeza Rápida de Disfluências (Hesitações "ééé", gagueiras, mantendo 'né?' e tom natural)
            cleaned_text = clean_speech_disfluencies(raw_text)
            final_text = cleaned_text
            ollama_ms = 0.0
            fallback_used = False

            if args.refine:
                refine_res = refiner.refine(cleaned_text)
                final_text = refine_res.text
                ollama_ms = refine_res.elapsed_ms
                fallback_used = refine_res.fallback_used

            # 4. Injeção de Texto no Campo Ativo
            paste_res = injector.inject(final_text)
            paste_ms = paste_res.elapsed_ms

            total_latency_ms = (time.perf_counter() - release_time) * 1000

            play_cue("success")
            if signals:
                signals.completed.emit(final_text)

            # 5. Exibição da Telemetria Detalhada
            print("\r" + " " * 72 + "\r", end="", flush=True)
            print("=" * 72)
            if args.refine:
                print(f"💬 BRUTO (Whisper):    \"{raw_text}\"")
                print(f"✨ REFINADO (Ollama):   \"{final_text}\"")
            else:
                print(f"💬 TRANSCRIÇÃO:         \"{final_text}\"")

            print("-" * 72)
            print(f"⏱️  LATÊNCIA PONTA A PONTA: {total_latency_ms:.1f} ms")
            print(f"   ├─ Transcrição Whisper: {whisper_ms:.1f} ms ({trans_result.device_used.upper()} {trans_result.compute_type})")
            if args.refine:
                fb_tag = " (Fallback ativado)" if fallback_used else ""
                print(f"   ├─ Refinamento Ollama:  {ollama_ms:.1f} ms [{args.ollama_model}]{fb_tag}")
            print(f"   ├─ Injeção Clipboard:   {paste_ms:.1f} ms (Restaurado: {'Sim' if paste_res.clipboard_restored else 'Não'})")
            print(f"   └─ Duração do Áudio:    {audio_result.duration_seconds:.2f} s ({audio_result.total_samples:,} amostras)")
            print("=" * 72)

            if args.save_test_wav:
                save_wav_file("gravacao_teste.wav", audio_result.audio_data, audio_result.sample_rate)
                print(f"💾 Cópia de depuração salva em gravacao_teste.wav")

            print(f"\n[Pronto para o próximo ditado — Segure {active_hotkey.upper()}]...\n")

        except Exception as e:
            print(f"\n[ERRO NO PIPELINE]: {e}")
            if signals:
                signals.discarded.emit()
        finally:
            with processing_lock:
                is_processing = False

    preview_stop_event = threading.Event()
    preview_thread = None

    def _run_preview_loop():
        last_preview_text = ""
        while not preview_stop_event.is_set():
            if not recorder.is_recording:
                break
            snapshot = recorder.get_current_audio_snapshot()
            if snapshot is not None and len(snapshot) >= 4800:  # ~0.30s a 16kHz
                try:
                    # Pega no máximo os últimos 3.5s para manter a latência de preview cravada em ~100ms
                    chunk = snapshot[-56000:] if len(snapshot) > 56000 else snapshot
                    res = preview_transcriber.transcribe(
                        chunk,
                        beam_size=1,
                        vad_filter=False,
                        initial_prompt="",
                    )
                    text = res.text.strip()
                    if text and text != last_preview_text and not preview_stop_event.is_set():
                        last_preview_text = text
                        if signals:
                            signals.partial_preview.emit(text)
                except Exception:
                    pass
            # Intervalo ultra-rápido entre checagens (100ms)
            if preview_stop_event.wait(0.10):
                break

    def on_press():
        nonlocal preview_thread
        if is_processing:
            print("\r⚠️  [Aguarde] Pipeline anterior ainda em execução...", end="", flush=True)
            return
        started = recorder.start_recording()
        if started:
            play_cue("start")
            preview_stop_event.clear()
            if signals:
                signals.recording_started.emit()
            if preview_transcriber is not None and use_gui:
                preview_thread = threading.Thread(target=_run_preview_loop, daemon=True)
                preview_thread.start()
            print(f"\r\n🎙️  [GRAVANDO...] Segure {active_hotkey.upper()} e fale agora...", end="", flush=True)

    def on_release(duration: float):
        preview_stop_event.set()
        t_release = time.perf_counter()
        result = recorder.stop_recording()
        play_cue("stop")
        if signals:
            signals.transcribing_started.emit()
        print("\r" + " " * 72 + "\r", end="", flush=True)

        if result and result.total_samples > 0:
            t = threading.Thread(
                target=process_pipeline_async,
                args=(result, t_release),
                daemon=True,
            )
            t.start()
        else:
            if signals:
                signals.discarded.emit()
            print("[!] Gravação finalizada, mas nenhuma amostra foi capturada.\n")

    def on_discard(duration: float):
        preview_stop_event.set()
        recorder.stop_recording()
        play_cue("discard")
        if signals:
            signals.discarded.emit()
        print("\r" + " " * 72 + "\r", end="", flush=True)
        print(f"⚠️  [DESCARTADO] Toque rápido ({duration * 1000:.1f} ms < {args.debounce * 1000:.0f} ms) — Proteção anti-clique ativada.\n")

    listener = PushToTalkListener(
        hotkey_name=active_hotkey,
        debounce_seconds=args.debounce,
        on_press_start=on_press,
        on_release_stop=on_release,
        on_discard=on_discard,
    )

    listener.start()
    log_step(f"Listener iniciado para atalho '{active_hotkey}'")
    print(f"\n[✓] SISTEMA OPERACIONAL!")
    print(f"    👉 Segure [{active_hotkey.upper()}] para ditar, solte para colar automaticamente.")
    print(f"    👉 Pressione [Ctrl + C] para encerrar.\n")

    try:
        if use_gui and app:
            if pill:
                pill.show_startup(2500, hotkey_str=active_hotkey.upper())
                play_cue("success")
            log_step("Iniciando app.exec()")
            # Roda o loop de eventos Qt
            exit_code = app.exec()
            log_step(f"app.exec() finalizou com código {exit_code}")
            with open(os.path.join(APP_DIR, "wasper_exit.log"), "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] app.exec() retornou código {exit_code}\n")
        else:
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n[Encerrando Wasper...]")
    except Exception as e:
        import traceback
        with open(os.path.join(APP_DIR, "wasper_crash.log"), "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
    finally:
        with open(os.path.join(APP_DIR, "wasper_exit.log"), "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Entrou no bloco finally.\n")
        try:
            listener.stop()
        except Exception:
            pass
        try:
            recorder.close()
        except Exception:
            pass
        if pill:
            pill.close()
        if tray:
            tray.hide()
        try:
            if 'lock_file' in locals() and lock_file:
                lock_file.close()
                if os.path.exists(lock_path):
                    os.remove(lock_path)
        except Exception:
            pass
        print("[✓] Recursos liberados com sucesso. Até logo!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(os.path.join(APP_DIR, "wasper_fatal.log"), "a", encoding="utf-8") as f:
            f.write(f"FATAL ERROR:\n{traceback.format_exc()}\n")
