import sys
sys.path.append('/usr/local/lib/python3.8/site-packages/')

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key
import time
import sqlite3

#name of the cache
CACHE_FILENAME = "cache.json"

def open_cache():
    ''' opens the cache file if it exists and loads the JSON into
    the CACHE dictionary.

    if the cache file doesn't exist, creates a new cache dictionary
    
    Parameters
    ----------
    None

    Returns
    -------
    The opened cache
    '''
    try:
        cache_file = open(CACHE_FILENAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict

def save_cache(cache_dict):
    ''' saves the current state of the cache to disk
    Parameters
    ----------
    cache_dict: dict
        The dictionary to save
    Returns
    -------
    None
    '''
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILENAME,"w")
    fw.write(dumped_json_cache)
    fw.close()

def construct_unique_key(category, params):
    ''' constructs a key that is guaranteed to uniquely and 
    repeatably identify an API request by its params, API_KEY is not cached here

    Parameters
    ----------
    category: string
        A piece of url after the base url for the search category
    params: dict
        A dictionary of param:value pairs, without api_key
    
    Returns
    -------
    string
        the unique key as a string
    '''
    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = category + connector + connector.join(param_strings)
    return unique_key

def get_data(category, params):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    category: string
        A piece of url after the base url for the search category
    params: dict
        a dictionary of parameters without API_KEY
    
    Returns
    -------
    dict
        a converted API return from Dota2 API
    '''
    base_url = "http://api.opendota.com/api/"
    rst_dict = {}
    cache = open_cache()
    #check cache
    cache_key = construct_unique_key(category, params)
    if(cache_key in cache):
        print(f"Using cache {cache_key}")
        return cache[cache_key]
    #if not in cache
    print(f"Fetching {cache_key}")
    #add api_key to params
    params["api_key"] = secrets.API_KEY
    #request
    response = requests.get(url=base_url+category+"/", params=params)
    rst_dict = json.loads(response.text)
    #save to cache
    cache[cache_key] = rst_dict
    save_cache(cache)

    return rst_dict

def construct_database():
    '''Create .Dota2_api sqlite file
    and construct tables
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    drop_Players='''
        DROP TABLE IF EXISTS "ProPlayers";
    '''
    create_Players='''
        CREATE TABLE IF NOT EXISTS "ProPlayers"(
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "account_id"    INTEGER NOT NULL,
            "steamid"       STRING NOT NULL,
            "profileurl"    STRING NOT NULL,
            "personaname"   STRING NOT NULL,
            "name"          STRING NOT NULL,
            "country_code"  STRING NOT NULL,
            "fantasy_role"  INTEGER NOT NULL,
            "team_id"       INTEGER NOT NULL,
            "team_name"     STRING NOT NULL,
            "team_tag"      STRING NOT NULL,
            "is_pro"        INTEGER
        );
    '''
    cur.execute(drop_Players)
    cur.execute(create_Players)

    drop_Matches='''
        DROP TABLE IF EXISTS "Mathes";
    '''
    create_Matches='''
        CREATE TABLE IF NOT EXISTS "Mathes"(
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "match_id"      INTEGER NOT NULL,
            "duration"      INTEGER NOT NULL,
            "game_mode"     INTEGER NOT NULL,
            "human_players" INTEGER NOT NULL,
            "radiant_win"   INTEGER NOT NULL,
            "player0_account_id"  INTEGER NOT NULL,
            "player0_hero_id"   INTEGER NOT NULL,
            "player0_kill"      INTEGER NOT NULL,
            "player0_death"     INTEGER NOT NULL,
            "player0_assist"    INTEGER NOT NULL,
            "player0_rank_tier" INTEGER NOT NULL,
            
            "player1_account_id"  INTEGER NOT NULL,
            "player1_hero_id"   INTEGER NOT NULL,
            "player1_kill"      INTEGER NOT NULL,
            "player1_death"     INTEGER NOT NULL,
            "player1_assist"    INTEGER NOT NULL,
            "player1_rank_tier" INTEGER NOT NULL,
            
            "player2_account_id"  INTEGER NOT NULL,
            "player2_hero_id"   INTEGER NOT NULL,
            "player2_kill"      INTEGER NOT NULL,
            "player2_death"     INTEGER NOT NULL,
            "player2_assist"    INTEGER NOT NULL,
            "player2_rank_tier" INTEGER NOT NULL,

            "player3_account_id"  INTEGER NOT NULL,
            "player3_hero_id"   INTEGER NOT NULL,
            "player3_kill"      INTEGER NOT NULL,
            "player3_death"     INTEGER NOT NULL,
            "player3_assist"    INTEGER NOT NULL,
            "player3_rank_tier" INTEGER NOT NULL,

            "player4_account_id"  INTEGER NOT NULL,
            "player4_hero_id"   INTEGER NOT NULL,
            "player4_kill"      INTEGER NOT NULL,
            "player4_death"     INTEGER NOT NULL,
            "player4_assist"    INTEGER NOT NULL,
            "player4_rank_tier" INTEGER NOT NULL,
            
            "player5_account_id"  INTEGER NOT NULL,
            "player5_hero_id"   INTEGER NOT NULL,
            "player5_kill"      INTEGER NOT NULL,
            "player5_death"     INTEGER NOT NULL,
            "player5_assist"    INTEGER NOT NULL,
            "player5_rank_tier" INTEGER NOT NULL,
            
            "player6_account_id"  INTEGER NOT NULL,
            "player6_hero_id"   INTEGER NOT NULL,
            "player6_kill"      INTEGER NOT NULL,
            "player6_death"     INTEGER NOT NULL,
            "player6_assist"    INTEGER NOT NULL,
            "player6_rank_tier" INTEGER NOT NULL,
            
            "player7_account_id"  INTEGER NOT NULL,
            "player7_hero_id"   INTEGER NOT NULL,
            "player7_kill"      INTEGER NOT NULL,
            "player7_death"     INTEGER NOT NULL,
            "player7_assist"    INTEGER NOT NULL,
            "player7_rank_tier" INTEGER NOT NULL,

            "player8_account_id"  INTEGER NOT NULL,
            "player8_hero_id"   INTEGER NOT NULL,
            "player8_kill"      INTEGER NOT NULL,
            "player8_death"     INTEGER NOT NULL,
            "player8_assist"    INTEGER NOT NULL,
            "player8_rank_tier" INTEGER NOT NULL,

            "player9_account_id"  INTEGER NOT NULL,
            "player9_hero_id"   INTEGER NOT NULL,
            "player9_kill"      INTEGER NOT NULL,
            "player9_death"     INTEGER NOT NULL,
            "player9_assist"    INTEGER NOT NULL,
            "player9_rank_tier" INTEGER NOT NULL
            
        );
    '''
    cur.execute(drop_Matches)
    cur.execute(create_Matches)
    conn.commit()

def add_DB_Players(player_dict):
    '''insert player entry to Players table
    
    Parameters
    ----------
    params: player_dict
        a dictionary of player informations
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    insert_Players = '''
        INSERT INTO ProPlayers
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    if len(player_dict) == 0:
        #empty input dictinory, return
        return
        
    is_pro = "0"
    if player_dict["is_pro"]:
        is_pro = "1"
    
    player = [str(player_dict["account_id"]),player_dict["steamid"],player_dict["profileurl"],player_dict["personaname"],player_dict["name"],player_dict["country_code"],str(player_dict["fantasy_role"]),str(player_dict["team_id"]),player_dict["team_name"],player_dict["team_tag"],is_pro]

    cur.execute(insert_Players, player)
    conn.commit()

if __name__ == "__main__":
    #example of ProPlayer seaching, params is empty for this example
    category = "ProPlayers"
    params = {}
    rst_dict = get_data(category, params)
    print(rst_dict[0])

    construct_database()
    # for i in range(len(rst_dict)):
    #     add_DB_Players(rst_dict[i])

    player_Miracle = rst_dict[656]

    #example of get match data
    category = "matches/5729327011"
    rst_dict = get_data(category, params)
    print(rst_dict["players"][0])