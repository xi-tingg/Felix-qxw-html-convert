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
    gap: 40px;
    margin: 0 auto;
    padding: 10px;
    box-sizing: border-box;
}

.clues-column {
    display: flex;
    flex-direction: column;
    width: auto;
    font-family: Arial, sans-serif;
}

.clues-column h3 {
    text-align: center;
    margin-bottom: 10px;
    font-weight: bold;
    border-bottom: 1px solid #333;
    padding-bottom: 5px;
}

.clues-column div {
    padding: 6px 0;
    /* border-bottom: 1px dotted #ccc; */
}

.crossword-grid {
    width: 500px;
}

.cell.active {
  background-color: #ffe58a;
}

</style>
</head>
<body>
<center>

<div class="crossword-wrapper">
    """

cell_preamble = r"""<div class="crossword-grid">
<div style="border-width:0px;width:541px;height:541px;position:relative;">
<div style="border-width:0px;top:0px;left:0px;width:541px;height:541px;position:absolute;">"""

javascript_postamble = r"""<script>
// Store data in memory instead of localStorage
const cellData = {};

// Set initial current direction
let currentDirection = 'across';

function genNextCell(allCells, cell, curDirection) {
  const thisLeft = parseInt(cell.style.left);
  const thisTop = parseInt(cell.style.top);
  
  if (curDirection === 'across') {
    const rowCells = allCells
      .filter(c => Math.abs(parseInt(c.style.top) - thisTop) < 5)
      .sort((a, b) => parseInt(a.style.left) - parseInt(b.style.left));

    for (let c of rowCells) {
      if (parseInt(c.style.left) > thisLeft) return c;
    }
  } else if (curDirection === 'down') {
    // Find next cell in same column, below
    const colCells = allCells
      .filter(c => Math.abs(parseInt(c.style.left) - thisLeft) < 5)
      .sort((a, b) => parseInt(a.style.top) - parseInt(b.style.top));

    for (let c of colCells) {
      if (parseInt(c.style.top) > thisTop) return c;
    }
  }

  return null;
}

function genPrevCell(allCells, cell, direction) {
  const thisLeft = parseInt(cell.style.left);
  const thisTop = parseInt(cell.style.top);

  if (direction === 'across') {
    // same row, to the left
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
    // same column, above
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


// Get all input cells and set up event listeners
const cells = document.querySelectorAll('input.cell');
cells.forEach((cell, index) => {
  const key = 'cell_' + index;
  
  // Restore value from memory if it exists
  if (cellData[key]) {
    cell.value = cellData[key];
  }
  
  // Save input to memory and auto-uppercase
  cell.addEventListener('input', (e) => {
    e.target.value = e.target.value.toUpperCase(); // optional uppercase

    // only move if the cell is filled
    if (cell.value.length >= cell.maxLength) {
      const allCells = Array.from(cells);
      const i = allCells.indexOf(cell);
      let nextCell = null;

      if (currentDirection === 'across') {
        nextCell = allCells[i + 1]; // move right
      } else { // down
        const thisLeft = parseInt(cell.style.left);
        const thisTop = parseInt(cell.style.top);
        nextCell = allCells.find(c =>
          parseInt(c.style.left) === thisLeft && parseInt(c.style.top) > thisTop
        );
      }

      if (nextCell) nextCell.focus();
    }
  });

  cell.addEventListener('focus', () => {
    cells.forEach(c => c.classList.remove('active'));

    const clues = cell.dataset.clue.split(',').map(s => s.trim());

    // If current direction not available, auto-switch
    if (
      currentDirection === 'across' &&
      !clues.some(c => c.endsWith('a'))
    ) {
      currentDirection = 'down';
    }
    if (
      currentDirection === 'down' &&
      !clues.some(c => c.endsWith('d'))
    ) {
      currentDirection = 'across';
    }

    const activeClue =
      currentDirection === 'down'
        ? clues.find(c => c.endsWith('d'))
        : clues.find(c => c.endsWith('a'));

    cells.forEach(c => {
      const cClues = c.dataset.clue.split(',').map(s => s.trim());
      if (cClues.includes(activeClue)) {
        c.classList.add('active');
      }
    });
  });
  
  // Navigate between cells with arrow keys
  cell.addEventListener('keydown', (e) => {
    e.target.value = e.target.value.toUpperCase();
    const allCells = Array.from(cells);
    const currentIndex = allCells.indexOf(cell);
    
    let nextCell = null;
    
    switch(e.key) {
      case ' ':
        e.preventDefault();
        currentDirection = currentDirection === 'across' ? 'down' : 'across';
        cell.blur();
        cell.focus(); // re-trigger highlighting
        return;
      
      case 'Enter':
        e.preventDefault();
        nextCell = genNextCell(allCells, cell, currentDirection);
        break
      case 'ArrowRight':
        nextCell = genNextCell(allCells, cell, 'across');
        break;
      case 'ArrowLeft':
        nextCell = genPrevCell(allCells, cell, 'across');
        break;
      case 'ArrowDown':
        nextCell = genNextCell(allCells, cell, 'down');
        break;
      case 'ArrowUp':
        nextCell = genPrevCell(allCells, cell, 'down');
        break;
      case 'Delete':
      case 'Backspace':
        cell.value = ''
        nextCell = genPrevCell(allCells, cell, currentDirection)
      }
    
    if (nextCell && ['Enter', 'ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown', 'Delete', 'Backspace'].includes(e.key)) {
      e.preventDefault();
      nextCell.focus();
    }
  });
});
</script>
"""

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

        # Add across and down information
        if (
            row == 0 or 
            col == max_col or 
            (row < max_row - 1 and (Cell.is_black(cell_matrix[row-1][col])) and not Cell.is_black(cell_matrix[row + 1][col])) # Cell.is_black(cell_matrix[row][col+1]) and Cell.is_black(cell_matrix[row][col-1]))
            ):
            cur.is_down = True
            Cell.add_clue(cur, f"{number}d")
            down_clues.append(int(number))

        if (
            col == 0 or
            row == max_row or
            (col < max_col - 1 and (Cell.is_black(cell_matrix[row][col - 1])) and not Cell.is_black(cell_matrix[row][col+1])) # Cell.is_black(cell_matrix[row+1][col]) and Cell.is_black(cell_matrix[row][col-1]))
            ):
            cur.is_across = True
            Cell.add_clue(cur, f"{number}a")
            across_clues.append(int(number))
    
        cur.is_beginning = True
        cur.is_white = True
        heads.append(cur)

    return cell_matrix, heads, sorted(across_clues), sorted(down_clues),

def directional_cell_matrix(cell_matrix, heads, across_clues, down_clues):
    max_row = len(cell_matrix) - 1
    max_col = len(cell_matrix[0]) - 1

    # every cell in heads is a beginning
    for head in heads:
        for clue in head.clue_number:
            if 'd' in clue:
                curr_row = head.row + 1
                current_num = int(clue[:-1])
                next_clue = next((c for c in down_clues if int(c) > current_num), None)
                if curr_row < max_row:
                    curr = cell_matrix[curr_row][head.col]
                    while (not Cell.is_black(curr) and curr_row <= max_row):
                        curr = cell_matrix[curr_row][head.col]
                        if clue not in curr.clue_number:
                            curr.add_clue(clue)
                        if not next_clue == None:
                            curr.next_down_clue = f"{next_clue}d"
                        curr_row += 1
            
            if 'a' in clue:
                curr_col = head.col + 1
                current_num = int(clue[:-1])
                next_clue = next((c for c in across_clues if int(c) > current_num), None)
                if curr_col < max_col:
                    curr = cell_matrix[head.row][curr_col]
                    while (not Cell.is_black(curr) and curr_col <= max_col):
                        curr = cell_matrix[head.row][curr_col]
                        if clue not in curr.clue_number:
                            curr.add_clue(clue)
                        if not next_clue == None:
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
def generate_cells(cells, lines, numbers, directional_cell_matrix):
    cell_output = []

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
                    f'<input class="cell" data-clue="{clues}" data-direction="{direction}" data-next-a-clue="{curCell.next_across_clue}" data-next-d-clue="{curCell.next_down_clue}" style="left:{Cell.getLeft(curCell)};top:{Cell.getTop(curCell)};" maxlength="1">'
                )
            
            else: 
                cell_output.append(
                     f'<div class="bk" style="left:{Cell.getLeft(curCell)};top:{Cell.getTop(curCell)};"></div>'
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

    cell_output.append(f'</div></div></div>')
    return cell_output

#
# Clues helper functions
#

def across_clues_generator(across_clues):
    across_clues_ = []
    across_clues_.append(f'<div class="clues-column", style="padding-left: 3%">')
    across_clues_.append(f'<h3>Across</h3>')

    for c in range(len(across_clues)):
        clue = across_clues[c]
        split = clue.split('.')
        clue_num = int(split[0])
        clue_ = f'<div class="clue" data-clue="{clue_num}a">{clue}</div>'
        across_clues_.append(clue_)

    across_clues_.append(f'</div>')
    return across_clues_

def down_clues_generator(down_clues):
    down_clues_ = []
    down_clues_.append(f'<div class="clues-column">')
    down_clues_.append(f'<h3>Down</h3>')

    for c in range(len(down_clues)):
        clue = down_clues[c]
        split = clue.split('.')
        clue_num = int(split[0])
        clue_ = f'<div class="clue", data-clue="{clue_num}d">{clue}</div>'
        down_clues_.append(clue_)
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
    dir_cell_matrix = directional_cell_matrix(numbered_cell_matrix, heads, across_clues, down_clues)

    output = []

    # Preambles
    output.append(html_preamble)

    # Across clues
    output.extend(across_clues_generator(across_clues_list))

    # Crosswsord grid
    output.append(cell_preamble)
    output.extend(generate_cells(cells, lines, numbers, dir_cell_matrix))

    # Down clues
    output.extend(down_clues_generator(down_clues_list))

    output.append(f'</div>')
    output.append(f'</center>')

    # Postamble
    output.append(javascript_postamble)
    output.append("</body> \n</html>")

    with open(outfile, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

    print("Done:", outfile)


if __name__ == "__main__":
    main()
