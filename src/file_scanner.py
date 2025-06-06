"""
hand_parser.py

Scans and parses raw PokerStars hand history files to extract individual
hand entries that have not been previously processed.

Reads `.txt` files from a specified directory, identifies individual
hands using regex, and checks against the database to avoid
duplicate processing.

Functions:
    - get_hand_id(raw_hand_text):
    - split_hands(file_content):
    - scan_hand_history_folder():

Dependencies:
    - db.py: Uses `hand_already_processed` and `add_hand_id` for tracking
    hand parsing.

Usage:
"""

import os
import re
from src.db import hand_already_processed, add_hand_id

# Look for an env var, else goes to a raw_hands_example" folder in repo
# If you have pokerstars, then switch this line to your hand history folder
ALL_HANDS = os.getenv(
            "POKER_HAND_DIR",
            os.path.join(os.getcwd(), "raw_hands_example")
)

# Regex to split on each hand boundary (preserves the header)
HAND_SPLIT_REGEX = re.compile(r"(?=PokerStars Hand #\d+:)")
# Regex to extract hand ID
HAND_ID_REGEX = re.compile(r"PokerStars Hand #(\d+):")


def get_hand_id(raw_hand_text):
    """Extract the hand ID from a block of raw hand text."""
    match = HAND_ID_REGEX.search(raw_hand_text)
    return match.group(1) if match else None


def split_hands(file_content):
    """
    Split a text blob into individual hand histories based
    on header boundaries. Returns a list of hand strings.
    """
    raw_chunks = HAND_SPLIT_REGEX.split(file_content)
    hands = []
    for chunk in raw_chunks:
        chunk = chunk.strip()
        if chunk.startswith("PokerStars Hand #"):
            hands.append(chunk)
    return hands


def scan_hand_history_folder():
    """
    Walk through RAW_HANDS_DIR and one level of subdirectories to
    find .txt files. Splits each file into hands, filters out processed ones,
    and returns list of (hand_id, file_path, raw_hand_text).
    """
    new_hands = []
    file_paths = []

    # Gather .txt files in top-level and one subdirectory
    for entry in os.listdir(ALL_HANDS):
        path = os.path.join(ALL_HANDS, entry)
        if os.path.isdir(path):
            for fname in os.listdir(path):
                if fname.lower().endswith(".txt"):
                    file_paths.append(os.path.join(path, fname))
        elif entry.lower().endswith(".txt"):
            file_paths.append(path)

    # Process each file
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        hands = split_hands(content)
        print(f"Found {len(hands)} hands in {os.path.basename(file_path)}")

        for raw in hands:
            hand_id = get_hand_id(raw)
            if not hand_id or hand_already_processed(hand_id):
                continue

            # Mark this hand as processed
            add_hand_id(hand_id)
            new_hands.append((hand_id, file_path, raw))

    return new_hands


# Example usage
if __name__ == '__main__':
    new_hands = scan_hand_history_folder()
    print(f"Total new hands to process: {len(new_hands)}")
    for hid, path, raw in new_hands[:5]:
        print(f"  {hid} from {os.path.basename(path)}")
