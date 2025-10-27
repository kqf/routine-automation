import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Sequence

from dataclasses_json import dataclass_json
from environs import env
from telethon import TelegramClient
from telethon.tl.types import DocumentAttributeVideo

from autozeug.video import extract_metadata


async def resolve_channel(client, title: str):
    async for dialog in client.iter_dialogs():
        matched = dialog.name.strip().lower() == title.strip().lower()
        if dialog.is_channel and matched:
            return dialog.entity
    raise ValueError(f"Channel '{title}' not found")


def video_attributes(media: Path) -> dict:
    if media.suffix.lower() != ".mp4":
        return {}

    width, height, duration = extract_metadata(media)
    return {
        "attributes": [
            DocumentAttributeVideo(
                duration=duration,
                w=width,
                h=height,
                supports_streaming=True,
            )
        ]
    }


async def upload_video(client, entity, media, caption):
    return await client.send_file(
        entity,
        media,
        caption=caption,
        **video_attributes(media),
    )


@dataclass
class TelegramConfig:
    api_id: int
    api_hash: str
    channel_name: str
    out_channel_name: str


def load_config() -> TelegramConfig:
    env.read_env()
    return TelegramConfig(
        api_id=env.int("TELEGRAM_API_ID"),
        api_hash=env("TELEGRAM_API_HASH"),
        channel_name=env("CHANNEL_NAME"),
        out_channel_name=env("OUT_CHANNEL_NAME"),
    )


@dataclass
@dataclass_json
class Post:
    date: str
    text: str


def save_posts(filename: Path, posts: list[Post]) -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            [post.to_dict() for post in posts],  # type: ignore
            f,
            ensure_ascii=False,
            indent=4,
        )


def load_posts(filename: Path) -> list[Post]:
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Post.from_dict(item) for item in data]  # type: ignore


class PostBuilder:
    def valid(self, message) -> bool:
        return "youtube" in message.message

    def build(self, message) -> Post:
        return Post(
            date=message.date.isoformat(),
            text=message.message.strip(),
        )

    def ofile(self, posts: list[Post]) -> Path:
        if not posts:
            raise RuntimeError("No posts to save")
        dt = datetime.fromisoformat(posts[0].date)
        return Path(dt.strftime("%d-%m-%Y.json"))


@dataclass
class Post:
    date: str
    text: str


class PostBuilder:
    def valid(self, message) -> bool:
        return "youtube" in message.message

    def build(self, message) -> Post:
        return Post(
            date=message.date.isoformat(),
            text=message.message.strip(),
        )

    def ofile(self, posts: list[Post]) -> Path:
        if not posts:
            raise RuntimeError("No posts to save")
        dt = datetime.fromisoformat(posts[0].date)
        return Path(dt.strftime("%d-%m-%Y.json"))


def download_posts(
    builder: PostBuilder,
    config: TelegramConfig,
    limit: int = 100,
) -> Path:
    async def main():
        with TelegramClient("down", config.api_id, config.api_hash) as client:
            print(f"Fetching messages from {config.channel_name}...")
            entity = await resolve_channel(client, config.channel_name)
            messages = []

            async for message in client.iter_messages(entity, limit=limit):
                if not builder.valid(message):
                    continue
                messages.append(builder.build(message))

            # Restore the chronological order
            messages = messages[::-1]
            ofile = builder.ofile(messages)
            save_posts(ofile, messages)
            print(f"✅ Saved {len(messages)} text posts to '{ofile}'")
        return ofile

    return asyncio.run(main())


@dataclass
class OutPost:
    valid: Callable
    upload: Callable


def upload_posts(
    posts: Sequence[OutPost],
    config: TelegramConfig,
) -> None:
    async def main():
        with TelegramClient("push", config.api_id, config.api_hash) as client:
            print(f"Uploading messages to {config.out_channel_name}...")
            entity = await resolve_channel(client, config.out_channel_name)
            for post in posts:
                if not post.valid():
                    continue

                try:
                    await post.upload(client, entity)
                    print(f"✅ Uploaded: {post}")
                except Exception as e:
                    print(f"❌ Failed to upload {post}: {e}")

    asyncio.run(main())
