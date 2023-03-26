# Video splitter on silence

This is a small plugin I wrote which uses the `pydub.silence` plugin.

It takes in a video file, splits on the silence but its slightly modified.

This plugin will split the silence away from the track and keep it in a separate file. 

So all video with sound will be kept, and all video without sound will also be kept (files will be named _voice or _silence).

## Why?

I make YouTube videos and I pause a lot when thinking or time-lapsing. 

It's a very repetitive task when editing the video, so I made this plugin to speed that up. 

## 🧐 Features

- Easily adaptable by modifying the code to what you need
- Splits video into chunks of silence and non silence
- Gives you a prompt to edit the audio files before the final output
- Works for DaVinci Resolve free, but all you would have to do is change any conversion lines
- Prints out each step for you to follow in-case of debugging

## 🫥 Limitations
- Since DaVinci Resolve free only has limited codecs, you have to convert the video
- Since we are splitting the video into chunks, you have to recompile the video and this takes time.

## 🤔 How it works
1) Loop through all the files in this dir that are MKVs
2) Create folder structure
3) Rip voice audio from video
4) Convert AAC to WAV
5) Wait for user to modify audio
6) Analyse the VOICE audio and find everywhere silence is detected
7) Split the MKV video based on the silence detected
8) Convert all MKV's exported to MOV
9) Clear up temp files

## 🛠️ Installation Steps

This plugin assumes you have a specific video setup. The video can be called anything and be any length (I'm not sure how 2 hour + long videos would cope with limited RAM).

The setup requires you to have an MKV file.

It also requires your video to have 3 audio tracks.

1 - combined voice and background audio
2 - background only audio
3 - voice only audio

These can easily be setup in OBS (or simular) with advanced audio tracks.

1) Download the repo
2) Make sure Python is installed and use the command to install PyDub:
    ```bash
        pip install pydub
    ```
3) Create a folder called `files_to_process` next to main.py.
4) Drop your MKV videos into this folder. As many as you wish.
5) Now you need to modify the plugin to allow it to export silence as well as voiced sections
6) Open up: `./venv/lib/python3.10/site-packages/pydub/silence.py`
7) Modify the function `detect_nonsilent` (around line 100)
8) Change the for loop from:
    ```python
       for start_i, end_i in silent_ranges:
           nonsilent_ranges.append([prev_end_i, start_i])
           prev_end_i = end_i
    ```
   to:
    ```python
       for start_i, end_i in silent_ranges:
           if (len(nonsilent_ranges) > 0):
               nonsilent_ranges.append([prev_end_i, start_i, "voice"])
      
           nonsilent_ranges.append([start_i, end_i, "silence"]) # add in the silences
      
           prev_end_i = end_i
    ```
9) Modify the function `split_on_silence` (around line 116)
10) Change the output_ranges assigning from:
    ```python
    output_ranges = [
        [ start - keep_silence, end + keep_silence ]
        for (start,end)
            in detect_nonsilent(audio_segment, min_silence_len, silence_thresh, seek_step)
    ]
    ```
   to:
    ```python
    output_ranges = [
        [ start - keep_silence, end + keep_silence,audioType ]
        for (start,end,audioType)
            in detect_nonsilent(audio_segment, min_silence_len, silence_thresh, seek_step)
    ]
    ```
11) Then modify the function `split_on_silence` (around line 164)
12) Change the return from:
    ```python
    return [
        [audio_segment[ max(start,0) : min(end,len(audio_segment)) ]]
        for start,end in output_ranges
    ]
    ```
   to:
    ```python
    return [
        [audio_segment[ max(start,0) : min(end,len(audio_segment)) ],audioType]
        for start,end,audioType in output_ranges
    ]
    ```
13) Run main.py via the terminal:
    ```bash
        python main.py
    ```