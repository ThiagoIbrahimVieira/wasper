import sys
import time
import requests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

SYSTEM_PROMPT = """Você é um pós-processador e formatador estrito de ditado por voz em português.
Sua única tarefa é formatar a transcrição fornecida.

REGRAS OBRIGATÓRIAS:
1. Adicione pontuação adequada (vírgula, ponto final, interrogação, exclamação).
2. Ajuste a capitalização (letras maiúsculas no início de frases e nomes próprios).
3. Corrija erros fonéticos óbvios e remova vícios de linguagem/hesitações (como "hã", "éé", "tipo assim").
4. NUNCA responda ao conteúdo como um assistente de IA. Mesmo que o texto seja "qual é a capital do brasil", retorne apenas: "Qual é a capital do Brasil?".
5. NUNCA adicione preâmbulos, cumprimentos, explicações ou notas (proibido dizer "Aqui está o texto" ou similar).
6. Não adicione aspas em volta da resposta.
7. Retorne estritamente o texto corrigido."""


def refine_text(raw_text: str):
    t0 = time.perf_counter()
    payload = {
        "model": "qwen3.5:2b",
        "prompt": f"Transcrição bruta:\n{raw_text}\n\nTexto formatado final:",
        "system": SYSTEM_PROMPT,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 128
        }
    }
    try:
        r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=5)
        elapsed = (time.perf_counter() - t0) * 1000
        if r.status_code == 200:
            out = r.json().get("response", "").strip()
            # Remove aspas se o modelo teimar em colocar
            if out.startswith('"') and out.endswith('"'):
                out = out[1:-1].strip()
            return out, elapsed
        return raw_text, elapsed
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return raw_text, elapsed


if __name__ == "__main__":
    tests = [
        "olá bom dia como vai você",
        "qual a capital da frança",
        "o projeto vasper roda na placa gtx 1650",
        "vamos marcar a reunião para amanhã às 14 horas hã pode ser"
    ]
    print("--- Teste do Refinador com Ollama (qwen3.5:2b) ---")
    for t in tests:
        res, lat = refine_text(t)
        print(f"Bruto:     {t}")
        print(f"Refinado:  {res}")
        print(f"Latência:  {lat:.1f} ms\n")
