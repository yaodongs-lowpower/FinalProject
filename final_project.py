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
    result_list: list
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
    N/A
    
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
    N/A
    
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
        hero_id = hero_dict[name]["id"]
        #get matchup data
        category = f"heroes/{hero_id}/matchups"
        raw_data = get_data(category, {})
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
    # #example of ProPlayer seaching, params is empty for this example
    # category = "ProPlayers"
    # params = {}
    # rst_dict = get_data(category, params)
    # print(rst_dict[0])

    # construct_DB_ProPlayers()
    # construct_DB_Matches()
    # # for i in range(len(rst_dict)):
    # #     add_DB_Players(rst_dict[i])

    # player_Miracle = rst_dict[656]

    # #example of get match data
    # category = "matches/5729327011"
    # rst_dict = get_data(category, params)
    # print(rst_dict["players"][0])

    ######starts here######
    # #get proplayer information
    #get_n_store_ProPlayers()
    #get_n_store_ActiveProPlayers()

    # #get recent matches info of a player
    #account_id = 105248644
    #get_n_store_recent_matches(account_id)

    # #search a player's account_id
    #result = user_search("A Neutral Creep")
    #print(result)
    
    # #get all heroes info
    get_n_store_Heroes()