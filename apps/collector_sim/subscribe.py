import os, json
from paho.mqtt.client import Client, CallbackAPIVersion

MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")  # force localhost
TOPIC = "sensors/#"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except Exception:
        data = msg.payload.decode(errors="ignore")
    print(f"[{msg.topic}] {data}")

client = Client(CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(MQTT_HOST, 1883, 60)
client.subscribe(TOPIC, qos=1)
print(f"Subscribed to {TOPIC} on {MQTT_HOST}")
client.loop_forever()
