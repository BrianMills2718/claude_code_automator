#!/usr/bin/env python3
"""Main entry point for the calculator application."""

from src.cli import CLI


def main() -> None:
    """Run the calculator application."""
    cli = CLI()
    try:
        cli.run()
    except KeyboardInterrupt:
        print("\nCalculator exited.")


if __name__ == "__main__":
    main()