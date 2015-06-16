#!/usr/bin/env python

import os
import shutil
import subprocess
import sys
import traceback


class InstallerError(Exception):

    """
    Exception class to represent errors occurred during the installation
    process

    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def links(cwd, hookspath):
    """
    Creates links to the hooks scripts.

    """

    update_link = hookspath + os.sep + "update"
    post_receive_link = hookspath + os.sep + "post-receive"

    if not os.path.lexists(update_link):
        os.symlink(cwd + os.sep + "update.py", update_link)
    else:
        raise InstallerError("update link already exists.")

    if not os.path.lexists(post_receive_link):
        os.symlink(cwd + os.sep + "post-receive.py", post_receive_link)
    else:
        raise InstallerError("post-receive link already exists.")


def language(cwd, gitpath):
    """
        Installs languages

    """

    for item in os.listdir(cwd + os.sep + "messages"):

        original_file = cwd + os.sep + "messages" + \
            os.sep + item + os.sep + item + ".po"

        dest_path = gitpath + os.sep + "locale" + \
            os.sep + item + os.sep + "LC_MESSAGES"
        dest_file = dest_path + os.sep + item + ".po"

        if os.path.isfile(original_file):

            # Create path
            os.makedirs(dest_path)
            # Copy *.po file
            shutil.copy(original_file, dest_path)
            # Generate *.mo file
            p = subprocess.Popen(["msgfmt", dest_file], cwd=dest_path)
            p.communicate()


def main():

    cwd = os.getcwd()
    pathlist = cwd.split(os.sep)

    # Detect git repository
    if (".git" in pathlist and
            "hooks" in pathlist and
            pathlist.index(".git") < pathlist.index("hooks")):

        # Get .git and hooks path
        hookspath = os.sep.join(pathlist[:pathlist.index("hooks") + 1])
        gitpath = os.sep.join(pathlist[:pathlist.index(".git") + 1])

        # Install
        links(cwd, hookspath)
        language(cwd, gitpath)
    else:
        raise InstallerError("Repository not detected")


if __name__ == "__main__":

    try:
        main()

    except InstallerError as e:

        print("{0}: {1}".format("Instaler error", e.value))
        sys.exit(1)

    except:

        print("{0}: {1}".format("Instaler unexpected error",
                                traceback.format_exc()))
