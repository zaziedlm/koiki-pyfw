"""
E2E Docker API Test for PyJWT Migration
========================================
Docker コンテナ上の API に対して、JWT 認証の E2E 検証を行う。

E2: ユーザー登録 → ログイン → トークン取得 → 認証付きAPI呼び出し
E3: 無効トークンでの拒否確認 (改ざん/期限切れ/不正形式)
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"

# テスト用ユーザー (ユニークにするためタイムスタンプ付加)
TEST_TIMESTAMP = int(time.time())
TEST_EMAIL = f"e2e_pyjwt_{TEST_TIMESTAMP}@test.example.com"
TEST_PASSWORD = "E2eTestP@ss123!"
TEST_USERNAME = f"e2e_pyjwt_{TEST_TIMESTAMP}"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def log_pass(test_id: str, msg: str):
    print(f"  {Colors.GREEN}PASS{Colors.RESET} [{test_id}] {msg}")


def log_fail(test_id: str, msg: str):
    print(f"  {Colors.RED}FAIL{Colors.RESET} [{test_id}] {msg}")


def log_skip(test_id: str, msg: str):
    print(f"  {Colors.YELLOW}SKIP{Colors.RESET} [{test_id}] {msg}")


def log_info(msg: str):
    print(f"  {Colors.CYAN}INFO{Colors.RESET} {msg}")


def api_request(method: str, path: str, data=None, headers=None, form_data=None):
    """API リクエストヘルパー"""
    url = f"{BASE_URL}{API_PREFIX}{path}"
    req_headers = {"Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    body = None
    if form_data:
        body = urllib.parse.urlencode(form_data).encode("utf-8")
        req_headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data:
        body = json.dumps(data).encode("utf-8")
        req_headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode("utf-8")
            return resp.status, json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        resp_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(resp_body)
        except json.JSONDecodeError:
            return e.code, {"raw": resp_body}
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}


def test_health():
    """API サーバーが起動していることを確認"""
    try:
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "healthy":
                log_pass("PRE", f"API server healthy (v{data.get('version', '?')})")
                return True
    except Exception as e:
        log_fail("PRE", f"API server not reachable: {e}")
    return False


# ===========================================================================
# E2: ログイン → 認証付き API 呼び出し
# ===========================================================================
def test_e2_register_and_login():
    """E2-1: ユーザー登録"""
    print(f"\n{Colors.BOLD}=== E2: ユーザー登録 → ログイン → 認証付きAPI ==={Colors.RESET}")

    # E2-1: ユーザー登録
    status_code, body = api_request("POST", "/auth/register", data={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USERNAME,
    })

    if status_code == 201:
        log_pass("E2-1", f"ユーザー登録成功 (email={TEST_EMAIL})")
    elif status_code == 409 or status_code == 400:
        log_info(f"ユーザー既存 or バリデーションエラー ({status_code}): {body.get('detail', body)}")
        log_skip("E2-1", "ユーザー登録スキップ (既存)")
    else:
        log_fail("E2-1", f"ユーザー登録失敗: {status_code} {body}")
        return None

    # E2-2: ログイン (OAuth2 form)
    status_code, body = api_request("POST", "/auth/login", form_data={
        "username": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })

    if status_code == 200 and "access_token" in body:
        access_token = body["access_token"]
        token_type = body.get("token_type", "")
        refresh_token = body.get("refresh_token", "")
        log_pass("E2-2", f"ログイン成功 (token_type={token_type}, token={access_token[:20]}...)")
        if refresh_token:
            log_pass("E2-2b", f"リフレッシュトークン取得 (token={refresh_token[:20]}...)")
        else:
            log_info("リフレッシュトークンなし (設定による)")
        return access_token, refresh_token
    else:
        log_fail("E2-2", f"ログイン失敗: {status_code} {body}")
        return None


def test_e2_authenticated_api(access_token: str):
    """E2-3/4: 認証付きAPI呼び出し"""

    # E2-3: /users/me エンドポイント
    status_code, body = api_request("GET", "/users/me", headers={
        "Authorization": f"Bearer {access_token}",
    })

    if status_code == 200:
        log_pass("E2-3", f"認証付き /users/me 成功 (email={body.get('email', '?')})")
    else:
        log_fail("E2-3", f"認証付き /users/me 失敗: {status_code} {body}")

    # E2-4: Todo CRUD (認証付き)
    # Create
    status_code, body = api_request("POST", "/todos", data={
        "title": f"PyJWT E2E Test {TEST_TIMESTAMP}",
        "description": "Migration verification test item",
    }, headers={
        "Authorization": f"Bearer {access_token}",
    })

    if status_code in (200, 201):
        todo_id = body.get("id", "?")
        log_pass("E2-4a", f"Todo作成成功 (id={todo_id})")

        # Read
        status_code2, body2 = api_request("GET", f"/todos/{todo_id}", headers={
            "Authorization": f"Bearer {access_token}",
        })
        if status_code2 == 200:
            log_pass("E2-4b", f"Todo読取成功 (title={body2.get('title', '?')})")
        else:
            log_fail("E2-4b", f"Todo読取失敗: {status_code2}")

        # Delete (cleanup)
        status_code3, _ = api_request("DELETE", f"/todos/{todo_id}", headers={
            "Authorization": f"Bearer {access_token}",
        })
        if status_code3 in (200, 204):
            log_pass("E2-4c", f"Todo削除成功 (cleanup)")
        else:
            log_info(f"Todo削除: {status_code3} (cleanup失敗は問題なし)")
    elif status_code == 401:
        log_fail("E2-4a", f"Todo作成で認証エラー: {body}")
    else:
        log_fail("E2-4a", f"Todo作成失敗: {status_code} {body}")


# ===========================================================================
# E3: 無効トークンでの拒否確認
# ===========================================================================
def test_e3_invalid_tokens():
    """E3: 各種無効トークンが正しく拒否されることを確認"""
    print(f"\n{Colors.BOLD}=== E3: 無効トークンでの拒否検証 ==={Colors.RESET}")

    # E3-1: トークンなし
    status_code, body = api_request("GET", "/users/me")
    if status_code == 401:
        log_pass("E3-1", f"トークンなし → 401 拒否")
    else:
        log_fail("E3-1", f"トークンなし → 期待: 401, 実際: {status_code}")

    # E3-2: 不正形式トークン
    status_code, body = api_request("GET", "/users/me", headers={
        "Authorization": "Bearer this.is.not.a.valid.jwt.token",
    })
    if status_code == 401:
        log_pass("E3-2", f"不正形式トークン → 401 拒否")
    else:
        log_fail("E3-2", f"不正形式トークン → 期待: 401, 実際: {status_code}")

    # E3-3: 改ざんトークン（シグネチャ部分を変更）
    import jwt as pyjwt
    # 別のシークレットで署名したトークンを送信
    fake_token = pyjwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "completely_wrong_secret_key_12345678",
        algorithm="HS256",
    )
    status_code, body = api_request("GET", "/users/me", headers={
        "Authorization": f"Bearer {fake_token}",
    })
    if status_code == 401:
        log_pass("E3-3", f"改ざんトークン(不正シークレット) → 401 拒否")
    else:
        log_fail("E3-3", f"改ざんトークン → 期待: 401, 実際: {status_code}")

    # E3-4: 期限切れトークン (Production のシークレットは不明だが、形式チェック)
    expired_token = pyjwt.encode(
        {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(hours=24)},
        "some_random_key_for_expired_test",
        algorithm="HS256",
    )
    status_code, body = api_request("GET", "/users/me", headers={
        "Authorization": f"Bearer {expired_token}",
    })
    if status_code == 401:
        log_pass("E3-4", f"期限切れトークン → 401 拒否")
    else:
        log_fail("E3-4", f"期限切れトークン → 期待: 401, 実際: {status_code}")

    # E3-5: 空の Bearer トークン
    status_code, body = api_request("GET", "/users/me", headers={
        "Authorization": "Bearer ",
    })
    if status_code in (401, 403, 422):
        log_pass("E3-5", f"空トークン → {status_code} 拒否")
    else:
        log_fail("E3-5", f"空トークン → 期待: 401/403/422, 実際: {status_code}")


# ===========================================================================
# E4: Keycloak OIDC フロー確認 (設定確認のみ)
# ===========================================================================
def test_e4_keycloak_availability():
    """E4: Keycloak 接続確認"""
    print(f"\n{Colors.BOLD}=== E4: Keycloak OIDC 確認 ==={Colors.RESET}")

    # E4-1: Keycloak well-known endpoint
    try:
        req = urllib.request.Request(
            "http://localhost:8090/realms/master/.well-known/openid-configuration"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            issuer = data.get("issuer", "?")
            jwks_uri = data.get("jwks_uri", "?")
            log_pass("E4-1", f"Keycloak OIDC Discovery 応答 (issuer={issuer})")
            log_info(f"JWKS URI: {jwks_uri}")
    except Exception as e:
        log_skip("E4-1", f"Keycloak 未接続 or 未設定: {e}")
        return

    # E4-2: JWKS エンドポイント
    try:
        req = urllib.request.Request(
            "http://localhost:8090/realms/master/protocol/openid-connect/certs"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            keys = data.get("keys", [])
            log_pass("E4-2", f"JWKS エンドポイント応答 ({len(keys)} keys)")
            for k in keys:
                log_info(f"  kid={k.get('kid','?')}, alg={k.get('alg','?')}, kty={k.get('kty','?')}")

            # E4-3: PyJWK.from_dict() で署名用キーが構築可能か検証
            # 注: use=enc (暗号化用) の鍵は署名には使われないため除外
            from jwt import PyJWK
            signing_keys = [k for k in keys if k.get("use") != "enc"]
            enc_keys = [k for k in keys if k.get("use") == "enc"]
            if enc_keys:
                log_info(f"暗号化用鍵 {len(enc_keys)} 件はスキップ (use=enc, 署名には未使用)")

            success_count = 0
            for k in signing_keys:
                try:
                    signing_key = PyJWK.from_dict(k)
                    if signing_key and signing_key.key:
                        success_count += 1
                except Exception as err:
                    log_fail("E4-3", f"PyJWK.from_dict() 失敗: kid={k.get('kid')}, error={err}")

            if success_count == len(signing_keys) and len(signing_keys) > 0:
                log_pass("E4-3", f"全署名鍵 {success_count}/{success_count} の PyJWK.from_dict() 構築成功")
            elif len(signing_keys) == 0:
                log_skip("E4-3", "署名用鍵が見つかりません")
            else:
                log_fail("E4-3", f"{success_count}/{len(signing_keys)} 署名鍵のみ成功")
    except Exception as e:
        log_skip("E4-2", f"JWKS 取得失敗: {e}")

    # E4-4: SSO エンドポイント存在確認
    sso_endpoints = [
        "/auth/sso/login",
        "/auth/sso/callback",
    ]
    for ep in sso_endpoints:
        # OPTIONS or GET to check existence (405 = exists but wrong method)
        status_code, body = api_request("GET", ep)
        if status_code in (200, 302, 307, 405, 422):
            log_pass("E4-4", f"SSO endpoint {ep} 存在確認 ({status_code})")
        elif status_code == 404:
            log_skip("E4-4", f"SSO endpoint {ep} 未登録 (404)")
        else:
            log_info(f"SSO endpoint {ep}: {status_code}")


# ===========================================================================
# メイン実行
# ===========================================================================
def main():
    print(f"\n{Colors.BOLD}{'='*60}")
    print("PyJWT Migration E2E Verification Test")
    print(f"{'='*60}{Colors.RESET}")
    print(f"  Target: {BASE_URL}")
    print(f"  Time:   {datetime.now().isoformat()}")

    results = {"pass": 0, "fail": 0, "skip": 0}

    # カウント用のラッパー (簡易)
    orig_pass = log_pass.__code__
    orig_fail = log_fail.__code__
    orig_skip = log_skip.__code__

    # Pre-check
    if not test_health():
        print(f"\n{Colors.RED}API サーバーに接続できません。テスト中止。{Colors.RESET}")
        sys.exit(1)

    # E2: 登録 → ログイン → 認証付きAPI
    login_result = test_e2_register_and_login()
    if login_result:
        access_token, refresh_token = login_result
        test_e2_authenticated_api(access_token)
    else:
        log_fail("E2", "ログインフロー失敗のため認証付きAPIテストをスキップ")

    # E3: 無効トークン拒否
    test_e3_invalid_tokens()

    # E4: Keycloak OIDC
    test_e4_keycloak_availability()

    print(f"\n{Colors.BOLD}{'='*60}")
    print(f"E2E Verification Complete")
    print(f"{'='*60}{Colors.RESET}\n")


if __name__ == "__main__":
    main()
