#!/usr/bin/env python3
from argparse import ArgumentParser
import pymunk as pm
import pyglet as pg
from multiprocessing import Process, Event, Queue
from queue import Empty


# /!\ Pyglet coordinate system originates in the lower-left corner
class Display(Process):
    """Defines a window to display the environment's state."""

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

        self._win = None  # This is necessary otherwise the openGL environment is not correctly initialized
        self._batch = None
        self._shapes = {}  # Keep track of existing objects, keyed by their ID
        self._groups = None 
        self._q = q
        self._evt = evt

    def on_close(self):
        # Let the main thread now that the window closed
        if not self._evt.is_set():
            self._evt.set()
            # Propagate the standard closing process
            return self._win.on_close()

    def on_draw(self):
        # TODO: Split that into an init_display() and on_draw() function
        # TODO: init_display() creates all the objects
        if not self._win.has_exit:
            # Get the data to display next
            try:
                data = self._q.get(timeout=1)
            except Empty:
                # Nothing new, closing the window
                self._win.close()
                return 

            # Clear the window
            self._win.clear()

            # Update display according to content of `data`
            curr_ids = set()
            for obj in data:
                curr_ids.add(obj[1])
                if obj[0] == 'Circle':
                    try:
                        # Modify the position of existing shape
                        self._shapes[obj[1]].x = obj[3]
                        self._shapes[obj[1]].y = obj[4]
                    except KeyError:
                        print('New Circle')
                        # Otherwise create new shape in the right location
                        self._shapes[obj[1]] = pg.shapes.Circle(obj[3],
                                                                obj[4],
                                                                radius=obj[5],
                                                                color=(255, 0, 0),
                                                                batch=self._batch,
                                                                group=self._groups[obj[2]])
                elif obj[0] == 'Segment':
                    try:
                        # Modify the position of existing shape
                        self._shapes[obj[1]].x = obj[3][0]
                        self._shapes[obj[1]].y = obj[3][1]
                        self._shapes[obj[1]].x2 = obj[4][0]
                        self._shapes[obj[1]].y2 = obj[4][1]
                    except KeyError:
                        print('New Segment')
                        # Otherwise create new shape in the right location
                        self._shapes[obj[1]] = pg.shapes.Line(obj[3][0], obj[3][1],
                                                              obj[4][0], obj[4][1],
                                                              thickness=obj[5],
                                                              color=(255, 0, 0),
                                                              batch=self._batch,
                                                              group=self._groups[obj[2]])

            # Remove non-existent shapes from storage
            # TODO: This might be un-necessary, and slowing us down. Therefore, you might want to remove it.
            for k in set(self._shapes.keys()).difference(curr_ids):
                print(k)
                del self._shapes[k]

            # Draw everything, everywhere, and all at once
            self._batch.draw()

    def init(self):
        # Initialize the window
        self._win = pg.window.Window()
        # Let the window know how to draw things
        self._win.push_handlers(on_draw=self.on_draw, on_close=self.on_close)

        # Initialize a batch
        self._batch = pg.graphics.Batch()

        # Initialize the groups (this is only for graphics and does not impact grouping in the physics simulation)
        self._groups = {k: pg.graphics.Group() for k in [pm.Body.DYNAMIC, pm.Body.KINEMATIC, pm.Body.STATIC]}

    def run(self):
        # Initialize the display and its context
        self.init()

        try:
            # Run the loop forever
            pg.app.run(interval=1/30)
        except RuntimeError:
            if not self._evt.is_set():
                self._evt.set()


if __name__ == "__main__":
    # Declare a command line interface
    parser = ArgumentParser()
    parser.add_argument('--headless',
                        dest='headless',
                        action='store_true',
                        help='A flag indicating whether to run the simulation in headless mode or not.')

    # Gather any command line argument
    args = parser.parse_args()

    # Create the environment
    env = pm.Space()
    env.gravity = (0, -9.81)

    # Put a ball at altitude in the environment
    bdy = pm.Body()
    ball = pm.Circle(body=bdy, radius=10)
    ball.elasticity = 1  # perfect bounce
    ball.friction = 0  # frictionless
    ball.mass = 3  # mass defined on shape. Body mass and moment will be computed when object is added to environment

    # Add the ball in the environment
    bdy.position = (100, 100)
    env.add(bdy, ball)

    # Put a segment not too far from it
    bdy = pm.Body()
    seg = pm.Segment(body=bdy, a=(0, 0), b=(10, 10), radius=5)
    seg.mass = 5
    seg.friction = 0
    seg.elasticity = 1

    # Add the segment to the world
    bdy.position = (200, 200)
    env.add(bdy, seg)

    # Instantiate display thread to monitor environment state if necessary
    if not args.headless:
        q = Queue()
        end_evt = Event()
        disp = Display(q, end_evt)
        disp.start()

    try:
        # Let the world evolve
        cnt = 0
        while ball.body.position.y - ball.radius > 0:  # /!\ Do not stop the simulation if the display closes
            env.step(1 / 30)

            # Do not queue data if the display does not exist
            if not (args.headless or end_evt.is_set()):
                # TODO: Split that into an init_env() and step() functions
                # Send only the shapes to the display thread
                shapes = []
                for shape in env.shapes:
                    if type(shape) is pm.shapes.Circle:
                        shapes.append(('Circle', shape.body.id, shape.body.body_type, shape.body.position.x, shape.body.position.y, shape.radius))
                    elif type(shape) is pm.shapes.Segment:
                        shapes.append(('Segment', shape.body.id, shape.body.body_type, shape.a, shape.b, shape.radius))

                # Send the data to the display
                q.put(list(shapes))

    finally:
        # Wait for the display to close if necessary
        if not args.headless:
            disp.join()
