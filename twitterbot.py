#!/usr/bin/env python2.7
# -*- coding: UTF-8 -*-
"""Built on habnabit's example twisted IRC bot:
   https://gist.github.com/habnabit/5823693"""

import tweepy, requests, time, os, sys, ConfigParser
from twisted.internet import defer, ssl, endpoints, protocol, reactor, task
from twisted.python import log
from twisted.words.protocols import irc
from urlparse import urlparse

config = ConfigParser.ConfigParser()
config.read("config.ini")

def get_extension(url):
    """Return the filename extension from url, or ''."""
    parsed = urlparse(url)
    root, ext = os.path.splitext(parsed.path)
    return ext # or ext[1:] if you don't want the leading '.'

def decodeIRCmsg(bytes):
    """Yrittää dekoodata vastaanotetut bitit kolmella eri enkoodauksella."""
    try:
        text = bytes.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text = bytes.decode('iso-8859-1')
        except UnicodeDecodeError:
            text = bytes.decode('cp1252')
    return text

def caseInsensitiveComparison(msg, blacklist):
    if blacklist == []:
        return 0
    comparisonMsg = msg.upper()
    comparisonBlacklist = [x.upper() for x in blacklist]
    if any(word in comparisonMsg for word in comparisonBlacklist):
        return 1
    else:
        return 0

class IRCProtocol(irc.IRCClient):
    nickname = config.get('IRC','Nickname')
    realname = config.get('IRC','RealName')
    username = config.get('IRC','Username')

    def __init__(self):
        self.deferred = defer.Deferred()
        self.lasttime = 0
        self.cooldown = config.getint('BotOptions', 'TweetCooldown')

    def connectionLost(self, reason):
        print("IRC-yhteys poikki: %s" % (reason))

    def signedOn(self):
        # This is called once the server has acknowledged that we sent
        # both NICK and USER.
        print("Yhdistetty IRC-serveriin.")
        for channel in self.factory.channels:
            self.join(channel)
        def restartloop(reason): # toimiikohan näin? saa nähdä
            reason.printTraceback()
            print "Replyntarkistusloop kaatui: " + reason.getErrorMessage()
            self.loopcall.start(15.0).addErrback(restartloop)
        def startstream():
            rlistener = ReplyListener()
            replystream = tweepy.Stream(auth = api.auth, listener = rlistener)
            replystream.filter(track=['@' + user], async=True)
        if config.getboolean('BotOptions','FollowReplies'):
            startstream()
            self.loopcall = task.LoopingCall(self.checkReplies)
            self.loopcall.start(15).addErrback(restartloop)

    def joined(self, channel):
        print("Joinattu kanavalle %s" % (channel))

    # Obviously, called when a PRIVMSG is received.
    def privmsg(self, user, channel, message):
        nick, _, host = user.partition('!')
        message = message.strip()
        if not message.startswith('!'):  # not a trigger command
            return  # so do nothing
        command, sep, rest = message.lstrip('!').partition(' ')
        # Get the function corresponding to the command given.
        func = getattr(self, 'command_' + command, None)
        irc.IRCClient # Or, if there was no function, ignore the message.
        currenttime = int(time.time()) # uuden komennon lähetysaika talteen
        if func is None or (currenttime-self.lasttime < self.cooldown): 
        # tarkistaa onko funktiota olemassa, onko cooldown kulunut
            return
        # maybeDeferred will always return a Deferred. It calls func(rest), and
        # if that returned a Deferred, return that. Otherwise, return the
        # return value of the function wrapped in
        # twisted.internet.defer.succeed. If an exception was raised, wrap the
        # traceback in twisted.internet.defer.fail and return that.
        d = defer.maybeDeferred(func, rest)
        # Add callbacks to deal with whatever the command results are.
        # If the command gives error, the _show_error callback will turn the
        # error into a terse message first:
        d.addErrback(self._showError)
        # Whatever is returned is sent back as a reply:
        if channel == self.nickname:
            # When channel == self.nickname, the message was sent to the bot
            # directly and not to a channel. So we will answer directly too:
            d.addCallback(self._sendMessage, nick)
        else:
            # Otherwise, send the answer to the channel, and use the nick
            # as addressing in the message itself:
            d.addCallback(self._sendMessage, channel, nick)

    def _sendMessage(self, msg, target, nick=None):
        if msg == "NOMSG":
            return
        self.lasttime = int(time.time())
        self.msg(target, msg)

    def _showError(self, failure):
        return failure.getErrorMessage()

    def command_t(self, rest):
        """Yksinkertainen tekstitwiittaus-komento: !t twiitti. Palauttaa twiitin urlin."""
        viesti = decodeIRCmsg(rest).replace('\\n', '\n') # enkoodaus ja newlinet toimimaan \n-muodossa
        if caseInsensitiveComparison(viesti, blacklist):
            return "NOMSG"
        api.update_status(viesti)
        url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
        print("Twiitattu: %s" % (url))
        return url 

    def command_tr(self, rest):
        """Replykomento, joka lisää @user jolle replytään viestin alkuun ellei sitä
           jo siinä ollut viestiä lähettäessä."""
        replytweetid = rest.split(' ', 1)[0]
        viesti = decodeIRCmsg(rest.split(' ', 1)[1]).replace('\\n', '\n')
        replytweetauthor = '@' + api.get_status(replytweetid).author.screen_name
        if (replytweetauthor not in viesti) and (replytweetauthor != '@'+user):
            viesti = replytweetauthor + ' ' + viesti
        if caseInsensitiveComparison(viesti, blacklist):
            return "NOMSG"
        api.update_status(viesti, in_reply_to_status_id=replytweetid)
        url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
        print("Twiitattu: %s" % (url))
        return url

    def command_ti(self, rest):
        """Tweet image: !ti kuvanurl twiitti. Kuvan lähteeksi varmistetaan imgur
           turvallisuussyistä.
           TODO: update_with_media on deprecated, korvaa se uudella menetelmällä
           TODO: Nykyisessä muodossa vaaditaan viesti, mahdollista ilman?
           TODO: poista tiedosto virhetilanteessa"""
        imageurl = decodeIRCmsg(rest.split(' ', 1)[0])
        if "imgur.com" not in imageurl:
            return "Uppaa imguriin."
        try:
            viesti = decodeIRCmsg(rest.split(' ', 1)[1]).replace('\\n', '\n')
        except IndexError:
            viesti = None
        if viesti != None:
            if caseInsensitiveComparison(viesti, blacklist):
                return "NOMSG"
        filename = "temp" + get_extension(imageurl)
        request = requests.get(imageurl, stream=True) # vedetään kuva requestiin
        with open(filename, 'wb') as image: # tallennetaan kuva
            for chunk in request:
                image.write(chunk)
        api.update_with_media(filename, status=viesti)
        os.remove(filename)
        url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
        print("Twiitattu: %s" % (url))
        return url

    def command_tri(self, rest):
        """Tweet reply image: !tri twiitid kuvanurl twiitti. Edellinen funktio kuvalla."""
        imageurl = decodeIRCmsg(rest.split(' ', 2)[1])
        if "imgur.com" not in imageurl:
            return "Uppaa imguriin."
        replytweetid = rest.split(' ', 2)[0]
        replytweetauthor = '@' + api.get_status(replytweetid).author.screen_name
        try:
            viesti = decodeIRCmsg(rest.split(' ', 2)[2]).replace('\\n', '\n')
            if (replytweetauthor not in viesti) and (replytweetauthor != '@'+user):
                viesti = replytweetauthor + ' ' + viesti
        except IndexError:
            if replytweetauthor != '@'+user:
                viesti = replytweetauthor
            else:
                viesti = None
        if viesti != None:
            if caseInsensitiveComparison(viesti, blacklist):
                return "NOMSG"
        filename = "temp" + get_extension(imageurl)
        request = requests.get(imageurl, stream=True)
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)
        api.update_with_media(filename, status=viesti, in_reply_to_status_id=replytweetid)
        os.remove(filename)
        url = 'http://twitter.com/statuses/%s' % api.user_timeline(id=user)[0].id
        print("Twiitattu: %s" % (url))
        return url


    def checkReplies(self):
        """LooppingCalliin työnnettävä funktio joka lukee replies.txt
           ja syöttää tiedoston uudet rivit irc-kanavalle. Lopuksi 
           tyhjentää tiedoston."""
        f = open("replies.txt", "r+")
        replies = f.readlines()
        if replies == []:
            return
        else:
            for line in replies:
                for channel in self.factory.channels:
                    self._sendMessage(msg=line, target=channel)
            f.seek(0)
            f.truncate()
            f.close()

class IRCFactory(protocol.ReconnectingClientFactory):
    protocol = IRCProtocol
    channels = config.get('IRC','Channels').split(',')
    def clientConnectionLost(self, connector, reason):
        print("IRC-yhteys katkesi: %s" % (reason))
        print("Yritetään yhdistää uusiksi.")
        self.retry(connector)
    def clientConnectionFailed(self, connector, reason):
        print("Ei saatu yhteyttä IRC-serveriin: %s" % (reason))
        print("Yritetään yhdistää uusiksi.")
        self.retry(connector)

class ReplyListener(tweepy.StreamListener, IRCFactory, IRCProtocol):
    """Luokka, joka on vastuussa Twitter-streamin monitoroinnista.
       Täsmäävän twiitin vastaanottaessaan kirjoitetaan rivi replies.txt:iin.
       IRCProtocol-luokassa määritelty funktio startstream() käynnistää streamin.
       TODO: järkevämpi tapa siirtää replyt IRCProtocol-luokkaan kuin tiedostoon kirjoittaminen.""" 
    def __init__(self):
        print("Replyjenseurantastream päällä.")
        super(ReplyListener, self).__init__()
        if not os.path.exists("replies.txt"):
            open('replies.txt', 'w').close() 
            print("Luotiin replies.txt.")

    def on_status(self, tweet):
        message = tweet.text.replace("\n", " ").encode("utf-8")
        author = tweet.author.screen_name.encode("utf-8")
        tweetid = str(tweet.id).encode("utf-8")
        print("Uusi reply: < %s> %s http://twitter.com/statuses/%s" % (author, message, tweetid))
        f = open("replies.txt", "a")
        f.write("< %s> %s http://twitter.com/statuses/%s\n" % (author, message, tweetid))

    def on_error(self, status):
        print("Virhe streamissa: %s" % (status))
        if status == 420: # 420 tarkoittaa että API käskee painua vittuun, parempi totella
            print("Otetaan stream pois päältä.")
            return False
        else:
            print("Yritetään uudestaan minuutin päästä.")
            time.sleep(60)
            return True

def main(reactor, description):
    endpoint = endpoints.clientFromString(reactor, description)
    factory = IRCFactory()
    d = endpoint.connect(factory)
    d.addCallback(lambda protocol: protocol.deferred)
    return d

if __name__ == '__main__':
    log.startLogging(sys.stderr)
    consumer_key =  config.get('Twitter','ConsumerKey')
    consumer_secret = config.get('Twitter','ConsumerSecret') 
    access_token = config.get('Twitter','AccessToken')
    access_token_secret = config.get('Twitter','AccessTokenSecret')
    blacklist = config.get('BotOptions','BlacklistedWords').split(',')
    if blacklist == ['none']:
        blacklist = []
    user = config.get('Twitter','User')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    server = config.get('IRC','Server')
    port = config.get('IRC','Port')
    if config.getboolean('IRC','UseSSL'):
        serverargument = ['ssl:'+server+':'+port]
    else:
        serverargument = ['tcp:'+server+':'+port]
    task.react(main, serverargument)
