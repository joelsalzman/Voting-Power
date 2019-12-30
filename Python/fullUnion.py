# -*- coding: utf-8 -*-
"""
    Overlays all congressional districts into a single layer

Created on Thu Nov 21 12:06:41 2019

@author: Joel Salzman
"""

# Imports
import geopandas as gpd
import numpy as np
import os, time, sys
from shapely.wkt import dumps, loads
from shapely.ops import unary_union
sys.path.append(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\Python")
from useful import *
from prepGeoms import *
import warnings
warnings.filterwarnings(action = "ignore")



### Grabs prepped shapefiles
def getFiles(folder, getAll=True):
    
    # Fill a dictionary with the cgds
    cgds = {}
    for file in os.listdir(cgdPath("", folder)):
        if "." not in file:
            continue
        df = gpd.read_file(cgdPath(file, folder), driver = "GeoJSON", encoding = "UTF-8")
        
        # Change the name of the key
        key = file.replace("clean_","").replace(".js","")
        try:
            cgds[int(key)] = df
        except:
            cgds[key] = df
        print(f"Loaded {list(cgds.keys())[-1]}")
        
        if not getAll and len(cgds):
            break
    
    # If the cgds aren't accessible, generate them
    if len(cgds) == 0:
        cgds = prepShapefiles()
        
    return cgds



### Union lots of geometries by stacking them
def stackUnion(add, stack, thing, sliver_size=0.001):
    
    # Prepare to fail
    failures = []
    backup = stack.copy()
    
    # Ensure the geometries are all valid
    add   = ensureValid(add)
    stack = ensureValid(stack)
    
    # Union the new layer to the overlay
    try:
        try:
            stack = gpd.overlay(add, stack, "union")
        except:
            stack = roundCoords(stack, 5)
            try:
                stack = gpd.overlay(add, stack, "union")
            except:
                add   = roundCoords(add, 5)
                stack = gpd.overlay(ensureValid(add), ensureValid(stack), "union")
            
        # Round the coordinates
        stack = roundCoords(stack, 5)
        print(f"    Added {thing}{' '*(21-len(thing))}{now()}")
            
    except Exception as e:
        failures.append(thing)
        print(e)
        print(f"--- FAILED TO ADD {thing} ---------\n")
        return backup, failures
        
    # Return the new union
    stack = ensureValid(stack)
    return stack, failures



### Makes sure fields stay full
def fillFields(row):
    
    # Make sure not to loop forever
    iterations = 0
    
    # Only act if there are null values in the row
    while len(row) != len(row.dropna()):
        
        # Set the numerical index
        idx = 0
        
        # Check the columns
        for col, val in row.items():
            if "DIS" in str(col) and np.isnan(val):
                
                # First try to set the value to the previous column's
                if idx > 0 and not np.isnan(row.iloc[idx-1]):
                    row.iloc[idx] = row.iloc[idx-1]
                    
                # If the previous column is empty, try setting the value to the next column's
                elif not np.isnan(row.iloc[idx+1]):
                    row.iloc[idx] = row.iloc[idx+1]
                    
            idx += 1
            
        iterations += 1
        if iterations == len(row):
            break
    
    return row

 
        
### Overlays all the congressional districts over time into a single layer for each state
def stateUnion(st, cgds={}, out=True, reverse=False, stop=None):
    
    # Prepare to union everything
    if not len(cgds):
        cgds = getFiles("clean")
    cgdKeys = list(cgds.keys())
    tst = time.time()
    
    # Create empty dictionaries to store information for the logs
    failures  = {st:[]}
    additions = {st:[]}
    
    print(f"Unioning {st}{' '*(21 - len(st))} {now()}")
    
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
    if not stop or str(stop) not in keys[0]:
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
            
            # Make sure the fields are in the right order and are full
            full = full[sorted(full.columns)].apply(lambda r: fillFields(r))
            
            # Stop if requested
            if stop and str(stop) in k:
                break
                
    # Output the union
    full = ensureValid(full)
    full["STATE"] = st
    if out:
        full.to_file(cgdPath(f"{st}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Completed {st}{' '*(20 - len(st))} {now(tst, False)}")
    return full, failures, additions



### Does the state in separate halves
def halfState(st, cgds={}):
    
    if not len(cgds):
        cgds = getFiles("clean")
    print(f"Attempting halfState on {st}")
        
    first  = stateUnion(st, cgds, False, False, 2009)[0]
    second = stateUnion(st, cgds, False, True,  2011)[0]
    both   = stackUnion(first, second, f"{st} Both")
    bothFx = both[0][sorted(both[0].columns)].apply(lambda r: fillFields(r))
    bothFx.to_file(cgdPath(f"{st}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
    
    return bothFx, {st:[]}
    


### Performs the stateUnion for every state
def allStates(cgds={}, reverse=False, start_at=None):
            
    # Prepare an empty list to fill with the unioned layers
    lyrs = []
        
    # Get the files if necessary
    clean = getFiles("clean") if not len(cgds) else cgds
    
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
            print(f"Unioning {st}{' '*(21 - len(st))} {now()}")
            
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
            print(f"Completed {st}{' '*(20 - len(st))} {now(tst, False)}")
            
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
        
        if len(union[1][st]):
            del union
            union = halfState(st, clean)
        
        union = union.apply(lambda r: fillFields(r))
        
        # Print the information about the state union to text files
        for i in range(1, len(union)):
            info = union[i]
            key = "failures" if i == 1 else "additions"
            with open(os.path.join(os.getcwd(), "Python", "logs", f"stateUnion_{key}.txt"), "a+") as f:
                f.write(f"{st}: {info[st]}\n")
    
    print(f"Total time elapsed: {now()}")
    return lyrs



### Merges the overlaid states into one file
def fullUnion(lyrs={}):
    
    failures = []
    
    # Get the files
    if not len(lyrs):
        lyrs = getFiles("by_state")
    
    # Set up the base
    base = list(getFiles("clean", False).values())[0].drop(columns = ["DISTRICT"])
    base = ensureValid(roundCoords(base.dissolve(by = "STATE").reset_index(), 5))
    full = []
    print("Created base")
        
    # Join all layers together
    for k in list(lyrs.keys()):
        gdf = lyrs[k]
        
        bs = base.loc[base["STATE"] == k]
        bs.geometry = [unary_union(bs.geometry)]
        
        try:
            clip = gpd.overlay(ensureValid(gdf), bs, "intersection")
        except:
            try:
                rnd  = roundCoords(ensureValid(gdf), 5)
                clip = gpd.overlay(ensureValid(rnd), ensureValid(bs), "intersection")
            except:
                print(f"--- FAILED ON {k} ---")
                failures.append(k)
                continue
        
        full = clip if not len(full) else full.append(clip)
        
        print(f"    Added {k}{' '*(20 - len(k))} {now()}")
        
    # Output
    full = ensureValid(full)
    full.to_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    print(f"Union complete")
    if len(failures):
        print(failures)
    
    

### Replaces a state's data in the full union
def updateFull(state, file=""):
    
    # Get the files
    full = gpd.read_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")
    if not len(file):
        file = gpd.read_file(cgdPath(f"{state}.js", "by_state"), driver = "GeoJSON", encoding = "UTF-8")
    
    # Replace any existing rows with the state for the new file
    full = full.loc[full["STATE"] != state].append(file)
    print(f"Updated {state}")
    
    # Return the updated file
    full.to_file(cgdPath("CGD_UNION.js", ""), driver = "GeoJSON", encoding = "UTF-8")