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
    """
    Evaluates whether a prop bet is a good bet using real balldontlie stats.
    prop: 'PTS', 'AST', 'REB'
    line: the prop line
    opponent: opponent team abbreviation
    """
    # 1️⃣ Get player ID
    player_id = get_player_id(player)
    if not player_id:
        return {
            "player": player,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Player not found",
            "explanation": ["Player name not found in database."]
        }

    # 2️⃣ Get last 10 games
    df = get_last_games(player_id, num_games=10)
    if df is None or df.empty:
        return {
            "player": player,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ No recent games",
            "explanation": ["No recent game stats available."]
        }

    # 3️⃣ Map prop to column
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

    # 4️⃣ Compute metrics
    season_avg = df[col].mean()                   # avg of last 10 games (as proxy for season)
    last5_avg = df[col].tail(5).mean()           # last 5 games average
    hit_rate = (df[col] > line).sum() / len(df)  # fraction over line

    # 5️⃣ Simple scoring formula
    season_score = min(season_avg / line, 1)
    recent_score = min(last5_avg / line, 1)
    probability = (season_score*0.35 + recent_score*0.30 + hit_rate*0.35) * 100

    # 6️⃣ Verdict thresholds
    if probability >= 65:
        verdict = "✅ Good Bet"
    elif probability >= 55:
        verdict = "⚠️ Lean"
    else:
        verdict = "❌ Pass"

    # 7️⃣ Explanation bullets
    explanation = [
        f"Season avg (proxy from last 10 games): {season_avg:.1f} vs line {line}",
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
        
