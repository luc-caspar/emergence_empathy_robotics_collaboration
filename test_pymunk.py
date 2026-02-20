#!/usr/bin/env python3
from time import sleep
import pymunk as pm
import pyglet as pg
from threading import Thread, Event
from queue import Queue, Empty


FPS = 60

# /!\ Pyglet coordinate system originates in the lower-left corner
class Display(Thread):
    """Defines a threaded window to display the environment's state."""

    def __init__(self, q, evt):
        """
        Parameters:
        -----------
        q: queue.Queue
            A queue for communicating environment states between the physics engine and the display.

        evt: threading.Event
            A flag signaling the end of an experiment, at which time the window should be closed.

        """
        # Initialize the parent class
        super().__init__()

        self._win = pg.window.Window()
        self._q = q
        self._evt = evt

    def on_draw(self):
        # Let the main thread now that the window closed
        if self._win.has_exit:
            self._evt.set()
        else:
            # Get the data to display next
            try:
                data = self._q.get(timeout=3)
            except Empty:
                # Nothing new, closing the window
                self._win.close()

            # Clear the window
            self._win.clear()

            # TODO: Update display according to content of `data`

    def run(self):
        # Let the window know how to draw things
        self._win.push_handlers(on_draw=self.on_draw)

        try:
            # Run the loop forever
            pg.app.run(interval=1/FPS)
        except RuntimeError:
            if not self._evt.is_set():
                self._evt.set()


if __name__ == "__main__":
    # Create the environment
    env = pm.Space()
    env.gravity = (0, -9.81)

    # Instantiate a window to display the state
    q = Queue()
    end_evt = Event()
    disp = Display(q, end_evt)
    disp.start()

    # Let the world evolve
    cnt = 0
    while not end_evt.is_set():  # Do not stop the simulation if the display closes
        cnt += 1
        env.step(1 / FPS)
        # TODO: Stop queuing data if window is closed (i.e.: `end_evt.is_set()`)
        sleep(1 / FPS)  # Do not wait for the display to move on with the simulation
        if cnt == 180:
            end_evt.set() # Do not close the display when the simulation is done

    # Wait for the display to close
    disp.join()
