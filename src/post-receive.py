#!/usr/bin/env python

"""
@summary: This module synchronises a GIT repository with one associated
ClearCase view. It must be used as an post-receive hook in the bare repository
and will perform all necessary operations to maintain ClearCase after the
execution of a push operation takes effect.

"""

import os
import traceback
import sys

from ClearCase import CCError
from ClearCase import ClearCase
from GIT import GIT
from GIT import GITError
from HooksConfig import HooksConfig
from HooksConfig import ConfigException


def add_file (ccpath):
  """
  Adds one file to ClearCase view.

  """

  cc = ClearCase()
  cc.create_file(ccpath)


def modify_file(ccpath):
  """
  Checks in one file in the ClearCase view.

  """

  cc = ClearCase()
  cc.checkin(ccpath)


def checkin_all():
  """
  Checks in every file and folder found checked out in the view.

  """

  cc = ClearCase()
  cc.checkin_all()


def process_push(cc_view_path, file_status_list):
  """
  This procedure executes the right ClearCase operation for every file in the
  file_status_list.

  """

  # Load user messages
  _ = HooksConfig.get_translations()

  for git_file in file_status_list:

    if git_file[1] != ".gitignore":
      """
      .gitignore file must have no version in CC.
      Note: In the future could be interesting a list of ignored files.

      """

      if git_file[0] == 'A':

        add_file(cc_view_path + git_file[1])

      elif git_file[0] == 'M':

        modify_file(cc_view_path + git_file[1])

      # Deleted files do not need post_receive operations.


def do_sync(old_revision, new_revision, git, config, refs):
  """
  Checks conditions to do a Clearcase sync:
    * Reference must be a HEAD
    * Old revision must be not null.
    * New revision must exists (For example, a tag has no new revision.
    * Committer must be different from the cc_pusher_user defined in the
      configuration file
    * Branch (ref[2]) must be in the sync branches list

  """

  sync = False

  if refs[1] == "heads" and not git.isNullRevision(old_revision) and \
  new_revision is not None and  refs[2] is not None and \
  refs[2] in config.get_sync_branches():

    committer = git.get_commiter(new_revision)

    sync = committer != config.get_cc_pusher_user()

  return sync


def get_standard_input():
  """
  Returns the old and new revisions from the standard input because this hook
  does not receive parameters from Git.

  """

  line = sys.stdin.readline()
  params = line.split()

  if len(params) > 1:

    return params[0], params [1], params[2]

  else:

    return params[0], None, None


def main():
  """
  Retrieves the old and new revisions from the standard input and performs
  all necessary operations to maintain ClearCase after GIT updates its
  references.

  """

  # Load user messages
  _ = HooksConfig.get_translations()

  try:

    git = GIT()
    config = HooksConfig()

    old_revision, new_revision, refs = get_standard_input()

    """
    ref[0] = "refs"
    ref[1] can be: "heads", "remotes", "tags"
    ref[2] can be: a reference to the head (branch), remote or tags respectively
    
    """
    refs = refs.split('/')

  except (GITError, ConfigException) as e:

    print _("post-receive hook error:"), e.value
    sys.exit(1)

  except:

    print _("post-receive hook unexpected error:"), sys.exc_info()
    sys.exit(1)

  if do_sync(old_revision, new_revision, git, config, refs):

    try:

      # Path to ClearCase view
      cc_view_path = config.get_view() + os.sep

      # Update ClearCase view and recover file status list using GIT
      git.pull(cc_view_path)
      file_status_list = git.get_commit_files(old_revision, new_revision)

      # Process every file
      process_push(cc_view_path, file_status_list)

      # Check in every remaining check out
      checkin_all()

    except (GITError, CCError, ConfigException) as e:

      print _("post-receive hook error:"), e.value
      sys.exit(1)

    except:

      print _("post-receive hook unexpected error:"), traceback.format_exc()
      sys.exit(1)


if __name__ == "__main__":

  main()
