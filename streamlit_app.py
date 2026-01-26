# ===============================
#  PROPS AI - FULL WORKING VERSION
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
import pandas as pd
import streamlit as st

@st.cache_data
def load_all_players():
    df = pd.read_csv("nba_rosters_30_teams_full.csv")
    return df

players_df = load_all_players()
st.write(f"Loaded {len(players_df)} players")

# ===============================
#  2️⃣ Fetch last N games
# ===============================

def get_last_games(player_id, num_games=10):
    try:
        res = requests.get(
            "https://www.balldontlie.io/api/v1/stats",
            params={
                "player_ids[]": player_id,
                "per_page": num_games,
                "postseason": False
            }
        )
        res.raise_for_status()
        stats = res.json().get("data", [])
        if not stats:
            return None
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
#  3️⃣ Evaluate prop bet
# ===============================

def evaluate_prop(player, prop, line, opponent):
    player_id = get_player_id_local(player)
    if not player_id:
        return {
            "player": player,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Player not found",
            "explanation": ["Player not found in database."]
        }

    df = get_last_games(player_id, num_games=10)
    if df is None or df.empty:
        return {
            "player": player,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ No recent games",
            "explanation": ["No recent stats available."]
        }

    prop_map = {"PTS": "pts", "AST": "ast", "REB": "reb"}
    if prop not in prop_map:
        return {
            "player": player,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Invalid prop",
            "explanation": ["Choose PTS, AST, or REB."]
        }

    col = prop_map[prop]

    # Metrics
    season_avg = df[col].mean()                   # last 10 games proxy for season
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
        "player": player,
        "prop": prop,
        "line": line,
        "opponent": opponent,
        "probability": round(probability,1),
        "verdict": verdict,
        "explanation": explanation
    }

# ===============================
#  4️⃣ Streamlit UI
# ===============================

player = st.text_input("Player Name", "Luka Doncic")
prop = st.selectbox("Prop Type", ["PTS", "AST", "REB"])
line = st.number_input("Prop Line", min_value=0.0, value=29.5)
opponent = st.text_input("Opponent (Team Abbrev)", "GSW")

if st.button("Evaluate Bet"):
    result = evaluate_prop(player, prop, line, opponent)

    st.markdown(f"## {result['verdict']}")
    st.metric("Confidence", f"{result['probability']}%")

    st.markdown("### 📊 Why this bet:")
    for reason in result["explanation"]:
        st.write("•", reason)

