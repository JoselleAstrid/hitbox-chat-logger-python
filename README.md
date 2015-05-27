## Overview

This Python program joins a stream chat on hitbox.tv anonymously, and logs chat messages to a file.

Note that Hitbox chats operate on websockets, not IRC, which is why IRC doesn't really work with Hitbox chat. There used to be an IRC gateway for Hitbox chat at glados.tv, but it's not operational anymore.

* This is just a bare-bones chat logger; there's no support to type messages in chat using this program. That would require logging into Hitbox, which could be supported... but I also couldn't figure out how to accept text input while listening for chat messages (on Windows in particular).
* Messages are printed and logged with timestamps.
* If no server messages or pings are received for a while, it'll assume it's disconnected and will attempt a reconnect. If a connect fails, it'll attempt a reconnect after waiting a bit.
* Getting past messages when you enter a channel is not supported.

## Setup and running (from source)

* Get Python 3.4 or higher. (Tested with version 3.4.3)
* Install the Python packages `requests` and `websockets`. (Tested with requests 2.7.0 and websockets 2.4)
* Run the `main.py` script to run the program.

## Usage

* Enter a Hitbox channel name to join. It should start logging messages to the file `hitbox__<channel name>.txt`. Next time you run the chat logger for that channel, it'll just add to the existing log file if there is one.
* Exit the program with Ctrl+C. It might take some time for the program exit to register, like up to 10 seconds (on Windows at least).
