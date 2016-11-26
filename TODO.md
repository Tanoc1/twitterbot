# Twitterbot TODO
* Mietitään miksei reconnectaus pelaa

* Blacklist-match palauttaa pitkän errorin, mutta ei tunnu aiheuttavan mitään muuta ongelmaa: ongelma johtuu siitä että Twisted odottaa returnista jotain validia stringiä jonka palauttaa kanavalle, mutta itse en halua spämmiä kanavaa millään "blacklisted"-viesteillä, niin olkoon. Katsotaan jos saataisiin palattua funktioista ilman erroria.

* Replyjenseuranta järkevämmäksi (nykyisellään erillinen thread kirjoittaa saadut viestit tiedostoon, josta toinen looppi lukee ne IRC-kanavalle ja tyhjentää tiedoston)

* !ti-komento:

  update_with_media on vanhentunut, korvaa se uudella menetelmällä

  Ladattu tiedosto ei poistu virhetilanteessa

* Mahdollisesti komentojen overhaulaus niin että kaikki tehtäisiin !t-komennon takaa:
  !t -rii tweetid imgur imgur viesti <- reply kahdella kuvalla

* Venaillaan että Tweepyyn koodataan videoiden uppaus

* Botin koodin siistiminen
