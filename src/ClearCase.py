"""
@summary: This module executes ClearCase commands in the command line and gets
the result or the possible exceptions.

@note: Use of subprocess.Popen method to get the standard error output can be
replaced from Python version 2.7 by subprocess.check_output.
For further information:
http://docs.python.org/2/library/subprocess.html

"""

import os
import subprocess
import sys

from HooksConfig import HooksConfig


class CCError(Exception):

    """
    Exception class to represent errors occurred during the execution of
    ClearCase commands in this module.

    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class ClearCase:

    _config = None
    _ = None

    def __init__(self):
        """
        This constructor gets the current Hooks configuration and user messages.

        """

        try:

            # Load user messages
            self._ = HooksConfig.get_translations()

            # Get configuration
            self._config = HooksConfig()

        except:

            raise

    def is_versioned(self, ccpath):
        """
        Checks if the received file or folder is under ClearCase

        """

        result = False

        if os.path.exists(ccpath):

            try:
                p = subprocess.Popen([self._config.get_cleartool_path(), "ls",
                                    "-vob_only", ccpath],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

                out, err = p.communicate()

                if p.returncode == 0:

                    result = not (out is None or out == "")

            except:

                result = False

        return result

    def is_checkout(self, ccpath):
        """
        Checks if the    file or folder is in Checkout state

        """

        result = False

        p = subprocess.Popen([self._config.get_cleartool_path(), "lsco",
                            "-s", "-d", "-cvi", ccpath],
                            stdout=subprocess.PIPE)
        out = p.communicate()

        if p.returncode == 0 and out[0] != "":

            result = out[0].rstrip('\r\n') == ccpath

        return result

    def checkout(self, ccpath, comment, addVersion=False):
        """
        Executes the check out of the given file with the specified comment and
        optionally a version

        Raises CCError exception when the command fails.

        """

        # File/Folder must exists and have version in ClearCase
        if not addVersion and not self.is_versioned(ccpath):

            raise CCError(ccpath + self._("not_in_CC"))

        # Files/Folders can not be already checked out
        if self.is_checkout(ccpath):

            raise CCError(ccpath + self._("already_co"))

        # Add quotation marks to the comment
        cc_comment = '"' + comment + '"'

        if addVersion:

            command = [self._config.get_cleartool_path(), "co", "-c",
                    cc_comment, "-ver", ccpath]
        else:

            command = [self._config.get_cleartool_path(), "co", "-c",
                    cc_comment, ccpath]

        try:
            p = subprocess.Popen(command,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            out, err = p.communicate()

        except:
            raise CCError(self._("co") + " " + ccpath +
                        self._("command_failed") +
                        str(sys.exc_info()))

        if p.returncode != 0:

            raise CCError(self._("co") + " " + ccpath +
                        self._("command_failed") +
                        str(err))

    def uncheckout(self, ccpath):
        """
        Cancels a checkout of an element.

        Raises CCError exception when the command fails.

        """

        p = subprocess.Popen([self._config.get_cleartool_path(), "unco", "-rm",
                            ccpath])
        p.communicate()

        if p.returncode != 0:

            raise CCError(ccpath + " ct unco -rm" + self._("command_failed"))

    def checkin(self, ccpath):
        """
        Executes the check in of the given file or directory

        Raises CCError exception when the command fails.

        """

        if not os.path.exists(ccpath):

            raise CCError(ccpath + self._("not_in_CC"))

        if not self.is_checkout(ccpath):

            raise CCError(ccpath + self._("ci_not_co"))

        try:
            p = subprocess.Popen([self._config.get_cleartool_path(),
                                "ci", "-nc", ccpath],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)

            out, err = p.communicate()

        except:

            raise CCError(self._("ci") + " " + ccpath +
                        self._("command_failed") +
                        str(sys.exc_info()))

        if p.returncode != 0:

            raise CCError(self._("ci") + " " + ccpath +
                        self._("command_failed") +
                        str(sys.exc_info()))

    def create_dir(self, ccpath):
        """
        Creates a new directory in ClearCase.

        Raises CCError exception when the command fails.

        """

        if not os.path.isdir(ccpath):

            parent = ccpath

            # Remove last / when necessary
            if parent[len(parent) - 1] == os.sep:

                parent = parent[:-1]

            # Get parent directory
            parent = os.path.dirname(parent)

            if not os.path.isdir(parent):

                raise CCError(parent + self._("not_in_CC"))

            if not self.is_checkout(parent):
                # Check out parent directory
                self.checkout(parent, self._("CC_dir_modification_comment"))

            try:

                # Create new directory
                p = subprocess.Popen([self._config.get_cleartool_path(),
                                    "mkdir", "-c", self._("new_CC_folder"),
                                    ccpath],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
                out, err = p.communicate()

            except:

                raise CCError(ccpath + self._("creation_failed") +
                        str(sys.exc_info()))

            if p.returncode != 0:

                raise CCError(ccpath + self._("creation_failed") + str(err))

        else:

            raise CCError(ccpath + self._("already_in_CC"))

    def create_path(self, ccpath):
        """
        Creates a complete route of directories matching the given path.

        Raises CCError exception when the creation of any directory fails.

        """

        # Split path in directories
        dirs = ccpath.split(os.sep)

        # Because ccpath starts with os.sep the first element in dirs
        # will be the "" and must be deleted
        del dirs[0]

        current = os.sep

        for dir_name in dirs:

            current += dir_name

            # Create directory only if it did not exist previously
            if not os.path.isdir(current):

                try:

                    self.create_dir(current)

                except:

                    raise

            current += os.sep

    def create_file(self, ccpath):
        """
        Adds a new file to ClearCase. The file must exists previously.

        Raises CCError exception when a failure is detected.

        """

        if not os.path.isfile(ccpath):

            raise CCError(ccpath + self._("file_not_exists"))

      # Preserve current keep file if it exists
        if os.path.isfile(ccpath + ".keep"):
            os.rename(ccpath + ".keep", ccpath + ".keep.old")

        try:

            # Checkout file folder
            self.checkout(os.path.dirname(ccpath), self._("new_file"))

          # Open the file avoids anyone changes it during the check out
            with open(ccpath) as f:
                p = subprocess.Popen([self._config.get_cleartool_path(),
                                    "mkelem", "-nc", "-nco", ccpath],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
                out, err = p.communicate()
                f.close()
            if p.returncode == 0:
                """
                Previous operation puts an empty new file in the main
                ClearCase branch leaving the actual file as ccpath.keep
                We must add the content to our branch performing co then
                ci of the keep file.
                """
                self.checkout(ccpath + "@@/main/LATEST",
                        self._("new_file"), True)
                os.rename(ccpath + ".keep", ccpath)
                self.checkin(ccpath)
            else:
                raise CCError(ccpath + self._("creation_failed") + str(err))

        except IOError:

            raise CCError(ccpath + self._("file_not_exists"))

        except CCError:
            raise

        except:
            raise CCError(ccpath + self._("creation_failed") +
                        str(sys.exc_info()))

    def list_checkouts(self):
        """
        Lists every file and folder checked out in the current view.

        """

        colist = []

        for i in os.listdir(self._config.get_view()):

            current_path = self._config.get_view() + os.sep + i

            if os.path.isdir(current_path) and self.is_versioned(current_path):

                # Check if current path is checked out
                if self.is_checkout(current_path):

                    colist.append(current_path)

                try:
                    # Get all checked out children (file/folder)of current path
                    p = subprocess.Popen([self._config.get_cleartool_path(),
                                        "lsco", "-s", "-r", "-cvi",
                                        current_path],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
                    out, err = p.communicate()

                except:

                    raise CCError("ct lsco -s -r -cvi " +
                                self._config.get_view() +
                                self._("command_failed") +
                                str(sys.exc_info()))

                if p.returncode == 0:

                    if not (out is None or out == ""):

                        colist.extend(out.splitlines())

                else:

                    raise CCError("ct lsco -s -r -cvi " +
                                self._config.get_view() +
                                self._("command_failed") + str(err))

        # Reverse check out list to get directories' children files and folders
        # first
        colist.reverse()

        return colist

    def checkin_all(self):
        """
        Checks in every file and folder found checked out in the view.

        """

        colist = self.list_checkouts()

        for co in colist:

            try:

                self.checkin(co)

            except (CCError) as e:
                # print warning and continue executing check in
                print("{0} {1}".format(self._("WARNING"),
                                    co + self._("impossible_ci")))
                print(e)
                continue

            except:
                # print warning and continue executing check in
                print("{0} {1}".format(self._("WARNING"),
                                    co + self._("impossible_ci")))
                e = sys.exc_info()
                print(e)
                continue

    def uncheckout_all(self):
        """
        Cancels checkout status for every file and folder found checked out in the
        view.

        """

        colist = self.list_checkouts()

        for co in colist:

            try:

                self.uncheckout(co)

            except (CCError) as e:
                # print warning and continue executing check outs
                print("{0} {1}".format(self._("WARNING"),
                    co + self._("impossible_unco")))
                print(e)
                continue

            except:

                # print warning and continue executing check outs
                print("{0} {1}".format(self._("WARNING"),
                    co + self._("impossible_unco")))
                e = sys.exc_info()
                print(e)
                continue

            # Delete folders not versioned and empty
            if (os.path.isdir(co) and
               not os.listdir(co) and
               not self.is_versioned(co)):
                os.rmdir(co)

    def remove_name(self, ccpath):
        """
        Removes one file or folder from ClearCase.

        """

        # Parent dir must be checked out
        parent = os.path.dirname(ccpath)

        if not self.is_checkout(parent):

            self.checkout(parent, self._("CC_dir_modification_comment"))

        # Folders must be checked in before being deleted.
        if os.path.isdir(ccpath) and self.is_checkout(ccpath):

            self.checkin(ccpath)

        try:

            p = subprocess.Popen([self._config.get_cleartool_path(),
                                "rmname", ccpath],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
            out, err = p.communicate()

        except:

            raise CCError("ct rmname " + ccpath + self._("command_failed") +
                        str(sys.exc_info()))

        if p.returncode != 0:

            raise CCError("ct rmname " + ccpath + self._("command_failed") +
                        str(err))
