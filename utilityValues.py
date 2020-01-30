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
from prepGeoms import ensureValid

### Assigns utility values to polygons
def utilityValues(file=""):
    
    
    ### Calculates utility values by row
    def utilByRow(row, cols):
        
        # Select the correct values in the row
        valDict = {c: row.at[c] for c in cols}
        vals = np.asarray(list(valDict.values())).astype(float)
        
        # Presidential utility values must be multiplied by the number of electors in that state
        if office == "p":
            electors = []
            for col in valDict.keys():
                
                # Get the correct number of elections for each year
                v = float(states.loc[states["State"] == row["STATE"]][f"E_{col[-4:][:3]}0"])
                v -= 2 if row["STATE"] in ["NE", "ME"] else 0
                electors.append(v)
            
            # Multiply the margins by the number of electors that election affects
            electors = np.asarray(electors).astype(float)
            vals = np.multiply(vals, electors)
            
            # Handle split allocation in Maine and Nebraska
            if row["STATE"] in ["NE", "ME"]:
                menbRow = menb
                for c in cols:
                    menbRow = menbRow.loc[menbRow[c] == row.at[c]]
                menbVals = [menbRow.at[c] for c in cols]
                vals = np.add(vals, menbVals)
                
        # Return the average margin of victory across all relevant races
        return np.nanmean(vals)
    
    
    # Prepare to the geodata
    full = file.copy() if len(file) else gpd.read_file(cgdPath("CGD_MERGED.js", ""), driver="GeoJSON")
    full = ensureValid(full)
    
    # Prepare the other data
    menb = pd.read_csv(tbl("menbMargins.csv"))
    officeDict = {key:pd.read_csv(tbl(f'{key}Margins.csv')) for key in ("prez", "senate", "house")}
    
    # Add a utility value for each type of individual office
    for mt in ("raw", "dec"): 
        for office in ("house", "senate", "prez"):
            
            # Select the correct rows
            o = office[0]
            cols = list(filter(None, [c if mt in c and f"{o}_" in c else None for c in full.columns]))
            
            # Average the values in the row and put them into a new column
            full[f"{o}_AVG{mt}Margin"] = full.apply(lambda r: utilByRow(r, cols), axis = 1)
            print(f"    Averaged {office} {mt}{' '*(16-len(office)-len(mt))}{now()}")
    
            # Find the worst possible margin of that type of election to use to normalize the values
            worst = officeDict[office][f"{mt}Margin"].max()
            
            # Normalize the values
            full[f"{o}_AVG{mt}Margin_nrml"] = full[f"{o}_AVG{mt}Margin"].apply(
                    lambda v: 1 - (float(v) / worst) if not np.isnan(v) else 0)
    
        # Combine values
        nrml = [full[f"{o}_AVG{mt}Margin_nrml"] for o in ("h", "s", "p")]
        full[f"all_{mt}UTILITY"] = np.average(np.array(nrml), axis = 0)
        print(f"    Calculated {mt} utility{' '*(7-len(mt))}{now()}")
    
    # Output files
    simple = full.drop(columns = list(full.columns)[:list(full.columns).index("geometry")])
    simple.to_file(cgdPath("CGD_SIMPLE.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Outputted Simple              {now()}")
    full.to_file(cgdPath("CGD_FINAL.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    full.to_csv(tbl("_FINAL.csv"))
    print(f"Outputted Final               {now()}")
