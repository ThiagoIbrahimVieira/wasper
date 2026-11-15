"""
Suíte de Testes Automatizados - Fase 4 (Inserção no Campo Ativo)
Valida simulação de Ctrl+V, integridade de Unicode, preservação do clipboard e de foco.
"""

import sys
import time
import ctypes
import unittest
import pyperclip
from paste_injector import PasteInjector

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


class TestPhase4PasteInjection(unittest.TestCase):
    def test_01_disabled_mode_bypasses_injection(self):
        """Quando desativado (--no-paste), não deve modificar clipboard nem disparar teclas."""
        pyperclip.copy("CLIPBOARD_INTACTO")
        injector = PasteInjector(enabled=False)
        res = injector.inject("Texto que não deve ser colado")
        self.assertTrue(res.success)
        self.assertEqual(pyperclip.paste(), "CLIPBOARD_INTACTO")
        self.assertLess(res.elapsed_ms, 5.0)

    def test_02_empty_text_handled_safely(self):
        """Texto vazio não deve disparar Ctrl+V nem gerar erros."""
        injector = PasteInjector(enabled=True)
        res = injector.inject("")
        self.assertTrue(res.success)
        self.assertEqual(res.text, "")

    def test_03_clipboard_restoration(self):
        """Verifica se o conteúdo anterior da área de transferência é rigorosamente restaurado."""
        original_content = f"Conteúdo Pré-Existente {time.time()}"
        pyperclip.copy(original_content)

        injector = PasteInjector(enabled=True, paste_delay=0.01, restore_delay=0.05)
        res = injector.inject("Texto transcrito para colar")

        self.assertTrue(res.success)
        self.assertTrue(res.clipboard_restored)
        restored = pyperclip.paste()
        self.assertEqual(restored, original_content, "A área de transferência original deve ser restaurada")

    def test_04_unicode_and_special_characters_integrity(self):
        """Valida se acentos, cedilha, pontuação e emojis são copiados sem corrupção."""
        unicode_sample = "Atenção: áéíóú, João & Maria! 🚀\nLinha 2 com ç e ~."
        injector = PasteInjector(enabled=True, paste_delay=0.02, restore_delay=0.05)
        res = injector.inject(unicode_sample)

        self.assertTrue(res.success)
        self.assertEqual(res.text, unicode_sample)

    def test_05_foreground_window_focus_is_preserved(self):
        """Valida que o processo de injeção não altera nem rouba o foco da janela ativa no Windows."""
        user32 = ctypes.windll.user32
        hwnd_before = user32.GetForegroundWindow()

        injector = PasteInjector(enabled=True, paste_delay=0.01, restore_delay=0.05)
        injector.inject("Teste de preservação de foco")

        hwnd_after = user32.GetForegroundWindow()
        self.assertEqual(hwnd_before, hwnd_after, "O identificador da janela em foco (HWND) não deve ser alterado")


if __name__ == "__main__":
    unittest.main()
