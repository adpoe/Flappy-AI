import random
import itertools
import ast
import copy

# IMPLEMENTED EXPLORE BUT:
# seems to do worse with explore function set to high number
# think it's because we gather data that's not r
# representative of actual
# situations the bird will find himself in
# AND --> depending on how we set the alpha, these early explorations have more impact on values than later ones


# STORING PATH
# tried storing path, and in the short term it works great
# but long run flappy optimizes too early and performs worse!
# kept code for this, but comment out and not using
# this was an initial test to gain understanding of the system
# and it was instructive, but a failure

# FPS
# Choice of FPS also has a strong effect on how well flappy does and the other parameters
# started at 30, but also experimented with 60
# > fps usually yields better results, because more data collection overall, so that makes sense.

# Problem
# Too fast.. he doesn't move at all... sometimes
# not sure the cause... only sending a something to the queue
# WHEN decide to jump... maybe sending jumps too frequently?

# Discretization
# finer discretization --> better performance
# but also:  more choices!
# more time complexity. AND more space complexity.
# so a very distinct tradeoff


class QLearningAgent:
    # state space = (bird_height, pipe_bottom_y, pipe_dist, pipe_collision)
    # reward = if no collision +1, if collision -1000
    #
    # THINK:
    #   * bird height - pipe_bottom_y can discretized into 3 buckets
    #       0 = close  ( y < 100 )
    #       1 = mid    ( 100 < y < 200 )
    #       2 = far    ( 200 < y )
    #   * same thing for pipe dist
    #       0 = close  ( x < 100 )
    #       1 = mid    ( 100 < x < 200 )
    #       2 = far    ( 200 < x )

    #  now need a way to grab all this information...
    #  initialize an agent and pass the bird and pipes to it each time we start an episode
    #  so --> run episode needs to take an argument, and that argument is the Q-LearningAgent
    #  and once we initialize the pipes and bird, we pass those values into the Q-LearningAgent each time

    #  if each of these 3 buckets were crossed with each other, how many total states would we have?
    #  these are the nodes from each level of our tree.
    #  can use this --> nodes = list(itertools.product( (0,1,2) , repeat=2))
    #           gives 9 nodes to search through, discretely at each step... or does it...
    #  they aren't really nodes... they're possible states... and we only have two options (nodes)
    #        Node 1 = Stay
    #        Node 2 = Jump
    #  and we can store data into our Q-Learning agent based on those 9 discrete spaces
    #  depending on which state we are in, we store our statistics for the step in that particular node.
    #  or not -- each of thee are nodes, i think...
    #  Okay, so -->
    #       nodes = list(itertools.product( (0,1,2) , repeat=2))
    #       STATE_ACTION_PAIRS = state_action_pairs = list(itertools.product(nodes, ('S', 'J')))


    def __init__(self, saved_strategy=None):
        """
        Pass in file name of saved strategy, if we have one
        :param saved_strategy:
        :return:
        """
        # need to set these each new episode
        self.bird = None #bird   # set=bird
        self.pipes = None #pipes  # set=pipes
        self.pp = None #pp     # flappy's pipe info data structure

        # current state
        #self.current_state = self.observeState(self.bird, self.pipes, self.pp)
        self.current_state = None
        # time
        #self.t = 0
        self.t = 1000
        if saved_strategy is not None:
            self.t = 100

        # Q-ARRAY
        # load a saved strategy if we have one
        # pass in the file name
        self.q_data = {}
        if saved_strategy is None:
            s_a_pairs = self.generateStates() # get all state/action pairs
            # turn them all into strings and initialize our dictionary with them
            for elem in s_a_pairs:
                key = str(elem)
                self.q_data[key] = 0.0
        else:
            with open(saved_strategy, 'r') as f:
                data_string = f.read()
                data_dict = ast.literal_eval(data_string)
                self.q_data = data_dict

        # agent-specific values
        self.gamma = 0.7

        #Alpha should be different depending on whether we load or start from scratch
        # alpha = "learning rate", also used for 'explore' function
        if saved_strategy is None:
            self.alpha = lambda n: 1./(1+n)
        else:
            self.alpha = lambda n: 1./(10000+n)

        # N-Array --> n(s,a)
        # Keeps track of how many times we've been in state s, performing action a
        self.n_data = copy.deepcopy(self.q_data)

        if saved_strategy is None:
            # avoid division by zero error
             for k in self.n_data.iterkeys():
                self.n_data[k] = 1.0
        else:
            for k in self.n_data.iterkeys():
                self.n_data[k] = 10.0


        # path
        self.path = []
        return

    def generateStates(self):
        """
        :return: Returns a list containing all discretized states for Flappy Bird proble
        """
        #nodes = list(itertools.product( (0,1,2) , repeat=2))  # OLD / SAFE
        nodes = list(itertools.product( (0,1,2,3,4), repeat=2))
        STATE_ACTION_PAIRS = state_action_pairs = list(itertools.product(nodes, ('S', 'J')))
        return state_action_pairs


    def observeState(self, bird, pipes, pp):
        # observe state flappy is in
        #  get info here --> and calculate reward after we check for collision....
        bird_height = bird.y
        pipe_bottom = 500 - pp.bottom_height_px
        pipe_dist = pp.x
        """ OLD / SAFE
        # first value in state tuple
        height_category = 0
        dist_to_pipe_bottom = pipe_bottom - bird.y
        if dist_to_pipe_bottom < 100:
            height_category = 0
        elif dist_to_pipe_bottom < 200:
            height_category = 1
        else:
            height_category = 2

        # second value in state tuple
        dist_category = 0
        dist_to_pipe_horz = pp.x - bird.x
        if dist_to_pipe_horz < 100:  # works:  100
            dist_category = 0
        elif dist_to_pipe_horz < 200: # works: 200
            dist_category = 1
        else:
            dist_category = 2
        """

                # first value in state tuple
        height_category = 0
        dist_to_pipe_bottom = pipe_bottom - bird.y
        if dist_to_pipe_bottom < 8:
            height_category = 0
        elif dist_to_pipe_bottom < 20:
            height_category = 1
        elif dist_to_pipe_bottom < 125:
            height_category = 2
        elif dist_to_pipe_bottom < 250:
            height_category = 3
        else:
            height_category = 4

        # second value in state tuple
        dist_category = 0
        dist_to_pipe_horz = pp.x - bird.x
        if dist_to_pipe_horz < 8:  # works:  100
            dist_category = 0
        elif dist_to_pipe_horz < 20: # works: 200
            dist_category = 1
        elif dist_to_pipe_horz < 125: # works: 200
            dist_category = 2
        elif dist_to_pipe_horz < 250: # works: 200
            dist_category = 3
        else:
            dist_category = 4

        # check for collision
        pipe_collision = any(p.collides_with(bird) for p in pipes)
        collision = pipe_collision
        state = (height_category, dist_category, collision)
        return state

    def performAction(self, state):
        # perform action that maximizes expected reward
        actions = self.getActions(state)
        if not self.explore():
            best_action = self.findMaxReward(actions)
        else:
            best_action = self.exploreDecision()
        # send this action back to game space, and either it will say
        # 'MOUSEBUTTONUP', or nothing this turn
        # so, need to connect this to our game itself
        return best_action, state

    # then let clock tick
    def updateTime(self):
        self.t += 1
        self.alpha(self.t)

    # place after the get events part of loop in the game
    def collectReward(self, state, collision):
        # obverse new state and collect reward associated
        # +1 if alive
        # -1000 if dead
        reward = 1
        # if True in state:
        if collision:
            reward = -1000
        return reward

    def updateQArray(self, prev_state, action, reward):
        # update Q array according to the q-learning rule
        # generate key for our dictionaries
        key = ((prev_state[0], prev_state[1]), action)
        # perform Q-Calculation
        q_sample = reward + self.gamma * self.q_data[str(key)]
        q_old = self.q_data[str(key)]
        """ OPTIONS FOR ALPHA, or 'LEARNING POLICY' """
        #q_new = q_old + self.alpha(self.t) * q_sample
        q_new = q_old + 1/self.n_data[str(key)] * q_sample
        #self.q_data[str(key)] = reward + self.gamma * self.q_data[str(key)]
        # updated the q array with new value
        self.q_data[str(key)] = q_new
        # update n_array, with how many times we've peformed this action
        self.n_data[str(key)] += 1.0
        return

    # place at bottom of loop
    def updateState(self):
        # set current state to s'
        self.current_state = self.observeState(self.bird, self.pipes, self.pp)
        return

    def saveStrategy(self, fname):
        """
        Save the q_data dictionary, so we can load it back in later
        and keep learning more
        :param fname:
        :return:
        """
        f = open(fname, "w")
        f.write(str(self.q_data))
        f.close()

    # and repeat the loop!

    #################################
    ####### MAIN LEARNING LOOP ######
    #################################
    # TODO: Implement LEARN! Chain it all together and start giving it a try. See how it goes.

    def newEpisode(self, bird, pipes):
        """
            Run this method each time we start a new episode
        """
        self.bird = bird
        self.pipes = pipes

    def newIteration(self):
        self.pp = self.pipes[0]

    def stepAndMakeChoice(self):
        # chain actions above all together
        #self.newEpisode(self.bird, self.pipes, self.pp)
        self.current_state = self.observeState(self.bird, self.pipes, self.pp)
        action,state = self.performAction(self.current_state)
        #self.trackPath(state, action)  # --> PATH TRACKING
        return action,state

    def learnFromChoice(self, action, prev_state, collision):
        self.updateTime()
        self.updateState()
        reward = self.collectReward(prev_state, collision)
        if reward < 1:
            print str(reward)
        self.updateQArray(prev_state, action, reward)
        #self.updatePathValues(reward) # --> PATH TRACKING


    ###############################
    ##### UTILITY FUNCTIONS #######
    ###############################
    def findMaxReward(self, actions):
        # find max reward predicted for all possible actions
        decision = 'S'
        # we know only two actions for flappy
        reward_jump = self.q_data[actions[0]]
        reward_stay = self.q_data[actions[1]]
        print "REWARD JUMP="+str(reward_jump)
        print "REWARD STAY="+str(reward_stay)
        if reward_jump > reward_stay:
            decision = 'J'

        return decision

    def getActions(self, state):
        # given a state, return a list containing possible actions
        # should only be 2 for Flappy Bird --> Jump or Stay
        t = (state[0], state[1])
        jump = str((t, 'J'))
        stay = str((t, 'S'))
        return [jump, stay]

    ##############################
    ###### EXPLORE DECISION ######
    ##############################
    def explore(self):
        """
        :return: decision on whether we should explore!
        """
        r = random.random()  # get a random Real number in range [0,1)
        if self.alpha(self.t) > r:
            print "EXPLORE!"
            return True
        else:
            return False

    def exploreDecision(self):
        """
        :return: for flappy, we're only choose between two states
                jump, or don't jump.
                So return either 0 or 1
        """
        action = 'S'
        index = random.randint(0,1)
        if index == 1:
            action = 'J'
        return action

    ########################
    ###### TRANSITION ######
    ########################
    # TODO:  Updated previous values in a weighted way using the next TWO functions.
    #        Third is for Transition pobs... and still confused on that.
    def trackPath(self, prev_state, action):
        key = str(((prev_state[0], prev_state[1]), action))
        if len(self.path) < 10:
            self.path.append(key)
        else:
            self.path.pop(0)
            self.path.append(key)

    def updatePathValues(self, reward):
        i = 0
        for key in self.path:
            i += 1
            weight = lambda i: 1./(1+i)
            q_sample = reward + self.gamma * self.q_data[str(key)]
            q_old = self.q_data[str(key)]
            q_new = q_old + self.alpha(self.t) * q_sample
            #self.q_data[str(key)] = reward + self.gamma * self.q_data[str(key)]
            # updated the q array with new value
            self.q_data[str(key)] = q_new * weight(self.t)


    def transition_probs(self, new_state, action, prev_state):
        """  Finds prob of ending up in new state, given that we are in
             current state, performing given action
        :param new_state:
        :param action:
        :param state:
        :return:
        """
        # Formula: Pr(s' | a, s)
        # Pr(s')
        # possible new states
        possible_fst = []
        if prev_state[0] == 0:
            y0 = prev_state[0]
            y1 = prev_state[0] + 1
            possible_fst.append(y0)
            possible_fst.append(y1)
        elif prev_state[0] == 2:
            y1 = prev_state[0] - 1
            y2 = prev_state[0]
            possible_fst.append(y1)
            possible_fst.append(y2)
        else:
            y0 = prev_state[0]
            y1 = prev_state[0] + 1
            y2 = prev_state[0] - 1
            possible_fst.append(y0)
            possible_fst.append(y1)
            possible_fst.append(y2)

        possible_snd = []
        if prev_state[1] == 0:
            x0 = prev_state[1]
            x1 = prev_state[1] + 1
            possible_snd.append(x0)
            possible_snd.append(x1)
        elif prev_state[1] == 2:
            x1 = prev_state[1] - 1
            x2 = prev_state[1]
            possible_fst.append(x1)
            possible_fst.append(x2)
        else:
            x0 = prev_state[0]
            x1 = prev_state[0] + 1
            x2 = prev_state[0] - 1
            possible_snd.append(x0)
            possible_snd.append(x1)
            possible_snd.append(x2)
        # get possible state/action pairs
        possible_states = list(itertools.product(possible_fst, possible_snd))
        state_action_pairs  = list(itertools.product(possible_states, ['J','S']))

        qk_sp_ap = {}
        for elem in state_action_pairs:
            qk_sp_ap[str(elem)] = self.q_data[str(elem)]

        max_qk_sp_ap = max(qk_sp_ap.iterkeys(), key=(lambda key: qk_sp_ap[key]))

        discounted_max = self.gamma * max_qk_sp_ap

        # Pr(a,s)
        key = ((prev_state[0], prev_state[1]), action)
        key = str(key)

        reward = self.q_data[key]
        # get prob being in state by n(s,a) value / # clock ticks
