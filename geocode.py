# -*- coding: utf-8 -*-
"""
    Geocodes data

Created on Tue Nov 19 11:55:10 2019

@author: Joel Salzman
"""

# Imports
import pandas as pd
import geopandas as gpd
import sys
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from prepGeoms import prepShapefiles, ensureValid
from fullUnion import getFiles, stackUnion
    


### Pulls and cleans voting data
def getVotingData(merge=True):
    
    offices = {key:pd.read_csv(tbl(f'{key}Margins.csv')) for key in ("prez", "senate", "house")}

    # Prepare to merge the data by setting column names and types
    for o in offices.keys():
        uniqueCols = []
        for c in list(offices[o].columns):
            col = f"{o[:1]}_{c}" if c in keepFromCSV[3:] + newCols else c
            uniqueCols.append(col)
        offices[o].columns = uniqueCols
        for c in offices[o].columns:
            if offices[o][c].dtype == "bool" or "Votes" in c or "Margin" in c:
                offices[o][c] = offices[o][c].astype("float64")
    
    # Return a dictionary with the separate dataframes
    if not merge:
        return offices
    
    # Merge the voting data into one dataframe
    return offices["prez"].merge(
                    offices["senate"], how="outer", left_on=["state", "year"], right_on=["state", "year"]
            ).merge(
                    offices["house"],  how="outer", left_on=["state", "year"], right_on=["state", "year"])



### Geocodes the data to year maps
def addByYear(yr):
    
    # Grab the data
    offices = getVotingData()
    cgd     = prepShapefiles()
    files   = getFiles("by_year")
    full    = list(files.values())[0]
    for yr in list(files.keys())[1:]:
        full = stackUnion(files[yr], full, yr)
    
    # Add attributes to the shapefiles
    if yr in cgd.keys(): ########## FIX FOR SPECIALS
        shp = cgd[yr]
        y = yr + 1
    
    # Merge all data from the year into one dataframe
    houseYr  = offices["house"] [offices["house"] ["year"] == y] ##### FIX
    prezYr   = offices["prez"]  [offices["prez"]  ["year"] == y] ##### FOR
    senateYr = offices["senate"][offices["senate"]["year"] == y] ##### L8R
    
    stw = prezYr.merge(senateYr, how="outer", left_on=["state", "year"], right_on=["state", "year"])
    df  = houseYr.merge(stw,     how="left",  left_on=["state", "year"], right_on=["state", "year"])
    
    # Ensure geometry is still okay
    shp = ensureValid(shp)
    
    df.to_csv(tbl(f"Full_{yr}.csv"), index = False)
    
    # Merge the data with the shapefile
    try:
        merged = shp.merge(df, how="left", left_on=["STATE", "DISTRICT"], right_on=["state", "district"])
        merged = merged.drop(columns = ["STATE", "DISTRICT", "year"])
        merged.to_file(cgdPath(f"cgdFrom_{yr}.js"), driver = 'GeoJSON', encoding = "UTF-8")
        print(f"    Merged {yr} to shp...")
    except Exception as e:
        print(f"    FAILED TO MERGE {yr} TO SHP: {e}")
    
    print("Added attributes")



### Adds margin data to the unioned GeoDataFrame
def geocode(gdf=""):
    
    # Grab the data
    if not len(gdf):
        gdf = gpd.read_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    merged = gdf.copy()
    allData = getVotingData()
    print(f"    Loaded data               {now()}")
    
    # Make sure the columns are all the same type
    for df in (merged, allData):
        for c in df.columns:
            df[c] = df[c].astype("object")
    
    # Merge the data by year
    for yr, df in allData.groupby("year"):
        
        # Rename the columns
        dist = f"DIS_{int(yr)-1}"
        data = df.copy().rename(columns = {"district": dist, "state": "STATE"}).drop(columns = "year")
        data.columns = [f"{c}_{yr}" if c not in ("STATE", dist) else c for c in data.columns]
        
        # Drop useless columns
        data = data.drop_duplicates().dropna(axis = 1, how = "all")
        
        # Merge the data
        merged = merged.merge(data, how = "left", left_on = ["STATE", dist], right_on = ["STATE", dist])
        print(f"    Geocoded {yr} elections   {now()}")
    
    # Make sure the output has the correct rows and columns
    merged = ensureValid(merged)
    cols  = list(merged.columns)
    gmIdx = cols.index("geometry")
    merged = merged[cols[:gmIdx] + cols[gmIdx+1:] + [cols[gmIdx]]]
    print(f"Voting data geocoded          {now()}")

    # Output the file
    merged.to_csv(tbl("_MERGED.csv"))
    merged.to_file(cgdPath("CGD_MERGED.js", ""), driver = "GeoJSON", encoding = "UTF-8")
