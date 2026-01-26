# ===============================
#  PROPS AI - STREAMLIT READY
# ===============================

import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Props AI", layout="centered")
st.title("🏀 Props AI")
st.subheader("Evaluate a player's prop bet using real NBA stats")

# ===============================
#  1️⃣ Load all players locally
# ===============================

@st.cache_data
def load_all_players():
    # Make sure this CSV is in the same folder as streamlit_app.py
    df = pd.read_csv("nba_rosters_30_teams_full.csv")
    return df

players_df = load_all_players()
st.write(f"Loaded {len(players_df)} players")

# ===============================
#  2️⃣ Player lookup
# ===============================

def get_player_id_local(player_name):
    """Return player ID from CSV using partial, case-insensitive match"""
    name_lower = player_name.lower()
    matches = players_df[players_df["player_name"].str.lower().str.contains(name_lower)]
    if matches.empty:
        return None
    # Return the player row (we’ll use name and team)
    return matches.iloc[0]

# ===============================
#  3️⃣ Fetch last N games stats from balldontlie
# ===============================

def get_last_games(player_name, team_abbr, num_games=10):
    """Fetch last N games from balldontlie for a player"""
    # First, search player by name and team
    try:
        res = requests.get(
            "https://www.balldontlie.io/api/v1/players",
            params={"search": player_name}
        )
        res.raise_for_status()
        data = res.json().get("data", [])
        if not data:
            return None
        # Find the exact team match
        player_id = None
        for p in data:
            if p["team"]["abbreviation"].upper() == team_abbr.upper():
                player_id = p["id"]
                break
        if player_id is None:
            player_id = data[0]["id"]  # fallback to first match

        # Fetch last games
        res2 = requests.get(
            "https://www.balldontlie.io/api/v1/stats",
            params={
                "player_ids[]": player_id,
                "per_page": num_games,
                "postseason": False
            }
        )
        res2.raise_for_status()
        stats = res2.json().get("data", [])
        if not stats:
            return None

        # Convert to DataFrame
        df = pd.DataFrame([{
            "pts": s["pts"],
            "ast": s["ast"],
            "reb": s["reb"],
            "opponent": s["game"]["home_team"]["abbreviation"]
            if s["team"]["id"] != s["game"]["home_team"]["id"]
            else s["game"]["visitor_team"]["abbreviation"]
        } for s in stats])
        return df
    except:
        return None

# ===============================
#  4️⃣ Evaluate prop bet
# ===============================

def evaluate_prop(player_name, prop, line, opponent):
    player_row = get_player_id_local(player_name)
    if player_row is None:
        return {
            "player": player_name,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Player not found",
            "explanation": ["Player not found in CSV."]
        }

    player_name_csv = player_row["player_name"]
    team_abbr = player_row["team_name"]

    df = get_last_games(player_name_csv, team_abbr, num_games=10)
    if df is None or df.empty:
        return {
            "player": player_name_csv,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ No recent games",
            "explanation": ["No recent stats available from balldontlie."]
        }

    prop_map = {"PTS": "pts", "AST": "ast", "REB": "reb"}
    if prop not in prop_map:
        return {
            "player": player_name_csv,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Invalid prop",
            "explanation": ["Choose PTS, AST, or REB."]
        }

    col = prop_map[prop]

    # Metrics
    season_avg = df[col].mean()                   # last 10 games proxy
    last5_avg = df[col].tail(5).mean()           # last 5 games
    hit_rate = (df[col] > line).sum() / len(df)  # fraction over line

    # Scoring formula
    season_score = min(season_avg / line, 1)
    recent_score = min(last5_avg / line, 1)
    probability = (season_score*0.35 + recent_score*0.30 + hit_rate*0.35) * 100

    # Verdict
    if probability >= 65:
        verdict = "✅ Good Bet"
    elif probability >= 55:
        verdict = "⚠️ Lean"
    else:
        verdict = "❌ Pass"

    explanation = [
        f"Season avg (last 10 games proxy): {season_avg:.1f} vs line {line}",
        f"Last 5 games avg: {last5_avg:.1f}",
        f"Hit rate over line: {int(hit_rate*100)}%",
        f"Probability score: {probability:.1f}%"
    ]

    return {
        "player": player_name_csv,
        "prop": prop,
        "line": line,
        "opponent": opponent,
        "probability": round(probability,1),
        "verdict": verdict,
        "explanation": explanation
    }

# ===============================
#  5️⃣ Streamlit UI
# ===============================

player_input = st.text_input("Player Name", "Luka Doncic")
prop_input = st.selectbox("Prop Type", ["PTS", "AST", "REB"])
line_input = st.number_input("Prop Line", min_value=0.0, value=29.5)
opponent_input = st.text_input("Opponent (Team Abbrev)", "GSW")

if st.button("Evaluate Bet"):
    result = evaluate_prop(player_input, prop_input, line_input, opponent_input)
    st.markdown(f"## {result['verdict']}")
    st.metric("Confidence", f"{result['probability']}%")
    st.markdown("### 📊 Why this bet:")
    for reason in result["explanation"]:
        st.write("•", reason)

