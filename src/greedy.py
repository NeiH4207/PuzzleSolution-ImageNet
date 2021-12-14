from copy import deepcopy
import numpy as np
from src.data_helper import DataProcessor
from multiprocessing import Pool

class Greedy():
    def __init__(self, env, model, n_bests=256, verbose=False):
        self.env = env
        self.model = model
        self.n_bests = n_bests
        self.verbose = verbose
        
    def next_action(self, state):
        lost_positions = []
        for i in range(state.block_dim[0]):
            for j in range(state.block_dim[1]):
                if state.lost_block_labels[i][j] == 1:
                    lost_positions.append((i, j))
        valid_block_pos, best_pos = self.env.get_valid_block_pos(state, kmax=self.n_bests)
        best_action = None
        best_prob = 0
        if self.verbose:
            state.save_image()
        for x, y in valid_block_pos:
            for _x, _y in lost_positions:
                # get dropped_subblocks 2x2 from dropped_blocks
                i, j = best_pos[x][y]
                subblocks = deepcopy(state.dropped_blocks[i:i+2, j:j+2])
                params = []
                for angle in range(4):
                    block = np.rot90(state.blocks[_x][_y], k=angle)
                    subblocks[x - i][y - j] = block
                    recovered_image = DataProcessor.merge_blocks(subblocks)
                    recovered_image_ = DataProcessor.convert_image_to_three_dim(recovered_image)
                    dropped_index_image = DataProcessor.merge_blocks(state.lost_index_img_blocks[i:i+2, j:j+2], mode='gray')
                    prob, angle_prob = self.model.predict(recovered_image_, state.index_imgs[x-i][y-j], dropped_index_image)
                    action = ((x, y), (_x, _y), angle)
                    # subblocks[x - i][y - j] = np.zeros(state.block_shape, dtype=np.uint8)
                    # new_image = deepcopy(state.dropped_blocks)
                    # new_image[x][y] = np.rot90(state.blocks[_x][_y], k=angle)
                    # new_image_ = DataProcessor.merge_blocks(new_image)
                    # cv2.imwrite('output/sample.png', new_image_)
                    # print(prob[0], angle_prob[0])
                    # print()
                    if prob  > best_prob:
                        best_prob = prob
                        best_action = action
        if self.verbose:
            state.save_image()
        return best_action, best_prob