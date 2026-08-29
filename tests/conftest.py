import sys
from pathlib import Path

# Add apps/sandbox-worker/src to sys.path for test discovery
root_dir = Path(__file__).resolve().parent.parent
worker_src = root_dir / "apps" / "sandbox-worker" / "src"
if str(worker_src) not in sys.path:
    sys.path.insert(0, str(worker_src))
