import os
import time
import pdb
import pybullet as p
import pybullet_data
import utils_ur5_robotiq140
from collections import deque
import numpy as np
import math
import matplotlib.pyplot as plt
from gym.spaces import Box

ACTION_RANGE = 1.0
OBJ_RANGE = 0.1
Deg2Rad = 3.141592/180.0

class UR5_robotiq():

    def __init__(self, args):
        
        # print(args.GUI)
        if args.GUI =='GUI':
            self.serverMode = p.GUI # GUI/DIRECT
        else:
            self.serverMode = p.DIRECT

        self.thforce=0.01
        self.initdis=0
        self.distance_threshold = 0.001
        self.reward_type = 'sparse'
        self.has_object = False
        # self.goal = np.array([0.13, -0.65, 1.02])

        self.loadURDF_all()
        # p.setRealTimeSimulation(1)
        # p.setTimeStep(1.0/240.0)

        # environment check
        # while(True):
        #     pass

        # print(controlJoints)
        self.eefID = 7 # ee_link
        self._max_episode_steps = args.epi_step
        self.observation_space = 39     # Input size
        self.action_space = Box(-ACTION_RANGE, ACTION_RANGE, (4,))

        self.init_pose = [-0.18269931421578223, -1.2624127482337664, 1.6356823388624389, -1.944575358530638, -1.5708127721603529, -0.44438877709013885]

        self.home_pose()
        p.stepSimulation()

        pose = self.getRobotPose()
        self.Orn = [pose[3], pose[4], pose[5], pose[6]]
        self.fOri=0
        # self.goal = np.array(self.targetStartPos)elf.d_oldelf.d_old


    def loadURDF_all(self):
        self.UR5UrdfPath = "./urdf/ur5_peg.urdf"
        # self.UR5UrdfPath = "./urdf/ur5_robotiq85.urdf"

        # connect to engine servers
        self.physicsClient = p.connect(self.serverMode)
        # add search path for loadURDFs
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, -9.8)
        # p.setTimeStep(0.1)

        # Gripper Setting
        self.gripper_main_control_joint_name = "robotiq_85_left_knuckle_joint"
        self.mimic_joint_name = ["robotiq_85_right_knuckle_joint",
                            "robotiq_85_left_inner_knuckle_joint",
                            "robotiq_85_right_inner_knuckle_joint",
                            "robotiq_85_left_finger_tip_joint",
                            "robotiq_85_right_finger_tip_joint"]
        self.mimic_multiplier = [1, 1, 1, -1, -1] 

        # Load URDF
        # define world
        self.planeID = p.loadURDF("plane.urdf")

        tableStartPos = [0.7, 0.0, 0.8]
        tableStartOrientation = p.getQuaternionFromEuler([0, 0, 90.0*Deg2Rad])
        self.tableID = p.loadURDF("./urdf/objects/table.urdf", tableStartPos, tableStartOrientation,useFixedBase = True, flags=p.URDF_USE_INERTIA_FROM_FILE)
        
        # define environment
        self.holePos = [0.6, 0.0, 0.87]
        self.holeOri = p.getQuaternionFromEuler([1.57079632679, 0, 0.261799333]) #.261799333
        
        self.boxId = p.loadURDF(
        "./urdf/peg_hole_gazebo/hole/urdf/hole.SLDPRT.urdf",
        self.holePos, self.holeOri,
        flags = p.URDF_USE_INERTIA_FROM_FILE,useFixedBase=True)
        # p.changeDynamics(self.boxId ,-1,lateralFriction=0.5,spinningFriction=0.1)
      
        # self.holePos = [0.6, -0.1, 0.67]
        # self.holeOri = p.getQuaternionFromEuler([1.57079632679, 0, 0.261799333]) #.261799333
        
        # define environment
        # ur5standStartPos = [0.0, 0.0, 0.0]
        # ur5standStartOrientation = p.getQuaternionFromEuler([0, 0, 0])
        # self.ur5_standID = p.loadURDF("./urdf/objects/ur5_stand.urdf", ur5standStartPos, ur5standStartOrientation,useFixedBase = True)

        # setup ur5 with robotiq 85
        robotStartPos = [0.0, 0.0, 0.0]
        robotStartOrn = p.getQuaternionFromEuler([0,0,0])

        print("----------------------------------------")
        print("Loading robot from {}".format(self.UR5UrdfPath))        
        self.robotID = p.loadURDF(self.UR5UrdfPath, robotStartPos, robotStartOrn,useFixedBase = True,flags=p.URDF_USE_INERTIA_FROM_FILE)
                             # flags=p.URDF_USE_INERTIA_FROM_FILE)
        self.joints, self.controlJoints = utils_ur5_robotiq140.setup_sisbot(p, self.robotID)
        for i in range(p.getNumJoints(self.robotID)):
            p.enableJointForceTorqueSensor(self.robotID,i)
        
        self.last=0

    def step(self, action):

        self.move(action)   #move > moveL
        self.next_state_dict = self.get_state()
        
        rel_pose=np.asarray([self.next_state_dict[0]-self.next_state_dict[7],self.next_state_dict[1]-self.next_state_dict[8],self.next_state_dict[2]-self.next_state_dict[9]])
        rel_ori=self.next_state_dict[3]-self.next_state_dict[10]
        force=[]
        for i in range(3):
            force.append(self.next_state_dict[i+4])
        dis_error=np.linalg.norm(rel_pose, axis=-1, ord=2)
        self.done=False
        goal=False
        #self.done = self.contact
        reward=0
        if (dis_error<self.distance_threshold):
            goal=True
        if ((dis_error)/self.initdis)>1.5:
            self.done=True
            print('outofrange')
        reward-=0.5*(dis_error)/self.initdis
        reward-=0.5*abs(rel_ori)*10000
        #print(rel_ori)
        #if self.contact==True:
        #    temp=sum(abs(force))/100
        #    if temp>5:
        #        temp=5
        #    reward-=temp
        if self.done:
            self.contact=False
            if goal:
                reward=10.0
            elif dis_error<0.5:
                pass
            else:
               reward=-1.0
        return self.next_state_dict, reward, self.done, {}


    def reset(self):
        print('reset')
        self.home_pose()
        self.state_dict = self.get_state()
        temp=np.asarray([self.state_dict[0]-self.state_dict[7],self.state_dict[1]-self.state_dict[8],self.state_dict[2]-self.state_dict[9]])
        self.initdis=np.linalg.norm(temp ,axis=-1, ord=2)
        # # p.removeAllUserDebugItems()
        time.sleep(1)
        print('init_pose',self.state_dict)
        return self.state_dict

    def home_pose(self):

        for i, name in enumerate(self.controlJoints):
            if i > 6:
                break
            # print(i()
            self.joint = self.joints[name]

            pose1 = self.init_pose[i]
            #p.resetJointState(self.robotID, self.joint.id, targetValue=pose1, targetVelocity=0)
            if i < 6:
                p.resetJointState(self.robotID, self.joint.id, targetValue=pose1, targetVelocity=0)
       
        p.stepSimulation()


    def moveL(self, targetPose, setTime = 0.1):
        stepSize = 240*setTime

        currentPose = self.getRobotPoseE()
        delta = []
        for i in range(len(currentPose)):
            delta.append((targetPose[i] - currentPose[i])/stepSize)
            
        # # p.removeAllUserDebugItems()
        #print("Delta")
        # print(delta)

        start = time.time()

        for t in range(int(stepSize)):
            stepPos = []
            stepOri = []
            for i in range(3):
                stepPos.append(currentPose[i] + (t+1)*delta[i])
            stepOri.append(0)
            stepOri.append(1.5707963)
            stepOri.append(currentPose[5] + (t+1)*delta[5])
            stepOri = p.getQuaternionFromEuler(stepOri)
        for t in range(int(stepSize)):
            
            jointPos = p.calculateInverseKinematics(self.robotID,
                                                    self.eefID,
                                                    stepPos,
                                                    stepOri)
            
            # pos.append(1)
            # jointPos = urk.invKine(pos)
            # print('---------------')
            # print(jointPos)
            for i, name in enumerate(self.controlJoints):
                joint = self.joints[name]
                targetJointPos = jointPos[i]

                p.setJointMotorControl2(self.robotID,
                                        joint.id,
                                        p.POSITION_CONTROL,
                                        targetPosition = targetJointPos,
                                        # targetVelocity = 5,
                                        force = joint.maxForce, 
                                        maxVelocity = joint.maxVelocity)

            # p.addUserDebugLine((0.6475237011909485, 0.6443161964416504, 0.9296525716781616),(0,0,0))
        # for i in range(10):
            
            p.stepSimulation()
            # self.getCameraImage()
        
        # print(p.getLinkState(self.robotID, 7 , computeLinkVelocity = 1)[6])
        end = time.time()

        # print(end-start)

    def recovery(self):
        pos = p.getLinkState(self.robotID, 7)[4]#4
        pose=[]
        for i in range(3):
            if i==2:
                pose.append(pos[i]+0.0005)
            else:
                pose.append(pos[i])
        ori=[0,1.5707963267948966, self.last]
        ori = p.getQuaternionFromEuler(ori)
        jointPos = p.calculateInverseKinematics(self.robotID,
                                                    self.eefID,
                                                    pose,
                                                    ori)
        for i, name in enumerate(self.controlJoints):
            joint = self.joints[name]
            targetJointPos = jointPos[i]

            p.setJointMotorControl2(self.robotID,
                                        joint.id,
                                        p.POSITION_CONTROL,
                                        targetPosition = targetJointPos,
                                        # targetVelocity = 5,
                                        force = joint.maxForce, 
                                        maxVelocity = joint.maxVelocity)
            for _ in range(10):
                p.stepSimulation()


    
    def move(self, action,setTime=0.01):
        stepSize = 240*setTime
        currentPose = self.getRobotPoseE()
            
        stepPos=[]
        stepOri=[]
        for i in range(3):
            stepPos.append(currentPose[i] + action[i])
        stepOri.append(0)
        stepOri.append(1.5707963)
        stepOri.append(currentPose[5]+action[3])
        stepOri = p.getQuaternionFromEuler(stepOri)
        
        jointPos = p.calculateInverseKinematics(self.robotID,
                                                    self.eefID,
                                                    stepPos,
                                                    stepOri)
        for i, name in enumerate(self.controlJoints):
            joint = self.joints[name]
            targetJointPos = jointPos[i]

            p.setJointMotorControl2(self.robotID,
                                        joint.id,
                                        p.POSITION_CONTROL,
                                        targetPosition = targetJointPos,
                                        # targetVelocity = 5,
                                        force = joint.maxForce, 
                                        maxVelocity = joint.maxVelocity)

            # p.addUserDebugLine((0.6475237011909485, 0.6443161964416504, 0.9296525716781616),(0,0,0))
        # for i in range(10):
            
        
        for _ in range(30):
            contact = p.getContactPoints(bodyA=self.robotID,bodyB=self.boxId)
            p.stepSimulation()
            # self.getCameraImage()
        #print(joint_positions)
        self.last=currentPose[5]
        currentPose = self.getRobotPoseE()
        if abs(currentPose[3])>0.01:
            self.recovery()

    def getRobotPose(self):
        currentPos = p.getLinkState(self.robotID, 7)[4]#4
        currentOri = p.getLinkState(self.robotID, 7)[5]#5
        #currentOri = p.getEulerFromQuaternion(currentOri)
        currentPose = []
        currentPose.extend(currentPos)
        currentPose.extend(currentOri)
        return currentPose 

    def getRobotPoseE(self):
        currentPos = p.getLinkState(self.robotID, 7)[4]#4
        currentOri = p.getLinkState(self.robotID, 7)[5]#5
        currentOri = p.getEulerFromQuaternion(currentOri)
        currentPose = []
        currentPose.extend(currentPos)
        currentPose.extend(currentOri)
        return currentPose              

    def get_state(self):
        object_pos = [0.6, 0.0, 0.87]
        object_ori= [1.57079632679, 0, 0.261799333]
        #object_ori= p.getQuaternionFromEuler(object_ori)
        joint_states = p.getJointStates(self.robotID, range(p.getNumJoints(self.robotID)))

        joint_positions = [state[0] for state in joint_states] #  -> (8,)
        jp=np.asarray(joint_positions)
        joint_torque=[state[3] for state in joint_states]
        ee_force=joint_states[7][2]
        torque_list=[]
        for i in range(len(self.controlJoints)):
            if i > 6:
                break
            torque_list.append(joint_torque[self.joint.id])
        #print(torque_list)
        #torque=np.asarray(torque_list)
        ee_force=np.asarray(ee_force)
        #print(ee_force)
        # End-Effector States
        ee_states = p.getLinkState(self.robotID, 7 , computeLinkVelocity = 1)
        ee_pos = ee_states[0]
        ee_ori = ee_states[1]
        ee_ori= p.getEulerFromQuaternion(ee_ori)
        #print(ee_ori)
        #ee_angular_vel = ee_states[7]

        self.contact = p.getContactPoints(bodyA=self.robotID,bodyB=self.boxId)
        #self.contact2 = p.getContactPoints(bodyA=self.robotID,bodyB=self.tableID)

        # Final states
        # obs = np.concatenate([
        #     ee_pos, ee_linear_vel, #gripper_state, gripper_vel,
        #     object_pos, object_ori, object_linear_vel, object_angular_vel,
        #     self.object_rel_pos, object_rel_vel,
        # ])self.object_rel_pos[0],self.object_rel_pos[1],self.object_rel_pos[2],, rel_ori
        #rel_ori = object_ori[2] - ee_ori[2]
        obs_temp = np.array([
            ee_pos[0], ee_pos[1], ee_pos[2], ee_ori[2],ee_force[0],ee_force[1],ee_force[2]
            ])
        #obs1=np.concatenate((obs_temp,ee_force),axis=None)
        ##obs2=np.concatenate((obs,jp),axis=None)

        obs_temp2=np.array([object_pos[0],object_pos[1],object_pos[2], object_ori[2]])
        obs=np.concatenate((obs_temp,obs_temp2),axis=None)
        #print(ee_ori)
        return obs

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))

    def lol(self):
        object_pos=[]
        for i in range(3):
            if i==2:
                object_pos.append(self.holePos[i]+0.2)
            else:
                object_pos.append(self.holePos[i])
        currentPose = self.getRobotPoseE()
        objectOri = []
        objectOri.append(0)
        objectOri.append(1.5707963)
        objectOri.append(0.261799333)
        objectOri = p.getQuaternionFromEuler(objectOri)
        jointPos = p.calculateInverseKinematics(self.robotID,
                                                    self.eefID,
                                                    object_pos,
                                                    objectOri)
        print(jointPos)
        time.sleep(1000)

    def process(self,angle):
        if angle>1.5707963/2+1.5707963:
            return angle-1.5707963/2-1.5707963
        elif angle>1.5707963:
            return angle-1.5707963
        elif angle>1.5707963/2:
            return angle-1.5707963/2
        elif angle<-1.5707963-1.5707963/2:
            return angle+1.5707963+1.5707963
        elif angle<-1.5707963:
            return angle+1.5707963+1.5707963/2
        elif angle<-1.5707963/2:
            return angle+1.5707963
        elif angle<0:
            return angle+1.5707963/2
        else:
            return angle