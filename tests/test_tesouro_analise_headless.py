import subprocess
import sys


def test_public_api_imports_without_ui_or_network_modules():
    code = (
        "import sys\n"
        "import b3_selic_pre.application.tesouro as t\n"
        "for name in ('tkinter', 'matplotlib', 'urllib', 'http'):\n"
        "    assert name not in sys.modules, name\n"
        "assert t.SeriesProvider is not None\n"
        "assert t.classificar_familia('Tesouro Selic 2029').familia == 'SELIC'\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_public_api_exposes_analysis_contract():
    from b3_selic_pre.application.tesouro import (
        SeriesKey,
        SeriesPoint,
        SeriesProvider,
        TesouroSeriesProvider,
        classificar_familia,
        composicao_estoque_por_familia,
        fluxo_liquido_por_familia,
        percentual_demanda_por_familia,
    )

    assert SeriesKey is not None
    assert SeriesPoint is not None
    assert SeriesProvider is not None
    assert TesouroSeriesProvider is not None
    assert classificar_familia is not None
    assert composicao_estoque_por_familia is not None
    assert percentual_demanda_por_familia is not None
    assert fluxo_liquido_por_familia is not None
