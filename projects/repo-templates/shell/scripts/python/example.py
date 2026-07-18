#!/usr/bin/env python3
"""
Example Python CLI utility script template.
"""
import argparse
import logging
import sys

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        level=level,
        stream=sys.stderr
    )

def main():
    parser = argparse.ArgumentParser(
        description="Example template python command-line tool."
    )
    parser.add_argument(
        "-d", "--host",
        default="127.0.0.1",
        help="Specify the target host address"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable debug logging"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logging.info("Starting Python script execution...")
    logging.info(f"Target host configured: {args.host}")
    logging.info("Execution complete!")

if __name__ == "__main__":
    main()
EOF
