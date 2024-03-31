# MapFile

Information regarding how a map file is stored.

## Format

A map file begins with a header of 8 bytes, containing integer (little endian) values representing the width and height
of the map:

| Map Width<br/>4 Bytes | Map Height<br/>4 Bytes |
|-----------------------|------------------------|
| Unsigned Integer      | Unsigned Integer       |

The width represents how many walls exist per row of the map.  
The height represents the number of rows.

Each wall is represented by one bit, 1 for existing and 0 for not.

The width is padded to be a multiple of 8.  
The padding should be ignored.
