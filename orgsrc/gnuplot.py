import sublime
import sublime_plugin
import sys
import io
import re
import logging
import subprocess, os
import threading, time, signal
from shutil import move
import types
import OrgExtended.orgtableformula as fml
import OrgExtended.orgparse.date as odate
import traceback
import datetime

# GNU Plot Babel Mode

def GetTerminalFromOutputFile(filename):
    out = ""
    if(filename):
        ff,ext = os.path.splitext(filename)
        if(ext == '.png'):
            out += 'set term png \n'
        if(ext == '.jpg' or ext == '.jpeg'):
            out += 'set term jpeg \n'
        if(ext == '.gif'):
            out += 'set term gif \n'
        if(ext == '.html'):
            out += 'set term canvas \n'
        if(ext == '.txt'):
            out += 'set term dumb \n'
        if(ext == '.svg'):
            out += 'set term svg \n'
        if(ext == '.ps'):
            out += 'set term postscript \n'
    return out


def FormatDateTime(now):
    if(isinstance(now,datetime.datetime)):
        return now.strftime("%Y-%m-%d %H:%M")  
    else:
        return now.strftime("%Y-%m-%d")  

def FormatText(txt):
    txt = txt.strip()
    try:
        rc = odate.OrgDate.list_from_str(txt)
        if(len(rc) > 0):
            return FormatDateTime(rc[0].start).strip()
    except:
        #print("FAILED FORMAT: " + str(traceback.format_exc()))
        pass
    if(" " in txt):
        txt = "\"" + txt + "\""
    return txt

def PreProcessSourceFile(cmd):
    filename = cmd.params.Get('file',None)
    var = cmd.params.Get('var',None)
    if(var):
        out = ""
        for k in var:
            v = var[k]
            if(isinstance(v,fml.TableDef)):
                out += "$" + str(k) + " << EOD\n"
                for r in v.ForEachRow():
                    first = True
                    for c in v.ForEachCol():
                        txt = v.GetCellText(r,c)
                        out += ('\t' if not first else "") + FormatText(txt)
                        first = False
                    out += '\n'
                out += "EOD\n"
        cmd.source = out + cmd.source
    if(filename):
        out = GetTerminalFromOutputFile(filename)
        cmd.output = filename
        out += "set output \"" + filename.replace("\\","\\\\") + "\"\n"
        # Append the source output information
        cmd.source = out + cmd.source

def Extension(cmd):
    return ".gplt"

# Actually do the work, return an array of output.
def Execute(cmd, sets):
    plotcmd = sets.Get("gnuplot",r"C:\Program Files\gnuplot\bin\gnuplot.exe")
    commandLine = [plotcmd, "-c", cmd.filename]
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    except:
        startupinfo = None
    # cwd=working_dir, env=my_env,
    cwd = os.path.join(sublime.packages_path(),"User") 
    popen = subprocess.Popen(commandLine, universal_newlines=True, cwd=cwd, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (o,e) = popen.communicate()
    
    #outpath     = os.path.dirname(cmd.filename)
    sourcepath = os.path.dirname(cmd.sourcefile)
    relpath = os.path.join(cwd,cmd.output)
    if(os.path.exists(relpath)):
        destFile    = os.path.join(sourcepath,cmd.output)
        if(destFile != relpath):
            move(relpath, destFile)

    return o.split('\n') + e.split('\n')


# Run after results are in the buffer. We can do whatever
# Is needed to the buffer post execute here.
def PostExecute(cmd):
    pass
