"""Commands for using a local-testcontainer for testing."""

from __future__ import annotations

import contextlib
import dataclasses
import json
import pathlib
import pprint
import re
import subprocess
import sys
import time
from typing import Iterator

import click
import filelock
import pydantic
import requests


@click.group()
def main():
    """Start or stop a W&B backend for testing.

    This manages a singleton local-testcontainer Docker process on your system.
    You can start it up manually before running system_tests to speed up the
    setup time; otherwise, any pytest invocation of system_tests that requires
    the local-testcontainer will correctly start up a single instance of it
    and shut it down after.

    This tool is safe for concurrent use. In particular, multiple parallel
    pytest invocations will only start a single container, and the container
    will be kept alive until the last invocation exits.

    NOTE: In certain error conditions, such as if you force-quit a pytest run,
    the local-testcontainer process might not get cleaned up. You may use the
    `release` or `stopall` commands manually to unblock it.
    """


@main.command()
@click.argument("id")
@click.option(
    "--name",
    help="The name for the server.",
    default="wandb-local-testcontainer",
)
@click.option(
    "--hostname",
    help="""The hostname for a running backend (e.g. localhost).

    If provided, then --base-port and --fixture-port are required.
    """,
)
@click.option(
    "--base-port",
    help="The backend's 'base' port (usually 8080).",
    type=int,
)
@click.option(
    "--fixture-port",
    help="The backend's 'fixture' port (usually 9015)",
    type=int,
)
def start(
    id: str,
    name: str,
    hostname: str | None,
    base_port: int | None,
    fixture_port: int | None,
) -> None:
    """Start and/or keep the container running until ID is released.

    The exit code is 0 if the backend starts up and is healthy. Otherwise,
    the exit code is 1.

    The backend is accessible on localhost.

    If --hostname is provided, then the given server is used instead of
    starting a Docker container. This is generally used in CI.

    Prints a JSON dictionary with the following keys:

        base_port: The main port (for GraphQL / FileStream / web UI)
        fixture_port: Port used for test-specific functionalities
    """
    with _info_file() as info:
        if hostname:
            if not base_port:
                raise AssertionError("--base-port required")
            if not fixture_port:
                raise AssertionError("--fixture-port required")

            server = _start_external(
                info,
                name=name,
                hostname=hostname,
                base_port=base_port,
                fixture_port=fixture_port,
            )
        else:
            server = _start_managed(info, name=name)

        server.ids.append(id)
        click.echo(
            json.dumps(
                {
                    "base_port": server.base_port,
                    "fixture_port": server.fixture_port,
                }
            )
        )


def _start_external(
    info: _InfoFile,
    name: str,
    hostname: str,
    base_port: int,
    fixture_port: int,
) -> _ServerInfo:
    server = info.servers.get(name)

    if server:
        if not server.hostname == hostname:
            _echo_bad(f"Already running on hostname {server.hostname}.")
            sys.exit(1)
        if not server.base_port == base_port:
            _echo_bad(f"Already running with base port {server.base_port}.")
            sys.exit(1)
        if not server.fixture_port == fixture_port:
            _echo_bad(f"Already running with fixture port {server.fixture_port}.")
            sys.exit(1)
    else:
        server = _ServerInfo(
            managed=False,
            ids=[],
            hostname=hostname,
            base_port=base_port,
            fixture_port=fixture_port,
        )
        info.servers[name] = server

    app_health_url = f"http://{hostname}:{base_port}/healthz"
    fixture_health_url = f"http://{hostname}:{fixture_port}/health"  # no z

    if not _check_health(app_health_url, timeout=30):
        _echo_bad(f"{app_health_url} did not respond HTTP 200.")
        sys.exit(1)

    if not _check_health(fixture_health_url, timeout=30):
        _echo_bad(f"{fixture_health_url} did not respond HTTP 200.")
        sys.exit(1)

    _echo_good("Server is healthy!")
    return server


def _start_managed(info: _InfoFile, name: str) -> _ServerInfo:
    server = info.servers.get(name)

    if server:
        _start_check_existing_server(server)
    else:
        server = _start_new_server(info, name=name)

    return server


def _start_check_existing_server(server: _ServerInfo) -> None:
    if _check_health(f"http://localhost:{server.base_port}/healthz"):
        _echo_good("Server is running.")
    else:
        _echo_bad("Server is not healthy.")
        sys.exit(1)


def _start_new_server(info: _InfoFile, name: str) -> _ServerInfo:
    server = _ServerInfo(
        managed=True,
        hostname="localhost",
        base_port=0,
        fixture_port=0,
        ids=[],
    )

    _start_container(name=name).apply_ports(server)

    if not _check_health(
        f"http://localhost:{server.base_port}/healthz",
        timeout=30,
    ):
        _echo_bad("Server did not become healthy in time (base).")
        sys.exit(1)

    if not _check_health(
        f"http://localhost:{server.fixture_port}/health",
        timeout=30,
    ):
        _echo_bad("Server did not become healthy in time (fixtures).")
        sys.exit(1)

    _echo_good("Server is up and healthy!")

    info.servers[name] = server
    return server


@main.command()
@click.argument("id")
@click.option(
    "--name",
    help="The server name used in the 'start' command.",
    default="wandb-local-testcontainer",
)
def release(id: str, name: str) -> None:
    """Release ID, stopping the container if no more IDs remain."""
    with _info_file() as info:
        server = info.servers.get(name)

        if not server:
            _echo_bad(f"Server {name} is not running.")
            sys.exit(1)

        if id not in server.ids:
            _echo_bad(f"ID {id} was not in the list.")
            sys.exit(1)

        server.ids.remove(id)

        if server.ids:
            _echo_good(f"Removed {id}. {len(server.ids)} left.")
            return

        _stop_container(name)
        del info.servers[name]
        _echo_good(f"Shut down {name}!")


@main.command()
def stopall() -> None:
    """Stops all servers, disregarding any IDs still using them."""
    with _info_file() as info:
        for name, server in info.servers.items():
            if server.managed:
                _stop_container(name)

        info.servers.clear()
        _echo_good("Shut down local-test-container!")


@main.command(name="print-debug")
def print_debug() -> None:
    """Dump information for debugging this script."""
    with _info_file() as info:
        _echo_info(pprint.pformat(info))


def _resources(suffix: str) -> pathlib.Path:
    return pathlib.Path(__file__).with_suffix(suffix)


@contextlib.contextmanager
def _info_file() -> Iterator[_InfoFile]:
    with filelock.FileLock(_resources(".state.lock")):
        with open(_resources(".state"), "a+") as f:
            f.seek(0)
            content = f.read()

            if content:
                try:
                    state = _InfoFile.model_validate_json(content)
                except Exception as e:
                    _echo_bad(f"Couldn't parse state file; remaking it: {e}")
                    state = _InfoFile()
            else:
                state = _InfoFile()

            yield state

            f.truncate(0)
            f.write(state.model_dump_json())


class _InfoFile(pydantic.BaseModel):
    servers: dict[str, _ServerInfo] = {}
    """Map from server names to information about them."""


class _ServerInfo(pydantic.BaseModel):
    managed: bool
    """Whether this script started the server or just connected to it."""

    ids: list[str]
    """IDs of processes that are preventing us from killing the server."""

    hostname: str
    """The server's address, e.g. 'localhost'."""

    base_port: int
    """The exposed 'base' port, used for GraphQL and FileStream APIs."""

    fixture_port: int
    """The exposed 'fixture' port, used for test-related functionalities."""


def _check_health(health_url: str, timeout: int = 1) -> bool:
    """Returns True if the URL responds with HTTP 200 within a timeout.

    Args:
        health_url: The URL to which to make GET requests.
        timeout: The timeout in seconds after which to give up.
    """
    start_time = time.monotonic()

    _echo_info(
        f"Waiting up to {timeout} second(s)"
        f" until {health_url} responds with HTTP 200."
    )

    while True:
        try:
            response = requests.get(health_url)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass

        if time.monotonic() - start_time >= timeout:
            return False

        time.sleep(1)


@dataclasses.dataclass(frozen=True)
class _WandbContainerPorts:
    base_port: int
    fixture_port: int

    def apply_ports(self, server: _ServerInfo) -> None:
        server.base_port = self.base_port
        server.fixture_port = self.fixture_port


def _start_container(
    *,
    name: str,
    clean_up: bool = True,
) -> _WandbContainerPorts:
    """Start the local-testcontainer.

    This issues the `docker run` command and returns immediately.

    Args:
        name: The container name to use.
        clean_up: Whether to remove the container and its volumes on exit.
            Passes the --rm option to docker run.
    """
    docker_flags = [
        "--detach",
        *["-e", "WANDB_ENABLE_TEST_CONTAINER=true"],
        *["--name", name],
        *["--volume", f"{name}-vol:/vol"],
        # Expose ports to the host.
        *["--publish", "8080"],  # base port
        *["--publish", "9015"],  # fixture port
        # Only this platform is available for now. Without specifying it,
        # Docker defaults to the host's platform and fails if it's not
        # supported.
        *["--platform", "linux/amd64"],
    ]

    if clean_up:
        docker_flags.append("--rm")

    image = (
        "us-central1-docker.pkg.dev"
        "/wandb-production/images/local-testcontainer"
        ":master"
    )

    subprocess.check_call(
        ["docker", "run", *docker_flags, image],
        stdout=sys.stderr,
    )

    ports_str = subprocess.check_output(["docker", "port", name]).decode()

    port_line_re = re.compile(r"(\d+)(\/\w+)? -> [^:]*:(\d+)")
    base_port = 0
    fixture_port = 0
    for line in ports_str.splitlines():
        match = port_line_re.fullmatch(line)
        if not match:
            continue

        internal_port = match.group(1)
        external_port = match.group(3)

        if internal_port == "8080":
            base_port = int(external_port)
        elif internal_port == "9015":
            fixture_port = int(external_port)

    if not base_port:
        raise AssertionError(f"Couldn't determine W&B base port: {ports_str}")
    if not fixture_port:
        raise AssertionError(f"Couldn't determine W&B fixture port: {ports_str}")

    return _WandbContainerPorts(
        base_port=base_port,
        fixture_port=fixture_port,
    )


def _stop_container(name: str) -> None:
    subprocess.check_call(["docker", "rm", "-f", name], stdout=sys.stderr)


def _echo_good(msg: str) -> None:
    msg = click.style(msg, fg="green")
    prefix = click.style("local_wandb_server.py", bold=True)
    click.echo(f"{prefix}: {msg}", err=True)


def _echo_info(msg: str) -> None:
    prefix = click.style("local_wandb_server.py", bold=True)
    click.echo(f"{prefix}: {msg}", err=True)


def _echo_bad(msg: str) -> None:
    msg = click.style(msg, fg="red")
    prefix = click.style("local_wandb_server.py", bold=True)
    click.echo(f"{prefix}: {msg}", err=True)


if __name__ == "__main__":
    main()
