# -*- coding: utf-8 -*-
"""
    Geocodes data

Created on Tue Nov 19 11:55:10 2019

@author: Joel Salzman
"""

# Imports
import pandas as pd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import sys
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from fullUnion import prepShapefiles
    


### Geocodes the data
def addAttributes(individual=False):
    print("Trying to add attributes")
    
    # Grab the data
    offices = {key:pd.read_csv(tbl(f'{key}Margins.csv')) for key in ("prez", "senate", "house")}
    cgd = prepShapefiles()
    full = fullUnion(cgd)
    
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
    
    # Add attributes to the shapefiles
    for yr in years:
        if yr in cgd.keys(): ########## FIX FOR SPECIALS
            shp = cgd[yr]
            y = yr + 1
        else:
            continue
        
        # Merge all data from the year into one dataframe
        houseYr  = offices["house"] [offices["house"] ["year"] == y] ##### FIX
        prezYr   = offices["prez"]  [offices["prez"]  ["year"] == y] ##### FOR
        senateYr = offices["senate"][offices["senate"]["year"] == y] ##### L8R
        
        stw = prezYr.merge(senateYr, how="outer", left_on=["state", "year"], right_on=["state", "year"])
        df  = houseYr.merge(stw,     how="left",  left_on=["state", "year"], right_on=["state", "year"])
        
        # Ensure geometry is still okay
        shp["geometry"] = [MultiPolygon([ft]) if type(ft) == Polygon else ft for ft in shp.geometry]
        shp = shp[shp.is_valid]
        
        if individual:
            df.to_csv(tbl(f"Full_{yr}.csv"), index = False)
            
            # Merge the data with the shapefile
            try:
                merged = shp.merge(df, how="left", left_on=["STATE", "DISTRICT"], right_on=["state", "district"])
                merged = merged.drop(columns = ["STATE", "DISTRICT", "year"])
                merged.to_file(cgdPath(f"cgdFrom_{yr}.js"), driver = 'GeoJSON', encoding = "UTF-8")
                print(f"    Merged {yr} to shp...")
            except Exception as e:
                print(f"    FAILED TO MERGE {yr} TO SHP: {e}")
        else:
            
            # Merge the data with the union
            df.columns = [c.replace("_", f"_{y}_") if c not in ["state", "district"] else c for c in df.columns]
            try:
                full = full.merge(df, how="left", left_on=["STATE", f"DISTRICT_{y}"],
                                  right_on=["state", "district"])
                full = full.drop(columns = ["state", "district", "year"])
                full.to_file(cgdPath("CGD_UNION.js"), driver = 'GeoJSON', encoding = "UTF-8")
                full.to_csv(tbl(f"FULL.csv"), index = False)
                print(f"    Merged {yr} to full...")
            except Exception as e:
                print(f"    FAILED TO MERGE {yr} TO FULL: {e}")
    
    print("Added attributes")

addAttributes()