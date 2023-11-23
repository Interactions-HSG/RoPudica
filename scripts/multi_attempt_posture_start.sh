cd ./posture_processor
# source posture/bin/activate

max_iteration=50

for i in $(seq 1 $max_iteration)
do
  python posture.py
  result=$?
  if [[ $result -eq 0 ]]
  then
    echo "Result successful"
    break   
  else
    echo "Result unsuccessful"
    sleep 1
  fi
done

if [[ $result -ne 0 ]]
then
  echo "All of the trials failed!!!"
fi
