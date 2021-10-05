# Author: Sean Kelly
# Date: 11/25/20 
# Filename: numberlink.py
# 
# Usage: python3 numberlink.py puzzle1.txt

import sys
from pysat.solvers import Glucose3
import math

def read_puzzle(puzzle_name):
    """Read in each puzzle position from a puzzle.txt file where
    each row of the puzzle is listed on a single line."""

    file_type = puzzle_name.split('.')[1]
    puzzle_file = open(puzzle_name, "r")
    string_puzzle = puzzle_file.readlines() #1 Dimensional maze with rows of type string with '\n'
    puzzle = []

    if file_type == "txt":
        #removes newline from end of each row in maze and appends it to 2D maze array with row * col = type character
        for row in range(len(string_puzzle)):
            puzzle.append(list(string_puzzle[row]))
            del puzzle[row][len(puzzle[row])-1] #del '\n'
    else: #csv file
        for row in range(len(string_puzzle)):
            temp_str = string_puzzle[row].splitlines()
            puzzle.append(temp_str[0].split(','))
    puzzle_file.close()

    return puzzle
#End read_puzzle()

def read_puzzle_csv(puzzle_name):

    puzzle_file = open(puzzle_name, "r")    
    string_puzzle = puzzle_file.readlines() #1 Dimensional maze with rows of type string with '\n'
    puzzle = []

    for row in range(len(string_puzzle)):
        temp_str = string_puzzle[row].splitlines()
        puzzle.append(temp_str[0].split(','))
    
    puzzle_file.close()

    return puzzle
#End read_puzzle_csv()


def find_adj_squares(puzzle,row,col):
    """finds adjacent squares surrounding terminal square"""

    #         Up     R    Down   L
    dirs = [[-1,0],[0,1],[1,0],[0,-1]] #directions of adjacent squares from a given square

    valid_adjs = []
    for adj_dir in range(len(dirs)): 
        cur_row = row + dirs[adj_dir][0]
        cur_col = col + dirs[adj_dir][1]
        if cur_row >= 0 and cur_row < len(puzzle): #valid row pos
            if cur_col >= 0 and cur_col < len(puzzle): #valid col pos
                valid_adjs.append((cur_row,cur_col)) #list of valid puzzle positions
    return valid_adjs
#end find_adj_squares()

def find_terminal_squares(puzzle, phi, gridVariables, numbers):

    terminal_squares = []
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            for num in numbers:
                if puzzle[r][c] == str(num):
                    phi.add_clause([gridVariables[(r,c),num]])
                    terminal_squares.append([(r,c),num])
                    #print(num,"Terminal values:",gridVariables[(r,c),num])
    return terminal_squares

def free_square_domain(puzzle, phi, gridVariables, numbers):

    #print("Free Square Domain at MOST Constraints")
    #At MOST 1 number can be true per square
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            for num_i in numbers:
                for num_j in numbers:
                    if num_i < num_j:
                        phi.add_clause([-1*gridVariables[(r,c),num_i],-1*gridVariables[(r,c),num_j]]) #(-1a V -1b) Ʌ (-1a V -1c)...
                        #print("   ",-1*gridVariables[(r,c),num_i],' or ',-1*gridVariables[(r,c),num_j])

    #print("Free Square Domain at LEAST Constraints")
    #At LEAST 1 number must be true per square
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            temp_or = []
            for num in numbers:
                temp_or.append(gridVariables[(r,c),num])
            #print("   ",temp_or)
            phi.add_clause(temp_or) #(1a V 1b V 1c V 1d V 1e) Ʌ (2a V 2b V 2c V 2d V 2e)...

def terminal_square_adjs(puzzle, phi, gridVariables, terminal_squares):

    #print("terminal_square_adjs:")
    #Terminal squares must have at MOST 1 adjacent square of same number
    for square in terminal_squares:
        valid_adjs = find_adj_squares(puzzle,square[0][0],square[0][1])
        
        for adj_i in range(len(valid_adjs)):
            for adj_j in range(len(valid_adjs)):

                #the 2 adjacents are equal to the terminal square's value
                if adj_i < adj_j and valid_adjs[adj_i][1] == square[1] and valid_adjs[adj_j][1] == square[1]:
                    pos_i = valid_adjs[adj_i]
                    pos_j = valid_adjs[adj_j]
                    #print("POS i:",valid_adjs[adj_i], '- POS_j:',valid_adjs[adj_j],"Square:",square[1])
                    phi.add_clause([-1*gridVariables[pos_i,square[1]],-1*gridVariables[pos_j,square[1]]]) #(-1a V -2a) Ʌ (-1a V -5a)...
                    #print("at MOST:",end='')
                    #print(-1*gridVariables[pos_i,square[1]],'or',-1*gridVariables[pos_j,square[1]])


    #Terminal squares must have at LEAST 1 adjacent square of same number
    for square in terminal_squares:
        valid_adjs = find_adj_squares(puzzle,square[0][0],square[0][1])
        temp_or = []
        for adj in valid_adjs:
            temp_or.append(gridVariables[(adj[0],adj[1]),square[1]])
        phi.add_clause(temp_or)
        #print("at LEAST:",temp_or)

def free_square_adjs(puzzle, phi, gridVariables, terminal_squares, numbers):

    terminal_pos_list = []
    for square in terminal_squares:
        terminal_pos_list.append(square[0])

    #print("Non-terminal exactly 2:\n")

    #Each non-terminal square has at MOST 2 adjacent squares of the same number
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            if puzzle[r][c] == '.': #Non-terminal square

                valid_adjs = find_adj_squares(puzzle,r,c)
                for i in range(len(valid_adjs)):
                    for j in range(len(valid_adjs)):
                        for k in range(len(valid_adjs)):

                            #the 2 adjacents are equal to the non-terminal square's value
                            if i < j and j < k:
                                for num in numbers:
                                    temp_or = [-1*gridVariables[(r,c),num]]
                                    temp_or.append(-1*gridVariables[valid_adjs[i],num])
                                    temp_or.append(-1*gridVariables[valid_adjs[j],num])
                                    temp_or.append(-1*gridVariables[valid_adjs[k],num])
                                    phi.add_clause(temp_or) # Num => (-a V -b V -c) == (-Num V -a V -b V -c) 
                                    # (-a V -b V -c) Ʌ (-a V -b V -d) Ʌ ... == -(aɅbɅc) Ʌ -(aɅbɅd) Ʌ ...
                                    #print("non-term at MOST:",temp_or)


    #Each non-terminal square has at LEAST 2 adjacent squares of the same number
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):

            if puzzle[r][c] == '.': #Non-terminal square
                valid_adjs = find_adj_squares(puzzle,r,c)

                #print()

                if len(valid_adjs) == 2: #2 valid adjacent squares for number to link
                    for adj in range(len(valid_adjs)):
                        for num in numbers:
                            phi.add_clause([-1*gridVariables[(r,c),num],gridVariables[valid_adjs[adj],num]])
                            # Num => (a Ʌ b) == -Num V (a Ʌ b) == (-Num V a) Ʌ (-Num V b)
                            # a Ʌ b
                            #print(len(valid_adjs),"valid_adjs",valid_adjs)
                            #print("   non-term at LEAST:",-1*gridVariables[(r,c),num],'or',gridVariables[valid_adjs[adj],num])

                if len(valid_adjs) == 3: #3 valid adjacent squares to place 2 lamps
                    for i in range(len(valid_adjs)):
                        for j in range(len(valid_adjs)):
                            if i < j: #prevents duplicate clauses
                                for num in numbers:
                                    temp_or = [-1*gridVariables[(r,c),num]]
                                    query_idx = [i,j]
                                    for adj in query_idx:
                                        temp_or.append(gridVariables[valid_adjs[adj],num])
                                    phi.add_clause(temp_or)
                                    # Num => (a V b) == (-Num V a V b) == (-Num V a V b) Ʌ (-Num V a V c) Ʌ (-Num V b V c)
                                    # (a V b) Ʌ (a V c) Ʌ (b V c)
                                    #print(len(valid_adjs),"valid_adjs",valid_adjs)
                                    #print(     "non-term at LEAST:",temp_or)

                if len(valid_adjs) == 4: #4 valid adjacent squares to place 2 lamps
                    for i in range(len(valid_adjs)):
                        for j in range(len(valid_adjs)):
                            for k in range(len(valid_adjs)): 
                                if i < j and j < k:
                                    for num in numbers:
                                        temp_or = [-1*gridVariables[(r,c),num]]
                                        query_idx = [i, j, k]
                                        for adj in query_idx:
                                            temp_or.append(gridVariables[valid_adjs[adj],num])
                                        phi.add_clause(temp_or)
                                        # (a V b V c) Ʌ (a V b V d) Ʌ (a V c V d) Ʌ (b V c V d)
                                        #print(len(valid_adjs),"valid_adjs",valid_adjs)
                                        #print(      "non-term at LEAST:",temp_or)
#End free_square_adjs()

def define_colors():

    CBLACKBG  = '\33[40m'
    CREDBG    = '\33[41m'
    CGREENBG  = '\33[42m'
    CYELLOWBG = '\33[43m'
    CBLUEBG   = '\33[44m'
    CVIOLETBG = '\33[45m'
    CBEIGEBG  = '\33[46m'
    CWHITEBG  = '\33[47m'

    CGREYBG    = '\33[100m'
    CREDBG2    = '\33[101m'
    CGREENBG2  = '\33[102m'
    CYELLOWBG2 = '\33[103m'
    CBLUEBG2   = '\33[104m'
    CVIOLETBG2 = '\33[105m'
    CBEIGEBG2  = '\33[106m'
    CWHITEBG2  = '\33[107m'

    colors = []
    colors.append(CBLACKBG)
    colors.append(CREDBG)
    colors.append(CGREENBG)
    colors.append(CYELLOWBG)
    colors.append(CBLUEBG)
    colors.append(CVIOLETBG)
    colors.append(CBEIGEBG)
    colors.append(CWHITEBG)
    colors.append(CGREYBG)
    colors.append(CREDBG2)
    colors.append(CGREENBG2)
    colors.append(CYELLOWBG2)
    colors.append(CBLUEBG2)
    colors.append(CVIOLETBG2)
    colors.append(CBEIGEBG2)
    colors.append(CWHITEBG2)

    return colors
#End define_colors()

def main():

    if len(sys.argv) != 2:
        sys.exit("Usage: python3 numberlink.py puzzle_file")

    puzzle_name = sys.argv[1]
    #puzzle = read_puzzle(puzzle_name)
    puzzle = read_puzzle(puzzle_name)

    print("Puzzle:")
    for row in puzzle:
        print(row)

    max_num = -1*math.inf
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            if puzzle[r][c] != '.' and int(puzzle[r][c]) > max_num:
                max_num = int(puzzle[r][c])

    numbers = []
    for num in range(max_num):
        numbers.append(num+1)

    #Model containing constraints of lamps in puzzle squares
    phi = Glucose3()

    #Create a variable for each square on the board with T,F value for each domain number
    val = 1
    output = {}
    gridVariables = dict()
    for r in range(len(puzzle)):
        for c in range(len(puzzle)):
            for num in numbers:
                gridVariables[(r,c),num] = val
                output[val] = (r,c),num
                val += 1

    #Each square must have exactly 1 true domain variable
    free_square_domain(puzzle, phi, gridVariables, numbers)
    print()

    #Finds terminal squares and adds them as true to gridVariables
    terminal_squares = find_terminal_squares(puzzle, phi, gridVariables, numbers)
    #print("\nTerminal Squares:",terminal_squares)

    #Each terminal square has exactly 1 adjacent square of the same number
    terminal_square_adjs(puzzle, phi, gridVariables, terminal_squares)

    #Each non-terminal square has exactly 2 adjacent squares of the same number
    free_square_adjs(puzzle, phi, gridVariables, terminal_squares, numbers)

    #Solves CNF sentences
    solution = phi.solve()
    if solution == False:
        print("No Solution")

    #Places numbers on appropriate coordinates to solve puzzle
    solved_puzzle = puzzle
    for square in phi.get_model():
        if square > 0: #number is true in position
            pos,num = output[square]
            solved_puzzle[pos[0]][pos[1]] = num

    #Display verbose puzzle solution
    for row in solved_puzzle:
        print(row)
    print('\n')

    #Display colorful puzzle solution
    colors = define_colors()
    reset_color = '\33[00m'
    max_num = 0
    for row in solved_puzzle:
        for num in row:
            print(colors[num],"",reset_color,end='')
            if num > max_num:
                max_num = num
        print('\n')

    print(reset_color,"--- Color Key ---")
    for num in range(max_num):
        print(colors[num+1],num+1,end=' ')
    print(reset_color,end='')

if __name__ == "__main__":
    main()