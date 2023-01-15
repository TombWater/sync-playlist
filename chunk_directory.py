#! /usr/local/bin/python3

import argparse
import itertools
import os
import shutil
import sys

def move(src, dst, dry_run):
  print("move: %s\n   -> %s" % (src, dst))
  if not dry_run:
    shutil.move(src, dst)

def move_dirs(path, chunk_name, chunk, dry_run):
  chunk_root = os.path.join(path, chunk_name)
  if not os.path.isdir(chunk_root):
    print("+dir: %s" % chunk_root)
    if not dry_run:
      os.makedirs(chunk_root)
  for d in chunk:
    src = os.path.join(path, d)
    dst = os.path.join(path, chunk_name, d)
    move(src, dst, dry_run)

def split_directory(path, size, dry_run=False):
  subdirs = sorted(os.listdir(path))
  alpha_groups = itertools.groupby(subdirs, lambda item: item[0].upper())
  alpha_dict = dict()
  for alpha, items in alpha_groups:
    alpha_dict.setdefault(alpha, list()).extend(list(items))

  summary = dict()

  chunk_dict = dict()
  chunk = list()
  alpha_range = list()
  for alpha, items in sorted(alpha_dict.items()):
    combined_len = len(chunk) + len(items)

    if combined_len < size:
      chunk.extend(items)
      alpha_range.append(alpha)
      continue

    # Carry over current items to the next chunk if the chunk
    # is already closer to the target size without them.
    if (combined_len + len(chunk)) / 2 > size:
      carryover = True
    else:
      carryover = False
      chunk.extend(items)
      alpha_range.append(alpha)

    # Close out this chunk and start a new one.
    if carryover or len(chunk) >= size:
      del(alpha_range[1:-1])
      chunk_name = '-'.join(alpha_range)
      summary[chunk_name] = len(chunk)
      move_dirs(path, chunk_name, chunk, dry_run)
      chunk = list()
      alpha_range = list()

    if carryover:
      chunk.extend(items)
      alpha_range.append(alpha)

  # Close out the residual chunk.
  if chunk:
    del(alpha_range[1:-1])
    chunk_name = '-'.join(alpha_range)
    summary[chunk_name] = len(chunk)
    move_dirs(path, chunk_name, chunk, dry_run)

  print("\nsummary:")
  for c, n in sorted(summary.items()):
    print("%s = %d items" % (c, n))

def flatten_directory(path, dry_run=False):
  for d in sorted(os.listdir(path)):
    subdir = os.path.join(path, d)
    if os.path.isdir(subdir):
      for item in os.listdir(subdir):
        src = os.path.join(subdir, item)
        dst = os.path.join(path, item)
        move(src, dst, dry_run)
      print("-del: %s" % subdir)
      if not dry_run:
        os.rmdir(subdir)

def main():
  """Divide a directory's content into chunks of a given size, or move all subdirectories content into the parent"""

  parser = argparse.ArgumentParser(
      description=main.__doc__)
  op_group = parser.add_mutually_exclusive_group(required=True)
  op_group.add_argument("-s", "--split", type=int,
      help="Split a directory into chunks of a given number of children")
  op_group.add_argument("-j", "--join", action="store_true",
      help="Join all subdirectories content into the parent")
  parser.add_argument("-f", "--force", action="store_true",
      help="Really move things rather than just showing what be moved.")
  parser.add_argument("dir")
  args = parser.parse_args()

  if not os.path.isdir(args.dir):
    print("Must be a directory: %s" % args.dir, file=sys.stderr)
    return 1

  dry_run = not args.force
  if args.join:
    flatten_directory(args.dir, dry_run)
  elif args.split > 0:
    split_directory(args.dir, args.split, dry_run)
  else:
    print("Split must be > 0", file=sys.stderr)
    return 1

  if dry_run:
    print("\nPass -f to do it for real")

if __name__ == "__main__":
  main()
