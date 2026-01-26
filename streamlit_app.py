#
#BallDontlie
#
import requests
import pandas as pd

BASE_URL = "https://www.balldontlie.io/api/v1"

def get_player_id(player_name):
    res = requests.get(f"{BASE_URL}/players", params={"search": player_name})
    data = res.json()["data"]
    if not data:
        return None
    return data[0]["id"]

def get_last_games(player_id, num_games=10):
    res = requests.get(
        f"{BASE_URL}/stats",
        params={
            "player_ids[]": player_id,
            "per_page": num_games,
            "postseason": False
        }
    )
    stats = res.json()["data"]

    if not stats:
        return None

    df = pd.DataFrame([{
        "pts": s["pts"],
        "ast": s["ast"],
        "reb": s["reb"],
        "opponent": s["game"]["home_team"]["abbreviation"]
        if s["team"]["id"] != s["game"]["home_team_id"]
        else s["game"]["visitor_team"]["abbreviation"]
    } for s in stats])

    return df

import streamlit as st

# ===============================
# 🧠 BET EVALUATION LOGIC
# ===============================
def evaluate_prop(player, prop, line, opponent):
    season_avg = {"PTS": 30.2, "AST": 8.4, "REB": 8.9}
    last10_avg = {"PTS": 32.5, "AST": 9.1, "REB": 9.6}
    hit_rate = {"PTS": 0.70, "AST": 0.65, "REB": 0.60}
    matchup_modifier = {"PTS": 0.55, "AST": 0.52, "REB": 0.48}
    trend = {"PTS": 0.60, "AST": 0.58, "REB": 0.55}

    season_score = min(season_avg[prop] / line, 1)
    recent_score = min(last10_avg[prop] / line, 1)

    probability = (
        season_score * 0.30 +
        recent_score * 0.25 +
        hit_rate[prop] * 0.20 +
        matchup_modifier[prop] * 0.15 +
        trend[prop] * 0.10
    ) * 100

    if probability >= 65:
        verdict = "✅ Good Bet"
    elif probability >= 55:
        verdict = "⚠️ Lean"
    else:
        verdict = "❌ Pass"

    explanation = [
        f"Season avg: {season_avg[prop]} vs line {line}",
        f"Last 10 avg: {last10_avg[prop]}",
        f"Hit rate over line: {int(hit_rate[prop]*100)}%",
        f"Matchup favorability: {int(matchup_modifier[prop]*100)}%",
        f"Recent trend score: {int(trend[prop]*100)}%"
    ]

    return {
        "player": player,
        "prop": prop,
        "line": line,
        "opponent": opponent,
        "probability": round(probability, 1),
        "verdict": verdict,
        "explanation": explanation
    }

# ===============================
# 🌐 STREAMLIT UI
# ===============================
st.set_page_config(page_title="Props AI", layout="centered")

st.title("🏀 Props AI")
st.subheader("Is this prop a good bet?")

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
        
