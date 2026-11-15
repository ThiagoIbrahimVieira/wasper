"""
Wasper — Limpador de Disfluências e Hesitações de Fala
Executa em pura CPU em menos de 1 milissegundo, preservando a identidade,
os verbos essenciais e expressões naturais do usuário (ex: 'né?', 'sabe?').
"""

import re


def clean_speech_disfluencies(text: str) -> str:
    """
    Limpa disfluências reais (gagueiras, 'ééé', repetições) preservando
    o tom de voz e expressões conversacionais (como 'né?', 'sabe?', verbos 'é').
    """
    if not text:
        return ""

    s = text.strip()

    # 1. Remove hesitações prolongadas ("ééé", "hummm", "hãã", "ahhh")
    s = re.sub(r"\b(é{2,}|eh{2,}|hum+|hã+|ah+)\b", "", s, flags=re.IGNORECASE)

    # 2. Remove pausa de hesitação isolada entre vírgulas (ex: ", é, ")
    s = re.sub(r",\s*é\s*,", ",", s, flags=re.IGNORECASE)

    # 3. Remove gagueira de palavras repetidas idênticas (ex: "mais, mais" -> "mais", "pra pra" -> "pra")
    s = re.sub(r"\b(\w+)(,\s*|\s+)\1\b", r"\1", s, flags=re.IGNORECASE)

    # 4. Limpeza de pontuação duplicada e espaçamento resultante
    s = re.sub(r",\s*,+", ",", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r"\s+", " ", s).strip()

    if s:
        s = s[0].upper() + s[1:]

    return s
