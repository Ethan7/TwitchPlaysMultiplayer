# Code taken from http://www.wituz.com/make-your-own-twitch-plays-stream.html #
# All credit for this code goes to Wituz #

import socket
import sys
import re
 
class Twitch:
 
    user = "";
    oauth = "";
    s = None;
 
    def twitch_login_status(self, data):
        if not re.match(r'^:(testserver\.local|tmi\.twitch\.tv) NOTICE \* :Login unsuccessful\r\n$', data): return True
        else: return False
 
    def twitch_connect(self, user, key):
        self.user = user;
        self.oauth= key;
        print("Connecting to twitch.tv");
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        s.settimeout(0.6);
        connect_host = "irc.twitch.tv";
        connect_port = 6667;
        try:
            s.connect((connect_host, connect_port));
        except:
            print("Failed to connect to twitch");
            sys.exit();
        print("Connected to twitch");
        print("Sending our details to twitch...");
        US = 'USER %s\r\n' % user;
        PA = 'PASS %s\r\n' % key;
        NI = 'NICK %s\r\n' % user;
        s.sendall(US.encode('utf-8'));
        s.sendall(PA.encode('utf-8'));
        s.sendall(NI.encode('utf-8'));
 
        if not self.twitch_login_status(s.recv(1024).decode('utf-8')):
            print("... and they didn't accept our details");
            sys.exit();
        else:
            print("... they accepted our details");
            print("Connected to twitch.tv!")
            self.s = s;
            JO = 'JOIN #%s\r\n' % user;
            s.sendall(JO.encode('utf-8'));
            s.recv(1024);
 
    def check_has_message(self, data):
        return re.match(r'^:[a-zA-Z0-9_]+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+(\.tmi\.twitch\.tv|\.testserver\.local) PRIVMSG #[a-zA-Z0-9_]+ :.+$', data)
 
    def parse_message(self, data):
        return {
            'channel': re.findall(r'^:.+\![a-zA-Z0-9_]+@[a-zA-Z0-9_]+.+ PRIVMSG (.*?) :', data)[0],
            'username': re.findall(r'^:([a-zA-Z0-9_]+)\!', data)[0],
            'message': re.findall(r'PRIVMSG #[a-zA-Z0-9_]+ :(.+)', data)[0]
        }
 
    def twitch_recieve_messages(self, amount=1024):
        data = None
        try: data = self.s.recv(1024).decode('utf-8');
        except: return False;
 
        if not data:
            print("Lost connection to Twitch, attempting to reconnect...");
            self.twitch_connect(self.user, self.oauth);
            return None
 
        #self.ping(data)
 
        if self.check_has_message(data):
            return [self.parse_message(line) for line in filter(None, data.split('\r\n'))];