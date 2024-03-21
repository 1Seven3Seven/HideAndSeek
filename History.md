# A documented history of the versions here

## Version 1

A simple client and server that communicates the player position and the enemy position alongside the enemies target.  
This was in an attempt to see the lag between the client and the sever.

In the client, the white dot is the player, the green dot is the enemy, the red dot is the enemies target.  
The target is the players position according to the server at that point in time.  
I notice that, when run on the same machine, there is a one frame delay.  
When running on different machines, there is the same one frame delay, but with occasional stuttering.

Because the code to receive information is inside the game loop, when the network lags, so does the game.
