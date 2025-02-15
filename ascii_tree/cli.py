"""Command line interface for ascii_tree."""

import argparse
from pathlib import Path

from ascii_tree import tree_gen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    args = parser.parse_args()
    tree_gen.main(Path(args.root))


if __name__ == '__main__':
    main()
