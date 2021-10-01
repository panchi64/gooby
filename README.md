# Discord Server Bot
This is an automated assistant that has been built to suit all of my friend's needs in our Discord server.

THIS PROJECT IS NOT COMPLETE, VIEW THE COMMITS TO SEE THE MOST UP-TO-DATE WORKING FUNCTIONALITY

## Features
The bot has the following capabilities:
* Playing music from multiple platforms including:
    * Spotify
    * YouTube
    * Soundcloud
* D&D assistance
    * Initiative tracker
    * Dice Roller (any size)
    * Human character face generator (TBD)
* Receive patch notes from your favorite games! The current games supported are:
    * Overwatch
    * Valheim
    * Deep Rock Galactic
    * Starbase
    * Apex Legends
    * Valorant
    * Elite Dangerous
    * Guild Wars 2
    * Vermintide 2
    * Rocket League
    * TaleSpire
    * Genshin Impact
    * Splitgate
    * Minecraft
        * Snapshots
        * Full releases
        * OptiFine
* Define any word you prompt it. Using a combination of both Urban Dictionary and Google
* Notify when any given streamers are live!
* It can create a voting system for debates within a server. With the power of DEMOCRACY!
* Remotely manage a Minecraft server by connecting it to your server! (The server must be run on Spigot/Bukkit) Functionality includes:
    * Restarting the server every X amount of time or manually
    * Initializing the server
    * Stopping the server
    * Backing up Minecraft world
    * Allowlist management
    * Sending messages from discord to the server
    * Providing server performance details when requested like:
        * Tick rate
        * Processor and RAM usage
        * IP provision on request
    * Providing a link to download the server's world
* Randomly choose a message in a given channel and make fun of it. For example:
    * ``Tomorrow we ride at dawn`` gets converted to ``Look at this clown saying "tOmOrRoW wE rIdE aT dAwN"`` followed by a given emoji.
* Manual override for sending and reading messages.

## Dependencies
* [Dotenv](https://github.com/cdimascio/dotenv-java)
* [Gson](https://github.com/google/gson)
* [Google's OAuth Client](https://developers.google.com/api-client-library/java/google-oauth-java-client)
* [Javacord](https://github.com/Javacord/Javacord)
* [Log4j2](https://logging.apache.org/log4j/2.x/maven-artifacts.html)
