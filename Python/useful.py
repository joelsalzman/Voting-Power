# -*- coding: utf-8 -*-
"""
    Useful little functions and data

Created on Tue Nov 19 15:49:27 2019

@author: Joel Salzman
"""
import os, time, math
import pandas as pd

# Set working directory
if "Voting" not in os.getcwd():
    os.chdir(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting")
elif "Python" in os.getcwd():
    os.chdir("..")

# Path getters
tbl = lambda file: os.path.join(os.getcwd(), "Tables", file)
cgdPath = lambda file, folder="by_year": os.path.join(os.getcwd(), "GIS", "cgd", folder, f"{file}")

# Useful lists and dataframes
years = [y for y in range(1999, 2020)]  # range of years to look at
states = pd.read_csv(tbl("states.csv")) # state identifiers (name, abbr, fips) and electors by decade
keepFromCSV = ["year", "state", "district",
               "writein", "special", "runoff", "candidate", "party", "candidatevotes", "totalvotes"]
newCols = ["runnerUp", "ruParty", "ruVotes", "rawMargin", "decMargin", "winner", "winVotes", "totalVotes"]

### Record times
t0 = time.time()
def now(t = t0):
    rn   = time.time() - t
    hrs  = 0
    mins = math.floor(rn / 60)
    while (mins >= 60):
        mins -= 60
        hrs  += 1
    sec  = round(rn % 60) if rn > 60 else round(rn)
    if hrs:
        tm = f"{hrs}h:{mins}m:{sec}s"
    if mins:
        tm = f"{mins}m:{sec}s"
    else:
        tm = f"{sec}s"
    return f"{' '*(20 - len(tm))}({tm})"