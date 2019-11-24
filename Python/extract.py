# -*- coding: utf-8 -*-
"""
    Extracts compressed shapefiles

Created on Thu Oct 17 12:16:26 2019

@author: Joel Salzman
"""

import os, shutil
os.chdir(r"C:\Users\joelj\OneDrive\Documents\Projects\Voting\GIS\cgd")

def extractAllInFolder(folder, out=True):
    success = False
    done = []
    for file in os.listdir(os.getcwd()):
        try:
            if file not in done:
                shutil.unpack_archive(os.path.join(os.getcwd(), file))
                done.append(file)
                success = True
            if out:
                print(f"Extracted {file}")
        except:
            if out:
                print(f"Failed on {file}")
    return success

stop = 0;
while(extractAllInFolder("clean") and stop < 4):
    continue
    stop+=1