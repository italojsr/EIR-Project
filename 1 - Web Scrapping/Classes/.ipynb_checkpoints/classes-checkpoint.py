
import pandas as pd
import numpy as np

#Create list with the name of all world cups
a_file = open(r"C:\Users\italo\OneDrive\Documentos\GitHub\TCC\name_of_all_worldcups.txt","r",newline = '')
raw_worldcups = a_file.read()
worldcups = raw_worldcups.splitlines(False)
a_file.close()

#Create a list with the name of all teams that have participated in the world cups until now
b_file = open(r"C:\Users\italo\OneDrive\Documentos\GitHub\TCC\name_of_all_teams.txt","r",newline = '')
raw_teams = b_file.read()
name_of_all_teams = raw_teams.splitlines(False)
b_file.close()

class Worldcup:
    def __init__(self,file_path):
        #df = pd.read_csv(file_path,header = [0,1],index_col = 0)
        #df.index = range(0,df.shape[0])
        #self.__world_cup_df = df
        self.__world_cup_df = pd.read_csv(file_path,header = [0,1],index_col = 0)
    def get_teams(self):
        #Returns a list with all teams from the world cup
        teams = list(self.with_multicolumns().T.index.levels[0])
        return teams
       
    def as_database(self):
        pass
    def with_multicolumns(self):
        return self.__world_cup_df
    
    def save_csv(self,worldcup_name):
        self.__world_cup_df.to_csv(worldcup_name)
    
class WorldcupPlayers(Worldcup):
    def __init__(self,worldcup_name):
        
        file_path = "C:/Users/italo/OneDrive/Documentos/GitHub/TCC/WorldCup DataFrames/worldcupfootball+wikipedia/{}.csv".format(worldcup_name)
        super().__init__(file_path) #Initialize the attributes of the parent class

    def get_players_from_team(self,team_name):
        # Returns an object Players which contains a dataframe with information of the player from the especified team.
        players_from_team = Team_Players(self.with_multicolumns()[team_name],team_name)
        return players_from_team        
    def count_players_by_trimester(self):
        # Returns a numpy array with the total number of players from the world cup borned at each trimester of the year.
        worldcup_teams = self.get_teams()
        worldcup_trimesters = np.zeros(5)
        for team in worldcup_teams:
            players = self.get_players_from_team(team)
            worldcup_trimesters += np.array(players.count_players_by_trimester())
        return worldcup_trimesters

class WorldcupTrimesters(Worldcup):
    def __init__(self,worldcup_name):
        file_path = "C:/Users/italo/OneDrive/Documentos/GitHub/TCC/Quarters/World cups Quarters/Quarters (MultiColumns)/{} quarters (MultiColumns).csv".format(worldcup_name)
        super().__init__(file_path)
    def get_trimesters_from_team(self,team_name):
        # Returns an object Trimesters which contains a dataframe for the especified team
        trimesters_from_team = Team_Trimesters(self.with_multicolumns()[team_name],team_name)
        return trimesters_from_team
    def count_players_by_trimester(self):
        # Returns a numpy array with the total number of players from the world cup borned at each trimester of the year.
        worldcup_teams = self.get_teams()
        worldcup_trimesters = np.zeros(5)
        for team in worldcup_teams:
            worldcup_trimesters += self.with_multicolumns()[team]['Frequence'].values
        return worldcup_trimesters



class Team:
    def __init__(self,team_name):
        self.__team_name = team_name
    def get_team_name(self):
        return self.__team_name
    def get_participated_worldcups(self):
        options = []
        for worldcup in worldcups:
            teams = WorldcupTrimesters(worldcup).get_teams()
            if self.get_team_name() in teams:
                options.append(worldcup)
        return options



        
class Team_Players(Team):
    def __init__(self,players_df,team_name):
        self.__players_df = players_df 
        super().__init__(team_name)
    def df(self):
        return self.__players_df
    def get_players_name(self):
        return self.__players_df['Name']
    def get_players_position(self):
        return self.__players_df['Position']
    def get_players_day(self):
        return self.__players_df['Day']
    def get_players_month(self):
        filtering = self.__players_df['Month']>0
        return self.__players_df[filtering]['Month']
    def get_players_year(self):
        return self.__players_df['Year']
    
    
    def count_players_borned_between_months(self,initial_month,end_month):
        players_month = self.get_players_month()
        period = (initial_month<players_month) & (players_month<=end_month)
        return players_month[period].value_counts().sum() #Return the number of players borned between the selected quartiles
    
    def count_players(self):
        n = self.count_players_borned_between_months(0,12)
        return n
    
    
    def count_players_by_trimester(self):
        count_by_tri = []
        for i in range(0,12,3):
            count_by_tri.append(self.count_players_borned_between_months(i,i+3))
        count_by_tri.insert(0,sum(count_by_tri))
        count_by_tri = np.array(count_by_tri)
        return count_by_tri
    def percent_players_by_trimester(self):
        count_by_tri = self.count_players_by_trimester()
        total = count_by_tri[0]
        percentage = np.around((count_by_tri/total)*100,1)
        return percentage


class Team_Trimesters(Team):
    def __init__(self,trimesters_df,team_name):
        self.__trimester_df = trimesters_df
        super().__init__(team_name)
    def df(self):
        return self.__trimester_df
    def unify_1st_2nd_tri(self):
        df = self.df()
        unified_df =df.iloc[2:,:].copy()
        unified_df.iloc[0] =df.iloc[1] + df.iloc[2]
        unified_df.index = ['Primeiro e Segundo Quartil','Terceiro Quartil','Quarto Quartil']
        return unified_df





    



