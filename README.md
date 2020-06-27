# Agar.io in Python
Openai Gym environment to play a local version of https://agar.io, a multiple agent game. 
This project referenced javascript impelmentation of agar https://github.com/m-byte918/MultiOgar-Edited but rewritten and heavily modified to python
A video demo of this repo can be found at [Youtube](https://www.youtube.com/watch?v=Au9oQNOB0gI&feature=youtu.be)

# Play with mouse and keyboard
Run python src/HumanControl.py to play!
![Screenshot](https://github.com/buoyancy99/PyAgar/blob/master/img/Agar_OpenAI_Gym.gif?raw=true)


# Progress
All game components, teleop and gym interface are done. Gameplay is smooth. Need to make bots smarter. 

# Environment
The environment is defined in Env.py. This is a multiagent environment and you can specify any number of players. See HumanControl.py for sample use. The state space for each agent is [mouse.x, mouse.y, IfSplit, IfFeed, IfNoSplitNoFeed]. You are allowed to control multiple agents by passing a [N, 5] 2D array. 


