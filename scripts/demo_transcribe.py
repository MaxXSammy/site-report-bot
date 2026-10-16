import sys

from site_report_bot.transcription import transcribe

print(transcribe(sys.argv[1]))
