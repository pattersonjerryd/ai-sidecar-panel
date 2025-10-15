# apps/collector_sim/publisher.py

import os
import time
import json
import random
import paho.mqtt.client as mqtt

# --- Settings ---------------------------------------------------------------
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC = "sensors/wetvac-1"
PUBLISH_INTERVAL_SEC = 2
# ---------------------------------------------------------------------------

def on_connect(client, userdata, flags, reason_code, properties=None):
    # reason_code 0 == success
    print(f"[publisher] connected rc={reason_code} to {MQTT_HOST}:{MQTT_PORT}")

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.enable_logger()  # optional: prints reconnects/timeouts

    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()

    try:
        while True:
            payload = {
                "device_id": "wetvac-1",
                "site": "TampaDental",
                "metric": "water_flow_lpm",
                "value": round(random.uniform(0, 25), 2),
                "status": "ok",
                "ts": time.time(),
            }

            # occasional “leak” spike
            if random.random() < 0.07:
                payload["value"] = round(random.uniform(60, 120), 2)
                payload["status"] = "anomaly"

            info = client.publish(TOPIC, json.dumps(payload), qos=1)
            info.wait_for_publish()  # wait for QoS1 ack so we know it sent

            print(f"[publisher] sent → {TOPIC} value={payload['value']} status={payload['status']}")
            time.sleep(PUBLISH_INTERVAL_SEC)
    except KeyboardInterrupt:
        print("\n[publisher] stopping…")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()
