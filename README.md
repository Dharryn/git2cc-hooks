git2cc-hooks
============
This set of hooks lets a team work with ClearCase (from this point forward CC) and Git repositories simultaneously and bring changes between them in an easy way anytime is necessary.

Git updates CC in every push operation in a completely transparent way for the user.

CC updates to Git are made as usual performing a commit then a push to the bare repository. There is one requirement, this operation must be performed by a special user as we will see later.

## Initial configuration

* We must have a **snapshot view** in our server. Nobody should work anytime in this view because we will use it to synchronize the repository changes.
* We must have a user in the server to bring changes from CC to Git.
* Initialize a Git bare repository in the server:
```shell
$ git init --bare
```
* Initialize a Git repository in the CC snapshot view:
```shell
$ git init
```
* Edit the snapshow view repository configuration:
```shell
$ git config --local core.filemode true #(so GIT could understand modifications in file permissions as changes)
$ git remote add origin <URL_OF_BARE_GIT_REPO>
```
* Make the initial commit and push to the server. This is a good moment to create and add a `.gitignore` file to avoid the commit of unnecessary files.
```shell
$ git add –A
$ git commit –m “Initial commit”
$ git push -u origin master
```
* Remove the previous Git filemode option. This is necessary for the first commit, but must be removed in this point so the hooks can work properly. The reason is that current project version doesn't support changes in file permissions.
```shell
$ git config --local core.filemode false
```
## Hooks installation

* Clone git2cc-hooks project inside the hooks directory of the bare repository:
```shell
$ cd <URL_OF_BARE_GIT_REPO>/hooks
$ git clone git@github.com:Dharryn/git2cc-hooks.git
```
* Ensure execution permissions to the files **update.py** and **post_receive.py**
```shell
$ cd git2cc-hooks/src
$ chmod u+x update.py post_receive.py
```
* Make the following links inside <URL_OF_BARE_GIT_REPO>/hooks:
```
$ ln –s src/update.py update
$ ln –s src/post_receive.py post-receive
```
* Create a proper locale path structure for your language.
```shell
$ mkdir -p <URL_OF_BARE_GIT_REPO>/locale/<YOUR_LANGUAGE>/LC_MESSAGES
```
* Copy your language file in the previous folder: 
```shell
$ cp <URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/messages/<YOUR_LANGUAGE>/<YOUR_LANGUAGE.po> <URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES
```
* Enter inside `<URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES` and execute the following command:
```shell
$ msgfmt <YOUR_LANGUAGE>.po #This will create the file hooks.mo
```
* Copy directory `<URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/hooks_config` and all its contents to `<URL_OF_BARE_GIT_REPO>`
```shell
$ cp -R <URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/hooks_config <URL_OF_BARE_GIT_REPO>
```

## Configuration
Edit the configuration file:`<URL_OF_BARE_GIT_REPO>/hooks_config/bridge.cfg`
* Section `[cc_view]`
  * **path** path to our CC **snapshot view.**
* Section `[cc_config]`
  * **cleartool_path** path to CC executable. Already contains the default value.
  * **cc_pusher_user** user performing synchronizations from CC to Git. This user should be used for **CC -> Git** synchronizations only.
* Section `[git_config]`
  * **sync_branches** branch or branches (comma separated) that will bring changes from Git to CC. Usually this value will be reserved for master.
