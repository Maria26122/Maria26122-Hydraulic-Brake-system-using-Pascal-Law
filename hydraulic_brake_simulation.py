import sys
import os
import math
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# --- Constants ---
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
FRAMES_PER_SECOND = 60

# Colors (R, G, B)
COLOR_BACKGROUND_GRADIENT_TOP = (0.55, 0.80, 0.98)      # Upper portion of the sky gradient (sky blue)
COLOR_BACKGROUND_GRADIENT_BOTTOM = (0.95, 0.95, 1.0)    # Lower portion of the sky gradient (soft white/blue)
COLOR_SUN = (1.0, 0.95, 0.7)
COLOR_CLOUD = (1.0, 1.0, 1.0)
COLOR_GRASS = (0.45, 0.8, 0.45)
COLOR_ROAD = (0.18, 0.18, 0.18)
COLOR_ROAD_EDGE = (0.35, 0.35, 0.35)
COLOR_ROAD_CENTER_LINE = (1.0, 1.0, 0.7)
COLOR_BRAKE_PEDAL = (0.7, 0.1, 0.1)
COLOR_MASTER_CYLINDER = (0.3, 0.3, 0.3)
COLOR_SLAVE_CYLINDER = (0.3, 0.3, 0.3)
COLOR_BRAKE_FLUID = (0.1, 0.4, 0.9)
COLOR_HYDRAULIC_PIPE = (0.1, 0.4, 0.9)
COLOR_BRAKE_DISC = (0.5, 0.5, 0.5)
COLOR_BRAKE_PAD = (0.9, 0.1, 0.1)
COLOR_TEXT_LABEL = (255, 255, 255)
COLOR_PRESSURE_ARROW = (1.0, 0.8, 0.1)
COLOR_CAR_BODY = (1.0, 0.3, 0.1)  # Bright orange-red for car body
COLOR_CAR_ACCENT = (0.7, 0.2, 0.0)    # Accent color for car lower body
COLOR_CAR_WINDOW = (0.85, 0.97, 1.0)
COLOR_CAR_BUMPER = (0.8, 0.8, 0.9)
COLOR_CAR_HEADLIGHT = (1.0, 1.0, 0.7)

# Piston colors
COLOR_PISTON_MAIN_BODY = (0.8, 0.8, 0.8)   # Light metallic silver for piston body
COLOR_PISTON_FRONT = (0.5, 0.5, 0.5)       # Medium gray for piston tip
COLOR_PISTON_RING = (1.0, 0.6, 0.0)        # Bright orange for piston ring

# --- Simulation State Variables ---
is_brake_applied = False
brake_pedal_position = 0.0  # 0.0 = fully released, 1.0 = fully pressed
brake_pad_position = 0.0    # 0.0 = fully retracted, 1.0 = fully engaged
brake_disc_rotation_angle = 0.0
car_horizontal_offset = 0.0

# --- Modular Drawing Functions ---
def draw_rectangle(x_coordinate, y_coordinate, width, height, color_value):
    glColor3f(*color_value)
    glBegin(GL_QUADS)
    glVertex2f(x_coordinate, y_coordinate)
    glVertex2f(x_coordinate+width, y_coordinate)
    glVertex2f(x_coordinate+width, y_coordinate+height)
    glVertex2f(x_coordinate, y_coordinate+height)
    glEnd()

def draw_circle(center_x, center_y, radius, color_value, segment_count=32):
    glColor3f(*color_value)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(center_x, center_y)
    for segment_index in range(segment_count+1):
        angle = 2*math.pi*segment_index/segment_count
        glVertex2f(center_x + radius*math.cos(angle), center_y + radius*math.sin(angle))
    glEnd()

def draw_ellipse(center_x, center_y, radius_x, radius_y, color_value, segment_count=32):
    glColor3f(*color_value)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(center_x, center_y)
    for segment_index in range(segment_count+1):
        angle = 2*math.pi*segment_index/segment_count
        glVertex2f(center_x + radius_x*math.cos(angle), center_y + radius_y*math.sin(angle))
    glEnd()

def draw_arrow(start_x, start_y, end_x, end_y, color_value, line_width=4):
    glColor3f(*color_value)
    glLineWidth(line_width)
    glBegin(GL_LINES)
    glVertex2f(start_x, start_y)
    glVertex2f(end_x, end_y)
    glEnd()
    # Draw arrowhead
    arrow_angle = math.atan2(end_y-start_y, end_x-start_x)
    arrow_size = 12
    for arrowhead_angle in [-0.4, 0.4]:
        glBegin(GL_LINES)
        glVertex2f(end_x, end_y)
        glVertex2f(end_x - arrow_size*math.cos(arrow_angle+arrowhead_angle), end_y - arrow_size*math.sin(arrow_angle+arrowhead_angle))
        glEnd()

def draw_background_scene():
    # Draw sky gradient
    glBegin(GL_QUADS)
    glColor3f(*COLOR_BACKGROUND_GRADIENT_TOP)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glColor3f(*COLOR_BACKGROUND_GRADIENT_BOTTOM)
    glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
    glVertex2f(0, WINDOW_HEIGHT)
    glEnd()
    # Draw sun
    draw_circle(700, 80, 50, COLOR_SUN, segment_count=40)
    # Draw clouds
    for cloud_cx, cloud_cy, cloud_rx, cloud_ry in [(180, 90, 40, 18), (220, 110, 30, 14), (160, 110, 22, 10)]:
        draw_ellipse(cloud_cx, cloud_cy, cloud_rx, cloud_ry, COLOR_CLOUD, segment_count=24)
    for cloud_cx, cloud_cy, cloud_rx, cloud_ry in [(500, 60, 32, 14), (530, 75, 22, 10), (480, 80, 18, 8)]:
        draw_ellipse(cloud_cx, cloud_cy, cloud_rx, cloud_ry, COLOR_CLOUD, segment_count=24)
    # Draw grass
    draw_rectangle(0, 320, WINDOW_WIDTH, WINDOW_HEIGHT-320, COLOR_GRASS)

def draw_roadway():
    # Draw road base
    road_y_coordinate = 260
    road_height = 80
    draw_rectangle(0, road_y_coordinate, WINDOW_WIDTH, road_height, COLOR_ROAD)
    # Draw road edges
    edge_height = 8
    draw_rectangle(0, road_y_coordinate, WINDOW_WIDTH, edge_height, COLOR_ROAD_EDGE)
    draw_rectangle(0, road_y_coordinate+road_height-edge_height, WINDOW_WIDTH, edge_height, COLOR_ROAD_EDGE)
    # Draw center dashed line
    dash_width = 40
    dash_gap = 32
    center_line_y = road_y_coordinate + road_height//2 - 4
    for dash_x in range(0, WINDOW_WIDTH, dash_width + dash_gap):
        draw_rectangle(dash_x, center_line_y, dash_width, 8, COLOR_ROAD_CENTER_LINE)

def draw_brake_pedal(pedal_position):
    # Draw brake pedal base
    draw_rectangle(80, 400, 30, 100, COLOR_MASTER_CYLINDER)
    # Draw brake pedal arm (rotates downward)
    pedal_rotation_angle = -pedal_position * 30  # degrees
    glPushMatrix()
    glTranslatef(95, 480, 0)
    glRotatef(pedal_rotation_angle, 0, 0, 1)
    draw_rectangle(-10, -60, 20, 60, COLOR_BRAKE_PEDAL)
    glPopMatrix()

def draw_master_cylinder(pedal_position):
    # Draw master cylinder body
    draw_rectangle(120, 470, 60, 30, COLOR_MASTER_CYLINDER)
    # Draw piston (moves right as pedal is pressed)
    piston_x_coordinate = 120 + pedal_position*20
    # Draw piston main body (shorter and smaller, different shade)
    draw_rectangle(piston_x_coordinate+2, 478, 10, 14, COLOR_PISTON_MAIN_BODY)
    # Draw piston tip (rounded, slightly darker)
    draw_circle(piston_x_coordinate+12, 485, 5, COLOR_PISTON_FRONT, segment_count=16)
    # Draw piston ring (vivid orange, small)
    draw_circle(piston_x_coordinate+7, 485, 3, COLOR_PISTON_RING, segment_count=12)

def draw_hydraulic_fluid_lines(pedal_position):
    # Draw pipe from master cylinder to T-junction
    glColor3f(*COLOR_HYDRAULIC_PIPE)
    glLineWidth(8)
    glBegin(GL_LINE_STRIP)
    glVertex2f(180+pedal_position*20, 485)
    glVertex2f(250, 485)
    glVertex2f(250, 300)
    glEnd()
    # Draw split to left and right slave cylinders
    glBegin(GL_LINES)
    glVertex2f(250, 300)
    glVertex2f(180, 200)
    glVertex2f(250, 300)
    glVertex2f(320, 200)
    glEnd()
    # Draw pressure arrows
    draw_arrow(200+pedal_position*20, 485, 245, 485, COLOR_PRESSURE_ARROW)
    draw_arrow(250, 310, 185, 210, COLOR_PRESSURE_ARROW)
    draw_arrow(250, 310, 315, 210, COLOR_PRESSURE_ARROW)

def draw_slave_cylinder(slave_x, slave_y, pad_position):
    # Draw slave cylinder body
    draw_rectangle(slave_x, slave_y, 40, 30, COLOR_SLAVE_CYLINDER)
    # Draw piston (moves left as pad_position increases)
    piston_horizontal_offset = pad_position*15
    # Draw piston main body (shorter and smaller, different shade)
    draw_rectangle(slave_x-7-piston_horizontal_offset, slave_y+8, 7, 14, COLOR_PISTON_MAIN_BODY)
    # Draw piston tip (rounded, slightly darker)
    draw_circle(slave_x-7-piston_horizontal_offset+7, slave_y+15, 3.5, COLOR_PISTON_FRONT, segment_count=12)
    # Draw piston ring (vivid orange, small)
    draw_circle(slave_x-7-piston_horizontal_offset+3.5, slave_y+15, 2, COLOR_PISTON_RING, segment_count=8)

def draw_brake_pad(pad_x, pad_y, pad_position, pad_side='left'):
    # Draw brake pad, which moves toward disc as pad_position increases
    pad_offset = pad_position*18
    if pad_side == 'left':
        draw_rectangle(pad_x-18-pad_offset, pad_y+10, 18, 40, COLOR_BRAKE_PAD)
    else:
        draw_rectangle(pad_x+40+pad_offset, pad_y+10, 18, 40, COLOR_BRAKE_PAD)

def draw_brake_disc(disc_x, disc_y, rotation_angle):
    # Draw brake disc (rotates)
    glPushMatrix()
    glTranslatef(disc_x+20, disc_y+30, 0)
    glRotatef(rotation_angle, 0, 0, 1)
    draw_circle(0, 0, 30, COLOR_BRAKE_DISC)
    # Draw disc holes
    glColor3f(0.2,0.2,0.2)
    for hole_index in range(6):
        hole_angle = 2*math.pi*hole_index/6
        glBegin(GL_POLYGON)
        for segment_index in range(8):
            t = 2*math.pi*segment_index/8
            glVertex2f(18*math.cos(hole_angle)+4*math.cos(t), 18*math.sin(hole_angle)+4*math.sin(t))
        glEnd()
    glPopMatrix()

def draw_car_body(horizontal_offset):
    # Draw car with bright color and rounded shapes, moves left when braking
    glPushMatrix()
    glTranslatef(horizontal_offset, 0, 0)
    # Draw car shadow
    draw_ellipse(210, 220, 70, 12, (0.2, 0.2, 0.22), segment_count=32)
    # Draw main car body (rounded rectangle)
    glColor3f(*COLOR_CAR_BODY)
    glBegin(GL_POLYGON)
    for i in range(16):
        angle = math.pi + i*math.pi/15
        glVertex2f(120+180*abs(math.cos(angle))/2 + 10*math.sin(angle), 170+30*math.sin(angle))
    glVertex2f(320, 210)
    glVertex2f(120, 210)
    glEnd()
    # Draw lower body accent
    draw_rectangle(120, 200, 200, 20, COLOR_CAR_ACCENT)
    # Draw roof (rounded)
    draw_ellipse(220, 150, 70, 28, COLOR_CAR_WINDOW, segment_count=32)
    # Draw windows (front and rear)
    draw_ellipse(170, 155, 28, 18, COLOR_CAR_WINDOW, segment_count=24)
    draw_ellipse(270, 155, 28, 18, COLOR_CAR_WINDOW, segment_count=24)
    # Draw bumpers
    draw_rectangle(110, 200, 20, 12, COLOR_CAR_BUMPER)
    draw_rectangle(290, 200, 20, 12, COLOR_CAR_BUMPER)
    # Draw headlights
    draw_circle(110, 206, 5, COLOR_CAR_HEADLIGHT)
    draw_circle(310, 206, 5, COLOR_CAR_HEADLIGHT)
    # Draw wheels (with hubcaps)
    draw_circle(150, 220, 18, (0.1,0.1,0.1))
    draw_circle(150, 220, 9, (0.8,0.8,0.9))
    draw_circle(270, 220, 18, (0.1,0.1,0.1))
    draw_circle(270, 220, 9, (0.8,0.8,0.9))
    # Draw smiling face (front bumper)
    glColor3f(0.2, 0.2, 0.2)
    glLineWidth(2)
    glBegin(GL_LINE_STRIP)
    for t in range(13):
        angle = math.pi*0.15 + t*math.pi*0.7/12
        glVertex2f(200+18*math.cos(angle), 210+7*math.sin(angle))
    glEnd()
    glPopMatrix()

# --- Label/Overlay Helper ---
def draw_labels_and_overlay(pygame_screen, pygame_font, pygame_font_large, pedal_position, pad_position, car_offset_value):
    # Draw labels and user interface using Pygame 2D overlay
    overlay_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
    # Labels for system components
    overlay_surface.blit(pygame_font.render("Pedal", True, COLOR_TEXT_LABEL), (70, 510))
    overlay_surface.blit(pygame_font.render("Master Cylinder", True, COLOR_TEXT_LABEL), (120, 505))
    overlay_surface.blit(pygame_font.render("Brake Fluid", True, COLOR_TEXT_LABEL), (255, 320))
    overlay_surface.blit(pygame_font.render("Slave Cylinder", True, COLOR_TEXT_LABEL), (110, 215))
    overlay_surface.blit(pygame_font.render("Slave Cylinder", True, COLOR_TEXT_LABEL), (250, 215))
    overlay_surface.blit(pygame_font.render("Brake Pad", True, COLOR_TEXT_LABEL), (80, 235))
    overlay_surface.blit(pygame_font.render("Brake Pad", True, COLOR_TEXT_LABEL), (320, 235))
    overlay_surface.blit(pygame_font.render("Disc", True, COLOR_TEXT_LABEL), (130, 160))
    overlay_surface.blit(pygame_font.render("Disc", True, COLOR_TEXT_LABEL), (270, 160))
    overlay_surface.blit(pygame_font.render("Car", True, COLOR_TEXT_LABEL), (200+car_offset_value, 110))
    # User instructions
    overlay_surface.blit(pygame_font_large.render("Press F to Apply Brake", True, (255,255,0)), (20, 20))
    overlay_surface.blit(pygame_font_large.render("Press R to Release Brake", True, (0,255,255)), (20, 55))
    overlay_surface.blit(pygame_font_large.render("Press ESC to Exit", True, (255,128,128)), (20, 90))
    # Pascal's Law statement
    overlay_surface.blit(pygame_font.render("Pascal's Law: Pressure applied to a confined fluid is transmitted equally in all directions.", True, (200,200,255)), (80, 570))
    pygame_screen.blit(overlay_surface, (0,0))

# --- Main Simulation Loop ---
def main():
    global is_brake_applied, brake_pedal_position, brake_pad_position, brake_disc_rotation_angle, car_horizontal_offset

    pygame.init()
    pygame.display.set_caption("Hydraulic Brake Simulation - Pascal's Law")
    pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)
    simulation_clock = pygame.time.Clock()
    pygame_font = pygame.font.SysFont("Arial", 20, bold=True)
    pygame_font_large = pygame.font.SysFont("Arial", 28, bold=True)

    # OpenGL context setup
    glClearColor(1, 1, 1, 1)  # Custom background will be drawn
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)

    is_simulation_running = True
    while is_simulation_running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == QUIT:
                is_simulation_running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    is_simulation_running = False
                elif event.key == K_f:
                    is_brake_applied = True
                elif event.key == K_r:
                    is_brake_applied = False

        # --- Update Simulation State ---
        # Animate pedal and pad positions
        target_position = 1.0 if is_brake_applied else 0.0
        brake_pedal_position += (target_position - brake_pedal_position) * 0.2
        brake_pad_position += (target_position - brake_pad_position) * 0.2
        # Adjust disc rotation and car offset based on braking state
        if is_brake_applied:
            brake_disc_rotation_angle += 1.5 * (1.0 - brake_pad_position*0.8)
            car_horizontal_offset -= 0.5 * (1.0 - car_horizontal_offset/10)
        else:
            brake_disc_rotation_angle += 3.0
            car_horizontal_offset += (0.0 - car_horizontal_offset) * 0.1

        # --- Render OpenGL Scene ---
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()

        # Draw background (sky, sun, clouds, grass)
        draw_background_scene()

        # Draw road
        draw_roadway()

        # Draw car body (moves when braking)
        draw_car_body(car_horizontal_offset)

        # Draw brake pedal and master cylinder
        draw_brake_pedal(brake_pedal_position)
        draw_master_cylinder(brake_pedal_position)

        # Draw hydraulic fluid lines and pressure arrows
        draw_hydraulic_fluid_lines(brake_pedal_position)

        # Draw left brake assembly
        draw_slave_cylinder(120, 180, brake_pad_position)
        draw_brake_pad(120, 180, brake_pad_position, 'left')
        draw_brake_disc(140, 180, brake_disc_rotation_angle)

        # Draw right brake assembly
        draw_slave_cylinder(260, 180, brake_pad_position)
        draw_brake_pad(260, 180, brake_pad_position, 'right')
        draw_brake_disc(280, 180, brake_disc_rotation_angle)

        # --- Swap OpenGL Buffers ---
        pygame.display.flip()

        # --- Draw Pygame Overlay (Labels, UI) ---
        # Draw overlay text and labels using Pygame 2D after OpenGL flip
        pygame_screen = pygame.display.get_surface()
        draw_labels_and_overlay(pygame_screen, pygame_font, pygame_font_large, brake_pedal_position, brake_pad_position, car_horizontal_offset)

        # Do not call pygame.display.update() or pygame.display.flip() again here.
        # Only the OpenGL buffer should be swapped; overlay is drawn directly to the surface.

        simulation_clock.tick(FRAMES_PER_SECOND)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
