import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import click

from autozeug.telegram import load_config, push


def clean_caption(text: str) -> str:
    # Replace tabs and multiple spaces with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n+", "\n", text)
    # Strip leading/trailing whitespace on each line
    text = "\n".join(line.strip() for line in text.splitlines())
    return text


@dataclass
class MediaPost:
    name: str
    full_name: str
    caption: str = ""
    media: Optional[Path] = None

    def __post_init__(self):
        self.caption = f"**{self.name}**\n{clean_caption(self.caption)}"

    def __repr__(self):
        return (
            f"***\n{self.full_name}\n"
            f"Title: {self.name}\n"
            f"Media: {self.media}\n==="
        )

    def to_dict(self):
        return {
            "name": self.name,
            "full_name": self.full_name,
            "caption": self.caption,
            "media": str(self.media) if self.media else None,
        }


def nsort(s: str):
    splt = re.split(r"(\d+)", s)
    return [int(text) if text.isdigit() else text.lower() for text in splt]


def is_media_file(f: Path) -> bool:
    return f.suffix.lower() == ".mp4"


def is_description_file(f: Path) -> bool:
    return f.suffix.lower() == ".md"


def is_ignored_file(f: Path) -> bool:
    return f.suffix.lower() in (".docx", ".DS_Store")


def collect_subfolders(root: Path) -> List[Path]:
    stack = [root]
    folders: List[Path] = []

    while stack:
        folder = stack.pop()
        folders.append(folder)
        subfolders = sorted(
            [f for f in folder.iterdir() if f.is_dir()],
            reverse=True,
        )
        stack.extend(subfolders)

    return folders


def process_folder(
    folder: Path,
    parent_name: str,
    is_media: Callable[[Path], bool] = is_media_file,
    is_text: Callable[[Path], bool] = is_description_file,
    is_ignore: Callable[[Path], bool] = is_ignored_file,
) -> List[MediaPost]:
    prefix = f"{parent_name} / {folder.name}" if parent_name else folder.name
    files = sorted(
        [f for f in folder.iterdir() if f.is_file() and not is_ignore(f)],
    )
    if media_files := [f for f in files if is_media(f)]:
        captions = [f for f in files if is_text(f)]
        return [
            MediaPost(
                caption=captions[0].read_text(encoding="utf-8")
                if captions
                else "",
                name=folder.stem,
                full_name=f"{prefix} / {mf.stem}",
                media=mf,
            )
            for mf in media_files
        ]

    return [
        MediaPost(
            caption=f.read_text(encoding="utf-8") if is_text(f) else f.stem,
            name=f.stem,
            full_name=f"{prefix} / {f.stem}",
            media=None if is_text(f) else f,
        )
        for f in files
    ]


def prepare_posts(root: Path) -> List[MediaPost]:
    posts: List[MediaPost] = []
    folders = collect_subfolders(root)
    for folder in folders:
        parent = str(folder.parent.relative_to(root)) if folder != root else ""
        posts.extend(process_folder(folder, parent))

    posts.sort(
        key=lambda p: (len(Path(p.full_name).parts), nsort(p.full_name)),
    )
    return [MediaPost("Outline", "")] + posts


@click.command()
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, path_type=Path)
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Only print posts",
    default=False,
)
def main(directory: Path, dry_run: bool):
    config = load_config()
    posts = prepare_posts(directory)
    push(
        posts,  # type: ignore
        config,
        # dry_run=dry_run, # noqa
    )


if __name__ == "__main__":
    main()
