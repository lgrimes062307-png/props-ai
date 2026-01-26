import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Props AI", layout="centered")
st.title("🏀 Props AI")
st.subheader("Evaluate a player's prop bet using live NBA stats")

# ===============================
#  1️⃣ Function to fetch player stats from your NBA API
# ===============================
def get_player_stats(player_name, last_games=10):
    """
    Fetch last N games stats for a player from your NBA API.
    Expected output: list of dicts with 'pts', 'ast', 'reb'.
    """
    try:
        url = "https://your-nba-api.com/player_stats"  # <-- replace with your API endpoint
        params = {
            "player": player_name,
            "last_games": last_games
        }
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        df = pd.DataFrame(data)
        if df.empty:
            return None
        return df
    except requests.exceptions.RequestException as e:
        st.warning(f"API request failed: {e}")
        return None

# ===============================
#  2️⃣ Evaluate prop bet
# ===============================
def evaluate_prop(player_name, prop, line, opponent):
    df = get_player_stats(player_name)
    
    if df is None:
        return {
            "player": player_name,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "⚠️ No stats",
            "explanation": ["No stats available from API for this player."]
        }

    prop_map = {"PTS": "pts", "AST": "ast", "REB": "reb"}
    if prop not in prop_map:
        return {
            "player": player_name,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "❌ Invalid prop",
            "explanation": ["Choose PTS, AST, or REB."]
        }

    col = prop_map[prop]
    season_avg = df[col].mean()
    last5_avg = df[col].tail(5).mean()
    hit_rate = (df[col] > line).sum() / len(df)
    probability = (season_avg/line*0.35 + last5_avg/line*0.30 + hit_rate*0.35)*100

    if probability >= 65:
        verdict = "✅ Good Bet"
    elif probability >= 55:
        verdict = "⚠️ Lean"
    else:
        verdict = "❌ Pass"

    explanation = [
        f"Season avg (last {len(df)} games): {season_avg:.1f} vs line {line}",
        f"Last 5 games avg: {last5_avg:.1f}",
        f"Hit rate over line: {int(hit_rate*100)}%",
        f"Probability score: {probability:.1f}%"
    ]

    return {
        "player": player_name,
        "prop": prop,
        "line": line,
        "opponent": opponent,
        "probability": round(probability,1),
        "verdict": verdict,
        "explanation": explanation
    }

# ===============================
#  3️⃣ Streamlit UI
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


