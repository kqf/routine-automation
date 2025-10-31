import re
from dataclasses import dataclass
from pathlib import Path

from autozeug.telegram import (
    Post,
    PostBuilder,
    load_config,
    load_posts,
    pull_posts,
    push_posts,
)
from autozeug.video import download_from_youtube, video_exists_and_valid


@dataclass
class OutPost:
    youid: str
    date: str
    text: str
    link: str
    video: Path


def find_youtube_links(text: str) -> list[str]:
    youtube_regex = (
        r"(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/(?:[\w\-\?&=/%#\.]+))"
    )
    return re.findall(youtube_regex, text)


def extrac_youtube_id(url: str) -> str:
    patterns = [
        r"youtube\.com/watch\?v=([A-Za-z0-9_\-]+)",
        r"youtube\.com/live/([A-Za-z0-9_\-]+)",
        r"youtu\.be/([A-Za-z0-9_\-]+)",
    ]
    for pattern in patterns:
        if match := re.search(pattern, url):
            return match[1]
    return url


def extract_posts(posts: list[Post], course: Path) -> dict[str, OutPost]:
    outposts: dict[str, OutPost] = {}
    for post in posts:
        for link in find_youtube_links(post.text):
            youid = extrac_youtube_id(link)
            if youid in outposts:
                continue
            outposts[youid] = OutPost(
                youid=youid,
                date=post.date,
                text=post.text,
                link=link,
                video=course / f"{youid}.mp4",
            )
    return outposts


def dowload_videos(posts: dict[str, OutPost]):
    for post in posts.values():
        if not video_exists_and_valid(post.video):
            download_from_youtube(post.video, post.link)


def main():
    config = load_config()
    cachefile = pull_posts(builder=PostBuilder(), config=config)
    original = load_posts(cachefile)
    posts = extract_posts(original, cachefile.with_suffix(""))
    dowload_videos(posts)
    push_posts(posts.values(), config=config)


if __name__ == "__main__":
    main()
