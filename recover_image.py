''' python3 recover_image.py -f natural_1 -v -m '''
import cv2
import numpy as np
from models.ProNet2 import ProNet2
from models.dla import DLA
from models.SimpleProNet import ProNet as SimpleProNet
# from models.VGG import ProNet
from models.VGG import VGG
from src.data_helper import DataProcessor
from src.recover.MCTS import MCTS
from src.recover.greedy import Greedy
from utils import *
from src.recover.environment import Environment, State, GameInfo
from configs import *
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game-info-path', type=str, default='./input/game_info/')
    parser.add_argument('--model-path', type=str, default='./trainned_models/')
    parser.add_argument('--model-name', type=str, default='model_2_0.pt')
    parser.add_argument('--output-path', type=str, default='./output/recovered_images/')
    parser.add_argument('-f', '--file-name', type=str, default='natural_19')
    parser.add_argument('--image-size-out', type=int, default=(512, 512))   
    parser.add_argument('-s', '--block-size', type=int, default=(32, 32))
    parser.add_argument('-a', '--algorithm', type=str, default='greedy')
    parser.add_argument('-v', '--verbose', action='store_true', default=True)
    parser.add_argument('-m', '--monitor', action='store_true')
    parser.add_argument('-t', '--threshold', type=float, default=1.0)
    parser.add_argument('-j', '--n_jumps', type=float, default=0)
    
    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    state = State(block_size=args.block_size)
    state.load_json(file_name=args.file_name + '.json')
    state.make()
    state.save_image()
    model = VGG('VGG7')
    # model.load_checkpoint(1, 827)
    model.load(1,907)
    model.eval()
    
    env = Environment()
    if args.algorithm == 'greedy':
        algo = Greedy(env, model, verbose=args.verbose, 
                    n_bests=7, threshold=args.threshold)
    elif args.algorithm == 'mcts':
        algo = MCTS(env, model, n_sim=8, 
                c_puct=1, threshold=args.threshold,
                n_bests=5, verbose=False)
    else:
        raise Exception('Unknown algorithm')
    
    print('Start recovering...')
    print('Threshold:', args.threshold)
    
    start = time.time()
    states = [state]
    n_jumps = args.n_jumps
    
    if args.monitor:
        inp = input('Number of jump steps: ')
        n_jumps = int(inp)
    
    while state.depth < state.max_depth:
        actions, probs = algo.get_next_action(state)
        n_jumps = max(n_jumps - 1, 0)
        for idx, action in enumerate(actions):
            action = tuple(action)
            _state = state.copy()
            _state = env.step(_state, action, verbose=args.verbose)
            if args.verbose:
                _state.save_image()
            if args.monitor:
                if n_jumps > 0:
                    if _state.depth < state.max_depth:
                        states.append(_state.copy())
                        state = _state
                        break
                # Input 'a' if accept, 'r' if reject
                inp = input('(a/r/b/j), accept/reject/back/jump: ')
                if inp == 'b':
                    # input number of steps to go back
                    inp = -1
                    while inp < 0 or inp >= len(states):
                        inp = int(input('input number of steps to go back: '))
                        if inp < 0 or inp >= len(states):
                            print('the number of steps to go back should be between 0 and {}'.format(len(states)-1))
                    states = states[:-int(inp)]
                    state = states[-1]
                    algo.threshold = 1.0
                    break
                elif inp == 'j':
                    # input number of steps to jump
                    n_jumps = int(input('input number of steps to jump: '))
                    states.append(_state.copy())
                    state = _state           
                    algo.threshold = args.threshold    
                    break
                elif 'r' in inp:
                    continue
                else:
                    state = _state
                    states.append(_state.copy())
                    break
            else:
                state = _state
                states.append(_state.copy())
                break
        
        
            # env.show_image(state)
        print('Probability: {}'.format(probs[0]))
        print('Done step: {} / {}'.format(state.depth, state.max_depth))
        print('Time: %.3f' % (time.time() - start))
        
    new_blocks = np.zeros(state.original_blocks.shape, dtype=np.uint8)
    for i in range(state.block_dim[0]):
        for j in range(state.block_dim[1]):
            x, y, angle = state.inverse[i][j]
            new_blocks[i][j] = np.rot90(state.original_blocks[x][y], k=angle)
    recovered_image = DataProcessor.merge_blocks(new_blocks)

    end = time.time()
    
    # recovered_image = cv2.resize(recovered_image, args.image_size_out)
    cv2.imwrite(args.output_path + args.file_name + '.png', recovered_image)
    print('Recovered image saved at: ' + args.output_path + args.file_name+ '.png')
    print('Time: {}'.format(end - start))
    DataProcessor.save_item_to_binary_file(
        state,
        'output/states/' + args.file_name.split('.')[0] + '.bin') # _' + args.file_name
    
if __name__ == "__main__":
    main()