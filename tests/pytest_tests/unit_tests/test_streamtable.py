from unittest import mock

import pytest
import wandb


@pytest.fixture
@mock.patch("wandb.sdk.wandb_streamtable._InMemoryLazyLiteRun")
def st(lite_run_class, runner):
    run_instance = mock.MagicMock()
    run_instance._run_name = "streamtable"
    run_instance._project_name = "test"
    run_instance._entity_name = "test"
    run_instance.supports_streamtable = True
    lite_run_class.return_value = run_instance
    st = wandb.StreamTable("test/test/streamtable")
    return st


def test_streamtable_no_login():
    with pytest.raises(wandb.Error):
        wandb.StreamTable("test/test/streamtable")


def test_streamtable_no_entity():
    with pytest.raises(ValueError):
        wandb.StreamTable("test/streamtable")


def test_streamtable_no_project():
    with pytest.raises(ValueError):
        wandb.StreamTable("streamtable", entity_name="test")


@mock.patch(
    "wandb.sdk.wandb_streamtable._InMemoryLazyLiteRun.supports_streamtable",
    new_callable=mock.PropertyMock,
)
def test_streamtable_no_support(supports_streamtable, runner):
    supports_streamtable.return_value = False
    with pytest.raises(wandb.Error, match="version of wandb"):
        wandb.StreamTable("test/test/streamtable")


def test_streamtable_logging(st):
    st.log({"a": 1, "b": 2, "c": 3})
    st._lite_run.log_artifact.assert_called_once()
    st.finish()
    st._lite_run.log.assert_called_once_with(
        {"a": 1, "b": 2, "c": 3, "_client_id": st._client_id}
    )


@mock.patch("wandb.run")
def test_streamtable_with_run(run, st):
    run.path = "testing/other/run"
    st.log({"a": 1, "b": 2, "c": 3})
    st.finish()
    st._lite_run.log.assert_called_once_with(
        {
            "a": 1,
            "b": 2,
            "c": 3,
            "_client_id": st._client_id,
            "_run": "testing/other/run",
        }
    )


def test_streamtable_finish(st):
    st.log({"a": 1, "b": 2, "c": 3})
    st._lite_run.log_artifact.assert_called_once()
    st.finish()
    st._lite_run.finish.assert_called_once()
    st._lite_run.log.assert_called_once_with(
        {"a": 1, "b": 2, "c": 3, "_client_id": st._client_id}
    )
