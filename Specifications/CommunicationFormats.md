# Communication

The different types of messages that can be sent.

## Server Messages

A list of the messages a server can send to the clients.

- [Handling Client Connections and Disconnections](#handling-client-connections-and-disconnections)
    - [Client New ID](#client-new-id)
    - [Client ID Parrot Correct](#client-id-parrot-correct)
    - [Client Disconnect](#client-disconnect)
    - [Client Disconnect Acknowledgement](#client-disconnect-acknowledgement)
    - [Client Reconnect Accepted](#client-reconnect-accepted)
- [Transferring Map Data](#transferring-map-data)
    - [Map Data](#map-data)
    - [Map Checksum Correct](#map-checksum-correct)
    - [Map Checksum Incorrect](#map-checksum-incorrect)
    - [Starting Position](#starting-position)
- [Updating Client Information](#updating-client-information)
    - [Client Name Accepted](#client-name-accepted)
    - [Client Name Rejected](#client-name-rejected)
    - [New Client Name Notification](#new-client-name-notification)
    - [Client Connected Notification](#client-connected-notification)
    - [Client Disconnected Notification](#client-disconnected-notification)
- [In Game Messages](#in-game-messages)
    - [Position and State Data](#position-and-state-data)
    - [End Game](#end-game)
- [Misc](#misc)
    - [Start Game](#start-game)

### Handling Client Connections and Disconnections

#### Client New ID

Each new client must be given a unique client id.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x01                         | Unsigned Integer      |

#### Client ID Parrot Correct

A client must parrot back its Client ID.  
If the parroted Client ID is the same as the one the server sent, this must be indicated

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x02                         |

#### Client Disconnect

A statement to a client that it will be disconnected.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x03                         |

#### Client Disconnect Acknowledgement

An acknowledgement of a client wanting to be disconnected.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x04                         |

#### Client Reconnect Accepted

If a client abruptly disconnects, and it attempts to reconnect, it can send a reconnect request alongside its client
id.  
If this is a valid reconnect attempt then this must be acknowledged.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x05                         |

### Transferring Map Data

#### Map Data

Each client must receive the map before being allowed to start the game.  
Used to send map data to clients.

##### Format

| Message Indicator<br/>1 Byte | Map Width<br/>4 Bytes | Map Height<br/>4 Bytes | Map Data<br/>Variable Length |
|------------------------------|-----------------------|------------------------|------------------------------|
| 0x11                         | Unsigned Integer      | Unsigned Integer       | ...                          |

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
| 0x12                         |

#### Map Checksum Incorrect

Once a client has received all the map data, a checksum should be calculated and sent to the server.  
Used to indicate that the received checksum was incorrect.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x13                         |

#### Starting Position

Once map data has been sent, a client must be notified of its starting position.  
Must be sent after the map data has been sent and correct checksum received.

##### Format

| Message Indicator<br/>1 Byte | X Position<br/>4 Bytes | Y Position<br/>4 Bytes |
|------------------------------|------------------------|------------------------|
| 0x14                         | Integer                | Integer                |

### Updating Client Information

Clients may update their name, this should be responded to, and other clients should be notified.  
Clients may also connect and disconnect, other clients should be notified.

#### Client Name Accepted

A client may send a new name during the lobby phase.  
Used to indicate that the clients name was accepted.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x21                         |

#### Client Name Rejected

A client may send a new name during the lobby phase.  
Used to indicate that the clients name was rejected.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0x22                         |

#### New Client Name Notification

Once a clients name has been accepted, the other clients must be notified of this.  
Used to send a clients name to other clients.

##### Format

| Message Indicator<br/>1 Byte | String Length<br/>4 Bytes | String Data<br/>Variable Length |
|------------------------------|---------------------------|---------------------------------|
| 0x23                         | Unsigned Integer          | ...                             |

#### Client Connected Notification

When a new client connects, all other clients need to be notified of this.  
Used to notify clients that a client has connected and what its client id is.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x24                         | Unsigned Integer      |

#### Client Disconnected Notification

When a client disconnects, all other clients need to be notified of this.  
Used to notify clients that a client has disconnected and what its client id is.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x25                         | Unsigned Integer      |

### In Game Messages

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

### Misc

#### Start Game

Once all clients have indicated that they are ready a game can be started.  
Used to begin a game.

##### Format

| Message Indicator<br/>1 Byte |
|------------------------------|
| 0xF0                         |

## Client Messages

A list of the messages a client can send to the server.

- [Connecting or Disconnecting from a Server](#connecting-or-disconnecting-from-a-sever)
    - [New Connection Request](#new-connection-request)
    - [Client ID Parrot](#client-id-parrot)
    - [Client Reconnection Request](#client-reconnection-request)

### Connecting or Disconnecting from a Sever

#### New Connection Request

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
| 0x03                         | Unsigned Integer      |

#### Client Reconnection Request

If a client abruptly disconnects and wants to reconnect to the server preserving information, a reconnect attempt can be
made.  
A client sends a reconnect request alongside its client id.

##### Format

| Message Indicator<br/>1 Byte | Client ID<br/>4 Bytes |
|------------------------------|-----------------------|
| 0x02                         | Unsigned Integer      |

### Other

#### Map Checksum

Once a client has received the map data it needs to calculate the checksum for that map.  
Only the map data itself should be used for the checksum, not the message indicator or the size.

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

