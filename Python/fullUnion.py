# -*- coding: utf-8 -*-
"""
    Overlays all congressional districts into a single layer

Created on Thu Nov 21 12:06:41 2019

@author: Joel Salzman
"""

# Imports
import geopandas as gpd
import os, time, sys
from shapely.ops import snap, unary_union
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from prepGeoms import *
import warnings
warnings.filterwarnings(action = "ignore")



### Grabs prepped shapefiles
def getClean():
    
    # Fill a dictionary with the cgds
    cgds = {}
    for file in os.listdir(cgdPath("", "clean")):
        if "." not in file:
            continue
        df = gpd.read_file(cgdPath(file, "clean"), driver = "GeoJSON", encoding = "UTF-8")
        
        # Change the name of the key
        cgds[int(file.replace("clean_","").replace(".js",""))] = df
        print(f"Loaded {list(cgds.keys())[-1]}")
    
    # If the clean cgds aren't accessible, generate them
    if len(cgds) == 0:
        cgds = prepShapefiles()
        
    return cgds



### Eliminates sliver polygons
def eliminateSlivers(gdf, sliver_size):
    
    # Make sure that all the geometries are valid
    gdf = ensureValid(gdf)
    
    # Determine which polygons count as slivers
    eliminate = gdf[gdf.geometry.area < sliver_size]
    ignored = 0
    
    for row in eliminate.itertuples():
        
        # Copy the sliver to a new GeoDataFrame
        sliver = gpd.GeoDataFrame([row])
        
        # Subset the adjacent polygons
        closeby = gdf[gdf.geometry.intersects(sliver) | gdf.geometry.touches(sliver)]
        
        # If there are no adjacent polygons, buffer the sliver and search again
        if not len(closeby):
            bigSliv = sliver
            bigSliv.geometry = [bigSliv.geometry[0].buffer(0.1)]
            closeby = gdf[gdf.geometry.intersects(bigSliv) | gdf.geometry.touches(bigSliv)]
            
            # Ignore slivers with no neighbors
            if not len(closeby):
                ignored += 1
                continue
        
        # Select the biggest adjacent polygon
        biggest = closeby.loc[closeby.geometry.area.idxmax()]
            
        # Remove all columns from the sliver except for geometry
        cols = list(sliver.columns)
        cols.remove("geometry")
        sliver = sliver.drop(columns = cols)
        
        # Merge the sliver with the biggest adjacent polygon
        sliver.crs = biggest.crs = {"init": "epsg:4326"}
        both = gpd.overlay(sliver, gpd.GeoDataFrame([biggest]), "union")
        biggest["geometry"] = [both.geometry.unary_union]
    
    if len(eliminate):
        print(f"      Found {len(eliminate)} sliver(s), {ignored} ignored")
    gdf.reset_index(drop = True, inplace = True)
    return gdf



### Union lots of geometries by stacking them
def stackUnion(add, stack, thing, sliver_size=0.001):
    
    print(f"    Adding {thing}...")
    
    # Prepare to fail
    failures = []
    backup = stack.copy()
    
    # Ensure the geometries are all valid
    add   = ensureValid(add)
    stack = roundCoords(stack, 5)
    
    try:
        
        # Union the new layer to the overlay
        stack = gpd.overlay(add, stack, "union")
        print(f"      Union performed {now()}")
        
        # Round the coordinates
        stack = eliminateSlivers(stack, sliver_size)
        stack = roundCoords(stack, 5)
        print(f"    Added  {thing}       {now()}")
            
    except Exception as e:
        failures.append(thing)
        print(e)
        print(f"--- FAILED TO ADD {thing} ---------\n")
        return backup, failures
        
    # Return the new union
    stack = ensureValid(stack)
    return stack, failures

 
        
### Overlays all the congressional districts over time into a single layer for each state
def stateUnion(st, cgds={}, reverse=False):
    
    # Prepare to union everything
    cgdKeys = list(cgds.keys())
    if not len(cgds):
        cgds = getClean()
    tst = time.time()
    
    # Create empty dictionaries to store information for the logs
    failures  = {st:[]}
    additions = {st:[]}
    
    print(f"Unioning {st} at {now()}")
    
    # Isolate and prepare the files
    files = []
    for yr in cgdKeys:
        df = cgds[yr][cgds[yr]["STATE"] == st]
        if yr != cgdKeys[0]:
            df = df.drop(columns = "STATE")
        df = df.rename(columns = {"DISTRICT": f"DIS_{yr}"})
        df = ensureValid(df)
        files.append([str(yr), df])
    
    # Union identical geometries first
    uniqueGeoms = {}
    for i in range(1, len(files)):
        testGeomEquals = files[i][1].geometry.geom_equals(files[i-1][1].geometry).unique()
        if len(testGeomEquals) and testGeomEquals[-1]:
            union = gpd.overlay(files[i][1], files[i-1][1], "union")
            print(f"    Added {files[i][0]} to {files[i-1][0]}")
            
            # Put the new GeoDataFrame in the dictionary
            oldKey = f"{files[i-1][0]}"
            newKey = f'{oldKey.replace(f"{files[i][0]} ,","").replace(f"{files[i][0]}","")}, {files[i][0]}'
            uniqueGeoms[newKey] = union
            if oldKey in uniqueGeoms:
                uniqueGeoms.pop(oldKey)
            files[i] = [newKey, union]
        else:
            uniqueGeoms[files[i][0]] = files[i][1]
    
    # Union the rest of the geometries
    keys = list(uniqueGeoms.keys()) if not reverse else list(reversed(list(uniqueGeoms.keys())))
    full = uniqueGeoms[keys[0]]
    print(f"  Beginning Stack Union...\n    Added {keys[0]}")
    for k in keys[1:]:
        
        # Union the geometries
        stack = stackUnion(uniqueGeoms[k], full, k, 0)
        
        # Store relevant information
        if len(stack[1]):
            failures[st].append(stack[1])
        prev = len(full)
        full = stack[0]
        diff = len(full) - prev
        if diff:
            print(f"      {diff} new polygon(s), total now {len(full)}")
            additions[st].append(f"{k} {diff}")
                
    # Output the union
    full = ensureValid(full)
    full.to_file(cgdPath(f"{st}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
    print(f"{st} completed in {now(tst)}")
    return full, failures, additions
    


### Performs the stateUnion for every state
def allStates(cgds={}, reverse=False, start_at=None):
            
    # Prepare an empty list to fill with the unioned layers
    lyrs = []
        
    # Get the files if necessary
    clean = getClean() if not len(cgds) else cgds
    
    # Clear the logs
    if not start_at:
        for log in ("failures", "additions"):
            with open(os.path.join(os.getcwd(), "Python", "logs", f"stateUnion_{log}.txt"), "w") as f:
                f.write("")
    
    # Order the states by number of congressional districts in ascending order
    orderedStates = states.sort_values(by = ["E_1990"])
    soFar = 0
    
    # Do a simple attribute join on states with only one district
    simple = orderedStates[orderedStates["E_1990"] == 3]["State"].tolist()
    if not start_at or start_at in simple:
        for st in simple:
            tst = time.time()
            soFar += 1
            print(f"\n{soFar}/51")
            print(f"Unioning {st} at {now()}")
            
            # Isolate the state in the first year to use as a base
            yr = list(clean.keys())[0]
            base = clean[yr].loc[clean[yr]["STATE"] == st].rename(columns = {"DISTRICT": f"DIS_{yr}"})
            base = ensureValid(base)
            
            # Join the District column in the other years to the base
            for yr in list(clean.keys())[1:]:
                df = clean[yr][clean[yr]["STATE"] == st]
                df = df.drop(columns = "geometry")
                df = df.rename(columns = {"DISTRICT": f"DIS_{yr}"})
                base = base.merge(df, how = "left", left_on = ["STATE"], right_on = ["STATE"])
            
            # Output the merged file
            lyrs.append(base)
            base.to_file(cgdPath(f"{st}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
            print(f"{st} completed in {now(tst)}")
            
    # Union the rest of the states' congressional districts
    stateList  = orderedStates[orderedStates["E_1990"] > 3]["State"].tolist()
    foundStart = False
    for st in stateList:
        soFar += 1
        
        # Skip states if required
        if start_at and not foundStart:
            if st != start_at:
                continue
            else:
                soFar += len(simple)
                foundStart = True
        print(f"\n\nState {soFar}/{len(simple) + len(stateList)}")
        
        # Perform the union
        union = stateUnion(st, clean, reverse)
        lyrs.append(union[0]) 
        
        # Print the information about the state union to text files
        for i in range(1, len(union)):
            info = union[i]
            key = "failures" if i == 1 else "additions"
            with open(os.path.join(os.getcwd(), "Python", "logs", f"stateUnion_{key}.txt"), "a+") as f:
                f.write(f"{st}: {info[st]}\n")
    
    print(f"Total time elapsed: {now()}")
    return lyrs



### Merges the overlaid states into one file
def fullUnion():
    
    lyrs = getClean()
            
    # Find the smallest polygon in all the states to define how large slivers can be
    sliverMax  = min([float(p.area) for p in [g for g in [gdf.geometry for gdf in lyrs]]]) - 0.00001
    
    # Join all layers together
    full = list(lyrs.values())[0]
    for yr in list(lyrs.keys())[1:]:
        full = stackUnion(lyrs[yr], full, yr, sliverMax)[0]
        
    # Output
    full.to_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Union complete")
    
    

fullUnion()