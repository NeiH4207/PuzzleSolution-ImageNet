from copy import deepcopy
import numpy as np
from src.data_helper import DataProcessor
from multiprocessing import Pool

class Greedy():
    def __init__(self, env, 
                 model, 
                 n_bests=256, 
                 threshold=0.9,
                 verbose=False):
        self.env = env
        self.model = model
        self.n_bests = n_bests
        self.threshold = threshold
        self.verbose = verbose
        self.mask = None
        self.blocks_rotated = None
        
    def get_next_action(self, state):
        state = state.copy()
        if self.mask is None:
            self.mask = np.zeros((state.block_size[0] * 2, state.block_size[1] * 2, 3),
                                 dtype=np.uint8)
            self.blocks_rotated = np.zeros((state.block_dim[0], state.block_dim[1], 4, state.block_size[0], state.block_size[1], 3),
                                           dtype=np.uint8)
            for i in range(state.block_dim[0]):
                for j in range(state.block_dim[1]):
                    for k in range(4):
                        self.blocks_rotated[i][j][k] = np.rot90(state.blocks[i][j], k=k)
        
        lost_positions = []
        for i in range(state.block_dim[0]):
            for j in range(state.block_dim[1]):
                if state.lost_block_labels[i][j] == 1:
                    lost_positions.append((i, j))
        # if self.verbose:
        #     state.save_image()
        stop = False
        probs = []
        actions = []
        valid_block_pos, best_pos, ranks = self.env.get_valid_block_pos(state, kmax=self.n_bests, last_state=False)
        for x, y in valid_block_pos:
            for _x, _y in lost_positions:
                # get dropped_subblocks 2x2 from dropped_blocks
                i, j = best_pos[(x, y)]
                subblocks = np.array((
                    [state.dropped_blocks[i][j], state.dropped_blocks[i][j + 1]],
                    [state.dropped_blocks[i + 1][j], state.dropped_blocks[i + 1][j + 1]]), dtype=np.uint8)
                index = np.zeros(4, dtype=np.int32)
                index[(x - i) * 2 + (y - j)] = 1
                for angle in range(4):
                    subblocks[x - i][y - j] = self.blocks_rotated[_x][_y][angle]
                    recovered_image = DataProcessor.merge_blocks(subblocks, mask=self.mask)
                    recovered_image_ = DataProcessor.convert_image_to_three_dim(recovered_image)
                    prob = self.model.predict(recovered_image_, index) ** 2
                    action = ((x, y), (_x, _y), angle)
                    # subblocks[x - i][y - j] = np.zeros(state.block_shape, dtype=np.uint8)
                    # new_image = deepcopy(state.dropped_blocks)
                    # new_image[x][y] = np.rot90(state.blocks[_x][_y], k=angle)
                    # new_image_ = DataProcessor.merge_blocks(new_image)
                    # cv2.imwrite('output/sample.png', new_image_)
                    # print(action,  prob)
                    probs.append(prob)
                    actions.append(action)
                    if prob > self.threshold:
                        stop = True
                        break
                if stop:
                    break
            if stop:
                break
        # if self.verbose:
        #     state.save_image()
        return (np.array(actions, dtype=object)[np.argsort(probs)[::-1]]).tolist(), sorted(probs)[::-1]