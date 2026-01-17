## imports

__all__ = [
    "get_volume_configuration",
    "get_volume_mount_paths_by_name",
    "get_primary_volume_name",
    "get_primary_volume",
    "get_configured_volumes",
    "get_volume_secrets",
]

# standard
import base64
import functools
import json
import os
import pathlib
import typing

# custom
import modal


## methods


@functools.cache
def _get_volume_from_configuration(
    *,
    name: str,
    namespace: typing.Optional[typing.Any] = None,
    environment_name: typing.Optional[str] = None,
    create_if_missing: bool = False,
    version: typing.Optional[int] = None,
    client_credentials: typing.Optional[dict[str, str]] = None,
) -> modal.Volume:
    client = None
    if client_credentials:
        client = modal.Client.from_credentials(**client_credentials)
    return modal.Volume.from_name(
        name=name,
        namespace=namespace,
        environment_name=environment_name,
        create_if_missing=create_if_missing,
        version=version,
        client=client,
    )


def get_volume_configuration():
    volume_configurations = dict[str, dict[str, typing.Any]]()

    modal_volume_configuration_path = pathlib.Path(
        os.environ.get("MODAL_VOLUME_CONFIGURATION_PATH", "")
    )
    encoded_modal_volume_configuration = os.environ.get(
        "ENCODED_MODAL_VOLUME_CONFIGURATION"
    )

    if (
        modal_volume_configuration_path.is_file()
        and modal_volume_configuration_path.exists()
    ):
        volume_configurations.update(
            json.loads(modal_volume_configuration_path.read_text())
        )

    if encoded_modal_volume_configuration:
        volume_configurations.update(
            json.loads(
                base64.decodebytes(encoded_modal_volume_configuration.encode()).decode()
            )
        )

    return volume_configurations


def get_volume_mount_paths_by_name() -> dict[str, str]:
    volume_configurations = get_volume_configuration()
    mount_paths_by_name = {
        volume_kwargs["name"]: mount_path
        for mount_path, volume_kwargs in volume_configurations.items()
    }
    return mount_paths_by_name


def get_primary_volume_name() -> str:
    volume_configurations = get_volume_configuration()
    volumes_by_name = {
        volume_kwargs["name"]: _get_volume_from_configuration(**volume_kwargs)
        for volume_kwargs in volume_configurations.values()
    }

    if len(volumes_by_name) == 0:
        raise RuntimeError("No Modal volumes were configured!")

    primary_modal_volume_name = os.environ.get("PRIMARY_MODAL_VOLUME_NAME")
    if primary_modal_volume_name:
        return primary_modal_volume_name

    if len(volumes_by_name) == 1:
        return next(iter(volumes_by_name))

    raise RuntimeError(
        "A primary volume could not be identified!"
        f" Modal Volume configuration:\n{json.dumps(volume_configurations, indent=4)}"
    )


def get_primary_volume() -> modal.Volume:
    volume_configurations = get_volume_configuration()
    volumes_by_name = {
        volume_kwargs["name"]: modal.Volume.from_name(**volume_kwargs)
        for volume_kwargs in volume_configurations.values()
    }
    primary_volume_name = get_primary_volume_name()
    return volumes_by_name[primary_volume_name]


def get_configured_volumes() -> (
    dict[str | pathlib.PurePosixPath, modal.Volume | modal.CloudBucketMount]
):
    volume_configurations = get_volume_configuration()
    volumes_by_mount_path: dict[
        str | pathlib.PurePosixPath, modal.Volume | modal.CloudBucketMount
    ] = {
        mount_path: modal.Volume.from_name(**volume_kwargs)
        for mount_path, volume_kwargs in volume_configurations.items()
    }
    return volumes_by_mount_path


def get_volume_secrets():
    encoded_configuration = base64.encodebytes(
        json.dumps(get_volume_configuration()).encode()
    ).decode()
    return [
        modal.Secret.from_dict(
            {"ENCODED_MODAL_VOLUME_CONFIGURATION": encoded_configuration}
        )
    ]
