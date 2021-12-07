import _pickle as cPickle
from numpy.core.shape_base import block
from models.dla import DLA
from src.data_helper import DataHelper
from configs import configs, img_configs
import cv2
import numpy as np
from src.trainer import Trainer
from models.vgg import VGG
from models.ProNet import ProNet
import torch.nn as nn
import cv

def main():
    DataProcessor = DataHelper()
    file_dir = "/sharedfiles/cifar-10-batches-py/"
    # file_dir = "input/data/stl10_binary/"
    file_name = "data_batch_3"
    if configs['preprocess']:
        dataset = DataProcessor.load_data_from_binary_file(file_dir, file_name)[b'data']
        dataset = DataProcessor.transform(dataset, 
                                        img_configs['block-dim'],
                                        img_configs['block-size'])
        
        DataProcessor.save_data_to_binary_file(dataset, "input/dataset2x2.bin")     
        trainset, testset = DataProcessor.split_dataset(dataset, 0.95, saved=True)
    else:
        # dataset = DataProcessor.load_data_from_binary_file("input/", "test_dataset.bin")
        # trainset, testset = DataProcessor.split_dataset(dataset, 0.9, saved=True
        trainset, testset = DataProcessor.load_train_test_dataset(file_dir="input/")
        
    print("Train set size: ", len(trainset['data']))
    print("Test set size: ", len(testset['data']))
    # testset = {
    #     'data':testset['data'][:1000],
    #     'target':testset['target'][:1000]
    # }
    ''' print sample '''
    print("Sample: ", trainset['data'][0][0].shape)
    trainer = Trainer(model=ProNet(img_configs['image-size']), loss=nn.MSELoss, optimizer='adam',
                      train_loader=trainset, test_loader=testset, batch_size=64, epochs=10)
    trainer.model.load(2, 100)
    trainer.train()
    # trainer.test()
    sample_img = trainset['data'][0][0]
    cv2.imwrite("output/sample.png", sample_img)
    
    
if __name__ == "__main__":
    main()