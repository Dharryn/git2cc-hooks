#!/usr/bin/env python

"""
@summary: This module synchronises a GIT repository with one associated
ClearCase view. It must be used as an update hook in the bare repository and
will perform all necessary operations to maintain ClearCase before the
excecution of a push operation takes effect.

"""

import os
import sys
import traceback
import re
import Log

from ClearCase import CCError
from ClearCase import ClearCase
from GIT import GIT
from GIT import GITError
from HooksConfig import ConfigException
from HooksConfig import HooksConfig

def add_file(ccpath):
    """
    Creates all necessary directories in the git_file path. If a problem
    occurs during the execution of this method it will finish the execution of
    the script printing a message to the user.

    """
    cc = ClearCase()
    cc.create_path(os.path.dirname(ccpath))


def modify_file(ccpath, committer, comments):
    """
    This procedure checks out the file in ClearCase.

    """

    cc = ClearCase()
    co_comment = committer + ".GIT push:" + os.linesep
    make_label = False

    for comment in comments:

        m = re.search('@[A-Z_0-9]*',comment)
        if m is not None:
          label = m.group(0)[1:]
          Log.debug("Label found: " + label)
          make_label = True
          co_comment += re.sub('@[A-Z_0-9]*',"",comment) + os.linesep
        else:
          co_comment += comment + os.linesep

    Log.debug ("Making checkout FILE : " + ccpath + "  COMMENT:" + co_comment);

    cc.checkout(ccpath, co_comment)
    if make_label:
          cc.makelabel(ccpath, label)

def process_deletions(cc_view_path, old_revision, new_revision):
    """
    This procedure deletes all necessary files and folders from the file system
    and from ClearCase version.

    """

    git = GIT()
    cc = ClearCase()
    deletion_list = git.list_deletions(old_revision, new_revision)
    co_list = []
    
    for deletion in deletion_list:

        """
        We must check dpath existence every time because it could be deleted in
        a previous iteration. For example:

        deletion_list = ["dir1", "dir1/dir2", "dir1/dir2/file"]

        We could delete the list in reverse but is more efficient delete just
        dir1 folder because we do only one call to CC.

        """

        dpath = cc_view_path + deletion

        if os.path.exists(dpath):

            cc.remove_name(dpath, co_list)

    # Checkout dirs for delete files are check-in.
    #
    cc.checkin_list (co_list)

def process_push(committer, comments, file_status_list, old_revision,
                 new_revision):
    """
    This procedure executes the right ClearCase operation for every file in
    the file_status_list.

    """

    Log.debug("Processing push...")
    Log.debug("committer: " + committer)
    comments_str = '\n'.join(str(c) for c in comments)
    Log.debug("comments: " + comments_str)
    Log.info("Files received to synchronise with ClearCase: ")
    Log.info ("============================================")
    #[<File status>, <Path to file>]
    #M       icas/ccm/configurations/fdp/dep_evatool_fdp.xml
    #D       icas/ccm/load_balancer/Makefile
    for file_status in file_status_list:
        Log.info("  " + file_status[0] + "  " + file_status[1])
    Log.info ("============================================")
    delete_mark = False

    # Path to ClearCase view
    try:

        config = HooksConfig()
        cc_view_path = config.get_view() + os.sep

    except:

        raise

    # Load user messages
    _ = HooksConfig.get_translations()

    # Process every file
    for git_file in file_status_list:

        if git_file[1] != ".gitignore":
            """
            .gitignore file must have no version in CC.
            Note: In the future could be interesting a list of ignored files.

            """

            if git_file[0] == 'A':

                add_file(cc_view_path + git_file[1])

            elif git_file[0] == 'M':

                modify_file(cc_view_path + git_file[1], committer, comments)

            elif git_file[0] == 'D':

                if not delete_mark:

                    delete_mark = True

            else:

                efile = cc_view_path + git_file[1]
                Log.error ("{0} {1} {2}".format(_("update_hook_error"),
                                           _("filestatus_not_supported"),
                                           efile))
                sys.exit(1)

        else:

            ignored_path = cc_view_path + git_file[1]
            Log.error ("{0} : {1} {2}".format(_("NOTICE"),
                                         ignored_path,
                                         _("avoided_file")))

    # Deleted files require a special treatment.
    if delete_mark:

        process_deletions(cc_view_path, old_revision, new_revision)


def do_sync(old_revision, new_revision, git, cc_pusher_user):
    """
    Checks conditions to do a Clearcase sync:
        * Old revision must be not null.
        * New revision must exists (For example, a tag has no new revision.
        * Committer must be different from the cc_pusher_user defined in the
        configuration file
    """

    sync = False

    if not git.isNullRevision(old_revision) and new_revision is not None:

        committer = git.get_committer(new_revision)
        if (committer == cc_pusher_user):
            Log.debug ("Commiter is the Clearcase pusher: " + cc_pusher_user + ", no sync is done, it is a push from Clearcase")
            
        sync = committer != cc_pusher_user

    return sync


def main():
    """
    Retrieves the arguments of the script and performs all necessary operations
    before GIT updates any reference.

    """
    # Get args
    # hook_script = sys.argv[0]
    refs = sys.argv[1]
    old_revision = sys.argv[2]
    new_revision = sys.argv[3] if len(sys.argv) > 3 else None

    Log.debug ("=====================")
    Log.debug ("START NEW PUSH/UPDATE")
    Log.debug ("=====================")
    Log.debug ("refs: " + refs)
    Log.debug ("old_revision: " + old_revision)
    Log.debug ("new_revision: " + new_revision)
    Log.debug ("=====================")

    try:

        # Load user messages and configuration
        _ = HooksConfig.get_translations()
        config = HooksConfig()

    except (ConfigException) as e:

        Log.error("{0} {1}".format(_("update_hook_error"), e.value))
        sys.exit(1)

    """
    ref[0] = "refs"
    ref[1] can be: "heads", "remotes", "tags"
    ref[2] can be: a reference to the head (branch),
                remote or tags respectively
    """
    refs = refs.split('/')

    if refs[1] == "heads" and refs[2] in config.get_sync_branches():

        Log.info("{0}".format(_("branch_sync") + refs[2]))
        Log.debug("This git branch '" + refs[2] +
                  "' is configured as a synchronized Clearcase branch");
        try:

            git = GIT()
            sync = do_sync(old_revision, new_revision, git,
                           config.get_cc_pusher_user())

            if sync:

                # Load push info
                committer = git.get_committer(new_revision)
                comments = git.get_comments_list(old_revision, new_revision)
                file_status_list = git.get_commit_files(old_revision,
                                                        new_revision)

        except (GITError, ConfigException) as e:

            Log.error("{0} {1}".format(_("update_hook_error"), e.value))
            sys.exit(1)

        except:

            Log.error("{0} {1}".format(_("update_hook_unexpected_error"),
                                   sys.exc_info()))
            sys.exit(1)

        if sync:

            try:

                process_push(committer, comments, file_status_list,
                             old_revision, new_revision)

            except (CCError, ConfigException) as e:

                Log.error("{0} {1}".format(_("update_hook_error"), e.value))

                # Try to recover previous state
                cc = ClearCase()
                cc.uncheckout_all()

                sys.exit(1)

            except:

                Log.error("{0} {1}".format(_("update_hook_unexpected_error"),
                                       traceback.format_exc()))

                # Try to recover previous state
                cc = ClearCase()
                cc.uncheckout_all()

                sys.exit(1)

    else:

        if refs[1] == "heads":
            Log.debug("This git branch '" + refs[2] + "' is not configured as a synchronized Clearcase branch");
            Log.error("{0}".format(_("branch_not_sync") + refs[2]))

    Log.debug ("=====================")
    Log.debug ("END NEW PUSH/UPDATE")
    Log.debug ("=====================")

if __name__ == "__main__":

    main()
