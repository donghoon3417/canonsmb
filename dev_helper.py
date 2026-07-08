from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import time
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

IGNORE = {
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    "logs"
}

last = 0


class Handler(FileSystemEventHandler):
    def on_modified(self, event):
        global last

        if event.is_directory:
            return

        path = event.src_path

        for i in IGNORE:
            if i in path:
                return

        now = time.time()

        if now - last < 1:
            return

        last = now

        print("변경:", os.path.relpath(path, ROOT))

        subprocess.run(
            ["git", "add", "."],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print("git add 완료")


observer = Observer()
observer.schedule(Handler(), ROOT, recursive=True)
observer.start()

print("Dev Helper 실행중...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()

observer.join()