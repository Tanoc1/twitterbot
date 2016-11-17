Muista config! Avaimet saa apps.twitter.com. UseSSL ja FollowReplies vaativat yes/no-argumentin
Erota kanavat ja mustalistatut sanat toisistaan pilkulla, älä käytä välejä. Jos et halua
mustalistata mitään sanoja, kirjoita BlacklistedWordsin arvoksi none. FollowReplies
määrää, seuraako botti twitteristä saatuja replyjä @botinusername ja postaa ne kanavalle.
TweetCooldown on sekunneissa, ja määrää miten usein kanavalta voidaan lähettää twiittejä.

Asenna python-paketit: tweepy, urlparse, cryptography, requests, ConfigParser, twisted

Replyjä seuraava stream katkeilee?:
https://github.com/tweepy/tweepy/commit/c1eddf1a5788ec4947d3a363dfe165ea599c31fc
