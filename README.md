![](https://github.com/Shiphero/shbin/actions/workflows/pytest.yml/badge.svg)
![](https://github.com/Shiphero/shbin/actions/workflows/black.yml/badge.svg)

`shbin` turns a Github repo into a pastebin. 

It's a tiny command-line tool we've built at
[Shiphero](http://shiphero.com) that lets you easily upload code
snippets, notebooks, images, or any other file to a Github repository
that acts as your internal pastebin, and returns the URL to share it
with your team. If possible, this URL is automatically copied to the
clipboard. 

# Why? 

You want to share code snippets, images, notebooks, etc. with your team,
probably privately. Gist is great, but it has some limitations:

- The content may be secret but it is not private: if you have the url
  you have the access (and to err is human). 
- The ownership of the shared content is in the user's namespace, not
  the organization's.  What happens if the user leaves the organization? 
- You can't find some secret content shared by a teammate if the URL is
  lost. Only the person who created it can find it, and even that isn't
  easy if the content doesn't have a good name and description. 
- Content organization is difficult: you can upload multiple files to
  a gist, but you can't create folders.
- The default gist interface does not allow you to "paste" an image (you
  can paste it as part of a comment, but not as part of the gist content
  itself). Sharing screenshots is a common use case on computers. 

Using a full repository has all the advantages of Gist (rich content
rendering like markdown or ipynb, every change is a git commit, etc.)
without these limitations. 

The only downside of a plain repository is that it is not as easy as
"paste" the content, even when  editing through the Github interface.
But `shbin` solves that. 

# Usage

```console
# upload or update a file
$ shbin demo.py

# upload with a commit description
$ shbin demo.py -m "my cool demo script"         

# Upload any content in clipboard, discovering its format. e.g.
# a screenshot. The name will be random but the extension will be
# based on the format detected.
$ shbin -x          

# upload the content in the clipboard with a given filename
$ shbin -x -f my_snippet.md 

# upload from stdin
$ echo "some content" | shbin -

# download a given file (inside the namespace)
$ shbin dl my_snippet.md     

# update the content of a file that already exists
$ shbin my_snippet.md

# from clipboard with a given name to a directory in your user directory
$ shbin -x -f the_coolest_thing.py -d coolest_things/python

# upload several files in a directory
$ shbin *.ipynb *.csv -d notebooks/project -m "my new work"   

# Reformat the URL to link to Github pages.
$ shbin demo.py -p

$ shbin -h   # show full options
```

# How it works

It uses [Github API](https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#create-or-update-file-contents)
to create or update files in the given repo. So there is no need to
have the target repository fully cloned locally.  


# Install

The recommended way is to use [pipx](https://pypa.github.io/pipx/)

```console
pipx install shbin 
```

Alternatively, install directly with `pip`. 

```console
pip install --user shbin
```

To install the latest development version from the repository:

```console
pip install --user https://github.com/Shiphero/shbin/archive/refs/heads/main.zip
```

## OSX
shbin depends on 
[python-magic](https://github.com/ahupp/python-magic#osx). This can be
installed as follows.

- When using Homebrew: 

```console
brew install libmagic
```

- When using macports: 

```console
port install file
```

# Setup

Create a [new fine-grained personal token](https://github.com/settings/personal-access-tokens/new)
on Github restricted to your "pastebin" repository (under your user or
your organization's ownership), with read and write permissions on
"Contents". 

![image](https://user-images.githubusercontent.com/2355719/238758491-9d15e7e6-e4b7-43c8-a321-b65c968fc7e0.png)

- Then set the environment variables in your preferred place:
    
  ```
  export SHBIN_GITHUB_TOKEN="<your personal token>"
  export SHBIN_REPO="<user_or_org>/<repo>"   # example "Shiphero/pastebin"   
   ```

- By default `shbin` assigns a top-level folder to separate the content
  uploaded by each user. This can be changed using the `SHBIN_NAMESPACE`
  environment variable or the `--namespace` argument from the command
  line. For example: 

  - `export SHBIN_NAMESPACE=""`        # no namespace
  - `export SHBIN_NAMESPACE="pastebin_folder"`  # the full pastebin is inside pastebin_folder/" 
  - `export SHBIN_NAMESPACE="pastebin_folder/{user}"`   # mix of both: each user has its own subfolder inside `pastebin_folder/` 

- [optional] To interact with the clipboard, we use the library `pyclip`.
  This may require some additional system dependencies
  depending your operating system. See [these notes](https://github.com/spyoungtech/pyclip#platform-specific-notesissues).

  If you want to disable the automatic copying of the URL to the clipboard 
  you can set the environment variable `SHBIN_COPY_URL=false` (or "0" or "no"). 
  
  This is useful in some Linux distributions that use Wayland as the call via `wl-copy`
  that `pyclip` uses in such environment can be slow. 



PRs are welcome! 
