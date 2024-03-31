from .Types import Node


class Maze:
    """
    Stores information about a maze.
    """

    def __init__(self, width: int, height: int, nodes: list[list[Node]] | None = None):
        self.width: int = width
        """The width of this maze."""
        self.height: int = height
        """The height of this maze."""

        self.nodes: list[list[Node]] = nodes
        """
        A 2D array of the nodes for this maze.
        """

        if nodes is None:
            self.nodes = [
                [
                    [0, 0, 0, 0] for _ in range(width)
                ] for _ in range(height)
            ]
