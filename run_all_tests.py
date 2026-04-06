import os
import sys
import subprocess

def run_test(file_path):
    print(f"\n{'='*60}")
    print(f" Testing: {os.path.basename(file_path)}")
    print(f"{'='*60}")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, "analyzer.py", file_path],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env
    )

    print(result.stdout)
    if result.stderr:
        print("Error output (stderr):", result.stderr)

def main():
    base_dir = "examples"
    if not os.path.exists(base_dir):
        print(f"Error: Directory '{base_dir}' not found!")
        return

    test_files = []
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".txt"):
                test_files.append(os.path.join(root, file))

    test_files.sort()

    if not test_files:
        print("No test files found.")
        return

    print(f"Found {len(test_files)} test files. Running...\n")

    for f in test_files:
        run_test(f)

    print(f"\nTesting completed.")

if __name__ == "__main__":
    main()