# ===============================
# Props AI — Official NBA.com Stats
# Single-file Streamlit App
# ===============================

import time
import pandas as pd
import streamlit as st

from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog

# -------------------------------
# Streamlit setup
# -------------------------------
st.set_page_config(page_title="Props AI", layout="centered")
st.title("🏀 Props AI")
st.caption("Powered by official NBA.com data (nba_api)")

# -------------------------------
# Find player ID (fuzzy search)
# -------------------------------
@st.cache_data
def find_player_id(player_name):
    """
    Finds NBA player ID using fuzzy name matching
    """
    matches = players.find_players_by_full_name(player_name)
    if not matches:
        return None
    return matches[0]["id"]

# -------------------------------
# Get last N games stats
# -------------------------------
@st.cache_data
def get_last_games_stats(player_id, num_games=10):
    """
    Fetch last N games for a player
    Returns DataFrame with PTS, AST, REB
    """
    time.sleep(0.6)  # IMPORTANT: avoid NBA.com rate limiting

    gamelog = playergamelog.PlayerGameLog(
        player_id=player_id,
        season="2024-25"
    )

    df = gamelog.get_data_frame()
    if df.empty:
        return None

    df = df.head(num_games)
    return df[["GAME_DATE", "MATCHUP", "PTS", "AST", "REB"]]

# -------------------------------
# Evaluate prop bet
# -------------------------------
def evaluate_prop(player_name, prop, line):
    player_id = find_player_id(player_name)
    if player_id is None:
        return None, "Player not found"

    df = get_last_games_stats(player_id)
    if df is None:
        return None, "No game data available"

    stat_col = {"PTS": "PTS", "AST": "AST", "REB": "REB"}[prop]

    season_avg = df[stat_col].mean()
    last5_avg = df[stat_col].head(5).mean()
    hit_rate = (df[stat_col] > line).mean()

    probability = (
        (season_avg / line) * 0.35 +
        (last5_avg / line) * 0.30 +
        hit_rate * 0.35
    ) * 100

    verdict = (
        "✅ Good Bet" if probability >= 65 else
        "⚠️ Lean" if probability >= 55 else
        "❌ Pass"
    )

    result = {
        "verdict": verdict,
        "probability": round(probability, 1),
        "season_avg": round(season_avg, 1),
        "last5_avg": round(last5_avg, 1),
        "hit_rate": round(hit_rate * 100, 1),
        "games": df
    }

    return result, None

# -------------------------------
# Streamlit UI
# -------------------------------
player_input = st.text_input("Player Name", "Luka Doncic")
prop_input = st.selectbox("Prop Type", ["PTS", "AST", "REB"])
line_input = st.number_input("Prop Line", min_value=0.0, value=29.5)

if st.button("Evaluate Bet"):
    result, error = evaluate_prop(player_input, prop_input, line_input)

    if error:
        st.error(error)
    else:
        st.subheader(result["verdict"])
        st.metric("Confidence", f"{result['probability']}%")

        st.markdown("### 📊 Why this bet:")
        st.write(f"- Season avg: **{result['season_avg']}**")
        st.write(f"- Last 5 games avg: **{result['last5_avg']}**")
        st.write(f"- Hit rate over line: **{result['hit_rate']}%**")

        st.markdown("### 🕒 Recent Games")
        st.dataframe(result["games"], use_container_width=True)
