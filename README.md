git2cc-hooks
============
Este hook permite a los grupos de trabajo tener su propio repositorio Git y llevar los cambios de forma automática y transparente al repositorio de ClearCase (en adelante CC).

La versión actual está sometida a continuas modificaciones. 

## Configuración inicial

* Debemos tener una vista CC asignada en el servidor. Si no tenemos una debemos solicitarla al responsable correspondiente.

* Debemos iniciar un repositorio bare en el servidor:
```shell
$ git init --bare
```
* Iniciamos un repositorio Git en nuestra vista:
```shell
$ git init
```
* Editamos el archivo `.git/config` de nuestra vista:
```shell
$ git config --local core.filemode true#(para que GIT interprete los cambios de permiso de los ficheros como modificaciones)
$ git remote add origin <URL_OF_BARE_GIT_REPO>
```
* Hacemos el commit inicial con todo el contenido de nuestra vista CC a GIT. (Se incluye todo menos lo que haya definido en el archivo exclude del paso anterior):
Este sería un buen punto para crear un `.gitignore` para evitar subida de los ficheros que no quieres que estén en el repositorio
```shell
$ git add –A
$ git commit –m “Initial commit”
$ git push -u origin master
```
* Eliminamos la opción de que GIT interprete los cambios en los permisos de los archivos como modificaciones. (Es necesario para el commit inicial, pero debe eliminarse esta opción para el correcto funcionamiento de los hooks)
```shell
$ git config --local core.filemode false
```
## Instalación de los Hooks

* Creamos un directorio llamado python dentro del directorio hooks de nuestro repositorio bare:
```shell
$ cd <URL_OF_BARE_GIT_REPO>/hooks
$ mkdir python
```
hacer el clone de la url de github, la release ultima stable.

* Damos permisos de ejecución a los ficheros '''update.py''' y '''post_receive.py'''
```shell
$ chmod u+x update.py post_receive.py
```
* Realizamos los siguientes enlaces en <URL_OF_BARE_GIT_REPO>/hooks:
```
$ ln –s python/update.py update
$ ln –s python/post_receive.py post-receive
```
* Creamos una estructura de directorios para el locale:
```shell
$ mkdir -p <URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES
```
* Copiamos el fichero `<URL_CC_VIEW>/fdp/macros/git/hooks/hooks.po` al directorio previamente creado `<URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES`
```shell
$ cp <URL_CC_VIEW>/fdp/macros/git/hooks/hooks.po <URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES
```
* Entramos en el directorio `<URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES` y ejecutamos el siguiente comando:
```shell
$ msgfmt hooks.po
```
Esto creará el archivo `hooks.mo`
* Copiamos el directorio `<URL_CC_VIEW>/fdp/macros/git/hooks/hooks_config` y su contenido a `<URL_OF_BARE_GIT_REPO>`

## Configuración de los Hooks
* Editamos el archivo `<URL_OF_BARE_GIT_REPO>/hooks_config/bridge.cfg` En la sección `[cc_view]`buscamos la opción `path` y escribimos nuestra `<URL_CC_VIEW>`
Normalmente no es necesario tocar el resto de opciones salvo que sepamos muy bien lo que estamos haciendo.

## Limitaciones del sistema
Realizados estos pasos podemos operar con GIT de forma transparente a ClearCase teniendo en cuenta las siguientes limitaciones de la versión:

* La actualización de la vista CC y llevar los cambios de CC a GIT debe hacerse de forma manual, preferentemente por una única persona encargada.
* No hay soporte para ramas de GIT. Se hace todo sobre el master.
* El renombrado de archivos y directorios se realiza como una eliminación seguida de una adición.
