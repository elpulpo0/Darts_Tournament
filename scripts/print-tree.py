import os

EXCLUDE = {
    ".venv",
    "__pycache__",
    "mlruns",
    ".git",
    ".pytest_cache",
    "node_modules",
    ".env",
    ".env.example",
    ".github",
    ".gitignore",
    ".vscode",
    "README.md",
    "__init__.py",
    "app.log",
    "debug.log",
    "error.log",
    "users.db",
    "favicon.ico",
    "build-meta.json",
    "package-lock.json",
    "babel.config.js",
    "shims-vue.d.ts",
    "vite-env.d.ts",
    "env.d.ts",
    "jsconfig.json",
    "release.config.cjs",
    "axios.ts",
    "tsconfig.json",
    "vite.config.js",
}


def print_tree(start_path=".", prefix=""):
    entries = [e for e in sorted(os.listdir(start_path)) if e not in EXCLUDE]
    entries_count = len(entries)
    for i, entry in enumerate(entries):
        path = os.path.join(start_path, entry)
        connector = "└── " if i == entries_count - 1 else "├── "
        if os.path.isdir(path):
            print(f"{prefix}{connector}{entry}/")
            extension = "    " if i == entries_count - 1 else "│   "
            print_tree(path, prefix + extension)
        else:
            print(f"{prefix}{connector}{entry}")


if __name__ == "__main__":
    app_name = os.getenv("APP_NAME")
    print(f"{app_name}/")
    print_tree()
