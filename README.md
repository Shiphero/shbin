# SHBin

A tiny tool to upload any snippets, notebooks or any other content easily to our [internal pastebin repo](https://github.com/Shiphero/pastebin).

# Install

- Install the package

```
pip install --user pipx
pipx install  git+ssh://git@github.com/Shiphero/shbin.git
```

- Create a new [personal token](https://github.com/settings/tokens). Follow [these instructions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) for details. Make sure of:
    
  - Enable Repo and User scopes
  - Enable SSO

- Set the environment variables:
    ```
    export SHBIN_GITHUB_TOKEN = "<your personal token>"
    export SHBIN_REPO = "Shiphero/pastebin" 
    ```
- [optionally] Install xclip. For example in Ubuntu/Debian
  
  ```console
  $ sudo apt install xclip
  ```

# Usage

```console
$ shbin demo.py -m "something cool to share"         

# upload content from the clipboard, discovering its format. e.g. an screenshot
$ shbin -x           

# upload several files in a directory
$ shbin *.ipynb *.csv -o notebooks/project -m "my new work"   


$ shbin -h   # show full options
```
