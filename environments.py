#!/usr/bin/env python3
import pymunk as pm
from math import sin, cos, radians, degrees


class Environment:
    def __init__(self, config, disp_q=None, disp_evt=None):
        self._env = None
        self._config = config

        self._headless = disp_q is None or disp_evt is None
        self._disp_q = disp_q
        self._disp_evt = disp_evt

        self._id_to_pm_id = {}
        self._objs = {}

        self._width = config.get('width', 100)
        self._height = config.get('height', 100)

    def _create_segment(self, **kwargs):
        # Compute the shape's features based on the given data
        # This is required because pymunk and pyglet do not declare shapes in the same way
        x = kwargs.get('x', 0) 
        y = kwargs.get('y', 0)
        width = kwargs.get('width', 10)
        height = kwargs.get('height', 10)
        rotation = kwargs.get('rotation', 0)
        x1 = x - cos(radians(rotation)) * width / 2
        x2 = x + cos(radians(rotation)) * width / 2
        y1 = y - sin(radians(rotation)) * width / 2
        y2 = y + sin(radians(rotation)) * width / 2

        # Allows for body type to be specified as a constant/string
        body_type = kwargs.get('body_type', pm.Body.DYNAMIC)
        if isinstance(body_type, str):
            body_type = getattr(pm.Body, body_type)
        # Instantiate the body and shape
        bdy = pm.Body(body_type=body_type)
        bdy.position = (x, y)
        bdy.angle = radians(rotation)
        bdy.health = kwargs.get('health')  # Allow to define health for agents
        shape = pm.shapes.Segment(body=bdy, a=(x1, y1), b=(x2, y2), radius=height)
        shape.mass = kwargs.get('mass', 1) 
        shape.elasticity = kwargs.get('bounce', 0)  # No bounce
        shape.friction = kwargs.get('friction', 0)  # Frictionless

        # and add them to the display if relevant
        msg = {}
        if not (self._headless or self._disp_evt.is_set()):
            msg = {'cmd': 'create',
                   'data': {'shape_type': 'Segment',
                            'shape_id': bdy.id,
                            'width': width,
                            'height': height,
                            'rotation': rotation,
                            'x': x,
                            'y': y,
                            'color': kwargs.get('color', (128, 128, 128))}}
        return shape, msg

    def _create_circle(self, **kwargs):
        msg = {}
        # Allows for body type to be specified as a constant/string
        body_type = kwargs.get('body_type', pm.Body.DYNAMIC)
        if isinstance(body_type, str):
            body_type = getattr(pm.Body, body_type)
        # Create the required body and shape
        bdy = pm.Body(body_type=body_type)
        bdy.position = (kwargs.get('x', 0), kwargs.get('y', 0))
        bdy.health = kwargs.get('health')
        shape = pm.shapes.Circle(body=bdy, radius=kwargs.get('radius', 10))
        shape.mass = kwargs.get('mass', 1) 
        shape.elasticity = kwargs.get('bounce', 0)  # No bounce
        shape.friction = kwargs.get('friction', 0)  # Frictionless
        # and add them to the display if relevant
        if not (self._headless or self._disp_evt.is_set()):
            msg = {'cmd': 'create',
                   'data': {'shape_type': 'Circle',
                            'shape_id': bdy.id,
                            'x': bdy.position.x,
                            'y': bdy.position.y,
                            'radius': shape.radius,
                            'color': kwargs.get('color', (255, 0, 0))}}
        return shape, msg

    def _create_box(self, **kwargs):
        msg = {}
        # Extract position and rotation
        x = kwargs.get('x', 0) 
        y = kwargs.get('y', 0)
        rotation = kwargs.get('rotation', 0)
        # Compute the vertices that make the box based on the width and height
        width = kwargs.get('width', 10)
        height = kwargs.get('height', 10)
        verts = [(-width/2, -height/2), (width/2, -height/2), (width/2, height/2), (-width/2, height/2)]
        # Allows for body type to be specified as a constant/string
        body_type = kwargs.get('body_type', pm.Body.DYNAMIC)
        if isinstance(body_type, str):
            body_type = getattr(pm.Body, body_type)
        # Instantiate the body and shape
        bdy = pm.Body(body_type=body_type)
        bdy.position = (x, y)
        bdy.angle = radians(rotation)
        bdy.health = kwargs.get('health')
        shape = pm.Poly(body=bdy, vertices=verts, radius=kwargs.get('radius', 0))
        shape.mass = kwargs.get('mass', 1) 
        shape.elasticity = kwargs.get('bounce', 0)  # No bounce
        shape.friction = kwargs.get('friction', 0)  # Frictionless

        # and add them to the display if relevant
        if not (self._headless or self._disp_evt.is_set()):
            msg = {'cmd': 'create',
                   'data': {'shape_type': 'Box',
                            'shape_id': bdy.id,
                            'width': width,
                            'height': height,
                            'rotation': rotation,
                            'x': x,
                            'y': y,
                            'color': kwargs.get('color', (0, 255, 0))}}
        return shape, msg

    def _create_poly(self, **kwargs):
        msg = {}
        # Extract position and rotation
        x = kwargs.get('x', 0) 
        y = kwargs.get('y', 0)
        rotation = kwargs.get('rotation', 0)
        # Extract the list of vertices that make up the polynomial shape
        verts = kwargs.get('vertices', [])
        # Allows for body type to be specified as a constant/string
        body_type = kwargs.get('body_type', pm.Body.DYNAMIC)
        if isinstance(body_type, str):
            body_type = getattr(pm.Body, body_type)
        # Instantiate the body and shape
        bdy = pm.Body(body_type=body_type)
        bdy.position = (x, y)
        bdy.angle = radians(rotation)
        bdy.health = kwargs.get('health')
        shape = pm.Poly(body=bdy, vertices=verts, radius=kwargs.get('radius', 0))
        shape.mass = kwargs.get('mass', 1) 
        shape.elasticity = kwargs.get('bounce', 0)  # No bounce
        shape.friction = kwargs.get('friction', 0)  # Frictionless

        # and add them to the display if relevant
        if not (self._headless or self._disp_evt.is_set()):
            msg = {'cmd': 'create',
                   'data': {'shape_type': 'Poly',
                            'shape_id': bdy.id,
                            'coordinates': verts,
                            'rotation': rotation,
                            'x': x,
                            'y': y,
                            'color': kwargs.get('color', (0, 255, 0))}}

        return shape, msg

    def _create_shape(self, shape_type, **kwargs):
        match shape_type.capitalize():
            case 'Circle':
                shape, msg = self._create_circle(**kwargs)
            case 'Segment':
                shape, msg = self._create_segment(**kwargs)
            case 'Box':
                shape, msg = self._create_box(**kwargs)
            case 'Poly':
                shape, msg = self._create_poly(**kwargs)
            case _:
                raise NotImplementedError(f'Cannot create a shape of type: {shape_type}')

        # Assign grouped filter to shape
        # TODO: Allow to specify categories and masks
        # TODO: Check if this is actually working or not
        # TODO: Also be aware that shapes that are constrained together can still collide depending on the value of `collide_bodies` assigned to the joint
        grp = kwargs.get('group')
        if grp is not None:
            shape.filter = pm.ShapeFilter(group=grp)

        # Add to the environment
        self._env.add(shape.body, shape)
        
        # Keep track of mapping between pymunk ID and shapes
        self._objs[shape.body.id] = shape
        # As well as between given ID and pymunk ID
        self._id_to_pm_id[kwargs.get('id', len(self._id_to_pm_id))] = shape.body.id

        return msg

    def _create_joint(self, joint_type, **kwargs):
        # Translate the IDs to pymunk IDs
        pm_a = self._id_to_pm_id[kwargs['id_a']]
        pm_b = self._id_to_pm_id[kwargs['id_b']]

        # Create required joint
        match joint_type:
            case 'PivotJoint':
                j = pm.PivotJoint(self._objs[pm_a].body,
                                self._objs[pm_b].body,
                                kwargs.get('pivot_point', (0, 0)))
            case 'PinJoint':
                j = pm.PinJoint(a=self._objs[pm_a].body,
                                b=self._objs[pm_b].body,
                                anchor_a=kwargs.get('anchor_a', (0, 0)),
                                anchor_b=kwargs.get('anchor_b', (0, 0)))
            case 'SlideJoint':
                j = pm.SlideJoint(self._objs[pm_a].body,
                                  self._objs[pm_b].body,
                                  kwargs.get('anchor_a', (0, 0)),
                                  kwargs.get('anchor_b', (0, 0)),
                                  kwargs['min'],  # Makes `min` a requirement
                                  kwargs['max'])  # Makes `max` a requirement
            case 'GrooveJoint':
                j = pm.GrooveJoint(self._objs[pm_a], self._objs[pm_b],
                                   groove_a=kwargs.get('groove_a', (-5, 5)), groove_b=kwargs.get('groove_b', (5, 5)),
                                   anchor_b=kwargs.get('anchor_b', (0, 0)))
            case _:
                raise NotImplementedError(f'Cannot create a joint of type: {joint_type}')

        j.collide_bodies = kwargs.get('collide_bodies', True)
        # Add to the environment
        self._env.add(j)

    def to_display(self):
        objs = []
        for k, s in self._objs.items():
            if s.body.body_type != pm.Body.STATIC:
                # TODO: Make sure `health` or the last value sent is in the interval [0, 255] since it will configure opacity
                if s.body.health is None:
                    opacity = 255
                else:
                    opacity = int(255 * s.body.health / 100)  # This is only an example
                objs.append((k, s.body.position.x, s.body.position.y, degrees(s.body.angle), opacity))
        return objs

    def get_obj(self, obj_id):
        """
        Retrieves the object with id `obj_id` from the environment.

        Parameters
        ----------
        obj_id: str | int
            The ID given to the object in the configuration file.

        Returns
        -------
        PyMunk.Shape
            The shape corresponding to the given `obj_id` or None if nothing was found.
        """

        try:
            pm_id = self._id_to_pm_id[obj_id]
            return self._objs[pm_id]
        except KeyError:
            return None

    def reset(self):
        """
        Clears and initializes the environment.
        """

        # If relevant remove all objects from the display
        if not (self._headless or self._disp_evt.is_set()):
            self._disp_q.put([{'cmd': 'delete', 'data': {'shape_id': obj}} for obj in self._objs])

        # Get a new space and configure it
        self._env = pm.Space()
        self._env.gravity = self._config.get('gravity', (0, 0))

        # Initialize the list of objects
        self._objs = {}

        # Create and configure all initial objects
        msgs = [self._create_shape(**obj) for obj in self._config.get('objects', [])]
        if not (self._headless or self._disp_evt.is_set()):
            self._disp_q.put(msgs)

        # Create and configure all initial joints
        for joint in self._config.get('joints', []):
            self._create_joint(**joint)

        # Reindex any static shapes after movement
        self._env.reindex_static()

    def step(self, intval, acts):
        """
        Apply the agents' actions, and move the simulation forward.

        Parameters
        ----------
        intval: float
            The amount of time (in seconds) by which to move the simulation forward

        acts: dict
            A dictionary containing the action to apply for each agent (i.e.: `{"agt_id": act, ... }`

        """
        # TODO: apply agent actions first

        self._env.step(intval)

    def observe(self):
        raise NotImplementedError("Please implement your own environment and define its observation function.")


class PushEnv(Environment):
    """
    Defines a maze-like environment with a static goal for the Push task.
    """

    def reset(self):
        # Execute the parent's method first
        super().reset()

        # Modify the objects' categories and masks to allow pushables to go through outer walls, but not agents

    def observe(self):
        # TODO: Observe the new state, define the reward, and check if the task has been completed
        return None, None, False

