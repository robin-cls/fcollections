"""Auxiliary data lookup an fetch module.

This modules aims at handling the auxiliary data that is needed by a
software, but is not shipped with the binary. It references useful
datasets, looks up for the files and eventually download missing files.

Software may call the class matching their use case and simply get the
file they need. The fetching part will be automatically done by this
module, allowing the caller to only know the dataset purpose and not its
distribution point.
"""

from __future__ import annotations

import argparse
import os
import typing as tp
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, track
from rich.table import Table
from typing_extensions import Annotated

from ._gshhg import GSHHG
from ._interface import IAuxiliaryDataFetcher
from ._karin import KarinFootprints

app = typer.Typer()
console = Console()

__all__ = ["main", "GSHHG", "IAuxiliaryDataFetcher", "KarinFootprints"]


def _defaults(
    preferred_target_folder: Path | None = None,
) -> dict[str, IAuxiliaryDataFetcher]:
    data_list = [
        GSHHG(preferred_target_folder),
        KarinFootprints(preferred_target_folder),
    ]
    return {x.name: x for x in data_list}


@app.command()
def summary():
    """Brief information for auxiliary data availability and look-up
    folders."""
    table = Table()
    for x in ["Type", "Available", "Keys", "Lookup Folders"]:
        table.add_column(x, overflow="fold")

    for name, data in _defaults().items():
        files = [data.file(key).exists() for key in data.keys]
        table.add_row(
            name,
            f"{sum(files)}/{len(files)}",
            ",".join(sorted(data.keys)),
            "\n".join(map(lambda x: x.as_posix(), data.lookup_folders())),
        )
    console.print(table)


@app.command()
def details(
    data_type: Annotated[
        str,
        typer.Argument(
            help="type of the auxiliary data: 'gshhg' or 'karin_footprints'"
        ),
    ],
):
    """Detailed information about a single auxiliary data source."""
    data = _defaults()[data_type]

    table = Table("Keys", "File Name", "Folder", "Present")
    for key in sorted(data.keys):
        file_path = data.file(key)
        table.add_row(
            key, file_path.name, file_path.parent.as_posix(), str(file_path.exists())
        )
    console.print(table)


@app.command()
def download(
    target_folder: Annotated[Path, typer.Argument(help="target folder for download")],
):
    """Download all auxiliary data from remote sources."""
    target_folder.mkdir(parents=True, exist_ok=True)

    datas = _defaults(target_folder).values()
    with Progress() as progress:
        data_task = progress.add_task("[cyan]Processing sources...", total=len(datas))

        for data in datas:
            # Inner task: processing items in each dataset
            key_task = progress.add_task(
                f"[green]Processing keys in {data.name}...", total=len(data.keys)
            )
            for key in data.keys:
                data[key]  # Will trigger a download if not found on local folders
                progress.update(key_task, advance=1)

        progress.remove_task(key_task)
        progress.update(data_task, advance=1)


@app.command()
def env():
    """Display the environment variables used by the program."""
    table = Table("Name", "Value")

    def _folder_status(env_variable: str) -> str:
        if env_variable in os.environ:
            folder = os.environ[env_variable]
            if not os.path.exists(folder):
                folder = f"INVALID -> '{folder}'"
        else:
            folder = "UNSET"

        return folder

    env_variable = "SAD_DATA"
    table.add_row(env_variable, _folder_status(env_variable))
    for name in _defaults().keys():
        env_variable = f"SAD_DATA_{name.upper()}"
        table.add_row(env_variable, _folder_status(env_variable))
    console.print(table)


def main():  # pragma: no cover (not worth testing, we rely on typer/click)
    """Entry point for the auxiliary data handling."""
    app()
