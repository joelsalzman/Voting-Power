# -*- coding: utf-8 -*-
"""
    Calculates utility values of congressional districts

Created on Tue Nov 19 11:58:18 2019

@author: Joel Salzman
"""

# Imports
import geopandas as gpd
import numpy as np
import sys
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *

### Assigns utility values to polygons
def utilityValues(f=""):
    
    
    ### Calculates utility values by row
    def utilByRow(row, office, marginType):
        
        # Select the correct values in the row
        vals = {col: row.at[col] if office in col and marginType in col else None for col in row.index}
        [vals.pop(col) if not vals[col] else vals[col] for col in row.index]
        
        # Presidential utility values must be multiplied by the number of electors in that state
        if office == "p":
            for yr in years:
                electors = float(states.loc[states["State"] == row["STATE"]][f"E_{str(yr)[:3]}0"])
                
                if row["STATE"] not in ["NE", "ME"]:
                    for col in vals.keys():
                        vals[col] *= electors
                
                # Nebraksa and Maine do proportional allocation
                else:
                    for col in vals.keys():
                        vals[col] *= electors - 2
                    #GET DATA FOR INDIVIDUAL DISTRICTS#########################################

        # Return the average margin of victory across all relevant races
        return np.nanmean(list(vals.values()))
    
    
    # Prepare to add 
    full = f if len(f) else gpd.read_file(cgdPath("CGD_MERGED.js", ""), driver="GeoJSON", encoding="UTF-8")
    
    # Add a utility value for each type of individual office
    for mt in ("raw", "dec"): 
        for office in ("house", "senate", "prez"):
            full[f"{office}_AVG{mt}Margin"] = full.apply(lambda r: utilByRow(r, office[0], mt), axis = 1)
            print(f"    Averaged {office} {mt}{' '*(16-len(office)-len(mt))}{now()}")
    
        # Combine values
        full[f"all_{mt}UTILITY"] = full.apply(lambda r: np.nanmean(
                [r.at[f"{office}_AVGrawMargin"] for office in ("h", "s", "p")]))
        print(f"    Calculated {mt} utility{' '*(16-len(mt))}{now()}")
    
    # Output files
    simple = full.drop(columns = list(full.columns)[:list(full.columns).index("geometry")])
    simple.to_file(cgdPath("CGD_SIMPLE.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Outputted Simple                          {now()}")
    full.to_file(cgdPath("CGD_FINAL.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Outputted Full                            {now()}")
