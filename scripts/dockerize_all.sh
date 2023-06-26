cd ./analysis_module
echo "Building analysis_module"
docker buildx build -t analysis_module .

cd ../expression_processor
echo "Building expression_processor"
docker buildx build -t expression_processor .

cd ../heartrate_processor
echo "Building heartrate_processor"
docker buildx build -t heartrate_processor .

cd ../linkedin_scraping
echo "Building linkedin_scraping"
docker buildx build -t linkedin_scraping .

cd ../robot_controller
echo "Building robot_controller"
docker buildx build -t robot_controller .