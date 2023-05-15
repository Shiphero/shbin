# SHBin

![](https://github.com/Shiphero/shbin/actions/workflows/pytest.yml/badge.svg)
![](https://github.com/Shiphero/shbin/actions/workflows/black.yml/badge.svg)

`shbin` turns a Github repo in a pastebin. 

It's tiny command line tool to upload snippets, notebooks, images or any other file easily to a repository that works as your internal Pastebin, returning the url to share it with your team.


# Why? 

You want to share code snippets, images, notebooks, etc. with your team, probably privately. Gist is awesome, but it has a few limitation:

- The content may be secret but it is not private: if you get the url, you have the access (and to err is human). 
- The ownership of the shared content is in the user's namespace, not the organization's. What happens if the user leaves the company? 
- You can't find a secret content shared by a teammate if the url is lost. Only the one who created it could find it, and it's not so easy if it doesn't have a name or a good description. 
- Content organization is difficult: in a gist you can upload several files but you can't create folders.
- The default gist interface does not allow you to "paste" an image (you can paste it as part of a comment, but not as part of the gist content itself). Sharing screenshots is a frequent use case on computers. 

Using a real repository has almost all the advantages of gist (rich content rendering like markdown or ipynb, every change is a git commit, etc) without these limitations. 

The only disadvantage of a repository is that it is not as easy as "pasting", even if the editing is done from the github interface. But `shbin` solves this. 


# Usage

```console
# upload 
$ shbin demo.py -m "my cool demo script"         

# upload any content in clipboard, discovering its format. e.g. an screenshot. 
# the name will be random but the extension will be based on the format detected.
$ shbin -x          

# upload content in the clipboard but giving it a name
$ shbin -x -f my_snippet.md 

# download a given file (inside the namespace)
$ shbin dl my_snippet.md     

# upgrade the content of a file that already exists
$ shbin my_snippet.md

# from clipboard with a given name to a directory in your user directory
$ shbin -x -f the_coolest_thing.py -d coolest_things/python

# upload several files in a directory
$ shbin *.ipynb *.csv -d notebooks/project -m "my new work"   

$ shbin -h   # show full options
```


# How it works

It uses [Github API](https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents) to create or update files in the given repo. So there is not need to have the target repository fully cloned.  


# Install

The recommended way is to use [pipx](https://pypa.github.io/pipx/)

```console
pipx install git+ssh://git@github.com/Shiphero/shbin.git
```

Alternatively, install directly with pip

```console
pipx install --user git+ssh://git@github.com/Shiphero/shbin.git
```

## OSX
It can be issues with [python-magic](https://github.com/ahupp/python-magic#osx) install

- When using Homebrew: 

```console
brew install libmagic
```

- When using macports: 

```console
port install file
```

# Setup

- Create a new [personal token](https://github.com/settings/tokens). Follow [these instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) for details. Make sure of:
    
  - Enable Repo and User scopes
  - Enable SSO if your organization requires it. 

- Set the environment variables:
    
    ```
    export SHBIN_GITHUB_TOKEN = "<your personal token>"
    export SHBIN_REPO = "<your organization>/<the repo>"   # example "Shiphero/pastebin"   
    ```

- By default `shbin` assigns a top-level folder to separate the content uploaded by each user. That could be changed with the `SHBIN_NAMESPACE` environment variable or `--namespace` argument from the command line.

  -  `export SHBIN_NAMESPACE=""`        # no namespace
  -  `export SHBIN_NAMESPACE="pastebin_folder"  # the full pastebin is inside pastebin_folder/" 
  - `export SHBIN_NAMESPACE="pastebin_folder/{user}"   # mix of both: each user has its own folder inside pastebin_folder/

- [optionally] Install xclip to be able to copy from your clipboard. For example in Ubuntu/Debian
  
  ```console
  $ sudo apt install xclip
  ```
