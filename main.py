#!/usr/bin/env python3
"""RescueRoute AI entry point."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline.rescue_pipeline import RescueRoutePipeline, demo


def main():
    parser = argparse.ArgumentParser(description="RescueRoute AI — Emergency Vehicle Corridor System")
    parser.add_argument(
        "mode",
        choices=["demo", "live", "train-emergency", "train-vehicles", "server"],
        help="Run mode",
    )
    parser.add_argument("--camera", default="0", help="Camera source for live mode")
    parser.add_argument("--origin", default="A", help="Starting intersection for routing")
    args = parser.parse_args()

    if args.mode == "demo":
        demo()
    elif args.mode == "live":
        source = int(args.camera) if args.camera.isdigit() else args.camera
        RescueRoutePipeline().run_live(camera_source=source, origin=args.origin)
    elif args.mode == "train-emergency":
        from ai_models.train_emergency import model  # noqa: F401
    elif args.mode == "train-vehicles":
        import ai_models.train_vehicles  # noqa: F401
    elif args.mode == "server":
        from backend.app import app, init_db

        init_db()
        app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    main()
