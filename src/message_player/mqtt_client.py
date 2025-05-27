from paho.mqtt import client as mqtt_client
import time
import settings

FIRST_RECONNECT_DELAY = 1
RECONNECT_RATE = 2
MAX_RECONNECT_COUNT = 12
MAX_RECONNECT_DELAY = 60

class MqttClient():
    
    def __init__(self, client_id, broker, port):
        """
        
        """

        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION2, client_id, protocol=mqtt_client.MQTTv5)
        self.client.username_pw_set(settings.MQTT_BROKER_USER, settings.MQTT_BROKER_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port)
        self.read_topic = None
        self.read_payload = None
        print(settings.MQTT_BROKER_USER)
        print(settings.MQTT_BROKER_PASSWORD)
        print(settings.TEST_TRACE)
        
    def on_message(self, client, userdata, message):
        #print(message.topic, "  ", message.payload.decode('utf-8'))
        self.read_payload = message.payload
        self.read_topic = message.topic

    def on_connect(self, mqttc, userdata, flags, rc, props):
        if rc == 0:
            print("Connected to MQTT Broker")
        else:
            print(f"Failed to connect to MQTT Broker, error code: {rc}")
            if rc==1:
                    print("1: Connection refused - incorrect protocol version")
            elif rc==2:
                    print("2: Connection refused - invalid client identifier")
            elif rc==3: 
                    print("3: Connection refused - server unavailable")
            elif rc==4: 
                    print("4: Connection refused - bad username or password")
            elif rc==5: 
                    print("5: Connection refused - not authorised")
        time.sleep(1)

    def on_disconnect(client, userdata, rc):
        print("Disconnected with result code: %s", rc)
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        while reconnect_count < MAX_RECONNECT_COUNT:
            print("Reconnecting in %d seconds...", reconnect_delay)
            time.sleep(reconnect_delay)

            try:
                client.reconnect()
                print("Reconnected successfully!")
                return
            except Exception as err:
                print("%s. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        print("Reconnect failed after %s attempts. Exiting...", reconnect_count)

    def start(self):
        self.client.loop_start()

    def subscribe(self, topic):
        self.client.subscribe(topic)

    def publish_message(self, topic, json):
        self.client.publish(topic, json)
        
    def read_message(self):
        return self.read_topic, self.read_payload
    
    def close(self):
        self.client.loop_stop()
        self.client.disconnect()

