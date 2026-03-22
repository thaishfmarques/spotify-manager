import csv
import io


def export_playlist(tracks):
    """Return a CSV string for the given list of track dicts."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "artist", "album", "duration_ms", "uri"])
    for t in tracks:
        writer.writerow([t["name"], t["artist"], t["album"], t["duration_ms"], t["uri"]])
    return output.getvalue()
