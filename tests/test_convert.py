from pathlib import Path
import pytest
from nb2pdf.converter import convert

TESTS_DIR = Path(__file__).parent
SAMPLE_NOTEBOOK = TESTS_DIR / "sample.ipynb"


def test_convert_sample_notebook(tmp_path):
    output_pdf = tmp_path / "output.pdf"
    result_path = convert(str(SAMPLE_NOTEBOOK), str(output_pdf))

    assert Path(result_path).exists()
    assert Path(result_path).stat().st_size > 0
