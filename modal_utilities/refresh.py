## imports

__all__ = ["app_function", "patch_modal_app", "refreshed_modal_volumes"]

# standard
import contextlib
import functools
import json
import os
import typing

# custom
import modal


## constants

VOLUME_ENV_KEY = "MODAL_DYNAMIC_VOLUME_CONFIG"


## classes

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])
T = typing.TypeVar("T", bound=type)


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
    reload_all_mounts=False,
) -> typing.Generator[list[modal.Volume], None, None]:
    if reload_all_mounts:
        # TODO: secrets approach creates new container each invocation
        if volume_configuration := os.environ.get(VOLUME_ENV_KEY):
            configured_volumes = json.loads(volume_configuration)
            all_volumes = list(map(modal.Volume.from_name, configured_volumes.values()))
        else:
            # TODO: this approach slows with each additional user/volume
            all_volumes = typing.cast(list[modal.Volume], modal.Volume.objects.list())

        volumes = list[modal.Volume]()
        for volume in all_volumes:
            try:
                volume.reload()
                volumes.append(volume)
            except modal.exception.NotFoundError:
                pass
            except RuntimeError as error:
                if "not attached" in str(error):
                    pass
                else:
                    raise

    else:
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
def app_function(app: modal.App, *configuration_args, **configuration_kwargs):
    def decorator(function: typing.Callable[P, R]):
        @modal.App.function(app, *configuration_args, **configuration_kwargs)
        @functools.wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with refreshed_modal_volumes(function=wrapper):
                return function(*args, **kwargs)

        return wrapper

    return decorator


@copy_signature(modal.App.cls)
@functools.wraps(modal.App.cls)
def app_cls(app: modal.App, *configuration_args, **configuration_kwargs):
    def class_decorator(cls: typing.Type[T]) -> typing.Type[T]:
        def decorator(function: typing.Callable[P, R]):
            @modal.method()
            @functools.wraps(function)
            def wrapper(self, *args: P.args, **kwargs: P.kwargs) -> R:
                with refreshed_modal_volumes(reload_all_mounts=True):
                    return function(self, *args, **kwargs)  # type: ignore

            return wrapper

        for attr_name, attr in cls.__dict__.items():  # type: ignore
            if callable(attr) and not attr_name.startswith("__"):
                setattr(cls, attr_name, decorator(attr))

        return modal.App.cls(app, *configuration_args, **configuration_kwargs)(cls)

    return class_decorator


def patch_modal_app(app: modal.App) -> modal.App:
    original_cls_decorator = app.cls
    original_function_decorator = app.function

    @copy_signature(original_cls_decorator)
    @functools.wraps(original_cls_decorator)
    def patched_cls_decorator(*configuration_args, **configuration_kwargs):
        return app_cls(app, *configuration_args, **configuration_kwargs)

    @copy_signature(original_function_decorator)
    @functools.wraps(original_function_decorator)
    def patched_function_decorator(*configuration_args, **configuration_kwargs):
        return app_function(app, *configuration_args, **configuration_kwargs)

    app.cls = patched_cls_decorator
    app.function = patched_function_decorator
    return app
