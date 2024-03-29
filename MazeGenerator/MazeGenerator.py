import random

from .Maze import Maze
from .Types import Coords, Node


class MazeGenerator:
    def __init__(self):
        self.horizontal_bias: int = 0
        self.vertical_bias: int = 0
        self.max_bias: int = 0

        self.seed: int | None = None
        """The seed used to generate the horizontal and vertical weights."""

        self.horizontal_weights: list[list[int]] = []
        """
        The horizontal weights between nodes.
        
        The weight between nodes at coords (5, 0) and (6, 0) is at [0][5].
        
        Put the shared y first then the min of the x.
        
        Only adjacent nodes should be considered.
        """

        self.vertical_weights: list[list[int]] = []
        """
        The vertical weights between nodes.
        
        The weight between nodes at coords (0, 5) and (0, 6) is at [0][5].
        
        Put the shared x first then the min of the y.
        
        Only adjacent nodes should be considered.
        """

        self.all_accepted_nodes: list[Coords] = []
        """A list of the coordinates of all accepted nodes."""

        self.nodes_to_look_at: list[Coords] = []
        """A list of accepted nodes of which have paths to consider."""

    @staticmethod
    def setup_nodes(maze: Maze) -> None:
        """
        Modifies the nodes of the given maze to contain edges.

        :param maze: The maze to be modified.
        """

        for x in range(maze.width):
            maze.nodes[0][x][1] = -1
            maze.nodes[maze.height - 1][x][3] = -1

        for y in range(maze.height):
            maze.nodes[y][0][0] = -1
            maze.nodes[y][maze.width - 1][2] = -1

    def generate_weights(self,
                         maze_width: int, maze_height: int,
                         horizontal_bias: int, vertical_bias: int,
                         seed: int | None):
        self.horizontal_bias = horizontal_bias
        self.vertical_bias = vertical_bias
        self.max_bias = max(horizontal_bias, vertical_bias) + 1
        self.seed = seed

        random.seed(seed)

        self.horizontal_weights = [
            [
                random.randint(0, horizontal_bias) for _ in range(maze_width - 1)
            ] for _ in range(maze_height)
        ]

        self.vertical_weights = [
            [
                random.randint(0, vertical_bias) for _ in range(maze_height - 1)
            ] for _ in range(maze_width)
        ]

    def pass_through(self, maze):
        # Information regarding the path of lowest weight to be added

        lowest_weight: int = self.max_bias
        lowest_weight_direction: int = 0
        # lw = lowest weight
        lw_coordinates: tuple[int, int] | None = None
        lw_adjacent_coordinates: tuple[int, int] | None = None

        for node_index in range(len(self.nodes_to_look_at) - 1, -1, -1):
            node_coords = self.nodes_to_look_at[node_index]
            node = maze.nodes[node_coords[1]][node_coords[0]]

            # If we have no directions to consider
            if 0 not in node:
                # Remove from nodes we look at and skip
                self.nodes_to_look_at.remove(node_coords)
                continue

            for direction, finished in enumerate(node):
                if finished:
                    continue

                # Acquire the adjacent node

                adjacent_node_coords: Coords

                if direction == 0:  # Looking left
                    adjacent_node_coords = (node_coords[0] - 1, node_coords[1])
                elif direction == 1:  # Looking up
                    adjacent_node_coords = (node_coords[0], node_coords[1] - 1)
                elif direction == 2:  # Looking right
                    adjacent_node_coords = (node_coords[0] + 1, node_coords[1])
                else:
                    adjacent_node_coords = (node_coords[0], node_coords[1] + 1)

                adjacent_node: Node = maze.nodes[adjacent_node_coords[1]][adjacent_node_coords[0]]

                if 1 in adjacent_node:
                    continue

                # If we cannot traverse to the adjacent node
                if adjacent_node[(direction + 2) % 4] == -1:
                    # Make sure our node reflects this, skip
                    maze.nodes[node_coords[1]][node_coords[0]][direction] = -1
                    continue

                # Acquire the weight of the path to the adjacent node

                weight: int

                if direction % 2:  # If looking up or down
                    weight = self.vertical_weights[node_coords[0]][min(node_coords[1], adjacent_node_coords[1])]
                else:  # If looking left or right
                    weight = self.horizontal_weights[node_coords[1]][min(node_coords[0], adjacent_node_coords[0])]

                # If the path we are looking at is now the lowest weight, skip
                if weight >= lowest_weight:
                    continue

                lowest_weight = weight
                lowest_weight_direction = direction
                lw_coordinates = node_coords
                lw_adjacent_coordinates = adjacent_node_coords

        # If we found no node, we are done
        if lw_coordinates is None:
            return False

        # Modify the nodes to add in the shortest path
        maze.nodes[lw_coordinates[1]][lw_coordinates[0]][lowest_weight_direction] = 1
        maze.nodes[lw_adjacent_coordinates[1]][lw_adjacent_coordinates[0]][(lowest_weight_direction + 2) % 4] = 1

        # Store the node we just added
        self.all_accepted_nodes.append(lw_adjacent_coordinates)
        self.nodes_to_look_at.append(lw_adjacent_coordinates)

        return True

    def __call__(self,
                 width: int, height: int,
                 vertical_bias: int = 10, horizontal_bias: int = 10,
                 starting_position: Coords | None = None,
                 seed: int | None = None) -> Maze:
        maze = Maze(width, height)

        if starting_position is not None:
            if starting_position[0] < 0 or starting_position[1] < 0:
                raise ValueError(f"Starting position ({starting_position[0]}, {starting_position[1]}) "
                                 f"must have values of at least 0")

            if starting_position[0] >= width:
                raise ValueError(f"Starting position x coordinate {starting_position[0]} "
                                 f"is not less than the maze width {width}")

            if starting_position[0] >= height:
                raise ValueError(f"Starting position y coordinate {starting_position[1]} "
                                 f"is not less than the maze height {height}")

        else:
            starting_position = (0, 0)

        self.all_accepted_nodes = [starting_position]
        self.nodes_to_look_at = [starting_position]

        self.setup_nodes(maze)
        self.generate_weights(maze.width, maze.height, horizontal_bias, vertical_bias, seed)

        while self.pass_through(maze):
            pass

        return maze
