import numpy as np
from gridgame import *

game = ShapePlacementGrid(GUI=False, render_delay_sec=0.5, gs=6, num_colored_boxes=5)
shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')
np.savetxt('initial_grid.txt', grid, fmt="%d")

##############################################################################################################################

# Initialization

# shapePos is the current position of the brush.

# currentShapeIndex is the index of the current brush type being placed (order specified in gridgame.py).

# currentColorIndex is the index of the current color being placed (order specified in gridgame.py).

# grid represents the current state of the board. 
    
    # -1 indicates an empty cell
    # 0 indicates a cell colored in the first color (indigo by default)
    # 1 indicates a cell colored in the second color (taupe by default)
    # 2 indicates a cell colored in the third color (veridian by default)
    # 3 indicates a cell colored in the fourth color (peach by default)

# placedShapes is a list of shapes that have currently been placed on the board.
    
    # Each shape is represented as a list containing three elements: a) the brush type (number between 0-8), 
    # b) the location of the shape (coordinates of top-left cell of the shape) and c) color of the shape (number between 0-3)

    # For instance [0, (0,0), 2] represents a shape spanning a single cell in the color 2=veridian, placed at the top left cell in the grid.

# done is a Boolean that represents whether coloring constraints are satisfied. Updated by the gridgames.py file.

##############################################################################################################################

shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')

print(shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done)

# check if shape covers any empty cells
def covers_empty_cell(grid, shape, pos):
    for i, row in enumerate(shape):
        for j, cell in enumerate(row):
            if cell and grid[pos[1] + i, pos[0] + j] == -1:
                return True
    return False

def count_shapes(placedShapes):
    return len(placedShapes)

def count_empty_cells(grid):
    return np.sum(grid == -1)

def count_conflicts(grid):
    conflicts = 0
    gs = grid.shape[0]
    #iterate over every cell
    for y in range(gs):
        for x in range(gs):
            #skip if cell is empty
            if grid[y, x] == -1:
                continue
            #check if current cell is equal to cell on right
            if x + 1 < gs and grid[y, x] == grid[y, x + 1]:
                conflicts += 1
            #check if current cell is equal to cell below
            if y + 1 < gs and grid[y, x] == grid[y + 1, x]:
                conflicts += 1

    return conflicts

#Create score based on objectives
def objective(grid, placedShapes):
    empty_penalty = count_empty_cells(grid)
    conflict_penalty = count_conflicts(grid)

    if empty_penalty == 0:
        shape_penalty = len(placedShapes)
    else:
        shape_penalty = 0

    return (
        -20 * empty_penalty
        -50 * conflict_penalty
        -1 * shape_penalty
    )
    
no_improve_steps = 0
MAX_NO_IMPROVE = 100
actions = ['switchshape','switchcolor','right','left','down','up','place','place','place']
try:
    while not done:
        action = random.choice(actions)
        prev_score = objective(grid, placedShapes)
        if action == 'place':
            if game.canPlace(grid, game.shapes[currentShapeIndex], shapePos):
                (shapePos,currentShapeIndex,currentColorIndex,grid,placedShapes,done,) = game.execute('place')
            else:
                no_improve_steps += 1
                continue
        else:
            (shapePos,currentShapeIndex,currentColorIndex,grid,placedShapes,done,) = game.execute(action)
            
        curr_score = objective(grid, placedShapes)
        
        if curr_score>prev_score:
            no_improve_steps = 0
        elif curr_score == prev_score and random.random() < 0.2:
            no_improve_steps = 0
        else:
            print("Previous score", prev_score)
            print("Current score", curr_score)
            (shapePos,currentShapeIndex,currentColorIndex,grid,placedShapes,done,) = game.execute('undo')
            no_improve_steps +=1
        if no_improve_steps > MAX_NO_IMPROVE:
            print("Stuck → forcing exploration")
            game.execute('switchshape')
            game.execute('switchcolor')
            no_improve_steps = 0
except KeyboardInterrupt:
    print("\nExecution interrupted by user. Exiting cleanly.")

np.savetxt('grid.txt', grid, fmt="%d")
with open("shapes.txt", "w") as outfile:
    outfile.write(str(placedShapes))