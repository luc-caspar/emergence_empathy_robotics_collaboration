#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
import json
from multiprocessing import Queue, Event
from environments import PushEnv
from display import Display
from agent import Agent


class PushTask:
    """
    Defines a multi-agent push task, where the goal is to bring an object to a
    specific location by navigating a series of obstacles.
    """

    def __init__(self, config_path, headless=True):
        # Load the configuration
        if isinstance(config_path, str):
            config_path = Path(config_path)
        config_path = config_path.expanduser().resolve()

        if not (config_path.exists() or config_path.is_file()):
            raise RuntimeError(f"The provided configuration file does not exist, or you do not have access to it: {config_path}")

        with config_path.open('r') as f:
            self._config = json.load(f)

        self._max_steps = self._config.get('max_steps', 1)
        self._fps = self._config.get('fps', 30)

        # Get the environment's configuration
        env_config = self._config.get('environment')
        if env_config is None:
            raise RuntimeError("No environment configuration provided.")

        # Check if rendering is required
        self._headless = headless
        if not headless:
            self._disp_q = Queue()
            self._disp_evt = Event()
            self._disp = Display(self._disp_q, self._disp_evt, self._fps, env_config.get('width', 100), env_config.get('height', 100))
        else:
            self._disp_q = None
            self._disp_evt = None

        # Instantiate the environment
        self._env = PushEnv(env_config, self._disp_q, self._disp_evt)

        # Instantiate all agents
        # While still allowing to run empty environments
        agts_config = self._config.get('agents', [])
        if len(agts_config) > 0:
            self._agts = [Agent(cfg) for cfg in agt_configs]
        else:
            self._agts = []

    def reset(self):
        """
        Resets the task, its agents and environment to an intial state.
        """

        # Reset all agents
        for agt in self._agts:
            agt.reset()

        # Reset thet environment
        self._env.reset()

    def save(self):
        """
        Saves the agents' states to file.
        """

        for agt in self._agts:
            agt.save()

    def run(self):
        # If relevant, start the display
        if not self._headless:
            self._disp.start()

        try:
            end = False
            cnt = 0
            while not end and cnt <= self._max_steps:
                # Observe the environment
                obs, rew, end = self._env.observe()

                # Let the agents decide on their next action
                acts = [agt.act(obs, rew, end) for agt in self._agts]

                # Move the environment forward
                self._env.step(1/self._fps, acts)

                # If relevant display new environment's state
                if not(self._headless or self._disp_evt.is_set()):
                    msg = {'cmd': 'display',
                           'data': self._env.to_display()}
                    self._disp_q.put([msg])

                # Increment the steps counter
                cnt += 1
        finally:
            # If relevant wait for display to stop
            if not(self._headless or self._disp_evt.is_set()):
                while self._disp.is_alive():
                    self._disp.join(1)
                    if self._disp_evt.is_set():
                        while not self._disp_q.empty():
                            self._disp_q.get()


if __name__ == "__main__":
    # Declare a command line interface
    parser = ArgumentParser()
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=Path,
                        required=True,
                        help='The relative path to the task configuration file.')
    parser.add_argument('--headless',
                        dest='headless',
                        action='store_true',
                        help='A flag indicating whether to run the simulation in headless mode (fast) or not (slow).')

    # Extract parameters from the command line
    args = parser.parse_args()

    # Instantiate the task
    task = PushTask(config_path=args.config, headless=args.headless)

    # Reset the task
    task.reset()

    # Run the task
    task.run()
