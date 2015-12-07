#!/usr/bin/env python

"""
@summary: This module synchronises a GIT repository with one associated
ClearCase view. It must be used as an post-receive hook in the bare repository
and will perform all necessary operations to maintain ClearCase after the
execution of a push operation takes effect.

"""

import os
import sys
import traceback
import Log

from ClearCase import CCError
from ClearCase import ClearCase
from GIT import GIT
from GIT import GITError
from HooksConfig import ConfigException
from HooksConfig import HooksConfig


def add_file(ccpath, labels, list_co):
    """
    Adds one file to ClearCase view.

    """

    cc = ClearCase()

    cc.create_file(ccpath, labels, list_co)


def checkin_file(ccpath, labels):
    """
    Checks in one file in the ClearCase view.

    """

    cc = ClearCase()
    cc.checkin(ccpath, labels)


def checkin_all(cc_view_path):
    """
    Checks in every file and folder found checked out in the view.

    """
    git = GIT()
    labels = git.last_commit_labels(cc_view_path)
    cc = ClearCase()
    cc.checkin_all(labels)

def log_received_files_and_labels (labels, file_status_list):
    """
    This procedure will log using the log package all the received files and
    labels.

    """
    list_of_files = '\n'.join(str(p) for p in file_status_list)
    
    Log.debug ("Post-receive hook Received Git Files")
    Log.debug ("====================================")
    Log.debug (list_of_files)
    
    Log.debug ("Labels received to synchronise with ClearCase")
    Log.debug ("============================================")
    Log.debug (labels)
    
def process_push(cc_view_path, file_status_list):
    """
    This procedure executes the right ClearCase operation for every file in the
    file_status_list.

    """

    # Load user messages
    HooksConfig.get_translations()

    git = GIT()
    
    labels = git.last_commit_labels(cc_view_path)

    list_co = []
    
    log_received_files_and_labels (labels, file_status_list)
    
    for git_file in file_status_list:

        if git_file[1] != ".gitignore":
            """
            .gitignore file must have no version in CC.
            Note: In the future could be interesting a list of ignored files.

            """

            if git_file[0] == 'A':

                add_file(cc_view_path + git_file[1], labels, list_co)

            elif git_file[0] == 'M':

                checkin_file(cc_view_path + git_file[1], labels)

            # Deleted files do not need post_receive operations.

    # Checkout dirs needed to Add files checked-in.
    cc = ClearCase()
    cc.checkin_list (list_co, labels)
    
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

    if (refs[1] == "heads" and
            not git.isNullRevision(old_revision) and
            new_revision is not None and
            refs[2] is not None and
            refs[2] in config.get_sync_branches()):

        committer = git.get_committer(new_revision)

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

        return params[0], params[1], params[2]

    else:

        return params[0], None, None


def main():
    """
    Retrieves the old and new revisions from the standard input and performs
    all necessary operations to maintain ClearCase after GIT updates its
    references.

    """
    Log.debug ("START POST-RECEIVE")
    Log.debug ("==================")
    
    # Load user messages
    _ = HooksConfig.get_translations()

    try:

        git = GIT()
        config = HooksConfig()

        old_revision, new_revision, refs = get_standard_input()

        """
        ref[0] = "refs"
        ref[1] can be: "heads", "remotes", "tags"
        ref[2] can be: a reference to the head (branch),
                       remote or tags respectively
        """
        refs = refs.split('/')

    except (GITError, ConfigException) as e:
        Log.error("{0} {1}".format(_("post-receive hook error:"), e.value))
        Log.error("Please review checkout files!!!!")
        sys.exit(1)

    except:
        Log.error("{0} {1}".format(_("post-receive hook unexpected error:"),
                               sys.exc_info()))
        Log.error("Please review checkout files!!!!")
        sys.exit(1)

    if do_sync(old_revision, new_revision, git, config, refs):

        try:

            # Path to ClearCase view
            cc_view_path = config.get_view() + os.sep

            # Update ClearCase view and recover file status list using GIT
            Log.debug("git pull from " + cc_view_path + "...")
            git.pull(cc_view_path)
            Log.debug("git pull from " + cc_view_path + "...OK")
            file_status_list = git.get_commit_files(old_revision, new_revision)

            # Process every file
            process_push(cc_view_path, file_status_list)

            # Check in every remaining check out
            #checkin_all (cc_view_path)

        except (GITError, CCError, ConfigException) as e:
            Log.error("{0} {1}".format(_("post-receive hook error:"), e.value))
            Log.error("Please review checkout files!!!!")
            sys.exit(1)

        except:
            Log.error("{0} {1}".format(_("post-receive hook unexpected error:"),
                                   traceback.format_exc(), sys.exc_info()[0]))
            Log.error("Please review checkout files!!!!")
            sys.exit(1)

    Log.debug ("END POST-RECEIVE")

if __name__ == "__main__":

    main()
