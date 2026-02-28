"""
PyJWT Migration Verification Tests (T1-T8)
==========================================
python-jose + jwcrypto → PyJWT[crypto] 移行の観点別検証テスト。

観点:
  T1: HS256 トークン生成 (create_access_token)
  T2: HS256 トークンデコード検証
  T3: HS256 有効期限切れ拒否
  T4: HS256 改ざん検知
  T5: RS256 PyJWK.from_dict() 鍵構築
  T6: RS256 署名検証成功
  T7: RS256 不正鍵拒否
  T8: 例外マッピング完全性
"""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from jwt import PyJWK
from jwt.exceptions import (
    DecodeError,
    ExpiredSignatureError,
    InvalidKeyError,
    InvalidSignatureError,
    InvalidTokenError,
    PyJWKError,
)


# ---------------------------------------------------------------------------
# HS256 テスト用定数
# ---------------------------------------------------------------------------
HS256_SECRET = "test_jwt_secret_for_migration_verification"
HS256_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# RS256 テスト用ヘルパー
# ---------------------------------------------------------------------------
def _generate_rsa_keypair():
    """テスト用 RSA 2048-bit 鍵ペアを生成"""
    from cryptography.hazmat.primitives.asymmetric import rsa as _rsa

    private_key = _rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key


def _private_key_to_pem(private_key) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _public_key_to_jwk_dict(private_key, kid: str = "test-kid-001") -> dict:
    """公開鍵を JWK dict 形式に変換 (JWKS keys[] の1要素に相当)"""
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    import json

    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()

    def _int_to_base64url(n: int, length: int) -> str:
        import base64
        data = n.to_bytes(length, byteorder="big")
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    # RSA 2048-bit: n=256 bytes, e=3 bytes
    return {
        "kty": "RSA",
        "use": "sig",
        "kid": kid,
        "alg": "RS256",
        "n": _int_to_base64url(public_numbers.n, 256),
        "e": _int_to_base64url(public_numbers.e, 3),
    }


# ===========================================================================
# T1: HS256 トークン生成 — create_access_token 互換性
# ===========================================================================
class TestT1_HS256TokenGeneration:
    """PyJWT の jwt.encode() が python-jose と同等のトークンを生成することを検証"""

    def test_encode_produces_valid_jwt_string(self):
        """jwt.encode() が 3-part dot-separated JWT 文字列を返す"""
        payload = {
            "sub": "42",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3, f"JWT は header.payload.signature の3パート: got {len(parts)}"

    def test_encode_with_additional_claims(self):
        """追加クレーム (iss, aud, iat) が正しくエンコードされる"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": "user-123",
            "exp": now + timedelta(hours=1),
            "iss": "koiki-fw",
            "aud": "koiki-client",
            "iat": now,
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)
        decoded = pyjwt.decode(
            token,
            HS256_SECRET,
            algorithms=[HS256_ALGORITHM],
            audience="koiki-client",
            issuer="koiki-fw",
        )
        assert decoded["sub"] == "user-123"
        assert decoded["iss"] == "koiki-fw"
        assert decoded["aud"] == "koiki-client"

    def test_create_access_token_integration(self):
        """libkoiki.core.security.create_access_token が正常動作する"""
        with patch("libkoiki.core.security.settings") as mock_settings:
            mock_settings.JWT_SECRET = HS256_SECRET
            mock_settings.JWT_ALGORITHM = HS256_ALGORITHM
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60

            from libkoiki.core.security import create_access_token

            token = create_access_token(subject="99")
            assert isinstance(token, str)
            assert len(token.split(".")) == 3

            # デコードして sub を確認
            decoded = pyjwt.decode(
                token, HS256_SECRET, algorithms=[HS256_ALGORITHM]
            )
            assert decoded["sub"] == "99"


# ===========================================================================
# T2: HS256 トークンデコード検証
# ===========================================================================
class TestT2_HS256TokenDecode:
    """jwt.decode() がペイロードを正しく復元することを検証"""

    def test_decode_restores_payload(self):
        """エンコード → デコードでペイロードが正確に復元される"""
        original = {
            "sub": "user-42",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "custom_claim": "hello",
        }
        token = pyjwt.encode(original, HS256_SECRET, algorithm=HS256_ALGORITHM)
        decoded = pyjwt.decode(token, HS256_SECRET, algorithms=[HS256_ALGORITHM])

        assert decoded["sub"] == original["sub"]
        assert decoded["custom_claim"] == original["custom_claim"]
        assert "exp" in decoded

    def test_decode_with_algorithms_list(self):
        """algorithms パラメータがリスト形式で正しく機能する"""
        payload = {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        # 複数アルゴリズムを許可リストに含める
        decoded = pyjwt.decode(
            token, HS256_SECRET, algorithms=["HS256", "HS384", "HS512"]
        )
        assert decoded["sub"] == "1"

    def test_decode_integer_subject_roundtrip(self):
        """sub を文字列化した値が正しくラウンドトリップする (security.py の挙動)"""
        user_id = 12345
        payload = {
            "sub": str(user_id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)
        decoded = pyjwt.decode(token, HS256_SECRET, algorithms=[HS256_ALGORITHM])
        assert int(decoded["sub"]) == user_id


# ===========================================================================
# T3: HS256 有効期限切れ拒否
# ===========================================================================
class TestT3_HS256ExpiryEnforcement:
    """期限切れトークンが正しく拒否されることを検証"""

    def test_expired_token_raises_expired_signature_error(self):
        """exp が過去のトークンは ExpiredSignatureError を送出"""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        with pytest.raises(ExpiredSignatureError):
            pyjwt.decode(token, HS256_SECRET, algorithms=[HS256_ALGORITHM])

    def test_expired_signature_error_is_invalid_token_error(self):
        """ExpiredSignatureError は InvalidTokenError のサブクラス (例外マッピング互換性)"""
        assert issubclass(ExpiredSignatureError, InvalidTokenError)

    def test_leeway_allows_slightly_expired_token(self):
        """leeway パラメータで猶予期間内の期限切れトークンを許容"""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=5),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        # leeway=10 秒で 5秒前の期限切れを許容
        decoded = pyjwt.decode(
            token, HS256_SECRET, algorithms=[HS256_ALGORITHM], leeway=10
        )
        assert decoded["sub"] == "user-1"

    def test_leeway_rejects_beyond_grace_period(self):
        """leeway を超えた期限切れは拒否される"""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=30),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        with pytest.raises(ExpiredSignatureError):
            pyjwt.decode(
                token, HS256_SECRET, algorithms=[HS256_ALGORITHM], leeway=10
            )


# ===========================================================================
# T4: HS256 改ざん検知
# ===========================================================================
class TestT4_HS256TamperDetection:
    """署名改ざん・不正シークレットの検知を検証"""

    def test_wrong_secret_raises_invalid_signature_error(self):
        """異なるシークレットで署名されたトークンは検証失敗"""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, "correct_secret", algorithm=HS256_ALGORITHM)

        with pytest.raises(InvalidSignatureError):
            pyjwt.decode(token, "wrong_secret", algorithms=[HS256_ALGORITHM])

    def test_invalid_signature_error_is_invalid_token_error(self):
        """InvalidSignatureError は InvalidTokenError のサブクラス"""
        assert issubclass(InvalidSignatureError, InvalidTokenError)

    def test_tampered_payload_detected(self):
        """ペイロード部分を改ざんしたトークンは検証失敗"""
        import base64

        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        # ペイロード部分を改ざん
        parts = token.split(".")
        # 偽のペイロードを作成
        fake_payload = base64.urlsafe_b64encode(b'{"sub":"admin","exp":9999999999}')
        parts[1] = fake_payload.decode().rstrip("=")
        tampered_token = ".".join(parts)

        with pytest.raises(InvalidTokenError):
            pyjwt.decode(tampered_token, HS256_SECRET, algorithms=[HS256_ALGORITHM])

    def test_malformed_token_raises_decode_error(self):
        """不正なフォーマットのトークンは DecodeError を送出"""
        with pytest.raises(DecodeError):
            pyjwt.decode("not.a.valid.jwt.token", HS256_SECRET, algorithms=[HS256_ALGORITHM])

    def test_decode_error_is_invalid_token_error(self):
        """DecodeError は InvalidTokenError のサブクラス"""
        assert issubclass(DecodeError, InvalidTokenError)


# ===========================================================================
# T5: RS256 PyJWK.from_dict() 鍵構築
# ===========================================================================
class TestT5_RS256KeyConstruction:
    """PyJWK.from_dict() が JWK dict から正しく署名鍵を構築することを検証
    (sso_service.py の _verify_jwt_with_jwks で使用)"""

    def test_from_dict_constructs_valid_key(self):
        """RSA JWK dict から PyJWK オブジェクトを正常生成"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)

        signing_key = PyJWK.from_dict(jwk_dict)
        assert signing_key is not None
        assert signing_key.key is not None

    def test_from_dict_preserves_kid(self):
        """kid (Key ID) が保持される"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key, kid="my-custom-kid")

        signing_key = PyJWK.from_dict(jwk_dict)
        assert signing_key.key_id == "my-custom-kid"

    def test_from_dict_with_invalid_jwk_raises_error(self):
        """不正な JWK dict は PyJWKError を送出"""
        invalid_jwk = {"kty": "RSA", "kid": "bad-key"}  # n, e が不足

        with pytest.raises((InvalidKeyError, PyJWKError)):
            PyJWK.from_dict(invalid_jwk)

    def test_from_dict_matches_original_public_key(self):
        """from_dict() で構築した鍵が元の公開鍵と一致する"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        # 元の公開鍵の PEM と比較
        original_pub_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        restored_pub_pem = signing_key.key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        assert original_pub_pem == restored_pub_pem


# ===========================================================================
# T6: RS256 署名検証成功
# ===========================================================================
class TestT6_RS256SignatureVerification:
    """RS256 で署名されたトークンが PyJWK 鍵で検証成功することを確認
    (sso_service.py の jwt.decode(key=signing_key, ...) の動作検証)"""

    def test_rs256_encode_and_decode_roundtrip(self):
        """RS256: 秘密鍵で署名 → PyJWK(公開鍵) でデコード"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        payload = {
            "sub": "oidc-user-1",
            "iss": "https://idp.example.com",
            "aud": "koiki-client",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc),
        }

        # 秘密鍵で署名
        private_pem = _private_key_to_pem(private_key)
        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm="RS256",
            headers={"kid": "test-kid-001"},
        )

        # PyJWK で検証
        decoded = pyjwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            audience="koiki-client",
            issuer="https://idp.example.com",
        )
        assert decoded["sub"] == "oidc-user-1"
        assert decoded["iss"] == "https://idp.example.com"

    def test_rs256_with_leeway(self):
        """RS256 トークンに leeway パラメータが適用される (sso_service.py SSO_CLOCK_SKEW_SECONDS)"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        # 5秒前に期限切れのトークン
        payload = {
            "sub": "user-2",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=5),
        }
        private_pem = _private_key_to_pem(private_key)
        token = pyjwt.encode(payload, private_pem, algorithm="RS256")

        # leeway=10 で許容
        decoded = pyjwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            leeway=10,
        )
        assert decoded["sub"] == "user-2"

    def test_rs256_with_options_dict(self):
        """options dict による検証制御 (sso_service.py の形式と一致)"""
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        payload = {
            "sub": "user-3",
            "iss": "https://idp.example.com",
            "aud": "koiki-client",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        private_pem = _private_key_to_pem(private_key)
        token = pyjwt.encode(payload, private_pem, algorithm="RS256")

        # sso_service.py と同じ options 構造
        decoded = pyjwt.decode(
            token,
            key=signing_key,
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
            },
            audience="koiki-client",
            issuer="https://idp.example.com",
            leeway=30,
        )
        assert decoded["sub"] == "user-3"


# ===========================================================================
# T7: RS256 不正鍵拒否
# ===========================================================================
class TestT7_RS256WrongKeyRejection:
    """異なる RSA 鍵で署名されたトークンが拒否されることを検証"""

    def test_wrong_rsa_key_raises_error(self):
        """別の RSA 鍵ペアの公開鍵では検証失敗"""
        # 鍵ペア A で署名
        private_key_a = _generate_rsa_keypair()
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        private_pem_a = _private_key_to_pem(private_key_a)
        token = pyjwt.encode(payload, private_pem_a, algorithm="RS256")

        # 鍵ペア B の公開鍵で検証 → 失敗
        private_key_b = _generate_rsa_keypair()
        jwk_dict_b = _public_key_to_jwk_dict(private_key_b, kid="different-kid")
        signing_key_b = PyJWK.from_dict(jwk_dict_b)

        with pytest.raises(InvalidSignatureError):
            pyjwt.decode(token, key=signing_key_b, algorithms=["RS256"])

    def test_hs256_token_rejected_when_rs256_required(self):
        """HS256 で署名されたトークンを RS256 限定で検証すると失敗"""
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        hs256_token = pyjwt.encode(payload, "secret", algorithm="HS256")

        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        with pytest.raises(InvalidTokenError):
            pyjwt.decode(hs256_token, key=signing_key, algorithms=["RS256"])

    def test_none_algorithm_rejected_at_decode(self):
        """alg=none 攻撃がデコード時に拒否される (PyJWT のセキュリティ保護)"""
        # PyJWT は encode 時に "none" を許容するが、decode 時に algorithms リストに
        # "none" が含まれていなければ拒否する。これが攻撃防御のポイント。
        payload = {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        none_token = pyjwt.encode(payload, None, algorithm="none")

        # algorithms=["RS256"] しか許可しない場合、"none" トークンは拒否される
        private_key = _generate_rsa_keypair()
        jwk_dict = _public_key_to_jwk_dict(private_key)
        signing_key = PyJWK.from_dict(jwk_dict)

        with pytest.raises(InvalidTokenError):
            pyjwt.decode(none_token, key=signing_key, algorithms=["RS256"])

    def test_none_algorithm_rejected_with_hs256(self):
        """alg=none トークンは HS256 検証でも拒否される"""
        payload = {"sub": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
        none_token = pyjwt.encode(payload, None, algorithm="none")

        with pytest.raises(InvalidTokenError):
            pyjwt.decode(none_token, HS256_SECRET, algorithms=["HS256"])


# ===========================================================================
# T8: 例外マッピング完全性
# ===========================================================================
class TestT8_ExceptionMappingCompleteness:
    """python-jose の JWTError/JWKError 相当をすべて InvalidTokenError で捕捉できることを検証
    (security.py: except (InvalidTokenError, ValidationError))
    (sso_service.py: except InvalidTokenError / except (InvalidKeyError, PyJWKError))"""

    def test_all_jwt_errors_are_subtypes_of_invalid_token_error(self):
        """主要な JWT エラーがすべて InvalidTokenError のサブクラス"""
        error_classes = [
            DecodeError,
            ExpiredSignatureError,
            InvalidSignatureError,
        ]
        for cls in error_classes:
            assert issubclass(cls, InvalidTokenError), (
                f"{cls.__name__} は InvalidTokenError のサブクラスであるべき"
            )

    def test_invalid_key_error_hierarchy(self):
        """InvalidKeyError の継承階層を確認"""
        # InvalidKeyError は PyJWT の独自例外
        assert issubclass(InvalidKeyError, Exception)

    def test_pyjwk_error_hierarchy(self):
        """PyJWKError の継承階層を確認"""
        assert issubclass(PyJWKError, Exception)

    def test_security_py_exception_pattern(self):
        """security.py の except (InvalidTokenError, ValidationError) パターンが
        トークンデコード失敗を正しく捕捉する"""
        from pydantic import ValidationError

        # 不正トークン → InvalidTokenError
        caught_invalid_token = False
        try:
            pyjwt.decode("invalid", HS256_SECRET, algorithms=[HS256_ALGORITHM])
        except (InvalidTokenError, ValidationError):
            caught_invalid_token = True
        assert caught_invalid_token, "InvalidTokenError が except 句で捕捉されるべき"

    def test_sso_service_exception_pattern_jwt(self):
        """sso_service.py の except InvalidTokenError パターンが JWT エラーを捕捉"""
        # 期限切れトークン
        payload = {
            "sub": "user-1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        token = pyjwt.encode(payload, HS256_SECRET, algorithm=HS256_ALGORITHM)

        caught = False
        try:
            pyjwt.decode(token, HS256_SECRET, algorithms=[HS256_ALGORITHM])
        except InvalidTokenError:
            caught = True
        assert caught, "InvalidTokenError が ExpiredSignatureError を捕捉するべき"

    def test_sso_service_exception_pattern_jwk(self):
        """sso_service.py の except (InvalidKeyError, PyJWKError) パターンが JWK エラーを捕捉"""
        caught = False
        try:
            PyJWK.from_dict({"kty": "RSA"})  # 不正な JWK
        except (InvalidKeyError, PyJWKError):
            caught = True
        assert caught, "(InvalidKeyError, PyJWKError) が不正 JWK を捕捉するべき"

    def test_get_unverified_header_works(self):
        """jwt.get_unverified_header() が sso_service.py で使用される形式で動作"""
        private_key = _generate_rsa_keypair()
        private_pem = _private_key_to_pem(private_key)
        payload = {"sub": "test", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}

        token = pyjwt.encode(
            payload,
            private_pem,
            algorithm="RS256",
            headers={"kid": "key-123"},
        )

        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "RS256"
        assert header["kid"] == "key-123"
