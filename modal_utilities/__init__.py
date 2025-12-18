## imports

__all__ = ["app_function", "refreshed_modal_volumes"]

# standard
import contextlib
import functools
import importlib.metadata
import typing

# custom
import modal


## constants

__version__ = importlib.metadata.version("modal-utilities")


## classes

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])


# adapted from stackoverflow.com/a/59717891
class copy_signature(typing.Generic[F]):
    def __init__(self, target: F) -> None: ...
    def __call__(self, wrapped: typing.Callable[..., typing.Any]) -> F:
        return typing.cast(F, wrapped)


## methods


@contextlib.contextmanager
def refreshed_modal_volumes() -> typing.Generator[list[modal.Volume], None, None]:
    # TODO: the current approach omits any function-specific volumes
    app = modal.App._get_container_app()  # TODO: should be passed directly
    assert app, "Modal App can only be accessed from within Modal container!"

    # TODO: repr is a hacky approach to resolving these volumes
    volumes = list(map(eval, map(repr, app._local_state.volumes_default.values())))

    for volume in volumes:
        volume.reload()

    try:
        yield volumes
    finally:
        for volume in volumes:
            volume.commit()


P = typing.ParamSpec("P")
R = typing.TypeVar("R")


@copy_signature(modal.App.function)
@functools.wraps(modal.App.function)
def app_function(app: modal.App, *function_args, **function_kwargs):
    def decorator(function: typing.Callable[P, R]):
        @modal.App.function(app, *function_args, **function_kwargs)
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with refreshed_modal_volumes():
                return function(*args, **kwargs)

        return wrapper

    return decorator
