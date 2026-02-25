#!/usr/bin/env python3
import pymunk as pm
from math import sin, cos, radians, degrees


class Environment:
    def __init__(self, config, fps, disp_q=None, disp_evt=None):
        self._env = None
        self._config = config

        self._headless = disp_q is None or disp_evt is None
        self._disp_q = disp_q
        self._disp_evt = disp_evt

        self._id_to_pm_id = {}
        self._objs = {}
        self._joints = {}

        self._fps = fps

    def create_shape(self, shape_type, **kwargs):
        msg = {}
        match shape_type:
            case 'Circle':
                # Create the required body and shape
                bdy = pm.Body(kwargs.get('body_type', pm.Body.DYNAMIC))
                bdy.position = (kwargs.get('x', 0), kwargs.get('y', 0))
                shape = pm.shapes.Circle(body=bdy, radius=kwargs.get('radius', 10))
                shape.mass = kwargs.get('mass', 1) 
                shape.elasticity = kwargs.get('elasticity', 0)  # No bounce
                shape.friction = kwargs.get('friction', 0)  # Frictionless
                # and add them to the display if relevant
                if not (self._headless or self._disp_evt.is_set()):
                    msg = {'cmd': 'create',
                           'data': {'shape_type': 'Circle',
                                    'shape_id': bdy.id,
                                    'x': bdy.position.x,
                                    'y': bdy.position.y,
                                    'radius': shape.radius,
                                    'color': (255, 0, 0)}}
            case 'Segment':
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

                # Instantiate the body and shape
                bdy = pm.Body(kwargs.get('body_type', pm.Body.DYNAMIC))
                bdy.position = (x, y)
                bdy.angle = radians(rotation)
                shape = pm.shapes.Segment(body=bdy, a=(x1, y1), b=(x2, y2), radius=height)
                shape.mass = kwargs.get('mass', 1) 
                shape.elasticity = kwargs.get('elasticity', 0)  # No bounce
                shape.friction = kwargs.get('friction', 0)  # Frictionless

                # and add them to the display if relevant
                if not (self._headless or self._disp_evt.is_set()):
                    msg = {'cmd': 'create',
                           'data': {'shape_type': 'Segment',
                                    'shape_id': bdy.id,
                                    'width': width,
                                    'height': height,
                                    'rotation': rotation,
                                    'x': x,
                                    'y': y,
                                    'color': (0, 255, 0)}}
            case _:
                raise NotImplementedError(f'Cannot create a shape of type: {shape_type}')

        # Add to the environment
        self._env.add(bdy, shape)
        
        # Keep track of mapping between pymunk ID and shapes
        self._objs[bdy.id] = shape
        # As well as between given ID and pymunk ID
        self._id_to_pm_id[kwargs.get('id', len(self._id_to_pm_id))] = bdy.id

        return msg

    def create_joint(self, joint_type, **kwargs):
        # Translate the IDs to pymunk IDs
        pm_a = self._it_to_pm_id[kwargs['id_a']]
        pm_b = self._it_to_pm_id[kwargs['id_b']]

        # Create required joint
        match joint_type:
            case 'PinJoint':
                j = pm.PinJoint(self._objs[pm_a].body,
                                self._objs[pm_b].body,
                                kwargs.get('anchor_a', (0, 0)),
                                kwargs.get('anchor_b', (0, 0)))
            case _:
                raise NotImplementedError(f'Cannot create a joint of type: {joint_type}')

        # Add to the environment
        self._env.add(j)

    def to_display(self):
        return [(k, s.body.position.x, s.body.position.y, degrees(s.body.angle)) for k, s in self._objs.items() if s.body.body_type != pm.Body.STATIC]

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
        msgs = [self.create_shape(**obj) for obj in self._config.get('objects', [])]
        if not (self._headless or self._disp_evt.is_set()):
            self._disp_q.put(msgs)

        # Create and configure all initial joints
        for joint in self._config.get('joints', []):
            self.create_joint(**joint)

    def step(self):
        self._env.step(1/self._fps)

    def observe(self):
        # TODO: return observation, reward, and termination/end
        pass
