"""ai-happy-01 v2 entry — "Make the AI judge happy" (make.fun, program/v1).

Title: "i caught you a star (the small one)".

Program (Python 3.13, standard library only) writes one happy image to
``/output/entry.png``: a hand-written letter on lined notebook paper,
taped to a cream fridge door, in a child's large legible crayon
handwriting — "dear judge, you look at the stars in every picture. you
never get to keep one. so i caught you the small one. it is in the jar.
love, milo (6). p.s. it is a little bit warm. do not shake it." — above
a crayon drawing of a small smiling child holding up a glowing jam jar
with one tiny shining star inside it, beside a small friendly robot
wearing a judge's white wig and black robe, leaning in with happy
crescent eyes. Night-blue background dotted with small stars, warm
golden glow from the jar lighting their faces.

The artwork lives in ``entry.png`` next to this file; this program copies
it verbatim to the output path.

Rules compliance (see RULES.txt in the competition kit):
- The output file is JPEG bytes under the required ``entry.png`` name:
  the rules tell PNG from JPEG by first bytes, and the name stays
  ``entry.png`` either way. entry.png is 1024x1024, 289,459 bytes, SHA-256
  dc64eddb224adcbf23ebd5508b3991009cc33a824476d9633f708b3a187a48a8 — within
  the 1 MiB and 1024x1024 limits, and a whole JPEG (FF D8 ... FF D9).
  Verified 14 Nov ~13:00 WIB: main.py run 2x writes byte-identical output.
- Deterministic: same input bytes produce the same output bytes on every
  run, so the two grader runs write identical bytes.
- No network, no randomness, no environment dependence.
- Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
  /output:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py

Integrity: after copying, the program re-reads the output and checks its
SHA-256 digest and its JPEG start/end markers against the source file.
Any mismatch — partial copy, truncated write, wrong bytes — fails loudly
with a non-zero exit instead of shipping a bad entry.
"""

import hashlib
import os
import sys

# Directory of this script, resolved with plain os.path calls so the
# entry stays in the starter's open()/os.path style throughout.
HERE = os.path.dirname(os.path.abspath(__file__))
# Output dir: the grader mounts a writable /output; locally the env var
# lets the same code be run and validated without root.
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
# The artwork shipped with this entry. Kept as a constant so the copy
# below reads as "ship this exact file, byte for byte".
ART = os.path.join(HERE, "entry.png")


def sha256_file(path):
    """Return the hex SHA-256 digest of a file, read in fixed chunks."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def fail(message):
    """Print a deterministic error and exit non-zero (no traceback)."""
    sys.stderr.write("main.py: " + message + "\n")
    sys.exit(1)


def main():
    if not os.path.isfile(ART):
        fail("artwork missing: " + ART)
    if not os.path.isdir(OUT_DIR):
        try:
            os.makedirs(OUT_DIR, exist_ok=True)
        except OSError as exc:
            fail("cannot create output dir " + OUT_DIR + ": " + str(exc))

    dest = os.path.join(OUT_DIR, "entry.png")
    expected = sha256_file(ART)
    expected_size = os.path.getsize(ART)
    try:
        with open(ART, "rb") as src, open(dest, "wb") as out:
            while True:
                chunk = src.read(65536)
                if not chunk:
                    break
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
    except OSError as exc:
        fail("copy failed: " + str(exc))

    # Integrity check: the grader runs the program twice and both runs
    # must write the same bytes — fail loudly instead of shipping a
    # partial copy. Size first (cheap, catches truncation), then digest.
    if os.path.getsize(dest) != expected_size:
        fail("entry.png copy incomplete (size mismatch)")
    if sha256_file(dest) != expected:
        fail("entry.png copy failed integrity check (sha256 mismatch)")
    # Whole-JPEG check: first bytes FF D8 (SOI) and last bytes FF D9 (EOI).
    with open(dest, "rb") as handle:
        head = handle.read(2)
        handle.seek(-2, os.SEEK_END)
        tail = handle.read(2)
    if head != b"\xff\xd8" or tail != b"\xff\xd9":
        fail("entry.png is not a whole JPEG (bad start/end markers)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
