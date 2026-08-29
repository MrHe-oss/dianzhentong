from pathlib import Path


def test_learning_center_does_not_use_pyarrow_backed_dataframe():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "st.dataframe(" not in source
    assert "st.table(" not in source
    assert "render_markdown_table" in source

