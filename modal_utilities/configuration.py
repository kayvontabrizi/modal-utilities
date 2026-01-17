## imports

__all__ = ["collect_configuration_arguments", "get_configured_modal_function"]

# standard
import json
import pathlib
import typing

# custom
import modal

# local
from . import volumes as modal_utilities_volumes


## classes


class ModalConfigurationArguments(typing.TypedDict, total=False):
    cpu: float | tuple[float, float]
    memory: int | tuple[int, int]
    gpu: str | modal.gpu._GPUConfig
    env: dict[str, str | None]
    secrets: typing.Collection[modal.Secret]
    volumes: dict[str | pathlib.PurePosixPath, modal.Volume | modal.CloudBucketMount]
    retries: int | modal.Retries
    max_containers: int
    buffer_containers: int
    scaledown_window: int
    timeout: int
    region: str | typing.Sequence[str]
    cloud: str
    concurrency_limit: int
    container_idle_timeout: int
    allow_concurrent_inputs: int


## methods


def parse_cpu(value: str | None) -> float | tuple[float, float] | None:
    if value is None:
        return None
    if "," in value:
        parts = value.split(",")
        return (float(parts[0]), float(parts[1]))
    return float(value)


def parse_memory(value: str | None) -> int | tuple[int, int] | None:
    if value is None:
        return None
    if "," in value:
        parts = value.split(",")
        return (int(parts[0]), int(parts[1]))
    return int(value)


def parse_gpu(value: str | None) -> str | modal.gpu._GPUConfig | None:
    if value is None:
        return None
    return value


def parse_environment_variables(
    values: list[str] | None,
) -> dict[str, str | None] | None:
    if not values:
        return None
    environment = {}
    for item in values:
        if "=" in item:
            key, value = item.split("=", 1)
            environment[key] = value
        else:
            environment[item] = None
    return environment


def parse_secrets(
    values: list[str] | None,
) -> typing.Collection[modal.Secret] | None:
    if not values:
        return None
    return [modal.Secret.from_name(name) for name in values]


def parse_volumes(
    values: list[str] | None,
) -> dict[str | pathlib.PurePosixPath, modal.Volume | modal.CloudBucketMount]:
    if not values:
        return {}
    volumes = {}
    for item in values:
        if ":" in item:
            volume_name, mount_path = item.split(":", 1)
            volumes[mount_path] = modal.Volume.from_name(volume_name)
    return volumes


def parse_retries(value: str | None) -> int | modal.Retries | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        config = json.loads(value)
        return modal.Retries(**config)


def parse_region(values: list[str] | None) -> str | typing.Sequence[str] | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return values


def collect_configuration_arguments(parameters: dict[str, typing.Any]):
    parsers = {
        "cpu": parse_cpu,
        "memory": parse_memory,
        "gpu": parse_gpu,
        "env": parse_environment_variables,
        "secrets": parse_secrets,
        "volumes": parse_volumes,
        "retries": parse_retries,
        "max_containers": None,
        "buffer_containers": None,
        "scaledown_window": None,
        "timeout": None,
        "region": parse_region,
        "cloud": None,
        "concurrency_limit": None,
        "container_idle_timeout": None,
        "allow_concurrent_inputs": None,
    }
    collected_arguments = {
        key: (parser or (lambda x: x))(parameters[key])
        for key, parser in parsers.items()
        if key in parameters
    }
    return ModalConfigurationArguments(
        **{
            key: value
            for key, value in collected_arguments.items()
            if value is not None and value != {}
        }  # type: ignore
    )


def preset_modal_configuration(arguments: ModalConfigurationArguments):
    secrets = [secret for secret in arguments.get("secrets", [])]
    secrets.extend(modal_utilities_volumes.get_volume_secrets())
    provided_volumes = {k: v for k, v in arguments.get("volumes", {}).items()}
    required_volumes = modal_utilities_volumes.get_configured_volumes()
    volumes = dict[str | pathlib.PurePosixPath, modal.Volume | modal.CloudBucketMount]()
    for mount_path, volume in provided_volumes.items():
        if volume in required_volumes.values():
            continue
        if isinstance(volume, modal.Volume):
            volume = volume.read_only()
        else:
            raise NotImplementedError(
                f'Volumes of the type "{type(volume)}" are not supported'
            )
        volumes[mount_path] = volume
    volumes.update(required_volumes)
    arguments["secrets"] = secrets
    arguments["volumes"] = volumes


def get_configured_modal_function(
    app_name: str,
    class_name: str,
    function_name: str,
    parameters: dict[str, typing.Any],
    pre_configure=True,
) -> modal.Function:
    configuation_kwargs = collect_configuration_arguments(parameters)
    if pre_configure:
        preset_modal_configuration(configuation_kwargs)
    ModalClass = modal.Cls.from_name(app_name, class_name)
    ConfiguredModalClass = ModalClass.with_options(**configuation_kwargs)
    modal_function = getattr(ConfiguredModalClass(), function_name)
    return modal_function
