from copy import deepcopy
import logging
import math
import cv2
import numpy as np
from requests.api import get
from utils import LongestIncreasingSubsequence as LIS
EPS = 1e-8
log = logging.getLogger(__name__)

class Standard():
    """
    This class handles the A* algorithm.
    """

    def __init__(self, env, verbose=False):
        self.env = env
        self.verbose = verbose
        self.cursor = None 
        self.curr_pos = None # Source
        self.shape = None
        self.sequential_mode = False
        self.curr_value = None
        self.action_list = []
        
    def update_curr_pos(self, state):
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]
        for i in range(4):
            _x, _y = self.curr_pos[0] + dx[i], self.curr_pos[1] + dy[i]
            _x = (_x + self.shape[0]) % self.shape[0]
            _y = (_y + self.shape[1]) % self.shape[1]
            if state.targets[_x][_y] == self.curr_value:
                self.curr_pos = (_x, _y)
                return
        
    def set_next_position(self, state, curr_pos):
        value = state.targets[curr_pos[0]][curr_pos[1]]
        
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                if state.targets[i][j] == value + 1:
                    self.curr_pos = (i, j)
                    self.curr_value = value + 1
                    return
        
    def set_cursor(self, state):
        self.action_list = []
        self.shape = state.shape
        for i in range(self.shape[0]):
            for j in range(self.shape[1]):
                if state.targets[i][j] == state.shape[0] * state.shape[1] - 1:
                    self.cursor = (i, j)
                if state.targets[i][j] == 0:
                    self.curr_pos = (i, j)
                    self.curr_value = 0
                    
        self.action_list.append(('choose', (self.cursor[0], self.cursor[1])))
        self.sequential_mode = True
                
    def move_left(self):
        action = ('swap', (self.cursor[0], 
                         self.cursor[1], 
                         self.cursor[0], 
                         (self.cursor[1] - 1 + self.shape[1]) % self.shape[1]))
        self.cursor = (self.cursor[0],
                          (self.cursor[1] - 1 + self.shape[1]) % self.shape[1])
        return action
        
    def move_right(self):
        action = ('swap', (self.cursor[0], 
                         self.cursor[1], 
                         self.cursor[0], 
                        (self.cursor[1] + 1) % self.shape[1]))
        self.cursor = (self.cursor[0],
                        (self.cursor[1] + 1) % self.shape[1])
        return action
    
    def move_up(self):
        action = ('swap', (self.cursor[0],
                            self.cursor[1],
                            (self.cursor[0] - 1 + self.shape[0]) % self.shape[0],
                            self.cursor[1]))
        self.cursor = ((self.cursor[0] - 1 + self.shape[0]) % self.shape[0],
                          self.cursor[1])
        return action
    
    def move_down(self):
        action = ('swap', (self.cursor[0], 
                         self.cursor[1], 
                         (self.cursor[0] + 1) % self.shape[0], 
                         self.cursor[1]))
        self.cursor = ((self.cursor[0] + 1) % self.shape[0],
                          self.cursor[1])
        return action
    
    def execute_last_row(self, state):
        
        arr = [x for x in state.targets[self.shape[0] - 1]]
        last = len(arr) - 1
        for _ in range(1, len(arr)):
            idx = np.argmax(arr[:last+1])
            if idx == last:
                last -= 1
                continue
            self.action_list.append(('choose', (self.shape[0] - 1, idx)))
            while idx < last:
                arr[idx], arr[idx + 1] = arr[idx + 1], arr[idx]
                self.action_list.append(('swap', (self.shape[0] - 1, idx, self.shape[0] - 1, idx + 1)))
                idx += 1
            last -= 1
            
        if len(self.action_list) > 0:
            self.sequential_mode =  True
        return self.get_action(state)
    
    def run_sequential(self):
        action = self.action_list[0]
        self.action_list = self.action_list[1:]
        if len(self.action_list) == 0:
            self.sequential_mode = False
        return action
    
    def get_action(self, state):
        self.update_curr_pos(state)
        x_source, y_source = self.curr_pos[0], self.curr_pos[1]
        x_cursor, y_cursor = self.cursor[0], self.cursor[1]
        value = state.targets[x_source][y_source]
        x_target, y_target = value // self.shape[1], value % self.shape[1]
        
        
        if self.sequential_mode:
            return self.run_sequential()
        
        if x_target == self.shape[0] - 1:
            return self.execute_last_row(state)
        
        if x_source == x_target and y_source == y_target:
            self.set_next_position(state, self.curr_pos)
            return self.get_action(state)
        
        if x_source == x_target:
            if x_cursor == x_target:
                return self.move_down()
            if y_cursor != y_source:
                return self.move_right()
            else:
                self.action_list.append(self.move_up())
                if self.cursor[1] == self.shape[1] - 1:
                    self.action_list.append(self.move_left())
                else:
                    self.action_list.append(self.move_right())
                self.sequential_mode = True
                return self.get_action(state)
        
        if x_cursor != x_source and y_source == y_cursor:
            if x_cursor < x_source and y_target == self.shape[1] - 1:
                return self.move_down()
            return self.move_right()
            
        if x_source > x_cursor:
            return self.move_down()
        elif x_source < x_cursor:
            return self.move_up()
        elif y_source != y_target:
            return self.move_right()
        if (y_target == self.shape[1] - 1):
            if (y_source + 1) % self.shape[1] == y_cursor:
                self.sequential_mode =  True
                for i in range(x_source - x_target - 1):
                    self.action_list.extend(
                        [self.move_up(), self.move_left(), 
                            self.move_down(), self.move_right(),
                            self.move_up()]
                    )
                for i in range(self.shape[1] - 3):
                    self.action_list.append(self.move_right())
                self.action_list.extend(
                    [
                        self.move_up(),
                        self.move_right(),
                        self.move_right(),
                        self.move_down(),
                        self.move_left(),
                        self.move_up(),
                        self.move_left(),
                        self.move_down()
                        ]   
                )
                if self.cursor[0] == self.shape[0] - 1:
                    self.action_list.extend(
                        [
                            self.move_right(),
                            self.move_right(),
                        ]
                    )
                return self.get_action(state)
        elif y_source != y_cursor - 1 :
            return self.move_left()
        else:
            self.sequential_mode =  True
            for i in range(x_source - x_target):
                self.action_list.extend(
                    [self.move_up(), self.move_left(), 
                           self.move_down(), self.move_right(),
                           self.move_up()]
                )
            return self.get_action(state)
        