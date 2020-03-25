import pychromecast
import sys

mediaUrl = sys.argv[1]
mediaType = "audio/mp3"
oogleHomeAddress="192.168.43.167"

googleHome = pychromecast.Chromecast(googleHomeAddress)
googleHome.wait()
googleHome.media_controller.play_media(mediaUrl+"?text="+text+"&lang="+lang,mediaType)
googleHome.media_controller.block_until_active()
