from pytubefix import YouTube
from pytubefix.cli import on_progress


video_file = 'https://www.youtube.com/watch?v=ZSYLxi5JhVI'


yt = YouTube(video_file, 
             on_progress_callback=on_progress)



audio = yt.streams.filter(only_audio=True).first()


if audio:
    print('Downloading Audio...')
    audio.download(filename=f'{yt.title}_audio.mp4')
else:
    pass