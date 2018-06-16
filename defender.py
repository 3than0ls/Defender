import math
import random
import pygame
from pygame.locals import *
from win32api import GetSystemMetrics
pygame.init()

# Display Settings
# width and height, on original device that as programmed on was 2560 and 1440
width = GetSystemMetrics(0)
height = GetSystemMetrics(1)  # possibly delete
display = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
"""
Part of the display resizing solution
screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)  # we use width and height JUST to make sure.
display = pygame.Surface((width, height))  # what we do is we have a surface display and scale it to the resolution
screen_display_scale_ratio = (width + height) / (2560 + 1440)
"""
icon = pygame.image.load('images/Asteroid (Medium).png')
pygame.display.set_icon(icon)
pygame.display.set_caption("Defender")


def end():
    global running
    running = False
    print('Exiting')
    pygame.quit()
    quit()


def text(window, col, rect, label, font_size):
    """A function that can render and display text on window."""
    font = pygame.font.Font("fonts/Coalition_v2..ttf", font_size)
    render = font.render(label, 1, col)
    new_rect = render.get_rect(center=(rect[0]+rect[2]/2, rect[1]+rect[3]/2))
    window.blit(render, new_rect)


class Button:
    """A Button class, built for all kinds of purposes"""
    def __init__(self, window, rect, message, off_color, on_color, message_color, message_font_size):
        # location
        self.rect = rect
        self.rect[0] -= self.rect[2]/2
        self.rect[1] -= self.rect[3]/2
        # message attributes
        self.message = message
        # on and off colors
        self.color = off_color
        self.o_f = off_color
        self.o_c = on_color
        # message color
        self.m_c = message_color
        # message font
        self.m_f_c = message_font_size
        # what surface to display on
        self.display = window

    def in_button(self):
        mouse_pos = pygame.mouse.get_pos()
        if pygame.Rect(self.rect).collidepoint(mouse_pos[0], mouse_pos[1]):
            return True

    def clicked(self):
        if self.in_button():
            self.color = self.o_c
            if pygame.mouse.get_pressed()[0]:
                return True
        else:
            self.color = self.o_f

    def draw(self):
        global text
        pygame.draw.rect(display, self.color, self.rect)
        text(self.display, self.m_c, self.rect, self.message, self.m_f_c)


class Spaceship:
    def __init__(self, loc=None, ship_type="destroyer"):
        self.loc = [width/2, height/2] if not loc else loc # spaceship needs to stay in center position
        self.images = [
            pygame.image.load("images\Frigate.png"),
            pygame.image.load("images\Fighter.png"),
            pygame.image.load("images\Destroyer.png")
        ]
        # We are not using rects for collision detections. This will be done with masks for pixel perfect collision.
        # We use rects to rotate the images on center and also draw them at locations
        self.image_rects = None
        # the masks
        self.mask = None
        # What kind of spaceship is it?
        self.type = ship_type
        # Moving variables
        self.directions = [0, 0]
        self.dir_override = False
        # the speed an acceleration
        self.acceleration = 0
        self.speed = 0
        self.max_speed = 4
        self.moving = False
        # Variables for transformations
        self.center = None
        # Angle at which the spaceship is pointing at
        self.angle = 0  # in degrees
        # mouse and keyboard variables
        self.kp = pygame.key.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        # the ships targeting system, so it doesn't turn instantly.
        self.target = [0, 0]
        self.easing = 0.1  # easing is how long the target will reach the mouse position
        # flames for aesthetics when moving, and info
        self.flame_image = pygame.image.load('images/Thruster Flames.png')
        self.flame_info = None # this will include a tuple that has flame distance from center and scale ration
        # ships stats
        if ship_type == "fighter":  # have to define it statically so it won't update to that value every loop
            self.health = 30
        elif ship_type == "frigate":
            self.health = 100
        elif ship_type == "destroyer":
            self.health = 250
        # ship shooting missile: attributes and stuff
        self.reload = 0
        self.reload_speed = 1
        self.missile_image = pygame.image.load("images/Missile.png")

    def controls(self):
        """controls the input from user"""
        # movement controls
        # this is the acceleration. It will also eventually include playing the music for the spaceship moving.
        if self.moving:  # speeds it up
            if self.speed < self.max_speed:
                self.acceleration += self.max_speed/100000
                self.speed += self.acceleration
            else:
                self.speed = self.max_speed
        else:
            self.speed = 0
            self.acceleration = 0
            self.directions[0] /= 1.05
            self.directions[1] /= 1.05

        # moving forwards
        if self.kp[K_w]:
            self.directions = [(self.target[0] - self.loc[0]), (self.target[1] - self.loc[1])]
            # distance must be defined here WHEN the ship is moving.
            distance = math.sqrt(self.directions[0]*self.directions[0]+self.directions[1]*self.directions[1])
            if distance != 0:
                self.directions[0] /= distance
                self.directions[1] /= distance
                self.directions[0] *= self.speed
                self.directions[1] *= self.speed
            self.moving = True

        # backing up
        elif self.kp[K_s] and Asteroid.collided:  # only used when collision
            self.dir_override = True  # the override allows ships to pass through asteroids. it makes it so you can
            # back up easier

            self.directions = [(self.target[0] - self.loc[0]), (self.target[1] - self.loc[1])]
            distance = math.sqrt(self.directions[0]*self.directions[0]+self.directions[1]*self.directions[1])
            if distance != 0:
                self.directions[0] /= -distance
                self.directions[1] /= -distance
                self.directions[0] *= self.speed*2
                self.directions[1] *= self.speed*2
            self.moving = True

        else:
            self.moving = False

    def rot_center(self, image, rect, angle):
        new_image = pygame.transform.rotate(image, angle)
        rect = new_image.get_rect(center=rect.center)
        return new_image, rect

    def frigate(self):
        """Defines the blueprint of the frigate type spaceship"""
        self.image_rects = self.images[0].get_rect(center=self.loc)
        self.center = (
            self.image_rects.centerx,
            self.image_rects.centery
        )
        self.easing = 0.025
        self.max_speed = 3.5
        rot_frigate, self.image_rects = self.rot_center(self.images[0], self.image_rects, self.angle-90)
        self.mask = pygame.mask.from_surface(rot_frigate)
        self.image_rects.center = self.loc
        display.blit(rot_frigate, self.image_rects)

    def fighter(self):
        """Defines the blueprint of the fighter type spaceship"""
        self.mask = pygame.mask.from_surface(self.images[1])
        self.image_rects = self.images[1].get_rect(center=self.loc)
        self.center = (
            self.image_rects.centerx,
            self.image_rects.centery
        )
        self.max_speed = 6
        self.easing = 0.5
        rot_fighter, self.image_rects = self.rot_center(self.images[1], self.image_rects, self.angle-90)
        self.mask = pygame.mask.from_surface(rot_fighter)
        self.image_rects.center = self.loc
        display.blit(rot_fighter, self.image_rects)

    def destroyer(self):
        """Defines the blueprint of the destroyer type spaceship"""
        self.mask = pygame.mask.from_surface(self.images[2])
        self.image_rects = self.images[2].get_rect(center=self.loc)
        self.center = self.image_rects.center
        self.max_speed = 3
        self.easing = 0.006
        rot_destroyer, self.image_rects = self.rot_center(self.images[2], self.image_rects, self.angle-90)
        self.mask = pygame.mask.from_surface(rot_destroyer)
        self.image_rects.center = self.loc
        display.blit(rot_destroyer, self.image_rects)

    def shoot_missile(self, list_of_missiles):
        """Code for drawing and moving projectiles launched from ship
        Pushes missiles into a global list, which is the drawn, and the camera is applied to it"""
        if self.reload <= 100:
            self.reload += self.reload_speed
        if pygame.mouse.get_pressed()[0] and self.reload > 100:
            if self.type == "destroyer":
                list_of_missiles.append(
                    Missile(
                        (self.center[0]+100*math.sin(math.radians(self.angle+35)),
                         self.center[1]+100*math.cos(math.radians(self.angle+35))),
                        self.angle)
                )
                list_of_missiles.append(
                    Missile(
                        (self.center[0]+100*math.sin(math.radians(self.angle+145)),
                         self.center[1]+100*math.cos(math.radians(self.angle+145))),
                        self.angle)
                )
            else:
                print("Shooting not yet implemented for this spaceship type.")
            self.reload = 0
        for missile in missile_list:
            missile.launch()
            missile.draw()

    def find_angle(self):
        if not Asteroid.collided:
            self.angle = math.degrees(-math.atan2(self.target[1]-self.center[1], self.target[0]-self.center[0]))

    def stat_display(self):
        # health display
        pygame.draw.rect(display, (255, 0, 0), (main_menu_button_on.rect[3], 0, self.health*10, 20))
        # reload display
        display.blit(self.missile_image, (width-75, height-100))
        pygame.draw.rect(display, (200, 200, 200), (width-80, height-100, 20, 100))
        pygame.draw.rect(display, (255, 255, 255), (width-80, height, 20, -self.reload))

    def draw_engine(self):
        # draw engine/moving flame
        if not (math.fabs(self.directions[0]) <= 0.008 and math.fabs(self.directions[1]) <= 0.008):
            # scale the flame
            scale_flame = pygame.transform.scale(
                self.flame_image,
                (self.flame_info[1], self.flame_info[1])
            )

            # get the rotated image and rect of the flame
            rot_flame, rot_rect = self.rot_center(scale_flame, self.flame_image.get_rect(), self.angle-90)
            # sets the center of the flame to be in a certain position
            if self.type == "fighter":
                rot_rect.center = (
                    self.image_rects.centerx + (self.flame_info[0]+math.fabs(self.directions[0]/2))
                    * math.sin(math.radians(self.angle-90)),
                    self.image_rects.centery + (self.flame_info[0]+math.fabs(self.directions[1])/2)
                    * math.cos(math.radians(self.angle-90))
                )
            elif self.type == "frigate":
                rot_rect.center = (
                    self.image_rects.centerx + (self.flame_info[0]+math.fabs(self.directions[0]*2.5))
                    * math.sin(math.radians(self.angle-90)),
                    self.image_rects.centery + (self.flame_info[0]+math.fabs(self.directions[1])*2.5)
                    * math.cos(math.radians(self.angle-90))
                )
            else:
                rot_rect.center = (
                    self.image_rects.centerx + (self.flame_info[0]-10+math.fabs(self.directions[0]*8))
                    * math.sin(math.radians(self.angle-90)),
                    self.image_rects.centery + (self.flame_info[0]-10+math.fabs(self.directions[1])*8)
                    * math.cos(math.radians(self.angle-90))
                )

            display.blit(rot_flame, rot_rect)

    def draw(self):
        self.draw_engine()

        if self.type == "fighter":
            self.fighter()
        elif self.type == "frigate":
            self.frigate()
        elif self.type == "destroyer":
            self.destroyer()

        if self.flame_info is None:  # updates the flame info needed to blit it properly with the right size - once
            self.flame_info = (self.image_rects.height/2, int(0.18*self.image_rects.width))

    def all(self):
        # We first update the attributes needed later in our methods
        # update key pressing
        self.kp = pygame.key.get_pressed()
        # updates mouse pressing
        self.mouse_pos = pygame.mouse.get_pos()

        # update mouse and target
        if not Asteroid.collided:
            self.target[0] += (self.mouse_pos[0] - self.target[0]) * self.easing
            self.target[1] += (self.mouse_pos[1] - self.target[1]) * self.easing  # apply easing
        pygame.draw.circle(display, [255, 0, 0], (int(self.target[0]), int(self.target[1])), 10)  # target circle

        # updates collision variables
        self.dir_override = False

        self.controls()
        self.draw()
        self.find_angle()


center_spaceship = Spaceship()


class Camera:
    def __init__(self, screen_width, screen_height):
        self.state = Rect(0, 0, width, height)
        self.direction = [0, 0]

    def apply(self, target):
        return target.rect.move(self.direction)

    def update(self, target):
        self.direction = target


camera = Camera(width, height)


class Missile:
    def __init__(self, loc, angle):
        self.angle = angle
        self.image = pygame.image.load("images\Missile.png")
        self.rect = self.image.get_rect(center=loc)
        self.loc = loc
        self.dir = 5
        self.speed = 1.5
        self.rot_missile = None
        self.hit = False
        self.destroyed = False
        self.mask = pygame.mask.from_surface(self.image)
        self.remove_from_list_countdown = 500
        # explosion variables
        self.explosion_image = pygame.image.load("images/Explosion.png")
        self.explosion_rect = self.explosion_image.get_rect()
        self.explosion_pos = None
        self.explosion_scale_size = 10
        self.explosion_scale_speed = 5

    def rot_center(self, image, rect):
        new_image = pygame.transform.rotate(image, self.angle-90)
        rect = new_image.get_rect(center=rect.center)
        return new_image, rect

    def launch(self):
        # create rotated missile with it's new rect
        self.rot_missile, self.rect = self.rot_center(self.image, self.rect)
        # assign the rect a center
        self.loc = (
            self.loc[0] + self.dir * math.sin(math.radians(self.angle + 90)) - Asteroid.directions[0],
            self.loc[1] + self.dir * math.cos(math.radians(self.angle + 90)) - Asteroid.directions[1]
        )
        self.rect.center = self.loc
        # self.dir += self.speed  # produces a nice effect of the missile speeding up

    def remove(self):
        if self.hit:
            self.remove_from_list_countdown -= 1

        if self.remove_from_list_countdown <= 0:
            self.destroyed = True

    def explode(self):
            # add functions to remove missile from missile list, decrease health, and more
            self.explosion_scale_size += self.explosion_scale_speed**2  # expand the explosion
            self.explosion_scale_speed /= 1.08  # make it so that the expanding slowly halts
            zoom_explosion = pygame.transform.scale(
                self.explosion_image,
                (int(self.explosion_scale_size), int(self.explosion_scale_size))
            )
            self.explosion_rect = zoom_explosion.get_rect(center=self.explosion_pos)
            display.blit(zoom_explosion, self.explosion_rect)

    def draw(self):
        self.remove()
        # update mask
        self.mask = pygame.mask.from_surface(self.rot_missile)
        # draws missile only when in display viewing to save time
        if -100 <= self.rect.centerx <= width+100 and -100 <= self.rect.centery <= height+100:
            if not self.hit:
                display.blit(self.rot_missile, self.rect)
        else:
            self.destroyed = True


# our missile list
missile_list = []


class Asteroid:
    directions = center_spaceship.directions
    collided = False

    def __init__(self, loc, size="large"):
        self.size = size
        self.loc = loc
        self.base_image = pygame.image.load('images/Asteroid (Medium).png')
        self.images = (
            pygame.transform.scale(self.base_image, (100, 100)),
            self.base_image,
            pygame.transform.scale(self.base_image, (400, 400))
        )
        self.image_rects = self.images[1].get_rect(center=self.loc)  # defaults to medium. May remove the center
        # the mask
        self.image_masks = pygame.mask.from_surface(self.images[2])
        self.damage = 0
        # explosion image - move to Missile class
        self.explosion_image = pygame.image.load("images/Explosion.png").convert()
        self.explosion_rect = self.explosion_image.get_rect()
        self.explosion_pos = None
        self.explosion_scale_size = self.explosion_rect.width

    def move(self):
        # self.loc[0] += -camera.direction[0]
        # self.loc[1] += -camera.direction[0]
        self.loc[0] += -Asteroid.directions[0]
        self.loc[1] += -Asteroid.directions[1]

    def in_display(self):
        """determines if asteroid is in display window, and if not, it will later be
         implemented to stop blitting and performing methods of  asteroids to reduce processing time"""
        return 0 - self.image_rects.width < self.loc[0] < width + self.image_rects.width \
            and 0 - self.image_rects.height < self.loc[1] < height + self.image_rects.height

    def small(self):
        self.image_rects = self.images[0].get_rect()
        self.image_masks = pygame.mask.from_surface(self.images[0])
        display.blit(self.images[0], self.loc)
        self.damage = 1

    def medium(self):
        self.image_rects = self.images[1].get_rect()
        self.image_masks = pygame.mask.from_surface(self.images[1])
        display.blit(self.images[1], self.loc)
        self.damage = 3

    def large(self):
        self.image_rects = self.images[2].get_rect()
        self.image_masks = pygame.mask.from_surface(self.images[2])
        display.blit(self.images[2], self.loc)
        self.damage = 5

    def draw(self):
        if self.size == "small":
            self.small()
        elif self.size == "medium":
            self.medium()
        elif self.size == "large":
            self.large()

    def collide_spaceship(self):
        """Detects and handles collision with spaceship"""
        offset_x = center_spaceship.loc[0]-self.loc[0]-center_spaceship.image_rects.width/2
        offset_y = center_spaceship.loc[1]-self.loc[1]-center_spaceship.image_rects.height/2
        overlap = self.image_masks.overlap(center_spaceship.mask, (int(offset_x), int(offset_y)))  # overlap is local

        if overlap is not None:
            Asteroid.collided = True
            center_spaceship.speed = 5
            if not center_spaceship.dir_override:
                center_spaceship.moving = False
                Asteroid.directions = [0, 0]
                # camera.directions = [0, 0]

    def collide_missile(self):
        """Detects and handles collisions with missiles"""
        global missile_list
        for missile in missile_list:
            offset_x = missile.rect.centerx-self.loc[0]-missile.rect.width/2
            offset_y = missile.rect.centery-self.loc[1]-missile.rect.height/2
            overlap = self.image_masks.overlap(missile.mask, (int(offset_x), int(offset_y)))  # overlap is local

            if overlap is not None:
                missile.hit = True
                missile.dir = 0  # makes the speed to nothing.
                missile.explosion_pos = self.loc[0]+overlap[0], self.loc[1]+overlap[1]
                missile.explode()

    def all(self):
        if self.in_display():
            self.draw()
        self.collide_spaceship()
        self.collide_missile()


asteroids = [Asteroid([random.randint(0, width), random.randint(0, height)]) for i in range(0, 1)]

# ------------------RUNNER------------------- move this down later
running = True
# ------------------SCENE CONTROLLER-------------------
scene = "START_MENU"   # scenes are START_MENU, GAME, and GAME.MAIN_MENU
# ------------------START MENU VARIABLES AND FUNCTION---------------------
start_menu_button_play = Button(
    display,
    [width/5, height*(1/4), width/4, height/5],
    "Start",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    40,
)

start_menu_button_exit = Button(
    display,
    [width/5, height*(3/4), width/4, height/5],
    "Exit",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    40,
)

background = pygame.image.load("images/Defender Background.jpg").convert()


def start_menu():
    global scene, background
    # draw the background
    display.blit(background, (0, 0))
    # game title
    text(display, [255, 255, 255], (width*1700/2560, height/2, 1, 1), "DEFENDER", int(width*150/2560)+10)
    start_menu_button_play.draw()
    if start_menu_button_play.clicked():
        scene = "GAME"
    start_menu_button_exit.draw()
    if start_menu_button_exit.clicked():
        end()


# ------------------MAIN MENU VARIABLES AND FUNCTION---------------------
main_menu_button_off = Button(
    display,
    [width/2, height/2-300, 400, 150],
    "Return",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    40
)
main_menu_button_start = Button(
    display,
    [width/2, height/2, 400, 150],
    "Home",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    40
)
main_menu_button_exit = Button(
    display,
    [width/2, height/2+300, 400, 150],
    "Exit",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    40
)


def main_menu():
    global scene, asteroids
    main_menu_button_off.draw()
    if main_menu_button_off.clicked():
        scene = "GAME"
    main_menu_button_start.draw()
    if main_menu_button_start.clicked():
        scene = "START_MENU"
        # reset asteroids positions, essentially making new map
        asteroids = [Asteroid([random.randint(-500, width+500), random.randint(-500, height+500)]) for i in range(0, 3)]
    main_menu_button_exit.draw()
    if main_menu_button_exit.clicked():
        end()


# ------------------GAME VARIABLES AND FUNCTION---------------------
main_menu_button_on = Button(
    display,
    [75, 50, 150, 100],
    "Menu",
    (130, 130, 130),
    (100, 100, 100),
    (0, 0, 0),
    35,
)


def game():
    global scene, missile_list
    # The background, will be changed later
    display.fill((0, 0, 0))

    # Update the asteroid direction, this is used in the Asteroid class
    Asteroid.directions = center_spaceship.directions

    # update missile list using a center_spaceship method
    center_spaceship.shoot_missile(missile_list)

    # draw center_spaceship and uses all methods EXCEPT stat display which is placed on top of asteroids.
    center_spaceship.all()

    Asteroid.collided = False
    # draws the asteroids
    for asteroid in asteroids:
        asteroid.all()
    # moves the asteroids
    for asteroid_movement in asteroids:
        asteroid_movement.move()

    # filters list, which removes all attributes
    missile_list = [missile for missile in missile_list if not missile.destroyed]

    # display stats for spaceship
    center_spaceship.stat_display()

    # draw main menu button
    main_menu_button_on.draw()
    if main_menu_button_on.clicked():
        scene = "GAME.MAIN_MENU"


def main():
    print(width, height)  # prints the width and height.
    global display
    # pygame.mouse.set_cursor((8, 8), (0, 0), (0, 0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0, 0, 0))
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                end()
        if scene == "START_MENU":
            start_menu()
        elif scene == "GAME":
            game()
        elif scene == "GAME.MAIN_MENU":
            main_menu()
        else:
            print('Something went wrong with the scene controller.')
            quit()

        # mouse_pos = pygame.mouse.get_pos()
        # pygame.draw.circle(  # circle for mouse
        #    display, [0, 0, 255],
        #    (int(mouse_pos[0]), int(mouse_pos[1])),
        #    8
        # )

        """
        Also part of the resizing solution
        display = pygame.transform.scale(display, \
        (int(screen_display_scale_ratio*width), int(screen_display_scale_ratio*height)))
        screen.blit(display, (0, 0))
        """
        # Draws everything that needs to be draw, not just one part
        pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    main()
