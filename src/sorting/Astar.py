from copy import deepcopy
import logging
import math
import cv2
import numpy as np
EPS = 1e-8
log = logging.getLogger(__name__)

class Astar():
    """
    This class handles the A* algorithm.
    """

    def __init__(self, env, verbose=False):
        self.env = env
        self.verbose = verbose
        
    def get_action(self, state):
        s = state.get_string_presentation()
        state = state.copy()
        
        actions = self.env.get_available_actions(state)
    
        rewards = []
        for action in actions:
            rewards.append(self.env.get_strict_reward(state, action))
        if rewards == []:
            return None
        best_actions = np.array(np.argwhere(rewards == np.max(rewards)), dtype=object).flatten()
        best_action = np.random.choice(best_actions)
        return actions[best_action]