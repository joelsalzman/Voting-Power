# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 13:54:06 2019

@author: joelj
"""

# Imports
import geopandas as gpd
import os, json, shapely
from shapely.geometry import shape, mapping
from shapely.geometry.multipolygon import MultiPolygon
import sys
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *



### Returns a dictionary containing the year and associated congressional districts shapefile
def getOriginal():
    
    # Prepare a dictionary to return the shapefiles
    cgd = {}

    # Transform the shapefile name into the year it was drawn for use as a key (ex: cgd106 -> 1999)
    rename = lambda f: (int(f[f.find("d")+1:f.find("d")+4]) * 2) + 1787
    
    # Put the shapefiles into a dictionary
    for file in os.listdir(os.path.join(os.getcwd(), "GIS", "cgd", "original")):
        if file.endswith(".shp"):
            shp = gpd.read_file(os.path.join(os.getcwd(), "GIS", "cgd", "original", file))
            shp.crs = {"init": "epsg:4326"}
            cgd[rename(file)] = shp
    
    return cgd
  


### Returns a new MultiPolygon with changed coordinates
def roundCoords(coords, precision=0, tree=[]):
    
    # Fill empty lists with properly nested tuples
    newCoords = []
    for a in range(len(coords)):
        outer = [[]]
        for b in range(len(coords[a][0])):
            inner = []
            for c in coords[a][0][b]:
                inner.append(round(c, precision))
                
            outer[0].append(tuple(inner))
        newCoords.append(tuple(outer))
        outer[0] = tuple(outer[0])
    
    # Return a new MultiPolygon constructed from the new coordinates
    return shape(json.loads(json.dumps({"type": "MultiPolygon", "coordinates": newCoords})))



### Make invalid geometries valid
def ensureValid(df, geom_type=MultiPolygon):
    
    # See if there are invalid geometries
    old = len(df)
    bad = len(df[~df.is_valid])
    if bad:
        
        # Use a zero buffer to fix problematic intersections
        df.geometry = df.geometry.apply(lambda g: g.buffer(0.0) if not g.is_valid else g)
        
        # Remove remaining invalid geometries because I have no idea how to fix them
        df = df.loc[df.is_valid & ~df.is_empty]
        
        # Print how many geometries were changed
        dropped = f", dropped {str(old - len(df))}" if old != len(df) else ""
        print(f"        Fixed {bad} invalid polygon(s)", end = f"{dropped}\n")
        
        
    # Ensure that every geometry is a MultiPolygon
    df.geometry = df.geometry.apply(lambda g: geom_type([g]) if type(g) != geom_type else g)
    
    return df



### Prepares shapefiles for geocoding
def prepShapefiles():
    
    # Prepare variables
    keepInShp = ['geometry', 'STATE', 'CONG_DIST', 'CD116FP', 'CD115FP']
    shapes  = getOriginal()
    prepped = {}
    
    for k in shapes.keys():
        print(f"    Preparing {k}...")
        
        # Grab the file
        shp = shapes[k]
        
        # Round the points
        shp = ensureValid(shp)
        newPolys = []
        for f in mapping(shp.geometry)["features"]:
            coords  = json.loads(json.dumps(f["geometry"]["coordinates"]))
            rounded = roundCoords(coords, precision = 5)
            newPolys.append(rounded)
        shp["geometry"] = newPolys
        shp = shp[shp.is_valid]
        
        # Make sure the file has the correct fields
        if "STATE" not in shp.columns:
            shp["STATE"] = [states.loc[states["FP"] == float(fp), "State"].values[0] for fp in shp["STATEFP"]]
        shp = shp.filter(items = keepInShp).dropna()
        shp.columns = [c if c not in keepInShp[-3:] else "DISTRICT" for c in shp.columns]
        if len(shp["STATE"][0]) == 2:
            shp["STATE"] = [states.loc[states["Abbr"] == st, "State"].values[0] for st in shp["STATE"]]
        
        # Ensure there's only one row per district
        shp = shp.dissolve(by = ["STATE", "DISTRICT"])
        shp.reset_index(inplace = True)
        
        # Get the dataframe ready for merging
        shp = shp[shp["DISTRICT"] != "ZZ"]
        shp["DISTRICT"] = shp["DISTRICT"].astype("float64")
        shp.geometry = ensureValid(shp)
        prepped[k] = shp
        shp.to_file(cgdPath(f"clean_{k}.js", "clean"), driver = "GeoJSON", encoding = "UTF-8")
    
    print("Prepared shapefiles\n")
    return prepped