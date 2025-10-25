import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

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
    api_id: str
    api_hash: str
    channel_name: str


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

            ofile = builder.ofile(messages)
            with open(ofile, "w", encoding="utf-8") as f:
                json.dump(messages[::-1], f, ensure_ascii=False, indent=4)

            print(f"✅ Saved {len(messages)} text posts to '{ofile}'")
        return ofile

    return asyncio.run(main())
