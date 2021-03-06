import ray
import matplotlib.pyplot as plt
import numpy as np
from math import sqrt

class Point:

    def __init__(self, mouse, x=0, y=0, z=0):
        self.mouse = mouse
        self.x = x
        self.y = y
        self.z = z
        self.px = x
        self.py = y
        self.pz = z
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.constraints = []
        self.pinned = False

    def add_constraint(self, pt):
        self.constraints.append(Constraint(self, pt))

    def add_force(self, x, y, z=0):
        if self.pinned:
            return
        self.vx += x
        self.vy += y
        self.vz += z

    def resolve_constraints(self):
        for constraint in self.constraints:
            constraint.resolve()
        boundsx = 800
        boundsy = 800
        boundsz = 800
        if self.x >= boundsx:
            self.x = 2 * boundsx - self.x
        elif self.x < 1:
            self.x = 2 - self.x
        if self.y >= boundsy:
            self.y = 2 * boundsy - self.y
        elif self.y < 1:
            self.y = 2 - self.y
        if self.z >= boundsz:
            self.z = 2 * boundsz - self.z
        elif self.z <= -boundsz:
            self.z = -2 * boundsz - self.z

    def update(self, delta):
        if self.mouse.down:
            dx = self.x - self.mouse.x
            dy = self.y - self.mouse.y
            dz = self.z - self.mouse.z
            dist = sqrt(dx ** 2 + dy ** 2)

            if self.mouse.button == 1:
                if dist < self.mouse.influence:
                    self.px = self.x - (self.mouse.x - self.mouse.px) * 1.8
                    self.py = self.y - (self.mouse.y - self.mouse.py) * 1.8
            elif dist < self.mouse.cut and (not self.mouse.height_limit or abs(dz) < self.mouse.height_limit):
                print dz
                self.constraints = []

        # gravity parameter, increase magnitude to increase gravity
        gravity = -7000
        self.add_force(0, 0, gravity)
        delta *= delta

        nx = self.x + ((self.x - self.px)) * 0.99 + ((self.vx / 2.0) * delta)
        ny = self.y + ((self.y - self.py)) * 0.99 + ((self.vy / 2.0) * delta)
        nz = self.z + ((self.vz / 2.0) * delta)

        self.px = self.x
        self.py = self.y
        self.pz = self.z

        self.x = nx
        self.y = ny
        self.z = nz

        self.vx = 0
        self.vy = 0
        self.vz = 0

class Constraint:

    def __init__(self, p1=None, p2=None, tear_dist=100):
        self.p1 = p1
        self.p2 = p2
        self.length = sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2 + (p1.z - p2.z) ** 2)
        self.tear_dist = tear_dist

    def resolve(self):
        dx = self.p1.x - self.p2.x
        dy = self.p1.y - self.p2.y
        dz = self.p1.z - self.p2.z
        dist = sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        diff = (self.length - dist) / float(dist)

        if dist > self.tear_dist:
            self.p1.constraints.remove(self)

        # Elasticity, usually pick something between 0.01 and 1.5
        elasticity = 1.2

        px = dx * diff * 0.5 * elasticity
        py = dy * diff * 0.5 * elasticity
        pz = dz * diff * 0.5 * elasticity

        if not self.p1.pinned:
            self.p1.x += px
            self.p1.y += py
            self.p1.z += pz

        if not self.p2.pinned:
            self.p2.x -= px
            self.p2.y -= py
            self.p2.z -= pz

class Cloth:

    def __init__(self, mouse, width, height, dx, dy):
        self.mouse = mouse
        self.pts = []
        for i in range(height):
            for j in range(width):
                pt = Point(self.mouse, 50 + dx * j, 50 + dy * i)
                if i > 0:
                    pt.add_constraint(self.pts[width * (i - 1) + j])
                if j > 0:
                    pass
                    pt.add_constraint(self.pts[-1])
                if i == height - 1 or i == 0:
                    pt.pinned = True
                self.pts.append(pt)

    def update(self):
        # Setting this to 5 is pretty decent, probably don't need to increase it
        physics_accuracy = 5
        for i in range(physics_accuracy):
            for pt in self.pts:
                pt.resolve_constraints()
        for pt in self.pts:
            pt.update(0.016, self.mouse)
        for pt in self.pts:
            if pt.constraints == []:
                self.pts.remove(pt)

class CircleCloth(Cloth):

    def __init__(self, mouse, width, height, dx, dy, centerx, centery, radius):
        self.mouse = mouse
        self.pts = []
        self.circlepts = []
        self.normalpts = []
        self.grabbed_pts = []
        for i in range(height):
            for j in range(width):
                pt = Point(self.mouse, 50 + dx * j, 50 + dy * i)
                if i > 0:
                    pt.add_constraint(self.pts[width * (i - 1) + j])
                if j > 0:
                    pass
                    pt.add_constraint(self.pts[-1])
                if i == height - 1 or i == 0:
                    pt.pinned = True
                if abs((pt.x - centerx) **2 + (pt.y - centery) ** 2 - radius **2) < 2000:
                    self.circlepts.append(pt)
                else:
                    self.normalpts.append(pt)
                self.pts.append(pt)

    def update(self):
        physics_accuracy = 5
        for i in range(physics_accuracy):
            for pt in self.pts:
                pt.resolve_constraints()
        for pt in self.pts:
            pt.update(0.016)
        for pt in self.pts:
            if pt.constraints == []:
                self.pts.remove(pt)
                if pt in self.circlepts:
                    self.circlepts.remove(pt)
                else:
                    self.normalpts.remove(pt)

    def pin_position(self, x, y):
        count = 0
        for pt in self.pts:
            if abs((pt.x - x) ** 2 + (pt.y - y) ** 2) < 1000:
                count += 1
                pt.pinned = True
                self.grabbed_pts.append(pt)
        print count

    def unpin_position(self, x, y):
        if abs((pt.x - x) ** 2 + (pt.y - y) ** 2) < 1000:
            pt.pinned = False
            self.grabbed_pts.remove(pt)

    def tension(self, x, y, z=0):
        for pt in self.grabbed_pts:
            pt.x += x
            pt.y += y
            pt.z += z
            pt.px = pt.x
            pt.py = pt.y
            pt.pz = pt.z
        print [(pt.x, pt.y, pt.pinned) for pt in self.grabbed_pts]

class Mouse:

    def __init__(self, x=0, y=0, z=0, height_limit=False):
        self.down = False
        self.button = 0
        self.x = x
        self.y = y
        self.z = z
        self.px = x
        self.py = y
        self.pz = z
        self.cut = 10
        self.influence = 5
        self.height_limit=height_limit

    def move(self, x, y):
        self.px = self.x
        self.py = self.y
        self.x = x
        self.y = y


@ray.remote([], [int])
def simulate_cloth():

    mouse = Mouse(0, 300, 0, 100)
    mouse.down = True
    mouse.button = 0

    circlex = 300
    circley = 300
    radius = 150

    c = CircleCloth(mouse, 100, 100, 5,5, circlex, circley, radius)
    c.update()

    c.pin_position(circlex, circley)

    plt.ion()

    for i in range(5):
        plt.clf()
        pts = np.array([[p.x, p.y] for p in c.normalpts])
        cpts = np.array([[p.x, p.y] for p in c.circlepts])
        plt.scatter(pts[:,0], pts[:,1], c='w')
        plt.scatter(cpts[:,0], cpts[:,1], c='b')
        ax = plt.gca()
        plt.axis([0, 600, 0, 600])
        ax.set_axis_bgcolor('white')
        plt.pause(0.01)
        c.update()


        # simulate moving the mouse in a circle while cutting, overcut since no perception
        if i < 150:
            theta = 360.0/100.0 * i * np.pi / 180.0
            x = radius * np.cos(theta)
            y = radius * np.sin(theta)

            mouse.move(x + circlex, y + circley)

        # Still testing this stuff
        # if i < 20:
        #     c.tension(0, 0, 2)
        # if i >= 50 and i < 60:

        #     c.tension(-1, 1, 1)

    # return something, so that we can call ray.get to wait for this task to finish
    return 0

if __name__ == "__main__":

    ray.init(start_ray_local=True, num_workers=2)

    # launch two simulations in parallel
    result1 = simulate_cloth.remote()
    result2 = simulate_cloth.remote()

    # wait for the first simulation to finish
    ray.get(result1)
    # wait for the second simulation to finish
    ray.get(result2)
