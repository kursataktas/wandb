import base64
import hashlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Tuple, Type, TypeVar, Union
from unittest.mock import Mock, call, patch

import pytest
import requests
import responses
import wandb.errors
import wandb.sdk.internal.internal_api
import wandb.sdk.internal.progress
from wandb.apis import internal
from wandb.errors import CommError
from wandb.sdk.lib import retry

from .test_retry import MockTime, mock_time  # noqa: F401

_T = TypeVar("_T")


@pytest.fixture
def mock_responses():
    with responses.RequestsMock() as rsps:
        yield rsps


def test_agent_heartbeat_with_no_agent_id_fails():
    a = internal.Api()
    with pytest.raises(ValueError):
        a.agent_heartbeat(None, {}, {})


def test_get_run_state_invalid_kwargs():
    with pytest.raises(CommError) as e:
        _api = internal.Api()

        def _mock_gql(*args, **kwargs):
            return dict()

        _api.api.gql = _mock_gql
        _api.get_run_state("test_entity", None, "test_run")

    assert "Error fetching run state" in str(e.value)


@pytest.mark.parametrize(
    "existing_contents,expect_download",
    [
        (None, True),
        ("outdated contents", True),
        ("current contents", False),
    ],
)
def test_download_write_file_fetches_iff_file_checksum_mismatched(
    existing_contents: Optional[str],
    expect_download: bool,
):
    url = "https://example.com/path/to/file.txt"
    current_contents = "current contents"
    with responses.RequestsMock() as rsps, tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "file.txt")

        if expect_download:
            rsps.add(
                responses.GET,
                url,
                body=current_contents,
            )

        if existing_contents is not None:
            with open(filepath, "w") as f:
                f.write(existing_contents)

        _, response = internal.InternalApi().download_write_file(
            metadata={
                "name": filepath,
                "md5": base64.b64encode(
                    hashlib.md5(current_contents.encode()).digest()
                ).decode(),
                "url": url,
            },
            out_dir=tmpdir,
        )

        if expect_download:
            assert response is not None
        else:
            assert response is None


def test_internal_api_with_no_write_global_config_dir(tmp_path):
    with patch.dict("os.environ", WANDB_CONFIG_DIR=str(tmp_path)):
        os.chmod(tmp_path, 0o444)
        internal.InternalApi()
        os.chmod(tmp_path, 0o777)  # Allow the test runner to clean up.


def test_fetch_orgs_and_org_entities_from_entity(mock_server):
    """Test fetching organization entities from an entity."""
    api = wandb.Api()

    # Test team/org entity case
    mock_server.gql.return_value = {
        "entity": {
            "organization": {
                "name": "test-org",
                "orgEntity": {"name": "test-org-entity"},
            },
            "user": None,
        }
    }
    result = api._fetch_orgs_and_org_entities_from_entity("team-entity")
    assert result == [("test-org-entity", "test-org")]

    # Test personal entity with single org
    mock_server.gql.return_value = {
        "entity": {
            "organization": None,
            "user": {
                "organizations": [
                    {
                        "name": "personal-org",
                        "orgEntity": {"name": "personal-org-entity"},
                    }
                ]
            },
        }
    }
    result = api._fetch_orgs_and_org_entities_from_entity("personal-entity")
    assert result == [("personal-org-entity", "personal-org")]

    # Test personal entity with multiple orgs
    mock_server.gql.return_value = {
        "entity": {
            "organization": None,
            "user": {
                "organizations": [
                    {
                        "name": "org1",
                        "orgEntity": {"name": "org1-entity"},
                    },
                    {
                        "name": "org2",
                        "orgEntity": {"name": "org2-entity"},
                    },
                ]
            },
        }
    }
    result = api._fetch_orgs_and_org_entities_from_entity("personal-entity")
    assert result == [("org1-entity", "org1"), ("org2-entity", "org2")]

    # Test entity not found (This I haven't seen in the wild but adding a test for it)
    mock_server.gql.return_value = None
    with pytest.raises(ValueError, match="Unable to find an entity with name"):
        api._fetch_orgs_and_org_entities_from_entity("non-existent-entity")

    # Test personal entity with no orgs
    mock_server.gql.return_value = {
        "entity": {
            "organization": None,
            "user": {"organizations": []},
        }
    }
    with pytest.raises(
        ValueError,
        match="Unable to resolve an organization associated with personal entity",
    ):
        api._fetch_orgs_and_org_entities_from_entity("personal-entity")

    # No entity found
    mock_server.gql.return_value = {
        "entity": {
            "organization": None,
            "user": None,
        }
    }
    with pytest.raises(
        ValueError,
        match="Unable to resolve an organization associated with personal entity",
    ):
        api._fetch_orgs_and_org_entities_from_entity("potato-entity")

    # Test invalid response structure
    mock_server.gql.return_value = {
        "entity": {
            "organization": {
                "name": "hello",
                "orgEntity": None,
            },
            "user": None,
        }
    }
    with pytest.raises(ValueError, match="Unable to find an organization under entity"):
        api._fetch_orgs_and_org_entities_from_entity("invalid-entity")


def test_match_org_with_fetched_org_entities():
    api = internal.InternalApi()

    # Test successful matches should return the correct org_entity_name
    assert (
        api._match_org_with_fetched_org_entities(
            "org-display", [("org-entity", "org-display")]
        )
        == "org-entity"
    )

    assert (
        api._match_org_with_fetched_org_entities(
            "org-entity", [("org-entity", "org-display")]
        )
        == "org-entity"
    )

    assert (
        api._match_org_with_fetched_org_entities(
            "org-display-2",
            [("org-entity", "org-display"), ("org-entity-2", "org-display-2")],
        )
        == "org-entity-2"
    )

    # Test error when org doesn't match (single org case)
    with pytest.raises(
        ValueError, match="Expecting the organization name or entity name to match"
    ):
        api._match_org_with_fetched_org_entities(
            "wrong-org", [("org-entity", "org-display")]
        )

    # Test error when org doesn't match (multiple orgs case)
    with pytest.raises(
        ValueError, match="Personal entity belongs to multiple organizations"
    ):
        api._match_org_with_fetched_org_entities(
            "wrong-org",
            [("org1-entity", "org1-display"), ("org2-entity", "org2-display")],
        )


def test_resolve_org_entity_name_with_single_org():
    api = internal.InternalApi()

    # Mock server introspection and GQL responses
    api.server_organization_type_introspection = Mock(return_value=["orgEntity"])
    api._fetch_orgs_and_org_entities_from_entity = Mock(
        return_value=[("org-entity", "org-display")]
    )

    assert api._resolve_org_entity_name("entity", "org-display") == "org-entity"
    assert api._resolve_org_entity_name("entity", "org-entity") == "org-entity"
    assert api._resolve_org_entity_name("entity") == "org-entity"

    # Error when org doesn't match
    with pytest.raises(
        ValueError, match="Expecting the organization name or entity name to match"
    ):
        api._resolve_org_entity_name("entity", "potato-org")

    # Error when entity is None or empty string
    with pytest.raises(
        ValueError, match="Entity name is required to resolve org entity name."
    ):
        api._resolve_org_entity_name(None)
    with pytest.raises(
        ValueError, match="Entity name is required to resolve org entity name."
    ):
        api._resolve_org_entity_name("")


def test_resolve_org_entity_name_with_multiple_orgs():
    api = internal.InternalApi()
    api.server_organization_type_introspection = Mock(return_value=["orgEntity"])
    api._fetch_orgs_and_org_entities_from_entity = Mock(
        return_value=[
            ("org1-entity", "org1-display"),
            ("org2-entity", "org2-display"),
            ("org3-entity", "org3-display"),
        ]
    )
    # Error for personal entity with multiple orgs and no org specified because
    # we don't know which org to use
    with pytest.raises(ValueError, match="belongs to multiple organizations"):
        api._resolve_org_entity_name("entity")

    # Should work with organization specified
    assert api._resolve_org_entity_name("entity", "org1-display") == "org1-entity"
    assert api._resolve_org_entity_name("entity", "org2-entity") == "org2-entity"

    # Error when org doesn't match the list of personal orgs the entity belongs to
    with pytest.raises(
        ValueError, match="Personal entity belongs to multiple organizations"
    ):
        api._resolve_org_entity_name("entity", "potato-org")


def test_resolve_org_entity_name_with_old_server():
    api = internal.InternalApi()
    api.server_organization_type_introspection = Mock(return_value=[])

    # Should error without organization
    with pytest.raises(ValueError, match="unavailable for your server version"):
        api._resolve_org_entity_name("entity")

    # Should return organization as-is when specified
    assert api._resolve_org_entity_name("entity", "org-name-input") == "org-name-input"


MockResponseOrException = Union[Exception, Tuple[int, Mapping[int, int], str]]


@pytest.mark.skipif(
    sys.version_info.major == 3 and sys.version_info.minor < 8,
    reason="flaky on 3.7",
)
class TestUploadFile:
    """Tests `upload_file`."""

    class TestSimple:
        def test_adds_headers_to_request(
            self, mock_responses: responses.RequestsMock, example_file: Path
        ):
            response_callback = Mock(return_value=(200, {}, "success!"))
            mock_responses.add_callback(
                "PUT", "http://example.com/upload-dst", response_callback
            )
            internal.InternalApi().upload_file(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                extra_headers={"X-Test": "test"},
            )
            assert response_callback.call_args[0][0].headers["X-Test"] == "test"

        def test_returns_response_on_success(
            self, mock_responses: responses.RequestsMock, example_file: Path
        ):
            mock_responses.add(
                "PUT", "http://example.com/upload-dst", status=200, body="success!"
            )
            resp = internal.InternalApi().upload_file(
                "http://example.com/upload-dst", example_file.open("rb")
            )
            assert resp.content == b"success!"

        # test_async_returns_response_on_success: doesn't exist,
        # because `upload_file_async` doesn't return the response.

        @pytest.mark.parametrize(
            "response,expected_errtype",
            [
                ((400, {}, ""), requests.exceptions.HTTPError),
                ((500, {}, ""), retry.TransientError),
                ((502, {}, ""), retry.TransientError),
                (requests.exceptions.ConnectionError(), retry.TransientError),
                (requests.exceptions.Timeout(), retry.TransientError),
                (RuntimeError("oh no"), RuntimeError),
            ],
        )
        def test_returns_transienterror_on_transient_issues(
            self,
            mock_responses: responses.RequestsMock,
            example_file: Path,
            response: MockResponseOrException,
            expected_errtype: Type[Exception],
        ):
            mock_responses.add_callback(
                "PUT",
                "http://example.com/upload-dst",
                Mock(return_value=response),
            )
            with pytest.raises(expected_errtype):
                internal.InternalApi().upload_file(
                    "http://example.com/upload-dst", example_file.open("rb")
                )

    class TestProgressCallback:
        def test_smoke(
            self, mock_responses: responses.RequestsMock, example_file: Path
        ):
            file_contents = "some text"
            example_file.write_text(file_contents)

            def response_callback(request: requests.models.PreparedRequest):
                assert request.body.read() == file_contents.encode()
                return (200, {}, "success!")

            mock_responses.add_callback(
                "PUT", "http://example.com/upload-dst", response_callback
            )

            progress_callback = Mock()
            internal.InternalApi().upload_file(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                callback=progress_callback,
            )

            assert progress_callback.call_args_list == [
                call(len(file_contents), len(file_contents))
            ]

        def test_handles_multiple_calls(
            self, mock_responses: responses.RequestsMock, example_file: Path
        ):
            example_file.write_text("12345")

            def response_callback(request: requests.models.PreparedRequest):
                assert request.body.read(2) == b"12"
                assert request.body.read(2) == b"34"
                assert request.body.read() == b"5"
                assert request.body.read() == b""
                return (200, {}, "success!")

            mock_responses.add_callback(
                "PUT", "http://example.com/upload-dst", response_callback
            )

            progress_callback = Mock()
            internal.InternalApi().upload_file(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                callback=progress_callback,
            )

            assert progress_callback.call_args_list == [
                call(2, 2),
                call(2, 4),
                call(1, 5),
                call(0, 5),
            ]

        @pytest.mark.parametrize(
            "failure",
            [
                requests.exceptions.Timeout(),
                requests.exceptions.ConnectionError(),
                (400, {}, ""),
                (500, {}, ""),
            ],
        )
        def test_rewinds_on_failure(
            self,
            mock_responses: responses.RequestsMock,
            example_file: Path,
            failure: MockResponseOrException,
        ):
            example_file.write_text("1234567")

            def response_callback(request: requests.models.PreparedRequest):
                assert request.body.read(2) == b"12"
                assert request.body.read(2) == b"34"
                return failure

            mock_responses.add_callback(
                "PUT", "http://example.com/upload-dst", response_callback
            )

            progress_callback = Mock()
            with pytest.raises((retry.TransientError, requests.RequestException)):
                internal.InternalApi().upload_file(
                    "http://example.com/upload-dst",
                    example_file.open("rb"),
                    callback=progress_callback,
                )

            assert progress_callback.call_args_list == [
                call(2, 2),
                call(2, 4),
                call(-4, 0),
            ]

    @pytest.mark.parametrize(
        "request_headers,response,expected_errtype",
        [
            (
                {"x-amz-meta-md5": "1234"},
                (400, {}, "blah blah RequestTimeout blah blah"),
                retry.TransientError,
            ),
            (
                {"x-amz-meta-md5": "1234"},
                (400, {}, "non-timeout-related error message"),
                requests.RequestException,
            ),
            (
                {"x-amz-meta-md5": "1234"},
                requests.exceptions.ConnectionError(),
                retry.TransientError,
            ),
            (
                {},
                (400, {}, "blah blah RequestTimeout blah blah"),
                requests.RequestException,
            ),
        ],
    )
    def test_transient_failure_on_special_aws_request_timeout(
        self,
        mock_responses: responses.RequestsMock,
        example_file: Path,
        request_headers: Mapping[str, str],
        response,
        expected_errtype: Type[Exception],
    ):
        mock_responses.add_callback(
            "PUT", "http://example.com/upload-dst", Mock(return_value=response)
        )
        with pytest.raises(expected_errtype):
            internal.InternalApi().upload_file(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                extra_headers=request_headers,
            )

    # test_async_transient_failure_on_special_aws_request_timeout: see
    # `test_async_retries_on_special_aws_request_timeout` on TestUploadRetry.

    class TestAzure:
        MAGIC_HEADERS = {"x-ms-blob-type": "SomeBlobType"}

        @pytest.mark.parametrize(
            "request_headers,uses_azure_lib",
            [
                ({}, False),
                (MAGIC_HEADERS, True),
            ],
        )
        def test_uses_azure_lib_if_available(
            self,
            mock_responses: responses.RequestsMock,
            example_file: Path,
            request_headers: Mapping[str, str],
            uses_azure_lib: bool,
        ):
            api = internal.InternalApi()

            if uses_azure_lib:
                api._azure_blob_module = Mock()
            else:
                mock_responses.add("PUT", "http://example.com/upload-dst")

            api.upload_file(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                extra_headers=request_headers,
            )

            if uses_azure_lib:
                api._azure_blob_module.BlobClient.from_blob_url().upload_blob.assert_called_once()
            else:
                assert len(mock_responses.calls) == 1

        @pytest.mark.parametrize(
            "response,expected_errtype,check_err",
            [
                (
                    (400, {}, "my-reason"),
                    requests.RequestException,
                    lambda e: e.response.status_code == 400 and "my-reason" in str(e),
                ),
                (
                    (500, {}, "my-reason"),
                    retry.TransientError,
                    lambda e: (
                        e.exception.response.status_code == 500
                        and "my-reason" in str(e.exception)
                    ),
                ),
                (
                    requests.exceptions.ConnectionError("my-reason"),
                    retry.TransientError,
                    lambda e: "my-reason" in str(e.exception),
                ),
            ],
        )
        def test_translates_azure_err_to_normal_err(
            self,
            mock_responses: responses.RequestsMock,
            example_file: Path,
            response: MockResponseOrException,
            expected_errtype: Type[Exception],
            check_err: Callable[[Exception], bool],
        ):
            mock_responses.add_callback(
                "PUT", "https://example.com/foo/bar/baz", Mock(return_value=response)
            )
            with pytest.raises(expected_errtype) as e:
                internal.InternalApi().upload_file(
                    "https://example.com/foo/bar/baz",
                    example_file.open("rb"),
                    extra_headers=self.MAGIC_HEADERS,
                )

            assert check_err(e.value), e.value


class TestUploadFileRetry:
    """Test the retry logic of upload_file_retry.

    Testing the file-upload logic itself is done in TestUploadFile, above;
    this class just tests the retry logic (though it does make a couple
    assumptions about status codes, like "400 isn't retriable, 500 is.")
    """

    @pytest.mark.parametrize(
        ["schedule", "num_requests"],
        [
            ([200, 0], 1),
            ([500, 500, 200, 0], 3),
        ],
    )
    def test_stops_after_success(
        self,
        example_file: Path,
        mock_responses: responses.RequestsMock,
        schedule: Sequence[int],
        num_requests: int,
    ):
        handler = Mock(side_effect=[(status, {}, "") for status in schedule])
        mock_responses.add_callback("PUT", "http://example.com/upload-dst", handler)

        internal.InternalApi().upload_file_retry(
            "http://example.com/upload-dst",
            example_file.open("rb"),
        )

        assert handler.call_count == num_requests

    def test_stops_after_bad_status(
        self,
        example_file: Path,
        mock_responses: responses.RequestsMock,
    ):
        handler = Mock(side_effect=[(400, {}, "")])
        mock_responses.add_callback("PUT", "http://example.com/upload-dst", handler)

        with pytest.raises(wandb.errors.CommError):
            internal.InternalApi().upload_file_retry(
                "http://example.com/upload-dst",
                example_file.open("rb"),
            )
        assert handler.call_count == 1

    def test_stops_after_retry_limit_exceeded(
        self,
        example_file: Path,
        mock_responses: responses.RequestsMock,
    ):
        num_retries = 8
        handler = Mock(return_value=(500, {}, ""))
        mock_responses.add_callback("PUT", "http://example.com/upload-dst", handler)

        with pytest.raises(wandb.errors.CommError):
            internal.InternalApi().upload_file_retry(
                "http://example.com/upload-dst",
                example_file.open("rb"),
                num_retries=num_retries,
            )

        assert handler.call_count == num_retries + 1
