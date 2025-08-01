#!/usr/bin/env python3
"""
Engine Testing Script for toto.c Chess Engine
Tests basic UCI communication and engine functionality
"""

import subprocess
import time
import os
import sys

class EngineTest:
    def __init__(self, engine_path="./toto_engine"):
        self.engine_path = engine_path
        self.process = None

    def start_engine(self):
        """Start the engine process"""
        try:
            # Try different executable names
            possible_names = [self.engine_path, f"{self.engine_path}.exe", "./toto_engine", "./toto_engine.exe"]

            for name in possible_names:
                if os.path.exists(name):
                    self.engine_path = name
                    break
            else:
                print(f"Engine executable not found. Tried: {possible_names}")
                return False

            print(f"Starting engine: {self.engine_path}")
            self.process = subprocess.Popen(
                [self.engine_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=0
            )
            return True

        except Exception as e:
            print(f"Failed to start engine: {e}")
            return False

    def send_command(self, command):
        """Send a command to the engine"""
        if self.process and self.process.stdin:
            print(f">>> {command}")
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()

    def read_response(self, timeout=2.0):
        """Read response from engine"""
        if not self.process:
            return []

        import select
        responses = []
        start_time = time.time()

        while time.time() - start_time < timeout:
            if os.name == 'nt':  # Windows
                # Simple polling for Windows
                time.sleep(0.1)
                try:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        print(f"<<< {line}")
                        responses.append(line)
                        if line.startswith("uciok") or line.startswith("readyok") or line.startswith("bestmove"):
                            break
                except:
                    break
            else:  # Unix-like systems
                ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
                if ready:
                    line = self.process.stdout.readline()
                    if line:
                        line = line.strip()
                        print(f"<<< {line}")
                        responses.append(line)
                        if line.startswith("uciok") or line.startswith("readyok") or line.startswith("bestmove"):
                            break
                else:
                    time.sleep(0.1)

        return responses

    def test_uci_protocol(self):
        """Test basic UCI protocol"""
        print("\n=== Testing UCI Protocol ===")

        # Test UCI command
        self.send_command("uci")
        responses = self.read_response()

        uci_ok = any("uciok" in resp for resp in responses)
        if uci_ok:
            print("✓ UCI protocol initialized successfully")
        else:
            print("✗ UCI protocol initialization failed")
            return False

        # Test isready command
        self.send_command("isready")
        responses = self.read_response()

        ready_ok = any("readyok" in resp for resp in responses)
        if ready_ok:
            print("✓ Engine is ready")
        else:
            print("✗ Engine not ready")
            return False

        return True

    def test_position_and_search(self):
        """Test position setting and search"""
        print("\n=== Testing Position and Search ===")

        # Set starting position
        self.send_command("ucinewgame")
        time.sleep(0.1)

        self.send_command("position startpos moves e2e4")
        time.sleep(0.1)

        # Search for best move
        self.send_command("go movetime 1000")  # Search for 1 second
        responses = self.read_response(timeout=3.0)

        best_move = None
        for resp in responses:
            if resp.startswith("bestmove"):
                parts = resp.split()
                if len(parts) >= 2:
                    best_move = parts[1]
                    break

        if best_move:
            print(f"✓ Engine found best move: {best_move}")
            return True
        else:
            print("✗ Engine did not return a move")
            return False

    def test_multiple_positions(self):
        """Test engine with multiple positions"""
        print("\n=== Testing Multiple Positions ===")

        positions = [
            ("startpos", "Starting position"),
            ("startpos moves e2e4 e7e5", "After 1.e4 e5"),
            ("startpos moves e2e4 e7e5 g1f3 b8c6", "After 1.e4 e5 2.Nf3 Nc6"),
        ]

        for position, description in positions:
            print(f"\nTesting: {description}")
            self.send_command(f"position {position}")
            self.send_command("go movetime 500")

            responses = self.read_response(timeout=2.0)
            best_move = None

            for resp in responses:
                if resp.startswith("bestmove"):
                    parts = resp.split()
                    if len(parts) >= 2:
                        best_move = parts[1]
                        break

            if best_move:
                print(f"  ✓ Best move: {best_move}")
            else:
                print(f"  ✗ No move found")

    def interactive_mode(self):
        """Interactive mode for manual testing"""
        print("\n=== Interactive Mode ===")
        print("Enter UCI commands (type 'quit' to exit):")

        while True:
            try:
                command = input(">>> ").strip()
                if command.lower() == 'quit':
                    break

                self.send_command(command)

                # Read responses for a short time
                responses = self.read_response(timeout=1.0)
                if not responses:
                    print("(no response)")

            except KeyboardInterrupt:
                break
            except EOFError:
                break

    def cleanup(self):
        """Clean up the engine process"""
        if self.process:
            self.send_command("quit")
            time.sleep(0.5)
            self.process.terminate()
            self.process = None

def main():
    print("Chess Engine Test Script")
    print("=" * 40)

    # Check if engine exists
    engine_paths = ["toto_engine", "toto_engine.exe", "./toto_engine", "./toto_engine.exe"]

    engine_found = False

    for path in engine_paths:
        if os.path.exists(path):
            engine_found = True
            break

    if not engine_found:
        print("Error: Chess engine not found!")
        print("Please compile toto.c first:")
        print("  gcc toto.c -o toto_engine")
        print()
        print("Also ensure you have the NNUE file:")
        print("  nn-eba324f53044.nnue")
        return 1

    # Check for NNUE file
    nnue_files = ["nn-eba324f53044.nnue", "eval.nnue", "nnue.bin"]
    nnue_found = any(os.path.exists(f) for f in nnue_files)

    if not nnue_found:
        print("Warning: NNUE file not found!")
        print("The engine may not work properly without it.")
        print("Expected files:", ", ".join(nnue_files))
        print()

    # Run tests
    tester = EngineTest()

    try:
        if not tester.start_engine():
            return 1

        # Run basic tests
        success = True
        success &= tester.test_uci_protocol()
        success &= tester.test_position_and_search()

        if success:
            tester.test_multiple_positions()

            # Ask for interactive mode
            print("\n" + "=" * 40)
            if input("Enter interactive mode? (y/n): ").lower().startswith('y'):
                tester.interactive_mode()

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error during testing: {e}")
    finally:
        tester.cleanup()

    print("\nTesting complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
