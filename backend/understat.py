from understatapi import UnderstatClient
from datetime import datetime
import requests

def get_upcoming_matches():
    with UnderstatClient() as understat:
        match_data = understat.league(league="La_Liga").get_match_data(season='2025')
        
        upcoming = []
        current_time = datetime.now()
        
        for match in match_data:
            match_time = datetime.strptime(match['datetime'], '%Y-%m-%d %H:%M:%S')
            
            if match_time > current_time and not match['isResult']:
                upcoming.append({
                    'date': match['datetime'],
                    'home_team': match['h']['title'],
                    'away_team': match['a']['title']
                })
                
                if len(upcoming) == 5:
                    break
        
        return upcoming
    
def fetch_la_liga_teams():
    url = "https://www.thesportsdb.com/api/v1/json/3/search_all_teams.php?l=Spanish%20La%20Liga"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        teams = {team['strTeam']: team['idTeam'] for team in data['teams']}
        return teams
    else:
        raise Exception("Failed to fetch La Liga teams")
    
def fetch_team_stats(team_id):
    url = f"https://www.thesportsdb.com/api/v1/json/3/lookupteam.php?id={team_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        team_data = data['teams'][0]
        return {
            "goals_scored": int(team_data.get('intGoalsScored', 0)),
            "goals_conceded": int(team_data.get('intGoalsConceded', 0)),
            "shots": int(team_data.get('intShots', 0)),
            "shots_on_target": int(team_data.get('intShotsOnTarget', 0)),
            "average_distance": float(team_data.get('strAverageDistance', 0.0)),
            "free_kicks": int(team_data.get('intFreeKicks', 0)),
            "penalties_scored": int(team_data.get('intPenaltiesScored', 0)),
            "penalties_attempted": int(team_data.get('intPenaltiesAttempted', 0))
        }
    else:
        raise Exception(f"Failed to fetch stats for team ID {team_id}")
    
def generate_team_mapping(teams):
    sorted_teams = sorted(teams.keys())
    team_mapping = {team: idx + 1 for idx, team in enumerate(sorted_teams)}
    return team_mapping
