import av
import io
import numpy as np


def load_audio_from_file_or_bytes(source, target_sample_rate: int = 16000) -> np.ndarray:
    """
    Decodifica qualquer formato de áudio (MP3, WAV, OGG, FLAC) diretamente
    para um array NumPy float32 normalizado (-1.0 a 1.0) em 16.000 Hz mono.
    """
    container = av.open(source)
    stream = container.streams.audio[0]

    resampler = av.AudioResampler(
        format="flt",       # float32
        layout="mono",      # 1 canal
        rate=target_sample_rate
    )

    audio_frames = []
    for frame in container.decode(stream):
        for resampled in resampler.resample(frame):
            audio_frames.append(resampled.to_ndarray().reshape(-1))

    container.close()

    if not audio_frames:
        return np.array([], dtype=np.float32)

    return np.concatenate(audio_frames).astype(np.float32)
