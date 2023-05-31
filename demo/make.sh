!/usr/bin bash
asciinema rec --overwrite -c 'tuterm usage.tutorial --mode demo' usage.cast 
svg-term --window --width 75 --height 24 --padding 1 --in usage.cast --out usage.svg
rm usage.cast
