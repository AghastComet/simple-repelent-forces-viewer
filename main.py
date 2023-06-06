from PySide6.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QHBoxLayout, QDoubleSpinBox, QPushButton
from PySide6.QtCore import QTimer, Slot
from PySide6.QtGui import QPixmap
from PIL import Image
from PIL.ImageQt import ImageQt
import random

INITAL_WALL_FORCE = 2
INITAL_DOT_FORCE = 0.1
UNSCALED_SIZE = 100
INITAL_FRICTION = 0

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.image = QLabel()
        im = Image.new("RGB", (500,500))
        qim = ImageQt(im)
        pixmap = QPixmap.fromImage(qim)
        self.image.setPixmap(pixmap)
        layout.addWidget(self.image)

        add_remove_layout = QHBoxLayout()
        add_button = QPushButton("Add Dot")
        remove_button = QPushButton("Remove Random Dot")
        remove_offscreen_button = QPushButton("Remove Offscreen Dots")
        add_button.pressed.connect(self.add_dot)
        remove_button.pressed.connect(self.remove_dot)
        remove_offscreen_button.pressed.connect(self.remove_offscreen_dot)
        add_remove_layout.addWidget(add_button)
        add_remove_layout.addWidget(remove_button)
        add_remove_layout.addWidget(remove_offscreen_button)
        layout.addLayout(add_remove_layout)


        friction_layout = QHBoxLayout()
        friction_layout.addWidget(QLabel("Dot Friction"))
        self.friction = QDoubleSpinBox()
        self.friction.setMinimum(0)
        self.friction.setMaximum(1)
        self.friction.setSingleStep(0.01)
        self.friction.setValue(INITAL_FRICTION)
        
        friction_button = QPushButton("Set Friction")
        friction_button.clicked.connect(self.change_friction)
        friction_layout.addWidget(self.friction)
        friction_layout.addWidget(friction_button)
        layout.addLayout(friction_layout)

        wall_force_layout = QHBoxLayout()
        wall_force_layout.addWidget(QLabel("Set repelent force of wall"))
        self.wall_force = QDoubleSpinBox()
        self.wall_force.setSingleStep(0.1)
        self.wall_force.setValue(INITAL_WALL_FORCE)
        
        wall_force_button = QPushButton("Set Force")
        wall_force_button.clicked.connect(self.set_wall_force)
        wall_force_layout.addWidget(self.wall_force)
        wall_force_layout.addWidget(wall_force_button)
        layout.addLayout(wall_force_layout)

        dot_force_layout = QHBoxLayout()
        dot_force_layout.addWidget(QLabel("Set repelent force of dots"))
        self.dot_force = QDoubleSpinBox()
        self.dot_force.setSingleStep(0.1)
        self.dot_force.setValue(INITAL_DOT_FORCE)
        
        dot_force_button = QPushButton("Set Force")
        dot_force_button.clicked.connect(self.set_dot_force)
        dot_force_layout.addWidget(self.dot_force)
        dot_force_layout.addWidget(dot_force_button)
        layout.addLayout(dot_force_layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000//22)
        self.i = 0

        self.simulator = Simulator()

        self.setLayout(layout)
        self.show()

    @Slot()
    def set_dot_force(self):
        self.simulator.dot_force = self.dot_force.value()

    @Slot()
    def set_wall_force(self):
        self.simulator.wall_force = self.wall_force.value()

    @Slot()
    def add_dot(self):
        self.simulator.dots.append(Dot())

    @Slot()
    def remove_dot(self):
        if len(self.simulator.dots) == 0:
            return
        self.simulator.dots[random.randrange(len(self.simulator.dots))] = self.simulator.dots[-1]
        self.simulator.dots = self.simulator.dots[:-1]

    @Slot()
    def remove_offscreen_dot(self):
        dots = []
        for dot in self.simulator.dots:
            if 0 <= dot.x <= 1 and 0 <= dot.y <= 1:
                dots.append(dot)
        self.simulator.dots = dots

    @Slot()
    def change_friction(self):
        self.simulator.friction = self.friction.value()

    @Slot()
    def tick(self):
        self.simulator.step()
        im = Image.new("RGB", (UNSCALED_SIZE,UNSCALED_SIZE))
        pixels = im.load()
        for x in range(UNSCALED_SIZE):
            for y in range(UNSCALED_SIZE):
                px = x/UNSCALED_SIZE
                py = y/UNSCALED_SIZE
                colors = self.simulator.get_color(px,py)
                pixels[x,y] = tuple(int(abs(c)*255) for c in colors)

        im = im.resize((500,500), resample=Image.Resampling.BILINEAR)
        qim = ImageQt(im)
        pixmap = QPixmap.fromImage(qim)
        self.image.setPixmap(pixmap)

class Dot:
    def __init__(self):
        self.x = random.random()
        self.y = random.random()
        self.vx = 0
        self.vy = 0
    def set_velocity(self, dots, friction, wall_force, dot_force):
        dvx,dvy = 0,0
        for dot in dots:
            if dot != self:
                dist = (self.x - dot.x)**2 + (self.y - dot.y)**2
                dvx += (self.x-dot.x)/dist*dot_force
                dvy += (self.y-dot.y)/dist*dot_force

        dvx -= self.x**2 * wall_force
        dvx += (1-self.x)**2 * wall_force
        dvy -= self.y**2 * wall_force
        dvy += (1-self.y)**2 * wall_force

        self.vx += dvx/1000
        self.vy += dvy/1000
        self.vx *= (1-friction)
        self.vy *= (1-friction)
    def set_position(self):
        self.x += self.vx * 0.3
        self.y += self.vy * 0.3

class Simulator():
    def __init__(self):
        self.dots = []
        self.friction = INITAL_FRICTION
        self.wall_force = INITAL_WALL_FORCE
        self.dot_force = INITAL_DOT_FORCE
    def step(self):
        for dot in self.dots:
            dot.set_velocity(self.dots, self.friction, self.wall_force, self.dot_force)
        for dot in self.dots:
            dot.set_position()
    def get_color(self, x, y):
        dvx,dvy = 0,0
        for dot in self.dots:
                dist = (x - dot.x)**2 + (y - dot.y)**2
                dvx += (x-dot.x)/dist*self.dot_force
                dvy += (y-dot.y)/dist*self.dot_force
        dvx -= x**2 * self.wall_force
        dvx += (1-x)**2 * self.wall_force
        dvy -= y**2 * self.wall_force
        dvy += (1-y)**2 * self.wall_force
        return dvx, 0, dvy
    
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle("Repellent Forces")
    window.show()
    sys.exit(app.exec())
