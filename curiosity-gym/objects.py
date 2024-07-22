import copy
import random
from abc import ABC, abstractmethod
from typing import Self, override

import numpy as np
import pygame

from constants import IX_TO_COLOR, STATE_TO_ROTATION
from enums import Action


class GridObject(ABC):
    # Class-level attributes
    id = None
    next_id = 1
    id_map = {}

    def __init__(self, position: tuple[int,int], color: int = 0, state: int = 0) -> None:
        self.start_position = np.array(position)
        self.position = np.array(position)
        self.start_color = color
        self.color = color
        self.start_state = state
        self.state = state

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        cls.id = GridObject.next_id
        GridObject.id_map[cls] = cls.id
        GridObject.next_id += 1

    @abstractmethod
    def render(self, canvas: pygame.Surface, pixelsquare: float):
        pass

    def get_identity(self) -> np.ndarray:
        return np.array([self.__class__.id, self.color, self.state])

    def interact(self, agent: Self) -> None:
        pass

    def reset(self):
        self.position = self.start_position
        self.state = self.start_state
        self.color = self.start_color

    def step(
        self, action: Action,
        front_object: Self | None = None,
        walkable: bool = False,
        ) -> None:
        pass

    def simulate(
        self, action: Action,
        front_object: Self | None = None,
        walkable: bool = False,
        ) -> Self:
        simulated = copy.deepcopy(self)
        simulated.step(action, front_object, walkable)
        return simulated

    def walkable(self) -> bool:
        return False


class Agent(GridObject):

    @override
    def step(
        self, action: Action,
        front_object: GridObject | None = None,
        walkable: bool = False,
        ) -> None:

        if action == Action.FORWARD and walkable:
            self.position = self.position + STATE_TO_ROTATION[self.state] * np.array([1,-1])

        elif action == Action.TURN_RIGHT:
            self.state = (self.state - 1) % 4

        elif action == Action.TURN_LEFT:
            self.state = (self.state + 1) % 4

        elif action == Action.INTERACT and front_object:
            front_object.interact(self)

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        # Constant parameters
        c = np.array([0.5, 0.5])
        d = 0.35
        r = STATE_TO_ROTATION[self.state]

        # Calculate points for triangle rotation
        p1 = (self.position + c - np.array([-d, d]) * r) * pixelsquare
        p2 = (self.position + c - [d, -d] * np.flip(r) + [-d, d] * r ) * pixelsquare
        p3 = (self.position + c + [d, -d] * np.flip(r) + [-d, d] * r ) * pixelsquare

        # Draw agent
        pygame.draw.polygon(
            canvas,
            IX_TO_COLOR[self.color],
            (p1, pygame.Vector2(*p2), pygame.Vector2(*p3)),
            0 # filled triangle
        )

    def get_front(self) -> np.ndarray:
        return self.position + STATE_TO_ROTATION[self.state] * np.array([1,-1])


class Wall(GridObject):

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        pygame.draw.rect(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Rect(
                pygame.Vector2(*(pixelsquare * self.position)),
                (pixelsquare, pixelsquare),
            ),
        )


class Target(GridObject):

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        pygame.draw.rect(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Rect(
                pygame.Vector2(*(pixelsquare * self.position)),
                (pixelsquare, pixelsquare),
            ),
        )

    @override
    def walkable(self) -> bool:
        return True


class Door(GridObject):

    @override
    def interact(self, agent):
        if self.state == 2 and agent.color != self.color:
            return
        elif self.state == 2 and agent.color == self.color:
            self.state = 0
            agent.color = agent.start_color
        else:
            self.state = (self.state + 1) % 2

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        if self.state > 0:
            pygame.draw.rect(
                canvas,
                IX_TO_COLOR[self.color],
                pygame.Rect(
                    pygame.Vector2(*(pixelsquare * self.position)),
                    (pixelsquare, pixelsquare),
                ), 5
            )

            pygame.draw.circle(
                canvas,
                IX_TO_COLOR[self.color],
                pygame.Vector2(*((self.position + np.array([0.75,0.5])) * pixelsquare)),
                0.1 * pixelsquare,
            )

        else:
            pygame.draw.rect(
                canvas,
                IX_TO_COLOR[self.color],
                pygame.Rect(
                    pygame.Vector2(*(pixelsquare * self.position)),
                    (pixelsquare*0.2, pixelsquare),
                ), 5
            )

    @override
    def walkable(self) -> bool:
        return self.state == 0


class Key(GridObject):

    @override
    def interact(self, agent: Agent) -> None:
        agent.color = self.color
        self.position = np.array([-1,-1])

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        pygame.draw.circle(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Vector2(*((self.position + np.array([0.5,0.4])) * pixelsquare)),
            0.15 * pixelsquare,
            5
        )
        pygame.draw.line(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Vector2(*((self.position + np.array([0.5,0.55])) * pixelsquare)),
            pygame.Vector2(*((self.position + np.array([0.5,0.8])) * pixelsquare)),
            5
        )
        pygame.draw.line(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Vector2(*((self.position + np.array([0.5,0.7])) * pixelsquare)),
            pygame.Vector2(*((self.position + np.array([0.4,0.7])) * pixelsquare)),
            5
        )


class RandomBlock(GridObject):

    @override
    def step(
        self, action: Action,
        front_object: Self | None = None,
        walkable: bool = False,
        ) -> None:
        self.color = random.randint(3,len(IX_TO_COLOR)-1)

    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        pygame.draw.rect(
            canvas,
            IX_TO_COLOR[self.color],
            pygame.Rect(
                pygame.Vector2(*((self.position + np.array([0.15,0.15])) * pixelsquare)),
                (pixelsquare*0.7, pixelsquare*0.7),
            ),
        )
        font = pygame.font.SysFont("freesansbold", 60)
        img = font.render("?", True, (255, 255, 255))
        canvas.blit(img, pygame.Vector2(*((self.position + np.array([0.3,0.25])) * pixelsquare)))


class Enemy(GridObject):

    @override
    def __init__(self, 
                 position: tuple[int,int],
                 color: int = 9,
                 state: int = 0,
                 reach: int = 2
                 ) -> None:
        super().__init__(position, color, state)
        self.reach = reach
        self.direction = 1

    @override
    def step(
        self, action: Action,
        front_object: Self | None = None,
        walkable: bool = False,
        ) -> None:
        self.position = self.position + self.direction * STATE_TO_ROTATION[self.state] * np.array([1,-1])
        if self.position[self.state%2] == self.start_position[self.state%2] + self.reach or \
        self.position[self.state%2] == self.start_position[self.state%2] - self.reach or \
        self.position[self.state%2] == self.start_position[self.state%2]:
            self.direction *= -1

    @override
    def walkable(self) -> bool:
        return True

    @override
    def render(self, canvas: pygame.Surface, pixelsquare: float) -> None:
        pygame.draw.polygon(
            canvas,
            IX_TO_COLOR[self.color],
            (
                pygame.Vector2(*((self.position + np.array([0.25,0.2])) * pixelsquare)),
                pygame.Vector2(*((self.position + np.array([0.75,0.2])) * pixelsquare)),
                pygame.Vector2(*((self.position + np.array([0.85,0.55])) * pixelsquare)),
                pygame.Vector2(*((self.position + np.array([0.5,0.85])) * pixelsquare)),
                pygame.Vector2(*((self.position + np.array([0.15,0.55])) * pixelsquare)),
            )
        )
        pygame.draw.circle(
            canvas,
            (255,255,255),
            pygame.Vector2(*((self.position + np.array([0.35,0.37])) * pixelsquare)),
            5
        )
        pygame.draw.circle(
            canvas,
            (255,255,255),
            pygame.Vector2(*((self.position + np.array([0.65,0.37])) * pixelsquare)),
            5
        )
        pygame.draw.line(
            canvas,
            (255,255,255),
            pygame.Vector2(*((self.position + np.array([0.4,0.63])) * pixelsquare)),
            pygame.Vector2(*((self.position + np.array([0.6,0.63])) * pixelsquare)),
            3
        )
