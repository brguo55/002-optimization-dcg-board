#!/usr/bin/env python3
"""
converter.py

A simple script that uses nbconvert to turn main250227.ipynb into main.md.
Make sure:
  1. 'converter.py' and 'main250227.ipynb' are in the same directory.
  2. nbconvert (jupyter) is installed (pip install nbconvert).

Usage:
  python3 converter.py
"""

import subprocess

def convert_notebook():
    cmd = [
        "jupyter", "nbconvert",
        "--to", "markdown",
        "main2.ipynb",   # The notebook to convert
        "--output", "main.md" # The resulting Markdown file
    ]
    try:
        subprocess.run(cmd, check=True)
        print("Conversion successful: main.ipynb -> main.md")
    except FileNotFoundError:
        print("Error: 'jupyter' command not found. Make sure nbconvert is installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error during conversion:\n{e}")

if __name__ == "__main__":
    convert_notebook()



