#!/usr/bin/env python3
"""
notebook_conversion_script.py

A simple script to convert the Jupyter notebook named "main250227.ipynb"
into a "main.md" Markdown file using nbconvert.

Usage:
  1. Ensure this script and main250227.ipynb are in the same directory.
  2. Install nbconvert (if not already): pip install nbconvert
  3. Run: python3 notebook_conversion_script.py

It will produce "main.md" in the current folder upon success.
"""

import subprocess

def convert_notebook_to_md():
    """
    Calls `jupyter nbconvert` to convert "main250227.ipynb" into "main.md".
    """
    cmd = [
        "jupyter", "nbconvert",
        "--to", "markdown",
        "main250227.ipynb",   # The notebook to convert
        "--output", "main.md" # The resulting Markdown file
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Conversion successful: main250227.ipynb -> main.md")
    except FileNotFoundError:
        print("Error: The 'jupyter' command is not found. Make sure nbconvert (or Jupyter) is installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion:\n{e}")

if __name__ == "__main__":
    convert_notebook_to_md()



