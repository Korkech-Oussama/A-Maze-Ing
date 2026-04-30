PYTHON = python3
PIP = $(PYTHON) -m pip
MAIN = a_maze_ing.py
CONFIG = config.txt

.PHONY: all install run debug lint lint-strict clean fclean re build

# By default, running 'make' will build the package
all: build

install:
	$(PIP) install flake8 mypy build --break-system-packages 2>/dev/null || \
	$(PIP) install flake8 mypy build

run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

build:
	@echo "Building the package..."
	$(PIP) install --upgrade build --break-system-packages 2>/dev/null || $(PIP) install --upgrade build
	$(PYTHON) -m build
	@echo "Moving and renaming to mazegen.tar.gz..."
	cp dist/mazegen-*.tar.gz ./mazegen.tar.gz
	@echo "Package mazegen.tar.gz built successfully in the root directory."

lint:
	flake8 .
	mypy . \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict

clean:
	@echo "Cleaning temporary build and cache files..."
	rm -rf dist/ mazegen.egg-info/ .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	rm -f maze.txt

fclean: clean
	@echo "Removing the built package..."
	rm -f mazegen.tar.gz

re: fclean all