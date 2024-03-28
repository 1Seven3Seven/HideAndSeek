# Communication

The different types of messages that can be sent.

## Server Messages

A list of the messages a server can send to the clients.

- [Client ID](#client-id)
- [Client ID Correct](#client-id-correct)
- [Client Disconnect](#client-disconnect)
- [Client Reconnect Accepted](#client-reconnect-accepted)
- [Start Game](#start-game)
- [Map Data](#map-data)
- [Map Checksum Correct](#map-checksum-correct)
- [Map Checksum Incorrect](#map-checksum-incorrect)
- [Client Name Accepted](#client-name-accepted)
- [Client Name Rejected](#client-name-rejected)
- [New Client Name](#new-client-name)
- [Position and State Data](#position-and-state-data)
- [End Game](#end-game)
- [New Client Connected](#new-client-connected)

### Specifics of Messages

#### Client ID

Each new client must be given a unique Client id.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x01                         | Unsigned Integer      |

#### Client ID Correct

A client must parrot back its Client ID.  
If the parroted Client ID is the same as the one the server sent, this must be indicated

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x02                         |

#### Client Disconnect

An acknowledgement of a client wanting to be disconnected.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x03                         |

#### Client Reconnect Accepted

If a client abruptly disconnects, and it attempts to reconnect, it can send a reconnect request alongside its client
id.  
If this is a valid reconnect attempt then this must be acknowledged.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x04                         |

#### Start Game

Once all clients have indicated that they are ready a game can be started.  
Used to begin a game.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x05                         |

#### Map Data

Each client must receive the map before being allowed to start the game.  
Used to send map data to clients.

##### Format

| Message Indicator<br/>1 Byte | Map Width<br/>4 Bytes | Map Height<br/>4 Bytes | Map Data<br/>Variable Length |
|------------------------------|-----------------------|------------------------|------------------------------|
| 0x06                         | Unsigned Integer      | Unsigned Integer       | ...                          |

For now the map is a rectangle.  
The width and height are used to calculate the size of the map data.

The width is the number of bits per row of the map.  
The height is the number of rows.

The map data format is simple.  
It is a rectangle where each cell has one of two states, filled in or not.

Here is an example map, width is 8, height is 4:

```
▉▉▉▉▉▉▉▉
▉ ▉  ▉ ▉
▉      ▉
▉▉▉▉▉▉▉▉
```

Each cell in the map is represented by one bit, 1 for filled in and 0 for not.  
Thus this converts to:

```
11111111
10100101
10000001
11111111
```

If the width of the map is not a multiple of 8, it should be padded with zeros to become a multiple of 8.  
This padding should be discarded.

#### Map Checksum Correct

Once a client has received all the map data, a checksum should be calculated and sent to the server.  
Used to indicate that the received checksum was correct.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x07                         |

#### Map Checksum Incorrect

Once a client has received all the map data, a checksum should be calculated and sent to the server.  
Used to indicate that the received checksum was incorrect.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x08                         |

#### Client Name Accepted

A client may send a new name during the lobby phase.  
Used to indicate that the clients name was accepted.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x09                         |

#### Client Name Rejected

A client may send a new name during the lobby phase.  
Used to indicate that the clients name was rejected.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x0A                         |

#### New Client Name

Once a clients name has been accepted, the other clients must be notified of this.  
Used to send a clients name to other clients.

##### Format

| Message Indicator<br/>1 Byte | String Length<br/>4 Bytes | String Data<br/>Variable Length |
|------------------------------|---------------------------|---------------------------------|
| 0x0B                         | Unsigned Integer          | ...                             |

#### Position and State Data

The position and state data has no message indicator.  
Once the start message has been sent, the only messages to be communicated is the position and state data.

##### Format

The format for one client:

| Client ID<br/>4 Bytes | Client State<br/>1 Byte | Position X<br/>4 Bytes | Position Y<br/>4 Bytes |
|-----------------------|-------------------------|------------------------|------------------------|
| Unsigned Integer      |                         | Integer                | Integer                |    

The size of the position and state data is the size of one client (13 Bytes) multiplied by the number of clients.  
So given 5 clients, the size of the position and state data is `5 * 13 = 65 Bytes`.

#### End Game

Client IDs must be non-zero and positive.  
As such, when wanting to end a game, a Client ID of 0 should be sent.  
The client will expect to receive the same number of bytes as the position and state data.  
As such to end a game, a message of same size as the position and state data should be sent, with all zeroes.

Given the same example of 5 clients, we need to send 65 bytes of 0.

#### New Client Connected

When a new client connects, all other clients need to be notified.  
Used to indicate to other clients that a new client has connected. 

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x0C                         | Unsigned Integer      |

## Client Messages

A list of the messages a client can send to the server.

- [New Connection](#new-connection)
- [Client ID Parrot](#client-id-parrot)
- [Map Checksum](#map-checksum)
- [Name Change](#name-change)
-

### Specifics of Messages

#### New Connection

When a client connects to the server, it must indicate that it is a new client.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x01                         |

#### Client ID Parrot

When a client receives its client id number, it must parrot it to the server.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x02                         | Unsigned Integer      |

#### Map Checksum

Once a client has received the map data it needs to calculate the checksum for that map.  
The checksum is a CRC (Cyclic Redundancy Check) checksum resulting in a 32-bit unsigned integer.    
In python [zlib.crc32](https://docs.python.org/3/library/zlib.html#zlib.crc32) should be used.

##### Format

| Message Indicator<br/>1 Byte | Checksum<br/>4 Bytes |
|------------------------------|----------------------|
| 0x03                         | Unsigned Integer     |

#### Name Change

A client may want to change the name it is referred to as.  
Used to indicate to the server that a new name is used.  
The server may accept or reject this new name, in the case of rejection, the old name should be used.

##### Format

| Message Indicator<br/>1 Byte | String Length<br/>4 Bytes | String Data<br/>Variable Length |
|------------------------------|---------------------------|---------------------------------|
| 0x04                         | Unsigned Integer          | ...                             |

