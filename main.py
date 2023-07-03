# STEP 1 - Loop through all the files in this dir that are MKVs
# STEP 1a - Get audio details
# STEP 1b - Create folder structure
# STEP 1c - Split audio from video
# STEP 1d - Wait for user to correct the audio TODO: automate?
# STEP 1e - Add corrected audio back into temp video
# STEP 2 - Analyse the VOICE audio and find everywhere silence is detected
# STEP 3 - Split the MKV video, M4A VOICE audio & M4A GAME audio based on the silence detected
# STEP 4 - Convert all MKV's exported to MOV
# STEP 5 - Clear up temp files

from pydub import AudioSegment
from pydub.silence import split_on_silence
import os
from os.path import exists
import shutil
from datetime import datetime, timedelta
import subprocess

# variables
filesToSkip = []
path = "./files_to_process"
filepath_index = 1

foundFiles = []
hasStudioVersion = True


class FileData:
	file_name = ""
	file_name_no_extension = ""
	base_conversion_path = ""
	game_audio_export_path = ""
	voice_audio_export_path = ""
	conversion_path = ""
	conversion_temp_path = ""
	split_voice_audio_path = ""
	split_game_audio_path = ""
	split_video_path = ""


# create the folder structure so all output folders / files exist
def setup_folder_structure(file_detail):
	# create dir for exported assets
	if not os.path.exists(file_detail.conversion_path):
		os.makedirs(file_detail.conversion_path)

	# create dir for exported audio assets
	if not os.path.exists(file_detail.conversion_temp_path):
		os.makedirs(file_detail.conversion_temp_path)

	# create dir for split voice audio assets
	if not os.path.exists(file_detail.split_voice_audio_path):
		os.makedirs(file_detail.split_voice_audio_path)

	# create dir for split game audio assets
	if not os.path.exists(file_detail.split_game_audio_path):
		os.makedirs(file_detail.split_game_audio_path)

	# create dir for split video assets
	if not os.path.exists(file_detail.split_video_path):
		os.makedirs(file_detail.split_video_path)


# take the video then split based on the parameters
def split_video_by_time(video_file, start_time, end_time, index, recompile, conversion_temp_path):

	if recompile:
		command = f"ffmpeg -i {video_file} -loglevel quiet -map 0:v:0 -map 0:a:0 -map 0:a:1 -ss {start_time} -to {end_time} {conversion_temp_path}"
	else:
		command = f"ffmpeg -i {video_file} -loglevel quiet -c copy -map 0:v:0 -map 0:a:0 -map 0:a:1 -ss {start_time} -to {end_time} {conversion_temp_path}"

	run_command(command, 2)


# if studio version, use MKV otherwise use MOV
def get_file_type():
	if hasStudioVersion:
		return ".mkv"
	else:
		return ".mov"


# run a system command returning time taken
def run_command(command, dash_indent_amount):
	indent = ""

	for i in range(dash_indent_amount):
		indent += f" -"

	# output
	print(f"{indent} Running command: {command}")

	# Split all the audio out
	os.system(command)


# loop through all found files, store data, export audio, wait for modifications, repeat until done
def get_audio_files():
	global foundFiles
	global path

	files = [f for f in os.listdir(path) if f.endswith(".mkv")]

	# loop through all files in this location and set the sounds up
	for fileName in files:

		if fileName in filesToSkip:
			continue

		# output log
		print(f" - Step 1a - Working on file {filepath_index}/{len(files)} - {fileName}")

		# create class for later use
		fileDetails = FileData()
		fileDetails.file_name = fileName
		fileDetails.file_name_no_extension = fileDetails.file_name.replace(".mkv", "")

		# conversion details
		fileDetails.conversion_path = f"{path}/exported/{fileDetails.file_name_no_extension}"
		fileDetails.conversion_temp_path = f"{fileDetails.conversion_path}/temp"

		# audio details
		fileDetails.game_audio_export_path = f"{fileDetails.conversion_temp_path}/{fileDetails.file_name_no_extension}_GameAudio"
		fileDetails.voice_audio_export_path = f"{fileDetails.conversion_temp_path}/{fileDetails.file_name_no_extension}_VoiceAudio"

		# split paths details
		fileDetails.split_voice_audio_path = f"{fileDetails.conversion_path}/"
		fileDetails.split_game_audio_path = f"{fileDetails.conversion_path}/"
		fileDetails.split_video_path = f"{fileDetails.conversion_path}/"

		# save
		foundFiles.append(fileDetails)

		# STEP 1b - call folder setup to create all folders
		print(f" - Step 1b - Create folder structure for {fileDetails.file_name}")
		setup_folder_structure(fileDetails)

		# build up command
		if exists(f"{fileDetails.voice_audio_export_path}.wav"):
			print(f" - Audio already split. Skipping...")
		else:
			print(f" - Step 1c: Splitting audio")
			splitAudioCommand = f"ffmpeg -i {path}/{fileDetails.file_name} -loglevel quiet -map 0:2 -c copy {fileDetails.game_audio_export_path}.aac -map 0:3 -c copy {fileDetails.voice_audio_export_path}.aac"
			run_command(splitAudioCommand, 1)

			# convert VOICE aac to wav
			voice_audio_convert_command = f"ffmpeg -i {fileDetails.voice_audio_export_path}.aac -loglevel quiet -c copy {fileDetails.voice_audio_export_path}.wav"
			run_command(voice_audio_convert_command, 1)

			# Delete old VOICE aac file
			os.remove(f"{fileDetails.voice_audio_export_path}.aac")

			# convert GAME aac to wav
			game_audio_convert_command = f"ffmpeg -i {fileDetails.game_audio_export_path}.aac -loglevel quiet -c copy {fileDetails.game_audio_export_path}.wav"
			run_command(game_audio_convert_command, 1)

			# Delete old GAME aac file
			os.remove(f"{fileDetails.game_audio_export_path}.aac")

			# let user sort audio
			print(f" - Step 1d - User correcting file")
			input("Now you can modify the audio. Press any key to continue...")

			print(f" - Step 1e - Adding audio back into video")

			audio_add_command = f"ffmpeg -i {path}/{fileDetails.file_name} -i {fileDetails.game_audio_export_path}.wav -i {fileDetails.voice_audio_export_path}.wav -loglevel quiet -vcodec copy -map 0:v:0 -map 1:a -c:a:0 pcm_u8 -map 2:a -c:a:1 pcm_u8 {fileDetails.conversion_temp_path}/{fileDetails.file_name_no_extension}.bak.mkv"
			run_command(audio_add_command, 1)

			print(f" - Audio added successfully")


# take the file, process the audio, split then export each chunk (takes the longest)
def process_all_files(file):
	global filepath_index

	# output log
	print(f" - Working on file {filepath_index}/{len(foundFiles)} - {file.file_name}")

	# load the audio into memory
	print(f" - Loading audio into memory")
	voice_audio = AudioSegment.from_wav(f"{file.voice_audio_export_path}.wav")

	# STEP 5 - split voice audio where the silence is 300ms or more and get chunks of audio
	print(f" - Step 2: Split voice on silence")
	chunks = split_on_silence(
		# Use the loaded audio.
		voice_audio,
		# Specify that a silent chunk must be at least
		min_silence_len=50,

		# treat 'silence' as -65 dBFS
		silence_thresh=-65,

		# keep the silence?
		keep_silence=True
	)

	# store the ms of the chunk
	chunk_start_time = timedelta(seconds=0)

	# loop over each chunk of audio
	for chunk_index, audio_chunk in enumerate(chunks):
		indexStr = str(chunk_index + 1).zfill(4)  # setup index naming convention minimum 2 characters (01, 10, 100)
		audio_chunk_sequence = audio_chunk[0]  # get the audio chunk
		audio_chunk_type = audio_chunk[1]  # get the type of audio
		temp_name = f"OLD_video_{indexStr}.mkv"  # get the temp video name
		final_video = f"{file.split_video_path}{file.file_name_no_extension}_{indexStr}_{audio_chunk_type}{get_file_type()}"  # the final output name
		audioMS = len(audio_chunk_sequence)  # get milliseconds
		# get how long the chunk is and store the duration in seconds
		endTime = chunk_start_time + timedelta(milliseconds=audioMS)
		skip_video_generation = False  # do we need to skip splitting the video
		recompileVideo = False  # false = fast but can fail, true = slow but will 100% succeed

		print(f" - - - - - - - - - - - - - - - - - - - - - - - - - - - ")
		print(f" - - {chunk_index + 1}/{len(chunks)} - {indexStr} - {audioMS}ms")

		# if the chunk is silence and the length < 300ms, or voice type and < 100ms then skip
		if (audio_chunk_type == "silence" and audioMS < 1500) or (audio_chunk_type == "voice" and audioMS < 200):
			print(f" - - video ms {audioMS}, type {audio_chunk_type} too short, skipping...")

			# remove video if it exists already
			if exists(final_video):
				print(f" - - deleting video...")
				os.remove(final_video)

			skip_video_generation = True

		# does the video already exist - check validity
		if not skip_video_generation and exists(final_video):
			print(f" - - video already exists")
			print(f" - - valid video check 1/2 ...")

			# check if the output has a video file or if its failed
			result = subprocess.run(['ffprobe', '-loglevel', 'error', '-select_streams', 'v', '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', f"{final_video}"], stdout=subprocess.PIPE)
			recompileVideo = result.stdout != b'video\n'

			if recompileVideo:
				print(" - - Video error - corrupt video. Recompiling...")

			# if it's not failed
			if not recompileVideo:
				print(" - - valid video check 2/2...")

				# check 2 - check if the video contains freezes
				result = subprocess.run(['ffmpeg', '-i', f"{final_video}", '-vf', 'freezedetect=n=-120dB:d=1', '-map', '0:v:0', '-f', 'null', '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
				lines = ""
				for line in result.stdout:
					lines = lines + line

				if "freezedetect" in lines:
					recompileVideo = True
					print(lines)
					print(" - - Video error - freeze detected. Recompiling...")

			# if true, the video failed and needs recompiling
			if recompileVideo:
				print(f" - - video needs recompiling, deleting video...")
				os.remove(final_video)
				skip_video_generation = False
			else:
				print(f" - - video is fine, skipping...")
				skip_video_generation = True

		if not skip_video_generation:
			output_location = f"{file.conversion_temp_path}/{temp_name}"

			# STEP 3 - output log
			print(f" - - Step 3: Chunk {chunk_index + 1}/{len(chunks)} for {file.file_name} - start time: {chunk_start_time}; end time {endTime}")
			split_video_by_time(f"{file.conversion_temp_path}/{file.file_name_no_extension}.bak.mkv", chunk_start_time, endTime, indexStr, recompileVideo, f"{output_location}")  # convert time to ms

			# STEP 4 - convert MKV's to MOV
			print(f" - - Step 4: Converting split video chunk to MOV")
			split_video_command = f"ffmpeg -i {file.conversion_temp_path}/{temp_name} -loglevel quiet -map 0 -vcodec dnxhd -acodec pcm_s16le -s 1920x1080 -r 30000/1001 -b:v 36M -pix_fmt yuv422p -f mov {final_video}"
			run_command(split_video_command, 2)

			# remove split file after conversion
			if exists(f"{file.conversion_temp_path}/{temp_name}"):
				os.remove(f"{file.conversion_temp_path}/{temp_name}")

		# set the new start time to the previous end time
		chunk_start_time = endTime

	# increment index
	filepath_index = filepath_index + 1

	# STEP 9 - Clear audio files from above
	# shutil.rmtree(conversion_temp_path)
	print(" - Step 5 - clear audio files")


# begin the application
def main():
	global foundFiles

	# STEP 1 - loop over all locations in this dir
	print("Step 1: Looping through all files and export audio")
	get_audio_files()

	print("Step 2: All audio gathered, beginning splitting...")
	# loop through all files and start parsing audio
	for file_item in foundFiles:
		process_all_files(file_item)


if __name__ == '__main__':
	main()
# os.system("shutdown -h 10")
