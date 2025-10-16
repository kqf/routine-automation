import asyncio
import json
from dataclasses import dataclass
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


def download_posts(
    config: TelegramConfig,
    output_file: str = "15-09-2025.json",
    limit: int = 100,
):
    if Path(output_file).exists():
        return output_file

    client = TelegramClient("downloader", config.api_id, config.api_hash)

    async def main():
        client.start()
        print(f"Fetching messages from {config.channel_name}...")
        entity = await resolve_channel(client, config.channel_name)
        messages = []

        async for message in client.iter_messages(entity, limit=limit):
            if message.message:
                if "youtube" not in message.message:
                    continue

                messages.append(
                    {
                        "date": message.date.isoformat(),
                        "text": message.message.strip(),
                        "course": Path(output_file).stem,
                    }
                )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(messages[::-1], f, ensure_ascii=False, indent=4)

        print(f"✅ Saved {len(messages)} text posts to '{output_file}'")

    asyncio.run(main())
    return output_file
