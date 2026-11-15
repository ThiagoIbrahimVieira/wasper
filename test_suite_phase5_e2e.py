"""
Suíte de Testes Automatizados - Fase 5 (Integração e Robustez Ponta a Ponta)
Valida todo o pipeline encadeado: Áudio -> Whisper -> Ollama -> Paste Injector.
"""

import os
import sys
import time
import unittest
import numpy as np
import pyperclip

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from transcriber import WhisperTranscriber
from refiner import OllamaRefiner
from paste_injector import PasteInjector
from audio_utils import load_audio_from_file_or_bytes


class TestPhase5EndToEndIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n[Fase 5 E2E] Carregando modelos para testes ponta a ponta...")
        cls.transcriber = WhisperTranscriber(model_name="base", device="auto", language="pt")
        cls.refiner = OllamaRefiner(model="qwen3.5:2b", timeout=12.0, enabled=True)
        cls.injector = PasteInjector(enabled=True, paste_delay=0.01, restore_delay=0.05)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.audio_curto = load_audio_from_file_or_bytes(os.path.join(base_dir, "teste_curto.mp3"))

    def test_01_e2e_fast_mode_whisper_and_paste(self):
        """Pipeline rápido: Áudio em RAM -> Whisper (GPU) -> PasteInjector (sem Ollama)."""
        original_clip = f"CLIPBOARD_ANTES_DO_TESTE_{time.time()}"
        pyperclip.copy(original_clip)

        t_release = time.perf_counter()

        # 1. Transcreve
        trans = self.transcriber.transcribe(self.audio_curto, sample_rate=16000)
        self.assertTrue(len(trans.text) > 0)

        # 2. Injeta
        paste_res = self.injector.inject(trans.text)
        total_latency_ms = (time.perf_counter() - t_release) * 1000

        print(f"\n[E2E Modo Rápido] Texto: '{trans.text}'")
        print(f"    ├─ Latência Whisper: {trans.inference_time_seconds * 1000:.1f} ms")
        print(f"    ├─ Injeção Clipboard: {paste_res.elapsed_ms:.1f} ms")
        print(f"    └─ Latência Ponta a Ponta: {total_latency_ms:.1f} ms")

        self.assertTrue(paste_res.success)
        self.assertTrue(paste_res.clipboard_restored)
        self.assertEqual(pyperclip.paste(), original_clip)
        self.assertLess(total_latency_ms, 2500.0, "Modo rápido deve concluir em menos de 2.5s na GTX 1650")

    def test_02_e2e_refined_mode_whisper_ollama_paste(self):
        """Pipeline completo: Áudio em RAM -> Whisper -> Ollama Refiner -> PasteInjector."""
        original_clip = f"CLIPBOARD_ANTES_REFINADO_{time.time()}"
        pyperclip.copy(original_clip)

        t_release = time.perf_counter()

        # 1. Whisper
        trans = self.transcriber.transcribe(self.audio_curto, sample_rate=16000)

        # 2. Ollama
        ref_res = self.refiner.refine(trans.text)

        # 3. Paste
        paste_res = self.injector.inject(ref_res.text)

        total_latency_ms = (time.perf_counter() - t_release) * 1000

        print(f"\n[E2E Modo Refinado]")
        print(f"    ├─ Whisper Bruto:    '{trans.text}'")
        print(f"    ├─ Ollama Refinado:  '{ref_res.text}'")
        print(f"    ├─ Latência Whisper: {trans.inference_time_seconds * 1000:.1f} ms")
        print(f"    ├─ Latência Ollama:  {ref_res.elapsed_ms:.1f} ms (Fallback: {ref_res.fallback_used})")
        print(f"    └─ Latência Total:   {total_latency_ms:.1f} ms")

        self.assertTrue(paste_res.success)
        self.assertTrue(paste_res.clipboard_restored)
        self.assertEqual(pyperclip.paste(), original_clip)

    def test_03_silence_rejection(self):
        """Áudio de silêncio (amplitude zero) não deve gerar texto ou falhas no pipeline."""
        silence = np.zeros(16000, dtype=np.float32)  # 1 segundo de puro silêncio
        trans = self.transcriber.transcribe(silence, sample_rate=16000)
        # Whisper com VAD ativado deve descartar ou retornar texto vazio
        text = trans.text.strip()
        self.assertEqual(text, "", "Silêncio puro não deve produzir transcrição")

    def test_04_fallback_resilience_when_ollama_down(self):
        """Garante que se o Ollama estiver fora do ar, o pipeline usa o texto do Whisper sem travar."""
        broken_refiner = OllamaRefiner(endpoint="http://localhost:9999", enabled=True, timeout=0.5)
        raw_text = "texto que precisa passar mesmo sem ollama"
        ref_res = broken_refiner.refine(raw_text)
        self.assertTrue(ref_res.fallback_used)
        self.assertEqual(ref_res.text, raw_text)

        paste_res = self.injector.inject(ref_res.text)
        self.assertTrue(paste_res.success)


if __name__ == "__main__":
    unittest.main()
