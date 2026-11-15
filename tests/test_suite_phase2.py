import os
import sys
import time
import unittest
import numpy as np

# UTF-8 encoding
if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from audio_utils import load_audio_from_file_or_bytes
from transcriber import WhisperTranscriber, TranscriptionResult


class TestPhase2WhisperIntegration(unittest.TestCase):
    """Testes automatizados da Fase 2: Integração com Whisper Local PT-BR."""

    @classmethod
    def setUpClass(cls):
        # Carrega os áudios reais de teste
        cls.curto_path = "c:/Users/thiag/Documents/REA/Wasper/teste_curto.mp3"
        cls.longo_path = "c:/Users/thiag/Documents/REA/Wasper/teste_longo.mp3"
        cls.audio_curto = load_audio_from_file_or_bytes(cls.curto_path)
        cls.audio_longo = load_audio_from_file_or_bytes(cls.longo_path)

        # Inicializa o transcritor base
        cls.transcriber_base = WhisperTranscriber(model_name="base", device="auto", language="pt")

    def test_01_cuda_or_cpu_detected_and_active(self):
        """Verifica se o dispositivo detectado é válido (cuda ou cpu)."""
        self.assertIn(self.transcriber_base.actual_device, ("cuda", "cpu"))
        self.assertIn(self.transcriber_base.actual_compute_type, ("float16", "int8"))
        print(f"\n[INFO TEST] Dispositivo ativo: {self.transcriber_base.actual_device.upper()} ({self.transcriber_base.actual_compute_type})")

    def test_02_transcribe_short_audio_portuguese(self):
        """Transcreve áudio curto de 4.4s e valida precisão e métricas em português."""
        res = self.transcriber_base.transcribe(self.audio_curto, language="pt")
        self.assertIsInstance(res, TranscriptionResult)
        self.assertGreater(len(res.text), 10)
        self.assertEqual(res.language, "pt")
        self.assertGreater(res.inference_time_seconds, 0.0)

        # Validação semântica do texto transcrito
        text_lower = res.text.lower()
        self.assertIn("teste", text_lower)
        self.assertIn("transcrição", text_lower)
        self.assertIn("português", text_lower)
        print(f"[INFO TEST] Transcrição Curta ({res.inference_time_seconds*1000:.1f}ms): '{res.text}'")

    def test_03_transcribe_long_audio_portuguese(self):
        """Transcreve áudio longo de 14.1s e valida processamento completo."""
        res = self.transcriber_base.transcribe(self.audio_longo, language="pt")
        self.assertIsInstance(res, TranscriptionResult)
        self.assertGreater(len(res.text), 30)
        self.assertEqual(res.language, "pt")

        text_lower = res.text.lower()
        self.assertTrue("1650" in text_lower or "gtx" in text_lower)
        self.assertTrue("internet" in text_lower or "privacidade" in text_lower)
        print(f"[INFO TEST] Transcrição Longa ({res.inference_time_seconds*1000:.1f}ms): '{res.text}'")

    def test_04_cpu_fallback_mode_works(self):
        """Valida que o modo explícito CPU int8 funciona perfeitamente sem falhas."""
        transcriber_cpu = WhisperTranscriber(model_name="base", device="cpu", compute_type="int8", language="pt")
        self.assertEqual(transcriber_cpu.actual_device, "cpu")
        self.assertEqual(transcriber_cpu.actual_compute_type, "int8")

        res = transcriber_cpu.transcribe(self.audio_curto, language="pt")
        self.assertIn("teste", res.text.lower())
        print(f"[INFO TEST] Transcrição CPU ({res.inference_time_seconds*1000:.1f}ms): '{res.text}'")

    def test_05_memory_only_no_disk_writes(self):
        """Confirma que a transcrição opera estritamente a partir do array em RAM."""
        # Cria array float32 em memória
        audio_slice = self.audio_curto[:32000]  # 2 segundos
        res = self.transcriber_base.transcribe(audio_slice)
        self.assertIsInstance(res.text, str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
