# Declaração de uso de IA

## Ferramenta e modelo

- **Ferramenta:** Claude Code (CLI)
- **Modelo:** Claude Opus 5.5 (`claude-opus-5-5`)

## O que eu fiz

- Analisei o código e identifiquei os 5 defeitos (noites, câmbio, status, ordenação do ranking e limite de 200 linhas), além da causa da média `"0.00"` e da falha no teste de regressão.
- Escrevi o prompt para a IA com o diagnóstico, as correções propostas e a restrição de não alterar os testes.
- Decidi como implementar: `Decimal` puro no câmbio, desempate do ranking por `hotel_id`, adicionar testes e gerar a documentação de entrega.
- Revisei as alterações e os resultados.
- Rodei o `pytest` no Python 3.11 e o CLI no dataset completo.

## O que a IA fez

- Leu o código, os testes e o README, e confirmou o diagnóstico.
- Apontou que o conversor usava `float`, o que o README proíbe, e fez perguntas antes de implementar.
- Aplicou as 5 correções no código.
- Escreveu `tests/test_additional_rules.py` e verificou que os testes falham no código original e passam após a correção.
- Redigiu o `README-ENTREGA.md` e esta declaração.

## Sessão

A exportação da sessão está em `entrega/uso-de-ia/sessao.md` (gerada com `/export` do Claude Code).
