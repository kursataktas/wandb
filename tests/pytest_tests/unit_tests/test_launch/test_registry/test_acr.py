from unittest.mock import MagicMock

import pytest
from wandb.sdk.launch.registry.azure_container_registry import (
    AzureContainerRegistryHelper,
    ResourceNotFoundError,
)


@pytest.fixture
def mock_default_azure_credential(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(
        "wandb.sdk.launch.environment.azure_environment.DefaultAzureCredential", mock
    )
    return mock


@pytest.fixture
def mock_container_registry_client(monkeypatch):
    mock = MagicMock()
    (
        monkeypatch.setattr(
            "wandb.sdk.launch.registry.azure_container_registry.ContainerRegistryClient",
            MagicMock(return_value=mock),
        ),
    )
    return mock


def test_acr_from_config(mock_default_azure_credential, monkeypatch):
    """Test AzureContainerRegistry class."""
    config = {"uri": "https://test.azurecr.io/repository"}
    acr = AzureContainerRegistryHelper.from_config(config)
    assert acr.uri == "test.azurecr.io/repository"
    assert acr.registry_name == "test"
    assert acr.repo_name == "repository"


@pytest.mark.asyncio
async def test_acr_get_repo_uri(mock_default_azure_credential, monkeypatch):
    """Test AzureContainerRegistry class."""
    config = {"uri": "https://test.azurecr.io/repository"}
    registry = AzureContainerRegistryHelper.from_config(config)
    assert await registry.get_repo_uri() == "https://test.azurecr.io/repository"


@pytest.mark.asyncio
async def test_acr_check_image_exists(
    mock_default_azure_credential,
    mock_container_registry_client,
):
    """Test AzureContainerRegistry class."""
    # Make the mock client return a digest when get_manifest_properties is called and
    # check that the method returns True.
    mock_container_registry_client.get_manifest_properties.return_value = {
        "digest": "test"
    }
    config = {"uri": "https://test.azurecr.io/repository"}
    registry = AzureContainerRegistryHelper.from_config(config)
    assert await registry.check_image_exists("test.azurecr.io/launch-images:tag")


@pytest.mark.asyncio
async def test_acr_check_image_exists_not_found(
    mock_default_azure_credential,
    mock_container_registry_client,
):
    mock_container_registry_client.get_manifest_properties = MagicMock(
        side_effect=(ResourceNotFoundError())
    )
    registry = AzureContainerRegistryHelper(uri="https://test.azurecr.io/repository")
    assert not await registry.check_image_exists(
        "https://test.azurecr.io/repository:tag"
    )


def test_acr_registry_name(mock_default_azure_credential):
    """Test if repository name is parsed correctly."""
    config = {"uri": "https://test.azurecr.io/repository"}
    registry = AzureContainerRegistryHelper.from_config(config)
    assert registry.registry_name == "test"
    # Same thing but without https
    config = {"uri": "test.azurecr.io/repository"}
    registry = AzureContainerRegistryHelper.from_config(config)
    assert registry.registry_name == "test"
