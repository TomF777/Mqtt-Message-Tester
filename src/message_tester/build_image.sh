sudo docker build --build-arg date=$(date -u +'%Y-%m-%dT%H:%M:%SZ') --tag mqtt_message_tester_img:0.0.1 . 
