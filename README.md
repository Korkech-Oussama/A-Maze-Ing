> *This project has been created as part of the 42 curriculum by <okorkech> and <sbarbaq>.*

# 🌀 A-Maze-ing

A Python program that generates configurable mazes using a procedural maze generation algorithm.

---

## 📖 Description

**A-Maze-ing** reads a configuration file defining maze parameters (width, height, entry/exit points, generation settings), generates a maze grid, and writes the result to an output file.

**Core focuses:**
- Algorithmic maze generation
- Configuration-driven software design
- Modular and reusable code
- Reproducible maze generation using random seeds

The maze is generated using the **Depth-First Search (DFS) Backtracking algorithm**, which produces a **perfect maze** — exactly one unique path exists between any two cells.

> **Special Feature:** When the maze is large enough, a fixed **"42" pattern** is embedded in the center, composed of fully closed cells so the number remains visible inside the maze structure.

---

## 📁 Project Structure

```
.
├── a_maze_ing.py         # Entry point
├── config.txt            # Example configuration
├── Makefile
├── pyproject.toml
├── README.md
└── mazegen/
    ├── __init__.py
    ├── config_parser.py  # Parses and validates config file
    ├── maze_generator.py # Core DFS maze generation
    ├── display.py        # Visual representation
    └── output_writer.py  # Writes maze to output file
```

---

## ⚙️ Requirements

- Python 3
- pip

---

## 🚀 Installation & Usage

### Install dependencies

```bash
make install
```

Installs: `flake8`, `mypy`, `build`

### Run the program

```bash
make run
```

or directly:

```bash
python3 a_maze_ing.py config.txt
```

### Other commands

| Command | Description |
|---|---|
| `make debug` | Run in debug mode |
| `make build` | Build package → `mazegen.tar.gz` |
| `make lint` | Run linting |
| `make lint-strict` | Run strict linting |
| `make clean` | Remove build files |
| `make fclean` | Full clean |

---

## 🗒️ Configuration File

The program uses a `KEY=VALUE` format. Lines starting with `#` are comments.

**Example `config.txt`:**

```
WIDTH=20
HEIGHT=15
ENTRY=0,0
EXIT=19,14
OUTPUT_FILE=maze.txt
PERFECT=true
SEED=42
```

**Configuration fields:**

| Key | Description |
|---|---|
| `WIDTH` | Maze width in cells |
| `HEIGHT` | Maze height in cells |
| `ENTRY` | Entry coordinates `(x,y)` |
| `EXIT` | Exit coordinates `(x,y)` |
| `OUTPUT_FILE` | Output file name |
| `PERFECT` | Whether the maze should be a perfect maze |
| `SEED` | Optional random seed for reproducibility |

---

## 🧠 Maze Generation Algorithm

The maze uses the **Iterative Backtracker** (DFS) algorithm.

### Steps

1. Start from the entry cell
2. Mark the current cell as visited
3. Randomly select an unvisited neighboring cell
4. Remove the wall between the current cell and the neighbor
5. Move to the neighbor and repeat
6. If no unvisited neighbors exist, backtrack to the previous cell
7. Repeat until all cells are visited

### Guarantees

- ✅ No loops
- ✅ Exactly one path between any two cells
- ✅ Perfect maze

### Why DFS Backtracking?

- Simple to implement
- Produces visually interesting mazes
- Efficient for large grids
- Minimal memory usage
- Widely used in procedural generation

---

## 🔁 Reusable Module

The `MazeGenerator` class is designed to be imported into other projects:

```python
from mazegen import MazeGenerator
```

Exposed methods:
- Generate mazes
- Retrieve the maze grid
- Obtain the solution path
- Access the full maze structure

**Possible applications:** game level generation, puzzle generators, algorithm visualization, educational tools.

---

## 👥 Team & Planning

### Team

| Member | Role |
|---|---|
| `korkech` | Architecture, algorithm, config parser, output system |

### Initial Plan

1. Design configuration file format
2. Implement configuration parser
3. Implement maze generation algorithm
4. Add output writer
5. Create display module
6. Add packaging and Makefile automation

### Evolution

- Modularized into a reusable Python package
- Added static type checking with `mypy`
- Introduced build automation

---

## ✅ What Worked Well

- Modular architecture with clear separation of responsibilities
- Configuration-driven execution
- Reproducible maze generation via seeds

## 🔧 What Could Be Improved

- Support for additional maze generation algorithms
- Graphical maze visualization
- Interactive maze solving
- Performance optimization for very large mazes

---

## 🛠️ Tools Used

- **Python** — core language
- **flake8** — linting
- **mypy** — static type checking
- **Makefile** — build automation
- **Git** — version control

---

## 📚 Resources

- [Maze Generation Algorithms](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithms)
- [Maze Generation — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- [Depth-First Search — Wikipedia](https://en.wikipedia.org/wiki/Depth-first_search)
- [Python Documentation](https://docs.python.org/3/)

---

## 🤖 AI Usage

AI tools assisted with documentation formatting and README structure.
All core logic, algorithm implementation, and project architecture were implemented manually.
