from pathlib import Path
import ffmpeg
from telethon.tl.types import DocumentAttributeVideo


async def resolve_channel(client, channel_title: str):
    async for dialog in client.iter_dialogs():
        if (
            dialog.is_channel
            and dialog.name.strip().lower() == channel_title.strip().lower()
        ):
            return dialog.entity
    raise ValueError(f"Channel '{channel_title}' not found")


def get_video_metadata(file_path):
    probe = ffmpeg.probe(file_path)
    video_stream = next(s for s in probe["streams"] if s["codec_type"] == "video")

    width = video_stream["width"]
    height = video_stream["height"]
    # Duration is often in seconds as a string, e.g., '123.456'
    duration = float(probe["format"]["duration"])

    return width, height, duration


def additional_args(media: Path) -> dict:
    if media.suffix.lower() != ".mp4":
        return {}
    width, height, duration = get_video_metadata(media)
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
        **additional_args(media),
    )
