import time
import numpy as np
import sounddevice as sd
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class AudioRecordingResult:
    """Dados resultantes de uma captura de áudio Push-to-Talk."""
    audio_data: np.ndarray       # Amostras em float32 1D normalizadas (-1.0 a 1.0)
    duration_seconds: float      # Duração real em segundos
    sample_rate: int             # Taxa de amostragem (padrão 16000 Hz)
    total_samples: int           # Quantidade total de amostras
    rms_volume: float            # Nível RMS de energia do áudio
    peak_amplitude: float        # Amplitude máxima registrada (0.0 a 1.0)


class AudioRecorder:
    """
    Gerencia a captura contínua de áudio do microfone em buffer de memória.
    Configurado especificamente para o formato esperado pelo Whisper (16kHz, mono, float32).
    """

    def __init__(self, sample_rate: int = 16000, device: Optional[int] = None):
        self.sample_rate = sample_rate
        self.device = device
        self.is_recording = False
        self._frames = []
        self._stream: Optional[sd.InputStream] = None
        self._start_time = 0.0

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback executado pela thread de áudio do PortAudio a cada bloco."""
        if status:
            pass  # Overflow ou underflow silencioso
        if self.is_recording:
            self._frames.append(indata.copy())

    def start_stream(self):
        """Inicializa e mantém o stream do microfone aberto em segundo plano."""
        if self._stream is None or not self._stream.active:
            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    device=self.device,
                    blocksize=1024,
                    callback=self._audio_callback
                )
                self._stream.start()
            except Exception as e:
                raise RuntimeError(f"Falha ao abrir dispositivo de microfone: {e}")

    def start_recording(self) -> bool:
        """Inicia a acumulação de amostras de áudio em memória."""
        if self.is_recording:
            return False  # Já está gravando, evita duplicações
        
        self.start_stream()
        self._frames = []
        self._start_time = time.perf_counter()
        self.is_recording = True
        return True

    def get_current_audio_snapshot(self) -> Optional[np.ndarray]:
        """
        Retorna uma cópia do áudio acumulado até o momento sem interromper a gravação.
        Usado para o preview de streaming em tempo real na pílula flutuante (Passo 1).
        """
        if not self.is_recording:
            return None
        try:
            frames_copy = list(self._frames)
            if not frames_copy:
                return None
            return np.concatenate(frames_copy, axis=0).squeeze().copy()
        except Exception:
            return None

    def stop_recording(self) -> Optional[AudioRecordingResult]:
        """
        Encerra a gravação e retorna os dados acumulados em memória.
        Retorna None se nenhuma gravação estiver ativa.
        """
        if not self.is_recording:
            return None

        self.is_recording = False
        duration = time.perf_counter() - self._start_time

        if not self._frames:
            return AudioRecordingResult(
                audio_data=np.array([], dtype=np.float32),
                duration_seconds=duration,
                sample_rate=self.sample_rate,
                total_samples=0,
                rms_volume=0.0,
                peak_amplitude=0.0
            )

        # Concatena os blocos de áudio em um array 1D contíguo
        full_audio = np.concatenate(self._frames, axis=0).squeeze()
        self._frames = []

        total_samples = len(full_audio)
        peak = float(np.max(np.abs(full_audio))) if total_samples > 0 else 0.0
        rms = float(np.sqrt(np.mean(full_audio ** 2))) if total_samples > 0 else 0.0

        return AudioRecordingResult(
            audio_data=full_audio,
            duration_seconds=duration,
            sample_rate=self.sample_rate,
            total_samples=total_samples,
            rms_volume=rms,
            peak_amplitude=peak
        )

    def close(self):
        """Fecha o stream e libera todos os recursos de áudio."""
        self.is_recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            finally:
                self._stream = None
        self._frames = []
