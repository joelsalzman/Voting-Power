# -*- coding: utf-8 -*-
"""
    Calculates margins for elections

Created on 9/24/19

Author: Joel Salzman
"""

# Imports
import pandas as pd
import os

# Set working directory
if "Voting" not in os.getcwd():
    os.chdir(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting")
elif "Python" in os.getcwd():
    os.chdir("..")
# Path getters
tbl = lambda file: os.path.join(os.getcwd(), "Tables", file)
# Useful lists and dataframes
years = [y for y in range(1999, 2020)]
states = pd.read_csv(tbl("states.csv"))
keepFromCSV = ["year", "state", "district",
               "writein", "special", "runoff", "candidate", "party", "candidatevotes", "totalvotes"]
newCols = ["runnerUp", "ruParty", "ruVotes", "rawMargin", "decMargin", "winner", "winVotes", "totalVotes"]


### Calculates the margins and puts data for each election into a new dataframe
def processData():
    print("Trying to process data")
    
    # Gather the relevant data
    prezSimple   = pd.read_csv(tbl('1976-2016-president.csv'), thousands=","
                               ).filter(items = keepFromCSV[:2] + keepFromCSV[6:])
    senateSimple = pd.read_csv(tbl('1976-2018-senate.csv'), thousands="," , encoding='ISO-8859-1'
                               ).filter(items = keepFromCSV[:2] + [keepFromCSV[3]] + keepFromCSV[6:])
    houseSimple  = pd.read_csv(tbl('1976-2018-house.csv'), thousands="," , encoding='ISO-8859-1'
                               ).filter(items = keepFromCSV)
    
        
    ### Calculates the margins in each election
    def process(df, h=0):
        print(f"    Calculating margins...")
        
        # Prepare an empty dataframe to fill
        final = pd.DataFrame(data = [], columns = list(df.columns) + newCols[:-3])
        
        # Loop through each election
        for st in states["State"].tolist():
            districts = [False] if not h else df["district"].unique().tolist()
            for dist in districts:
                for yr in years:
                    elec = df
                    if h:
                        elec = df[((df["year"] == yr) | (df["year"] == yr + 1)) &
                                  (df["state"] == st) & (df["district"] == dist)]
                    else:
                        elec = df[((df["year"] == yr) | (df["year"] == yr + 1)) &
                                  (df["state"] == st)]
                    if elec.empty:
                        continue
                    
                    # Calculate the margins and append them to the new dataframe
                    try:
                        row    = df.iloc[pd.to_numeric(elec["candidatevotes"]).idxmax()]
                        first  = pd.to_numeric(row.at["candidatevotes"])
                        runUp  = df.iloc[pd.to_numeric(
                                elec[elec["candidatevotes"] != first]["candidatevotes"]).idxmax()]
                        second = pd.to_numeric(runUp.at["candidatevotes"])
                        total  = pd.to_numeric(row.at["totalvotes"])
                    except:
                        continue
                    
                    if not runUp.empty:
                        row["runnerUp"]  = runUp.at["candidate"]
                        row["ruParty"]   = runUp.at["party"]
                        row["ruVotes"]   = pd.to_numeric(runUp["candidatevotes"])
                        row["rawMargin"] = first - second
                        row["decMargin"] = (first / total) - (second / total)
                    else:
                        row["runnerUp"]  = None
                        row["ruParty"]   = None
                        row["ruVotes"]   = 0
                        row["rawMargin"] = first
                        row["decMargin"] = 1

                    final = final.append(row, ignore_index = True)
        
        return final
    
    
    # Output the new dataframes
    calculated = {"prez":process(prezSimple), "senate":process(senateSimple), "house":process(houseSimple, 1)}
    for k in calculated.keys():
        calculated[k] = calculated[k].rename(columns = 
                  {"candidate":"winner","candidatevotes":"winVotes", "totalvotes":"totalVotes"})
        calculated[k].to_csv(tbl(f"{k}Margins.csv"), index = False)
    print("Processed data")