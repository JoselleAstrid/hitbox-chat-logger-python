## Overview

This Python program joins a stream chat on hitbox.tv anonymously, and logs chat messages to a file.

Logging chat to a file is easy if the chat runs on IRC, since there are various IRC clients (mIRC, HexChat, etc.) that can log IRC messages. But unlike Twitch chat, Hitbox chat operates on websockets, not IRC. There used to be an unofficial IRC gateway for Hitbox chat at glados.tv, but it's not operational anymore. And there's no standard websockets chat protocol, so a program that supports Hitbox chat has to be written specifically for Hitbox chat. This is why Hitbox chat client solutions are hard to find.

What this program does and doesn't do:

* This is just a simple chat logger running in a console window. It's not a full chat client. In particular, there's no support to type messages in chat using this program. That would require logging into Hitbox, which could be supported... but I also couldn't figure out how to accept text input while listening for chat messages (on Windows machines in particular).
* Chat messages are logged (and printed to the console window) with timestamps.
* If no server messages or pings are received for a while, the program will assume it's disconnected and will attempt a reconnect. If a connect fails, it'll attempt to re-connect after waiting a bit.
* On hitbox.tv, it shows you some recent messages (which happened when you were not there) when you enter a channel, but this program does not support that feature.

## Setup and running (from source)

* Get Python 3.4 or higher, since this program uses asyncio. (Tested with version 3.4.3)
* Install the Python packages `requests` and `websockets`. (Tested with requests 2.7.0 and websockets 2.4)
* Run the `main.py` script to run the program.

## Usage

* Enter a Hitbox channel name to join.
* It should start logging messages to the file `hitbox__<channel name>.txt`, so there is one log file per channel. Next time you run the chat logger for that channel, it'll just add to the existing log file if there is one.
* The first time you run the program, the chat log files are saved under the sub-directory `logs` in the same directory as the program. The first run of the program also creates a preferences file, `prefs.txt`, which lets you change the log directory. To change the log directory, open `prefs.txt` file in a text editor, and change the `log_directory` line after the equals sign. You can specify an absolute file path (like `log_directory = C:\Chatlogs\Hitbox`) or a relative file path (like `log_directory = ..\Hitbox-chat-logs`).
  * You probably don't need to worry about the `status_display_level` preference, but if you want to see how the program works in more detail, you can change it to `info` or `debug`.
* Exit the program by closing the program window, or by typing Ctrl+C. For Ctrl+C, it might take several seconds for the program exit to register (on Windows at least).
