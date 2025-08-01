# SynapseChess

SynapseChess is a chess engine and GUI featuring NNUE (Efficiently Updatable Neural Network) evaluation. It includes a graphical interface, sound effects, and a powerful engine backend.

## Features

- Chess engine with NNUE evaluation
- Python-based GUI using Pygame
- Sound effects for moves, captures, and game events
- Cross-platform: Windows and Mac supported

## Requirements

- Python 3.7+
- [Pygame](https://www.pygame.org/)
- C/C++ compiler (GCC/Clang for Mac, MinGW/MSVC for Windows)
- `make` (for Mac, or install via Chocolatey/MSYS2 on Windows)
- NNUE evaluation file (`nn-eba324f53044.nnue`)

## Installation

### 1. Clone the Repository

```sh
git clone https://github.com/Brxj19/SynapseChess.git
cd SynapseChess
```

### 2. Install Python Dependencies

Make sure you have Python 3.7 or newer installed.

```sh
pip install -r requirements.txt
```

### 3. Install `make` and Compiler

#### **Mac**

- Install Xcode Command Line Tools (includes `make` and `gcc`):

```sh
xcode-select --install
```

#### **Windows**

- Install [Python](https://www.python.org/downloads/) if not already installed.
- Install [Chocolatey](https://chocolatey.org/install) (if not already installed).
- Open **Command Prompt as Administrator** and run:

```sh
choco install make mingw
```

Alternatively, you can use [MSYS2](https://www.msys2.org/) and install `make` and `gcc` via:

```sh
pacman -Syu
pacman -S make mingw-w64-x86_64-gcc
```

### 4. Build the Engine

From the project directory, run:

```sh
make
```

This will produce an executable named `engine` (or `engine.exe` on Windows).

### 5. Verify Assets

Ensure the following files and folders exist:

- `nn-eba324f53044.nnue` (NNUE weights file)
- `assets/pieces/` (piece images)
- `assets/sounds/` (sound files)

## Running the Project

### **Start the GUI**

```sh
python gui.py
```

The GUI will launch, and the engine will be used for computer moves.

### **Run Engine Tests**

```sh
python engine_test.py
```

## Notes

- The engine binary is built from [`engine.c`](engine.c) and NNUE sources in [`nnue/`](nnue/).
- The GUI communicates with the engine via standard input/output.
- You can replace the NNUE file with another compatible `.nnue` file if desired.

## Troubleshooting

- If you encounter missing DLL errors on Windows, ensure MinGW/MSYS2 is in your PATH.
- On Mac, if you get permission errors, try `chmod +x engine`.
- If you see errors about missing sound or piece files, check the `assets/` directory.

## License

MIT License

---

**Enjoy