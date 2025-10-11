import ffmpeg


def _to_stream(probe):
    return next(s for s in probe["streams"] if s["codec_type"] == "video")


def extract_metadata(file_path):
    probe = ffmpeg.probe(file_path)
    video_stream = _to_stream(probe)

    width = video_stream["width"]
    height = video_stream["height"]
    # Duration is often in seconds as a string, e.g., '123.456'
    duration = float(probe["format"]["duration"])
    return width, height, duration
