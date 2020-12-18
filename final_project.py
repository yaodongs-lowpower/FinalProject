###local sys path###
import sys
sys.path.append('/usr/local/lib/python3.8/site-packages/')
####################

from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import requests
import json
import secrets # file that contains your API key
import time
import sqlite3

matplotlib.use('Agg')

#name of the cache
CACHE_FILENAME = "cache.json"
#use flask
app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hero_search')
def hero_search():
    return render_template('hero_search.html')

@app.route('/handle_hero_search', methods=['POST'])
def handle_hero_search():
    '''
    Handel hero name input for hero info display
    '''
    usr_input = request.form["usr_input"]
    hero_result = search_hero(usr_input)
    #if input not found in DB
    if len(hero_result)==0:
        return render_template('not_found.html', usr_input=usr_input)
    #if found, display it
    (name, img, bio) = hero_search_parser(hero_result)
    return render_template('hero_page.html', name=name, img=img, bio=bio)

@app.route('/player_search')
def player_search():
    return render_template('player_search.html')

@app.route('/handle_player_search', methods=['POST'])
def handle_player_search():
    usr_input = request.form["usr_input"]
    #get player id
    result = user_search(usr_input)
    if result == []:
        return render_template('not_found.html', usr_input=usr_input)
    player_result = result[0]
    name = player_result["name"]
    id_ = player_result["account_id"]
    #get recent matches
    get_n_store_recent_matches(id_)
    #format match info helper
    (win_list, match_list, duration_list, hero_list, start_list, k_list, d_list, a_list) = format_match_info_helper(id_)
    draw_kda_win(win_list, k_list, d_list, a_list)
    #display it
    return render_template('match_page.html', name=name, win_list=win_list,match_list=match_list, duration_list=duration_list, hero_list=hero_list, start_list=start_list, k_list=k_list, d_list=d_list, a_list=a_list)

@app.route('/teams')
def teams():
    teams_dict = get_teams()
    return render_template('teams.html', teams_dict = teams_dict)

@app.route('/handle_teams', methods=['POST'])
def handle_teams():
    team = request.form.get("team")
    members = get_players_by_team(team)
    return render_template('team_page.html', members = members, team=team)

@app.route('/handle_player_search_id', methods=['POST'])
def handle_player_search_id():
    #get id of player
    id_ = request.form.get("id_")
    name = request.form.get("name")
    #find matches of that player
    get_n_store_recent_matches(id_)
    #format match info helper
    (win_list, match_list, duration_list, hero_list, start_list, k_list, d_list, a_list) = format_match_info_helper(id_)
    draw_kda_win(win_list, k_list, d_list, a_list)
    #display it
    return render_template('match_page.html', name=name, win_list=win_list,match_list=match_list, duration_list=duration_list, hero_list=hero_list, start_list=start_list, k_list=k_list, d_list=d_list, a_list=a_list)

def get_teams():
    ''' get pro team names of each region from DB

    Parameters
    ----------
    N/A

    Returns
    -------
    dict:
        team name list under region keys
    '''
    query = f'''
                SELECT  DISTINCT team_name, region
                FROM    ActiveProPlayers 
            '''
    results = DB_query(query)
    team_dict = {}
    #make it dict by regions
    for (team, region) in results:
        #if empty init as list
        if region not in team_dict.keys():
            team_dict[region] = []
        else:
            team_dict[region].append(team)

    return team_dict

def get_players_by_team(team):
    ''' get all pro player in the team

    Parameters
    ----------
    team: string
        pro team name

    Returns
    -------
    tuple:
        list of player names and ids,  in the specified team
    '''
    query = f'''
                SELECT  ActiveProPlayers.player_name    AS name, 
                        ProPlayers.account_id           AS id_
                FROM    ActiveProPlayers
                        INNER JOIN ProPlayers 
                        ON ActiveProPlayers.ProPlayers_table_id = ProPlayers.id
                WHERE   ActiveProPlayers.team_name = '{team}'
            '''
    results = DB_query(query)
    return results

def format_match_info_helper(id_):
    ''' use user id_ input to find match info in DB
    select the needed info for display

    Parameters
    ----------
    id_: int
        player account id

    Returns
    -------
    tuple:
        tuple of match infomation lists
    '''
    query = f'''
                SELECT * 
                FROM 'PlayerMatches'
                WHERE account_id = '{id_}'
    '''
    entries = DB_query(query)
    win_list = []
    match_list = []
    duration_list = []
    hero_list = []
    start_list = []
    k_list = []
    d_list = []
    a_list = []
    for (id, acnt, match, win, duration, hero_id, s_t, k, d, a) in entries:
        hero = find_hero_name([hero_id])[0]
        #translate 0-1 to won and lost
        if win == 1:
            win_t = "Won"
        else:
            win_t = "Lost"
        win_list.append(win_t)
        match_list.append(match)
        duration_list.append(duration)
        hero_list.append(hero)
        start_list.append(s_t)
        k_list.append(k)
        d_list.append(d)
        a_list.append(a)
    return (win_list, match_list, duration_list, hero_list, start_list, k_list, d_list, a_list)
        
def draw_kda_win(win_list, k_list, d_list, a_list):
    '''draw and store kda plot

    Parameters
    ----------
    win_list: list
        won/lost string for recent matches
    k_list: list
        number of kills for recent matches
    d_list: list
        number of deaths for recent matches
    a_list: list
        number of assists for recent matches

    Returns
    -------
    N/A
    '''
    output_file = "static/kda.png"
    plt.figure(figsize=(10,2))
    plt.plot(k_list, 'r', marker='o', label='kill')
    plt.plot(d_list, 'b', marker='x', label='death')
    plt.plot(a_list, 'g', marker='d', label='assist')
    lgd = plt.legend(bbox_to_anchor=(1.02, 1.), loc='upper left', borderaxespad=0.)

    ax = plt.gca()
    ticks = np.arange(0, len(k_list), 1)
    ax.set_xticks(ticks)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.grid(True)
    #ax.grid(True)
    ax.set_xticklabels([])
    plt.savefig(output_file, bbox_extra_artists=(lgd,), bbox_inches='tight')
    return

def search_hero(usr_input):
    ''' search hero infomation in database basing on user input
        if entry doesnt exist, return empty dictionary

    Parameters
    ----------
    usr_input: string
        the input hero name that user want to search

    Returns
    -------
    tuple:
        contains hero name, img link, bio, and matchup info
    '''
    query = f'''
                SELECT * 
                FROM 'Heroes'
                WHERE LOWER(name) = '{usr_input.lower()}'
            '''
    try:
        rst = DB_query(query)
    except:
        return ()
    else:
        if len(rst) == 0:
            return ()

        return rst[0]

def hero_search_parser(hero_result):
    ''' function to parse the return entry from Heroes DB
    find the hero name basing on the hero id
    call function to draw matchup plot

    Parameters
    ----------
    hero_result: tuple
        contains hero name, img link, bio, and matchup info

    Returns
    -------
    tuple:
        contains hero name, img link, bio
    '''
    name_list = find_hero_name([hero_result[4],hero_result[6],hero_result[8],hero_result[10],hero_result[12],hero_result[14]])
    draw_matchup(name_list,[hero_result[5],hero_result[7],hero_result[9],hero_result[11],hero_result[13],hero_result[15]])
    return (hero_result[1], hero_result[2], hero_result[3])

def draw_matchup(name_list, in_rate_list):
    ''' draw bar diagram of hero matchups, store it in static/matchup.png

    Parameters
    ----------
    name_list: list
        matchup hero names
    in_rate_list: list
        matchup hero win ratios

    Returns
    -------
    N/A
    '''
    rate_list = []
    for rate in in_rate_list:
        #if data is NULL
        if rate == "NULL":
            rate_list.append(0)
            continue
        rate = rate * 100
        rate = round(rate)
        rate_list.append(rate)

    output_file = 'static/matchup.png'
    fig, ax1 = plt.subplots(figsize=(9, 8))  # Create the figure
    pos = np.arange(len(name_list))
    rects = ax1.barh(pos, rate_list,
                     align='center',
                     height=0.5,
                     tick_label=name_list)
    ax1.set_title('3 Worst Against Heroes and 3 Best Against Heroes')
    ax1.set_xlim([0, 100])
    ax1.xaxis.grid(True, linestyle='--', which='major',
                   color='grey', alpha=.25)

    # Plot a solid vertical gridline to highlight the median position
    ax1.axvline(50, color='grey', alpha=0.25)
    ax1.set_xlabel('Win rate percentage')
    #print percentage in bars
    for i in range(len(rects)):
        rect = rects[i]
        xloc = -5
        yloc = rect.get_y() + rect.get_height() / 2
        width = int(rect.get_width())
        label = ax1.annotate(
                str(rate_list[i]), xy=(width, yloc), xytext=(xloc, 0),
                textcoords="offset points",
                horizontalalignment='right', verticalalignment='center',
                weight='bold', clip_on=True)
    plt.savefig(output_file)

def find_hero_name(id_list):
    ''' search DB to translate hero_id to hero name

    Parameters
    ----------
    id_list: list
        a list of hero ids

    Returns
    -------
    list:
        list of hero names
    '''
    name_list = []
    for id_ in id_list:
        if id_ == "NULL":
            name_list.append("NULL")
            continue
        query = f'''
            SELECT name 
            FROM 'Heroes'
            WHERE Id = '{id_}'
        '''
        name = DB_query(query)
        if name == []:
            name_list.append("NULL")
            continue
        name = name[0][0]
        name_list.append(name)
    return name_list

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
    '''Obtain API data from OpenDota API.
    
    Parameters
    ----------
    category: string
        A piece of url after the base url for the search category
    params: dict
        a dictionary of parameters without API_KEY
    arg: string
        put between url and params followed by a question mark
    
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
    response = requests.get(url=base_url+category, params=params)
    rst_dict = json.loads(response.text)
    #save to cache
    cache[cache_key] = rst_dict
    save_cache(cache)

    return rst_dict

def construct_DB_ProPlayers():
    '''Create .Dota2_api sqlite file
    and construct ProPlayers table
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    drop_ProPlayers='''
        DROP TABLE IF EXISTS "ProPlayers";
    '''
    create_ProPlayers='''
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
            "team_name"     STRING,
            "team_tag"      STRING,
            "is_pro"        INTEGER
        );
    '''
    cur.execute(drop_ProPlayers)
    cur.execute(create_ProPlayers)

def construct_DB_ActiveProPlayers():
    '''Create .Dota2_api sqlite file
    and construct ActiveProPlayers table
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    drop_ActiveProPlayers='''
        DROP TABLE IF EXISTS "ActiveProPlayers";
    '''
    #the ProPlayers_table_id links to player detail in ProPlayers table
    create_ActiveProPlayers='''
        CREATE TABLE IF NOT EXISTS "ActiveProPlayers"(
            "Id"                INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "player_name"       STRING,
            "team_name"         STRING,
            "region"            STRING,
            "ProPlayers_table_id" INTEGER NOT NULL
        );
    '''
    cur.execute(drop_ActiveProPlayers)
    cur.execute(create_ActiveProPlayers)

def construct_DB_PlayerMatches():
    '''Create .Dota2_api sqlite file
    and construct PlayerMatches table
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    drop_PlayerMatches='''
        DROP TABLE IF EXISTS "PlayerMatches";
    '''
    create_PlayerMatches='''
        CREATE TABLE IF NOT EXISTS "PlayerMatches"(
            "Id"            INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
            "account_id"    INTEGER NOT NULL,
            "match_id"      INTEGER,
            "win"           INTEGER,
            "duration"      STRING,
            "hero_id"       INTEGER NOT NULL,
            "start_time"    STRING,
            "kills"         INTEGER NOT NULL,
            "deaths"        INTEGER NOT NULL,
            "assists"       INTEGER NOT NULL
        );
    '''
    cur.execute(drop_PlayerMatches)
    cur.execute(create_PlayerMatches)
    conn.commit()

def construct_DB_Heroes():
    '''Create .Dota2_api sqlite file
    and construct Heroes table
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    drop_Heroes='''
        DROP TABLE IF EXISTS "Heroes";
    '''
    create_Heroes='''
        CREATE TABLE IF NOT EXISTS "Heroes"(
            "Id"            INTEGER PRIMARY KEY UNIQUE,
            "name"          STRING NOT NULL,
            "img_link"      STRING,
            "bio"           STRING,
            "best_against_1"            INTEGER,
            "best_against_win_rate_1"   FLOAT,
            "best_against_2"            INTEGER,
            "best_against_win_rate_2"   FLOAT,
            "best_against_3"            INTEGER,
            "best_against_win_rate_3"   FLOAT,
            "worst_against_1"           INTEGER,
            "worst_against_win_rate_1"  FLOAT,
            "worst_against_2"           INTEGER,
            "worst_against_win_rate_2"  FLOAT,
            "worst_against_3"           INTEGER,
            "worst_against_win_rate_3"  FLOAT
        );
    '''
    cur.execute(drop_Heroes)
    cur.execute(create_Heroes)
    conn.commit()

def add_DB_ProPlayers(player_dict):
    '''insert Pro Player entry to ProPlayers table
    
    Parameters
    ----------
    params: player_dict
        a dictionary of Pro player informations
    
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

def add_DB_ActiveProPlayers(player_list):
    '''insert team entries to ActiveProPlayers table
    
    Parameters
    ----------
    params: player_list
        A list contains ActiveProPlayers table entries
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    insert_players = '''
        INSERT INTO ActiveProPlayers
        VALUES (NULL, ?, ?, ?, ?)
    '''
    if len(player_list) == 0:
        #empty input dictinory, return
        return
    
    for player in player_list:
        cur.execute(insert_players, player)

    conn.commit()

def add_DB_PlayerMatches(match_list):
    '''insert team entries to ActiveProPlayers table
    
    Parameters
    ----------
    params: player_list
        A list contains ActiveProPlayers table entries
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    insert_matches = '''
        INSERT INTO PlayerMatches
        VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    if len(match_list) == 0:
        #empty input dictinory, return
        return
    
    for match in match_list:
        cur.execute(insert_matches, match)

    conn.commit()

def add_DB_Heroes(hero_list):
    '''insert team entries to Heroes table
    
    Parameters
    ----------
    params: hero_list
        A list contains Heroes table entries
    
    Returns
    -------
    N/A
    '''
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    insert_heroes = '''
        INSERT INTO Heroes
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    if len(hero_list) == 0:
        #empty input dictinory, return
        return
    for hero in hero_list:
        cur.execute(insert_heroes, hero)

    conn.commit()

def ActiveProPlayers_helper(team_dict):
    ''' accept team_dict as input, 
        search ProPlayer table for players of that team,
        construct a new list for feeding the ActiveProPlayers table
    
    Parameters
    ----------
    params: team_dict
        A dict of team lists under region keys
    
    Returns
    -------
    list
        A list of (Proplayer_name, team_name, region, table_id) tuples
    '''
    #dict for alternate name of a team
    alias_dict = {"omega gaming":"Ωmega gaming"}
    conn = sqlite3.connect('Dota2_api.sqlite')
    cur = conn.cursor()
    ActiveProPlayers_list = []
    region_list = list(team_dict.keys())
    #get region and team_name
    for region in region_list:
        for team_name in team_dict[region]:
            #search entries match the team name in ProPlayers table
            query = f'''  SELECT  name, Id
                        FROM    ProPlayers
                        WHERE   (LOWER(team_name) = '{team_name.lower()}')
                    '''
            result = cur.execute(query).fetchall()
            #if cannot find, try again without "Team "
            if (result == []):
                team_name = team_name.split("Team ")[-1]
                query = f'''  SELECT  name, Id
                        FROM    ProPlayers
                        WHERE   (LOWER(team_name) = '{team_name.lower()}')
                        '''
                result = cur.execute(query).fetchall()
            #if still cannot find, check alternate names
            if (result == [] and team_name.lower() in alias_dict.keys()):
                query = f'''  SELECT  name, Id
                        FROM    ProPlayers
                        WHERE   (LOWER(team_name) = '{alias_dict[team_name.lower()]}')
                        '''
                result = cur.execute(query).fetchall()
            #insert into list
            for (name, table_id) in result:
                ActiveProPlayers_list.append((name, team_name, region, table_id))
    return ActiveProPlayers_list

def get_n_store_ProPlayers():
    '''Construct ProPlayers table, API get ProPlayers data, Store in table
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    N/A
    '''
    construct_DB_ProPlayers()
    #get all pro players data
    category = "ProPlayers"
    params = {}
    rst_dict = get_data(category, params)
    for entry in rst_dict:
        add_DB_ProPlayers(entry)

def DB_query(query):
    '''A helper function to get data from Dota2_api.sqlite
    
    Parameters
    ----------
    query: String
        A command string pass to database from data query
    
    Returns
    -------
    list
        a list of tuples that represent the query result
    '''
    connection = sqlite3.connect("Dota2_api.sqlite")
    cursor = connection.cursor()
    result = cursor.execute(query).fetchall()
    connection.close()
    return result
    
def get_active_teams():
    '''Obtain web page with cache.
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    dict
        Active team name list under region keys
    '''
    url = "https://liquipedia.net/dota2/Portal:Teams"
    active_teams = {}
    cache = open_cache()
    #check cache
    cache_key = construct_unique_key("active_teams", {})
    if(cache_key in cache):
        print(f"Using cache {cache_key}")
        return cache[cache_key]
    #if not in cache
    print(f"Fetching {cache_key}")
    #request
    response = requests.get(url)
    #parse it with bs
    soup = BeautifulSoup(response.content, "html.parser")
    #get to the lists of teams
    all_teams = soup.find("div", class_="lp-container-fluid")
    region_boxes = all_teams.find_all("div", class_="panel-box")
    for region in region_boxes:
        #get region name, which is the key of return dictionary
        region_name_div = region.find("div", class_="panel-box-heading")
        region_name_a = region_name_div.find("a")
        region_name = str(region_name_a.text)
        #get team names in that region
        region_team = []
        region_team_div = region.find("div", class_="panel-box-body")
        region_team_spans = region_team_div.find_all("span", class_="team-template-team-standard")
        for span in region_team_spans:
            region_team_name = str(span.get("data-highlightingclass"))
            #remove content in ()
            region_team_name = region_team_name.split(' (')[0]
            region_team.append(region_team_name)
        #insert to dictionary
        active_teams[region_name] = region_team
        
    #save to cache
    cache[cache_key] = active_teams
    save_cache(cache)

    return active_teams

def get_n_store_ActiveProPlayers():
    '''get active teams from HTML and store to DB
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    N/A
    '''
    construct_DB_ActiveProPlayers()
    team_dict = get_active_teams()
    ActiveProPlayers_list = ActiveProPlayers_helper(team_dict)
    add_DB_ActiveProPlayers(ActiveProPlayers_list)

def get_n_store_recent_matches(account_id):
    '''Obtain recent 10 matches of a player from OpenDota API.
        process them and store in the thde PlayerMatches table.
    
    Parameters
    ----------
    account_id: int
        the account id of a dota player
    
    Returns
    -------
    N/A
    '''
    #get data from api
    category = f"players/{account_id}/matches"
    params = {"limit":10}
    result_list = get_data(category, params)
    #parse it
    PlayerMatches_list = PlayerMatches_helper(result_list, account_id)
    #construct DB
    construct_DB_PlayerMatches()
    #store into DB
    add_DB_PlayerMatches(PlayerMatches_list)

def PlayerMatches_helper(raw_list, account_id):
    '''convert raw match information to entries of PlayerMatches table
    
    Parameters
    ----------
    account_id: int
        the account id of a player
    raw_list: list
        a list of player recent matches from API
    
    Returns
    -------
    list:
        a list of tuples to feed PlayerMatches table
    '''
    return_list = []

    for item in raw_list:
        #skip tuple
        if (type(item) == tuple):
            continue

        match_id = item["match_id"]
        if (item["radiant_win"] == True):
            radiant_win = 1
        else:
            radiant_win = 0
        #player_slot 0 is radiant, 128 is not
        if (item["player_slot"] == 0):
            win = radiant_win
        else:
            if (radiant_win == 1):
                win = 0
            else:
                win = 1
        #convert duration in mins
        duration = str(round(item["duration"]/60)) + " mins"
        hero_id = item["hero_id"]
        #covert starttime
        start_time = epoch_conv(item["start_time"])
        kills = item["kills"]
        deaths = item["deaths"]
        assists = item["assists"]
        #insert into return list
        return_list.append((account_id, match_id, win, duration, hero_id, start_time, kills, deaths, assists))

    return  return_list

def epoch_conv(stamp):
    '''Convert epoch time stamp to human-readable time in GMT
    
    Parameters
    ----------
    stamp: int
        the epoch time stamp
    
    Returns
    -------
    string
        a converted time in GMT
    '''
    s = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stamp))
    return s + " GMT"
    
def user_search(player_name):
    '''search dota2 player name, return up to 10 name matches with account_id
    
    Parameters
    ----------
    player_name: string
        a string of palyer name
    
    Returns
    -------
    dict:
        dict of similar player names with their account_id and last match time
    '''
    category = "search"
    params = {'q':player_name}
    result_list = get_data(category,params)
    #parse it and, limit it to 10 entries
    limit = 10
    ct = 0
    return_list = []
    for item in result_list:
        temp_dict = {}
        temp_dict["account_id"] = item["account_id"]
        temp_dict["name"] = item["personaname"]
        #skip the player that has no last match record
        if "last_match_time" not in item.keys():
            continue
        temp_dict["last_match_time"] = item["last_match_time"]
        #insert to return list
        return_list.append(temp_dict)
        #limit to 10 entries
        ct += 1
        if ct == limit:
            break

    return return_list
    
def get_hero_links():
    '''get heros links from dota2 hero main HTML page
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    list
        a list of hero links
    '''
    #get hero info from HTML
    base_url = "https://www.dota2.com/heroes/"
    cache = open_cache()
    #check cache
    cache_key = construct_unique_key("heroes", {})
    if(cache_key in cache):
        print(f"Using cache {cache_key}")
        return cache[cache_key]
    #if not in cache
    print(f"Fetching {cache_key}")
    #request
    response = requests.get(base_url)
    #parse it with bs
    soup = BeautifulSoup(response.content, "html.parser")
    #get hero links
    soup = soup.find("div", id="heroPickerInner")
    soup = soup.find_all("a", class_="heroPickerIconLink")
    hero_links = []
    for a in soup:
        hero_links.append(str(a.get("href")))
    #store to cache
    cache[cache_key] = hero_links
    save_cache(cache)

    return hero_links

def get_hero_detail(hero_links):
    '''get heros detail from dota2 hero HTML page
    
    Parameters
    ----------
    list:
        a list of url string to hero detail page
    
    Returns
    -------
    list:
        a list of dictionaries, contains hero name, bio and link to img
    '''
    return_list = []
    for base_url in hero_links:
        cache = open_cache()
        #check cache
        cache_key = construct_unique_key("Hero-"+base_url, {})
        #if in cache, append into return list and check next one
        if(cache_key in cache):
            print(f"Using cache {cache_key}")
            return_list.append(cache[cache_key])
            continue
        #if not in cache
        print(f"Fetching {cache_key}")
        #request
        response = requests.get(base_url)
        #parse it with bs
        soup = BeautifulSoup(response.content, "html.parser")
        #get hero name
        soup = soup.find("div", id="centerColContent")
        name = soup.find("h1").text
        #get hero img, w/h 135/272
        img = soup.find("img", id="heroPrimaryPortraitImg").get("src")
        #get bio of hero
        bio =  soup.find("div", id="bioInner").text.strip()
        #inser to return list
        hero_dict = {}
        hero_dict["name"] = name
        hero_dict["img"] = img
        hero_dict["bio"] = bio
        return_list.append(hero_dict)
        #store into cache
        cache[cache_key] = hero_dict
        save_cache(cache)
    return return_list

def get_hero_info_api():
    '''get hero info from API
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    dict
        a dict of hero info, with hero name as keys
    '''
    category = "constants/heroes"
    params = {}
    hero_dict = get_data(category, params)
    #create a new copy of dict, replace keys with localized_name
    new_dict = {}
    for key in hero_dict.keys():
        hero = hero_dict[key]
        new_dict[hero["localized_name"]] = hero
    #PATCH# add new hero entry
    patch_dict = {}
    patch_dict["id"] = 123
    new_dict["Hoodwink"]=patch_dict
    #end PATCH
    return new_dict

def sort_helper(matchup_dict):
    '''a helper function for sorting matchup list
    
    Parameters
    ----------
    matchup_dict: dict
        a dictionary has hero_id and rate
    
    Returns
    -------
    float:
        the win rate of matchup
    '''
    return matchup_dict["rate"]

def Heroes_helper(hero_list):
    '''get hero id from API and match up data 
        return a Heros table entry tuples list
    
    Parameters
    ----------
    list:
        a list of dictionaries, contains hero name, bio and link to img
    
    Returns
    -------
    list
        a list of tuples to feed Heros table
    '''
    hero_dict = get_hero_info_api()
    #link hero id to hero_list
    entry_list = []
    for hero in hero_list:
        name = hero["name"]
        img = hero["img"]
        bio = hero["bio"]
        #check key
        if name not in hero_dict.keys():
            hero_id = 0
        else:
            hero_id = hero_dict[name]["id"]
        #get matchup data
        category = f"heroes/{hero_id}/matchups"
        raw_data = get_data(category, {})
        #if hero info not found in API, use NULLs 
        if raw_data == []:
            matchup1 = 0
            rate1 = 0
            matchup2 = 0
            rate2 = 0
            matchup3 = 0
            rate3 = 0
            matchup_1 = 0
            rate_1 = 0
            matchup_2 = 0
            rate_2 = 0
            matchup_3 = 0
            rate_3 = 0
            entry_list.append((hero_id, name, img, bio, matchup1, rate1, matchup2, rate2, matchup3, rate3, matchup_1, rate_1, matchup_2, rate_2, matchup_3, rate_3))
            continue
        rate_data = []
        #calculate win rate
        for matchup in raw_data:
            item = {}
            matchup_ct = matchup["games_played"]
            #only count matchup with not less than 10 matches
            if matchup_ct < 10:
                continue
            matchup_id = matchup["hero_id"]
            matchup_win = matchup["wins"]
            matchup_rate = matchup_win/matchup_ct
            item["rate"] = matchup_rate
            item["hero_id"] = matchup_id
            rate_data.append(item)
        #sort the matchup data
        rate_data.sort(reverse = True, key = sort_helper)
        matchup1 = rate_data[0]["hero_id"]
        rate1 = rate_data[0]["rate"]
        matchup2 = rate_data[1]["hero_id"]
        rate2 = rate_data[1]["rate"]
        matchup3 = rate_data[2]["hero_id"]
        rate3 = rate_data[2]["rate"]
        matchup_1 = rate_data[-1]["hero_id"]
        rate_1 = rate_data[-1]["rate"]
        matchup_2 = rate_data[-2]["hero_id"]
        rate_2 = rate_data[-2]["rate"]
        matchup_3 = rate_data[-3]["hero_id"]
        rate_3 = rate_data[-3]["rate"]
        #append to entry list
        entry_list.append((hero_id, name, img, bio, matchup1, rate1, matchup2, rate2, matchup3, rate3, matchup_1, rate_1, matchup_2, rate_2, matchup_3, rate_3))
    return entry_list

def get_n_store_Heroes():
    '''get heros bios from HTML and store to DB
    
    Parameters
    ----------
    N/A
    
    Returns
    -------
    N/A
    '''
    #get urls to each hero
    hero_links = get_hero_links()
    #use the link to get details of heros
    hero_list = get_hero_detail(hero_links)
    #link info with hero id from API and get matchup data
    entry_list = Heroes_helper(hero_list)
    #store into DB
    construct_DB_Heroes()
    add_DB_Heroes(entry_list)

if __name__ == "__main__":
    print('starting Flask app', app.name)
    #get data
    get_n_store_Heroes()
    get_n_store_ProPlayers()
    get_n_store_ActiveProPlayers()
    #run app
    app.run(debug=True)
    
    
