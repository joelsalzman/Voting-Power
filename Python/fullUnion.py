# -*- coding: utf-8 -*-
"""
    Overlays all congressional districts into a single layer

Created on Thu Nov 21 12:06:41 2019

@author: Joel Salzman
"""

# Imports
import pandas as pd
import geopandas as gpd
import os, shapely, json, time
from shapely.geometry import shape
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
import sys
sys.path.append(os.path.join(os.getcwd(), "Python"))
from useful import *



### Returns a dictionary containing the year and associated congressional districts shapefile
def getCGD():
    
    # Prepare a dictionary to return the shapefiles
    cgd = {}

    # Transform the shapefile name into the year it was drawn for use as a key (ex: cgd106 -> 1999)
    rename = lambda f: (int(f[f.find("d")+1:f.find("d")+4]) * 2) + 1787
    
    # Put the shapefiles into a dictionary
    for file in os.listdir(os.path.join(os.getcwd(), "GIS", "cgd", "original")):
        if file.endswith(".shp"):
            shp = gpd.read_file(os.path.join(os.getcwd(), "GIS", "cgd", "original", file))
            shp.crs = {'init' :'epsg:4326'}
            cgd[rename(file)] = shp
    
    return cgd
  


### Returns either a new MultiPolygon with changed coordinates or a list of point coordinates
def roundCoords(coords, precision=0):
    
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
    return shape(json.loads(json.dumps({"type": "MultiPolygon", "coordinates": newCoords}))).buffer(0.00001)

    

### Prepares shapefiles for geocoding
def prepShapefiles(forUnion=False):
    
    # Prepare variables
    keepInShp = ['geometry', 'STATE', 'CONG_DIST', 'CD116FP', 'CD115FP']
    shapes  = getCGD()
    prepped = {}
    
    for k in shapes.keys():
        print(f"    Preparing {k}...")
        
        # Grab the file
        shp = shapes[k]
        
        # Round the points
        shp["geometry"] = [MultiPolygon([ft]) if type(ft) == Polygon else ft for ft in shp.geometry]
        newPolys = []
        for f in shapely.geometry.mapping(shp.geometry)["features"]:
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
        
        # Drop the State column in all but one of the shapefiles to be merged
        if forUnion and k != list(shapes.keys())[0]:
            shp = shp.drop(columns = ["STATE"])
        
        # Get the dataframe ready for merging
        shp = shp[shp["DISTRICT"] != "ZZ"]
        shp["DISTRICT"] = shp["DISTRICT"].astype("float64")
        prepped[k] = shp
    
    print("Prepared shapefiles\n")
    return prepped

 
        
### Overlays all the congressional districts into a single layer
def fullUnion(prepped = {}):
    
    # Prepare to union everything
    #cgds = prepped if len(prepped) else prepShapefiles(True)
    t0 = time.time()
    one = gpd.read_file(cgdPath("cgd_union_1999to2005.js"), encoding = "UTF-8")
    print(f"Got 1999-2005 in {time.time() - t0} seconds")
    two = gpd.read_file(cgdPath("cgd_union_2007to2013.js"), encoding = "UTF-8")
    print(f"Got 2007-2013 in {time.time() - t0} seconds")
    three = gpd.read_file(cgdPath("cgd_union_2015to2019.js"), encoding = "UTF-8")
    print(f"Got 2015-2019 in {time.time() - t0} seconds")
    cgds = {"1":one, "2":two, "3":three}
    
    # Perform the unions
    lyrs = list(cgds.values())
    while len(lyrs) > 1:
        try:
            print(f"Trying Union {len(cgds) - len(lyrs) + 1}/{len(cgds) - 1} ({time.time() - t0} seconds)")
            overlaid = gpd.overlay(lyrs[-1], lyrs[-2], how = "union")
        except:
            try:
                print(f"    Buffering... ({time.time() - t0} seconds)")
                lyrs[-1]["geometry"] = lyrs[-1].geometry.buffer(0.00001)
                print(f"    Buffer created ({time.time() - t0})")
                overlaid = gpd.overlay(lyrs[-1], lyrs[-2], how = "union")
            except:
                print(f"    Buffering... ({time.time() - t0} seconds)")
                lyrs[-2]["geometry"] = lyrs[-2].geometry.buffer(0.00001)
                print(f"    Buffer created ({time.time() - t0} seconds)")
                overlaid = gpd.overlay(lyrs[-1], lyrs[-2], how = "union")
        lyrs.insert(0, overlaid)
        lyrs.pop()
        lyrs.pop()
        
    # Output
    lyrs[0].to_json(cgdPath("CGD_UNION.js"), driver = "GeoJSON", encoding = "UTF-8")
    print("Union complete: {time.time() - t0} seconds\n")
    return lyrs[0]

fullUnion()