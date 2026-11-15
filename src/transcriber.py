import os
import sys
import glob
import time
from dataclasses import dataclass
from typing import Optional, Tuple, List
import numpy as np


def ensure_cuda_dlls():
    """Registra os caminhos de DLLs das bibliotecas nvidia instaladas via pip."""
    try:
        venv_root = os.path.dirname(os.path.dirname(sys.executable))
        nvidia_bins = glob.glob(os.path.join(venv_root, "Lib", "site-packages", "nvidia", "*", "bin"))
        for p in nvidia_bins:
            if os.path.isdir(p):
                os.add_dll_directory(p)
                os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
    except Exception:
        pass


ensure_cuda_dlls()
from faster_whisper import WhisperModel


@dataclass
class TranscriptionResult:
    """Resultado da transcrição com telemetria detalhada."""
    text: str
    language: str
    language_probability: float
    inference_time_seconds: float
    model_name: str
    device_used: str
    compute_type: str


class WhisperTranscriber:
    """
    Gerencia o modelo Whisper local (via faster-whisper/CTranslate2).
    Suporta aceleração por GPU (CUDA float16/int8) com fallback automático e transparente para CPU (int8).
    """

    DEFAULT_INITIAL_PROMPT = (
        "Transcrição em português do Brasil com pontuação, números e símbolos exatos: "
        "1h30, 2h30, 6h48, 10h15, +, -, *, /, =, %, R$ 50,00, 10 + 5 - 2, "
        "sinais de +, -, sinais de mais, sinais de menos, @, #, &, VS Code, Git, Python."
    )

    def __init__(
        self,
        model_name: str = "base",
        device: str = "auto",
        compute_type: Optional[str] = None,
        language: str = "pt"
    ):
        self.model_name = model_name
        self.language = language
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None
        self.actual_device = "unknown"
        self.actual_compute_type = "unknown"

        self._load_model()

    def _load_model(self):
        """Carrega o modelo, tentando GPU primeiro (se device='auto' ou 'cuda') e caindo para CPU se falhar."""
        devices_to_try = []

        if self.device in ("auto", "cuda"):
            ct = self.compute_type or "float16"
            devices_to_try.append(("cuda", ct))
        
        if self.device in ("auto", "cpu"):
            ct = self.compute_type if (self.device == "cpu" and self.compute_type) else "int8"
            devices_to_try.append(("cpu", ct))

        last_error = None
        for dev, c_type in devices_to_try:
            try:
                t0 = time.perf_counter()
                self.model = WhisperModel(
                    self.model_name,
                    device=dev,
                    compute_type=c_type
                )
                self.actual_device = dev
                self.actual_compute_type = c_type
                self.load_duration = time.perf_counter() - t0
                return
            except Exception as e:
                last_error = e
                self.model = None

        raise RuntimeError(f"Não foi possível carregar o modelo Whisper '{self.model_name}': {last_error}")

    def transcribe(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
        beam_size: int = 1,
        vad_filter: bool = True,
        initial_prompt: Optional[str] = None
    ) -> TranscriptionResult:
        """
        Transcreve um array NumPy float32 contido em memória.
        Zero escrita em disco.
        """
        lang = language or self.language
        if self.model is None:
            raise RuntimeError("Modelo Whisper não está carregado.")

        if len(audio_data) == 0:
            return TranscriptionResult(
                text="",
                language=self.language,
                language_probability=1.0,
                inference_time_seconds=0.0,
                model_name=self.model_name,
                device_used=self.actual_device,
                compute_type=self.actual_compute_type
            )

        # Garante que o array é float32 1D
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        if audio_data.ndim > 1:
            audio_data = audio_data.squeeze()

        t0 = time.perf_counter()
        prompt = initial_prompt if initial_prompt is not None else self.DEFAULT_INITIAL_PROMPT
        segments, info = self.model.transcribe(
            audio_data,
            language=lang,
            beam_size=beam_size,
            vad_filter=vad_filter,
            initial_prompt=prompt
        )

        # Materializa os segmentos
        segment_texts = [s.text.strip() for s in segments if s.text.strip()]
        full_text = " ".join(segment_texts)
        inference_time = time.perf_counter() - t0

        return TranscriptionResult(
            text=full_text,
            language=info.language,
            language_probability=info.language_probability,
            inference_time_seconds=inference_time,
            model_name=self.model_name,
            device_used=self.actual_device,
            compute_type=self.actual_compute_type
        )
