 
import argparse
import datetime
import gym
import pybullet as p
import numpy as np
import itertools
import torch
import time

from con_env12 import UR5_robotiq

from collections import deque
from matplotlib import pyplot as plt

import collections
import random
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable

parser = argparse.ArgumentParser(description='PyTorch Soft Actor-Critic Args')
parser.add_argument('--env-name', default="Allegro",
                    help='Mujoco Gym environment (default: HalfCheetah-v2)')
parser.add_argument('--policy', default="Gaussian",
                    help='Policy Type: Gaussian | Deterministic (default: Gaussian)')
parser.add_argument('--eval', type=bool, default=True,
                    help='Evaluates a policy a policy every 10 episode (default: True)')
parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
                    help='discount factor for reward (default: 0.99)')
parser.add_argument('--tau', type=float, default=0.005, metavar='G',
                    help='target smoothing coefficient(τ) (default: 0.005)')
parser.add_argument('--lr', type=float, default=0.0003, metavar='G',
                    help='learning rate (default: 0.0003)')
parser.add_argument('--alpha', type=float, default=0.2, metavar='G',
                    help='Temperature parameter α determines the relative importance of the entropy\
                            term against the reward (default: 0.2)')
parser.add_argument('--automatic_entropy_tuning', type=bool, default=False, metavar='G',
                    help='Automaically adjust α (default: False)')
parser.add_argument('--seed', type=int, default=123456, metavar='N',
                    help='random seed (default: 123456)')
parser.add_argument('--batch_size', type=int, default=256, metavar='N',
                    help='batch size (default: 256)')
parser.add_argument('--num_steps', type=int, default=1000001, metavar='N',
                    help='maximum number of steps (default: 1000000)')
parser.add_argument('--hidden_size', type=int, default=256, metavar='N',
                    help='hidden size (default: 256)')
parser.add_argument('--updates_per_step', type=int, default=1, metavar='N',
                    help='model updates per simulator step (default: 1)')
parser.add_argument('--start_steps', type=int, default=10000, metavar='N',
                    help='Steps sampling random actions (default: 10000)')
parser.add_argument('--target_update_interval', type=int, default=1, metavar='N',
                    help='Value target update per no. of updates per step (default: 1)')
parser.add_argument('--replay_size', type=int, default=1000000, metavar='N',
                    help='size of replay buffer (default: 10000000)')
parser.add_argument('--cuda', action="store_true",
                    help='run on CUDA (default: False)')
parser.add_argument('--GUI', default="GUI",
                    help='Pybullet physics server mode  GUI | DIRECT (default: GUI)')
# parser.add_argument('--GUI', default="DIRECT",
                    # help='Pybullet physics server mode  GUI | DIRECT (default: GUI)')
parser.add_argument('--suffix', default="00",
                    help='Disticguish models (default: 00)')
parser.add_argument('--dist_threshold', type=float, default=0.01,
                    help='Goal and State distance threshold (default: 0.03)')
parser.add_argument('--future_k', type=int, default=4,
                    help='future_k (default: 4)')
parser.add_argument('--epi_step', type=int, default=50,
                    help='Max_episode_steps (default: 50)')
parser.add_argument('--evaluate', type=bool, default=False,
                    help='evaluate (default: False)')

args = parser.parse_args()

state_size=8
action_size=3

PATH="./saved_model3/model1200.3.pth"
actor= torch.load(PATH)
actor.eval()

# Environment
env = UR5_robotiq(args)
# env.getCameraImage()

pose = env.getRobotPose()
print("Robot initial pose")
print(pose)

pose = env.holePos
pose.extend(env.Orn)
#pose[2] += 0.15 
print("Robot target pose")
print(env.holePos)
# p.addUserDebugText('O',np.array(env.holePos)[:3])
# env.moveL(env.holePos)
# get = env.getRobotPose()
# print(get)

# torch.cuda.device(0)
# cuda = torch.device('cuda')
'''

pose = env.getRobotPose()
print("Robot final pose")
print(pose)
'''

def main():
    score = 0.0  
    global_step=0
   # time.sleep(50)
    #env.lol()
    # state = env.reset()
    for epi_n in range(1000):
        state = env.reset()
        time.sleep(1.0)
        #pre_noise=np.zeros(action_size)
        done = False
        step = 0
        score = 0
        #while False: #not done:
        step += 1
        global_step+=1
            
            #action = actor(torch.FloatTensor(state))
            # next_state, reward, done, info= env.step([0.0,0.0,0.0,0.0])
            #next_state, reward, done, info= env.step(list(action))
            # print('error',info,'next_state',next_state)
            # for _ in range(50):
        env.down(-0.08)
        #env.AdmittanceCtrl([0.0,0.0,-80.0,0.0])
        time.sleep(2)
        env.down(0.08)
        #env.AdmittanceCtrl([0.0,0.0,80.0,0.0])
        time.sleep(2)
        Pos=env.getRobotPoseE()
        print("Pose: {}".format(Pos))

            # next_state, reward, done, info= env.step([0.0,0.0,0.0,0.0])
            # print('error',info,'next_state',next_state)
            # time.sleep(0.1)
            #env.down(-0.005)
            # time.sleep(0.1)
            # break
            #score += reward
            #state = next_state
           # if done:
               
                #break
        print('Finish!!!!!!!!!!!!!!!!!!!!')
        

if __name__ == '__main__':
    main()

end = True
while end:
    end = True