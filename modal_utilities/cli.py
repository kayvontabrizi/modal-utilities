## imports

# standard
import typing

# custom
import typer


## constants

CPU = typing.Annotated[
    str | None,
    typer.Option(
        "--cpu",
        help="CPU cores to request. Single float (e.g., '4.0') or 'min,max' tuple (e.g., '1.0,4.0'). Default: 0.125 cores.",
    ),
]

Memory = typing.Annotated[
    str | None,
    typer.Option(
        "--memory",
        help="Memory in MiB. Single int (e.g., '1024') or 'min,max' tuple (e.g., '1024,2048'). Default: 128 MiB.",
    ),
]

GPU = typing.Annotated[
    str | None,
    typer.Option(
        "--gpu",
        help="GPU type: 'T4', 'L4', 'A10', 'L40S', 'A100-40GB', 'A100-80GB', 'H100', 'H100!', 'H200', 'B200'.",
    ),
]

Environment = typing.Annotated[
    list[str] | None,
    typer.Option(
        "--env",
        "-e",
        help="Environment variables as 'KEY=value'. Can be specified multiple times.",
    ),
]

Secrets = typing.Annotated[
    list[str] | None,
    typer.Option(
        "--secret",
        "-s",
        help="Modal secret names to inject. Can be specified multiple times.",
    ),
]

Volumes = typing.Annotated[
    list[str] | None,
    typer.Option(
        "--volume",
        "-v",
        help="Volume mounts as 'volume_name=mount_path'. Can be specified multiple times.",
    ),
]

Retries = typing.Annotated[
    str | None,
    typer.Option(
        "--retries",
        help='Retry count (int) or JSON config: \'{"max_retries": 3, "backoff_coefficient": 2.0, "initial_delay": 1.0, "max_delay": 60.0}\'.',
    ),
]

MaxContainers = typing.Annotated[
    int | None,
    typer.Option(
        "--max-containers",
        help="Maximum concurrent containers.",
    ),
]

BufferContainers = typing.Annotated[
    int | None,
    typer.Option(
        "--buffer-containers",
        help="Additional idle containers to maintain under load for reduced latency.",
    ),
]

ScaledownWindow = typing.Annotated[
    int | None,
    typer.Option(
        "--scaledown-window",
        help="Maximum idle time (seconds) before container shutdown during scale-down.",
    ),
]

Timeout = typing.Annotated[
    int | None,
    typer.Option(
        "--timeout",
        help="Maximum execution time in seconds. Default: 300 (5 minutes).",
    ),
]

Region = typing.Annotated[
    list[str] | None,
    typer.Option(
        "--region",
        help="Cloud region(s): 'us', 'us-east', 'eu-west', 'ap-northeast-1', etc. Can be specified multiple times.",
    ),
]

Cloud = typing.Annotated[
    str | None,
    typer.Option(
        "--cloud",
        help="Cloud provider: 'aws', 'gcp', 'oci', or 'auto'.",
    ),
]

ConcurrencyLimit = typing.Annotated[
    int | None,
    typer.Option(
        "--concurrency-limit",
        help="[DEPRECATED: use --max-containers] Maximum concurrent containers.",
        hidden=True,
    ),
]

ContainerIdleTimeout = typing.Annotated[
    int | None,
    typer.Option(
        "--container-idle-timeout",
        help="[DEPRECATED: use --scaledown-window] Container idle timeout in seconds.",
        hidden=True,
    ),
]

AllowConcurrentInputs = typing.Annotated[
    int | None,
    typer.Option(
        "--allow-concurrent-inputs",
        help="[DEPRECATED: use @modal.concurrent decorator] Concurrent inputs per container.",
        hidden=True,
    ),
]

MaxInputs = typing.Annotated[
    int | None,
    typer.Option(
        "--max-inputs",
        help="Maximum concurrent inputs per container. Omit for no concurrency.",
    ),
]

TargetInputs = typing.Annotated[
    int | None,
    typer.Option(
        "--target-inputs",
        help="Target concurrent inputs for autoscaling. Containers burst to max-inputs during scaleup.",
    ),
]

MaxBatchSize = typing.Annotated[
    int | None,
    typer.Option(
        "--max-batch-size",
        help="Maximum inputs combined into a single batch for batched functions.",
    ),
]

WaitMs = typing.Annotated[
    int | None,
    typer.Option(
        "--wait-ms",
        help="Maximum wait time (ms) after first input before executing an unfilled batch.",
    ),
]
