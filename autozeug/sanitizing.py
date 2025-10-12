import re
import unicodedata
from pathlib import Path

import click
from unidecode import unidecode

GERMAN_MAP = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "ß": "ss",
}


def replace_german_chars(text: str) -> str:
    for orig, repl in GERMAN_MAP.items():
        text = text.replace(orig, repl)
    return text


def safe_name(name: str) -> str:
    name = replace_german_chars(name)
    name = unidecode(name)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return name


def avoid_collision(path: Path) -> Path:
    counter = 1
    new_path = path
    while new_path.exists():
        new_path = path.with_stem(f"{path.stem}_{counter}")
        counter += 1
    return new_path


def rename_recursive(root_dir: Path, dry_run: bool):
    for path in sorted(
        root_dir.rglob("*"),
        key=lambda p: len(p.parts),
        reverse=True,
    ):
        safe_filename = safe_name(path.name)
        if safe_filename != path.name:
            new_path = path.with_name(safe_filename)
            new_path = avoid_collision(new_path)
            rel_old = path.relative_to(root_dir)
            rel_new = new_path.relative_to(root_dir)
            click.echo(f"{rel_old} -> {rel_new}")
            if not dry_run:
                path.rename(new_path)


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview changes without renaming files.",
)
def main(directory: Path, dry_run: bool):
    """Recursively sanitize filenames in DIRECTORY."""
    rename_recursive(directory, dry_run)
    if dry_run:
        click.secho("\nDry-run complete. No files were renamed.", fg="yellow")
    else:
        click.secho("\nRenaming complete.", fg="green")


if __name__ == "__main__":
    main()  # type: ignore
