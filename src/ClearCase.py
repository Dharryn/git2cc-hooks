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
import logging
import logging.handlers

from HooksConfig import HooksConfig

#LOG_FILENAME = "/tmp/" + os.path.basename(__file__).split('.')[0] + "." + str(os.getpid()) + '.log'
LOG_FILENAME = "/tmp/Git2CC.log"
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1000000, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

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
        This constructor gets the current Hooks configuration and user messages

        """

        try:

            # Load user messages
            self._ = HooksConfig.get_translations()

            # Get configuration
            self._config = HooksConfig()

        except:

            raise

    def need_merge(self, ccpath):
        """
        Checks if the received file or folder need merge on ClearCase

        """
        logger.debug("need_merge:"+ccpath)
        
        result = False
        
        if os.path.exists(ccpath):
            
            logger.debug("need_merge: exist_path")

            try:
                # Get the current version description
                # Ex : path@@/main/Step2_project/rel_1.3/15
                p = subprocess.Popen([self._config.get_cleartool_path(),
                                      "des","-short"
                                      ,ccpath],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
                out, err = p.communicate()

                logger.debug ("need_merge:" + str(p.returncode))

                logger.debug ("need_merge:" + " ".join(out))

                if p.returncode == 0:
                    
                    line=out.rstrip('\r\n')
                    
                    logger.debug("need_merge_line: " + line)

                    # Changes from (r)ight position of string the last number
                    # (15) with LATEST
                    branch=out.rpartition("/")[0]+"/LATEST"
                    
                    logger.debug ("need_merge: "+ccpath+","+line+","+branch)
                    
                    p = subprocess.Popen([self._config.get_cleartool_path(),
                                          "des","-short"
                                          ,branch],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                          
                    out, err = p.communicate()
                    
                    logger.debug
                    ("need_merge: compare:("+line+"=="+out.rstrip('\r\n')+")")
                    
                    result = (line != out.rstrip('\r\n'))
                    
            except:
                
                logger.debug("need_merge: exception " + str(sys.exc_info()))
                
                result = False
                
        else:

            logger.debug("need_merge: not_exist_path")

        if result:
            
            logger.debug("need_merge: TRUE!!!")
            
        else:
            
            logger.debug("need_merge: false")
            
        return result

    def is_versioned(self, ccpath):
        """
        Checks if the received file or folder is under ClearCase

        """

        logger.debug ("is_versioned:" + ccpath)
        
        result = False

        if os.path.exists(ccpath):

            try:
                if not os.path.isdir(ccpath):

                    p = subprocess.Popen([self._config.get_cleartool_path(),
                                          "ls",
                                          "-vob_only", ccpath],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)

                    out, err = p.communicate()

                else:

                    p = subprocess.Popen([self._config.get_cleartool_path(),
                                          "ls",
                                          "-vob_only","-directory", ccpath],
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

        logger.debug ("is_checkout:" + ccpath)
        
        result = False

        p = subprocess.Popen([self._config.get_cleartool_path(), "lsco",
                              "-s", "-d", "-cvi", ccpath],
                             stdout=subprocess.PIPE)
        out = p.communicate()

        if p.returncode == 0 and out[0] != "":

            result = out[0].rstrip('\r\n') == ccpath

        return result

    def makelabel(self, ccpath, label):
        """
        Create file, and ignore errors"
        """
        
        result = False
        
        logger.debug("Creating label :"+label+","+ccpath)
        
        p = subprocess.Popen([self._config.get_cleartool_path(),"mklbtype","-nc","-pbr",label],cwd=os.path.dirname(ccpath),
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        out = p.communicate()
        
        logger.debug(out);
        
        if p.returncode == 0 and out[0] != "":

            result = out[0].rstrip('\r\n') == ccpath

        p = subprocess.Popen([self._config.get_cleartool_path(),"mklabel",label,ccpath],
			    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        
        out = p.communicate()
        
        logger.debug(out);
        
        if p.returncode == 0 and out[0] != "":

            result = out[0].rstrip('\r\n') == ccpath

        return result

    def checkout(self, ccpath, comment, addVersion=False):
        """
        Executes the check out of the given file with the specified comment and
        optionally a version

        Raises CCError exception when the command fails.

        """

        logger.debug ("checkout:" + ccpath)
        
        # File/Folder must exists and have version in ClearCase
        if not addVersion and not self.is_versioned(ccpath):

            raise CCError(ccpath + self._("not_in_CC"))

        # Files/Folders can not be already checked out
        if self.is_checkout(ccpath):

            raise CCError(ccpath + self._("already_co"))

        if self.need_merge(ccpath):
            raise CCError(ccpath + self._("file_need_clearcase_merge"))

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

        logger.debug("uncheckout:" + ccpath)

        p = subprocess.Popen([self._config.get_cleartool_path(), "unco", "-rm",
                              ccpath])
        p.communicate()

        if p.returncode != 0:

            raise CCError(ccpath + " ct unco -rm" + self._("command_failed"))

    def set_label(self, label, ccpath):
        """
        Sets a CC label to an element

        Raises CCError exception when the command fails.

        """

        p = subprocess.Popen([self._config.get_cleartool_path(), "mklabel", "-replace", label, ccpath], stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out, err = p.communicate()

        if p.returncode != 0:

            raise CCError(ccpath + " ct mklabel -replace " + self._("command_failed") + str(err))

        else:

            logger.debug ("Label : " + label + " set in " + ccpath)

        
    def exists_label(self, label, ccpath):
        """
        Check if a label exists

        Raises CCError exception when the command fails.
        """
        result = False

        prevdir = os.getcwd()

        parent = os.path.dirname(ccpath)

        os.chdir(parent)

        try:
            p = subprocess.Popen([self._config.get_cleartool_path(), "lstype",
                              "lbtype:" + label],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            out, err = p.communicate()

        except:
            print ccpath + self._("exists_label_failed") + str(sys.exc_info())
            
        os.chdir (prevdir)

        if p.returncode == 0 and out[1] != "Error:":

            result = True

        return result

    def checkin(self, ccpath, labels=[]):
        """
        Executes the check in of the given file or directory

        Raises CCError exception when the command fails.

        """

        logger.debug("checkin:" + ccpath)

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
        else:

            self.create_and_set_labels (ccpath, labels);

    def create_dir(self, ccpath):
        """
        Creates a new directory in ClearCase.

        Raises CCError exception when the command fails.

        """

        logger.debug("create_dir:"+ccpath)

        if not os.path.isdir(ccpath):

            parent = ccpath

            # Remove last / when necessary
            if parent[len(parent) - 1] == os.sep:

                parent = parent[:-1]

            # Get parent directory
            parent = os.path.dirname(parent)

            if not os.path.isdir(parent):

                raise CCError(parent + self._("not_in_CC"))

            # Only create dir if not versioned in CC
            if not self.is_versioned(ccpath):
                
                if not self.is_checkout(parent):
                    # Check out parent directory
                    self.checkout(parent, self._("CC_dir_modification_comment"))

                try:

                    # Create new directory
                    p = subprocess.Popen([self._config.get_cleartool_path(),
                                          "mkdir", "-c",
                                          self._("new_CC_folder"),
                                          ccpath],
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
                    out, err = p.communicate()
                    
                    self.checkin(parent)
                    
                    self.checkin(ccpath)
                    
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

        logger.debug("create_path:" + ccpath)

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

    def create_file(self, ccpath, labels, list_co):
        """
        Adds a new file to ClearCase. The file must exists previously.

        Raises CCError exception when a failure is detected.

        """

        logger.debug("create_file:" + ccpath)

        if not os.path.isfile(ccpath):

            raise CCError(ccpath + self._("file_not_exists"))

        # Preserve current keep file if it exists (NOT NEEDED CC does it)
        #if os.path.isfile(ccpath + ".keep"):
        #    os.rename(ccpath + ".keep", ccpath + ".keep.old")

        try:

            if not self.is_checkout (os.path.dirname(ccpath)):
                # Checkout file folder
                self.checkout(os.path.dirname(ccpath), self._("new_file"))
                list_co.append (os.path.dirname (ccpath))
                
            # Open the file avoids anyone changes it during the check out
            with open(ccpath) as f:
                p = subprocess.Popen([self._config.get_cleartool_path(),
                                      "mkelem", "-nc", "-nco", ccpath],
                                     #cwd=os.path.dirname(ccpath)
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
                self.checkin(ccpath, labels)
            else:
                raise CCError(ccpath + self._("creation_failed") + str(err))

        except IOError:

            raise CCError(ccpath + self._("file_not_exists"))

        except CCError:
            raise

        except:
            raise CCError(ccpath + self._("creation_failed") +
                          str(sys.exc_info()))

    def list_checkouts_in_all_vobs(self):
        """
        List checkouts in all the configured vobs.
        """
        colist_in_vobs = []

        vobs = self._config.get_vobs()
        
        vobs_to_string = " ".join(str(x) for x in vobs)

        logger.debug("list_checkouts in all vobs : " + vobs_to_string)

        if not vobs:

            colist_in_vobs = self.list_checkouts("")
            
        else:
            
            for vob in vobs:
                colist_in_vobs.extend (self.list_checkouts(vob))

        list_of_checkouts = " ".join(str(x) for x in colist_in_vobs)
        
        logger.debug("Final list_checkout in all vobs : " + vobs_to_string +
                     " list of checkouts : " + list_of_checkouts)
        
        return colist_in_vobs

    
    def list_checkouts(self, vob):
        """
        Lists every file and folder checked out in the current view.

        """
        logger.debug("list_checkouts in vob : " + vob)

        colist = []

        vob_path = self._config.get_view() + os.sep + vob

        # list files in each vob.
        for i in os.listdir(vob_path):

            current_path = vob_path + os.sep + i

            logger.debug("Path to search checkouts : " + current_path)
            
            if os.path.isdir(current_path) and self.is_versioned(current_path):

                # Check if current path is checked out
                logger.debug("Path is checkout:"+ str
                             (self.is_checkout(current_path)))
                
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
                                  current_path +
                                  self._("command_failed") +
                                  str(sys.exc_info()))
                
                if p.returncode == 0:
                    
                    if not (out is None or out == ""):
                    
                        colist.extend(out.splitlines())
                        
                else:
                    
                    raise CCError("ct lsco -s -r -cvi " +
                                  current_path +
                                  self._("command_failed 2") + str(err))
                    
        # Reverse check out list to get directories' children files and folders
        # first
        colist.reverse()
        logger.debug("checkouts in vobs " + vob + " : " + ' '.join(colist))
        
        return colist
                
    def checkin_all(self, labels):
        """
        Checks in every file and folder found checked out in the view.

        """

        logger.debug("checkin_all")

        colist = []

        colist = self.list_checkouts_in_all_vobs()

        for co in colist:

            try:

                logger.debug("Checkin of: "+co)
                self.checkin(co, labels)

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
        Cancels checkout status for every file and folder found checked out in
        the view.

        """

        logger.debug("uncheckout_all")

        colist = []
        
        colist = self.list_checkouts_in_all_vobs()

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

    def remove_name(self, ccpath, colist):
        """
        Removes one file or folder from ClearCase.

        """

        logger.debug("remove_name:"+ccpath)

        # Parent dir must be checked out
        parent = os.path.dirname(ccpath)

        if not self.is_checkout(parent):
            
            self.checkout(parent, self._("CC_dir_modification_comment"))
            colist.append (parent)
            
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

    def create_label(self, label, ccpath):
        """
        Creates a new CC label.

        Raises CCError exception when the command fails or the label already 
        exists.

        """
        if not self.exists_label (label, ccpath):

            p = subprocess.Popen([self._config.get_cleartool_path(), "mklbtype", "-nc", "-pbr", label],cwd=os.path.dirname(ccpath),
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            out, err = p.communicate()

            if p.returncode != 0 and out[0] != "":

                logger.error (out)
                
                raise CCError(ccpath + " ct mklbtype -nc -pbr" + self._("command_failed") + str(err))
            
            else:

                logger.debug (out)

        else:

            logger.debug ("CC Label " + label + "Already created")
            
    def create_and_set_labels(self, ccpath, labels):
        """
        Creates new CC labels.

        Raises CCError exception when the command fails or the label already 
        exists.

        """
        for label in labels:

            try :
                
                if not self.exists_label (label, ccpath):
                    self.create_label (label, ccpath)

                self.set_label (label, ccpath)
                
            except:
                # print warning and continue executing check in
                print("{0} {1}".format(self._("WARNING"),
                                    label + self._("impossible_label")))
                e = sys.exc_info()
                print(e)
                continue

    def checkin_list(self, co_list, labels=[]):
        """
        Creates new CC labels.

        Raises CCError exception when the command fails or the label already 
        exists.

        """
        # Checkout dirs are check-in.
        #
        if co_list:

            logger.debug("checkin checkout dir in delete")
        
            for co_dir in co_list:
                self.checkin (co_dir)

        else:

            logger.debug("No files to checkin")
            
