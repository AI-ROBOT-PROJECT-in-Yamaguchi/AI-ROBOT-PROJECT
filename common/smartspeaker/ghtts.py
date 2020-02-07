import pychromecast
import sys

googleHomeAddress="192.168.43.167"
lang = sys.argv[1]
text = sys.argv[2]
mediaUrl = "http://9a0ec42c.ngrok.io/output.mp3"
mediaType = "audio/mp3"

googleHome = pychromecast.Chromecast(googleHomeAddress)
googleHome.wait()
googleHome.media_controller.play_media(mediaUrl+"?text="+text+"&lang="+lang,mediaType)
googleHome.media_controller.block_until_active()
