"""
Maze Generator Module.

This module provides a reusable MazeGenerator class that generates mazes
using the Iterative Backtracker (DFS) algorithm. It supports perfect mazes,
seeded randomness, and embeds a fixed "42" pattern in the center.

Example usage:
    from mazegen import MazeGenerator

    gen = MazeGenerator(width=20, height=15, seed=42, perfect=True)
    gen.generate(entry=(0, 0), exit_=(19, 14))
    print(gen.grid)           # 2D list of wall bitmasks
    print(gen.solution)       # list of 'N','E','S','W' directions
    print(gen.solution_path)  # list of (x, y) coordinates
"""

import random
import collections
from typing import List, Tuple, Optional, Set, Generator, Dict, Deque

WEST: int = 0b1000
SOUTH: int = 0b0100
EAST: int = 0b0010
NORTH: int = 0b0001

DELTA: Dict[int, Tuple[int, int]] = {
    WEST: (-1, 0),
    SOUTH: (0, 1),
    EAST: (1, 0),
    NORTH: (0, -1)
}

OPPOSIT: Dict[int, int] = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST
}

DIR_CHAR: Dict[int, str] = {
    NORTH: 'N',
    EAST: 'E',
    SOUTH: 'S',
    WEST: 'W',
}

# ── Fixed "42"
COORD_42: Set[Tuple[int, int]] = {
    # The '4'
    (0, 0),
    (0, 1),
    (0, 2), (1, 2), (2, 2),
                    (2, 3),
                    (2, 4),

    # The '2'
    (4, 0), (5, 0), (6, 0),
                    (6, 1),
    (4, 2), (5, 2), (6, 2),
    (4, 3),
    (4, 4), (5, 4), (6, 4)
}


class MazeGenerator:
    """
    Generates a maze using the Recursive Backtracker (DFS) algorithm.

    The maze is represented as a 2D grid where each cell stores a bitmask
    indicating which walls are CLOSED (1 = closed, 0 = open):
        bit 0 = North, bit 1 = East, bit 2 = South, bit 3 = West.
    Fully closed cells are represented by 15 (0xF).

    A fixed "42" pattern made of fully-closed cells is embedded
    in the exact centre of every generated maze, provided the maze is
    large enough.

    Attributes:
        width (int): Number of columns.
        height (int): Number of rows.
        seed (Optional[int]): Random seed for reproducibility.
        perfect (bool): If True, generates a perfect maze (single path).
        grid (List[List[int]]): 2D grid of wall bitmasks after generation.
        solution (List[str]): Shortest path directions ('N','E','S','W').
        solution_path (List[Tuple[int,int]]): Coords along solution path.
        entry (Tuple[int,int]): Entry cell (x, y).
        exit (Tuple[int,int]): Exit cell (x, y).
        cells_42 (Set[Tuple[int,int]]): Grid coordinates for "42" pattern.
        pattern_fits (bool): True if maze is large enough for "42" pattern.
    """

    def __init__(
        self,
        width: int = 20,
        height: int = 15,
        seed: Optional[int] = None,
        perfect: bool = True,
    ) -> None:
        """
        Initialize the MazeGenerator.

        Args:
            width (int): Number of columns (cells). Must be >= 2.
            height (int): Number of rows (cells). Must be >= 2.
            seed (Optional[int]): Random seed for reproducibility.
            perfect (bool): Generate a perfect maze (no loops). Default True.

        Raises:
            ValueError: If width or height is less than 2.
        """
        if width < 2 or height < 2:
            raise ValueError("Width and height must be at least 2.")
        self.width: int = width
        self.height: int = height
        self.seed: Optional[int] = seed
        self.perfect: bool = perfect
        self.grid: List[List[int]] = []
        self.solution: List[str] = []
        self.solution_path: List[Tuple[int, int]] = []
        self.entry: Tuple[int, int] = (0, 0)
        self.exit: Tuple[int, int] = (width - 1, height - 1)
        self.cells_42: Set[Tuple[int, int]] = set()
        self.pattern_fits: bool = False
        self._rng: random.Random = random.Random(self.seed)

    # ── Public API ─────────────────────────────────────────────────────

    def generate(
        self,
        entry: Optional[Tuple[int, int]] = None,
        exit_: Optional[Tuple[int, int]] = None,
    ) -> None:
        """
        Generate the maze grid and solve it.

        The generation process initializes a solid grid, reserves the "42"
        pattern if space permits, carves the passages using DFS, adds loops
        if the maze is imperfect, and finally calculates the shortest path
        from entry to exit.

        Args:
            entry (Optional[Tuple[int, int]]): Entry as (x, y).
            exit_ (Optional[Tuple[int, int]]): Exit as (x, y).

        Raises:
            ValueError: If entry/exit coordinates are invalid, identical,
                or intersect the "42" pattern.
        """
        if entry is not None:
            self.entry = entry
        if exit_ is not None:
            self.exit = exit_

        self._rng = random.Random(self.seed)
        # ── Step 1: initialise grid (all walls closed)
        self.grid = [[0xF] * self.width for _ in range(self.height)]

        # ── Step 2: compute and reserve the 42 pattern cells
        self.cells_42 = set()
        self.pattern_fits = False
        self._reserve_42_pattern()

        # ── Step 3: validate entry and exit
        self._validate_entry_exit()

        # ── Step 4: carve passages (DFS — skips reserved 42 cells)
        collections.deque(self._carve_core(), maxlen=0)

        # ── Step 5: add loops for non-perfect mazes
        if not self.perfect:
            self._add_loops()

        # ── Step 6: solve path
        self.solution, self.solution_path = self._solve_bfs()

    def get_hex_grid(self) -> List[str]:
        """
        Return the maze grid as a list of hex strings.

        This format is useful for serialization or text-based output.
        Each character represents a single cell's bitmask in hexadecimal.

        Returns:
            List[str]: A list of strings, each containing hex digits
                for a corresponding row.
        """
        return [
            "".join(format(cell, 'X') for cell in row)
            for row in self.grid
        ]

    # ── Private helpers ───────────────────────────────────────────────

    def _validate_entry_exit(self) -> None:
        """
        Validate the entry and exit coordinates.

        Raises:
            ValueError: If entry/exit are out of grid bounds.
            ValueError: If entry and exit are the exact same cell.
            ValueError: If entry/exit falls inside the "42" pattern cells.
        """
        ex, ey = self.entry
        xx, xy = self.exit
        if not (0 <= ex < self.width and 0 <= ey < self.height):
            raise ValueError(f"Entry {self.entry} is out of maze bounds.")
        if not (0 <= xx < self.width and 0 <= xy < self.height):
            raise ValueError(f"Exit {self.exit} is out of maze bounds.")
        if self.entry in self.cells_42 or self.exit in self.cells_42:
            raise ValueError(
                "entry and exit must not intersect with the 42 pattern."
            )
        if self.entry == self.exit:
            raise ValueError("Entry and exit must be different.")

    def _reserve_42_pattern(self) -> None:
        """
        Calculate and reserve grid coordinates for the "42" pattern.

        The pattern requires a minimum grid size of 9x7 to fit safely
        with a margin. If the grid is too small, or if the pattern
        overlaps with the entry/exit, the reservation is skipped and
        `pattern_fits` is set to False.
        """
        if self.width < 9 or self.height < 7:
            print("skip generating the 42 shield")
            return
        center_x: int = self.width // 2
        center_y: int = self.height // 2
        start_x: int = center_x - 3
        start_y: int = center_y - 2
        for (x, y) in COORD_42:
            dynamic_x: int = start_x + x
            dynamic_y: int = start_y + y
            self.cells_42.add((dynamic_x, dynamic_y))
        if self.entry in self.cells_42 or self.exit in self.cells_42:
            self.pattern_fits = False
            return
        self.pattern_fits = True

    def _carve_core(self) -> Generator[Tuple[int, int], None, None]:
        """
        Core carving logic using an Iterative Recursive Backtracker (DFS).

        This generator iterates through the grid, randomly tearing down
        walls between adjacent unvisited cells using bitwise negation.
        It inherently avoids carving into the reserved `cells_42`.

        Yields:
            Tuple[int, int]: The (x, y) coordinates of the current cell.
                Used to allow step-by-step animation.
        """
        x, y = self.entry
        stack = [(x, y)]
        while stack:
            cx, cy = stack[-1]
            yield cx, cy  # <-- animation step

            dirs = [NORTH, EAST, SOUTH, WEST]
            self._rng.shuffle(dirs)

            carved = False
            for direction in dirs:
                dx, dy = DELTA[direction]
                nx, ny = cx + dx, cy + dy

                # Check bounds, if cell is unvisited, and not part of '42'
                if (0 <= nx < self.width and 0 <= ny < self.height
                    and self.grid[ny][nx] == 15 and
                   (nx, ny) not in self.cells_42):

                    # Knock down wall between current cell and next cell
                    self.grid[cy][cx] &= ~direction
                    self.grid[ny][nx] &= ~OPPOSIT[direction]
                    stack.append((nx, ny))
                    carved = True
                    break

            if not carved:
                stack.pop()

    def _add_loops(self) -> None:
        """
        Create an imperfect maze by removing a percentage of internal walls.

        Targets approximately 15% of the total grid area to remove walls,
        creating multiple paths and loops. It strictly avoids altering the
        walls of the "42" pattern or the outer boundary of the maze.
        """
        walls_to_remove = int(self.width * self.height * 0.15)
        attempts = 0
        removed = 0
        while removed < walls_to_remove and attempts < walls_to_remove * 10:
            attempts += 1
            x = self._rng.randint(1, self.width - 2)
            y = self._rng.randint(1, self.height - 2)
            direction = self._rng.choice([EAST, SOUTH])
            dx, dy = DELTA[direction]
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if (x, y) in self.cells_42 or (nx, ny) in self.cells_42:
                    continue
                # If the wall exists, tear it down
                if self.grid[y][x] & direction:
                    self.grid[y][x] &= ~direction
                    self.grid[ny][nx] &= ~OPPOSIT[direction]
                    removed += 1

    def _solve_bfs(self) -> Tuple[List[str], List[Tuple[int, int]]]:
        """
        Find shortest path from entry point to exit point using BFS.

        Returns:
            Tuple[List[str], List[Tuple[int, int]]]:
                - First element: list of directions ('N', 'E', 'S', 'W').
                - Second element: list of (x, y) path coordinates.
                Returns empty lists if no path exists.
        """
        ex, ey = self.entry
        xx, xy = self.exit

        queue: Deque[Tuple[int, int]] = collections.deque()
        queue.append((ex, ey))
        came_from: Dict[Tuple[int, int],
                        Optional[Tuple[int, int]]] = {(ex, ey): None}
        dir_from: Dict[Tuple[int, int], str] = {}

        while queue:
            cx, cy = queue.popleft()
            if (cx, cy) == (xx, xy):
                break
            for direction in [NORTH, EAST, SOUTH, WEST]:
                if self.grid[cy][cx] & direction:
                    continue  # wall is closed
                ddx, ddy = DELTA[direction]
                nx, ny = cx + ddx, cy + ddy
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and (nx, ny) not in came_from):
                    came_from[(nx, ny)] = (cx, cy)
                    dir_from[(nx, ny)] = DIR_CHAR[direction]
                    queue.append((nx, ny))

        if (xx, xy) not in came_from:
            return [], []

        path: List[Tuple[int, int]] = []
        directions: List[str] = []
        current: Optional[Tuple[int, int]] = (xx, xy)
        while current is not None:
            path.append(current)
            prev = came_from[current]
            if prev is not None:
                directions.append(dir_from[current])
            current = prev

        path.reverse()
        directions.reverse()
        return directions, path

    def generate_stepwise(self) -> Generator[Tuple[int, int], None, None]:
        """
        Generator version of the maze generation process.

        Executes the same logic as `generate()`, but yields control
        back to the caller at every step of the DFS carving phase.
        This is designed to be consumed by a display or animation loop.

        Yields:
            Tuple[int, int]: The (x, y) coords of the carving step.
        """
        self._rng = random.Random(self.seed)
        self.grid = [[0xF] * self.width for _ in range(self.height)]
        self.cells_42 = set()
        self.pattern_fits = False
        self._reserve_42_pattern()
        yield from self._carve_core()
        if not self.perfect:
            self._add_loops()
        self.solution, self.solution_path = self._solve_bfs()

    # ── Legacy compatibility (old attribute names) ──────────────────────

    @property
    def _42_cells(self) -> List[Tuple[int, int]]:
        """
        Compatibility shim for access to the '42' pattern coordinates.

        Returns:
            List[Tuple[int, int]]: Representation of reserved coords.
        """
        return list(self.cells_42)

    @property
    def _42_fits(self) -> bool:
        """
        Compatibility shim for access to the pattern fit status.

        Returns:
            bool: True if the pattern successfully fit in the grid.
        """
        return self.pattern_fits
