# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 13:54:06 2019

@author: joelj
"""

# Imports
import geopandas as gpd
import os, sys, json
from shapely.geometry import shape, mapping
from shapely.wkt import dumps, loads
from shapely.geometry.multipolygon import MultiPolygon
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from makevalid import make_geom_valid ### From https://github.com/ftwillms/makevalid



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



### Rounds coordinates
def roundCoords(shp, precision=0):
    
    # Prepare an empty list for the rounded coordinates
    newPolys = []
    shp.geometry = shp.geometry.apply(lambda g: MultiPolygon([g]) if type(g) != MultiPolygon else g)
    
    # Grab the coordinates
    for f in mapping(shp.geometry)["features"]:
        coords  = json.loads(json.dumps(f["geometry"]["coordinates"]))
    
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
        
        # Create a new MultiPolygon from the new coordinates
        newShape = shape(json.loads(json.dumps({"type": "MultiPolygon", "coordinates": newCoords})))
        newPolys.append(newShape)
    
    # Return the new geometries
    shp["geometry"] = newPolys
    return shp



### Make invalid geometries valid instances of the correct type
def ensureValid(gdf, geom_type=MultiPolygon):
    
    gdf = gdf[~gdf.geometry.isna()]
    gdf.geometry = gdf.geometry.apply(lambda g: make_geom_valid(g))
    gdf.geometry = gdf.geometry.apply(lambda g: geom_type([g]) if type(g) != geom_type else g)
    return gdf



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
        
        # Make sure the geometries are valid
        shp = ensureValid(shp)
        shp = roundCoords(shp, 5)
        
        # Get the dataframe ready for merging
        shp = shp[shp["DISTRICT"] != "ZZ"]
        shp["DISTRICT"] = shp["DISTRICT"].astype("float64")
        prepped[k] = shp
        shp.to_file(cgdPath(f"clean_{k}.js", "clean"), driver = "GeoJSON", encoding = "UTF-8")
    
    print("Prepared shapefiles\n")
    return prepped