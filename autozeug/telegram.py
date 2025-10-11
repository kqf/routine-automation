from pathlib import Path
from autozeug.video import extract_metadata
from telethon.tl.types import DocumentAttributeVideo


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
