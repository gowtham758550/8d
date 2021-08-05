import numpy as np
from tqdm import tqdm
from mutagen.mp3 import MP3, MPEGInfo
from mutagen.easyid3 import EasyID3
from pydub import AudioSegment

def tags(info):
    ret = dict()
    try:	
        ret['title'] = info['title'][0]
        ret['album'] = info['album'][0]
        ret['artist'] = info['artist'][0]
        ret['genre'] = info['genre'][0]
    except:
        ret['artist'] = "Unknown"
    return ret


def converter(inputfile, outputfile, period):
    if period < 0:
        period = period*(-1)
    elif period == 0:
        period = 200
    audio = AudioSegment.from_file(inputfile, format='mp3')
    audio = audio + AudioSegment.silent(duration=150)
    fileinfo = MP3(inputfile, ID3=EasyID3)

    eightD = AudioSegment.empty()
    pan = 0.9*np.sin(np.linspace(0, 2*np.pi, period))
    chunks = list(enumerate(audio[::100]))

    for i, chunk in tqdm(chunks, desc='Converting', unit='chunks', total=len(chunks)):
        if len(chunk) < 100:
            continue
        newChunk = chunk.pan(pan[i % period])
        eightD = eightD + newChunk

    eightD.export(outputfile, format='mp3', bitrate=str(fileinfo.info.bitrate_mode/1000), tags=tags(fileinfo))


if __name__ == '__main__':
    inputfile = ""
    outputfile = ""
    period = 200
