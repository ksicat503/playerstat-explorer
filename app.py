import streamlit as st
import pandas as pd
from src.db import (
    get_player_overall_stats,
    get_population_stats,
    get_all_player_names,
)

# Path to SQLite database
DB_PATH = "poker_model.db"

# --- Streamlit Layout ---
st.set_page_config(page_title="Player Stats", layout="wide")
st.title("🔍 Player Stats Viewer")

# --- Sidebar: Show All Players ---
player_list = get_all_player_names()
if st.sidebar.checkbox("Show all players in database"):
    st.subheader("All Players")
    df_all = pd.DataFrame(player_list, columns=["Player"])
    st.dataframe(df_all, width=300, height=400)

# --- Main: Player Selection ---
player_name = st.selectbox(
    "Select a player to view stats:",
    options=[""] + player_list,
    format_func=lambda x: x or "— select a player —"
)

if player_name:
    # Fetch player and population stats
    pl_stats = get_player_overall_stats(player_name)
    pop_stats = get_population_stats()

    if pl_stats is None:
        st.error(f"Player '{player_name}' not found in the database.")
    else:
        # --- Metrics Cards ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Hands Played", pl_stats["hands"])
        col2.metric("VPIP %", f"{pl_stats['vpip_pct']}%")
        col3.metric("PFR %", f"{pl_stats['pfr_pct']}%")
        col4.metric("3-bet %", f"{pl_stats['three_bet_pct']}%")

        # --- Population Averages ---
        st.subheader("Population Averages")
        col5, col6, col7 = st.columns(3)
        col5.metric("VPIP %", f"{pop_stats['vpip_pct']}%")
        col6.metric("PFR %", f"{pop_stats['pfr_pct']}%")
        col7.metric("3-bet %", f"{pop_stats['three_bet_pct']}%")
else:
    st.info("Please select a player from the dropdown to view stats.")
