#!/usr/bin/env python3
"""
File: generate_project_structure.py
Author: ChatGPT
Date: 2025-02-20
Purpose: A generalized project directory structure generator that supports multiple input file types.
Function:
    - Load a project directory structure from JSON, YAML, or a plain text file (in tree format).
    - Recursively create directories and files as defined by the parsed structure.
    - Generate default README.md and LICENSE files (MIT License modified to credit "Big Bad Voodoo Daddy").
    - Provide options for interactive mode, dry-run, and customizable logging.
Inputs:
    --config: Path to a configuration file describing the project structure (JSON, YAML, or plain text).
    --project-name: Name of the project directory (if not specified in the config file).
    --interactive: Enable interactive mode to prompt for project name.
    --dry-run: Simulate the creation process without modifying the file system.
    --log-level: Set the logging level (DEBUG, INFO, WARNING, ERROR).
Outputs:
    - A generated directory structure with files on the file system.
Description:
    This script takes input from various file formats to generate a directory tree for any project.
    It leverages recursion and OOP principles for modular design and robust error handling.
File Path: ./generate_project_structure.py
"""

import json
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

import click

# Attempt to import PyYAML for YAML support.
try:
    import yaml
except ImportError:
    yaml = None
    logging.warning("PyYAML module not found. YAML configuration files will not be supported.")


# Default directory structure used if no configuration file is provided.
DEFAULT_STRUCTURE = {
    "README.md": None,
    "requirements.txt": None,
    "config": {
        "config.yaml": None  # Configurations for API keys, DB connection, etc.
    },
    "src": {
        "main.py": None,  # Application entry point
        "api": {
            "__init__.py": None,
            "base_api.py": None,       # Abstract base class for APIs
            "shopgoodwill_api.py": None,
            "ebay_api.py": None,       # For future use
            "facebook_api.py": None    # For future use
        },
        "models": {
            "__init__.py": None,
            "item.py": None,           # Item class definition
            "bid.py": None,            # Bid class definition
            "user.py": None            # (if needed)
        },
        "services": {
            "__init__.py": None,
            "data_extractor.py": None,
            "price_comparator.py": None,
            "bidding_logic.py": None,
            "queue_manager.py": None,
            "scheduler.py": None
        },
        "database": {
            "__init__.py": None,
            "db_manager.py": None
        },
        "utils": {
            "__init__.py": None,
            "logger.py": None,
            "config_loader.py": None,
            "error_handler.py": None
        }
    },
    "tests": {}  # Directory for unit tests and integration tests
}


class ProjectStructureCreator:
    """
    Creates a project directory structure based on a nested dictionary.
    Uses recursion to traverse and create directories and files with robust error handling.
    """

    def __init__(self, base_path: str, structure: dict, dry_run: bool = False):
        """
        Initialize the ProjectStructureCreator.

        Parameters:
            base_path (str): The root directory where the project will be created.
            structure (dict): A nested dictionary representing the project structure.
            dry_run (bool): If True, simulate creation without modifying the file system.
        """
        self.base_path = Path(base_path)
        self.structure = structure
        self.dry_run = dry_run

    def create_structure(self, current_path: Path, structure: dict) -> None:
        """
        Recursively creates directories and files based on the provided structure.

        Parameters:
            current_path (Path): The current directory path for creation.
            structure (dict): A dictionary representing subdirectories and files.
        """
        for name, content in structure.items():
            target = current_path / name
            if isinstance(content, dict):
                # Create a directory.
                try:
                    if self.dry_run:
                        logging.info(f"[Dry Run] Would create directory: {target}")
                    else:
                        target.mkdir(parents=True, exist_ok=True)
                        logging.info(f"Created directory: {target}")
                except Exception as e:
                    logging.error(f"Error creating directory '{target}': {e}")
                # Recursively create subdirectories/files.
                self.create_structure(target, content)
            else:
                # Create a file.
                try:
                    if self.dry_run:
                        logging.info(f"[Dry Run] Would create file: {target}")
                    else:
                        if not target.exists():
                            target.touch()
                            logging.info(f"Created file: {target}")
                except Exception as e:
                    logging.error(f"Error creating file '{target}': {e}")

    def run(self) -> None:
        """
        Initiates the creation process by setting up the base directory and recursively
        creating the entire project structure.
        """
        try:
            if self.dry_run:
                logging.info(f"[Dry Run] Would create base directory: {self.base_path}")
            else:
                self.base_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created base directory: {self.base_path}")
        except Exception as e:
            logging.error(f"Error creating base directory '{self.base_path}': {e}")
            sys.exit(1)
        self.create_structure(self.base_path, self.structure)


def load_structure_from_file(config_path: str) -> tuple:
    """
    Loads a project structure from a configuration file.
    Supports JSON, YAML, and plain text (tree format) files.

    Parameters:
        config_path (str): Path to the configuration file.

    Returns:
        tuple: (project_name, structure) where project_name can be None if not defined in the file.
    """
    path = Path(config_path)
    if not path.exists():
        logging.error(f"Configuration file '{config_path}' does not exist.")
        sys.exit(1)

    ext = path.suffix.lower()
    try:
        if ext in ['.yaml', '.yml']:
            if yaml is None:
                logging.error("PyYAML is not installed. Cannot process YAML files.")
                sys.exit(1)
            with path.open('r') as f:
                structure = yaml.safe_load(f)
            project_name = None
        elif ext == '.json':
            with path.open('r') as f:
                structure = json.load(f)
            project_name = None
        elif ext in ['.txt', '.tree']:
            project_name, structure = parse_tree_text(config_path)
        else:
            logging.error("Unsupported configuration file format. Use JSON, YAML, or plain text (.txt, .tree).")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error loading configuration file '{config_path}': {e}")
        sys.exit(1)

    if not isinstance(structure, dict):
        logging.error("Invalid configuration format. Expected a dictionary at the root.")
        sys.exit(1)
    return project_name, structure


def parse_tree_text(config_path: str) -> tuple:
    """
    Parses a plain text file representing a directory tree and returns a tuple of (project_name, structure).

    The expected format is similar to:
        shopmygoodwill/
        ├── README.md
        ├── requirements.txt
        ├── config/
        │   └── config.yaml           # Optional inline comments
        ...

    Parameters:
        config_path (str): Path to the text file.

    Returns:
        tuple: (project_name, structure) where project_name is derived from the first line if available,
               otherwise None.
    """
    pattern = re.compile(r"^([\s│]*)(├── |└── )(.+)$")
    try:
        with open(config_path, 'r') as f:
            lines = [line.rstrip() for line in f if line.strip() != '']
    except Exception as e:
        logging.error(f"Error reading text file '{config_path}': {e}")
        sys.exit(1)

    # Determine if the first line defines a root folder.
    first_line = lines[0]
    if first_line.endswith("/"):
        project_name = first_line.rstrip("/").strip()
        lines = lines[1:]  # Remove the root line.
    else:
        project_name = None

    root_dict = {}
    stack = [(0, root_dict)]  # Each item is a tuple: (level, current_dict)

    for line in lines:
        match = pattern.match(line)
        if not match:
            continue  # Skip lines that do not match the expected format.
        indent, branch, name_with_comment = match.groups()
        # Remove inline comments (anything after '#').
        name = name_with_comment.split("#")[0].strip()
        # Determine level: assume 4 characters per indentation level.
        level = len(indent.replace("│", " ")) // 4 + 1  # Root level is 1.
        # Determine if the entry is a directory (ends with '/') or a file.
        entry = {} if name.endswith("/") else None
        # Adjust the stack based on the current level.
        while stack and stack[-1][0] >= level:
            stack.pop()
        # Add the entry to the current parent's dictionary.
        parent_dict = stack[-1][1]
        parent_dict[name] = entry
        # If it's a directory, push it onto the stack.
        if isinstance(entry, dict):
            stack.append((level, entry))
    return project_name, root_dict
