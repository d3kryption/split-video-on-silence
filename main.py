# STEP 1 - Loop through all the files in this dir that are MKVs
# STEP 2 - Create folder structure
# STEP 3 - Rip audio (voice, game) from video
# STEP 4 - Convert AAC to WAV
# STEP 5 - Analyse the VOICE audio and find everywhere silence is detected
# STEP 6 - Split the MKV video, M4A VOICE audio & M4A GAME audio based on the silence detected
# STEP 7 - Convert all MKV's exported to MOV
# STEP 8 - Normalise all M4A VOICE and M4A GAME audio to wav
# STEP 9 - Clear up temp files

from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
from os import walk
import shutil
from datetime import datetime, timedelta

# variables
path = "./files_to_process"
filepath_index = 1

# conversion paths
base_conversion_path = f""
conversion_path = f"{path}/exported/{base_conversion_path}"
conversion_temp_path = f"{conversion_path}/temp/"

# split paths
split_voice_audio_path = f"{conversion_path}/"
split_game_audio_path = f"{conversion_path}/"
split_video_path = f"{conversion_path}/"


# create the folder structure so all output folders / files exist
def setup_folder_structure():
	global conversion_path
	global conversion_temp_path
	global split_voice_audio_path
	global split_game_audio_path
	global split_video_path

	print("Step 1: Setting up file structure")
	conversion_path = f"{path}/exported/{base_conversion_path}"
	conversion_temp_path = f"{conversion_path}/temp"

	# split paths
	split_voice_audio_path = f"{conversion_path}/"
	split_game_audio_path = f"{conversion_path}/"
	split_video_path = f"{conversion_path}/"

	# create dir for exported assets
	if not os.path.exists(conversion_path):
		os.makedirs(conversion_path)

	# create dir for exported audio assets
	if not os.path.exists(conversion_temp_path):
		os.makedirs(conversion_temp_path)

	# create dir for split voice audio assets
	if not os.path.exists(split_voice_audio_path):
		os.makedirs(split_voice_audio_path)

	# create dir for split game audio assets
	if not os.path.exists(split_game_audio_path):
		os.makedirs(split_game_audio_path)

	# create dir for split video assets
	if not os.path.exists(split_video_path):
		os.makedirs(split_video_path)


# take the video then split based on the parameters
def split_video_by_time(video_file, start_time, end_time, index):
	video_name = f"OLD_video_{index}.mov"

	command = f"ffmpeg -i {video_file} -loglevel quiet -map 0:v:0 -map 0:a:0 -map 0:a:1 -ss {start_time} -to {end_time} {conversion_temp_path}/{video_name}"
	run_command(command, 2)

	return video_name


# run a system command returning time taken
def run_command(command, dash_indent_amount):
	indent = ""

	for i in range(dash_indent_amount):
		indent += f" -"

	# output
	print(f"{indent} Running command: {command}")

	# Split all the audio out
	os.system(command)


# format time to seconds, minutes, hours...
def format_time(time):
	rounded_time = round(time, 2)

	if rounded_time < 60:
		return f"{rounded_time} seconds"
	elif rounded_time < 3600:
		return f"{rounded_time / 60} minutes"
	else:
		return f"{(rounded_time / 60) / 60} hours"


# STEP 1 - loop over all locations in this dir
print("Step 1: Looping through all files")

for (dirPath, dirNames, fileNames) in walk(path):

	# loop through all files in this location
	for fileName in fileNames:

		# if file ends with mkv (raw files)
		if fileName.endswith(".mkv"):

			# output log
			print(f" - Working on file {filepath_index}/{len(fileNames)} - {fileName}")

			# remove the extension so we have a pure file name
			file_name = fileName
			file_name_no_extension = file_name.replace(".mkv", "")

			# set paths
			base_conversion_path = file_name_no_extension

			# STEP 2 - call folder setup to create all folders
			setup_folder_structure()

			# STEP 3 - Rip audio (voice, game) from video
			game_audio_export_path = f"{conversion_temp_path}/{file_name_no_extension}_GameAudio"
			voice_audio_export_path = f"{conversion_temp_path}/{file_name_no_extension}_VoiceAudio"

			# build up command
			print(f" - Step 3: Splitting audio")
			splitAudioCommand = f"ffmpeg -i {path}/{file_name} -loglevel quiet -map 0:2 -c copy {game_audio_export_path}.aac -map 0:3 -c copy {voice_audio_export_path}.aac"
			run_command(splitAudioCommand, 1)

			# STEP 4 - convert VOICE aac to wav
			print(f" - Step 4: Converting audio to wav")
			voice_audio_convert_command = f"ffmpeg -i {voice_audio_export_path}.aac -loglevel quiet {voice_audio_export_path}.wav"
			run_command(voice_audio_convert_command, 1)

			# Delete old VOICE aac file
			os.remove(f"{voice_audio_export_path}.aac")

			# STEP 4a - convert GAME aac to wav
			game_audio_convert_command = f"ffmpeg -i {game_audio_export_path}.aac -loglevel quiet {game_audio_export_path}.wav"
			run_command(game_audio_convert_command, 1)

			# Delete old GAME aac file
			os.remove(f"{game_audio_export_path}.aac")

			# let user sort audio
			input("Now you can modify the audio. Press any key to continue...")

			# add audio back into video
			file_name_no_extension = f"{file_name_no_extension}"

			audio_add_command = f"ffmpeg -i {path}/{file_name} -i {game_audio_export_path}.wav -i {voice_audio_export_path}.wav -loglevel quiet -c copy -map 0:v:0 -map 0:a:1 -map 0:a:2 {conversion_temp_path}/{file_name_no_extension}.bak.mkv"
			run_command(audio_add_command, 1)

			# load the audio into memory
			print(f" - Loading audio into memory")
			voice_audio = AudioSegment.from_wav(f"{voice_audio_export_path}.wav")

			# STEP 5 - split voice audio where the silence is 300ms or more and get chunks of audio
			print(f" - Step 5: Split voice on silence")
			chunks = split_on_silence(
				# Use the loaded audio.
				voice_audio,
				# Specify that a silent chunk must be at least
				min_silence_len=200,

				# treat 'silence' as -65 dBFS
				silence_thresh=-65,

				# keep the silence?
				keep_silence=True
			)

			# store the ms of the chunk
			chunk_start_time = timedelta(seconds=0)

			# loop over each chunk of audio
			for chunk_index, audio_chunk in enumerate(chunks):
				# setup index naming convention minimum 2 characters (01, 10, 100)
				indexStr = str(chunk_index + 1).zfill(4)
				audio_chunk_sequence = audio_chunk[0]
				audio_chunk_type = audio_chunk[1]

				# get milliseconds
				audioMS = len(audio_chunk_sequence)

				print(f" - - {chunk_index + 1}/{len(chunks)} - {indexStr}")

				# get how long the chunk is and store the duration in seconds
				endTime = chunk_start_time + timedelta(milliseconds=audioMS)

				# STEP 6 - output log
				print(f" - - Step 6: Chunk {chunk_index + 1}/{len(chunks)} for {file_name} - start time: {chunk_start_time}; end time {endTime}")
				split_video_name = split_video_by_time(f"{conversion_temp_path}/{file_name_no_extension}.bak.mkv", chunk_start_time, endTime, indexStr)  # convert time to ms

				# STEP 7 - convert MKV's to MOV
				print(f" - - Step 7: Converting split video chunk to MOV")
				split_video_command = f"ffmpeg -i {conversion_temp_path}/{split_video_name} -loglevel quiet -map 0 -vcodec dnxhd -acodec pcm_s16le -s 1920x1080 -r 30000/1001 -b:v 36M -pix_fmt yuv422p -f mov {split_video_path}{file_name_no_extension}_{indexStr}_{audio_chunk_type}.mov"
				run_command(split_video_command, 2)

				# remove split file after conversion
				os.remove(f"{conversion_temp_path}/{split_video_name}")

				# set the new start time to the previous end time
				chunk_start_time = endTime

			# increment index
			filepath_index = filepath_index + 1

			# STEP 9 - Clear audio files from above
			print(" - Step 9 - clear audio files")
			shutil.rmtree(conversion_temp_path)

# os.system("shutdown -h 10")
