// ESP32 IoT Sensor Firmware for Nepal Cement/Brick Plant
// =========================================================
//
// Hardware:
//   - ESP32-WROOM-32
//   - DHT22 (temperature + humidity)  -- stack gas
//   - MQ-7 (CO sensor)                 -- stack CO
//   - MQ-135 (NOx, CO2)                -- stack NOx/CO2
//   - MAX31855 thermocouple            -- kiln burning zone T
//   - Pressure transducer 4-20 mA      -- kiln pressure
//
// Wiring:
//   DHT22:    VCC=5V, GND, DATA=GPIO4
//   MQ-7:     VCC=5V, GND, AOUT=GPIO34 (ADC)
//   MQ-135:   VCC=5V, GND, AOUT=GPIO35 (ADC)
//   MAX31855: SCK=GPIO18, CS=GPIO5, MISO=GPIO19
//   Pressure: 4-20mA -> 250Ω -> GPIO33 (0-5V -> 0-1.25V)
//
// MQTT topics:
//   nepal/<plant_id>/<kiln_id>/temperature
//   nepal/<plant_id>/<kiln_id>/co
//   nepal/<plant_id>/<kiln_id>/nox
//   nepal/<plant_id>/<kiln_id>/pressure
//
// Author: Nishchal Baniya, Himalayan Carbon Nepal
// License: MIT
// Required libraries:
//   - PubSubClient (MQTT)
//   - DHT sensor library
//   - ArduinoJson
//   - Adafruit MAX31855 (thermocouple)

#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <Adafruit_MAX31855.h>

// ===== Configuration =====
const char* WIFI_SSID     = "your-wifi-ssid";
const char* WIFI_PASSWORD = "your-wifi-pass";
const char* MQTT_BROKER   = "mqtt.example.com";
const int   MQTT_PORT     = 1883;
const char* MQTT_USER     = "plant-sensor";
const char* MQTT_PASS     = "your-mqtt-pass";

const char* PLANT_ID = "planta";
const char* KILN_ID  = "kiln-1";

// Pin definitions
#define DHT_PIN    4
#define DHT_TYPE   DHT22
#define MQ7_PIN    34    // ADC1_CH6
#define MQ135_PIN  35    // ADC1_CH7
#define PRESSURE_PIN 33  // ADC1_CH5
#define THERMO_SCK 18
#define THERMO_CS  5
#define THERMO_MISO 19

// Calibration (from datasheets + plant field data)
#define MQ7_RL      10.0     // Load resistor (kΩ)
#define MQ7_RO      27.5     // Sensor resistance in clean air (kΩ)
#define MQ135_R0    3.6
#define PRESSURE_V_MIN 0.5   // V at 0 Pa (typical transducer)
#define PRESSURE_V_MAX 4.5   // V at max range

// ===== Objects =====
WiFiClient   wifiClient;
PubSubClient mqtt(wifiClient);
DHT          dht(DHT_PIN, DHT_TYPE);
Adafruit_MAX31855 thermocouple(THERMO_SCK, THERMO_CS, THERMO_MISO);

// ===== State =====
unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL = 10_000;  // 10 seconds

// ===== Setup =====
void setup() {
  Serial.begin(115200);
  Serial.println("Nepal Cement IoT Sensor starting...");

  // Init sensors
  dht.begin();

  // WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  int wifi_attempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifi_attempts < 30) {
    delay(1000);
    Serial.print(".");
    wifi_attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected. IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWiFi failed. Running in offline mode.");
  }

  // MQTT
  mqtt.setServer(MQTT_BROKER, MQTT_PORT);
  mqtt.setBufferSize(1024);  // larger for JSON
  connectMQTT();

  Serial.println("Setup complete. Publishing every 10s.");
}

// ===== Main loop =====
void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    if (!mqtt.connected()) {
      connectMQTT();
    }
    mqtt.loop();
  }

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL) {
    lastPublish = now;
    readAndPublish();
  }

  delay(100);
}

// ===== Read sensors and publish =====
void readAndPublish() {
  // 1. Thermocouple (burning zone temperature)
  double T_kiln_C = thermocouple.readCelsius();
  if (!isnan(T_kiln_C)) {
    publishSensor("temperature", T_kiln_C, "C", 0.95);
  } else {
    Serial.println("Thermocouple error");
  }

  // 2. DHT (gas T + humidity for ambient check)
  float T_gas = dht.readTemperature();
  float H_gas = dht.readHumidity();
  if (!isnan(T_gas)) {
    publishSensor("gas_temperature", T_gas, "C", 0.90);
  }

  // 3. MQ-7 (CO)
  int raw_mq7 = analogRead(MQ7_PIN);
  float V_mq7 = raw_mq7 * 3.3 / 4095.0;        // ESP32 ADC is 12-bit, 0-3.3V
  float R_mq7 = MQ7_RL * (3.3 - V_mq7) / V_mq7;  // Voltage divider
  float ratio = R_mq7 / MQ7_RO;
  // CO ppm ~ a * (R/Ro)^b; for MQ-7: a=23.5, b=-1.5 (in 100 ppm range)
  float CO_ppm = 23.5 * pow(ratio, -1.5);
  if (CO_ppm < 1000) {  // sanity bound
    publishSensor("co", CO_ppm, "ppm", 0.85);
  }

  // 4. MQ-135 (NOx proxy: NH3 + NOx)
  int raw_mq135 = analogRead(MQ135_PIN);
  float V_mq135 = raw_mq135 * 3.3 / 4095.0;
  float R_mq135 = MQ7_RL * (3.3 - V_mq135) / V_mq135;
  float ratio135 = R_mq135 / MQ135_R0;
  // NH3: a=102, b=-2.6; CO2: a=110, b=-2.7
  float NOx_proxy = 102.0 * pow(ratio135, -2.6);  // proxy for NOx (NH3 in reality)
  publishSensor("nox_proxy", NOx_proxy, "ppm", 0.75);

  // 5. Pressure (4-20mA via 250Ω -> 0.5-4.5V)
  int raw_pres = analogRead(PRESSURE_PIN);
  float V_pres = raw_pres * 3.3 / 4095.0;
  // 4-20mA: 0.5V = 0Pa, 4.5V = max (e.g., 5000 Pa)
  float P_pa = (V_pres - PRESSURE_V_MIN) / (PRESSURE_V_MAX - PRESSURE_V_MIN) * 5000.0;
  if (P_pa >= 0) {
    publishSensor("pressure", P_pa, "Pa", 0.90);
  }
}

// ===== Publish one sensor reading =====
void publishSensor(const char* sensorType, float value, const char* unit, float quality) {
  StaticJsonDocument<256> doc;
  doc["value"] = value;
  doc["unit"] = unit;
  doc["quality"] = quality;
  doc["timestamp"] = millis();

  char payload[256];
  serializeJson(doc, payload);

  String topic = "nepal/";
  topic += PLANT_ID;
  topic += "/";
  topic += KILN_ID;
  topic += "/";
  topic += sensorType;

  if (WiFi.status() == WL_CONNECTED && mqtt.connected()) {
    mqtt.publish(topic.c_str(), payload, true);
  }
  // Always log to serial
  Serial.print(topic);
  Serial.print(" -> ");
  Serial.println(payload);
}

// ===== MQTT connection =====
void connectMQTT() {
  while (!mqtt.connected()) {
    Serial.print("Connecting to MQTT...");
    if (mqtt.connect("esp32-sensor-" + String(ESP.getEfuseMac(), HEX),
                     MQTT_USER, MQTT_PASS)) {
      Serial.println(" connected");
    } else {
      Serial.print(" failed, rc=");
      Serial.print(mqtt.state());
      Serial.println(" retrying in 5s");
      delay(5000);
    }
  }
}

// ===== OTA update (for production deployment) =====
#include <ArduinoOTA.h>
void setupOTA() {
  ArduinoOTA.setHostname("nepal-sensor-01");
  ArduinoOTA.setPassword("ota-pass");
  ArduinoOTA.begin();
}
