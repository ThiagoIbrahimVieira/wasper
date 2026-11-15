import time
import unittest
import numpy as np
from pynput import keyboard
from audio_recorder import AudioRecorder, AudioRecordingResult
from hotkey_manager import PushToTalkListener


class TestAudioRecorder(unittest.TestCase):
    """Testes automatizados do gravador de áudio em memória."""

    def setUp(self):
        self.recorder = AudioRecorder(sample_rate=16000)

    def tearDown(self):
        self.recorder.close()

    def test_01_recorder_initialization(self):
        """Verifica se o gravador inicializa com os parâmetros corretos para o Whisper."""
        self.assertEqual(self.recorder.sample_rate, 16000)
        self.assertFalse(self.recorder.is_recording)
        self.assertEqual(len(self.recorder._frames), 0)

    def test_02_real_audio_capture_samples_and_duration(self):
        """Testa gravação real de ~0.5s e valida coerência de amostras e tipo float32."""
        started = self.recorder.start_recording()
        self.assertTrue(started)
        self.assertTrue(self.recorder.is_recording)

        time.sleep(0.5)

        result = self.recorder.stop_recording()
        self.assertIsNotNone(result)
        self.assertIsInstance(result, AudioRecordingResult)
        self.assertFalse(self.recorder.is_recording)

        # Validações estruturais e numéricas
        self.assertEqual(result.sample_rate, 16000)
        self.assertGreaterEqual(result.duration_seconds, 0.45)
        self.assertLessEqual(result.duration_seconds, 0.70)

        # Total de amostras deve ser coerente: duration * 16000 (com margem de buffer)
        expected_min_samples = int(0.40 * 16000)
        self.assertGreater(result.total_samples, expected_min_samples)
        self.assertEqual(len(result.audio_data), result.total_samples)

        # Formato esperado pelo Whisper
        self.assertEqual(result.audio_data.dtype, np.float32)
        self.assertEqual(result.audio_data.ndim, 1)

    def test_03_repeated_recordings_stability(self):
        """Executa 4 gravações consecutivas para provar ausência de vazamento ou travamento."""
        for i in range(4):
            self.assertTrue(self.recorder.start_recording())
            time.sleep(0.25)
            res = self.recorder.stop_recording()
            self.assertIsNotNone(res)
            self.assertGreater(res.total_samples, 3000)
            self.assertEqual(len(self.recorder._frames), 0)

    def test_04_double_start_is_safely_ignored(self):
        """Verifica que chamar start_recording repetidamente não reinicia nem corrompe."""
        self.assertTrue(self.recorder.start_recording())
        # Segunda chamada deve retornar False (já gravando)
        self.assertFalse(self.recorder.start_recording())
        self.recorder.stop_recording()


class TestHotkeyListener(unittest.TestCase):
    """Testes automatizados da lógica de gatilho Push-to-Talk e debounce."""

    def test_01_debounce_discards_short_press(self):
        """Valida que toques rápidos (< 200 ms) são descartados."""
        discards = []
        releases = []

        listener = PushToTalkListener(
            hotkey_name="f8",
            debounce_seconds=0.20,
            on_discard=lambda d: discards.append(d),
            on_release_stop=lambda d: releases.append(d)
        )

        f8_key = keyboard.Key.f8

        # Simula toque de 80ms
        listener._on_press(f8_key)
        time.sleep(0.08)
        listener._on_release(f8_key)

        self.assertEqual(len(discards), 1)
        self.assertEqual(len(releases), 0)
        self.assertLess(discards[0], 0.20)
        self.assertFalse(listener.is_key_down)

    def test_02_valid_press_triggers_stop_callback(self):
        """Valida que toques sustentados (>= 200 ms) são aceitos."""
        starts = []
        releases = []
        discards = []

        listener = PushToTalkListener(
            hotkey_name="f8",
            debounce_seconds=0.20,
            on_press_start=lambda: starts.append(1),
            on_release_stop=lambda d: releases.append(d),
            on_discard=lambda d: discards.append(d)
        )

        f8_key = keyboard.Key.f8

        # Simula pressão sustentada de 250ms
        listener._on_press(f8_key)
        self.assertEqual(len(starts), 1)
        self.assertTrue(listener.is_key_down)

        time.sleep(0.25)
        listener._on_release(f8_key)

        self.assertEqual(len(releases), 1)
        self.assertEqual(len(discards), 0)
        self.assertGreaterEqual(releases[0], 0.20)
        self.assertFalse(listener.is_key_down)

    def test_03_windows_key_repeat_suppression(self):
        """Garante que o auto-repeat do Windows não dispara múltiplos inícios de gravação."""
        starts = []

        listener = PushToTalkListener(
            hotkey_name="f8",
            debounce_seconds=0.20,
            on_press_start=lambda: starts.append(1)
        )

        f8_key = keyboard.Key.f8

        # Simula 5 eventos repetidos de keyDown enviados pelo Windows
        listener._on_press(f8_key)
        listener._on_press(f8_key)
        listener._on_press(f8_key)
        listener._on_press(f8_key)
        listener._on_press(f8_key)

        # Deve disparar apenas 1 vez!
        self.assertEqual(len(starts), 1)

        listener._on_release(f8_key)
        self.assertFalse(listener.is_key_down)


if __name__ == "__main__":
    unittest.main(verbosity=2)
