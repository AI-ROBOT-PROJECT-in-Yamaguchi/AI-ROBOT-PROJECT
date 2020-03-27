import pychromecast
import sys
from ghconfig import *

mediaUrl = sys.argv[1]

googleHome = pychromecast.Chromecast(googleHomeAddress)
googleHome.wait()
googleHome.media_controller.play_media(mediaUrl+"?text="+text+"&lang="+lang,mediaType)
googleHome.media_controller.block_until_active()
