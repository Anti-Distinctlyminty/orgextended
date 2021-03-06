
import sublime
import sublime_plugin
import sys
import io
import re
import logging
import subprocess, os
import threading, time, signal
from shutil import copyfile
import OrgExtended.asettings as sets

# Python Babel Mode
def Extension(cmd):
	return ".pu"

def WrapStart(cmd):
	return "@startuml"

def WrapEnd(cmd):
	return "@enduml"

# Actually do the work, return an array of output.
def Execute(cmd,sets):
	jarfile = sets.Get("plantuml",None)
	if(jarfile == None):
		print("ERROR: cannot find plantuml jar file. Please setup the plantuml key in your settings file")
		return ["ERROR - missing plantuml.jar file"]
	cmd.output = cmd.params.Get('file',"diagram.png")
	outpath    = os.path.dirname(cmd.filename)
	sourcepath = os.path.dirname(cmd.sourcefile)
	commandLine = [r"java", "-jar", jarfile, cmd.filename]
	try:
		startupinfo = subprocess.STARTUPINFO()
		startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	except:
		startupinfo = None
	cwd = os.path.join(sublime.packages_path(),"User") 
	popen = subprocess.Popen(commandLine, universal_newlines=True, cwd=cwd, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

	(o,e) = popen.communicate()
	
	convertFile = os.path.join(outpath,os.path.splitext(os.path.basename(cmd.filename))[0] + ".png")
	destFile    = os.path.normpath(os.path.join(sourcepath,cmd.output))
	os.makedirs(os.path.dirname(destFile), exist_ok=True)
	copyfile(convertFile, destFile)
	return o.split('\n') + e.split('\n')

# Run after results are in the buffer. We can do whatever
# Is needed to the buffer post execute here.
def PostExecute(cmd):
	pass

# Create one of these and return true if we should show images after a execution.
def GeneratesImages(cmd):
	return True