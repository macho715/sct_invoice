from pathlib import Path
def test_scaffold_exists():
    assert Path('src').exists() and Path('tests').exists()
