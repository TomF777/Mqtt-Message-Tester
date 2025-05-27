"""
This script automatically tests availabilty of all mqtt messages in a trace from message player.
List of mqtt topics & messages is given in input JSON file.
JSON input files should be located in folder `input_json_files`.
"""
import csv
import time
import json
from enum import Enum
import settings
from mqtt_client import MqttClient

# specify in `.env` the trace number to test.
# This constant defines name for input json file (trace-01.json)
# and output result file (test-result-trace-01.csv)
TRACE_NAME = settings.TRACE_NAME

TOPIC_PLAYER_START = "signalPlayer/start"
TOPIC_PLAYER_STOP = "signalPlayer/stop"


class SimpleTimer:
    """
    implement a simple timer with polling.
    set timeout in second
    """
    def __init__(self, timeout):
        assert timeout > 0.0
        self.timeout = timeout
        self.start_timer = time.time()

    def is_time_elapsed(self):
        """
        Return True if timeout is reached, False otherwise.
        """
        diff_time = time.time() - self.start_timer
        return diff_time >= self.timeout

    def is_time_remaining(self):
        """
        Return True if timeout is not reached, False otherwise.
        """
        return not self.is_time_elapsed()

class SequenceStatus(Enum):
    """ Enum for test sequencer status """
    IDLE = 0
    TEST_STARTED = 1
    TEST_RUNNING = 2
    TEST_STOPPED = 3
    UNKNOWN = 4
    default = IDLE

class MessageTestApp:
    """ 
    Class for test of all mqtt topics in a trace, 
    where list of topics is given in an input JSON file
    """
    def __init__(self):

        # allow subscription to mqtt topics
        self.__allow_mqtt_topic = True

        # received mqtt message counter
        self.__mqtt_message_counter = 0

        # topic lists read out from input json file
        self._mqtt_topics = []

        # list with found mqtt topics
        self._mqtt_topics_tested = []

        self._subscription_list = []

        self._test_started = False

        # init mqtt client
        while True:
            try:
                settings.LOGGER.info("Connecting to MQTT broker...")
                self.mqtt_client = MqttClient("IoT_signal_tester",
                                            broker=settings.MQTT_HOST,
                                            port=settings.MQTT_PORT)
            except Exception as err:
                settings.LOGGER.info("Connection to MQTT broker failed: %s", err)
            else:
                break


    def user_callback(self, client, userdata, message):
        """Userlevel callback class.
        Args:
            client: mqtt client instance
            userdata: user defined data of any type
            message: received mqtt message
        """

        if message.topic in self._mqtt_topics and self.__allow_mqtt_topic is True:
            self.__handle_mqtt_topic(message.topic,json.loads(message.payload))
        else:
            # topic not allowed in MessageTestApp
            if not (self.__allow_mqtt_topic is False and topic in self._mqtt_topics):
                settings.LOGGER.info("Received unhandled topic %s", message.topic)


    def __handle_mqtt_topic(self, topic, json_payload):
        """Extract desired values from mqtt message and logger output

        Args:
            topic (str): Topic name
            json_payload (dict): json mqtt payload
        Returns:
        """

        if self._test_started is True:
            self.__mqtt_message_counter += 1
            # check if topic already appeared before
            if topic not in self._mqtt_topics_tested:
                # field in payload should exist
                if len(json_payload[0]["schema"]) > 0:
                    self._mqtt_topics_tested.append(topic)
                    settings.LOGGER.info("New MQTT topic received : \
                                            %s MQTT | payload: %s",
                                         topic,
                                         json_payload[0]["schema"],
                                         )


    def create_test_report(self):
        """ 
        Create final test report with statistics 
        how many topics were found during whole trace run
        """
        if len(self._mqtt_topics_tested) > 0:

            topics_not_found = []

            settings.LOGGER.info("=" * 40)
            settings.LOGGER.info("*" * 10 + " Creating Report " + "*" * 10)
            settings.LOGGER.info("=" * 40)

            settings.LOGGER.info(" Number of MQTT topics found: %s \n \
                                 Total number of MQTT topics in JSON file %s",
                                 len(self._mqtt_topics_tested),
                                 len(self._mqtt_topics))

            settings.LOGGER.info(" Test coverage: %s %%",
                                 round((100.0 *
                                        len(self._mqtt_topics_tested)
                                        /
                                        len(self._mqtt_topics)),1))

            with open("output_csv_files/test-result-"
                      + TRACE_NAME +
                      ".csv", "w", newline = '') as result_file:
                header = ['topic', 'payload_type', 'status']
                writer = csv.DictWriter(result_file, fieldnames = header)
                writer.writeheader()

                # iterate all MQTT topics and
                # check if topic exists in list with found topics
                for topic in range(0, len(self._mqtt_topics)):
                    if self._mqtt_topics[topic] in self._mqtt_topics_tested:
                        topic_status = 'OK'
                    else:
                        topic_status = 'NOK'
                        topics_not_found.append(self._mqtt_topics[topic])

                    writer.writerow({'topic':self._mqtt_topics[topic],
                                     'payload_type':'json',
                                     'status': topic_status })

                result_file.write("\n\nNumber of MQTT topics found: {} \
                                  || Total number of MQTT topics in JSON file {}".
                                    format(
                                 len(self._mqtt_topics_tested),
                                 len(self._mqtt_topics))
                                    )

                result_file.write("\nTest coverage: {} %".format(
                                  round((100.0 * len(self._mqtt_topics_tested)
                                         /
                                         len(self._mqtt_topics)),1)))
                result_file.write("\n\nTopics which were not found: \n")
                for topic in topics_not_found:
                    result_file.write(str(topic) + " \n")


    def start_test(self, trace_no, speed):
        """ Send json command to trace player to start it with proper settings

            Args:
            trace_no (str): trace number to be run during test
            speed (float): speed which the trace will run

            Returns:
          """

        settings.LOGGER.info("=" * 40)
        settings.LOGGER.info("*" *  14 + " Start Test " + "*" * 14)
        settings.LOGGER.info("=" * 40)

        settings.LOGGER.info(" ******** Testing trace: %s ******** ",
                             settings.TRACE_NAME)
        time.sleep(1)

        self._test_started = True
        self.__allow_mqtt_topic = True

        # reinit data for test
        self._mqtt_topics_tested.clear()
        self.__mqtt_message_counter = 0

        # create json command to send to trace player
        json_send_cmd = {"trace_name":trace_no, "speed":speed}

        self.mqtt_client.start()
        self.mqtt_client.publish_message(topic=TOPIC_PLAYER_START, json=json.dumps(json_send_cmd))
        time.sleep(0.2)

        settings.LOGGER.info("*" * 14 + " Trace Player Started " + "*" * 14)


    def stop_test(self):
        """ 
        Send json command to trace player to stop it 
        """

        settings.LOGGER.info("*" * 20)
        settings.LOGGER.info(" Test Completed ")
        settings.LOGGER.info("*" * 20)

        self._test_started = False
        self.__allow_mqtt_topic = False

        json_send_cmd = ''

        self.mqtt_client.start()
        self.mqtt_client.publish_message(topic=TOPIC_PLAYER_START, json=json_send_cmd)
        time.sleep(1)

        settings.LOGGER.info(" Trace Player Stopped ")


    def get_player_status(self):
        """ Get player status of current running trace

        Args:

        Returns:
                trace_status: playing/stopped or None
                trace_time_remained: time in [sec.] left 
                                to the end of current running trace
        """

        self.mqtt_client.start()
        self.mqtt_client.subscribe("signalPlayer/status")
        self.mqtt_client.read_message()


        if self.mqtt_client.read_payload is not None \
            and self.mqtt_client.read_topic == 'signalPlayer/status':
            trace_status = json.loads(self.mqtt_client.read_payload.decode('utf-8'))["status"]
            trace_length_in_sec = json.loads(self.mqtt_client.read_payload.decode('utf-8'))["trace_length"]
            trace_time_elapsed = json.loads(self.mqtt_client.read_payload.decode('utf-8'))["time_elapsed"]
            trace_time_remained = trace_length_in_sec - trace_time_elapsed
            return trace_status, trace_time_remained, trace_time_elapsed

        else:
            settings.LOGGER.info(" No response from Player Status received ")

        return None, None, None


if __name__ == "__main__":
    signal_tester = MessageTestApp()

    # read input config file with topics
    try:
        with open("./input_json_files/input_file_" + TRACE_NAME + ".json", "r") as data_file:
            data = json.load(data_file)

        # get number of topics in json file
        topic_size = len(data['trace'][0]['topics'])
        settings.LOGGER.info(f"Number of topics in JSON: {topic_size}")

        for topic_number in range(0, topic_size):
            # populate list with mqtt topics
            if data['trace'][0]['topics'][topic_number]['topic'][0:4] == "mqtt":
                signal_tester._mqtt_topics.append(data['trace'][0]['topics'][topic_number]['topic'])

    except (FileNotFoundError, IOError):
        settings.LOGGER.info("Wrong JSON file name of file doesn't exist")


    registered_mqtt_topics = []

    # Subscribe to all mqtt topics from json file
    if len(signal_tester._mqtt_topics) > 0:
        for topic in range(0, len(signal_tester._mqtt_topics)):
            signal_tester.mqtt_client.client.subscribe(signal_tester._mqtt_topics[topic],
                                                       qos=settings.MQTT_QOS)
            signal_tester.mqtt_client.client.message_callback_add(
                        signal_tester._mqtt_topics[topic], signal_tester.user_callback)

            settings.LOGGER.info("Subscription of %s added",
                                 signal_tester._mqtt_topics[topic])
    signal_tester.mqtt_client.start()

    # Start the program procedure
    seq_status = SequenceStatus(0)
    last_seq_status = SequenceStatus.TEST_STOPPED

    # Start the test procedure
    try:
        while True:
            # test sequence
            match seq_status:
                case SequenceStatus.IDLE:

                    if last_seq_status == SequenceStatus.TEST_STOPPED:
                        last_seq_status = SequenceStatus.UNKNOWN
                        time.sleep(1)
                        settings.LOGGER.info("=" * 55)
                        settings.LOGGER.info("#" * 14 + \
                                             " Waiting to start the test " + \
                                             "#" * 14)
                        settings.LOGGER.info("=" * 55)
                        time.sleep(2)
                    if len(signal_tester._mqtt_topics) > 0:
                        seq_status = SequenceStatus.TEST_STARTED

                case SequenceStatus.TEST_STARTED:
                    timer = SimpleTimer(1.0)
                    seq_status = SequenceStatus.TEST_RUNNING
                    time.sleep(2)
                    signal_tester.start_test(trace_no=TRACE_NAME, speed=1.0)

                case SequenceStatus.TEST_RUNNING:
                    # check every 1 sec if trace end reached
                    if timer.is_time_elapsed():
                        trace_status, \
                        trace_time_remained, \
                        trace_time_elapsed = signal_tester.get_player_status()

                        if trace_status is not None and \
                            trace_time_remained is not None and \
                            trace_time_elapsed is not None:
                            settings.LOGGER.info("\nTrace status: %s, \
                                                \n time remained: %s sec. \
                                                \n time elapsed: %s sec.",
                                                trace_status,
                                                round(trace_time_remained,1),
                                                round(trace_time_elapsed, 1))
                        if trace_status is not None and trace_time_remained < 1.0:
                            signal_tester.stop_test()
                            seq_status = SequenceStatus.TEST_STOPPED

                        # reinit timer
                        timer = SimpleTimer(1.0)

                case SequenceStatus.TEST_STOPPED:
                    last_seq_status = SequenceStatus.TEST_STOPPED
                    signal_tester.create_test_report()
                    signal_tester.mqtt_client.close()
                    break

    except Exception as ex:
        settings.LOGGER.error(ex)
        raise ex
