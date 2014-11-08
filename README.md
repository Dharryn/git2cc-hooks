git2cc-hooks
============
Este conjunto de hooks permite llevar cambios entre un repositorio ClearCase (en adelante CC) y uno Git de una forma fácil y sencilla. Los equipos podrán trabajar en ambos repositorios de forma simultánea y llevar los cambios de uno a otro cuando sea necesario.

Git actualiza los cambios en el repositorio CC en cada operación de push de una forma totalmente transparente.

Las actualizaciones de CC a Git se realizan mediante un commit seguido de un push de la forma habitual. El único requisito es que estas operaciones debe hacerlas un usuario en concreto.

## Configuración inicial

* Debemos tener una vista **snapshot** en CC asignada en el servidor. Nadie debería trabajar nunca en este directorio porque es la vista que vamos a utilizar para sincronizar los cambios.
* Debemos tener un usuario en el servidor asignado para llevar los cambios desde CC a Git.
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
$ git config --local core.filemode true #(para que GIT interprete los cambios de permiso de los ficheros como modificaciones)
$ git remote add origin <URL_OF_BARE_GIT_REPO>
```
* Hacemos el commit inicial con todo el contenido de nuestra vista CC a Git. (Este sería un buen momento para crear y añadir un fichero `.gitignore` para evitar subida de los ficheros indeseados al repositorio).
```shell
$ git add –A
$ git commit –m “Initial commit”
$ git push -u origin master
```
* Eliminamos la opción de que Git interprete los cambios en los permisos de los archivos como modificaciones. (Es necesario para el commit inicial, pero debe eliminarse esta opción para el correcto funcionamiento de los hooks debido a que de momento no soportan cambios en los permisos de los ficheros en la dirección Git -> CC)
```shell
$ git config --local core.filemode false
```
## Instalación de los Hooks

* Clonamos el proyecto git2cc-hooks dentro del directorio hooks de nuestro repositorio bare.
```shell
$ cd <URL_OF_BARE_GIT_REPO>/hooks
$ git clone git@github.com:Dharryn/git2cc-hooks.git
```

* Aseguramos permisos de ejecución a los ficheros '''update.py''' y '''post_receive.py'''
```shell
$ cd git2cc-hooks/src
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
* Copiamos el fichero `<URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/messages/<YOUR_LANGUAGE>/<YOUR_LANGUAGE.po>` en `<URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES`
```shell
$ cp <URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/messages/<YOUR_LANGUAGE>/<YOUR_LANGUAGE.po> <URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES
```
* Entramos en el directorio `<URL_OF_BARE_GIT_REPO>/locale/en/LC_MESSAGES` y ejecutamos el siguiente comando:
```shell
$ msgfmt <YOUR_LANGUAGE>.po
```
Esto creará el archivo `hooks.mo`
* Copiamos el directorio `<URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/hooks_config` y su contenido a `<URL_OF_BARE_GIT_REPO>`
```shell
$ cp -R <URL_OF_BARE_GIT_REPO>/hooks/git2cc-hooks/src/hooks_config <URL_OF_BARE_GIT_REPO>
```

## Configuración
* Editamos el archivo de configuración:`<URL_OF_BARE_GIT_REPO>/hooks_config/bridge.cfg`
  * Sección `[cc_view]`
    * *path* path a nuestra vista snapshot de CC.
  * Sección `[cc_config]`
    * *cleartool_path* path al ejecutable de CC. (Contiene el valor por defecto)
    * *cc_pusher_user* usuario que va a realizar la sincronización de CC a Git.
  * Sección `[git_config]`
    * *sync_branches* rama o ramas que llevarán cambios desde Git a CC. (Normalmente este valor corresponderá únicamente a la rama master).
