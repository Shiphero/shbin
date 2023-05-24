#!/usr/bin/env sh
# file: shbin_usage.sh
configure() {
    DELAY=0.1
    DELAY_SEP=0.15
    DELAY_PROMPT=1.2
    COLOR_MESSAGE='1;32'
}

run() {
M "upload or update a file"
c shbin $MY_WORKING_DIR/demo.py

M "upload with a commit description"
c shbin $MY_WORKING_DIR/demo_2.py -m \"my cool demo script\"

M "Upload any content in clipboard, discovering its format. e.g."
echo "some awesome thing" | pyclip copy
M "The name will be random but the extension will be based on the format detected."
c shbin -x

M "upload the content in the clipboard with a given filename"
echo "some awesome thing" | pyclip copy
c shbin -x -f my_snippet_2.md

M "upload from stdin"
echo some content | shbin -

M "download a given file (inside the namespace)"
c shbin dl alvarmaciel/my_snippet_2.md

c cat my_snippet_2.md

M "update the content of a file that already exists"
echo "some awesome new content" >> $MY_WORKING_DIR/my_snippet_2.md
c shbin $MY_WORKING_DIR/my_snippet_2.md

M "copy from clipboard"
c cat $MY_WORKING_DIR/demo.py | pyclip copy

M "upload the content with a given name to a directory in your user directory"
c shbin -x -f the_coolest_thing.py -d demo/coolest_things/python

M "upload several files in a directory"
c shbin $MY_WORKING_DIR/*.py $MY_WORKING_DIR/*.sh -d demo/notebooks/project -m \"my new work\"

M "Reformat the URL to link to Github pages."
c shbin $MY_WORKING_DIR/demo_3.py -p

M "show full options"
c shbin -h
}