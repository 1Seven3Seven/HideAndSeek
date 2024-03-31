from .MapData import MapData
from .MazeGenerator import Maze


def generate_map_using_maze(maze: Maze) -> MapData:
    width_3 = maze.width * 3
    height_3 = maze.height * 3

    map_data = MapData(width_3, height_3)

    for x in range(width_3):
        map_data.data[0][x] = 1
        map_data.data[height_3 - 1][x] = 1

    for y in range(height_3):
        map_data.data[y][0] = 1
        map_data.data[y][width_3 - 1] = 1

    for y in range(height_3):
        for x in range(width_3):
            if (x % 3 == 0 or x % 3 == 2) and (y % 3 == 0 or y % 3 == 2):
                map_data.data[y][x] = 1
                continue

    for y in range(maze.height):
        y_3 = y * 3

        for x in range(maze.width):
            x_3 = x * 3

            node = maze.nodes[y][x]

            if node == [1, 1, 1, 1]:
                map_data.data[y_3][x_3] = 0
                map_data.data[y_3][x_3 + 2] = 0
                map_data.data[y_3 + 2][x_3] = 0
                map_data.data[y_3 + 2][x_3 + 2] = 0
                continue

            if node[0] != 1:  # Left
                map_data.data[y_3 + 1][x_3] = 1

            if node[1] != 1:  # Top
                map_data.data[y_3][x_3 + 1] = 1

            if node[2] != 1:  # Right
                map_data.data[y_3 + 1][x_3 + 2] = 1

            if node[3] != 1:  # Bottom
                map_data.data[y_3 + 2][x_3 + 1] = 1

    for x in range(1, width_3 - 1):
        map_data.data[1][x] = 0
        map_data.data[height_3 - 2][x] = 0

    for y in range(1, height_3 - 1):
        map_data.data[y][1] = 0
        map_data.data[y][width_3 - 2] = 0

    return map_data
