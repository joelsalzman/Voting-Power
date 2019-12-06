# -*- coding: utf-8 -*-
"""
    Overlays all congressional districts into a single layer

Created on Thu Nov 21 12:06:41 2019

@author: Joel Salzman
"""

# Imports
import geopandas as gpd
import numpy as np
import os, time, json, sys
from shapely.ops import snap, unary_union, polygonize
from shapely.geometry import mapping, LineString, MultiPolygon
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from prepGeoms import *



### Grab prepped shapefiles
def getClean():
    
    # Fill a dictionary with the cgds
    cgds = {}
    for file in os.listdir(cgdPath("", "clean")):
        if "." not in file:
            continue
        df = gpd.read_file(cgdPath(file, "clean"), driver = "GeoJSON", encoding = "UTF-8")
        cgds[int(file.replace("clean_","").replace(".js",""))] = df
        print(f"Loaded {list(cgds.keys())[-1]}")
    
    # If the clean cgds aren't accessible, generate them
    if len(cgds) == 0:
        cgds = prepShapefiles()
        
    return cgds



### Eliminates sliver polygons
def eliminateSlivers(gdf, sliver_size, newCols):
    
    # Determine which polygons count as slivers
    eliminate = gdf[gdf.geometry.area < sliver_size]
    ignored   = 0
    
    for row in eliminate.itertuples():
        
        # Copy the sliver to a new GeoDataFrame
        sliver = gpd.GeoDataFrame([row])
        
        # Set conditions for removing the sliver
        hasNaN = len(sliver) != len(sliver.dropna())
        joined = False
        
        # Subset the adjacent polygons
        closeby = gdf[gdf.geometry.intersects(sliver) | gdf.geometry.touches(sliver)]
        if len(closeby):
        
            # Find a polygon with the same non-null, non-recent attributes as the sliver
            attributes = list(sliver.columns)
            similar = closeby
            for a in attributes:
                if a not in ["Index", "geometry", "STATE"] + newCols and not np.isnan(sliver[a][0]):
                    similar = similar.loc[similar[a] == sliver[a][0]]
            if len(similar):
                best = similar.loc[similar.geometry.area.idxmax()]
                
                # Remove all columns from the sliver except for geometry
                cols = list(sliver.columns)
                cols.remove("geometry")
                sliver = sliver.drop(columns = cols)
                
                # Join the sliver to the best polygon
                sliver.crs = best.crs = {"init": "epsg:4326"}
                both = gpd.overlay(sliver, gpd.GeoDataFrame([best]), "union")
                best["geometry"] = [both.geometry.unary_union]
                joined = True
        
        # Either drop the sliver from the overlay or record that there were no suitable joining candidates
        if hasNaN or joined:
            gdf = gdf.drop([row.Index])
        else:
            ignored += 1
    
    print(f"      Found {len(eliminate)} sliver(s), {ignored} ignored")
    gdf.reset_index(drop = True, inplace = True)
    return gdf



### Union lots of geometries by stacking them
def stackUnion(add, stack, thing, sliver_size=0.001):
    
    print(f"    Adding {thing}...")
    
    # Prepare to fail
    failures = []
    backup = stack
    
    try:     

        # Snap the add layer to the stack
        try:
            flat = stack.geometry.unary_union
            add.geometry   = [snap(g, flat, 0.0001) for g in add.geometry]
            stack.geometry = [snap(g, flat, 0.0001) for g in stack.geometry]
        except:
            
            # Try to fix the geometries and try again
            print("        Snap failed, trying buffer...")
            try:
                flat  = stack.geometry.buffer(0.00001).unary_union.buffer(-0.00001)
                
            # Break the polygons down into LineStrings and rebuild them
            except:
                print("        Rebuilding geometries...")
                fixed = []
                stack.geometry = multify(stack)
                for f in mapping(stack.geometry)["features"]:
                     coords = json.loads(json.dumps(f["geometry"]["coordinates"]))
                     cpairs = []
                     for a in range(len(coords)):
                         for b in range(len(coords[a][0])):
                             cpairs.append(tuple(coords[a][0][b]))
                     fixed.append(MultiPolygon(list(polygonize(unary_union(LineString(cpairs))))))
                stack.geometry = fixed
                stack = stack[stack.is_valid]
                flat  = stack.geometry.buffer(0.00001).unary_union.buffer(-0.00001)
            
            # Snap the geometries
            print(f"        Created buffer     ({now()})")
            add.geometry   = [snap(g, flat, 0.0001) for g in add.geometry]
            stack.geometry = [snap(g, flat, 0.0001) for g in stack.geometry]
        
        print(f"        Snapped geometries ({now()})")
        
        # Union the new layer to the overlay
        try:
            stack = gpd.overlay(add, stack, "union")
        
        except:
        
            # Add the unary union of the add geometries to join
            try:
                print(f"        Union failed, trying second buffer...")
                add.geometry = add.geometry.buffer(0.00001).buffer(-0.00001)
                print(f"        Created buffer     ({now()})")
                stack = gpd.overlay(add, stack, "union")
            
            # Iteratively increase the tolerance of the snap and retry
            except:
                print(f"        Union failed, trying more snaps...")
                flat  = stack.geometry.buffer(0.00001).unary_union.buffer(-0.00001)
                attempts = 1
                tol = 0.0002
                while attempts <= 20:
                    try:
                        print(f"        Tolerance now {tol} ({now()})")
                        add.geometry   = [snap(g, flat, round(tol, 4)) for g in add.geometry]
                        stack.geometry = [snap(g, flat, round(tol, 4)) for g in stack.geometry]
                        stack = gpd.overlay(add, stack, "union")
                        attempts = 50
                    except:
                        attempts += 1
                    tol += .0002 if attempts <= 10 else .003
                
                # Break the try block if the union still failed
                if attempts != 50:
                    raise UnboundLocalError("        Union failed with massive snapping tolerance")
                    
        print(f"      Union performed      ({now()})")
        
        # Eliminate sliver polygons
        addCols = list(add.columns)
        addCols.remove("geometry")
        stack   = eliminateSlivers(stack, sliver_size, addCols)
        
        print(f"    Added  {thing} ({now()})")
    
    
    except Exception as e:
        failures.append(thing)
        print(e)
        print(f"--- FAILED TO ADD {thing} ---------\n")
        return backup, failures
        
    # Return the new union
    stack["geometry"] = multify(stack)
    return stack, failures

 
        
### Overlays all the congressional districts over time into a single layer for each state
def stateUnion(st, cgds={}):
    
    # Prepare to union everything
    keys = list(cgds.keys())
    if not len(cgds):
        cgds = getClean()
    tst  = time.time()
    
    # Create empty dictionaries to store information from the logs
    failures  = {st:[]}
    additions = {st:[]}
    
    print(f"Unioning {st} at {now()}")
    
    # Isolate and prepare the files
    files = []
    for yr in keys:
        df = cgds[yr][cgds[yr]["STATE"] == st]
        if yr != keys[0]:
            df = df.drop(columns = "STATE")
        df = df.rename(columns = {"DISTRICT": f"DIS_{yr}"})
        df["geometry"] = multify(df)
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
    full = list(uniqueGeoms.values())[0]
    print(f"  Beginning Stack Union...\n    Added {list(uniqueGeoms.keys())[0]}")
    for k in list(uniqueGeoms.keys())[1:]:
        
        # Union the geometries
        stack = stackUnion(uniqueGeoms[k], full, k)
        
        # Store relevant information
        if len(stack[1]):
            failures[st].append(stack[1])
        prev = len(full)
        full = stack[0].dropna()
        diff = len(full) - prev
        if diff:
            print(f"      {diff} new polygon(s), total now {len(full)}")
            additions[st].append(diff)
                
    # Output the union
    full.geometry = multify(full)
    full.to_file(cgdPath(f"{st}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
    print(f"{st} completed in {now(tst)}")
    return full, failures, additions
    
    

### Merge the overlaid states into one file
def fullUnion(lyrs=[], cgds={}):
    
    if not len(lyrs):
        
        # Get the files if necessary
        clean = getClean() if not len(cgds) else cgds
        
        # Order the states by number of congressional districts in ascending order
        orderedStates = states.sort_values(by = ["E_1990"])
        soFar = 0
        
        # Do a simple attribute join on states with only one elector
        simple = orderedStates[orderedStates["E_1990"] == 3]["State"].tolist()
        for st in simple:
            tst = time.time()
            soFar += 1
            print(f"\n{soFar}/51")
            print(f"Unioning {st} at {now()}")
            
            # Isolate the state in the first year to use as a base
            yr = list(clean.keys())[0]
            base = clean[yr].loc[clean[yr]["STATE"] == st].rename(columns = {"DISTRICT": f"DIS_{yr}"})
            base.geometry = multify(base)
            
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
        stateList = orderedStates[orderedStates["E_1990"] > 3]["State"].tolist()
        for st in stateList:
            soFar += 1
            print(f"\n\n{soFar}/51")
            
            # Perform the union
            union = stateUnion(st, clean)
            lyrs.append(union[0]) 
            
            # Print the information about the state union to text files
            for i in range(1, len(union)):
                info = union[i]
                key = "failures" if i == 1 else "additions"
                with open(os.path.join(os.getcwd(), "Python", "logs", f"stateUnion_{key}.txt"), "a+") as f:
                    f.write(f"{st}: {info[st]}\n")
            
    # Find the smallest polygon in all the states to define how large slivers can be
    sliverMax  = min([float(p.area) for p in [g for g in [df.geometry for df in lyrs]]]) - 0.00001
    
    # Join all the merged states together
    full = list(lyrs.values())[0]
    for st in list(lyrs.keys())[1:]:
        full = stackUnion(lyrs[st], full, st, sliverMax)[0]
        
    # Output
    full.to_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Union complete")



fullUnion(cgds = clean)