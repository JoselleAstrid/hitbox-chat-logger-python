import asyncio
import datetime
import json
import logging
import os
import random
import sys
import time

import requests
import websockets
                
                
                
def utc_to_local(utc_time):
    return utc_time.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    
    
    
def print_error_and_exit(s):
    print(s)
    # Before proceeding with ending the program, let the console window stay
    # up by prompting for input. This lets the user read what went wrong.
    input("(Press Enter to close the program)")
    sys.exit()
    
    
    
class Prefs():
    
    default_file_contents = (
        "log_directory = logs\n"
        "status_display_level = error\n"
    )
    filename = 'prefs.txt'
    prefs = None
                 
    @classmethod
    def create_file(cls):
        with open(cls.filename, 'w') as f:
            f.write(cls.default_file_contents)
        
    @classmethod
    def load_from_file(cls):
        cls.prefs = dict()
        
        with open(cls.filename, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if len(line) == 0:
                    continue
                
                try:
                    name, value = line.split('=')
                except ValueError as e:
                    print_error_and_exit((
                        "prefs.txt: Line {} couldn't be read."
                        " Must have exactly one equals sign."
                    ).format(line_num))
                    
                name = name.strip()
                value = value.strip()
                cls.prefs[name] = value
                
    @classmethod
    def get(cls, name):
        if name in cls.prefs:
            return cls.prefs[name]
        else:
            print_error_and_exit((
                "prefs.txt: Couldn't find the preference '{}'."
                " If you have any trouble fixing this, just delete prefs.txt,"
                " and a new one should be created the next time you run this"
                " program."
            ).format(name))



def unwrap_message(wrapped_msg_d):
    # - Under the args key of an object/dict
    # - In a list as the only element
    # - As a string
    return json.loads(wrapped_msg_d['args'][0])



def wrap_message(msg_d):
    return {
        'name': 'message',
        'args': [msg_d],
    }



class ChatClient():
    
    def __init__(self, log_directory, logging_level):
        
        logging.basicConfig(
            format='..........%(levelname)s: %(message)s',
            level=logging_level
        )
        
        # Save the futures of the chat client tasks so we can cancel them
        # if needed.
        self.futures = dict()
        
        # If we receive no server messages for this long (including pings),
        # then we'll consider ourselves disconnected.
        self.time_until_disconnected = datetime.timedelta(seconds=100)
        
        # How often to compare the time since the last message versus the
        # "time until disconnected".
        # Also determines the max time we have to wait to stop the program
        # with Ctrl+C.
        self.disconnect_check_interval_seconds = 5
        
        # If a connect attempt fails, wait this long until another attempt.
        self.connect_retry_seconds = 10
        
        channel_name_input = input("Which streamer's chat are you joining?: ")
        self.channel_name = channel_name_input.lower()
        
        random.seed()
        random_number = random.randint(100000,999999)
        self.my_username = 'guest_{}'.format(random_number)
        
        chat_server_label = 'hitbox'
        log_filename = '{}__{}.txt'.format(chat_server_label, self.channel_name)
        self.log_filepath = os.path.join(log_directory, log_filename)
        
        # If the log file exists, show the latest lines from it.
        if os.path.isfile(self.log_filepath):
            print("Found a log file for this chat.")
            print("---------- Last few lines from log ----------")
            with open(self.log_filepath, 'r') as existing_log_file:
                # Make a pass through the file to count lines
                line_count = sum(1 for line in existing_log_file)
                # Reset the file pointer to the beginning
                existing_log_file.seek(0)
                # Read and print the last several lines
                for line_num, line in enumerate(existing_log_file, 1):
                    if line_num > line_count - 10:
                        print(line.strip())
            print("---------- End of log sample ----------")
        else:
            # Log file doesn't exist; how about the directory for log files?
            if not os.path.isdir(log_directory):
                # How about creating it?
                try:
                    os.mkdir(log_directory)
                except OSError:
                    print_error_and_exit(
                        "The log file directory doesn't exist and couldn't be"
                        " created. Please check prefs.txt to see if it was"
                        " typed correctly."
                    )
            print("You haven't logged anything from this chat yet.")
        # Now we should be set to write to the log filepath.
        print("\n")
        
    def write(self, s, logging_level=None, server_status=False, chat_log=False,
        timestamp=False, include_date=False):
    
        if include_date:
            date_format = '%Y/%m/%d %H:%M:%S'
        else:
            date_format = '%H:%M:%S'
        
        timestamp_obj = datetime.datetime.now()
        timestamp_str = timestamp_obj.strftime(date_format)
        to_write = "[{}] {}".format(timestamp_str, s)
            
        if logging_level:
            logging.log(logging_level, to_write)
        elif server_status:
            # Not really in a logging.log category, and still something
            # we want to differentiate from normal chat messages.
            print(".........." + to_write)
        elif chat_log:
            # Something we'd put in the chat log file.
            print(to_write)
            with open(self.log_filepath, 'a') as f:
                # Since we open and (implicitly) close the file every time
                # we write, the writes get saved as they happen.
                f.write(to_write + '\n')
                
        # Turns out there are no other kinds of messages that we'd run
        # through this function at the moment.

    @asyncio.coroutine
    def connect(self):
        
        chat_servers_url = 'http://api.hitbox.tv/chat/servers?redis=true'
        
        response = None
        while not response:
            try:
                response = requests.get(chat_servers_url)
            except requests.exceptions.ConnectionError:
                s = (
                    "Connect failed. Trying again in {} seconds."
                ).format(self.connect_retry_seconds)
                self.write(s, timestamp=True, server_status=True)
                
                yield from asyncio.sleep(self.connect_retry_seconds)
                
        server_ip = response.json()[0]['server_ip']
        
        websocket_id_url = server_ip + '/socket.io/1/'
        response = requests.get('http://' + websocket_id_url)
        # From the response text, get everything before the first colon
        connection_id = response.text[:(response.text.index(':'))]
        
        ws_url = 'ws://' + websocket_id_url + 'websocket/' + connection_id
        self.websocket = yield from websockets.connect(ws_url)
        self.time_last_received = datetime.datetime.utcnow()
    
    @asyncio.coroutine
    def wait_for_messages(self):
        
        while True:
            received_message = yield from self.websocket.recv()
            logging.debug(' << ' + str(received_message))
            
            if received_message is None:
                # Websocket connection has failed. Need to reconnect.
                self.write((
                    "Disconnected; websocket connection failed."
                    " Attempting to reconnect..."
                ), timestamp=True, server_status=True)
                self.futures['check_for_disconnect'].cancel()
                self.futures['wait_for_messages'].cancel()
                return
                
            self.time_last_received = datetime.datetime.utcnow()
            
            if received_message == '1::':
                # Connect confirmation.
                # Reply with a channel join request.
                send_d = {
                    'method': 'joinChannel',
                    'params': {
                        'channel': self.channel_name,
                        'name': self.my_username,
                        'token': '',
                        'isAdmin': False,
                    },
                }
                reply_to_send = '5:::' + json.dumps(wrap_message(send_d))
                
                s = "*** Joining channel: {}".format(self.channel_name)
                self.write(s, timestamp=True, chat_log=True, include_date=True)
                
            elif received_message == '2::':
                # Ping. Respond with a pong.
                reply_to_send = '2::'
                
                s = "Ping received; sending pong"
                self.write(s, logging_level=logging.INFO, timestamp=True)
                
            elif received_message.startswith('5:::'):
                receive_d = unwrap_message(json.loads(
                    received_message[len('5:::'):]
                ))
                
                if receive_d['method'] == 'chatMsg':
                    params = receive_d['params']
                    username = params['name']
                    text = params['text']
                    
                    # Log the message.
                    s = '<{}> {}'.format(username, text)
                    self.write(s, timestamp=True, chat_log=True)
                    reply_to_send = None
                    
                else:
                    # Something else that we don't handle.
                    reply_to_send = None
                
            else:
                # Something else that we don't handle.
                reply_to_send = None
                
            if reply_to_send:
                # Send our reply, if any.
                status = yield from self.websocket.send(reply_to_send)
                logging.debug(' >> ' + reply_to_send)
    
    @asyncio.coroutine
    def check_for_disconnect(self):
        
        while True:
            yield from asyncio.sleep(self.disconnect_check_interval_seconds)
            
            time_now = datetime.datetime.utcnow()
            if time_now - self.time_last_received > self.time_until_disconnected:
                s = (
                    "Disconnected? No server interaction for at least {} seconds."
                    " Attempting to reconnect..."
                ).format(self.time_until_disconnected.total_seconds())
                self.write(s, timestamp=True, server_status=True)
                self.futures['wait_for_messages'].cancel()
                self.futures['check_for_disconnect'].cancel()
                return
                
    # def part_channel(self):
    #     # Leave the channel (there's no server disconnect command).
    #     send_d = {
    #         'method': 'partChannel',
    #         'params': {
    #             'channel': self.channel_name,
    #             'name': self.my_username,
    #         },
    #     }
    #     reply_to_send = '5:::' + json.dumps(wrap_message(send_d))
        
    #     logging.info(' >> ' + reply_to_send)
    #     yield from self.websocket.send(reply_to_send)
    #     "Leaving the channel."
        
    #     # Exit the program.
    #     self.log_file.close()
    #     sys.exit()





if __name__ == '__main__':
    
    # Load preferences.
    try:
        Prefs.load_from_file()
    except IOError:
        Prefs.create_file()
        Prefs.load_from_file()
        
    # Get logging level from prefs.
    logging_level_str_to_const = dict(
        critical = logging.CRITICAL,
        error = logging.ERROR,
        warning = logging.WARNING,
        info = logging.INFO,
        debug = logging.DEBUG,
    )
    # Prefs calls it 'status_display_level' to avoid end-user confusion
    # with the chat-log file (which also has the word 'log' in it).
    logging_level = logging_level_str_to_const[
        Prefs.get('status_display_level').lower()
    ]
    
    # Initialize chat client.
    client = ChatClient(Prefs.get('log_directory'), logging_level)
    
    
    # Run chat client.
    while True:
        # Connect to the server.
        asyncio.get_event_loop().run_until_complete(client.connect())
        
        # Set up the main chat client functions as concurrent tasks.
        client.futures['wait_for_messages'] = \
            asyncio.async(client.wait_for_messages())
        client.futures['check_for_disconnect'] = \
            asyncio.async(client.check_for_disconnect())
            
        # These tasks will run forever until one of two things happens:
        #
        # (1) A chat disconnect is detected, in which case the tasks will
        # cancel themselves, and we will go back to the top of the while
        # loop here.
        # (2) Something crashes or we press Ctrl+C.
        tasks = [future for k,future in client.futures.items()]
        asyncio.get_event_loop().run_until_complete(asyncio.wait(tasks))
    
