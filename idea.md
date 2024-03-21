# Brainstorming

## Handshake , Communication, Termination

### Handshake

We have a little handshake between the client and the server.  
Once a TCP connection has been established.

1. The client sends its initial position in the following format: `initial_position:xxx,yyy|`.
    - The values `xxx` and `yyy` must be at least one digit long.
2. The server then sends the client its id, in the format: `id|`.
    - Where the id is a number of at least one digit.
3. The client sends this same id back.
4. Once the server has received this the message `start|` is then sent.

### Communication

#### Client

The client sends its position in the format:
`xxx,yyy|`.  
The position need only be sent when it has been changed, although sending the same position repeatedly should cause no
problems.

#### Server

If one connected client, the server sends the information in the following format:
`id;xxx,yyy;xxx,yyy|`.  
If multiple clients are connected, then each entry is seperated by a colon:
`id;xxx,yyy;xxx,yyy:id;xxx,yyy;xxx,yyy|`.

A client should consider the target position of every entry, bar itself, to be the actual position of that player.

### Termination

Termination is begun by either the client or the server sending simply the string `terminate`.  
Nothing should be sent after the terminate message.

Once the terminate message has been sent, the client or server must wait for a confirmation message of `terminate` to be
sent back.  
After receiving the confirmation, the socket should be closed.  
The side that initiated the termination should only close the socket after sending the terminate message.

If the server initiated the termination, it should send the termination message to every client and wait for the
response from each.  
No more clients should be accepted.

### Example communication

| Server                 | Client                       |
|------------------------|------------------------------|
|                        | `initial_position:xxx,yyy\|` |
| `start\|`              |                              |
| `id;xxx,yyy:xxx,yyy\|` | `xxx,yyy\|`                  |
| `id;xxx,yyy:xxx,yyy\|` | `xxx,yyy\|`                  |
| `id;xxx,yyy:xxx,yyy\|` | `terminate`                  |
| `terminate`            |                              |

## Server details

Once a client connects, a thread should be established for that client.  
This thread should handle the above handshake, then begin updating the client position.

If multiple positions are received, the latest one should be used.

```
xx1,yy1|xx2,yy2|xx3,yy3|xx4,yy4|xx5,yy5|
-> xx5,yy5|
```

If the terminate message is received, no updating should be done, a return terminate message should be sent.  
After sending the return terminate the socket should be closed and the data for that client deleted.

The initial position received should be used to set up the enemy and target positions for that specific client.

This should allow for the server to handle many clients connecting and disconnecting intermittently.

## Client details

Once the connection to the server has been made, the handshake should be performed, and the id stored somewhere.  
After receiving start, a thread should be established to handle receiving the positioning information.

Similar to the server, if multiple positions sets are received at once, the latest one should be used.

```
id;xx1,yy1;xx1,yy1:id;xx1,yy1;xx1,yy1|id;xx2,yy2;xx2,yy2:id;xx2,yy2;xx2,yy2|
-> id;xx2,yy2;xx2,yy2:id;xx2,yy2;xx2,yy2| 
```
