from pathlib import Path
import importlib.util
import sys
import textwrap
import types

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HVDC_ROOT = REPO_ROOT / "hvdc_pipeline"

scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(HVDC_ROOT / "scripts")]
sys.modules.setdefault("scripts", scripts_pkg)

stage1_pkg = types.ModuleType("scripts.stage1_sync")
stage1_pkg.__path__ = [str(HVDC_ROOT / "scripts/stage1_sync")]
sys.modules.setdefault("scripts.stage1_sync", stage1_pkg)

stage2_pkg = types.ModuleType("scripts.stage2_derived")
stage2_pkg.__path__ = [str(HVDC_ROOT / "scripts/stage2_derived")]
sys.modules.setdefault("scripts.stage2_derived", stage2_pkg)


def _load_module(module_name: str, module_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


stage1_sync = _load_module(
    "scripts.stage1_sync.data_synchronizer",
    HVDC_ROOT / "scripts/stage1_sync/data_synchronizer.py",
)
stage2_derived = _load_module(
    "scripts.stage2_derived.derived_columns_processor",
    HVDC_ROOT / "scripts/stage2_derived/derived_columns_processor.py",
)
run_pipeline = _load_module(
    "run_pipeline",
    HVDC_ROOT / "run_pipeline.py",
)


@pytest.fixture()
def pipeline_and_stage2_config(tmp_path: Path) -> tuple[Path, Path, Path]:
    project_root = tmp_path
    pipeline_config_path = project_root / "pipeline_config.yaml"
    stage2_config_path = project_root / "stage2_config.yaml"

    pipeline_config_path.write_text(
        textwrap.dedent(
            """
            paths:
              synced_dir: "data/processed/synced"
              derived_dir: "data/processed/derived"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    stage2_config_path.write_text(
        textwrap.dedent(
            """
            input:
              synced_file: "data/processed/synced/HVDC_WAREHOUSE_HITACHI_HE_synced.xlsx"
            output:
              derived_file: "data/processed/derived/HVDC_WAREHOUSE_HITACHI_HE_derived.xlsx"
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    return project_root, pipeline_config_path, stage2_config_path


def test_stage1_and_stage2_share_synced_path(pipeline_and_stage2_config: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch) -> None:
    project_root, pipeline_config_path, stage2_config_path = pipeline_and_stage2_config

    warehouse_dir = project_root / "warehouse"
    warehouse_dir.mkdir(parents=True, exist_ok=True)
    warehouse_file = warehouse_dir / "HVDC_WAREHOUSE_HITACHI_HE.xlsx"
    warehouse_file.touch()

    monkeypatch.setattr(stage1_sync, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(stage1_sync, "PIPELINE_CONFIG_PATH", pipeline_config_path)

    monkeypatch.setattr(stage2_derived, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(stage2_derived, "PIPELINE_CONFIG_PATH", pipeline_config_path)
    monkeypatch.setattr(stage2_derived, "STAGE2_CONFIG_PATH", stage2_config_path)

    stage1_path = stage1_sync.resolve_synced_output_path(
        warehouse_file,
        config_path=pipeline_config_path,
        project_root=project_root,
    )
    stage2_path = stage2_derived.resolve_synced_input_path(
        pipeline_config_path=pipeline_config_path,
        stage2_config_path=stage2_config_path,
        project_root=project_root,
    )

    assert stage1_path == stage2_path
    assert stage1_path.name.endswith("_synced.xlsx")
    assert stage1_path.parent.exists()


def test_run_pipeline_uses_shared_synced_path(
    pipeline_and_stage2_config: tuple[Path, Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root, pipeline_config_path, stage2_config_path = pipeline_and_stage2_config

    shared_path = project_root / "data/processed/synced/HVDC_WAREHOUSE_HITACHI_HE_synced.xlsx"
    shared_path.parent.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(run_pipeline, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(run_pipeline, "PIPELINE_CONFIG_PATH", pipeline_config_path)
    monkeypatch.setattr(run_pipeline, "STAGE2_CONFIG_PATH", stage2_config_path)

    calls: list[tuple[Path, Path, Path]] = []

    def fake_resolve(*, pipeline_config_path: Path, stage2_config_path: Path, project_root: Path) -> Path:
        calls.append((pipeline_config_path, stage2_config_path, project_root))
        return shared_path

    monkeypatch.setattr(run_pipeline, "resolve_stage2_synced_input_path", fake_resolve)

    monkeypatch.setattr(run_pipeline, "process_derived_columns", lambda **_: True)

    assert run_pipeline.run_stage(1, {}) is True
    assert run_pipeline.run_stage(2, {}) is True
    assert calls[0] == calls[1]
    assert calls[0] == (pipeline_config_path, stage2_config_path, project_root)
