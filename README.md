# qxw-html
This python script converts html output from QXW into a fully interactive HTML embed you can embed into your websites or webpages. 

This was created and optimised for Imperial's Felix to embed crosswords into their pages.

# Usage
To use this converted, have your qxw crossword.html and clues.txt in the same directory as this script.

    $ python3 ./converter.py crossword.html clues.txt output.html

This will generate your interactive crossword as output.html

## Features
* Arrrow keys to change focused input cell
* Auto select next input cell
* Detection of cells that belong to the same word
* Improve clues display
* Mini clue box for selected word

## Future features
* Optimise for mobile viewers 