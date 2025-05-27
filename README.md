This project automatically tests availabilty of all mqtt messages in a trace published from message player.

List of mqtt topics & messages is given in input JSON file.

JSON input files should be located in folder `input_json_files`.

Message Player starts to publish different mqtt messaged after it receives message with topic `signalPlayer/start`.
Message Tester subscribes to topics given in json file and checks if mqtt messages appear.

As soon as, at least one valid payload was read out, the respective topic is recognized as tested.
Ideally, all topics from input json file should occur at least once during the respective trace run.

The test result is written to the csv file in folder `output_csv_file` and contains status OK/NOK for each topic.
Stats OK means the topic with valid payload was found during test. 

Additionally there is a coverage statistics for the test and information which topics from the json file were not found during the test.


# Deployment in Docker:

1. build docker images for `message_player` and `message_tester`
   cd ./src/message_player
   bash build_image.sh

   cd ./src/message_tester
   bash build_image.sh

2. run docker compose:
   bash deploy.sh
