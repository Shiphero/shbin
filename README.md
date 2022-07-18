# SHbin
A tiny but powerful tool to upload any content easily to our shared repo.

# First Steps

- Create a personal token from https://github.com/settings/tokens
  Follow these instructions for details https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token
  Make sure of:
    
    - Enable Repo and User scopes
    - Enable SSO
- Set the environment variable:
    ```
    export SHBIN_GITHUB_TOKEN = "<your personal token>"
    ```
- Install pygithub
  ```
  $pip --user install pygithub
  ```
- [optionally] Install xclip. For example in Ubuntu/Debian
  
  ```
  $ sudo apt install xclip
  ```
# Usage

```
$ shbin <file>
$ shbin  # upload content from the clipboard, discovering its format. e.g. an screenshot
$ shbin <file> -u -m "your message"   # update a file and add a commit message
$ shbin <file1> <file2> [...]         # upload several files  
$ shbin -h   # show full options
```
