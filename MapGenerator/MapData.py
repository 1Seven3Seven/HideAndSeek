import struct


class MapData:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height

        self.data: list[list[int]] = [
            [
                0 for _ in range(width)
            ] for _ in range(height)
        ]

    def _convert_data_to_list_of_strings(self) -> list[str]:
        """
        Converts the underlying map data into a list of strings padded so length is a multiple of 8.

        :return: A list of strings representing the map data.
        """

        _length = len(self.data[0])
        extension_len = 8 - _length % 8
        extension = "0" * extension_len
        rows = ["".join([str(_value) for _value in _row]) + extension for _row in self.data]

        return rows

    def save_raw(self, filename: str) -> None:
        """
        Save the map data in a raw binary format.

        :param filename: The filename to save under.
        """

        if not filename.endswith(".mapdata"):
            filename += ".mapdata"

        rows = self._convert_data_to_list_of_strings()

        header = struct.pack("<II", self.width, self.height)

        with open(filename, "wb") as f:
            f.write(header)

            for row in rows:
                row_bytes = bytes(
                    [
                        int(row[n:n + 8], 2)
                        for n in range(0, len(row), 8)
                    ]
                )
                f.write(row_bytes)

    @classmethod
    def from_raw(cls, filename: str):
        if not filename.endswith(".mapdata"):
            raise ValueError(f"Expected file of type '*.mapdata', got {filename}")

        with open(filename, "rb") as f:
            header = f.read(8)

            width, height = struct.unpack("<II", header)

            map_data = cls(width, height)

            width_in_bytes = int((width + 7) // 8)

            for y in range(height):
                row_bytes = f.read(width_in_bytes)

                row_bits_str = "".join(f'{byte:08b}' for byte in row_bytes)

                for i in range(width):
                    map_data.data[y][i] = int(row_bits_str[i])

        return map_data

    def save_simple(self, filename: str) -> None:
        """
        Save the map data in a simplified format compared to the raw format.

        The width and height are comma seperated on the first line.
        Each row of the map is represented by ones and zeros that would make up the raw bytes.
        New lines are used to make it a little more readable.

        Not intended to be used outside of testing.

        :param filename: The filename to save under.
        """

        if not filename.endswith(".txt"):
            filename += ".txt"

        with open(filename, "w") as f:
            f.write(f"{self.width},{self.height}\n")
            f.writelines(
                [line + "\n" for line in self._convert_data_to_list_of_strings()]
            )

    def save_pretty(self, filename: str) -> None:
        """
        Save the map data in a textfile using UTF-8 characters to be easily viewed.

        Not intended to be used outside of testing.

        :param filename: The filename to save under.
        """

        if not filename.endswith(".txt"):
            filename += ".txt"

        with open(filename, "w", encoding="UTF-8") as f:
            f.writelines(
                [
                    "".join([str("▉" if wall else " ") for wall in row]) + "\n" for row in self.data
                ]
            )
