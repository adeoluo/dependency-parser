"""Dependency Parser - an arc-standard transition-based parser, from scratch."""

from dependency_parser.evaluation import AttachmentReport, evaluate
from dependency_parser.parser import Parse, Parser, TrainingConfig

__version__ = "0.1.0"

__all__ = [
    "AttachmentReport",
    "Parse",
    "Parser",
    "TrainingConfig",
    "evaluate",
]
