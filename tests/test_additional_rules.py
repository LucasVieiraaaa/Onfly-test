"""Testes adicionais: cenários não cobertos pelos testes fornecidos."""

import json
import os
import subprocess
import sys

from helpers import PROJECT_ROOT, SRC_DIR, run_cli


def test_nights_across_year_boundary(tmp_path):
    """A virada de ano também usa a diferença real de datas, multiplicada pelos quartos."""
    report = run_cli(
        tmp_path,
        [{"checkin_date": "2024-12-30", "checkout_date": "2025-01-02", "rooms": "2"}],
    )
    assert report["summary"]["total_room_nights"] == 6
    assert report["by_month"][0]["month"] == "2024-12"


def test_no_show_and_cancelled_excluded_from_month_and_ranking(tmp_path):
    """NO_SHOW e CANCELLED não aparecem em by_month nem em top_hotels."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "amount": "100.00"},
            {
                "reservation_id": "R-2",
                "hotel_id": "H02",
                "status": "NO_SHOW",
                "amount": "9999.00",
                "checkin_date": "2025-03-10",
                "checkout_date": "2025-03-12",
            },
            {
                "reservation_id": "R-3",
                "hotel_id": "H03",
                "status": "CANCELLED",
                "amount": "8888.00",
                "checkin_date": "2025-04-10",
                "checkout_date": "2025-04-12",
            },
        ],
    )
    assert [m["month"] for m in report["by_month"]] == ["2025-01"]
    assert [h["hotel_id"] for h in report["top_hotels"]] == ["H01"]
    assert report["summary"]["average_nightly_rate_brl"] == "100.00"


def test_top_hotels_tie_breaks_by_hotel_id_ascending(tmp_path):
    """Empate em total_brl é desempatado por hotel_id ascendente."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H03", "amount": "500.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "amount": "500.00"},
            {"reservation_id": "R-3", "hotel_id": "H02", "amount": "900.00"},
        ],
    )
    assert [h["hotel_id"] for h in report["top_hotels"]] == ["H02", "H01", "H03"]


def test_conversion_uses_decimal_and_rounds_half_up_only_at_the_end(tmp_path):
    """Somas exatas em Decimal; arredondamento half-up apenas na serialização."""
    report = run_cli(
        tmp_path,
        [
            {"reservation_id": "R-1", "currency": "USD", "amount": "0.01"},
            {"reservation_id": "R-2", "currency": "USD", "amount": "0.01"},
            {"reservation_id": "R-3", "currency": "USD", "amount": "0.01"},
        ],
    )
    # 0.01 * 5.42 = 0.0542 por reserva; soma exata 0.1626 -> "0.16".
    # Arredondar cada parcela antes (0.05 * 3) daria "0.15".
    assert report["summary"]["total_amount_brl"] == "0.16"
    assert report["summary"]["average_nightly_rate_brl"] == "0.05"


def test_validation_sample_matches_readme(tmp_path):
    """A amostra data/exemplo-validacao.csv reproduz a tabela do README."""
    output_path = tmp_path / "exemplo.json"
    report = _run_on_file(PROJECT_ROOT / "data" / "exemplo-validacao.csv", output_path)
    assert report["summary"] == {
        "total_reservations": 12,
        "confirmed_reservations": 9,
        "cancelled_reservations": 2,
        "no_show_reservations": 1,
        "total_room_nights": 28,
        "total_amount_brl": "7566.00",
        "average_nightly_rate_brl": "270.21",
    }
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 8, "room_nights": 25, "total_brl": "6684.00"},
        {"month": "2025-02", "reservations": 1, "room_nights": 3, "total_brl": "882.00"},
    ]
    assert [(h["hotel_id"], h["room_nights"], h["total_brl"]) for h in report["top_hotels"]] == [
        ("H01", 3, "1200.00"),
        ("H02", 2, "1084.00"),
        ("H12", 1, "1000.00"),
        ("H10", 4, "900.00"),
        ("H09", 3, "882.00"),
    ]


def _run_on_file(input_path, output_path):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "onfly_report",
            "--input",
            str(input_path),
            "--rates",
            str(PROJECT_ROOT / "data" / "taxas_cambio.csv"),
            "--output",
            str(output_path),
        ],
        cwd=str(PROJECT_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert process.returncode == 0, process.stderr
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_reads_all_rows_beyond_200(tmp_path):
    """O arquivo é lido por completo, sem limite de linhas."""
    rows = [{"reservation_id": f"R-{i}", "amount": "10.00"} for i in range(1, 251)]
    report = run_cli(tmp_path, rows)
    assert report["summary"]["total_reservations"] == 250
    assert report["summary"]["total_amount_brl"] == "2500.00"


def test_full_dataset_is_read_completely(tmp_path):
    """O dataset real tem 300 reservas e todas devem ser contadas."""
    report = _run_on_file(PROJECT_ROOT / "data" / "reservas_hoteis.csv", tmp_path / "report.json")
    summary = report["summary"]
    assert summary["total_reservations"] == 300
    assert (
        summary["confirmed_reservations"]
        + summary["cancelled_reservations"]
        + summary["no_show_reservations"]
        == 300
    )
