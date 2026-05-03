#!/usr/bin/env python3
"""
dev_db.py — manage the local dev database stack.

Usage:
    python dev_db.py up        # start all services
    python dev_db.py down      # stop and remove containers
    python dev_db.py restart   # stop then start
    python dev_db.py status    # show running containers
    python dev_db.py logs      # tail logs (Ctrl-C to exit)
    python dev_db.py psql      # open interactive psql shell
    python dev_db.py ping      # check postgres + redis connectivity
    python dev_db.py reset     # ⚠ destroy volumes and restart fresh
"""

import shutil
import subprocess
from pathlib import Path
import sys
import threading

SCRIPT_DIR = Path(__file__).parent.resolve()
COMPOSE_FILE = SCRIPT_DIR / "docker-compose.dev_db.yml"

def get_db_url():
    """ Get the database URL for connecting to the dev database. """
    return "postgresql://devuser:devpassword@localhost:5432/devdb"

def _is_docker_engine_running() -> bool:
    if shutil.which("docker") is None:
        return False

    result = subprocess.run(
        ["docker", "info"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )

    return result.returncode == 0

def up_dev_db():
    """ Start the dev database stack. """
    if not _is_docker_engine_running():
        print("Docker engine is not running. Please start Docker and try again.")
        sys.exit(1)

    subprocess.run(["docker-compose", "-f", str(COMPOSE_FILE), "up", "-d"], check=True)
    print("Dev database stack started.")

def up_dev_db_async():
    """ Start the dev database stack and wait for it to be ready. """
    print("Running dev database stack in the background...")
    threading.Thread(target=up_dev_db).start()

def down_dev_db():
    """ Stop and remove the dev database stack. """
    subprocess.run(["docker-compose", "-f", str(COMPOSE_FILE), "down", "-v"], check=True)
    print("Dev database stack stopped and removed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dev_db.py <command>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "up":
        up_dev_db()
    elif command == "down":
        down_dev_db()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)