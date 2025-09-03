// Service Worker 설치 단계
self.addEventListener('install', event => {
  console.log("📥 Service Worker installing...");
  // 곧바로 활성화되도록
  self.skipWaiting();
});

// Service Worker 활성화 단계
self.addEventListener('activate', event => {
  console.log("✅ Service Worker activated!");
  // 이전 캐시/불필요한 데이터 정리 가능 (지금은 패스)
  event.waitUntil(clients.claim());
});

// 푸시 알림 수신 단계
self.addEventListener('push', event => {
  let data = {};

  try {
    data = event.data.json();
  } catch (e) {
    data.message = event.data.text();
  }

  const title = "💡 자세 피드백 도착!";

  // gpt_feedback이 있으면 본문에 추가
  const bodyText = data.gpt_feedback 
    ? `${data.message}\n\n🤖 ${data.gpt_feedback}`
    : (data.message || "⚠️ 새로운 자세 알림이 도착했습니다.");

  const options = {
    body: bodyText,
    icon: '/static/icon.png',
    badge: '/static/badge.png'
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// 알림 클릭 시 동작
self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});
