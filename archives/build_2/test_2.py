import pygame
import sys
from OpenGL.GL import *
from OpenGL.GLU import *

vertices = (
    # x  y  z
    (1,   -1, -1),
    (1,   1, -1),
    (-1, 1, -1),
    (-1, -1, -1),
    (1, -1, 1),
    (1, 1, 1),
    (-1, -1, 1),
    (-1, 1, 1)
)

edges = (
    (0, 1),
    (0, 3),
    (0, 4),
    (2, 1),
    (2, 3),
    (2, 7),
    (6, 3),
    (6, 4),
    (6, 7),
    (5, 1),
    (5, 4),
    (5, 7)
)


def loadTexture():
    textureSurface = pygame.image.load('test_image.png')
    textureData = pygame.image.tostring(textureSurface, "RGBA", 1)
    width = textureSurface.get_width()
    height = textureSurface.get_height()

    glEnable(GL_TEXTURE_2D)
    texid = glGenTextures(1)

    glBindTexture(GL_TEXTURE_2D, texid)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height,
                 0, GL_RGBA, GL_UNSIGNED_BYTE, textureData)

    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    return texid


def draw_cube(lines=True):
    if lines:
        glBegin(GL_LINES)
        for edge in edges:
            glColor3fv((1, 1, 1))
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()
    else:
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(1.0,  1.0,  1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-1.0,  1.0,  1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-1.0,  1.0, -1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(1.0,  1.0, -1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(1.0, -1.0, -1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-1.0,  1.0, -1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-1.0,  1.0,  1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(1.0,  1.0,  1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(1.0,  1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(1.0, -1.0, -1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(1.0, -1.0, -1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(1.0,  1.0, -1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(1.0,  1.0,  1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(1.0, -1.0,  1.0)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(-1.0, -1.0, -1.0)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(-1.0, -1.0,  1.0)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(-1.0,  1.0,  1.0)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(-1.0,  1.0, -1.0)
        glEnd()

pygame.init()
display = (800, 600)
screen = pygame.display.set_mode(
    display, pygame.DOUBLEBUF | pygame.OPENGL | pygame.OPENGLBLIT)

loadTexture()

gluPerspective(45, display[0] / display[1], 0.1, 50.0)
glTranslatef(0.0, 0.0, -5)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_cube(lines=True)

    pygame.display.flip()