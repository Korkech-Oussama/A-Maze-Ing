"""Configuration file parser for A-Maze-ing."""

import sys
from typing import Optional, Set


class MazeConfig:
    """
    Parse and validate a maze configuration file.

    Format: KEY=VALUE per line, lines starting with # are comments.

    Attributes:
        width (int): Maze width in cells.
        height (int): Maze height in cells.
        entry (tuple): Entry coordinates (x, y).
        exit (tuple): Exit coordinates (x, y).
        output_file (str): Output filename.
        perfect (bool): Whether to generate a perfect maze.
        seed (Optional[int]): Random seed (optional).
        algorithm (str): Generation algorithm name (optional).
    """

    REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT",
                     "OUTPUT_FILE", "PERFECT"}

    def __init__(self, filepath: str) -> None:
        """
        Parse the configuration file.

        Args:
            filepath: Path to the config file.

        Raises:
            SystemExit: On any parsing or validation error.
        """
        self.width: int = 0
        self.height: int = 0
        self.entry: tuple[int, int] = (0, 0)
        self.exit: tuple[int, int] = (0, 0)
        self.output_file: str = "maze.txt"
        self.perfect: bool = True
        self.seed: Optional[int] = None
        self._parse(filepath)
        self._validate()

    def _parse(self, filepath: str) -> None:
        """Read and parse config file."""
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: Config file '{filepath}' not found.",
                  file=sys.stderr)
            sys.exit(1)
        except OSError as e:
            print(f"Error reading config file: {e}", file=sys.stderr)
            sys.exit(1)

        found_keys: Set[str] = set()
        for lineno, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                print(
                    f"Error: Line {lineno}: Invalid format '{line}' "
                    f"(expected KEY=VALUE).",
                    file=sys.stderr
                )
                sys.exit(1)
            key, _, value = line.partition('=')
            key = key.strip().upper()
            value = value.strip()
            found_keys.add(key)
            self._apply(key, value, lineno)

        missing = self.REQUIRED_KEYS - found_keys
        if missing:
            miss: str = ', '.join(sorted(missing))
            print(
                f"Error: Missing required config keys: {miss}",
                file=sys.stderr
            )
            sys.exit(1)

    def _apply(self, key: str, value: str, lineno: int) -> None:
        """Apply a single key-value pair."""
        try:
            if key == "WIDTH":
                self.width = int(value)
            elif key == "HEIGHT":
                self.height = int(value)
            elif key == "ENTRY":
                parts = value.split(',')
                self.entry = (int(parts[0]), int(parts[1]))
            elif key == "EXIT":
                parts = value.split(',')
                self.exit = (int(parts[0]), int(parts[1]))
            elif key == "OUTPUT_FILE":
                self.output_file = value
            elif key == "PERFECT":
                if value.lower() in ('true', '1'):
                    self.perfect = True
                elif value.lower() in ('false', '0'):
                    self.perfect = False
                else:
                    raise ValueError("PERFECT key must be a boolean")
            elif key == "SEED":
                self.seed = int(value)
        except (ValueError, IndexError) as e:
            print(
                f"Error: Line {lineno}: " +
                f"Invalid value for {key}='{value}': {e}",
                file=sys.stderr
            )
            sys.exit(1)

    def _validate(self) -> None:
        """Validate the parsed configuration."""
        if self.width < 2:
            print("Error: WIDTH must be at least 2.", file=sys.stderr)
            sys.exit(1)
        if self.height < 2:
            print("Error: HEIGHT must be at least 2.", file=sys.stderr)
            sys.exit(1)
        if self.width * self.height > 1000000:
            print("test")
            sys.exit(1)

        ex, ey = self.entry
        xx, xy = self.exit
        if not (0 <= ex < self.width and 0 <= ey < self.height):
            print(
                f"Error: ENTRY ({ex},{ey}) is outside maze bounds "
                f"({self.width}x{self.height}).",
                file=sys.stderr
            )
            sys.exit(1)
        if not (0 <= xx < self.width and 0 <= xy < self.height):
            print(
                f"Error: EXIT ({xx},{xy}) is outside maze bounds "
                f"({self.width}x{self.height}).",
                file=sys.stderr
            )
            sys.exit(1)
        if self.entry == self.exit:
            print("Error: ENTRY and EXIT must be different.", file=sys.stderr)
            sys.exit(1)
