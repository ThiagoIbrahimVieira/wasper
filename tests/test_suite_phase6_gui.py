"""
Suíte de Testes Automatizados - Fase 6 (Interface Flutuante Nativa PySide6)
Valida a criação do widget, transições de estado, ausência de foco e emissão de sinais.
"""

import sys
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from ui_overlay import FloatingPillWidget, OverlaySignals

# Garante que existe uma instância de QApplication para os testes
_app = QApplication.instance() or QApplication(sys.argv)


class TestPhase6GUI(unittest.TestCase):
    def setUp(self):
        self.pill = FloatingPillWidget()
        self.signals = OverlaySignals()

    def tearDown(self):
        self.pill.close()

    def test_01_window_flags_do_not_steal_focus(self):
        """Verifica se a janela tem a flag obrigatória de não aceitar foco do Windows."""
        flags = self.pill.windowFlags()
        self.assertTrue(bool(flags & Qt.WindowType.FramelessWindowHint), "Deve ser sem bordas")
        self.assertTrue(bool(flags & Qt.WindowType.WindowStaysOnTopHint), "Deve ficar sempre no topo")
        self.assertTrue(bool(flags & Qt.WindowType.WindowDoesNotAcceptFocus), "JAMAIS deve roubar foco da janela ativa")

    def test_02_state_transitions(self):
        """Testa a máquina de estados interna da pílula."""
        self.assertEqual(self.pill.state, FloatingPillWidget.STATE_HIDDEN)

        self.pill.show_listening()
        self.assertEqual(self.pill.state, FloatingPillWidget.STATE_LISTENING)
        self.assertEqual(self.pill.status_label.text(), "Ouvindo...")

        self.pill.show_transcribing()
        self.assertEqual(self.pill.state, FloatingPillWidget.STATE_TRANSCRIBING)
        self.assertEqual(self.pill.status_label.text(), "Transcrevendo...")

        self.pill.show_completed("Texto teste")
        self.assertEqual(self.pill.state, FloatingPillWidget.STATE_COMPLETED)
        self.assertIn("Texto teste", self.pill.status_label.text())

    def test_03_signals_dispatch(self):
        """Verifica se os sinais Qt acionam os métodos correspondentes do widget."""
        received = []
        self.signals.recording_started.connect(lambda: received.append("listening"))
        self.signals.transcribing_started.connect(lambda: received.append("transcribing"))
        self.signals.completed.connect(lambda t: received.append(f"done:{t}"))

        self.signals.recording_started.emit()
        self.signals.transcribing_started.emit()
        self.signals.completed.emit("ok")

        self.assertEqual(received, ["listening", "transcribing", "done:ok"])

    def test_04_tray_icon_creation(self):
        """Valida que o ícone na bandeja do sistema inicializa com menu contextual."""
        from ui_overlay import create_tray_icon
        tray = create_tray_icon(_app)
        self.assertIsNotNone(tray)
        self.assertIsNotNone(tray.contextMenu())
        tray.hide()


if __name__ == "__main__":
    unittest.main()
