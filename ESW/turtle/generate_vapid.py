from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

# VAPID 키 쌍 생성 (P-256 / prime256v1 / secp256r1)
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# 🔐 Private Key (PEM) - 서버에서만 사용
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode("utf-8")

# 🔓 Public Key (PEM) - 참고용
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode("utf-8")

# 🌐 Public Key (Base64URL, X9.62 Uncompressed Point)
raw_public = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)
public_base64url = base64.urlsafe_b64encode(raw_public).decode("utf-8")

# 출력
print("🔐 Private Key (PEM)\n", private_pem)
print("\n🔓 Public Key (PEM)\n", public_pem)
print("\n🌐 Public Key (Base64URL, JS applicationServerKey로 사용)\n", public_base64url)
