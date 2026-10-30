"""python3 test_scan.py — incremental scan re-parses only changed files and stays equal to a full scan."""
import json, os, tempfile, time
from pathlib import Path

import scan as dex

OPENERS = dex.load_base(Path(__file__).parent / "openers.json")
PHRASE = OPENERS[0]["phrase"]


def line(text):
    return json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}) + "\n"


def main():
    parsed = []
    real = dex.iter_assistant_lines
    dex.iter_assistant_lines = lambda p, **kw: (parsed.append(p), real(p, **kw))[1]
    with tempfile.TemporaryDirectory() as d:
        for i in range(3):
            Path(d, f"s{i}.jsonl").write_text(line(f"{PHRASE} — first"))
        cache = {}
        c1, files, _ = dex.scan(OPENERS, [d], [], cache)
        assert files == 3 and c1[PHRASE] == 3 and len(parsed) == 3, (files, c1[PHRASE], parsed)

        parsed.clear()
        c2, _, _ = dex.scan(OPENERS, [d], [], cache)
        assert parsed == [] and c2 == c1, parsed  # unchanged files are not re-read

        f = Path(d, "s1.jsonl")
        with f.open("a") as fh:
            fh.write(line(f"{PHRASE} — again"))
        os.utime(f, ns=(time.time_ns(), time.time_ns() + 10**9))
        Path(d, "s2.jsonl").unlink()
        parsed.clear()
        c3, files, blocks = dex.scan(OPENERS, [d], [], cache)
        assert parsed == [str(f)] and files == 2 == len(cache) and c3[PHRASE] == 3, (parsed, files, c3[PHRASE])
        assert (c3, files, blocks) == dex.scan(OPENERS, [d], [])  # equals a cold full scan

        c4, _, _ = dex.scan(OPENERS[1:], [d], [], cache)  # opener set changed: no stale entries
        assert PHRASE not in c4 and c4 == dex.scan(OPENERS[1:], [d], [])[0]

        f.chmod(0)  # unreadable once: must not be cached as empty
        os.utime(f, ns=(time.time_ns(), time.time_ns() + 2 * 10**9))
        assert dex.scan(OPENERS, [d], [], cache)[0][PHRASE] == 1
        f.chmod(0o644)
        assert dex.scan(OPENERS, [d], [], cache)[0][PHRASE] == 3
    print("ok")


if __name__ == "__main__":
    main()
