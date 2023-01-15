#! /usr/bin/python

import argparse
import itertools
import os
import re
import sys
from subprocess import call

import chunk_directory
from clean_filenames import FilenameCleaner
from itunes_playlist import iTunesLibrary

TMP_DIR = "/tmp/playlist-files"
INTRO_MP3 = "%s/Music/Ringtones/+A.mp3" % os.getenv("HOME")

def main(argv=None):
  """Collect a symlink farm out of an iTunes playlist, and rsync it to a destination."""

  my_dir = os.path.dirname(sys.argv[0])

  parser = argparse.ArgumentParser(
      description=main.__doc__)
  parser.add_argument("-p", "--playlist",
      help="Name of the iTunes playlist to copy. "
           "If not specified, the last collected symlinks run will be written")
  parser.add_argument("-d", "--dest_dir",
      help="Path to the directory where the songs will be written. "
           "If not specified, symlinks will be collected without copying them.")
  parser.add_argument("-l", "--library_xml",
      help="Path to \"iTunes Library.xml\"")
  parser.add_argument("-t", "--temp_dir",
      default=TMP_DIR,
      help="Path to the directory where symlinks will be collected.")
  parser.add_argument("-f", "--force", action="store_true",
      help="Really sync rather than just showing what rsync would do.")
  args = parser.parse_args()

  if not args.playlist and not args.dest_dir:
    print >>sys.stderr, "Specify either --playlist or --dest_dir or both."
    return 1

  if args.dest_dir and not os.path.isdir(args.dest_dir):
    print >>sys.stderr, "Destination must be a directory: %s" % args.dest_dir
    return 1

  if args.playlist:
    delete_directory_contents(args.temp_dir)
    link_intro(args.temp_dir)
    print >>sys.stderr, "Calculating symlinks"
    symlink_tree = compute_symlink_paths(args.playlist, my_dir, args.library_xml)

    # artists = symlink_tree.get("Artists", dict())
    # if artists:
    #   symlink_tree["Artists"] = split_tree(artists)
    # compilations = symlink_tree.get("Compilations", dict())
    # if compilations:
    #   symlink_tree["Compilations"] = split_tree(compilations)

    make_symlinks(args.temp_dir, symlink_tree)

  dry_run = not args.force
  if args.dest_dir:
    sync_files(args.temp_dir, args.dest_dir, dry_run)
    if dry_run:
      print "\nPass -f to do it for real"

def compute_symlink_paths(playlist_name, my_dir, library_xml=None):
  cleaner = FilenameCleaner(ccdict_path=my_dir)
  itunes = iTunesLibrary(library_xml)
  playlist = itunes.playlists[playlist_name]
  #path_prefix_re = re.compile(".*/iTunes Music/")
  path_prefix = itunes.music_folder
  compilations_re = re.compile("Compilations/")
  symlink_tree = {}
  for track in playlist:
    file_path = track["File Path"]
    if file_path:
      file_path = file_path.decode("utf-8")
      #relative_path = path_prefix_re.sub("", file_path)
      if file_path.startswith(path_prefix):
        relative_path = file_path[len(path_prefix):]
      else:
        relative_path = file_path
      relative_path = cleaner.clean_name(relative_path)
      if track.get("Genre", "").lower() == "classical":
        relative_path = "Classical/%s" % relative_path
      elif not track.get("Compilation"):
      #if not compilations_re.match(relative_path):
        relative_path = "Artists/%s" % relative_path

      # Split the relative path into a tree of dictionaries
      parent = symlink_tree
      pieces = relative_path.split('/')
      while pieces:
        piece = pieces.pop(0)
        # The leaf of the tree is a string that is the file path
        child = dict() if pieces else file_path
        parent = parent.setdefault(piece, child)

  return symlink_tree

def split_tree(tree, size=50):
  # First make fine-graned alpha groups
  alpha_tree = dict()
  alpha_groups = itertools.groupby(tree.iteritems(), lambda item: item[0][0].upper())
  for alpha, items in alpha_groups:
    alpha_tree.setdefault(alpha, dict()).update(dict(items))

  # Combine consecutive alpha groups into chunks of the desired size.
  chunk_tree = dict()
  chunk = dict()
  alpha_range = list()
  alpha_keys = sorted(alpha_tree.keys())
  while alpha_keys:
    alpha = alpha_keys.pop(0)
    alpha_range.append(alpha)
    chunk.update(alpha_tree[alpha])
    if len(chunk) >= size:
      del(alpha_range[1:-1])
      chunk_key = '-'.join(alpha_range)
      chunk_tree[chunk_key] = chunk
      chunk = dict()
      alpha_range = list()
  if chunk:
    del(alpha_range[1:-1])
    chunk_key = '-'.join(alpha_range)
    chunk_tree[chunk_key] = chunk

  return chunk_tree

def print_tree(tree, level=0):
  if type(tree) is not dict:
    print "--> %s%s" % ("  " * level, tree)
  else:
    for n, (k, v) in enumerate(sorted(tree.iteritems())):
      print "%02d. %s%s" % (n + 1, "  " * level, k)
      print_tree(v, level+1)

def make_symlinks(top_dir, symlink_tree):
  if not os.path.isdir(top_dir):
    os.makedirs(top_dir)
  for item, child in sorted(symlink_tree.iteritems()):
    item_path = "%s/%s" % (top_dir, item)
    if type(child) is dict:
      make_symlinks(item_path, child)
    else:
      print "%s\n->%s" % (child.encode('utf-8'), item_path.encode('utf-8'))
      os.symlink(child, item_path)

def delete_directory_contents(top):
  print >>sys.stderr, "Clearing staging directory %s" % top
  for root, dirs, files in os.walk(top, topdown=False):
    for name in files:
      os.remove(os.path.join(root, name))
    for name in dirs:
      os.rmdir(os.path.join(root, name))
  if not os.path.isdir(top):
    os.makedirs(top)

def link_intro(top_dir):
  if not os.path.isfile(INTRO_MP3):
    print >>sys.stderr, "Not linking missing intro file %s" % INTRO_MP3
    return
  print >>sys.stderr, "Linking intro file %s" % INTRO_MP3
  dest = os.path.join(top_dir, os.path.basename(INTRO_MP3))
  if os.path.isfile(dest):
    os.remove(dest)
  os.symlink(INTRO_MP3, dest)

def sync_files(src_dir, dest_dir, dry_run):
  rsync = [
    "/usr/bin/rsync",
    "--verbose",
    "--itemize-changes",
    "--recursive",
    "--copy-links",
    "--stats",
    "--size-only",
    "--delete",
    "--exclude='.*'",
    src_dir + "/",
    dest_dir + "/",
  ]
  if dry_run:
    print >>sys.stderr, "Would sync to %s" % dest_dir
    rsync.insert(1, "-n")
  else:
    print >>sys.stderr, "Syncing to %s" % dest_dir
  call(rsync)

if __name__ == "__main__":
  sys.exit(main())
