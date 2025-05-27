"""
This script simulates signal trace player and sends frequently multiple mqtt messages
with different frequency.
Input data configured in input_file.json file.
For each MQTT message following parameters are defined:

topic: MQTT topic
count: number of messages to be sent during one trace run
result: list of messages to be sent, each message is a JSON object

{
"topic" : "mqtt/DME/Torque_1_KCAN",
"count" : 60,
"result" : [
    { "schema": 
        {"message":"DME",
         "source":"MQTT_TRACE",
         "signals": {"Torque_1_KCAN":{"raw_value":3, "unit":""}}}} ]
}
"""

import time
import math
import json
from statemachine import StateMachine, State
import settings
from mqtt_client import MqttClient


PLAYER_START = "signalPlayer/start"
PLAYER_STOP = "signalPlayer/stop"
PLAYER_STATUS = "signalPlayer/status"


class SignalPlayerState(StateMachine):
    """
    State machine for the signal player.
    """
    # creating states
    stoppedState = State("stopped", initial = True)
    playingState = State("playing")

    # transitions of the state
    play = stoppedState.to(playingState)
    stop = playingState.to(stoppedState)


def read_config_file(file_name:str):
    """ 
    Reads the JSON file and returns the trace data, number of topics, and trace length.
    Args:
        file_name (str): The name of the JSON file containing the trace data.

    Returns:
        trace_data (dict): The trace data from the JSON file.
        topics_amount (int): The number of topics in the trace.
        trace_length (int): The length of the trace in seconds
    """

    try:
        with open(file_name, "r") as data_file:
            trace_data = json.load(data_file)
            # get number of topics in json file
            topics_amount = len(trace_data['trace'][0]['topics'])
            settings.LOGGER.info("Number of topics in JSON: %s", topics_amount)
            # get length in seconds of the trace
            trace_length = trace_data['trace'][0]["traceLengthSeconds"]
            settings.LOGGER.info("Trace length in seconds: %s", trace_length)
            return trace_data, topics_amount, trace_length

    except (FileNotFoundError, IOError):
        settings.LOGGER.info("Wrong JSON file name or file doesn't exist ")
        return None, None, None


if __name__ == '__main__':

    player_state = SignalPlayerState()
    trace_data, topics_amount, trace_length = read_config_file("input_file.json")
    if topics_amount is not None and trace_length is not None:
        # holds publish time intervals for each topic
        topics_publish_times = []

        for topic in range(topics_amount):
            # calculate time interval in seconds
            # how frequently each topic should be published during trace run
            topic_freq = round(
                float(trace_length / trace_data['trace'][0]['topics'][topic]["count"]),
                            1)

            topics_publish_times.append(topic_freq)
        settings.LOGGER.info("Topics publish times: %s", topics_publish_times)
        time.sleep(1)

        while True:
            try:
                settings.LOGGER.info("Connecting to MQTT broker...")
                mqtt_publisher = MqttClient("IoT_signal_player",
                                            settings.MQTT_HOST,
                                            settings.MQTT_PORT,)
            except Exception as err:
                settings.LOGGER.info("Connection to MQTT broker failed: %s", err)
            else:
                break

        mqtt_publisher.subscribe(PLAYER_START)
        mqtt_publisher.subscribe(PLAYER_STOP)
        mqtt_publisher.start()
        count_100ms = 0

        while True:
            time.sleep(0.1)
            settings.LOGGER.info("Waiting for messages...")
            # received message to start the player
            if mqtt_publisher.read_topic == PLAYER_START:
                mqtt_publisher.read_topic = ''
                if str(player_state.current_state) == "stopped":
                    player_state.play()
                # reset counter of 100ms ticks if stopped or playing
                count_100ms = 0

            # received message to stop the player
            elif mqtt_publisher.read_topic == PLAYER_STOP:
                mqtt_publisher.read_topic = ''
                if str(player_state.current_state) == "playing":
                    player_state.stop()

            # publish player status
            payload = {"status": str(player_state.current_state),
                       "time_elapsed": round(count_100ms * 0.1, 1),
                       "trace_length": trace_length}
            mqtt_publisher.publish_message(PLAYER_STATUS, json.dumps(payload))

            if str(player_state.current_state) == "playing":
                # check if count 100ms tick value
                # of respective topic is included in topics_publish_times
                for topic_number in range(topics_amount):
                    if count_100ms > 0 and \
                        math.isclose(
                                    count_100ms*10
                                     %
                                     int(topics_publish_times[topic_number]*10),
                                     0.0):
                        topic = trace_data['trace'][0]['topics'][topic_number]['topic']
                        payload = trace_data['trace'][0]['topics'][topic_number]['result']
                        mqtt_publisher.publish_message(topic, json.dumps(payload))
                        settings.LOGGER.info("Published message to topic: %s \
                                               with payload: %s", topic, payload)
                count_100ms += 1

                # trace completed
                if count_100ms * 0.1 > trace_length :
                    count_100ms = 0
                    settings.LOGGER.info("Trace completed")
