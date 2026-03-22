import re


def parse(text):
    """
    Parse plain text into a list of {"name": str, "artist": str} dicts.

    Supported formats (one track per non-empty line):
      - "Artist - Song Title"
      - "Song Title by Artist"
      - "Song Title"  (artist left empty)
    """
    results = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # "Artist - Song Title"
        m = re.match(r"^(.+?)\s+-\s+(.+)$", line)
        if m:
            results.append({"artist": m.group(1).strip(), "name": m.group(2).strip()})
            continue

        # "Song Title by Artist"
        m = re.match(r"^(.+?)\s+by\s+(.+)$", line, re.IGNORECASE)
        if m:
            results.append({"name": m.group(1).strip(), "artist": m.group(2).strip()})
            continue

        # Bare title
        results.append({"name": line, "artist": ""})

    return results
