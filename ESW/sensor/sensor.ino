#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <MPU6050.h>
#include <math.h>
#include <time.h>

const char* ssid = "KT_WiFi_58B5";
const char* password = "2ad81zb794";
const char* serverUrl = "http://172.30.1.22:5000/postdata";

MPU6050 imu;

void setup() {
  Serial.begin(115200);
  Wire.begin(21, 22);
  imu.initialize();

  // WiFi 연결
  WiFi.begin(ssid, password);
  Serial.print("🔌 WiFi 연결 중");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi 연결 완료!");

  // NTP 시간 설정
  configTime(9 * 3600, 0, "pool.ntp.org", "time.nist.gov");
  while (time(nullptr) < 100000) {
    Serial.print("⏳ 시간 동기화 중...\n");
    delay(500);
  }

  // IP 주소 확인
  IPAddress espIP = WiFi.localIP();
  Serial.print("📡 ESP32 IP 주소: ");
  Serial.println(espIP);
}

void loop() {
  int16_t ax_raw, ay_raw, az_raw, gx, gy, gz;
  imu.getMotion6(&ax_raw, &ay_raw, &az_raw, &gx, &gy, &gz);

  float ax = ax_raw / 16384.0;
  float ay = ay_raw / 16384.0;
  float az = az_raw / 16384.0;

  float pitch = atan2(ax, sqrt(ay * ay + az * az)) * 180 / PI;
  float roll  = atan2(ay, sqrt(ax * ax + az * az)) * 180 / PI;

  // ✅ roll = 90°가 정자세 기준
  float roll_deviation = abs(roll - 90.0);

  // 임계값 설정 (±20° 벗어나면 bad)
  String status = (roll_deviation > 20 || abs(pitch) > 20) ? "bad" : "good";

  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  char timestamp[25];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", timeinfo);

  Serial.printf("📈 Pitch: %.2f°, Roll: %.2f° (편차: %.2f°), Status: %s\n",
                pitch, roll, roll_deviation, status.c_str());
  Serial.printf("⏱️ Timestamp: %s\n", timestamp);

  String jsonData = "{";
  jsonData += "\"pitch\":" + String(pitch, 2) + ",";
  jsonData += "\"roll\":" + String(roll, 2) + ",";
  jsonData += "\"status\":\"" + status + "\",";
  jsonData += "\"timestamp\":\"" + String(timestamp) + "\"";
  jsonData += "}";

  Serial.print("📤 전송할 JSON: ");
  Serial.println(jsonData);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(jsonData);
    if (httpResponseCode > 0) {
      Serial.print("📬 서버 응답 코드: ");
      Serial.println(httpResponseCode);
    } else {
      Serial.print("❌ 전송 실패, 에러 코드: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  }

  delay(2000);
}
