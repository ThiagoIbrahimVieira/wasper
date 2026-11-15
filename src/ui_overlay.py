"""
Wasper — Pílula Flutuante Nativa (Floating Pill Widget) & Bandeja do Sistema
Interface gráfica ultra-leve, sem bordas e translúcida (Liquid Glass) em PySide6.
Zero roubo de foco, zero Electron, consumo de ~18 MB de RAM.
"""

import sys
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPainterPath,
    QBrush,
    QPen,
    QFont,
    QPixmap,
    QIcon,
    QAction,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QHBoxLayout,
    QGraphicsDropShadowEffect,
    QSystemTrayIcon,
    QMenu,
)


class OverlaySignals(QObject):
    """Sinais Qt para comunicação thread-safe entre o pipeline de áudio e a UI."""
    recording_started = Signal()
    transcribing_started = Signal()
    completed = Signal(str)
    discarded = Signal()
    audio_level = Signal(float)
    partial_preview = Signal(str)


class FloatingPillWidget(QWidget):
    """Widget flutuante em formato de pílula (Liquid Glass) sem bordas e sem foco."""

    STATE_HIDDEN = 0
    STATE_LISTENING = 1
    STATE_TRANSCRIBING = 2
    STATE_COMPLETED = 3

    def __init__(self):
        super().__init__()
        self.state = self.STATE_HIDDEN
        self.audio_level = 0.0
        self.pulse_phase = 0.0

        # Configurações de janela: sem borda, sempre no topo, tipo tool (fora da taskbar), sem foco
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self.setFixedSize(220, 48)

        # Layout interno
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 18, 0)
        layout.setSpacing(12)

        # Indicador visual
        self.indicator_label = QLabel(self)
        self.indicator_label.setFixedSize(14, 14)

        # Texto de estado
        self.status_label = QLabel("Wasper", self)
        font = QFont("Segoe UI", 10, QFont.Weight.Medium)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #f4f4f5;")

        layout.addWidget(self.indicator_label)
        layout.addWidget(self.status_label)
        layout.addStretch()

        # Sombra exterior (desativada para prevenir crash nativo 0xc0000005 no Qt6Widgets com janela translúcida)
        # shadow = QGraphicsDropShadowEffect(self)
        # shadow.setBlurRadius(28)
        # shadow.setColor(QColor(0, 0, 0, 180))
        # shadow.setOffset(0, 6)
        # self.setGraphicsEffect(shadow)

        # Timer de animação de pulso
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(40)  # ~25 FPS
        self.anim_timer.timeout.connect(self._on_anim_tick)

        # Timer para ocultar após conclusão
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self._start_fade_out)

        # Animação de fade-out
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(220)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.fade_anim.finished.connect(self._on_fade_finished)

    def reposition_on_screen(self):
        """Centraliza a pílula horizontalmente na parte inferior da tela principal."""
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            x = geom.x() + (geom.width() - self.width()) // 2
            y = geom.y() + geom.height() - self.height() - 40
            self.move(x, y)

    def show_listening(self):
        """Ativa o estado de escuta (segurando atalho)."""
        self.state = self.STATE_LISTENING
        self.setFixedWidth(220)
        self.status_label.setText("Ouvindo...")
        self.status_label.setStyleSheet("color: #f4f4f5;")
        self.reposition_on_screen()
        self.fade_anim.stop()
        self.setWindowOpacity(1.0)
        self.anim_timer.start()
        self.show()
        self.update()

    def show_transcribing(self):
        """Ativa o estado de transcrição (soltou atalho)."""
        self.state = self.STATE_TRANSCRIBING
        self.status_label.setText("Refinando texto...")
        self.status_label.setStyleSheet("color: #38bdf8; font-weight: 500;")
        font_metrics = self.status_label.fontMetrics()
        target_width = max(220, min(360, font_metrics.horizontalAdvance("Refinando texto...") + 75))
        self.setFixedWidth(target_width)
        self.reposition_on_screen()
        self.update()

    def show_completed(self, text: str = ""):
        """Exibe confirmação de sucesso e programa fade-out."""
        self.state = self.STATE_COMPLETED
        display_text = "Pronto!" if not text else (text[:28] + "..." if len(text) > 28 else text)
        self.status_label.setText(display_text)
        self.status_label.setStyleSheet("color: #10b981; font-weight: 600;")
        font_metrics = self.status_label.fontMetrics()
        target_width = max(220, min(480, font_metrics.horizontalAdvance(display_text) + 75))
        self.setFixedWidth(target_width)
        self.reposition_on_screen()
        self.anim_timer.stop()
        self.update()
        self.hide_timer.start(750)

    def show_partial_preview(self, text: str):
        """Exibe palavras parciais ao vivo enquanto o usuário fala (Passo 1 do Streaming)."""
        if self.state == self.STATE_LISTENING:
            clean = text.strip()
            if not clean:
                return
            snippet = clean
            if len(snippet) > 42:
                snippet = "..." + snippet[-39:]
            self.status_label.setText(snippet)
            self.status_label.setStyleSheet("color: #f4f4f5; font-weight: 500;")

            # Expande a pílula dinamicamente para acomodar o texto falado
            font_metrics = self.status_label.fontMetrics()
            target_width = max(220, min(540, font_metrics.horizontalAdvance(snippet) + 80))
            if self.width() < target_width or abs(self.width() - target_width) > 12:
                self.setFixedWidth(target_width)
                self.reposition_on_screen()
            self.update()

    def show_startup(self, duration_ms: int = 2800, hotkey_str: str = "F8"):
        """Exibe a pílula de boas-vindas na inicialização com animação e fade-out automático."""
        self.state = self.STATE_COMPLETED
        title = f"Wasper Ativo • {hotkey_str}"
        self.status_label.setText(title)
        self.status_label.setStyleSheet("color: #10b981; font-weight: bold;")
        font_metrics = self.status_label.fontMetrics()
        self.setFixedWidth(max(220, font_metrics.horizontalAdvance(title) + 75))
        self.reposition_on_screen()
        self.fade_anim.stop()
        self.setWindowOpacity(1.0)
        self.show()
        self.update()
        self.hide_timer.start(duration_ms)

    def show_discarded(self):
        """Descarte rápido."""
        self.anim_timer.stop()
        self._start_fade_out()

    def _start_fade_out(self):
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_fade_finished(self):
        self.state = self.STATE_HIDDEN
        self.hide()
        self.setWindowOpacity(1.0)

    def _on_anim_tick(self):
        self.pulse_phase += 0.15
        if self.pulse_phase > 6.28:
            self.pulse_phase = 0.0
        self.update()

    def paintEvent(self, event):
        """Renderiza o fundo estilo Liquid Glass com cantos arredondados e borda translúcida."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        radius = rect.height() / 2.0
        path.addRoundedRect(rect, radius, radius)

        # Fundo Dark Minimalist translúcido (zinc-950 com 92% de opacidade)
        bg_color = QColor(24, 24, 27, 235)
        painter.fillPath(path, QBrush(bg_color))

        # Borda de vidro sutil (Liquid Glass)
        border_pen = QPen(QColor(255, 255, 255, 32), 1.2)
        painter.strokePath(path, border_pen)

        # Desenha o indicador visual
        cx = 28
        cy = rect.center().y()

        if self.state == self.STATE_LISTENING:
            import math
            pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0
            r_glow = 5.0 + (pulse * 2.5)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(16, 185, 129, int(60 + pulse * 60)))
            painter.drawEllipse(int(cx - r_glow - 2), int(cy - r_glow - 2), int((r_glow + 2) * 2), int((r_glow + 2) * 2))

            painter.setBrush(QColor(16, 185, 129))
            painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

        elif self.state == self.STATE_TRANSCRIBING:
            import math
            pulse = (math.sin(self.pulse_phase * 1.5) + 1.0) / 2.0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(56, 189, 248, int(80 + pulse * 80)))
            painter.drawEllipse(int(cx - 7), int(cy - 7), 14, 14)
            painter.setBrush(QColor(56, 189, 248))
            painter.drawEllipse(int(cx - 4), int(cy - 4), 8, 8)

        elif self.state == self.STATE_COMPLETED:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(16, 185, 129))
            painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)


def create_tray_icon(app: QApplication, on_exit_callback=None, hotkey_str: str = "F8") -> QSystemTrayIcon:
    """Cria o ícone na bandeja do sistema (perto do relógio do Windows) com menu de saída."""
    # Gera um ícone minimalista estilizado programaticamente (círculo esmeralda com ponto central)
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Fundo escuro com borda
    painter.setBrush(QColor(24, 24, 27))
    painter.setPen(QPen(QColor(255, 255, 255, 60), 1.5))
    painter.drawEllipse(2, 2, 28, 28)

    # Ponto verde esmeralda
    painter.setBrush(QColor(16, 185, 129))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(10, 10, 12, 12)
    painter.end()

    tray = QSystemTrayIcon(QIcon(pixmap), app)
    tray.setToolTip(f"Wasper — Ditado por Voz Push-to-Talk ({hotkey_str})")

    menu = QMenu()
    title_action = QAction(f"Wasper ({hotkey_str})", menu)
    title_action.setEnabled(False)
    menu.addAction(title_action)
    menu.addSeparator()

    exit_action = QAction("Sair do Wasper", menu)
    if on_exit_callback:
        exit_action.triggered.connect(on_exit_callback)
    else:
        exit_action.triggered.connect(app.quit)
    menu.addAction(exit_action)

    tray.setContextMenu(menu)
    tray.show()
    return tray


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pill = FloatingPillWidget()
    tray = create_tray_icon(app, app.quit)
    pill.show_listening()

    QTimer.singleShot(2000, pill.show_transcribing)
    QTimer.singleShot(4000, lambda: pill.show_completed("Olá mundo!"))
    QTimer.singleShot(5500, app.quit)

    sys.exit(app.exec())
