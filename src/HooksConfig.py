"""
@summary: This class manages and validates the hooks configuration file.

"""

import locale
import gettext
import os
import ConfigParser


class ConfigException(Exception):
  """ 
  This class gets errors in the configuration file.

  """

  def __init__(self, value):
    self.value = value

  def __str__(self):
    return repr(self.value)


class HooksConfig(object):
  """
  Gets and manages the bridge configuration file.

  """

  __instance = None

  _ = None
  _config = ConfigParser.ConfigParser()
  _CONFIG_FILE = "hooks_config" + os.sep + "bridge.cfg"

  @staticmethod
  def get_default_locale():

    return ('en_US', 'UTF8')

  @staticmethod
  def get_translations():

    user_locale = locale.getdefaultlocale()

    if all(x is None for x in user_locale):

      user_locale = HooksConfig.get_default_locale()

    t = gettext.translation("Git2CC", "locale", user_locale, fallback=True)
    
    if isinstance(t, gettext.NullTranslations):
      
      user_locale = HooksConfig.get_default_locale()
      t = gettext.translation("Git2CC", "locale", user_locale, fallback=True)
      
    t.install()

    return t.ugettext


  def __new__(cls, *args, **kargs):

    if cls.__instance is None:

      cls.__instance = object.__new__(cls, *args, **kargs)

    return cls.__instance


  def __init__(self):
    """
    Class constructor that gets and validates the configuration and sets the
    translation alias

    """

    # Load user messages
    self._ = HooksConfig.get_translations()

    # Read and validate configuration file
    self._config.readfp(open(self._CONFIG_FILE))
    self._validate_config()


  def _validate_config(self):
    """
    This procedure checks the configuration file and ensures every section,
    field, file and folder existence.

    """

    # Section validation
    if not self._config.has_section("cc_view"):

      raise ConfigException(self._("missing_section") + " cc_view")

    elif not self._config.has_section("cc_config"):

      raise ConfigException(self._("missing_section") + " cc_config")
    
    # cc_view section fields validation
    if not self._config.has_option("cc_view", "path"):

      raise ConfigException(self._("missing_field") + " path " + 
                            self._("in_section") + " cc_view.")

    elif not os.path.isdir(self.get_view()):

      raise ConfigException(self.get_view() + self._("folder_not_exists"))

    # cc_config section fields validation
    if not self._config.has_option("cc_config", "cleartool_path"):

      raise ConfigException(self._("missing_field") + " cleartool_path " + 
                            self._("in_section") + " cc_config.")

    elif not os.path.isfile(self.get_cleartool_path()):

      raise ConfigException(self.get_cleartool_path() + 
                            self._("file_not_exists"))

    if not self._config.has_option("cc_config", "cc_pusher_user"):

      raise ConfigException(self._("missing_field") + " cc_pusher_user " + 
                            self._("in_section") + " cc_config.")
      
  def get_view(self):
    """
    Path to ClearCase view to sync

    """

    return self._config.get("cc_view", "path")

  def get_cleartool_path(self):
    """
    Path to clear tool command

    """

    return self._config.get("cc_config", "cleartool_path")

  def get_cc_pusher_user(self):
    """
    Returns the user pushing from the ClearCase view to sync work with Git.
    When hooks detect this users, they avoid doing any other operation.

    """

    return self._config.get("cc_config", "cc_pusher_user")

  def get_sync_branches(self):
    """
    Returns the list of Git branches in sync with ClearCase

    """

    branches = []

    if not self._config.has_option("git_config", "sync_branches"):

      branches.append("master")

    else:

      branches = self._config.get("git_config", "sync_branches").split(',')
      branches = [x.strip() for x in branches]

    return branches
