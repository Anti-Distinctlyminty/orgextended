
import re
import os
from fnmatch import fnmatch
import sublime
from .abstract import AbstractLinkResolver
import OrgExtended.orgdb as db
from OrgExtended.orgutil.util import *

PATTERN_SETTING = 'resolver.local_file.pattern'
PATTERN_DEFAULT = r'^(file:)?(?P<filepath>.+?)(((::(?P<row>\d+))(::(?P<col>\d+))?)|(::\#(?P<cid>[a-zA-Z0-9!$@%&_-]+))|(::\*(?P<heading>[a-zA-Z0-9!$@%&_-]+))|(::(?P<textmatch>[a-zA-Z0-9!$@%&_-]+)))?\s*$'

FORCE_LOAD_SETTING = 'resolver.local_file.force_into_sublime'
FORCE_LOAD_DEFAULT = ['*.txt', '*.org', '*.py', '*.rb',
                      '*.html', '*.css', '*.js', '*.php', '*.c', 
                      '*.cpp', '*.h', '*.png', '*.jpg', '*.gif', '*.cs']


class Resolver(AbstractLinkResolver):
    def tryMatchHeading(self, filepath, heading):
        fpath = self.view.RelativeTo(filepath).lower()
        fi = db.Get().FindInfo(fpath)
        row = None
        col = None
        if(fi):
            for n in fi.org:
                if not n.is_root() and n.heading == heading:
                    row = n.start_row + 1
                    col = 0
                    if row:
                        filepath += ':%s' % row
                    if col:
                        filepath += ':%s' % col
                    self.view.window().open_file(filepath, sublime.ENCODED_POSITION)
                    return True
        return None

    def tryMatchDirectTarget(self, filepath, val):
        fpath = self.view.RelativeTo(filepath).lower()
        fi = db.Get().FindInfo(fpath)
        if(fi):
            if(fi.org.targets):
                if(val in fi.org.targets):
                    tgt = fi.org.targets[val]
                    row = tgt['row'] + 1
                    col = tgt['col']
                    if row:
                        filepath += ':{0}'.format(row)
                    if col:
                        filepath += ':{0}'.format(col)
                    self.view.window().open_file(filepath, sublime.ENCODED_POSITION)
                    return True
        return None

    def tryMatchNamedObject(self, filepath, val):
        fpath = self.view.RelativeTo(filepath).lower()
        fi = db.Get().FindInfo(fpath)
        if(fi):
            if(fi.org.names):
                if(val in fi.org.names):
                    tgt = fi.org.names[val]
                    row = tgt['row'] + 1
                    col = 0
                    if row:
                        filepath += ':{0}'.format(row)
                    if col:
                        filepath += ':{0}'.format(col)
                    self.view.window().open_file(filepath, sublime.ENCODED_POSITION)
                    return True
        return None

    def __init__(self, view):
        super(Resolver, self).__init__(view)
        self.view = view
        get = self.settings.get
        pattern = get(PATTERN_SETTING, PATTERN_DEFAULT)
        self.regex = re.compile(pattern)
        self.force_load_patterns = get(FORCE_LOAD_SETTING, FORCE_LOAD_DEFAULT)

    def file_is_excluded(self, filepath):
        self.settings      = sublime.load_settings('OrgExtended.sublime-settings')
        basename = os.path.basename(filepath)
        if(isinstance(self.force_load_patterns,str)):
            self.force_load_patterns = self.force_load_patterns.split(',')
        for flpattern in self.force_load_patterns:
            if fnmatch(basename, flpattern):
                #print('found in force_load_patterns: ' + flpattern + " " + basename)
                return False
        folder_exclude_patterns = self.settings.get('folder_exclude_patterns')
        if(folder_exclude_patterns):
            if(isinstance(folder_exclude_patterns,str)):
                folder_exclude_patterns = folder_exclude_patterns.split(',')
            if basename in folder_exclude_patterns:
                #print('found in folder_exclude_patterns')
                return True
        file_exclude_patterns = self.settings.get('file_exclude_patterns')
        if(file_exclude_patterns):
            if(isinstance(file_exclude_patterns,str)):
                file_exclude_patterns = file_exclude_patterns.split(',')
            for pattern in file_exclude_patterns:
                if fnmatch(basename, pattern):
                    #print('found in file_exclude_patterns: ' + str(basename))
                    return True
        return False

    def expand_path(self, filepath):
        if(filepath.startswith("file:")):
            filepath = filepath.replace("file:","", 1)
        filepath = os.path.expandvars(filepath)
        filepath = os.path.expanduser(filepath)

        match = self.regex.match(filepath)
        if match:
            filepath, row, col, cid, heading, textmatch = match.group('filepath'), match.group('row'), match.group('col'), match.group('cid'), match.group('heading'), match.group('textmatch')
        else:
            row = None
            col = None
            cid = None
            heading = None
            textmatch = None

        # The presence of a custom ID means we jump
        # using a different means
        if(cid):
            #print("File Found ID trying to jump to: " + cid)
            db.Get().JumpToAnyId(cid)
            return True
        if(heading):
            #print("Found Heading trying to jump to: " + heading)
            fpath = self.view.RelativeTo(filepath).lower()
            fi = db.Get().FindInfo(fpath)
            if(fi):
                for n in fi.org:
                    if not n.is_root() and n.heading == heading:
                        row = n.start_row + 1
                        col = 0
                        break
        if(textmatch):
            #print("Found Textmatch trying to jump to: " + textmatch)
            fpath = self.view.RelativeTo(filepath).lower()
            if(self.tryMatchDirectTarget(fpath, textmatch)):
                return True
            if(self.tryMatchNamedObject(fpath, textmatch)):
                return True
            if(self.tryMatchHeading(fpath, textmatch)):
                return True
        #print("NO TEXT MATCH")
        drive, filepath = os.path.splitdrive(filepath)
        if not filepath.startswith('/') and not filepath.startswith('\\'):  # If filepath is relative...
            cwd = os.path.dirname(self.view.file_name())
            testfile = os.path.join(cwd, filepath)
            if os.path.exists(testfile):  # See if it exists here...
                filepath = testfile

        filepath = ''.join([drive, filepath]) if drive else filepath
        if not self.file_is_excluded(filepath):
            if row:
                filepath += ':%s' % row
            if col:
                filepath += ':%s' % col
            #print("Opening file: " + filepath)
            self.view.window().open_file(filepath, sublime.ENCODED_POSITION)
            return True
        else:
            #print('file_is_excluded: ' + filepath)
            return filepath

        return None

    def replace(self, content):
        content = self.expand_path(content)
        return content

    def execute(self, content):
        if content is not True:
            #print('normal open')
            return super(Resolver, self).execute(content)
