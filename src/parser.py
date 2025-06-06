"""
parser.py

Parses individual PokerStars hand history strings to extract player
seat assignments, button position, and preflop statistics (VPIP,
PFR, 3-bet, hands played) per player.

Functions:
    - determine_positions(seats, button_seat)
    - parse_hand(hand_text)

Usage:
    from src.parser import parse_hand
    stats = parse_hand(raw_hand_text)
"""

import re
from collections import defaultdict

# Regex patterns for parsing
SEAT_LINE = re.compile(r"^Seat (\d+): (\w+) \(\$?([\d.]+) in chips\)")
BUTTON_LINE = re.compile(r"Table '.*' (\d+)-max Seat #(\d+) is the button")
ACTION_LINE = re.compile(r"^(\w+): (folds|calls|checks|bets|raises)(.*)")

# Position labels by table size for max 6 players
POSITION_MAP_BY_SIZE = {
    2: ["BTN", "BB"],
    3: ["BTN", "SB", "BB"],
    4: ["BTN", "SB", "BB", "CO"],
    5: ["BTN", "SB", "BB", "UTG", "CO"],
    6: ["BTN", "SB", "BB", "UTG", "HJ", "CO"],
}


def determine_positions(seats, button_seat):
    """
    Assign seat positions dynamically based on actual number of seated players.

    Args:
        seats (dict): {seat_number: {"name": str, "chips": float}}
        button_seat (int): seat number holding the dealer button

    Returns:
        dict: player_name -> position label
    """
    n_players = len(seats)
    labels = POSITION_MAP_BY_SIZE.get(n_players)
    if labels is None:
        # fallback: first three positions, then EP
        labels = ["BTN", "SB", "BB"] + [f"EP{i}" for i in range(n_players - 3)]

    seat_order = sorted(seats.keys())
    # Ensure the button seat is valid
    if button_seat not in seat_order:
        return {}
    button_index = seat_order.index(button_seat)
    rotated = seat_order[button_index:] + seat_order[:button_index]

    pos_map = {}
    for i, seat_num in enumerate(rotated):
        pos = labels[i] if i < len(labels) else f"EP{i}"
        player = seats[seat_num]["name"]
        pos_map[player] = pos
        seats[seat_num]['position'] = pos
    return pos_map


def parse_hand(hand_text):
    """
    Parse a raw hand history string and compute per-player preflop stats.

    Args:
        hand_text (str): complete text of one PokerStars hand history

    Returns:
        dict: {player_name:
              {"hands_played", "vpip", "pfr", "three_bet", "position}
              }

              or None if parsing fails
    """
    lines = hand_text.strip().splitlines()
    seats = {}
    button_seat = None

    # First pass: collect seats and button info
    for line in lines:
        m = SEAT_LINE.match(line)
        if m:
            seat_num, name, chips = m.groups()
            seats[int(seat_num)] = {"name": name, "chips": float(chips)}
            continue
        m = BUTTON_LINE.match(line)
        if m:
            button_seat = int(m.group(2))

    # Guard malformed hands
    if not seats or button_seat is None:
        return None
    if button_seat not in seats:
        return None

    # Determine dynamic positions
    positions = determine_positions(seats, button_seat)
    if not positions:
        return None

    # Initialize stats
    stats = defaultdict(lambda: {"hands_played": 0, "vpip": 0, "pfr": 0,
                                 "three_bet": 0, "position": ""})
    for seat in seats.values():
        name = seat['name']
        stats[name]['hands_played'] = 1
        stats[name]['position'] = positions.get(name, "")

    # Second pass: track preflop actions
    preflop = False
    for line in lines:
        if line.startswith("*** HOLE CARDS ***"):
            preflop = True
            continue
        if line.startswith("*** FLOP ***"):
            break
        if preflop:
            m = ACTION_LINE.match(line)
            if m:
                player, action, _ = m.groups()
                if action in ("calls", "raises"):
                    stats[player]['vpip'] += 1
                if action == 'raises':
                    # first raise counts as PFR, subsequent as 3-bet
                    if stats[player]['pfr'] == 0:
                        stats[player]['pfr'] += 1
                    else:
                        stats[player]['three_bet'] += 1

    return stats


if __name__ == "__main__":
    # Checks positions for 2 - 6 people in table
    for n in range(2, 7):
        sample = {i: {"name": f"P{i}", "chips": 100} for i in range(1, n+1)}
        print(f"{n}-max mapping:", determine_positions(sample, button_seat=n))
    print()
