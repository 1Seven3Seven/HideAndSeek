# A documented history of the versions here

## Version 1

A simple client and server that communicates the player position and the enemy position alongside the enemies target.  
This was in an attempt to see the lag between the client and the sever.

In the client, the white dot is the player, the green dot is the enemy, the red dot is the enemies target.  
The target is the players position according to the server at that point in time.  
I notice that, when run on the same machine, there is a one frame delay.  
When running on different machines, there is the same one frame delay, but with occasional stuttering.

Because the code to receive information is inside the game loop, when the network lags, so does the game.

## Version 2

A way to prevent network stuttering from causing the client to stutter.  
There is now a thread that will constantly receive any updated positions from the client/server.  
The client/server simply reads those positions and then displays the results.

Because code to receive the positioning information is now in a thread, when the network stutters, the client does not.

I did notice that messages tended to back up, that is rather than simply receiving `100,100` the client/server
received `100,100100,100`.    
I have fixed this in a rather rudimentary way of taking the first instance of the data and ignoring the rest.  
You can see a slight problem if the following messages were received:

```
100,100
100,100100,100
100,100
```

The server translates this into:

```
100,100
100,100100
100,100
```

And so the client/server's y position of an entity may jump erratically.  
This also uses the oldest of the positions.  
To fix this each message can be sent with an ending character `100,100|` which the message is then split upon, grabbing
the last entry.  
I did not do this however, because I could not be bothered at the time, regardless of how simple it is.
