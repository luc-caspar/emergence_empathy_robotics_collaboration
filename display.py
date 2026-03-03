#!/usr/bin/env python3
from multiprocessing import Process
from queue import Empty
import pyglet as pg


class Display(Process):
    
    def __init__(self, q, evt, fps):
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

        # Initalize empty properties required putting things on screen
        # Those will be initialized later when the process actually starts
        # This is required in order for the OpenGL context to be correctly loaded
        self._win = None
        self._batch = None
        self._shapes = {}
        self._fps = fps

        # Used for communication between the environment and display
        self._q = q
        self._evt = evt

    def create_shape(self, shape_type, shape_id, **kwargs):
        # Define the same batch for all objects
        kwargs.update({'batch': self._batch})

        # Actually create the object of the required type
        match shape_type:
            case "Circle":
                self._shapes[shape_id] = pg.shapes.Circle(**kwargs)
            case "Segment" | "Box":
                try:
                    rotation = kwargs['rotation']
                    del kwargs['rotation']
                except KeyError:
                    rotation = 0
                self._shapes[shape_id] = pg.shapes.Rectangle(**kwargs)
                self._shapes[shape_id].anchor_position = (kwargs['width'] / 2, kwargs['height'] / 2)
                self._shapes[shape_id].rotation = rotation
            case _:
                self._evt.set()
                raise NotImplementedError(f'Cannot create a shape of type: {shape_type}')

    def delete_shape(self, shape_id):
        # Remove the shape from the list of shapes and from the display all together
        try:
            del self._shapes[shape_id]
        except KeyError:
            print("This should not happen. Let's ignore it.")

    def init_display(self):
        # Initialize the window
        self._win = pg.window.Window()
        # The "clear" color used when calling `window.clear()`
        pg.gl.glClearColor(1,1,1,1)
        # Let the window know how to draw things
        self._win.push_handlers(on_draw=self.on_draw, on_close=self.on_close)

        # Initialize a batch
        self._batch = pg.graphics.Batch()


    def on_draw(self):
        if not self._win.has_exit:
            # Get the data to display next
            try:
                msgs = self._q.get(timeout=1)
            except Empty:
                # Nothing new, assume this is the end of the environment, closing the window
                self._win.close()
                return 

            for msg in msgs:
                # Dispatch commands as requested by message
                match msg['cmd']:
                    case 'display':
                        # Extract the data from the message
                        data = msg['data']

                        # Clear the window
                        self._win.clear()

                        # Update display according to content of `data`
                        for obj in data:
                            try:
                                # Modify the position of existing shape
                                # This assumes that the shape created can be moved using (x, y) alone
                                self._shapes[obj[0]].x = obj[1]
                                self._shapes[obj[0]].y = obj[2]
                                self._shapes[obj[0]].rotation = obj[3]
                                curr_color = self._shapes[obj[0]].color
                                self._shapes[obj[0]].color = (*curr_color[0:3], obj[4])  # Use health to decrease opacity
                            except KeyError:
                                print("This should not happen. Let's ignore it")

                        # Draw everything, everywhere, and all at once
                        self._batch.draw()
                    case 'create':
                        # Extract the arguments from the message
                        kwargs = msg['data']

                        # Create the shape
                        self.create_shape(**kwargs)
                    case 'delete':  # Required to avoid deleting static objects
                        # Extract the shape's id from the message
                        shape_id = msg['data']['shape_id']
                        # Delete the thing
                        self.delete_shape(shape_id)
                    case _:
                        self._evt.set()
                        raise NotImplementedError(f'The command: {msg["cmd"]} has not been implemented yet.')

    def on_close(self):
        # Let the main process know that the window closed
        if not self._evt.is_set():
            self._evt.set()
            
        # Propagate the standard closing process
        return self._win.on_close()

    def run(self):
        # Initialize the display and its context
        self.init_display()

        try:
            # Run the loop forever
            pg.app.run(interval=1/self._fps)
        except RuntimeError:
            if not self._evt.is_set():
                self._evt.set()
