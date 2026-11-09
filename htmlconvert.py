import sys
import re
from bs4 import BeautifulSoup

# CELL CLASS
class Cell:
    def __init__(self, row, col, is_white, clue_number=None, is_beginning=None):
        """
        Initialize a crossword cell.

        Args:
            row (int): Row index in the grid.
            col (int): Column index in the grid.
            is_black (bool): True if the cell is a black square.
            value (str or None): Letter filled in the cell, None if empty.
            clue_number (int or None): Clue number if this cell starts a word.
        """
        self.row = row
        self.col = col
        self.is_white = is_white
        # self.value = value
        self.is_beginning = is_beginning
        # Ensure each Cell gets its own clue list (avoid shared mutable default)
        if clue_number is None:
            self.clue_number = []
        else: 
            self.clue_number = clue_number
        self.is_across = None
        self.is_down = None
        self.next_across_clue = None
        self.next_down_clue = None
        # self.across_word = None   # Reference to the Word object going across
        # self.down_word = None     # Reference to the Word object going down
        # self.visited = False      # Useful for solving algorithms

    def is_black(self):
        """Return True if the cell is fillable (not black)."""
        return not self.is_white

    def is_head(self):
        return self.is_beginning
    
    # Cell, int
    def add_clue(self, num):
        self.clue_number.append(num)

    def add_clues(self, nums):
        self.clue_number + nums

    def set_down(self):
        self.is_down = True
    
    def set_across(self):
        self.is_across = True
    
    def getLeft(self):
        return self.col * CELL_SIZE + 1
    
    def getTop(self):
        return self.row * CELL_SIZE + 1

    def __repr__(self):
        """Readable string for debugging."""
        if self.is_white:
            return f"{"H " if self.is_beginning else ''}{" ".join(self.clue_number)}, {self.next_across_clue} {self.next_down_clue}"
        else:
            return f"."


# CONSTANT
CELL_SIZE = 36

# PREAMBLES
# - html headers, css
html_preamble = r"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN"
"http://www.w3.org/TR/REC-html40/loose.dtd">
<html>
<!-- Created by Qxw 20200708 http://www.quinapalus.com -->
<head>
<title>Crossword</title>
<meta http-equiv="Content-Type" content="text/html;charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style type="text/css">
div.bk {position:absolute;font-size:0px;border-left:black 0px solid;border-right:black 0px solid;border-top:black 36px solid;border-bottom:black 0px solid;width:36px;height:36px;}
div.nu {position:absolute;font-size:12px;font-family:sans-serif;width:32px;height:32px;pointer-events:none;z-index:20;}
div.hr {position:absolute;font-size:0px;border-top:black 1px solid;pointer-events:none;}
div.vr {position:absolute;font-size:0px;border-left:black 1px solid;pointer-events:none;}
input.cell {
    position: absolute;
    width: 36px;
    height: 36px;
    font-size: 20px;
    text-transform: uppercase;
    text-align: center;
    border: 0.5px solid #000;
    background: white;
    outline: none;
    z-index: 10;
    padding: 0;
}
input.cell:focus {
    outline: 2px solid #0078d7;
    z-index: 15;
}

.clues {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 20px;
    font-family: Arial, sans-serif;
}

.crossword-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 20px;
    box-sizing: border-box;
}

.crossword-content {
  display: flex;
  flex-direction: column;
  align-items: center;
}

#clue-display {
    background: #f0f0f0;
    padding: 10px;
    margin-bottom: 10px;
    font-weight: bold;
    border-left: 5px solid #333;
    height: 10vh;
    width: 541px; /* Same width as crossword grid */
    overflow-y: auto;
    display: flex;
    align-items: center;
    box-sizing: border-box;
}

.clues-column {
    flex: 1;
    max-width: 400px;
    max-height: 35vh;
    display: flex;
    flex-direction: column;
    width: auto;
    font-family: Arial, sans-serif;
    overflow: hidden;
}

.clues-section {
    display: flex;
    justify-content: center;
    gap: 40px;
    padding: 20px;
    box-sizing: border-box;
    max-height: 35vh;
}

.clues-column h3 {
    text-align: center;
    margin: 0 0 10px 0;
    font-weight: bold;
    border-bottom: 1px solid #333;
    padding-bottom: 5px;
    flex-shrink: 0;
}

.clues-list {
    overflow-y: auto;
    flex: 1;
}

.clues-column div {
    padding: 6px 0;
    /* border-bottom: 1px dotted #ccc; */
}

.clues-list .clue {
    padding: 6px 0;
}

.crossword-grid {
    /* width set dynamically by scaleGrid() */
    overflow: visible;
}

.cell.active {
  background-color: #ffe58a;
}

#clue-display {
    background: #f0f0f0;
    padding: 10px;
    margin-bottom: 10px;
    font-weight: bold;
    border-left: 5px solid #333;
    height: 60px;
    width: 100%;
    overflow-y: auto;
    display: flex;
    align-items: center;
}

.container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

body {
  margin: 0;
  padding: 0;
}

@media (max-width: 600px) {
  .clues-section {
    flex-direction: column;
    max-height: none;
    gap: 0;
    padding: 10px;
  }

  .clues-column {
    max-width: 100%;
    max-height: 15vh;
  }

  .crossword-wrapper {
    padding: 10px;
  }
}

</style>
</head>
<body>
<center>
<div class="container">
    """


def javascript_postamble(labelled_across, labelled_down, cluesFile):
  vars = f"""
  let currentClue = '{labelled_across[0]}';
  let currentDirection = 'across';
  let labelled_across = {labelled_across};
  let labelled_down = {labelled_down};
  """

  cluesMap = generate_clue_map(cluesFile)

  script = r"""
  </div>
  </center>
  <script>
  // Store data in memory instead of localStorage
  const cellData = {};

  // Highlight colors
  const HIGHLIGHT_COLOR = '\#fffac2';
  const HOVER_COLOR = '\#f5f5f5';

  // Set initial current direction
  """ 

  post_script = r"""
  function updateClueDisplay(clueId) {
    const display = document.getElementById('clue-display');
    if (display && clueTexts[clueId]) {
      const direction = clueId.endsWith('a') ? 'A' : 'D';
      const clueText = clueTexts[clueId];
      const myArray = clueText.split(". ");
      display.innerHTML = `<strong>${clueId}</strong>: ${myArray[1]}`;
    }
  }

  function highlightClueInSidebar(clueId) {
    // Remove all previous highlights
    document.querySelectorAll('.clue').forEach(el => {
      el.style.backgroundColor = '';
      el.style.fontWeight = '';
    });
    
    // Highlight the active clue
    const clueElement = document.querySelector(`.clue[data-clue="${clueId}"]`);
    if (clueElement) {
      clueElement.style.backgroundColor = HIGHLIGHT_COLOR;
      clueElement.style.fontWeight = 'bold';
      // Scroll into view smoothly
      clueElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function getHeadCell(clue_num) {
    const cells = document.querySelectorAll('input.cell');
    const matchingCells = Array.from(cells).filter(c => 
      c.dataset.clue.includes(clue_num)
    );
    
    if (matchingCells.length === 0) return null;
    
    // Sort by top first, then by left (top-leftmost)
    matchingCells.sort((a, b) => {
      const topDiff = parseInt(a.style.top) - parseInt(b.style.top);
      if (topDiff !== 0) return topDiff;
      return parseInt(a.style.left) - parseInt(b.style.left);
    });
    
    return matchingCells[0];
  }

  function genNextCell(allCells, cell, direction) {
    const thisLeft = parseInt(cell.style.left);
    const thisTop = parseInt(cell.style.top);

    let next;
    if (direction === 'across') {
      next = allCells.find(c => 
        Math.abs(parseInt(c.style.top) - thisTop) < 5 && 
        parseInt(c.style.left) > thisLeft && 
        parseInt(c.style.left) <= thisLeft + 40
      );
    } else {
      next = allCells.find(c => 
        Math.abs(parseInt(c.style.left) - thisLeft) < 5 && 
        parseInt(c.style.top) > thisTop && 
        parseInt(c.style.top) <= thisTop + 40
      );
    }

    if (!next) {
      const nextClueId = getAndSetNextClue(cell);
      return getHeadCell(nextClueId);
    }

    return next;
  }

  function getAndSetNextClue(curCell) {
    let next;
    if (currentDirection === 'across') {
      next = curCell.dataset.nextAClue;
    } else {
      next = curCell.dataset.nextDClue;
    }

    if (!next || next === 'None') {
      if (currentDirection === 'across') {
        currentDirection = 'down';
        next = labelled_down[0];
      } else {
        currentDirection = 'across';
        next = labelled_across[0];
      }
    }
    
    currentClue = next;
    return next;
  }

  function genPrevCell(allCells, cell, direction) {
    const thisLeft = parseInt(cell.style.left);
    const thisTop = parseInt(cell.style.top);

    if (direction === 'across') {
      const rowCells = allCells
        .filter(c => Math.abs(parseInt(c.style.top) - thisTop) < 5)
        .sort((a, b) => parseInt(a.style.left) - parseInt(b.style.left));

      for (let i = rowCells.length - 1; i >= 0; i--) {
        if (parseInt(rowCells[i].style.left) < thisLeft) {
          return rowCells[i];
        }
      }
    }

    if (direction === 'down') {
      const colCells = allCells
        .filter(c => Math.abs(parseInt(c.style.left) - thisLeft) < 5)
        .sort((a, b) => parseInt(a.style.top) - parseInt(b.style.top));

      for (let i = colCells.length - 1; i >= 0; i--) {
        if (parseInt(colCells[i].style.top) < thisTop) {
          return colCells[i];
        }
      }
    }
    return null;
  }

  function setActiveClue(cell) {
    // Clear ALL highlights from grid cells
    const cells = document.querySelectorAll('input.cell');
    cells.forEach(c => {
      c.classList.remove('active');
      c.style.backgroundColor = '';
      c.style.fontWeight = '';
    });

    const clues = cell.dataset.clue.split(',').map(s => s.trim());

    // Determine which clue should be active based on current direction
    let activeClue;
    if (currentDirection === 'across') {
      activeClue = clues.find(c => c.endsWith('a'));
      if (!activeClue) {
        activeClue = clues.find(c => c.endsWith('d'));
        currentDirection = 'down';
      }
    } else {
      activeClue = clues.find(c => c.endsWith('d'));
      if (!activeClue) {
        activeClue = clues.find(c => c.endsWith('a'));
        currentDirection = 'across';
      }
    }

    if (activeClue) {
      currentClue = activeClue;
      
      // Highlight all cells in this clue using inline styles
      cells.forEach(c => {
        const cClues = c.dataset.clue.split(',').map(s => s.trim());
        if (cClues.some(clue => clue === activeClue)) {
          c.style.backgroundColor = HIGHLIGHT_COLOR;
        }
      });
      
      // Update clue display and sidebar
      updateClueDisplay(activeClue);
      highlightClueInSidebar(activeClue);
    }
  }

  // Get all input cells and set up event listeners
  const cells = document.querySelectorAll('input.cell');
  cells.forEach((cell, index) => {
    const key = 'cell_' + index;
    
    // Restore value from memory if it exists
    if (cellData[key]) {
      cell.value = cellData[key];
    }
    
    cell.addEventListener('input', () => {
      // Keep only the last character typed, uppercased (handles overwriting too)
      const letter = cell.value.slice(-1).toUpperCase();
      cell.value = /^[A-Z]$/.test(letter) ? letter : '';
      cellData[key] = cell.value;

      if (cell.value) {
        const next = genNextCell(Array.from(cells), cell, currentDirection);
        if (next) next.focus();
      }
    });

    // Click to focus and set direction
    cell.addEventListener('click', (e) => {
      const clues = cell.dataset.clue.split(',').map(s => s.trim());
      
      // NYT behavior: if clicking on already focused cell with multiple clues, toggle direction
      if (document.activeElement === cell && clues.length > 1) {
        currentDirection = currentDirection === 'across' ? 'down' : 'across';
      }
      
      // ALWAYS clear and re-highlight, even if already focused
      setActiveClue(cell);
    });

    cell.addEventListener('focus', () => {
      setActiveClue(cell);
    });
    
    // Navigate between cells with arrow keys
    cell.addEventListener('keydown', (e) => {
      const allCells = Array.from(cells);
      let nextCell = null;

      if (/^[a-z]$/i.test(e.key) && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        cell.value = e.key.toUpperCase();
        cellData[key] = cell.value;
        const next = genNextCell(Array.from(cells), cell, currentDirection);
        if (next) next.focus();
        return;
      }
      
      switch(e.key) {
        case ' ':
          e.preventDefault();
          // Toggle direction
          const clues = cell.dataset.clue.split(',').map(s => s.trim());
          if (clues.length > 1) {
            currentDirection = currentDirection === 'across' ? 'down' : 'across';
            setActiveClue(cell);
          }
          return;
        
        case 'Tab':
          e.preventDefault();
          if (e.shiftKey) {
            // Go to previous clue
            const clueList = currentDirection === 'across' ? labelled_across : labelled_down;
            const currentIndex = clueList.indexOf(currentClue);
            const prevClue = currentIndex > 0 ? clueList[currentIndex - 1] : clueList[clueList.length - 1];
            nextCell = getHeadCell(prevClue);
            currentClue = prevClue;
          } else {
            // Go to next clue
            nextClue = getAndSetNextClue(cell)
            nextCell = getHeadCell(nextClue);
          }
          break;
        
        case 'Enter':
          e.preventDefault();
          nextClue = getAndSetNextClue(cell)
          nextCell = getHeadCell(nextClue);
          break;
          
        case 'ArrowRight':
          e.preventDefault();
          nextCell = genNextCell(allCells, cell, 'across');
          currentDirection = 'across';
          break;
          
        case 'ArrowLeft':
          e.preventDefault();
          nextCell = genPrevCell(allCells, cell, 'across');
          currentDirection = 'across';
          break;
          
        case 'ArrowDown':
          e.preventDefault();
          nextCell = genNextCell(allCells, cell, 'down');
          currentDirection = 'down';
          break;
          
        case 'ArrowUp':
          e.preventDefault();
          nextCell = genPrevCell(allCells, cell, 'down');
          currentDirection = 'down';
          break;
          
        case 'Delete':
        case 'Backspace':
          e.preventDefault();
          if (cell.value) {
            // If cell has content, delete it
            cell.value = '';
            cellData[key] = '';
          } else {
            // If cell is empty, go to previous cell and delete
            nextCell = genPrevCell(allCells, cell, currentDirection);
            if (nextCell) {
              const prevKey = 'cell_' + allCells.indexOf(nextCell);
              nextCell.value = '';
              cellData[prevKey] = '';
            }
          }
          break;
      }
      
      if (nextCell) {
        nextCell.focus();
      }
    });
  });

  // Add click handlers to clue sidebar
  document.querySelectorAll('.clue').forEach(clueEl => {
    clueEl.addEventListener('click', () => {
      const clueId = clueEl.getAttribute('data-clue');
      if (clueId) {
        currentDirection = clueId.endsWith('a') ? 'across' : 'down';
        currentClue = clueId;
        const headCell = getHeadCell(clueId);
        if (headCell) {
          headCell.focus();
        }
      }
    });
    
    // Make clues hoverable for better UX
    clueEl.style.cursor = 'pointer';
    clueEl.addEventListener('mouseenter', () => {
      if (!clueEl.style.backgroundColor) {
        clueEl.style.backgroundColor = HOVER_COLOR;
      }
    });
    clueEl.addEventListener('mouseleave', () => {
      if (clueEl.style.backgroundColor === HOVER_COLOR) {
        clueEl.style.backgroundColor = '';
      }
    });
  });

  // Initialize with first cell
  const firstCell = getHeadCell(currentClue);
  firstCell.focus();
  updateClueDisplay(currentClue);
  setActiveClue(firstCell);

  function scaleGrid() {
    const nativeSize = 541;
    const padding = 32;
    const available = Math.min(window.innerWidth - padding, nativeSize);
    const scale = available / nativeSize;

    const gridOuter = document.querySelector('.crossword-grid');
    if (!gridOuter) return;
    const innerDiv = gridOuter.querySelector('div');
    innerDiv.style.transform = `scale(${scale})`;
    innerDiv.style.transformOrigin = 'top left';
    gridOuter.style.width = (nativeSize * scale) + 'px';
    gridOuter.style.height = (nativeSize * scale) + 'px';

    const content = document.querySelector('.crossword-content');
    if (content) content.style.width = (nativeSize * scale) + 'px';

    const clueDisplay = document.getElementById('clue-display');
    if (clueDisplay) clueDisplay.style.fontSize = Math.round(15 * scale) + 'px';
  }

  scaleGrid();
  window.addEventListener('resize', scaleGrid);

  </script>
  """
  return script + vars + cluesMap + post_script

# HELPER FUNCTIONS
# Helper function to extract top and left from style to use in cell generation
def extract_left_top(style):
    left  = re.search(r'left:(\d+px)', style)
    top   = re.search(r'top:(\d+px)', style)
    return (left.group(1), top.group(1))

# Convert left and top to int because both have px suffix
def convert_left_top_to_int(left, top):
    l = left.replace('px', '')
    t = top.replace('px', '')
    return int(l), int(t)

# All cells have class bk even if they are white cells
# White cells have a border containing #FFFFFF, 
# so any border-* means it is a white cell (fake black)
def is_white_cell(style):
    return "border-top:#FFFFFF" in style or "border-left:#FFFFFF" in style or \
           "border-right:#FFFFFF" in style or "border-bottom:#FFFFFF" in style

# Convert top and left to row and col of cell matrix
def top_left_to_row_col(top, left):
    row = top // CELL_SIZE
    col = left // CELL_SIZE
    return row, col

# Populate cell matrix with Cell data
def create_cell_matrix(cells, width, height):
    # cell_matrix = [[0 for x in range(width)] for y in range(height)]
    # left is the col, top is the row
    cell_matrix = [[0 for x in range(width + 1)] for y in range(height + 1)]
    for c in cells:
        style = c.get("style", "")
        left, top = extract_left_top(style)
        l, t = convert_left_top_to_int(left, top)
        col, row = top_left_to_row_col(l, t)
        is_white = is_white_cell(style)

        cell_matrix[row][col] = Cell(row, col, is_white)

    return cell_matrix

# Update cell matrix with data of start of words
def number_cell_matrix(cell_matrix, numbers):
    # PRE: All numbered cells are white and cell already exists in cell matrix
    heads = []
    across_clues = []
    down_clues = []
    for num in numbers:
        style = num.get("style", "")
        left, top = extract_left_top(style)
        number = num.text.strip()
        l, t = convert_left_top_to_int(left, top)
        row, col = top_left_to_row_col(t, l)
        cur = cell_matrix[row][col]
        max_row = len(cell_matrix) - 1
        max_col = len(cell_matrix[0]) - 1

        # Add across and down information FOR HEADS
        if (
            (row == 0 and not Cell.is_black(cell_matrix[row + 1][col])) or 
            (col == max_col and not Cell.is_black(cell_matrix[row + 1][col])) or 
            (row < max_row - 1 and (Cell.is_black(cell_matrix[row-1][col])) and not Cell.is_black(cell_matrix[row + 1][col])) # Cell.is_black(cell_matrix[row][col+1]) and Cell.is_black(cell_matrix[row][col-1]))
            ):
            cur.is_down = True
            Cell.add_clue(cur, f"{number}d")
            down_clues.append(int(number))

        if (
            (col == 0 and not Cell.is_black(cell_matrix[row][col+ 1])) or
            (row == max_row and not Cell.is_black(cell_matrix[row][col + 1])) or
            (col < max_col - 1 and (Cell.is_black(cell_matrix[row][col - 1])) and not Cell.is_black(cell_matrix[row][col+1])) # Cell.is_black(cell_matrix[row+1][col]) and Cell.is_black(cell_matrix[row][col-1]))
            ):
            cur.is_across = True
            Cell.add_clue(cur, f"{number}a")
            across_clues.append(int(number))
    
        cur.is_beginning = True
        cur.is_white = True
        heads.append(cur)

    return cell_matrix, heads, sorted(across_clues), sorted(down_clues),

def get_next_clue(curClue, list):
      i = list.index(curClue)
      if i == len(list) - 1:
          return list[0]
      else: 
        return list[i+1]

def directional_cell_matrix(cell_matrix, heads, across_clues, down_clues, labelled_across, labelled_down):
    max_row = len(cell_matrix) - 1
    max_col = len(cell_matrix[0]) - 1

    # every cell in heads is a beginning
    for head in heads:
        for clue in head.clue_number:
            if 'd' in clue:
                curr_row = head.row + 1
                current_num = int(clue[:-1])
                next_clue = get_next_clue(current_num, down_clues)
                # For head
                head.next_down_clue = f"{next_clue}d"

                if curr_row < max_row:
                    curr = cell_matrix[curr_row][head.col]
                    while (not Cell.is_black(curr) and curr_row <= max_row):
                        curr = cell_matrix[curr_row][head.col]
                        if clue not in curr.clue_number:
                          curr.add_clue(clue)
                        # For all following cells
                        curr.is_down = True
                        curr.next_down_clue = f"{next_clue}d"
                        curr_row += 1
            
            if 'a' in clue:
                curr_col = head.col + 1
                current_num = int(clue[:-1])
                next_clue = get_next_clue(current_num, across_clues)
                # For head
                head.next_across_clue = f"{next_clue}a"

                if curr_col < max_col:
                    curr = cell_matrix[head.row][curr_col]
                    while (not Cell.is_black(curr) and curr_col <= max_col):
                        curr = cell_matrix[head.row][curr_col]
                        if clue not in curr.clue_number:
                            curr.add_clue(clue)
                        # For all following cells
                        curr.is_across = True
                        curr.next_across_clue = f"{next_clue}a"
                        curr_col += 1

    return cell_matrix

def print_cell_matrix(cell_matrix, width=9):
    for row in cell_matrix:
        row_str = ""
        for cell in row:
            row_str += str(cell).ljust(width) + " | "
        print(row_str)

# Parse cells according to class
def generate_cells(cells, lines, numbers, directional_cell_matrix, across_clues, down_clues):
    cell_output = []
    cell_output.append(r"""
<div class="crossword-section">
    <div class="crossword-content">
      <div id="clue-display">
        Select a square to see the clue
      </div>
""")
    cell_output.append(f'<div class="crossword-grid">')
    cell_output.append(f'<div style="border-width:0px;width:541px;height:541px;position:relative;">')
    cell_output.append(f'<div style="border-width:0px;top:0px;left:0px;width:541px;height:541px;position:absolute;">')


    row_length = len(directional_cell_matrix)
    column_length = len(directional_cell_matrix[0])

    for row in range(row_length):
        for column in range(column_length):
            curCell = directional_cell_matrix[row][column]
            if curCell.is_white:
                clues = ",".join(curCell.clue_number)
                d = []
                if curCell.is_across: d.append("across")
                if curCell.is_down: d.append("down")
                direction = ",".join(d)
                cell_output.append(
                    f'<input class="cell" data-clue="{clues}" data-direction="{direction}" data-next-a-clue="{curCell.next_across_clue}" data-next-d-clue="{curCell.next_down_clue}" style="left:{Cell.getLeft(curCell)}px;top:{Cell.getTop(curCell)}px;">'
                )
            
            else: 
                cell_output.append(
                     f'<div class="bk" style="left:{Cell.getLeft(curCell)}px;top:{Cell.getTop(curCell)}px;"></div>'
                )

    for num in numbers:
        style = num.get("style", "")

        left, top = extract_left_top(style)

        number = num.text.strip()
        cell_output.append(
            f'<div class="nu" style="left:{left};top:{top};color:000000;text-align:left">{number}</div>'
        )

    # Default - we only change bk and nu
    cell_output.extend(lines)

    cell_output.append(f'</div></div></div></div></div>')
    return cell_output

#
# Clues helper functions
#

def clues_section_generator(across_clues, down_clues):
    clues_section = []
    clues_section.append(f'<div class="clues-section">')
    clues_section.extend(across_clues_generator(across_clues))
    clues_section.extend(down_clues_generator(down_clues))
    clues_section.append(f'</div>')

    return clues_section

def across_clues_generator(across_clues):
    across_clues_ = []
    across_clues_.append(f'<div class="clues-column">')
    across_clues_.append(f'<h3>Across</h3>')
    across_clues_.append(f'<div class="clues-list">')

    for c in range(len(across_clues)):
        clue = across_clues[c]
        split = clue.split('.')
        clue_num = int(split[0])
        clue_ = f'<div class="clue" data-clue="{clue_num}a">{clue}</div>'
        across_clues_.append(clue_)

    across_clues_.append(f'</div>')
    across_clues_.append(f'</div>')
    return across_clues_

def down_clues_generator(down_clues):
    down_clues_ = []
    down_clues_.append(f'<div class="clues-column">')
    down_clues_.append(f'<h3>Down</h3>')
    down_clues_.append(f'<div class="clues-list">')

    for c in range(len(down_clues)):
        clue = down_clues[c]
        split = clue.split('.')
        clue_num = int(split[0])
        clue_ = f'<div class="clue" data-clue="{clue_num}d">{clue}</div>'
        down_clues_.append(clue_)
    down_clues_.append(f'</div>')
    down_clues_.append(f'</div>')

    return down_clues_

def extract_clues(cluesfile, across_clues, down_clues):
    with open(cluesfile, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]  # remove empty lines
    
    mode = None  # None, "across", or "down"
    for line in lines:
        if line.lower() == "across":
            mode = "across"
            continue
        elif line.lower() == "down":
            mode = "down"
            continue

        if mode == "across":
            across_clues.append(line)
        elif mode == "down":
            down_clues.append(line)

def generate_clue_map(cluesfile):
  with open(cluesfile, "r", encoding="utf-8") as f:
      lines = [line.strip() for line in f if line.strip()]
  
  across_clues = []
  down_clues = []
  mode = None
  
  for line in lines:
      if line.lower() == "across":
          mode = "across"
          continue
      elif line.lower() == "down":
          mode = "down"
          continue
      
      if mode == "across":
          across_clues.append(line)
      elif mode == "down":
          down_clues.append(line)
  
  # Generate JavaScript object
  js_lines = ["const clueTexts = {"]
  
  # Process across clues
  for clue in across_clues:
      # Extract number from clue (e.g., "1. Text..." -> "1")
      clue_num = clue.split('.')[0].strip()
      # Escape single quotes in the clue text
      escaped_clue = clue.replace("'", "\\'")
      js_lines.append(f"  '{clue_num}a': '{escaped_clue}',")
  
  # Process down clues
  for clue in down_clues:
      clue_num = clue.split('.')[0].strip()
      escaped_clue = clue.replace("'", "\\'")
      js_lines.append(f"  '{clue_num}d': '{escaped_clue}',")
  
  # Remove trailing comma from last line
  if js_lines[-1].endswith(','):
      js_lines[-1] = js_lines[-1][:-1]
  
  js_lines.append("};")
  
  return '\n'.join(js_lines)

def label_clues_list(across_clues, down_clues):
    labelled_across = []
    labelled_down = []
    assert(isinstance(across_clues, list))
    assert(isinstance(down_clues, list))
    for a in across_clues:
        labelled_across.append(f'{a}a')
    for d in down_clues: 
        labelled_down.append(f'{d}d')

    return labelled_across, labelled_down

def main():
    if len(sys.argv) != 4:
        print("Usage: python htmlconvert.py input.html clues.txt output.html")
        sys.exit(1)

    infile = sys.argv[1]
    cluesfile = sys.argv[2]
    outfile = sys.argv[3]

    across_clues = []
    down_clues = []
    across_clues_list = []
    down_clues_list = []

    extract_clues(cluesfile, across_clues_list, down_clues_list)

    with open(infile, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "lxml")

    cells = soup.select("div.bk")
    numbers = soup.select("div.nu")
    lines = (str(tag) for tag in soup.select("div.hr, div.vr"))
    left, top = extract_left_top(cells[-1].get("style", ""))

    # Crossword's width and height
    # Width = number of cells in a row - 1, same for height ????
    left_val, top_val = convert_left_top_to_int(left, top)
    width, height = top_left_to_row_col(left_val, top_val)

    cell_matrix = create_cell_matrix(cells, width, height)
    numbered_cell_matrix, heads, across_clues, down_clues = number_cell_matrix(cell_matrix, numbers)
    labelled_across, labelled_down = label_clues_list(across_clues, down_clues)
    dir_cell_matrix = directional_cell_matrix(numbered_cell_matrix, heads, across_clues, down_clues, labelled_across, labelled_down)

    # To be used in js for next clue detection

    output = []

    # Preambles
    output.append(html_preamble)

    # Crosswsord grid
    output.extend(generate_cells(cells, lines, numbers, dir_cell_matrix, across_clues, down_clues))

    # Clues generator
    output.extend(clues_section_generator(across_clues_list, down_clues_list))

    # Postamble
    output.append(javascript_postamble(labelled_across, labelled_down, cluesfile))
    output.append("</body> \n</html>")

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Done:", outfile)


if __name__ == "__main__":
    main()
