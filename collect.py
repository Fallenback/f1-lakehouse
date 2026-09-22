# %%

import fastf1
import requests
import pandas as pd
import time 
import argparse
requests.packages.urllib3.disable_warnings()
pd.set_option('display.max_columns', None)   

# %%

class CollectResults:
    def __init__(self, years=[2021, 2022, 2023], modes=['R','S']):
        self.years = years
        self.modes = modes

    def get_data(self, year, gp, mode) -> pd.DataFrame:
        try:
            session = fastf1.get_session(year, gp, mode)
        except ValueError as err:
            print(f"corrida {gp} do ano {year} no modo {mode} não encontrada, pulando...")
            return pd.DataFrame()
         
        session._load_drivers_results()
        df = session.results
        df["Year"] = session.date.year
        df["Date"] = session.date
        df["Mode"] = session.name 
        df["RoundNumber"] = session.event["RoundNumber"]
        df["OfficialEventName"] = session.event["OfficialEventName"]
        df["Country"] = session.event["Country"]
        df["Location"] = session.event["Location"]
        return df

    def save_data(self, df:pd.DataFrame, year:int, gp:int, mode:str):
        filename = f"data/{year}_{gp:02}_{mode}.parquet"
        df.to_parquet(filename, index=False)
    
    def process(self, year, gp, mode):
        df = self.get_data(year, gp, mode)
        if df.empty:
            return False 
        self.save_data(df, year, gp, mode)
        time.sleep(2)
        return True
    
    def process_year_modes(self, year):
        for i in range(1,50):
            for mode in self.modes:
                if not self.process(year, i, mode) and mode == 'R':
                    return
                
    def process_years(self):
        for year in self.years:
            print(f"processando ano {year}...")
            self.process_year_modes(year)
            time.sleep(15)
       
        
# %%


parser = argparse.ArgumentParser()
parser.add_argument('--years', "-y",nargs='+', type=int)
parser.add_argument('--modes', "-m", nargs='+')
parser.add_argument('--start', "-s", type=int)
parser.add_argument('--stop', "-t", type=int)
args = parser.parse_args()

if args.years:
    collect = CollectResults(args.years, args.modes)

elif args.start and args.stop:
    years = [i for i in range (args.start, args.stop+1)]
    collect = CollectResults(years, args.modes)

collect.process_years()

# %%
