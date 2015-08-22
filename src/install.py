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


def install_executables(cwd, hookspath):
    """
    Enables hooks scripts execution flag and creates the necessary links.

    """

    # Paths
    update_file = cwd + os.sep + "update.py"
    post_receive_file = cwd + os.sep + "post-receive.py"

    update_link = hookspath + os.sep + "update"
    post_receive_link = hookspath + os.sep + "post-receive"

    # Execution flag
    os.chmod(update_file, 0744)
    os.chmod(post_receive_file, 0744)

    # Links
    if not os.path.lexists(update_link):
        os.symlink(update_file, update_link)
    else:
        raise InstallerError("update link already exists.")

    if not os.path.lexists(post_receive_link):
        os.symlink(post_receive_file, post_receive_link)
    else:
        raise InstallerError("post-receive link already exists.")


def install_language(cwd, gitpath):
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


def install_config(cwd, gitpath):
    """
        Installs configuration file

    """

    shutil.copytree(cwd + os.sep + "hooks_config",
                    gitpath + os.sep + "hooks_config")


def print_final_message(gitpath):

    print("{0}".format("Hooks successfully installed."))
    print("{0}: {1}".format(
        "Please review your configuration file",
        gitpath + os.sep + "hooks_config" + os.sep + "bridge.cfg"))


def main():

    cwd = os.getcwd()
    pathlist = cwd.split(os.sep)

    git_index = 0

    # Detect git repository
    for x in pathlist:
        if x.endswith(".git"):
            git_index = pathlist.index(x)

    if (git_index > 0 and
            "hooks" in pathlist and
            git_index < pathlist.index("hooks")):

        # Get .git and hooks path
        hookspath = os.sep.join(pathlist[:pathlist.index("hooks") + 1])
        gitpath = os.sep.join(pathlist[:git_index + 1])

        # Install
        install_executables(cwd, hookspath)
        install_language(cwd, gitpath)
        install_config(cwd, gitpath)

        # End message
        print_final_message(cwd)
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
