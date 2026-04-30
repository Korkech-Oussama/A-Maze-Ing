"""Output file writer for A-Maze-ing maze format."""

import sys
from typing import List  # noqa: F401
from mazegen import MazeGenerator


def write_output(
    generator: MazeGenerator,
    output_file: str,
) -> None:
    """
    Write the generated maze to a file in the required hex format.

    Format:
        - One hex digit per cell, row by row, one row per line.
        - An empty line separator.
        - Entry coordinates (x,y).
        - Exit coordinates (x,y).
        - Shortest path as N/E/S/W characters.
        - All lines end with newline.

    Args:
        generator: The MazeGenerator instance after generate() is called.
        output_file: Path to the output file.

    Raises:
        SystemExit: On file write error.
    """
    try:
        with open(output_file, 'w') as f:
            # Write grid rows
            for row in generator.grid:
                line = "".join(format(cell, 'X') for cell in row)
                f.write(line + "\n")

            # Empty separator line
            f.write("\n")

            # Entry, exit, solution
            ex, ey = generator.entry
            xx, xy = generator.exit
            f.write(f"{ex},{ey}\n")
            f.write(f"{xx},{xy}\n")
            f.write("".join(generator.solution) + "\n")

        print(f"Maze written to '{output_file}'.")

    except OSError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)
