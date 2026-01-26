import streamlit as st
import pandas as pd
from io import StringIO
import requests

st.set_page_config(page_title="Props AI", layout="centered")
st.title("🏀 Props AI")
st.subheader("Evaluate a player's prop bet using real NBA stats")

# ===============================
#  1️⃣ Embedded NBA players CSV
# ===============================

CSV_STRING = """player_name,team_name,position
LeBron James,LAL,SF
Anthony Davis,LAL,PF
D'Angelo Russell,LAL,PG
Austin Reaves,LAL,SG
Jarred Vanderbilt,LAL,C
Stephen Curry,GSW,PG
Klay Thompson,GSW,SG
Draymond Green,GSW,PF
Kevon Looney,GSW,C
Andrew Wiggins,GSW,SF
Giannis Antetokounmpo,MIL,PF
Khris Middleton,MIL,SF
Jrue Holiday,MIL,PG
Brook Lopez,MIL,C
Grayson Allen,MIL,SG
Kevin Durant,BKN,SF
Kyrie Irving,BKN,PG
Ben Simmons,BKN,PF
Nicolas Claxton,BKN,C
Joe Harris,BKN,SG
Joel Embiid,PHI,C
James Harden,PHI,SG
Tyrese Maxey,PHI,PG
Tobias Harris,PHI,PF
PJ Tucker,PHI,SF
Luka Doncic,DAL,PG
Kyrie Irving,DAL,SG
Christian Wood,DAL,C
Dorian Finney-Smith,DAL,SF
Reggie Bullock,DAL,SF
Jayson Tatum,BOS,SF
Jaylen Brown,BOS,SG
Marcus Smart,BOS,PG
Robert Williams,BOS,C
Al Horford,BOS,PF
Nikola Jokic,DEN,C
Jamal Murray,DEN,PG
Michael Porter Jr,DEN,SF
Aaron Gordon,DEN,PF
Kentavious Caldwell-Pope,DEN,SG
Damian Lillard,POR,PG
CJ McCollum,POR,SG
Jusuf Nurkic,POR,C
Anfernee Simons,POR,SG
Scoot Henderson,POR,PG
Devin Booker,PHX,SG
Kevin Durant,PHX,SF
Deandre Ayton,PHX,C
Chris Paul,PHX,PG
Mikal Bridges,PHX,SF
Anthony Edwards,MIN,SG
Karl-Anthony Towns,MIN,C
Rudy Gobert,MIN,C
D'Angelo Russell,MIN,PG
Jaden McDaniels,MIN,SF
Bradley Beal,WAS,SG
Kristaps Porzingis,WAS,C
Davis Bertans,WAS,PF
Kyle Kuzma,WAS,SF
Spencer Dinwiddie,WAS,PG
Ja Morant,MEM,PG
Jaren Jackson Jr,MEM,PF
Desmond Bane,MEM,SG
Steven Adams,MEM,C
Tyus Jones,MEM,PG
Donovan Mitchell,CLE,SG
Evan Mobley,CLE,C
Darius Garland,CLE,PG
Jarrett Allen,CLE,C
Caris LeVert,CLE,SG
Zion Williamson,NOP,PF
CJ McCollum,NOP,SG
Brandon Ingram,NOP,SF
Jonas Valanciunas,NOP,C
Herb Jones,NOP,SF
Jimmy Butler,MIA,SF
Bam Adebayo,MIA,C
Kyle Lowry,MIA,PG
Tyler Herro,MIA,SG
Duncan Robinson,MIA,SG
De'Aaron Fox,SAC,PG
Domantas Sabonis,SAC,PF
Harrison Barnes,SAC,SF
Richaun Holmes,SAC,C
Keegan Murray,SAC,SF
Trae Young,ATL,PG
Dejounte Murray,ATL,PG
John Collins,ATL,PF
Clint Capela,ATL,C
Bogdan Bogdanovic,ATL,SG
Pascal Siakam,TOR,PF
Fred VanVleet,TOR,PG
OG Anunoby,TOR,SF
Scottie Barnes,TOR,SF
Chris Boucher,TOR,C
Shai Gilgeous-Alexander,OKC,PG
Josh Giddey,OKC,PG
Luguentz Dort,OKC,SG
Chet Holmgren,OKC,C
Jalen Williams,OKC,SF
Julius Randle,NYK,PF
Jalen Brunson,NYK,PG
RJ Barrett,NYK,SG
Mitchell Robinson,NYK,C
Jalen Green,HOU,SG
Kevin Porter Jr,HOU,SG
Jabari Smith,HOU,PF
Alperen Sengun,HOU,C
"""

# Load CSV from string
@st.cache_data
def load_all_players():
    df = pd.read_csv(StringIO(CSV_STRING))
    return df

players_df = load_all_players()
st.write(f"Loaded {len(players_df)} players")

# ===============================
#  2️⃣ Player lookup function
# ===============================

def get_player_id_local(player_name):
    """Return player row from embedded CSV"""
    name_lower = player_name.lower()
    matches = players_df[players_df["player_name"].str.lower().str.contains(name_lower)]
    if matches.empty:
        return None
    return matches.iloc[0]

# ===============================
#  3️⃣ Fetch last games from balldontlie (optional)
# ===============================

def get_last_games(player_name, num_games=10):
    """Fetch last N games stats for a player"""
    try:
        # search player by name only
        res = requests.get(
            "https://www.balldontlie.io/api/v1/players",
            params={"search": player_name}
        )
        res.raise_for_status()
        data = res.json().get("data", [])
        if not data:
            return None

        player_id = data[0]["id"]  # just take the first match
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

    df = get_last_games(player_name_csv, num_games=10)
    if df is None or df.empty:
        return {
            "player": player_name_csv,
            "prop": prop,
            "line": line,
            "opponent": opponent,
            "probability": 0,
            "verdict": "⚠️ No API stats",
            "explanation": ["No recent stats available from balldontlie, fallback to CSV only."]
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


