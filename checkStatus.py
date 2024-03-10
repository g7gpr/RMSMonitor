#!/bin/env python3
# Copyright Mark McIntyre, 2024-
# # Contributions from David Rollinson & Chris Chad

import requests
import datetime
import sys
import os
import configparser
from tkinter import ttk
import tkinter as tk
from termcolor import colored


forceTerminal = False

def readConfigFile(cfgfile):
    cfg = configparser.ConfigParser()
    cfg.read(cfgfile)
    camlist = cfg['settings']['cameras'].split(',')
    thresholdlist = cfg['settings']['thresholds'].split(',')
    reportexception = cfg['settings']['report_only_exception']
    upload_warning = cfg['settings']['upload_warning'].split(',')
    upload_alert = cfg['settings']['upload_alert'].split(',')
    calibration_warning = cfg['settings']['calibration_warning'].split(',')
    calibration_alert = cfg['settings']['calibration_alert'].split(',')
    normal = cfg['settings']['normal'].split(',')
    
    return camlist, thresholdlist, reportexception, upload_warning,upload_alert, calibration_warning, calibration_alert, normal

def getLast(camid, search_string,r):


    if r.status_code != 200:
        if r.status_code == 404:
            print(f'data for {camid} not available')
        else:
            print(f'error: {r.status_code}')
        return None
    text = r.text.splitlines()


    linefound = None
    for line in text:
        if camid in line and search_string in line:
            linefound = line
            break

    if linefound is None:
        print(f'data for {camid} not available')
        return None


    lastdt = linefound.split(">")[2].split("<")[0]

    try:
        dtval = datetime.datetime.strptime(lastdt, '%Y-%m-%d %H:%M:%S')

    except:
        dtval = None

    return dtval


def getMeteors(camid, search_string,r):


    if r.status_code != 200:
        if r.status_code == 404:
            print(f'data for {camid} not available')
        else:
            print(f'error: {r.status_code}')
        return None
    text = r.text.splitlines()
    linefound = None
    for line in text:
        if camid in line and search_string in line:
            linefound = line
            break

    if linefound is None:
        print(f'data for {camid} not available')
        return None
    meteors = linefound.split("_stack_")[2].split("_meteors")[0]
    return meteors

def getStatus(camid, search_string,m):


    if r.status_code != 200:
        if r.status_code == 404:
            print(f'data for {camid} not available')
        else:
            print(f'error: {r.status_code}')
        return None
    text = r.text.splitlines()
    linefound = None
    for line in text:
        if camid in line:
            linenum = text.index(line)
            for j in range(linenum, linenum+10):
                if search_string in text[j]:
                    linefound = text[j]
                    linenum = j
                    break
            break

    if linefound is None:
        print(f'data for {camid} not available')
        return None
    status = linefound.split("Status: ")[1].split("<")[0]
    return status

if __name__ == '__main__':

    gui = not sys.stdin.isatty()
    if forceTerminal:
        gui = False
    if sys.platform == "win32":
        gui=True
    if len(sys.argv) > 1:
        cfgfile = sys.argv[1]
    else:
        cfgfile = 'rmsmonitor.ini'
    if not os.path.isfile(cfgfile):
        print(f'config file {cfgfile} missing')
        sys.exit(1)
    camids, thresholdlist, reportexception, upload_warning,upload_alert, calibration_warning, calibration_alert, normal = readConfigFile(cfgfile)

    camids_sorted = sorted(camids)
    camstati = []
    lastcamid = "  "
    download_counter = 0
    for camid in camids_sorted:
        camid = camid.strip().upper()
        if camid[0:2] != lastcamid[0:2]:
            baseurl = f'https://globalmeteornetwork.org/weblog/{camid[0:2]}/index.html'
            r = requests.get(baseurl)
            download_counter += 1
        lastuploaddtval = getLast(camid, 'Latest night',r)
        lastcalibratedtval = getLast(camid, 'Latest successful recalibration',r)
        camStatus = getStatus(camid,"Status:",r)
        
        numMeteors = getMeteors(camid,'meteors.jpg',r)
        if gui == False:
            if camStatus == None:
                camStatus = f"Pending"
                camStatus=format(camStatus, ' <17')
            else:
                if camStatus == None:
                    camStatus = format("Pending",' <17')
                camStatus = format(camStatus, ' <17')
            if numMeteors == None:
                numMeteors=f"  None    "
            else:
                numMeteors=f"{numMeteors}    "
                numMeteors=numMeteors.rjust(10)
        camstati.append([camid, lastuploaddtval, lastcalibratedtval, numMeteors, camStatus])
        lastcamid = camid

    if gui:
        root = tk.Tk()
        root.title("Camera Status")
        root.iconbitmap("gmn_mNT_icon.ico")
        # workaround for ttk bug on Python 3.7
        style = ttk.Style()
        actualTheme = style.theme_use()
        style.theme_create("dummy", parent=actualTheme)
        style.theme_use("dummy")
        style.configure("Treeview.Heading", font=("Arial Bold",12))
       
        # create window and table
        root.geometry()
        tree = ttk.Treeview(root, column=("c1", "c2", "c3", "c4", "c5"), show='headings')
        tree.column("#1", anchor=tk.CENTER, width=100)
        tree.heading("#1", text="Cam ID")
        tree.column("#2", anchor=tk.CENTER)
        tree.heading("#2", text="Last Update")
        tree.column("#3", anchor=tk.CENTER)
        tree.heading("#3", text="Last Calibration")
        tree.column("#4", anchor=tk.CENTER, width=100)
        tree.heading("#4", text="# Stacked")
        tree.column("#5", anchor=tk.CENTER)
        tree.heading("#5", text="Status")
        
    # set colour tags
        tree.tag_configure('upload_warning',foreground=upload_warning[0], background=upload_warning[1], font=("Arial Bold",12))
        tree.tag_configure('upload_alert',foreground=upload_alert[0], background=upload_alert[1], font=("Arial Bold",12))
        tree.tag_configure('calibration_warning', foreground=calibration_warning[0], background=calibration_warning[1], font=("Arial Bold",12))
        tree.tag_configure('calibration_alert', foreground=calibration_alert[0], background=calibration_alert[1], font=("Arial Bold",12))
        tree.tag_configure('normal',foreground='black', background='green', font=("Arial Bold",12))
        tree.tag_configure('error',foreground='black', background='white', font=("Arial Bold",12))
    else:
        print(colored("|===============================================================================|", "black", on_color="on_white"))
        print(colored("|Station Last Upload          Last Calibration     # Stacked   Status           |", "black", on_color="on_white"))
        print(colored("|-------------------------------------------------------------------------------|", "black", on_color="on_white"))
        error = ['black','white']
    # get data
    nowdt = datetime.datetime.now(datetime.timezone.utc)

    #if not False:
        

    #camstati.sort()
    #sort camstati by order of input list
    #more pyuthonic ways to achieve this, but this is clear

    camstati_original_sorting = []

    for cam in camids:
        cam = cam.strip()
        for this_cam in camstati:

            if this_cam[0].lower() == cam:
                camstati_original_sorting.append(this_cam)



    for rw in camstati_original_sorting:
        if rw[1] is None or rw[1] == 'None':
            tags='error'
            
            
        else:
            upload_age = nowdt.astimezone(datetime.timezone.utc) - rw[1].astimezone(datetime.timezone.utc)
            calibration_age = nowdt.astimezone(datetime.timezone.utc) - rw[2].astimezone(datetime.timezone.utc)
            #print(age)
            tags='normal'

            if calibration_age > datetime.timedelta(days=int(thresholdlist[0])):
                tags = 'calibration_warning'
            if calibration_age > datetime.timedelta(days=int(thresholdlist[1])):
                tags = 'calibration_alert'

            if upload_age > datetime.timedelta(days=int(thresholdlist[0])):
                tags = 'upload_warning'
            if upload_age > datetime.timedelta(days=int(thresholdlist[1])):
                tags = 'upload_alert'

        if reportexception == "false" or tags != "normal":
            if gui:
                tree.insert('', tk.END, values=rw, tags=(tags))
            else:
                if tags == 'calibration_warning':
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),calibration_warning[0], on_color="on_{}".format(calibration_warning[1])))
                elif tags == 'calibration_alert':
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),calibration_alert[0], on_color="on_{}".format(calibration_alert[1])))
                elif tags == 'upload_warning':
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),upload_warning[0], on_color="on_{}".format(upload_warning[1])))
                elif tags == 'upload_alert':
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),upload_alert[0], on_color="on_{}".format(upload_alert[1])))
                elif tags == 'normal':
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),normal[0], on_color="on_{}".format(normal[1])))
                elif tags == 'error':
                    for x in  range(1,3):
                        rw[x] = "None               "
                    
                    print(colored("|{}  {}  {}  {}  {}|".format(rw[0],rw[1],rw[2],rw[3],rw[4]),error[0], on_color="on_{}".format(error[1])))    
                    
    # display the matrix
    if gui:
        tree.pack(fill="y", expand=True)
        root.geometry()
        root.mainloop()
        
    else:
        print(colored("|===============================================================================|", "black", on_color="on_white"))
