import random

Node = list[int, int, int, int]
"""
A node in the maze generator.
The order of sides is (left, top, right, bottom).

States:
    - -1 Rejected
    - 0 To Be Considered
    - 1 Accepted
"""

Coords = tuple[int, int]
"""
Coordinates into a 2D array.
(x, y)
"""


class MazeGenerator:
    def __init__(self):
        self.width: int = 0
        self.height: int = 0

        self.horizontal_bias: int = 0
        self.vertical_bias: int = 0
        self.max_bias: int = 0

        self.seed: int | None = None

        self.nodes: list[list[Node]] = []
        """
        A 2D array of the nodes for the maze.
        """

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

    def setup_nodes(self,
                    width: int, height: int,
                    horizontal_bias: int = 10, vertical_bias: int = 10,
                    starting_position: Coords | None = None,
                    seed: int | None = None):
        # Save some stuff

        self.width = width
        self.height = height
        self.horizontal_bias = horizontal_bias
        self.vertical_bias = vertical_bias
        self.max_bias = max(horizontal_bias, vertical_bias) + 1
        self.seed = seed

        # Set up the nodes

        self.nodes = [
            [
                [0, 0, 0, 0] for _ in range(width)
            ] for _ in range(height)
        ]

        # The edges

        for x in range(width):
            self.nodes[0][x][1] = -1
            self.nodes[height - 1][x][3] = -1

        for y in range(height):
            self.nodes[y][0][0] = -1
            self.nodes[y][width - 1][2] = -1

        # Set up the weights

        random.seed(seed)

        self.horizontal_weights = [
            [
                random.randint(0, horizontal_bias) for _ in range(width - 1)
            ] for _ in range(height)
        ]

        self.vertical_weights = [
            [
                random.randint(0, vertical_bias) for _ in range(height - 1)
            ] for _ in range(width)
        ]

        # Starting position
        starting_position = (0, 0) if starting_position is None else starting_position

        self.nodes_to_look_at.append(starting_position)
        self.all_accepted_nodes.append(starting_position)

    def pass_through(self):
        # Information regarding the path of lowest weight to be added

        lowest_weight: int = self.max_bias
        lowest_weight_direction: int = 0
        # lw = lowest weight
        lw_coordinates: tuple[int, int] | None = None
        lw_adjacent_coordinates: tuple[int, int] | None = None

        for node_index in range(len(self.nodes_to_look_at) - 1, -1, -1):
            node_coords = self.nodes_to_look_at[node_index]
            node = self.nodes[node_coords[1]][node_coords[0]]

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

                adjacent_node: Node = self.nodes[adjacent_node_coords[1]][adjacent_node_coords[0]]

                if 1 in adjacent_node:
                    continue

                # If we cannot traverse to the adjacent node
                if adjacent_node[(direction + 2) % 4] == -1:
                    # Make sure our node reflects this, skip
                    self.nodes[node_coords[1]][node_coords[0]][direction] = -1
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
        self.nodes[lw_coordinates[1]][lw_coordinates[0]][lowest_weight_direction] = 1
        self.nodes[lw_adjacent_coordinates[1]][lw_adjacent_coordinates[0]][(lowest_weight_direction + 2) % 4] = 1
        self.all_accepted_nodes.append(lw_adjacent_coordinates)
        self.nodes_to_look_at.append(lw_adjacent_coordinates)

        return True

    def generate_maze(self):
        while self.pass_through():
            pass

        return self.nodes
