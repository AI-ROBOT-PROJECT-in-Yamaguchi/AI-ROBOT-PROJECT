import pychromecast
import sys
from ghconfig import *

def play(mediaUrl):
    googleHome = pychromecast.Chromecast(googleHomeAddress)
    googleHome.wait()
    googleHome.media_controller.play_media(mediaUrl+"?text="+text+"&lang="+lang,mediaType)
    googleHome.media_controller.block_until_active()

if __name__=="__main__":
    play(sys.argv[1])
