from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime, date
from openai import OpenAI
from pywebpush import webpush, WebPushException
import json
import os
import time

app = Flask(__name__, static_url_path='/static', static_folder='static')
log_data = []
subscriptions = []

# ✅ OpenAI 클라이언트 초기화
client = OpenAI(api_key=" abcd ")  # 실제 키로 교체하세요

# 🔐 VAPID 키 설정 (Base64URL 형식)
VAPID_PUBLIC_KEY = "BEkkxbnqYX1utrwY5ow02QX0mlLoaqg2sZKS1QWB-JEZyg_3ceGt0yNGOJpXlVmaXGGdA-NMv1wqkMywo1fflxQ"
VAPID_PRIVATE_KEY = "PPSTYKNCb7gLqQZ0ti6M0yz01sUx2zDFL3rpiMWp9c8"
VAPID_CLAIMS = {"sub": "mailto:pjh2553702@naver.com"}

# 🕒 상태 관리용 변수
last_feedback_time = 0
cooldown = 15  # 초 단위, bad일 때 15초마다 한 번만 반응
last_bad_time = None
daily_bad_count = 0
last_bad_date = None


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/postdata', methods=['POST'])
def postdata():
    global last_feedback_time, last_bad_time, daily_bad_count, last_bad_date
    data = request.json
    pitch = data.get("pitch")
    roll = data.get("roll")
    status = data.get("status")
    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M:%S')

    log_data.append({
        "timestamp": timestamp,
        "pitch": pitch,
        "roll": roll,
        "status": status
    })

    print(f"📥 받은 데이터 - Pitch: {pitch}, Roll: {roll}, Status: {status}")

    gpt_feedback = None

    # ✅ 시간대 분류
    hour = now.hour
    if 6 <= hour < 11:
        time_context = "아침"
    elif 11 <= hour < 17:
        time_context = "오후"
    elif 17 <= hour < 22:
        time_context = "저녁"
    else:
        time_context = "밤"

    # ✅ bad 상태일 때 지속 시간 & 일일 카운트 관리
    bad_duration = 0
    if status == "bad":
        if last_bad_time is None:
            last_bad_time = time.time()
        else:
            bad_duration = int(time.time() - last_bad_time)

        # 날짜 변경 시 카운트 리셋
        if last_bad_date != date.today():
            daily_bad_count = 0
            last_bad_date = date.today()

        daily_bad_count += 1
    else:
        last_bad_time = None  # good 상태로 돌아오면 초기화

    # ✅ bad 상태 & 쿨다운 지난 경우만 GPT 호출
    if status == "bad" and (time.time() - last_feedback_time > cooldown):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": (
                        "너는 개인 맞춤형 자세 교정 코치야. "
                        "말투는 친절하고 간결해야 하며, 바로 행동할 수 있는 조언을 제공해. "
                        "시간대와 습관을 반영해 개인화된 피드백을 해줘."
                    )},
                    {"role": "user", "content": f"""
사용자 이름: 제협
현재 상태: {status}
센서 값: Pitch={pitch}, Roll={roll}
현재 시간대: {time_context}
연속 bad 지속 시간: {bad_duration}초
오늘 bad 상태 누적 횟수: {daily_bad_count}

조건:
- bad → 교정 행동 1~2개 제안
- bad가 오래 지속되면 "지속 시간" 언급
- bad 횟수가 많으면 "환경 개선" 조언
- 답변은 1~2문장, 40자 이내
"""}
                ],
                max_tokens=150
            )
            gpt_feedback = response.choices[0].message.content
            print(f"🤖 GPT 피드백: {gpt_feedback}")
            last_feedback_time = time.time()  # 마지막 호출 시간 갱신
        except Exception as e:
            print(f"❌ GPT 피드백 생성 실패: {e}")

        # ✅ bad 상태일 때만 푸시 알림 전송
        try:
            for sub in subscriptions:
                webpush(
                    subscription_info=sub,
                    data=json.dumps({
                        "message": f"⚠️ 현재 자세가 좋지 않습니다.",
                        "gpt_feedback": gpt_feedback
                    }),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )
        except WebPushException as e:
            print(f"❌ 푸시 전송 실패: {e}")

    return "Data Received", 200


@app.route('/subscribe', methods=['POST'])
def subscribe():
    subscription = request.get_json()
    subscriptions.append(subscription)
    print("📧 구독 정보 저장 완료")
    return jsonify({"message": "Subscribed successfully"}), 201


@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename, mimetype="application/javascript")


@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
