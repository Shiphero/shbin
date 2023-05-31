!/usr/bin bash
rm my_snippet_2.md
asciinema rec --overwrite -c 'tuterm usage.tutorial --mode demo' usage.cast
svg-term --window --width 60 --height 20 --padding 1 --in usage.cast --out usage.svg
rm usage.cast