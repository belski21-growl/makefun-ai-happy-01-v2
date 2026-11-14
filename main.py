"""Ship the bundled artwork to the grader's output directory.

The repository carries one file, ``entry.png`` (JPEG bytes under that
name), and this program's whole job is to place an exact copy of it at
``<MAKEFUN_OUTPUT_DIR>/entry.png``.  Nothing is drawn or generated
here: the bytes that leave are the bytes that arrived, vetted three
ways (size, SHA-256, JPEG start/end markers) so a truncated or swapped
file can never slip through quietly.

Run it twice and the two outputs are identical.  Point the output
directory at the repository itself and it refuses instead of
clobbering its own source.
"""

import hashlib
import os
import sys

SOURCE_NAME = "entry.png"
MAX_BYTES = 1048576
CHUNK = 65536
JPEG_START = b"\xff\xd8"
JPEG_END = b"\xff\xd9"


def die(reason):
    """Complain once on stderr and stop with a failure."""
    sys.stderr.write("copy-artwork: " + reason + "\n")
    return 1


def where_we_live():
    """Directory holding this file (and therefore the artwork)."""
    return os.path.dirname(os.path.abspath(__file__))


def where_it_goes():
    """Output directory, from the environment, else /output."""
    chosen = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    if not chosen:
        return "/output"
    return chosen


def fingerprint(blob):
    """Return (size, sha256 hex) for one in-memory byte string."""
    return len(blob), hashlib.sha256(blob).hexdigest()


def looks_like_jpeg(blob):
    """True when blob opens and closes with the JPEG markers."""
    return blob[:2] == JPEG_START and blob[-2:] == JPEG_END


def load_artwork(path):
    """Read the bundled artwork and vet it before anything is written."""
    if not os.path.isfile(path):
        return None, "artwork not found: " + path
    with open(path, "rb") as handle:
        blob = handle.read()
    size, digest = fingerprint(blob)
    if size == 0:
        return None, "artwork is empty: " + path
    if size > MAX_BYTES:
        return None, "artwork over the 1 MiB cap: %d bytes" % size
    if not looks_like_jpeg(blob):
        return None, "artwork is not a whole JPEG (bad markers)"
    return (blob, size, digest), None


def write_out(blob, target):
    """Write blob to target in chunks, then confirm what landed."""
    with open(target, "wb") as handle:
        offset = 0
        while offset < len(blob):
            handle.write(blob[offset:offset + CHUNK])
            offset += CHUNK
        handle.flush()
        os.fsync(handle.fileno())
    with open(target, "rb") as handle:
        landed = handle.read()
    if len(landed) != len(blob):
        return "wrote %d bytes, expected %d" % (len(landed), len(blob))
    if fingerprint(landed)[1] != fingerprint(blob)[1]:
        return "written bytes fail the SHA-256 check"
    if not looks_like_jpeg(landed):
        return "written file is not a whole JPEG (bad markers)"
    return None


def run():
    """Copy the artwork to the output directory, verified end to end."""
    home = where_we_live()
    source = os.path.join(home, SOURCE_NAME)
    out_dir = where_it_goes()
    target = os.path.join(out_dir, SOURCE_NAME)

    if os.path.realpath(target) == os.path.realpath(source):
        return die("refusing: destination is the artwork itself: " + target)
    if not os.path.isdir(out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
        except OSError as exc:
            return die(
                "cannot create output directory " + out_dir + ": " + str(exc)
            )

    packed, problem = load_artwork(source)
    if problem is not None:
        return die(problem)
    blob, size, digest = packed

    trouble = write_out(blob, target)
    if trouble is not None:
        return die(trouble)

    sys.stdout.write("entry.png: %d bytes, sha256 %s\n" % (size, digest))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
