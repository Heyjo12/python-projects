# -*- coding: utf-8 -*-
import pygame
import numpy as np
import random
#import math
from deap import base, creator, tools

pygame.font.init()

#-----------------------------------------------------------------------------
# Game parameters
#-----------------------------------------------------------------------------

WIDTH, HEIGHT = 900, 500

WIN = pygame.display.set_mode((WIDTH, HEIGHT))

WHITE = (255, 255, 255)

TITLE = "Boom Master"
pygame.display.set_caption(TITLE)

FPS = 80
ME_VELOCITY = 5
MAX_MINE_VELOCITY = 3

BOOM_FONT = pygame.font.SysFont("comicsans", 100)   
LEVEL_FONT = pygame.font.SysFont("comicsans", 20)   

ENEMY_IMAGE  = pygame.image.load("mine.png")
ME_IMAGE = pygame.image.load("me.png")
SEA_IMAGE = pygame.image.load("sea.png")
FLAG_IMAGE = pygame.image.load("flag.png")

ENEMY_SIZE = 50
ME_SIZE = 50

ENEMY = pygame.transform.scale(ENEMY_IMAGE, (ENEMY_SIZE, ENEMY_SIZE))
ME = pygame.transform.scale(ME_IMAGE, (ME_SIZE, ME_SIZE))
SEA = pygame.transform.scale(SEA_IMAGE, (WIDTH, HEIGHT))
FLAG = pygame.transform.scale(FLAG_IMAGE, (ME_SIZE, ME_SIZE))

# ----------------------------------------------------------------------------
# Object classes
# ----------------------------------------------------------------------------

# Class representing a mine
class Mine:
    def __init__(self):

        # random x direction
        if random.random() > 0.5:
            self.dirx = 1
        else: 
            self.dirx = -1
            
        # random y direction    
        if random.random() > 0.5:
            self.diry = 1
        else: 
            self.diry = -1

        x = random.randint(200, WIDTH - ENEMY_SIZE) 
        y = random.randint(200, HEIGHT - ENEMY_SIZE) 
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        
        self.velocity = random.randint(1, MAX_MINE_VELOCITY)
        
# Class representing me, the agent        
class Me:
    def __init__(self):
        self.rect = pygame.Rect(10, random.randint(1, 300), ME_SIZE, ME_SIZE)  
        self.alive = True
        self.won = False
        self.timealive = 0
        self.sequence = []
        self.fitness = 0
        self.dist = 0
    
# Class representing the goal (flag)
class Flag:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH - ME_SIZE, HEIGHT - ME_SIZE - 10, ME_SIZE, ME_SIZE)
        
# Class representing the best individual - hall of fame   
class Hof:
    def __init__(self):
        self.sequence = []
            
# -----------------------------------------------------------------------------    
# Gameplan settings   
#-----------------------------------------------------------------------------
    
# Sets mine count based on num parameter
def set_mines(num):
    l = []
    for i in range(num):
        m = Mine()
        l.append(m)
        
    return l
    
# Initialises num number of me agents to start
def set_mes(num):
    l = []
    for i in range(num):
        m = Me()
        l.append(m)
        
    return l

# Resets all mes to start
def reset_mes(mes, pop):
    for i in range(len(pop)):
        me = mes[i]
        me.rect.x = 10
        me.rect.y = 10
        me.alive = True
        me.dist = 0
        me.won = False
        me.timealive = 0
        me.sequence = pop[i]
        me.fitness = 0

# -----------------------------------------------------------------------------    
# Senzor functions
# -----------------------------------------------------------------------------    


def dist_from_flag_senzor(me):
    x_dist = WIDTH - ME_SIZE/2 + 1 - me.rect.center[0] + 25
    y_dist = HEIGHT - ME_SIZE/2 + 1 - me.rect.center[1] + 25
    return x_dist + y_dist

def x_dist_from_mine_senzor(me, mines):
    dist_from_mines = []
    for mine in mines:
            x_dist = mine.rect.center[0] - me.rect.center[0]
            dist_from_mines.append(x_dist)
    dist_from_mines.sort()
    return dist_from_mines[0]

def y_dist_from_mine_senzor(me, mines):
    dist_from_mines = []
    for mine in mines:
            y_dist = me.rect.center[1] - mine.rect.center[1]
            dist_from_mines.append(y_dist)
    dist_from_mines.sort()
    return dist_from_mines[0]

def dist_from_right_wall_senzor(me):
    return WIDTH - me.rect.right

def dist_from_left_wall_senzor(me):
    return me.rect.left

def dist_from_top_wall_senzor(me):
    return me.rect.top

def dist_from_bottom_wall_senzor(me):
    return HEIGHT - me.rect.bottom

def time_until_end(SIMSTEPS, timer):
    return SIMSTEPS - timer

# ---------------------------------------------------------------------------
# Functions for agent movement
# ----------------------------------------------------------------------------

# Checks collisions of one agent with the mines, collision returns True
def me_collision(me, mines):    
    for mine in mines:
        if me.rect.colliderect(mine.rect):
            #pygame.event.post(pygame.event.Event(ME_HIT))
            return True
    return False
                     
# Colliding agents are removed and not rendered anymore
def mes_collision(mes, mines):
    for me in mes: 
        if me.alive and not me.won:
            if me_collision(me, mines):
                me.alive = False
                     
# Returns True, if all agents are dead            
def all_dead(mes):    
    for me in mes: 
        if me.alive:
            return False
    
    return True

# Returns True if noone is playing - all agents are dead or reached the goal
def nobodys_playing(mes):
    for me in mes: 
        if me.alive and not me.won:
            return False
    
    return True

# Return True if agent reached the goal
def me_won(me, flag):
    if me.rect.colliderect(flag.rect):
        return True
    
    return False

# Returns the number of living agents
def alive_mes_num(mes):
    c = 0
    for me in mes:
        if me.alive:
            c += 1
    return c

# Returns the number of agents that reached the goal
def won_mes_num(mes):
    c = 0
    for me in mes: 
        if me.won:
            c += 1
    return c

# Mine movement functions       
def handle_mine_movement(mine):
        
    if mine.dirx == -1 and mine.rect.x - mine.velocity < 0:
        mine.dirx = 1
       
    if mine.dirx == 1  and mine.rect.x + mine.rect.width + mine.velocity > WIDTH:
        mine.dirx = -1

    if mine.diry == -1 and mine.rect.y - mine.velocity < 0:
        mine.diry = 1
    
    if mine.diry == 1  and mine.rect.y + mine.rect.height + mine.velocity > HEIGHT:
        mine.diry = -1
         
    mine.rect.x += mine.dirx * mine.velocity
    mine.rect.y += mine.diry * mine.velocity


def handle_mines_movement(mines):
    for mine in mines:
        handle_mine_movement(mine)

#----------------------------------------------------------------------------
# Render functions
#----------------------------------------------------------------------------

# Window rendering
def draw_window(mes, mines, flag, level, generation, timer):
    WIN.blit(SEA, (0, 0))   
    
    t = LEVEL_FONT.render("level: " + str(level), 1, WHITE)   
    WIN.blit(t, (10  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("generation: " + str(generation), 1, WHITE)   
    WIN.blit(t, (150  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("alive: " + str(alive_mes_num(mes)), 1, WHITE)   
    WIN.blit(t, (350  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("won: " + str(won_mes_num(mes)), 1, WHITE)   
    WIN.blit(t, (500  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("timer: " + str(timer), 1, WHITE)   
    WIN.blit(t, (650  , HEIGHT - 30))
    
    WIN.blit(FLAG, (flag.rect.x, flag.rect.y))    
         
    # Mine rendering
    for mine in mines:
        WIN.blit(ENEMY, (mine.rect.x, mine.rect.y))
        
    # Agent rendering
    for me in mes: 
        if me.alive:
            WIN.blit(ME, (me.rect.x, me.rect.y))
        
    pygame.display.update()

def draw_text(text):
    t = BOOM_FONT.render(text, 1, WHITE)   
    WIN.blit(t, (WIDTH // 2  , HEIGHT // 2))     
    
    pygame.display.update()
    pygame.time.delay(1000)

#-----------------------------------------------------------------------------
# Neural network function, for inp input and weights wei, returns a list of four outputs
# for up, down, left, right
#----------------------------------------------------------------------------


def nn_function(inp, wei):
    midVals = []
    endVals = []
    for i in range(10):
        if inp[0]*wei[i] + inp[1]*wei[i + 10] + inp[2]*wei[i + 2*10] + inp[3]*wei[i + 3*10] + inp[4]*wei[i + 4*10] + inp[5]*wei[i + 5*10] + inp[6]*wei[i + 6*10] + inp[7]*wei[i + 7*10] >= wei[i + 80]:
            
            midVals.append(1)
        else:
            midVals.append(0)
    for i in range(4):
        endVals.append(midVals[0]*wei[i + 90] + midVals[1]*wei[i + 94] + midVals[2]*wei[i + 98] + midVals[3]*wei[i + 102] + midVals[4]*wei[i + 106] + midVals[5]*wei[i + 110] + midVals[6]*wei[i + 114] + midVals[7]*wei[i + 118] + midVals[8]*wei[i + 122] + midVals[9]*wei[i + 126])
    return endVals


# Agent navigation based of the neural network outputs
def nn_navigate_me(me, inp):
    next_dir = 0
    largest_out = -1
    out = np.array(nn_function(inp, me.sequence))
    for i in range(len(out)):
        if largest_out < out[i]:
            largest_out = out[i]
            next_dir = i
    ind = next_dir
    
    # up, if not a wall ahead
    if ind == 0 and me.rect.y - ME_VELOCITY > 0:
        me.rect.y -= ME_VELOCITY
        me.dist += ME_VELOCITY
    
    # down, if not a wall ahead
    if ind == 1 and me.rect.y + me.rect.height + ME_VELOCITY < HEIGHT:
        me.rect.y += ME_VELOCITY  
        me.dist += ME_VELOCITY
    
    # left, if not a wall ahead
    if ind == 2 and me.rect.x - ME_VELOCITY > 0:
        me.rect.x -= ME_VELOCITY
        me.dist += ME_VELOCITY
        
    # right, if not a wall ahead    
    if ind == 3 and me.rect.x + me.rect.width + ME_VELOCITY < WIDTH:
        me.rect.x += ME_VELOCITY
        me.dist += ME_VELOCITY
        
# Updates agents that reached the goal
def check_mes_won(mes, flag, timer):
    for me in mes: 
        if me.alive and not me.won:
            if me_won(me, flag):
                me.timealive = timer
                me.won = True
    
# Handle agent movement
def handle_mes_movement(mes, mines, flag, SIMSTEPS, timer):  
    for me in mes:
        if me.alive and not me.won:
            inp = []
            inp.append(dist_from_flag_senzor(me))
            inp.append(x_dist_from_mine_senzor(me, mines))
            inp.append(y_dist_from_mine_senzor(me, mines))
            inp.append(dist_from_right_wall_senzor(me))
            inp.append(dist_from_left_wall_senzor(me))
            inp.append(dist_from_top_wall_senzor(me))
            inp.append(dist_from_bottom_wall_senzor(me))
            inp.append(time_until_end(SIMSTEPS, timer))
            
            nn_navigate_me(me, inp)

# Update agent timers
def update_mes_timers(mes, timer):
    for me in mes:
        if me.alive and not me.won:
            me.timealive = timer

# ---------------------------------------------------------------------------
# Agent fitness function
#----------------------------------------------------------------------------

# Fitness function for all agents
def handle_mes_fitnesses(mes, levelTicks):    
    for me in mes:
        distFromWin = dist_from_flag_senzor(me)
        if me.won == True:
            me.fitness = 2000 + (levelTicks - me.timealive)
            continue
        if me.alive == False:
            me.fitness = 1
            continue
        if me.alive == True and me.won == False and dist_from_top_wall_senzor(me) <= 15 and dist_from_right_wall_senzor(me) <= 15:
            me.fitness = (1400 - distFromWin)/4
            continue
        if me.alive == True and me.won == False and dist_from_bottom_wall_senzor(me) <= 25 and dist_from_left_wall_senzor(me) <= 25:
            me.fitness =(1400 - distFromWin)/4
            continue
        me.fitness = 1400 - distFromWin
            
     
    
# Agents with best fitness is stored in the hall of fame
def update_hof(hof, mes):
    l = [me.fitness for me in mes]
    ind = np.argmax(l)
    hof.sequence = mes[ind].sequence.copy()
    
# ----------------------------------------------------------------------------
# main loop 
# ----------------------------------------------------------------------------

def main(): 
    # ========================================================================
    # Evolution parameters
    # ========================================================================
    
    POP_LEN = 50
    IND_LEN = 130  # Individual agent length (based on neural network structure)
    CXPB = 0.6         # Crossover probability
    MUTPB = 0.3        # Mutation probability
    
    SIMSTEPS = 500 #  Number of steps in the simulation
    
    currPopAvg = 0
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    toolbox = base.Toolbox()
    toolbox.register("attr_rand", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_rand, IND_LEN)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # Random mutation function
    def mutRandom(individual, indpbLower, indpbHigher):
        for me in mes:
            if me.sequence == individual:
                if me.fitness <= currPopAvg:
                    for i in range(len(individual)):
                        if random.random() < indpbHigher:
                            individual[i] = random.random()
                    return individual,        
                else:
                    for i in range(len(individual)):
                        if random.random() < indpbLower:
                            individual[i] = random.random()
                    return individual,
                
                
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutRandom, indpbLower=0.02, indpbHigher=0.06)
    toolbox.register("select", tools.selRoulette)
    toolbox.register("selectbest", tools.selBest)
    
    pop = toolbox.population(n=POP_LEN)
        
    # =====================================================================
    
    clock = pygame.time.Clock()
    
    # =====================================================================
    # Testing by playing and determining the fitness function 
   
    
    mines = []
    mes = set_mes(POP_LEN)    
    flag = Flag()
    
    hof = Hof()
        
    run = True

    level = 1  # Set number of mines (Difficulty setting)
    generation = 0
    
    evolving = True
    timer = 0
    
    while run:  
        clock.tick(FPS)     
        # If agents evolve a new set of agents is prepared - game reset
        if evolving:           
            timer = 0
            generation += 1
            reset_mes(mes, pop) # Reset agents with new parameters from evolution
            mines = set_mines(level) 
            evolving = False     
        timer += 1    
            
        check_mes_won(mes, flag, timer)
        handle_mes_movement(mes, mines, flag, SIMSTEPS, timer)   
        handle_mines_movement(mines)
        mes_collision(mes, mines)
        
        if all_dead(mes):
            evolving = True

        update_mes_timers(mes, timer)        
        draw_window(mes, mines, flag, level, generation, timer)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                
        # ---------------------------------------------------------------------
        # Second part of evolution after simulation
        

        if timer >= SIMSTEPS or nobodys_playing(mes):
            
            # New fitness funtion calculation
            handle_mes_fitnesses(mes, SIMSTEPS)
            
            update_hof(hof, mes)
            
            
            # Add fitness to agents
            countAvg = 0
            for i in range(len(pop)):
                ind = pop[i]
                me = mes[i]
                countAvg += me.fitness
                ind.fitness.values = (me.fitness, )
            currPopAvg = countAvg/len(mes)
            
            # Selection and genetic functions
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))
            
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)  
            
            pop[:] = offspring
            
            
            evolving = True
    
    pygame.quit()    


if __name__ == "__main__":
    main()