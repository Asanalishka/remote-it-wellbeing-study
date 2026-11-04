"""Execute and validate the survey notebook in the repository's Jupyter environment."""

import os
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main():
    root = Path(__file__).resolve().parents[1]
    cache = root / ".cache"
    for key, suffix in {
        "JUPYTER_CONFIG_DIR": "jupyter/config",
        "JUPYTER_DATA_DIR": "jupyter/data",
        "JUPYTER_RUNTIME_DIR": "jupyter/runtime",
        "IPYTHONDIR": "ipython",
        "MPLCONFIGDIR": "matplotlib",
        "XDG_CACHE_HOME": "",
    }.items():
        directory = cache / suffix
        directory.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(directory)
    path = root / "notebooks/01_data_analysis.ipynb"
    notebook = nbformat.read(path, as_version=4)
    NotebookClient(notebook, timeout=120, kernel_name="python3",
                   resources={"metadata": {"path": str(root)}}).execute()
    nbformat.validate(notebook)
    nbformat.write(notebook, path)
    print(f"Executed {sum(c.cell_type == 'code' for c in notebook.cells)} code cells: {path}")


if __name__ == "__main__":
    main()
