"""Punto de entrada: python app.py <comando> [argumentos]."""

import sys

from solicitudes.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
