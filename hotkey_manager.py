"""
Wasper — Gerenciador de Atalhos Push-to-Talk (Teclado e Mouse)
Suporta teclas globais (F1-F12, modificadores) e botões do mouse (mouse_x1, mouse_x2, mouse_middle).
Com supressão de eventos Win32 nativos para evitar que o mouse 4/5 navegue páginas para trás no Windows ("Browser Back").
"""

import time
from typing import Callable, Optional, Union
from pynput import keyboard, mouse


class PushToTalkListener:
    """
    Monitora eventos globais de pressão e liberação de tecla ou botão de mouse.
    """

    MOUSE_BUTTON_MAP = {
        "mouse_x1": mouse.Button.x1,
        "mouse4": mouse.Button.x1,
        "x1": mouse.Button.x1,
        "mouse_x2": mouse.Button.x2,
        "mouse5": mouse.Button.x2,
        "x2": mouse.Button.x2,
        "mouse_middle": mouse.Button.middle,
        "mouse3": mouse.Button.middle,
        "middle": mouse.Button.middle,
    }

    KEYBOARD_MAP = {
        "f1": keyboard.Key.f1,
        "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3,
        "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5,
        "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7,
        "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9,
        "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11,
        "f12": keyboard.Key.f12,
        "pause": keyboard.Key.pause,
        "scroll_lock": keyboard.Key.scroll_lock,
        "ctrl_r": keyboard.Key.ctrl_r,
        "alt_r": keyboard.Key.alt_r,
    }

    # Constantes Win32 para mensagens de mouse WH_MOUSE_LL
    WM_MBUTTONDOWN = 0x0207
    WM_MBUTTONUP = 0x0208
    WM_XBUTTONDOWN = 0x020B
    WM_XBUTTONUP = 0x020C
    WM_NCXBUTTONDOWN = 0x00AB
    WM_NCXBUTTONUP = 0x00AC

    def __init__(
        self,
        hotkey_name: str = "f8",
        debounce_seconds: float = 0.20,
        on_press_start: Optional[Callable[[], None]] = None,
        on_release_stop: Optional[Callable[[float], None]] = None,
        on_discard: Optional[Callable[[float], None]] = None
    ):
        self.hotkey_name = hotkey_name.lower().strip()
        self.debounce_seconds = debounce_seconds
        self.on_press_start = on_press_start
        self.on_release_stop = on_release_stop
        self.on_discard = on_discard

        self.is_key_down = False
        self._press_timestamp = 0.0
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None

        self.is_mouse_hotkey = self.hotkey_name in self.MOUSE_BUTTON_MAP
        self._target_mouse_button = self.MOUSE_BUTTON_MAP.get(self.hotkey_name)
        self._target_key = self._resolve_target_key(self.hotkey_name)

    def _resolve_target_key(self, name: str) -> Union[keyboard.Key, keyboard.KeyCode]:
        return self.KEYBOARD_MAP.get(name, keyboard.KeyCode.from_char(name) if len(name) == 1 else keyboard.Key.f8)

    def _matches_keyboard(self, key) -> bool:
        if not self.is_mouse_hotkey:
            if key == self._target_key:
                return True
            if hasattr(key, "name") and key.name and key.name.lower() == self.hotkey_name:
                return True
            if hasattr(key, "char") and key.char and key.char.lower() == self.hotkey_name:
                return True
        # F8 sempre permanece ativo como atalho de backup
        if key == keyboard.Key.f8 or (hasattr(key, "name") and key.name == "f8"):
            return True
        return False

    def _mouse_win32_filter(self, msg, data) -> bool:
        """
        Filtro de mensagens de baixo nível do Windows (WH_MOUSE_LL).
        Ao interceptar o botão configurado (ex: Mouse X1 / Voltar), executa o handler e
        suprime o evento no Windows para evitar que o navegador ou janela navegue para trás!
        """
        if not self.is_mouse_hotkey:
            return True

        is_down = False
        is_up = False
        matched = False

        if self.hotkey_name in ("mouse_x1", "x1", "mouse4"):
            btn_idx = (data.mouseData >> 16) & 0xFFFF
            if btn_idx == 1:
                if msg in (self.WM_XBUTTONDOWN, self.WM_NCXBUTTONDOWN):
                    matched = True
                    is_down = True
                elif msg in (self.WM_XBUTTONUP, self.WM_NCXBUTTONUP):
                    matched = True
                    is_up = True
        elif self.hotkey_name in ("mouse_x2", "x2", "mouse5"):
            btn_idx = (data.mouseData >> 16) & 0xFFFF
            if btn_idx == 2:
                if msg in (self.WM_XBUTTONDOWN, self.WM_NCXBUTTONDOWN):
                    matched = True
                    is_down = True
                elif msg in (self.WM_XBUTTONUP, self.WM_NCXBUTTONUP):
                    matched = True
                    is_up = True
        elif self.hotkey_name in ("mouse_middle", "mouse3", "middle"):
            if msg == self.WM_MBUTTONDOWN:
                matched = True
                is_down = True
            elif msg == self.WM_MBUTTONUP:
                matched = True
                is_up = True

        if matched:
            if is_down:
                self._handle_press()
            elif is_up:
                self._handle_release()

            # Suprime o evento no Windows para evitar 'Voltar Página' ou 'Fechar Aba'
            if self._mouse_listener is not None:
                self._mouse_listener.suppress_event()
            return False

        return True

    def _handle_press(self):
        if self.is_key_down:
            return

        self.is_key_down = True
        self._press_timestamp = time.perf_counter()

        if self.on_press_start:
            try:
                self.on_press_start()
            except Exception as e:
                print(f"[PushToTalk] Erro no callback on_press_start: {e}")

    def _handle_release(self):
        if not self.is_key_down:
            return

        self.is_key_down = False
        duration = time.perf_counter() - self._press_timestamp

        if duration < self.debounce_seconds:
            if self.on_discard:
                try:
                    self.on_discard(duration)
                except Exception as e:
                    print(f"[PushToTalk] Erro no callback on_discard: {e}")
        else:
            if self.on_release_stop:
                try:
                    self.on_release_stop(duration)
                except Exception as e:
                    print(f"[PushToTalk] Erro no callback on_release_stop: {e}")

    def _on_key_press(self, key):
        if self._matches_keyboard(key):
            self._handle_press()

    def _on_key_release(self, key):
        if self._matches_keyboard(key):
            self._handle_release()

    def start(self):
        """Inicia os listeners de teclado e mouse."""
        if self._keyboard_listener is None or not self._keyboard_listener.is_alive():
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()

        if self.is_mouse_hotkey:
            if self._mouse_listener is None or not self._mouse_listener.is_alive():
                self._mouse_listener = mouse.Listener(
                    win32_event_filter=self._mouse_win32_filter
                )
                self._mouse_listener.start()

    def stop(self):
        """Para todos os listeners e libera os hooks do Windows."""
        self.is_key_down = False
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None
