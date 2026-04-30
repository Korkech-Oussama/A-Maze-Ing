"""
A-Maze-ing: Maze Generator.

Usage:
    python3 a_maze_ing.py config.txt

Generates a maze from a configuration file and displays it in the terminal.
"""

import sys
from mazegen.config_parser import MazeConfig
from mazegen.output_writer import write_output
from mazegen.display import run_interactive
from mazegen import MazeGenerator
# Allow running from project root without installing the package


def main() -> None:
    """Main entry point for the A-Maze-ing program."""
    if len(sys.argv) != 2:
        print(
            "Usage: python3 a_maze_ing.py <config_file>",
            file=sys.stderr
        )
        sys.exit(1)

    config_path = sys.argv[1]

    # Parse configuration
    try:
        config = MazeConfig(config_path)
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Create and run generator
    try:
        gen = MazeGenerator(
            width=config.width,
            height=config.height,
            seed=config.seed,
            perfect=config.perfect,
        )
        gen.generate(entry=config.entry, exit_=config.exit)
    except MemoryError:
        print("Error: MemoryError", file=sys.stderr)
        sys.exit(1)
    except (ValueError, Exception) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output file
    write_output(gen, config.output_file)

    # Launch interactive terminal display
    run_interactive(gen, config)


if __name__ == "__main__":
    main()
