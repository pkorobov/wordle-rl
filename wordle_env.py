import numpy as np
from typing import Optional
from termcolor import colored
import os
import gym
from gym import spaces

from tokenizer import Tokenizer


GAME_VOCABULARY = ["sword", "crane", "plate"]
WORD_LENGTH = 5
MAX_TRIES = 6
EMBEDDING_DIM = 64


# state: 2 x 6 x 5 (guess, is_right)
class WordleEnv(gym.Env):
    def __init__(self):
        self.num_tries = 0
        # is_right matrix will contain 4 states per letter: empty, wrong, right, present in the word
        self.is_right = None
        # guess is the matrix of letter guesses during the current game
        self.guess = None
        self.word = None

        self.tokenizer = Tokenizer()
        self.game_voc_matrix = None
        self._initialize_vocabulary()

        self.action_space = spaces.MultiDiscrete([26] * 5)
        # I am not even sure that it is somehow used by gym or parallel wrapper
        self.observation_space = spaces.MultiDiscrete([26] * 2 * 5 * 6)
        self.reset()

    def _initialize_vocabulary(self):
        assert self.tokenizer is not None

        self.game_voc_matrix = np.zeros(shape=(len(GAME_VOCABULARY), WORD_LENGTH), dtype=np.int32)
        for i in range(len(GAME_VOCABULARY)):
            for j, letter in enumerate(GAME_VOCABULARY[i]):
                self.game_voc_matrix[i, j] = self.tokenizer.letter2index[letter]

    def reset(self, seed: Optional[int] = None):
        if seed is not None:
            np.random.seed(seed)

        word_idx = np.random.randint(len(GAME_VOCABULARY))
        self.word = self.game_voc_matrix[word_idx]

        self.num_tries = 0

        self.is_right = np.zeros((MAX_TRIES, WORD_LENGTH), dtype=np.int32)
        self.guess = np.zeros((MAX_TRIES, WORD_LENGTH), dtype=np.int32)
        self.guess[:, :] = self.tokenizer.letter2index['<PAD>']

        obs = np.stack([self.guess, self.is_right])
        return obs

    def step(self, action: np.ndarray):
        """
        Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.
        Accepts an action and returns a tuple (observation, reward, done, info).
        Args:
            action (object): an action provided by the agent
        Returns:
            observation (object): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (bool): whether the episode has ended, in which case further step() calls will return undefined results
            info: None TODO: use it somehow
        """

        assert len(action.shape) == 1
        assert len(action) == WORD_LENGTH

        info = dict()

        self.is_right[self.num_tries, :] = 1  # not right
        right_mask = (action == self.word)
        self.is_right[self.num_tries, right_mask] = 2  # right
        is_in = np.isin(self.word, action)
        self.is_right[self.num_tries, is_in] = 3  # semi-right

        self.guess[self.num_tries, :] = action

        reward, done = right_mask.sum() / WORD_LENGTH, False
        if right_mask.all() or self.num_tries == MAX_TRIES - 1:
            if right_mask.all():
                reward = 10.0
            done = True
            obs = self.reset()
        else:
            self.num_tries += 1
            obs = np.stack([self.guess, self.is_right])

        return obs, reward, done, info

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        for i in range(self.guess.shape[0]):
            s = []
            for j in range(self.guess.shape[1]):
                letter = " "
                if self.guess[i, j] != 0:
                    letter = self.tokenizer.index2letter[self.guess[i, j]]
                c = None
                if self.is_right[i, j] == 2:
                    c = "green"
                elif self.is_right[i, j] == 3:
                    c = "yellow"
                s.append(colored(letter, color=c))
            print("".join(s), end="\n")


if __name__ == "__main__":
    import time

    from wrappers import nature_dqn_env
    nenvs = 2
    env = nature_dqn_env(nenvs=nenvs)

    while True:

        # print("Choose your word...")
        # a = input()

        a = np.array([5, 5, 5, 5, 5])
        obs, reward, done, info = env.step(a.reshape(1, -1).repeat(nenvs, axis=0))
        # print(obs)
        time.sleep(0.5)
        # sim.render()
