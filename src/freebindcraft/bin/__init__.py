"""Entry-point shim for the ``bindcraft`` console script."""

import runpy


def main() -> None:
    """Run BindCraft binder design.

    Delegates to ``freebindcraft.bin.bindcraft`` by executing it as
    ``__main__`` so that all top-level script logic runs exactly as if
    the file had been called with ``python -m freebindcraft.bin.bindcraft``.
    """
    runpy.run_module(
        "freebindcraft.bin.bindcraft",
        run_name="__main__",
        alter_sys=True,
    )
