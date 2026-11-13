# Entrega — Consolidador de reservas Onfly

## Defeitos corrigidos

| # | Arquivo | Defeito | Causa raiz | Correção |
|-|-|-|-|-|
| 1 | `services/stay_calculator.py` | Noites erradas (negativas) na virada de mês/ano | Subtraía só o dia do mês (`checkout.day - checkin.day`), ignorando mês e ano. | `(checkout - checkin).days * rooms` |
| 2 | `services/currency_converter.py` | Valores em USD/EUR muito menores que o real | Dividia o valor pela taxa (`amount / rate`), e ainda passava por `float`. | `amount * rate`, só com `Decimal` |
| 3 | `services/status_policy.py` | `NO_SHOW` entrava em noites, valores, `by_month` e `top_hotels` | Considerava faturável tudo que fosse `!= "CANCELLED"`. | `status == "CONFIRMED"` |
| 4 | `services/report_builder.py` | Ranking mostrava os hotéis de menor valor primeiro | A chave de ordenação usava o valor em ordem crescente. | `key=(-amount, hotel_id)`: valor decrescente, empate por `hotel_id` crescente |
| 5 | `repositories/csv_reservation_repository.py` | Só 200 das 300 reservas eram lidas | Havia um `break` fixo ao chegar em 200 linhas. | Limite removido; o arquivo é lido inteiro |

A média de diárias saía `"0.00"` por causa do defeito 1: as noites negativas faziam `total_nights > 0` ser falso.

## Como investiguei

1. Li o README (regras de negócio e contrato) e segui o fluxo `cli → ReportBuilder → repositórios/serviços`.
2. Comparei cada serviço com a regra correspondente do README (noites, câmbio, status, ordenação e leitura). Cada defeito ficava isolado em uma função.
3. Contei as linhas do `data/reservas_hoteis.csv` (300 reservas) e comparei com o limite de 200 do repositório.
4. Corrigi com a menor mudança possível em cada ponto, sem alterar o CLI, o schema do relatório nem os testes fornecidos.
5. Adicionei testes em `tests/test_additional_rules.py` e confirmei que **todos falham no código original** e passam após a correção.

## Testes adicionados (`tests/test_additional_rules.py`)

- Noites na virada de ano com mais de um quarto, e mês do `by_month` pelo check-in.
- `NO_SHOW`/`CANCELLED` fora de `by_month` e `top_hotels`.
- Empate no ranking resolvido por `hotel_id` crescente.
- Soma exata em `Decimal`, com arredondamento half-up só na serialização.
- Arquivo com mais de 200 linhas e o dataset real com 300 reservas.
- A amostra `data/exemplo-validacao.csv` reproduz todas as tabelas do README.

## Como validar

```bash
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

pytest -q

PYTHONPATH=src python -m onfly_report \
  --input data/exemplo-validacao.csv \
  --rates data/taxas_cambio.csv \
  --output output/exemplo.json

PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json
```

## Resultados

`pytest -q` (Python 3.11.9):

```
............                                                             [100%]
12 passed
```

Antes da correção: `12 failed` (5 fornecidos e 7 adicionais).

Dataset completo (`data/reservas_hoteis.csv`):

```
Reservas: 300 | Confirmadas: 235 | Noites: 1347 | Total BRL: 396170.00
```

`cancelled_reservations` = 31, `no_show_reservations` = 34, `average_nightly_rate_brl` = `294.11`.
