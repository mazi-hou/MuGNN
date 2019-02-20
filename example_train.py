import sys, os
from config import Config
from graph_completion.nets import *
from project_path import bin_dir

# CUDA_LAUNCH_BLOCKING=1

directory = bin_dir / 'full_dbp15k'
config = Config(directory)
try:
    os.environ['CUDA_VISIBLE_DEVICES'] = sys.argv[1]
except IndexError:
    config.set_cuda(False)
config.set_graph_completion(False)
config.init(load=False)
config.set_net(SpGATNet)
config.print_parameter()
config.train()
