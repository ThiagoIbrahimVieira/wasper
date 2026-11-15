"""
Suíte de Testes Automatizados - Fase 3 (Refinamento Local com Ollama)
Valida disponibilidade, comportamento de fallback, desativação e formatação semântica.
"""

import sys
import unittest
from refiner import OllamaRefiner, RefinementResult

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")


class TestPhase3Refinement(unittest.TestCase):
    def test_refiner_disabled(self):
        """Quando desativado, deve retornar o texto original imediatamente sem chamar rede."""
        refiner = OllamaRefiner(enabled=False)
        self.assertFalse(refiner.is_available())
        res = refiner.refine("teste de texto bruto")
        self.assertEqual(res.text, "teste de texto bruto")
        self.assertFalse(res.fallback_used)
        self.assertLess(res.elapsed_ms, 5.0)

    def test_empty_input(self):
        """Entrada vazia deve retornar vazio imediatamente."""
        refiner = OllamaRefiner(enabled=True)
        res = refiner.refine("   ")
        self.assertEqual(res.text, "")
        self.assertFalse(res.fallback_used)

    def test_availability_check(self):
        """Verifica se o Ollama local e o modelo qwen3.5:2b são detectados."""
        refiner = OllamaRefiner(model="qwen3.5:2b", enabled=True)
        available = refiner.is_available()
        self.assertTrue(available, "Ollama local com modelo qwen3.5:2b deve estar acessível")

    def test_timeout_fallback(self):
        """Se o timeout for irrealisticamente baixo (ex: 0.001s), deve acionar fallback seguro."""
        refiner = OllamaRefiner(model="qwen3.5:2b", timeout=0.001, enabled=True)
        raw = "texto que nao tera tempo de ser refinado"
        res = refiner.refine(raw)
        self.assertEqual(res.text, raw)
        self.assertTrue(res.fallback_used)
        self.assertIn("Timeout", str(res.error_reason))

    def test_unreachable_endpoint_fallback(self):
        """Se o endpoint for inexistente, deve acionar fallback seguro imediatamente."""
        refiner = OllamaRefiner(endpoint="http://localhost:9999", enabled=True, timeout=0.5)
        raw = "texto para endpoint inexistente"
        res = refiner.refine(raw)
        self.assertEqual(res.text, raw)
        self.assertTrue(res.fallback_used)

    def test_real_model_refinement(self):
        """Teste real com o modelo local qwen3.5:2b."""
        refiner = OllamaRefiner(model="qwen3.5:2b", timeout=25.0, enabled=True)
        raw = "onde fica a padaria mais proxima"
        res = refiner.refine(raw)
        print(f"\n[Fase 3 Real] Bruto: '{raw}' -> Refinado: '{res.text}' (Latência: {res.elapsed_ms:.1f}ms, Fallback: {res.fallback_used})")
        self.assertFalse(res.fallback_used, f"Refinamento falhou: {res.error_reason}")
        self.assertTrue(res.text.endswith("?"), "Frase interrogativa deve terminar com ponto de interrogação")
        self.assertTrue(res.text[0].isupper(), "Primeira letra deve ser maiúscula")


if __name__ == "__main__":
    unittest.main()
