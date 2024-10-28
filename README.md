Boom Game Evolution

Boom Game Evolution is a simple 2D game where a neural network agent learns to reach a goal while avoiding bombs. The agent adapts over time using neural network and evolutionary principles to improve its performance.
Features

    Reinforcement Learning: Agent learns strategies to reach goals while dodging obstacles.
    Genetic Algorithm: Uses evolutionary techniques for optimization.
    Obstacle Avoidance: Agent dodges randomly generated bombs.

Dependencies

    pygame
    numpy
    random
    deap

Installation

    Clone the repository:

    bash

git clone https://github.com/your-username/boom-game-evolution.git

Install dependencies:

bash

    pip install -r requirements.txt

Recommended IDE

For optimal performance, it’s recommended to use Spyder IDE, especially for scientific computing tools.
Usage

Run the game with default settings:

bash

python main.py

Default Parameters

    Agent Population: 50 agents by default, adjustable using the POP_LEN parameter.
    Obstacles (Mines): Set by LEVEL parameter to change the number of bombs in the field.
