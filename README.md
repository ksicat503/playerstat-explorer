# Player Stat Explorer

A simple Python project that parses PokerStars hand history text files, computer per-player preflop statistics (VPIP, PFR, 3-bet), 
stores them in SQLite, and provides a Streamlit dashboard for exploring individual player metrics compared to the population's average.

## Description
This program reads raw PokerStars hand history `.txt.` files, extracts each invidual hand, and then computers the following basic preflop metrics for each player:
- Hands played
- VPIP (Voluntarily Put Money in Pot)
- PFR (Preflop Raise %)
- 3-bet percentage

All this hand data in stored in a local SQLite database. A Streamlit-based web interface allows for you to search for any player and view their metrics compared to the population average of your data. 

## Running the Program
1. Ingestion Pipeline  
```python main.py```
    - Scans for new hand files and parses each for desired stats
    - Stores results in poker_model.db

2. Streamlit Dashboard (for player stat visualization)  
```streamlit run app.py```
    - Launches a local web server
    - Searchable dropdown menu for all players in database and displays their stat lines and population comparison

