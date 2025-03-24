from flask import Flask, jsonify, request
import joblib
import pandas as pd
from datetime import datetime
from understat import get_upcoming_matches, fetch_la_liga_teams, fetch_team_stats 
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

model = joblib.load("models/nb_model.pkl")

feature_names = [
    "venue_code", "opp_code", "hour", "day_code", "goal_diff_rolling",
    "gf_rolling", "ga_rolling", "sh_rolling", "sot_rolling", "dist_rolling",
    "fk_rolling", "pk_rolling", "pkatt_rolling"
]

@app.route("/")
def home():
    return "Flask backend is running!"

@app.route("/api/upcoming-matches", methods=["GET"])
def upcoming_matches():
    matches = get_upcoming_matches()
    formatted_matches = []
    for match in matches:
        if isinstance(match['date'], str):
            match_date = datetime.strptime(match['date'], "%Y-%m-%d %H:%M:%S")
        else:
            match_date = match['date']
        formatted_matches.append({
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'date': match_date.isoformat()
        })
    return jsonify(formatted_matches)

def generate_team_mapping(teams):
    sorted_teams = sorted(teams.keys())
    team_mapping = {team: idx + 1 for idx, team in enumerate(sorted_teams)}
    return team_mapping

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.json

    team_a = data.get('team_a')
    team_b = data.get('team_b')
    hour = int(data.get('hour'))
    day_code = int(data.get('day_code'))

    try:
        la_liga_teams = fetch_la_liga_teams()
    except Exception as e:
        return jsonify({"error": f"Failed to fetch La Liga teams: {str(e)}"}), 500

    team_mapping = generate_team_mapping(la_liga_teams)

    if team_a not in la_liga_teams or team_b not in la_liga_teams:
        return jsonify({"error": "One or both teams are not in La Liga"}), 400

    try:
        team_a_stats = fetch_team_stats(la_liga_teams[team_a])
    except Exception as e:
        return jsonify({"error": f"Failed to fetch stats: {str(e)}"}), 500

    input_data = pd.DataFrame({
        "venue_code": [1],  # 1 for home (team_a), 0 for away
        "opp_code": [team_mapping.get(team_b)], 
        "hour": [hour],       
        "day_code": [day_code],    
        "goal_diff_rolling": [team_a_stats['goals_scored'] - team_a_stats['goals_conceded']],
        "gf_rolling": [team_a_stats['goals_scored']],  # Goals for (team_a)
        "ga_rolling": [team_a_stats['goals_conceded']],  # Goals against (team_a)
        "sh_rolling": [team_a_stats['shots']],  # Shots (team_a)
        "sot_rolling": [team_a_stats['shots_on_target']],  # Shots on target (team_a)
        "dist_rolling": [team_a_stats['average_distance']],  # Average shot distance (team_a)
        "fk_rolling": [team_a_stats['free_kicks']],  # Free kicks (team_a)
        "pk_rolling": [team_a_stats['penalties_scored']],  # Penalties scored (team_a)
        "pkatt_rolling": [team_a_stats['penalties_attempted']],  # Penalties attempted (team_a)
    })

    input_data = input_data[feature_names]

    probabilities = model.predict_proba(input_data)[0]
    return jsonify({
        'win_a': probabilities[0],
        'win_b': probabilities[1],
        'draw': probabilities[2]
    })

@app.route("/api/odds", methods=["POST"])
def odds_calculator():
    data = request.json
    stake = float(data['stake'])
    odds = float(data['odds'])

    if odds > 0:
        profit = stake * (odds / 100)
    else:
        profit = (stake / abs(odds)) * 100
    payout = profit + stake
    return jsonify({'profit': profit, 'payout': payout})

@app.route("/api/facts", methods=["GET"])
def facts():
    league_facts = [
        "La Liga was founded in 1929",
        "Real Madrid holds the record for most titles (35)",
        "The El Clásico (Real Madrid vs Barcelona) is the most watched club match in the world",
        "Only 9 teams have never been relegated from La Liga",
        "The fastest goal in La Liga history was scored in 7.42 seconds by Joseba Llorente in 2008",
        "Lionel Messi holds the record for most goals in a single season (50 goals in 2011-12)"
    ]
    return jsonify(league_facts)

if __name__ == "__main__":
    app.run(debug=True)