"""
Wasper - Módulo de Inserção no Campo Ativo (Fase 4)
Injeta o texto transcrito diretamente no campo focado simulando Ctrl+V,
preservando o conteúdo anterior da área de transferência.
"""

import sys
import time
import ctypes
from dataclasses import dataclass
from typing import Optional
import pyperclip

# Constantes Win32 para simulação de teclado
VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002


@dataclass
class PasteResult:
    success: bool
    text: str
    elapsed_ms: float
    clipboard_restored: bool
    error: Optional[str] = None


class PasteInjector:
    """Injetor de texto via simulação de área de transferência e Ctrl+V no Windows."""

    def __init__(
        self,
        enabled: bool = True,
        paste_delay: float = 0.03,
        restore_delay: float = 0.12,
    ):
        self.enabled = enabled
        self.paste_delay = paste_delay
        self.restore_delay = restore_delay
        self.is_windows = sys.platform == "win32"

    def _simulate_paste_keystrokes(self):
        """Dispara a sequência Ctrl + V usando a API nativa do Windows (keybd_event)."""
        if not self.is_windows:
            return

        user32 = ctypes.windll.user32
        # Ctrl Down
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        # V Down
        user32.keybd_event(VK_V, 0, 0, 0)
        # V Up
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        # Ctrl Up
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    def inject(self, text: str) -> PasteResult:
        """
        Copia o texto para a área de transferência, simula o Ctrl+V e restaura
        o conteúdo anterior da área de transferência após breve intervalo.
        """
        if not text:
            return PasteResult(
                success=True,
                text="",
                elapsed_ms=0.0,
                clipboard_restored=True,
            )

        if not self.enabled:
            return PasteResult(
                success=True,
                text=text,
                elapsed_ms=0.0,
                clipboard_restored=True,
                error="Injeção desativada (--no-paste)",
            )

        t0 = time.perf_counter()
        previous_clipboard = None
        has_previous_text = False

        # 1. Salva o conteúdo anterior da área de transferência
        try:
            previous_clipboard = pyperclip.paste()
            has_previous_text = True
        except Exception:
            # Caso a área de transferência contenha imagem ou dado não-texto
            has_previous_text = False

        try:
            # 2. Copia o novo texto
            pyperclip.copy(text)
            if self.paste_delay > 0:
                time.sleep(self.paste_delay)

            # 3. Simula Ctrl+V
            self._simulate_paste_keystrokes()

            # 4. Aguarda a aplicação em foco processar o evento de colar
            if self.restore_delay > 0:
                time.sleep(self.restore_delay)

            # 5. Restaura o conteúdo original da área de transferência
            restored = False
            if has_previous_text and previous_clipboard is not None:
                try:
                    pyperclip.copy(previous_clipboard)
                    restored = True
                except Exception:
                    restored = False

            elapsed_ms = (time.perf_counter() - t0) * 1000
            return PasteResult(
                success=True,
                text=text,
                elapsed_ms=elapsed_ms,
                clipboard_restored=restored,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            # Tenta restaurar em caso de erro
            if has_previous_text and previous_clipboard is not None:
                try:
                    pyperclip.copy(previous_clipboard)
                except Exception:
                    pass
            return PasteResult(
                success=False,
                text=text,
                elapsed_ms=elapsed_ms,
                clipboard_restored=False,
                error=str(e),
            )
