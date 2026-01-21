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
            return f"{"H " if self.is_beginning else ''}{" ".join(self.clue_number)}"
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
    e.target.value = e.target.value.toUpperCase();
    cellData[key] = e.target.value;
  });
  
  // Navigate between cells with arrow keys
  cell.addEventListener('keydown', (e) => {
    const allCells = Array.from(cells);
    const currentIndex = allCells.indexOf(cell);
    
    let nextCell = null;
    
    switch(e.key) {
      case 'ArrowRight':
        nextCell = allCells[currentIndex + 1];
        break;
      case 'ArrowLeft':
        nextCell = allCells[currentIndex - 1];
        break;
      case 'ArrowDown':
        // Find cell roughly below (36px down)
        const belowCells = allCells.filter(c => {
          const thisLeft = parseInt(cell.style.left);
          const thisTop = parseInt(cell.style.top);
          const cLeft = parseInt(c.style.left);
          const cTop = parseInt(c.style.top);
          return Math.abs(cLeft - thisLeft) < 5 && cTop > thisTop;
        });
        nextCell = belowCells[0];
        break;
      case 'ArrowUp':
        // Find cell roughly above
        const aboveCells = allCells.filter(c => {
          const thisLeft = parseInt(cell.style.left);
          const thisTop = parseInt(cell.style.top);
          const cLeft = parseInt(c.style.left);
          const cTop = parseInt(c.style.top);
          return Math.abs(cLeft - thisLeft) < 5 && cTop < thisTop;
        });
        nextCell = aboveCells[aboveCells.length - 1];
        break;
    }
    
    if (nextCell && ['ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
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

        if (
            col == 0 or
            row == max_row or
            (col < max_col - 1 and (Cell.is_black(cell_matrix[row][col - 1])) and not Cell.is_black(cell_matrix[row][col+1])) # Cell.is_black(cell_matrix[row+1][col]) and Cell.is_black(cell_matrix[row][col-1]))
            ):
            cur.is_across = True
            Cell.add_clue(cur, f"{number}a")
    
        # Cell.add_clue(cur, f"{number}{'a' if cur.is_across else ''}{'d' if cur.is_down else ''}")
        cur.is_beginning = True
        cur.is_white = True
        heads.append(cur)

    return cell_matrix, heads

# Update cell matrix to include clue number and direction of word
# i.e. if a cell belongs to a 'down' or an 'across' word
# this is for word highlighting and auto next letter
# Search cell matrix for 'beginning of words' and follow in the direction of
# until it reaches a black cell or the end of the crossword and label with 
# clue number and direction
# def directional_cell_matrix(cell_matrix):
#     # Use actual matrix dimensions to iterate safely
#     rows = len(cell_matrix)
#     cols = len(cell_matrix[0]) if rows > 0 else 0

#     for r in range(rows):
#         for c in range(cols):
#             cur = cell_matrix[r][c]
#             # Skip empty slots or non-Cell entries
#             if not isinstance(cur, Cell):
#                 continue

#             # Skip black cells
#             if Cell.is_black(cur):
#                 continue

#             # If this cell is a head, propagate its clue string to the word
#             if cur.is_head():
#                 head_clue = cur.clue_number[0] if cur.clue_number else None

#                 # Across: move right until a non-white cell or boundary
#                 # Will only be across if 
#                 # - left cell is black / does not exist
#                 # - right cell is white
#                 cc = c + 1
#                 while cc < cols and isinstance(cell_matrix[r][cc], Cell) and cell_matrix[r][cc].is_white:
#                     if head_clue is not None:
#                         cell_matrix[r][cc].add_clue(head_clue)
#                     cell_matrix[r][cc].set_across()
#                     cc += 1

#                 # Down: move down until a non-white cell or boundary
#                 rr = r + 1
#                 while rr < rows and isinstance(cell_matrix[rr][c], Cell) and cell_matrix[rr][c].is_white:
#                     if head_clue is not None:
#                         cell_matrix[rr][c].add_clue(head_clue)
#                     cell_matrix[rr][c].set_down()
#                     rr += 1

#     return cell_matrix

def directional_cell_matrix(cell_matrix, width, height, heads):
    max_row = len(cell_matrix) - 1
    max_col = len(cell_matrix[0]) - 1
    # every cell in heads is a beginning
    for head in heads:
        for clue in head.clue_number:
            if 'd' in clue:
                curr_row = head.row + 1
                if curr_row < max_row:
                    curr = cell_matrix[curr_row][head.col]
                    while (not Cell.is_black(curr) and curr_row <= max_row):
                        curr = cell_matrix[curr_row][head.col]
                        if clue not in curr.clue_number:
                            curr.add_clue(clue)
                        curr_row += 1
            
            if 'a' in clue:
                curr_col = head.col + 1
                if curr_col < max_col:
                    curr = cell_matrix[head.row][curr_col]
                    while (not Cell.is_black(curr) and curr_col <= max_col):
                        curr = cell_matrix[head.row][curr_col]
                        if clue not in curr.clue_number:
                            curr.add_clue(clue)
                        curr_col += 1

    return cell_matrix


    # for row in range(width + 1):
    #     for col in range(height + 1):
    #         cur = cell_matrix[row][col]
    #         clue_numbers = cur.clue_number

    #         # PRE: Heads of words can only have one clue number 
    #         # (crossword cells never contain more than one number - they share the same number)??
    #         # However cells can belong to more than one clue word
    #         if Cell.is_head(cur):
    #             curr = cell_matrix[row][col]

    #             # While loops:
    #             # Iteratively assigns clue number and direction until reaches
    #             # a black space or the boundary

    #             # Across
    #             while (curr.is_white and col < width):
    #                 col += 1
    #                 curr = cell_matrix[row][col]
    #                 Cell.add_clues(curr, clue_numbers)
    #                 Cell.set_across(curr)
                
    #             # Down
    #             while (curr.is_white and row < height):
    #                 row += 1
    #                 curr = cell_matrix[row][col]
    #                 Cell.add_clues(curr, clue_numbers)
    #                 Cell.set_down(curr)

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
            print(f"row: {row}, col: {column}, {curCell.is_white}")
            if curCell.is_white:
                clues = ",".join(curCell.clue_number)
                d = []
                if curCell.is_across: d.append("across")
                if curCell.is_down: d.append("down")
                direction = ",".join(d)
                cell_output.append(
                    f'<input class="cell" data-clue="{clues}" data-direction="{direction}" style="left:{Cell.getLeft(curCell)};top:{Cell.getTop(curCell)};" maxlength="1">'
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

def across_clues_generator(across_clues):
    across_clues_ = []
    across_clues_.append(f'<div class="clues-column", style="padding-left: 3%">')
    across_clues_.append(f'<h3>Across</h3>')

    for clue in across_clues:
        clue = f'<div>{clue}</div>'
        across_clues_.append(clue)

    across_clues_.append(f'</div>')
    return across_clues_

def down_clues_generator(down_clues):
    down_clues_ = []
    down_clues_.append(f'<div class="clues-column">')
    down_clues_.append(f'<h3>Down</h3>')
    for clue in down_clues:
        clue = f'<div>{clue}</div>'
        down_clues_.append(clue)
    down_clues_.append(f'</div>')

    return down_clues_


def main():
    if len(sys.argv) != 4:
        print("Usage: python htmlconvert.py input.html clues.txt output.html")
        sys.exit(1)

    infile = sys.argv[1]
    cluesfile = sys.argv[2]
    outfile = sys.argv[3]

    across_clues = []
    down_clues = []

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
    numbered_cell_matrix, heads = number_cell_matrix(cell_matrix, numbers)

    dir_cell_matrix = directional_cell_matrix(numbered_cell_matrix, width, height, heads)
    print_cell_matrix(dir_cell_matrix)


    output = []

    # Preambles
    output.append(html_preamble)

    # Across clues
    output.extend(across_clues_generator(across_clues))

    # Crosswsord grid
    output.append(cell_preamble)
    output.extend(generate_cells(cells, lines, numbers, dir_cell_matrix))

    # Down clues
    output.extend(down_clues_generator(down_clues))

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
