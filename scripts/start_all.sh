echo "Starting all Docker containers"
docker compose up -d

echo "Starting posture processor"
sh ./scripts/multi_attempt_posture_start.sh

echo "Starting pupil processor"
/Applications/Pupil\ Capture.app/Contents/MacOS/pupil_capture # only needed under MacOS
cd ./pupil_processor
source pupil/bin/activate
python3 processor.py
