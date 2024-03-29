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
