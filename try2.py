import numpy as np
import random
from gridgame import *
import json

##############################################################################################################################

# You can visualize what your code is doing by setting the GUI argument in the following line to true.
# The render_delay_sec argument allows you to slow down the animation, to be able to see each step more clearly.

# For your final submission, please set the GUI option to False.

# The gs argument controls the grid size. You should experiment with various sizes to ensure your code generalizes.
# Please do not modify or remove lines 18 and 19.

##############################################################################################################################

game = ShapePlacementGrid(GUI=False, render_delay_sec=0.5, gs=6, num_colored_boxes=5)
shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')
np.savetxt('initial_grid.txt', grid, fmt="%d")

##############################################################################################################################

# Initialization

# shapePos is the current position of the brush.

# currentShapeIndex is the index of the current brush type being placed (order specified in gridgame.py, and assignment instructions).

# currentColorIndex is the index of the current color being placed (order specified in gridgame.py, and assignment instructions).

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
trace = {
    "meta": {
        "grid_size": game.gridSize,
        "colors": game.colors
    },
    "frames": []
}

def record_frame(action):
    shapePos, shapeIdx, colorIdx, grid, placedShapes, done = game.execute("export")
    trace["frames"].append({
        "action": action,
        "shape_pos": shapePos.copy(),
        "current_shape": int(shapeIdx),
        "current_color": int(colorIdx),
        "grid": grid.tolist()
    })

def count_empty_cells(grid):
    """Count the number of empty cells in the grid"""
    return np.sum(grid == -1)

def count_conflicts(grid):
    """Count the number of adjacent cells with the same color (excluding empty cells)"""
    conflicts = 0
    gs = grid.shape[0]
    for y in range(gs):
        for x in range(gs):
            if grid[y, x] == -1:
                continue
            # Check right neighbor
            if x + 1 < gs and grid[y, x + 1] != -1:
                if grid[y, x] == grid[y, x + 1]:
                    conflicts += 1
            # Check bottom neighbor
            if y + 1 < gs and grid[y + 1, x] != -1:
                if grid[y, x] == grid[y + 1, x]:
                    conflicts += 1
    return conflicts

def count_unique_colors(placedShapes):
    """Count the number of unique colors used"""
    if not placedShapes:
        return 0
    colors = set([shape[2] for shape in placedShapes])
    return len(colors)

def objective(grid, placedShapes):
    """
    Objective function for first-choice hill climbing.
    Higher score is better.
    
    Priority hierarchy (most important first):
    1. Minimize conflicts (adjacent same colors)
    2. Minimize empty cells (fill the grid)
    3. Minimize number of shapes used (only matters when grid is complete)
    4. Minimize number of colors used (only matters when grid is complete)
    """
    empty = count_empty_cells(grid)
    conflicts = count_conflicts(grid)
    num_shapes = len(placedShapes)
    num_colors = count_unique_colors(placedShapes)
    
    # Conflicts are catastrophic - must be eliminated first
    if conflicts > 0:
        return -100000 * conflicts - 100 * empty
    
    # If no conflicts, focus on filling empty cells
    if empty > 0:
        return -1000 * empty
    
    # If grid is complete and valid, minimize shapes and colors
    return -10 * num_shapes - num_colors

def generate_random_action():
    """
    Generate a random action.
    Heavily weight 'place' since that's what makes progress.
    """
    actions = ['up', 'down', 'left', 'right', 'switchshape', 'switchcolor']
    # Add 'place' multiple times to make it more likely
    actions.extend(['place'] * 5)
    return random.choice(actions)

# First-choice hill climbing with variants:
# - Sideways moves: Allow moves with equal score occasionally to escape plateaus
# - Random restart: If stuck, undo some moves and try different path

max_iterations = 100000
no_improvement_limit = 500
restart_limit = 5
restarts = 0

while not done and restarts < restart_limit:
    iterations = 0
    no_improvement_count = 0
    consecutive_failures = 0  # Track failed placement attempts
    
    while not done and iterations < max_iterations and no_improvement_count < no_improvement_limit:
        iterations += 1
        
        # Get current state and score
        current_score = objective(grid, placedShapes)
        
        # Generate a random action
        action = generate_random_action()
        
        # Track whether we actually modified the grid
        action_succeeded = False
        
        if action == 'place':
            # Only try to place if it's legal
            if game.canPlace(grid, game.shapes[currentShapeIndex], shapePos):
                shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('place')
                record_frame('place')
                action_succeeded = True
                consecutive_failures = 0
            else:
                # Can't place here - don't count as a move
                consecutive_failures += 1
                # If we've failed too many times, force a position change
                if consecutive_failures > 20:
                    # Move to a random position
                    for _ in range(random.randint(1, 5)):
                        move = random.choice(['up', 'down', 'left', 'right'])
                        shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute(move)
                        record_frame(move)
                    consecutive_failures = 0
                continue
        else:
            # Movement or switching action
            shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute(action)
            record_frame(action)
        
        # Only evaluate if we placed something (movements don't change the score)
        if action_succeeded:
            new_score = objective(grid, placedShapes)
            
            # First-choice hill climbing decision
            if new_score > current_score:
                # Accept - improvement found!
                no_improvement_count = 0
            elif new_score == current_score and random.random() < 0.1:
                # Sideways move - accept 10% of the time to help escape plateaus
                no_improvement_count = 0
            else:
                # Reject - undo the placement
                game.execute('undo')
                record_frame('undo')
                shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')
                no_improvement_count += 1
        # For non-placement actions, we don't increment no_improvement_count
        # since they're just exploring the action space
    
    # Check if we're stuck
    if not done and no_improvement_count >= no_improvement_limit:
        restarts += 1
        print(f"Stuck after {iterations} iterations. Restart {restarts}/{restart_limit}")
        print(f"Current state: {len(placedShapes)} shapes, {count_empty_cells(grid)} empty, {count_conflicts(grid)} conflicts")
        
        # Random restart: undo a portion of placed shapes
        undo_count = min(max(len(placedShapes) // 4, 5), len(placedShapes))
        for _ in range(undo_count):
            if placedShapes:
                game.execute('undo')
                record_frame('undo')
        
        # Get fresh state
        shapePos, currentShapeIndex, currentColorIndex, grid, placedShapes, done = game.execute('export')

# Final output
print(f"\n{'='*50}")
print(f"FINAL RESULT:")
print(f"Shapes used: {len(placedShapes)}")
print(f"Colors used: {count_unique_colors(placedShapes)}")
print(f"Empty cells: {count_empty_cells(grid)}")
print(f"Conflicts: {count_conflicts(grid)}")
print(f"Done: {done}")
print(f"{'='*50}\n")


np.savetxt('grid.txt', grid, fmt="%d")
with open("shapes.txt", "w") as outfile:
    outfile.write(str(placedShapes))
    
with open("trace.json", "w") as f:
    json.dump(trace, f, indent=2)