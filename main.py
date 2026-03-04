#!/usr/bin/env python3
from argparse import ArgumentParser
from pathlib import Path
from multiprocessing import Queue, Event
import json
from display import Display
from environments import Environment
from settings import FPS


if __name__ == "__main__":
    # Declare a command line interface
    parser = ArgumentParser()
    parser.add_argument('-c', '--config',
                        dest='config',
                        type=Path,
                        required=True,
                        help='The relative path to the environment configuration file.')
    parser.add_argument('--headless',
                        dest='headless',
                        action='store_true',
                        help='A flag indicating whether to run the simulation in headless mode or not.')

    # Extract parameters from the command line
    args = parser.parse_args()

    # Load the configuration
    config_path = args.config.expanduser().resolve()
    if config_path.exists() and config_path.is_file():
        with config_path.open('r') as config_file:
            config = json.load(config_file)
        
        # If relevant instantiate and run the display
        if not args.headless:
            disp_q = Queue()
            disp_evt = Event()
            display = Display(disp_q, disp_evt, FPS, config.get('width', 100), config.get('height', 100))
            display.start()
        else:
            disp_q = None
            disp_evt = None

        try:
            # Instantiate the environment
            env = Environment(config, FPS, disp_q, disp_evt)

            # Reset the environment
            env.reset()

            # TODO: step through the environment for some time
            for i in range(FPS * 12):
                env.step(1 / FPS)

                # TMP: Apply an impulse to the segment
                # This is only to test the PinJoint
                # TODO: Why does the segment jump to the side on first application of local impulse?
                seg = env.get_obj(0)
                seg.body.apply_impulse_at_local_point(impulse=(0, 2))

                # If relevant send information to the display
                if not(args.headless or disp_evt.is_set()):
                    msg = {'cmd': 'display',
                           'data': env.to_display()}
                    disp_q.put([msg])

        finally:
            # If relevant wait for the display to stop
            if not(args.headless or disp_evt.is_set()):
                display.join()
    else:
        print(f'Error: file does not exist or you do not have access to it: {config_path}')
