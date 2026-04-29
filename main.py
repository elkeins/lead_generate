import argparse

from pipeline.milestone1 import run_milestone1


def main() -> None:
    parser = argparse.ArgumentParser(description="HVAC lead pipeline")
    parser.add_argument(
        "command",
        nargs="?",
        default="milestone1",
        choices=("milestone1", "milestone2", "milestone2-dashboard"),
        help="milestone1: collect & export 1.xlsx; milestone2: sequences + optional Instantly push; "
        "milestone2-dashboard: metrics HTTP server",
    )
    args = parser.parse_args()
    if args.command == "milestone1":
        run_milestone1()
        return
    if args.command == "milestone2":
        from pipeline.milestone2 import run_milestone2

        run_milestone2()
        return
    if args.command == "milestone2-dashboard":
        from outreach.dashboard import run_dashboard

        run_dashboard()
        return


if __name__ == "__main__":
    main()
