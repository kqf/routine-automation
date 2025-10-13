from pathlib import Path
import click
from markitdown import MarkItDown


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing .md files.")
@click.option(
    "--style-map",
    type=str,
    default=None,
    help="Optional style map for docx conversion (e.g. include comments).",
)
def main(directory: Path, overwrite: bool, style_map: str):
    """
    Recursively convert all .docx and .doc files in DIRECTORY to Markdown using MarkItDown.
    """
    md_converter = MarkItDown()
    for path in directory.rglob("*"):
        if path.suffix.lower() in [".docx", ".doc"]:
            output_path = path.with_suffix(".md")
            if output_path.exists() and not overwrite:
                click.echo(
                    f"Skipping {output_path.relative_to(directory)} (already exists)"
                )
                continue

            try:
                result = md_converter.convert(str(path))
                if result and hasattr(result, "text_content"):
                    output_path.write_text(result.text_content, encoding="utf-8")
                    click.echo(
                        f"{path.relative_to(directory)} -> {output_path.relative_to(directory)}"
                    )
                else:
                    click.secho(f"Conversion failed for {path}", fg="red")
            except Exception as e:
                click.secho(f"Error converting {path}: {e}", fg="red")

    click.secho("\nConversion complete.", fg="green")


if __name__ == "__main__":
    main()
