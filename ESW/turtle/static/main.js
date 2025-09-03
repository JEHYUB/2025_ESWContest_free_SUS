// ✅ 서버에서 생성한 Base64URL Public Key (한 줄 그대로)
const publicVapidKey = "BEkkxbnqYX1utrwY5ow02QX0mlLoaqg2sZKS1QWB-JEZyg_3ceGt0yNGOJpXlVmaXGGdA-NMv1wqkMywo1fflxQ=";

// ✅ Base64URL → Uint8Array 변환 함수 (패딩 보정 포함)
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding)
    .replace(/-/g, '+')
    .replace(/_/g, '/');

  const rawData = atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

document.getElementById('subscribeBtn').addEventListener('click', async () => {
  console.log("🟢 버튼 클릭됨");

  const permission = await Notification.requestPermission();
  console.log("📢 알림 권한 상태:", permission);

  if (permission === 'granted') {
    console.log("✅ 알림 권한 허용됨");
    await subscribeToPush();
  } else {
    alert("❌ 알림 권한이 허용되지 않았습니다.");
  }
});

async function subscribeToPush() {
  if ('serviceWorker' in navigator && 'PushManager' in window) {
    try {
      const registration = await navigator.serviceWorker.register('/service-worker.js');
      console.log("✅ Service Worker 등록 성공:", registration);

      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicVapidKey),
      });
      console.log("✅ Push 구독 성공:", subscription);

      const res = await fetch('/subscribe', {
        method: 'POST',
        body: JSON.stringify(subscription),
        headers: { 'Content-Type': 'application/json' },
      });

      console.log("📨 서버에 구독 정보 전송 완료", res);
      alert("✅ 푸시 알림 구독 완료!");
    } catch (err) {
      console.error("❌ Service Worker 등록 또는 구독 실패:", err);
    }
  } else {
    alert("❌ 이 브라우저는 푸시 알림을 지원하지 않습니다.");
  }
}