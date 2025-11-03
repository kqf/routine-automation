from pathlib import Path

import click
from markitdown import MarkItDown


def convert(md_converter, path, ipath, folder):
    result = md_converter.convert(str(path))
    if not result or not hasattr(result, "text_content"):
        click.secho(f"Conversion failed for {path}", fg="red")
        return

    ipath.write_text(result.text_content, encoding="utf-8")
    click.echo(f"{path.relative_to(folder)} -> {ipath.relative_to(folder)}")


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing .md files.",
)
@click.option(
    "--style-map",
    type=str,
    default=None,
    help="Optional style map for docx conversion (e.g. include comments).",
)
def main(directory: Path, overwrite: bool):
    md_converter = MarkItDown()
    for path in directory.rglob("*"):
        if path.suffix.lower() not in {".docx", ".doc"}:
            continue

        opath = path.with_suffix(".md")
        if opath.exists() and not overwrite:
            click.echo(f"Skipping {opath.relative_to(directory)} (exists)")
            continue
        convert(md_converter, path, opath, directory)
    click.secho("\nConversion complete.", fg="green")


if __name__ == "__main__":
    main()
