#! /usr/bin/python
# Copyright 2008, Tom Bridgwater


import os
import sys
import re
import urllib
import UserDict
import xml.sax.handler

class PListHandler(xml.sax.handler.ContentHandler):
  """A SAX handler to transform an Apple plist into nested lists and dicts"""
  def __init__(self):
    self.data = None
    self.scope = [ ]
    self.tag = None
    self.key = None
    self.value = None

  def startElement(self, name, attrs):
    if name == 'dict':
      new_dict = { }
      # The first dict is unnamed and becomes the top-level data,
      # subsequent dicts are added to the current scope.
      if (self.data is None):
        self.data = new_dict
      else:
        self.addValue(new_dict)
      self.scope.append(new_dict)
    elif name == 'array':
      new_array = [ ]
      self.addValue(new_array)
      self.scope.append(new_array)
    elif name in ( 'key', 'integer', 'string', 'date', 'true', 'false' ):
      self.tag = name
      self.value = ''

  def endElement(self, name):
    if name in ('dict', 'array'):
      self.scope.pop()
    elif name == 'key':
      self.key = self.value
    elif name in ( 'true', 'false' ):
      self.addValue(name)
    elif self.tag:
      self.addValue(self.value)
    self.tag = None
    self.value = None

  def characters(self, ch):
    if self.tag:
      self.value += ch

  def addValue(self, value):
    scope = self.scope[-1]
    if type(scope) is dict:
      scope[self.key] = value
    else:
      scope.append(value)


class iTunesLibrary(object):
  def __init__(self, music_library_xml_path=None):
    parser = self.make_xml_parser()
    if music_library_xml_path is None:
      #music_library_xml_path = "%s/Music/iTunes/iTunes Library.xml" % os.getenv('HOME') 
      music_library_xml_path = "%s/Music/Music/Library.xml" % os.getenv('HOME') 
    print >>sys.stderr, "Reading iTunes data from %s" % music_library_xml_path
    self.music_library_xml_path = music_library_xml_path
    handler = PListHandler()
    parser.setContentHandler(handler)
    xml_file = open(self.music_library_xml_path)
    parser.parse(xml_file)
    self.music_folder = file_string(handler.data['Music Folder'])
    self.tracks = iTunesTrackDict(handler.data['Tracks'])
    self.playlists = dict((pl['Name'], iTunesPlaylist(pl, self.tracks))
                          for pl in handler.data['Playlists'])

  def make_xml_parser(self):
    """
    Make and patch a SAX parser so it doesn't fetch the DTD from Apple, which
    causes excess network traffic and fails with an IOError when the network
    isn't available.  http://bugs.python.org/issue2124
    """
    parser = xml.sax.make_parser()
    def _patched_reset():
      parser._orig_reset()
      parser._parser.SetParamEntityParsing(
          xml.parsers.expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser._orig_reset = parser.reset
    parser.reset = _patched_reset
    return parser


class iTunesTrackDict(UserDict.UserDict):
  """
  A wrapper for the dictionary of tracks in an iTunes library. Lazilly
  synthesizes the "File Path" value for tracks that are stored as local files,
  or makes it None for other tracks.
  """
  file_prefix_re = re.compile('^file://(localhost)?')

  def __init__(self, tracks):
    UserDict.UserDict.__init__(self)
    self.data = tracks

  def __getitem__(self, id):
    track = self.data[id]
    if 'File Path' not in track:
      file_path = None
      if 'Location' in track:
        file_path = file_string(track['Location'])
        #location = str(track['Location'])
        #location = urllib.unquote(location).decode('utf-8')
        #(location, count) = self.file_prefix_re.subn('', location)
        #if count:
        #  file_path = location.encode('utf-8')
      track['File Path'] = file_path
    return track


FILE_PREFIX_RE = re.compile('^file://(localhost)?')
def file_string(location):
  location = urllib.unquote(str(location)).decode('utf-8')
  (location, count) = FILE_PREFIX_RE.subn('', location)
  return location.encode('utf-8') if count else None


class iTunesPlaylist(UserDict.UserDict):
  """
  A wrapper for a playlist dictionary in an iTunes library. Provides a
  getitem method for random access to and iteration over the tracks.
  """
  def __init__(self, playlist, library_tracks):
    UserDict.UserDict.__init__(self)
    self.data = playlist
    self._library_tracks = library_tracks

  def __getitem__(self, index):
    if 'Playlist Items' not in self.data: raise IndexError
    id = self.data['Playlist Items'][index]['Track ID']
    return self._library_tracks[id]

  def __len__(self):
    items = self.data.get('Playlist Items')
    return len(items) if items else 0


def main(argv=None):
  """Display the file paths to the tracks in an iTunes playlist.
     "Library" is used if no playlist specified.
Usage:
    playlist-files.py  ["Playlist Name"] ["/path/to/iTunes Music Library.xml"]

    Use '?' for playlist name to show the names of all playlists.
  """
  playlist_name = "Library"
  xml_path = None
  if argv is None:
    argv = sys.argv
  argv.pop(0) # remove program name
  if argv:
    playlist_name = argv.pop(0)
  if argv:
    xml_path = argv.pop(0)

  itunes = iTunesLibrary(xml_path)

  if playlist_name == '?':
    print 'Music Folder: %s' % itunes.music_folder
    print '[%d playlists]' % len(itunes.playlists)
    for playlist_name, playlist in sorted(itunes.playlists.items()):
      print '%s (%d tracks)' % (playlist_name, len(playlist))
    return 0

  try:
    playlist = itunes.playlists[playlist_name]
  except KeyError:
    print >>sys.stderr, "[Error] No such playlist: '%s'" % playlist_name
    return 1

  for track in playlist:
    file_path = track['File Path']
    if file_path:
      print file_path


if __name__ == "__main__":
  sys.exit(main())

