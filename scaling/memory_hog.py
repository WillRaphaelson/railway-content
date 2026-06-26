"""Allocate memory in steady increments until the platform kills the process.

A deliberately misbehaving worker for demonstrating what happens when a
Railway service outgrows its memory allotment. It grabs a fixed chunk of RAM
every interval, holds a reference so nothing gets garbage collected, and logs
its own resident set size as it climbs. On Railway you'll watch the Metrics
graph ramp up and then see the service get OOM-killed and restarted once it
crosses the memory limit for its plan (or its configured cap).

Configuration (all optional, set as Railway variables):
  CHUNK_MB        MiB to allocate each step          (default 50)
  INTERVAL_SEC    seconds to wait between steps       (default 2)
  MAX_MB          stop growing at this RSS, 0 = grow  (default 0, unbounded)
"""

import logging
import os
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("memory-hog")

CHUNK_MB = int(os.environ.get("CHUNK_MB", "50"))
INTERVAL_SEC = float(os.environ.get("INTERVAL_SEC", "2"))
MAX_MB = int(os.environ.get("MAX_MB", "0"))


def rss_mb():
    """Resident set size in MiB, read from /proc (Linux, i.e. Railway)."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) // 1024
    except OSError:
        pass
    return -1  # not on Linux (e.g. running locally on macOS)


def main():
    log.info(
        f"starting: +{CHUNK_MB} MiB every {INTERVAL_SEC}s"
        + (f", capped at {MAX_MB} MiB" if MAX_MB else ", unbounded (will OOM)")
    )

    blocks = []  # hold references so the memory is never reclaimed
    while True:
        if MAX_MB and rss_mb() >= MAX_MB:
            log.info(f"reached cap of {MAX_MB} MiB, holding steady at {rss_mb()} MiB")
            time.sleep(INTERVAL_SEC)
            continue

        # bytearray of actual non-zero bytes forces real pages to be committed,
        # not just lazily reserved address space.
        blocks.append(bytearray(b"x" * (CHUNK_MB * 1024 * 1024)))
        log.info(f"allocated {len(blocks) * CHUNK_MB} MiB total, RSS {rss_mb()} MiB")
        sys.stdout.flush()
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
