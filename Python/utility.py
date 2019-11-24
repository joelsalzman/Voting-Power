# -*- coding: utf-8 -*-
"""
    Calculates utility values of congressional districts

Created on Tue Nov 19 11:58:18 2019

@author: Joel Salzman
"""

# Imports
import geopandas as gpd
import numpy as np
import os
import sys
sys.path.append(os.path.join(os.getcwd(), "Python"))
from useful import *

### Assigns utility values to polygons
def utilityValues():
    
    # Prepare to add 
    full = gpd.read_file(cgdPath("CGD_UNION.js"))
    
    ### Calculates utility values
    def util(row, office, marginType):
        
        # Utility values of congressional races are just the average margin
        if office != "p":
            vals = [row.col if office in col and marginType in col else None for col in row.index]
            return np.average(filter(None, vals))
        
        # Presidential utility values must be multiplied by the number of electors in that state
        vals = {row[row.col.find("_")+1: row.col.find("_")+5]:
            row.col if office in col and marginType in col else None for col in row.index}
        if row.state not in ["NE", "ME"]:
            for yr in years:
                vals[yr] *= states[row.state][f"E_{yr[:3]}0"]
            return np.average(filter(None, vals.values()))
        
        # Nebraksa and Maine do proportional allocation
        for yr in years:
            vals[yr] *= states[row.state][f"E_{yr[:3]}0"] - 2
        #GET DATA FOR INDIVIDUAL DISTRICTS#########################################
    
    
    # Add a utility value for each type of individual office
    for office in ("h", "s", "p"):
        for mt in ("raw", "dec"): 
            full[f"{office}_AVG{mt}Margin"] = full.apply(lambda r: util(r, office, mt), axis = 1)
    
    # Combine values
    full["all_rawUTILITY"] = full.apply(lambda r: np.average(
            [r.at[f"{office}_AVGrawMargin"] for office in ("h", "s", "p")]))
    full["all_decUTILITY"] = full.apply(lambda r: np.average(
            [r.at[f"{office}_AVGdecMargin"] for office in ("h", "s", "p")]))
