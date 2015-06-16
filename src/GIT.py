"""
@summary: This module executes GIT commands in the command line and puts the
result in an easy access way.

"""

import os
import subprocess
import sys

from HooksConfig import HooksConfig


class GITError(Exception):

    """
    Exception class to represent errors occurred during the execution of GIT
    commands in this module.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class GIT:

    _ = None

    def __init__(self):

        try:

            # Load user messages
            self._ = HooksConfig.get_translations()

        except:

            raise

    @staticmethod
    def nullRevision():
        """
        Returns the null revision string to comparison purposes.

        """

        return "0000000000000000000000000000000000000000"

    @staticmethod
    def isNullRevision(revision):
        """
        Returns true in case that revision matches the null revision

        """

        return (revision == GIT.nullRevision())

    def _parse_diff(self, diff):
        """
        This function parses one string with lines containing the kind of
        modification and the path to a file during one push operation, then
        returns a list of lists which every element is in the form:

            [<File status>, <Path to file>]

        """

        filestatus = []

        lines = diff.splitlines()

        for line in lines:

            filestatus.append(line.split())

        return filestatus

    def _set_env(self, gitpath):
        """
        This function gets current execution environment and sets the necessary
        GIT variables.

        """

        gitenv = os.environ.copy()

        gitenv["GIT_DIR"] = gitpath + ".git"
        gitenv["GIT_WORK_TREE"] = gitpath

        return gitenv

    def get_commit_files(self, old_revision, new_revision):
        """
        This function executes a GIT diff between the old_revision and
        new_revision and returns a list of lists which every element is in the
        form:

            [<File status>, <Path to file>]

        Raises GITError exception when GIT command fails.

        """

        filestatus = []

        try:

            p = subprocess.Popen(["git", "diff", old_revision, new_revision,
                                  "--name-status"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            diff, err = p.communicate()

        except:

            raise GITError("git diff" + self._("command_failed") +
                           str(sys.exc_info()))

        if p.returncode == 0:

            filestatus = self._parse_diff(diff)

        else:

            raise GITError("git diff" + self._("command_failed") + str(err))

        return filestatus

    def get_comments_list(self, old_revision, new_revision):
        """
        This function returns a comments list of all commits between the
        old_revision and the new_revision in chronological order.

        Raises GITError exception when GIT command fails.

        """

        comments = []

        revision_range = old_revision + ".." + new_revision

        try:

            p = subprocess.Popen(["git", "rev-list", revision_range],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            revisions, err = p.communicate()

        except:

            raise GITError("git rev-list" + self._("command_failed") +
                           str(sys.exc_info()))

        if p.returncode == 0:

            for revision in revisions.splitlines():
                """
                Git command to get a revision comment. Original:

                http://git-scm.com/book/en/Customizing-Git-An-Example-Git-Enforced-Policy

                """
                try:

                    p1 = subprocess.Popen(["git", "cat-file", "commit",
                                           revision],
                                          stdout=subprocess.PIPE)
                    p2 = subprocess.Popen(["sed", "1,/^$/d"], stdin=p1.stdout,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
                    # Allow p1 to receive a SIGPIPE if p2 exits
                    p1.stdout.close()
                    comment, err = p2.communicate()

                except:

                    raise GITError("git cat-file" + self._("command_failed") +
                                   str(sys.exc_info()))

                if p.returncode == 0:

                    comments.append(comment.strip())

                else:

                    raise GITError("git cat-file" + self._("command_failed") +
                                   str(err))

            # Comments are reversed in time
            comments.reverse()

        else:

            raise GITError("git rev-list" + self._("command_failed") +
                           str(err))

        return comments

    def get_committer(self, revision):
        """
        Returns the push committer from the cat-file of the given revision.

        Raises GITError exception when GIT command fails.

        """

        committer = ""

        try:

            p = subprocess.Popen(["git", "log", "-1", "--pretty=%cn",
                                  revision],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            committer, err = p.communicate()

        except:

            raise GITError("git log" + self._("command_failed") +
                           str(sys.exc_info()))

        if p.returncode != 0:

            raise GITError("git log" + self._("command_failed") +
                           str(err))

        return committer

    def list_deletions(self, old_revision, new_revision):
        """
        Returns a list of files and folders deleted between the given revisions

        """

        deletions_list = []

        try:

            p = subprocess.Popen(["git", "diff-tree", "-t", old_revision,
                                  new_revision, "--diff-filter=D",
                                  "--name-only"],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            pathlist, err = p.communicate()

        except:

            raise GITError("git diff-tree" + self._("command_failed") +
                           str(sys.exc_info()))

        if p.returncode == 0:

            deletions_list = pathlist.splitlines()

        else:

            raise GITError("git cat-file" + self._("command_failed") +
                           str(err))

        return deletions_list

    def pull(self, gitpath):
        """
        Executes git pull command in the given path

        Raises GITError exception when GIT command fails.

        """

        gitenv = self._set_env(gitpath)

        try:

            p = subprocess.Popen(["git pull"],
                                 shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 env=gitenv)
            out, err = p.communicate()

        except:

            raise GITError(self._("CC_update_failed") + str(sys.exc_info()))

        if p.returncode != 0:

            raise GITError(self._("CC_update_failed") + str(err))
