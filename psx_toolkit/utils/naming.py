"""Naming helpers that are independent of Blender."""

import re
import unicodedata

_C_KEYWORDS = {
    "auto",
    "break",
    "case",
    "char",
    "const",
    "continue",
    "default",
    "do",
    "double",
    "else",
    "enum",
    "extern",
    "float",
    "for",
    "goto",
    "if",
    "inline",
    "int",
    "long",
    "register",
    "restrict",
    "return",
    "short",
    "signed",
    "sizeof",
    "static",
    "struct",
    "switch",
    "typedef",
    "union",
    "unsigned",
    "void",
    "volatile",
    "while",
}


def sanitize_c_identifier(value: str) -> str:
    """Convert a filename base into a lowercase C identifier."""

    ascii_value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    )
    identifier = re.sub(r"[^a-z0-9]+", "_", ascii_value.lower()).strip("_")
    if not identifier:
        identifier = "model"
    if identifier[0].isdigit():
        identifier = f"model_{identifier}"
    if identifier in _C_KEYWORDS:
        identifier = f"{identifier}_model"
    return identifier
