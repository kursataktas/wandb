import os
import pathlib
import shutil
import sys
from typing import Optional
from unittest.mock import patch

import numpy as np
import pytest
import wandb

run_name_base = pathlib.Path(__file__).stem
init_count = 1


def get_init_count():
    global init_count
    current_count = init_count
    init_count += 1
    return current_count


@pytest.fixture
def teardown():
    yield
    wandb.finish()
    if os.path.isdir("wandb"):
        shutil.rmtree("wandb")
    if os.path.isdir("artifacts"):
        shutil.rmtree("artifacts")


@pytest.mark.parametrize("num_files", [10, 100, 1_000, 10_000])
@pytest.mark.parametrize("async_upload_concurrency_limit", [None, 200])
def test_benchmark_upload_artifact(
    tmp_path: pathlib.Path,
    benchmark,
    async_upload_concurrency_limit: Optional[int],
    num_files: int,
):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    num_file_digits = len(str(num_files - 1))
    for filenum in range(num_files):
        (data_dir / f"file{filenum:0{num_file_digits}d}.txt").write_bytes(
            np.random.bytes(40_000)
        )

    with patch.dict(os.environ, {"WANDB_CACHE_DIR": str(tmp_path / "cache")}):
        with wandb.init(
            settings={"async_upload_concurrency_limit": async_upload_concurrency_limit},
        ) as run:
            artifact = wandb.Artifact("benchmark", "benchmark")
            artifact.add_dir(data_dir)
            run.log_artifact(artifact)
            benchmark.pedantic(
                target=artifact.wait,
                rounds=1,
                iterations=1,
            )


if __name__ == "__main__":
    pytest.main(sys.argv)
