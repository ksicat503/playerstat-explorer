# main.py

from src.db import create_tables, add_or_update_player, update_player_stats
from src.file_scanner import scan_hand_history_folder
from src.parser import parse_hand


def main():
    # Ensure DB schema exists
    create_tables()

    # Fetch unprocessed hands (hand_id, file_path, raw_text)
    hands = scan_hand_history_folder()
    print(f"Processing {len(hands)} new hands...")

    for hand_id, file_path, raw in hands:
        stats = parse_hand(raw)
        if not stats:
            print(f"Skipping hand {hand_id}: malformed or incomplete.")
            continue

        # Persist each player's stats
        for player, s in stats.items():
            pid = add_or_update_player(player)
            update_player_stats(
                player_id=pid,
                position=['position'],
                vpip_count=s['vpip'],
                pfr_count=s['pfr'],
                hands_played=s['hands_played'],
                three_bet_count=s['three_bet'],
                fold_to_four_bet_count=0,
                total_four_bet_opportunities=0
            )
        print(f"Saved stats for hand {hand_id} from {file_path}")

    print("Done.")


if __name__ == "__main__":
    main()
