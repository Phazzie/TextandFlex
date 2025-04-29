import os

ROOT = os.path.join(os.path.dirname(__file__), "src")
OUTPUT_FILE = "codebase_package.txt"

INCLUDE_FOLDERS = [
    "analysis_layer",
    "cli",
    "data_layer",
    "presentation_layer",
    "utils"
]

def collect_files():
    files = []
    for folder in INCLUDE_FOLDERS:
        folder_path = os.path.join(ROOT, folder)
        for dirpath, dirnames, filenames in os.walk(folder_path):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fname in filenames:
                if fname.endswith(".py"):
                    files.append(os.path.join(dirpath, fname))
    for fname in os.listdir(ROOT):
        if fname.endswith(".py") and fname != "__init__.py":
            files.append(os.path.join(ROOT, fname))
    return sorted(files)

def make_tree(files):
    tree = ""
    relpaths = [os.path.relpath(f, ROOT) for f in files]
    for path in relpaths:
        tree += f"  {path}\n"
    return tree

def main():
    files = collect_files()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write("DIRECTORY STRUCTURE AND FILE LIST:\n\n")
        out.write(make_tree(files))
        out.write("\n\n==============================\n")
        for f in files:
            rel = os.path.relpath(f, ROOT)
            out.write(f"========== {rel} ==========" + "\n\n")
            with open(f, encoding="utf-8") as src:
                out.write(src.read())
                out.write("\n\n==============================\n")
    print(f"Packaged {len(files)} files into {OUTPUT_FILE}")
    print("Files packaged:")
    for f in files:
        print(f"  {os.path.relpath(f, ROOT)}")
    print(f"Output file path: {os.path.abspath(OUTPUT_FILE)}")

if __name__ == "__main__":
    main()
