# Twitterbot TODO
* Mietitään miksei reconnectaus pelaa

* Replyjenseuranta järkevämmäksi (nykyisellään erillinen thread kirjoittaa saadut viestit tiedostoon, josta toinen looppi lukee ne IRC-kanavalle ja tyhjentää tiedoston)

* !ti-komento:

  update_with_media on vanhentunut, korvaa se uudella menetelmällä

  Ladattu tiedosto ei poistu virhetilanteessa

* Mahdollisesti komentojen overhaulaus niin että kaikki tehtäisiin !t-komennon takaa:
  !t -rii tweetid imgur imgur viesti <- reply kahdella kuvalla

* Venaillaan että Tweepyyn koodataan videoiden uppaus

* Botin koodin siistiminen
