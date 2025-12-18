## imports

__all__ = ["app_function", "patch_modal_app", "refreshed_modal_volumes"]

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
def refreshed_modal_volumes(
    app: typing.Optional[modal.App] = None,
    function: typing.Optional[modal.Function] = None,
) -> typing.Generator[list[modal.Volume], None, None]:
    if function:
        volumes_by_mount = function.spec.volumes
    else:
        app = app or modal.App._get_container_app()
        assert app, "Modal App can only be accessed from within Modal container!"

        volumes_by_mount = app._local_state.volumes_default

    # TODO: repr is a hacky approach to resolving these volumes
    volumes = list(map(eval, map(repr, volumes_by_mount.values())))

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
            with refreshed_modal_volumes(function=wrapper):
                return function(*args, **kwargs)

        return wrapper

    return decorator


def patch_modal_app(app: modal.App) -> modal.App:
    original_function_decorator = app.function

    @copy_signature(original_function_decorator)
    @functools.wraps(original_function_decorator)
    def patched_function_decorator(*function_args, **function_kwargs):
        return app_function(app, *function_args, **function_kwargs)

    app.function = patched_function_decorator
    return app
