#!/usr/bin/env python3
"""
CSRF検証テストスクリプト
フロントエンドのNext.js Route HandlersにおけるCSRF保護をテスト
"""

import json
import random
import string
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple


class CSRFTestResponse:
    """CSRFテスト用HTTPレスポンスのラッパークラス"""

    def __init__(
        self,
        status_code: int,
        content: bytes,
        headers: dict,
        cookies: Dict[str, str] = None,
    ):
        self.status_code = status_code
        self.content = content
        self.headers = headers
        self.text = content.decode("utf-8") if content else ""
        self.cookies = cookies or {}

    def json(self):
        """JSONレスポンスをパース"""
        if not self.text:
            return {}
        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            return {}


class CSRFTester:
    """CSRF検証テスター"""

    def __init__(self, frontend_url: str = "http://localhost:3000"):
        self.frontend_url = frontend_url
        self.session_cookies: Dict[str, str] = {}
        self.csrf_token: Optional[str] = None

    def parse_cookies(self, set_cookie_headers) -> Dict[str, str]:
        """Set-Cookieヘッダーからクッキーを解析"""
        cookies = {}

        # set_cookie_headers が文字列の場合と複数のヘッダーの場合に対応
        if isinstance(set_cookie_headers, str):
            header_list = [set_cookie_headers]
        elif isinstance(set_cookie_headers, list):
            header_list = set_cookie_headers
        else:
            return cookies

        for header in header_list:
            if not header:
                continue

            # セミコロンで分割して最初の部分（name=value）のみ取得
            cookie_parts = header.split(";")
            if cookie_parts and "=" in cookie_parts[0]:
                name, value = cookie_parts[0].split("=", 1)
                cookies[name.strip()] = value.strip()

        return cookies

    def make_request(
        self,
        method: str,
        url: str,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
        include_csrf: bool = True,
        custom_csrf: Optional[str] = None,
        include_cookies: bool = True,
    ) -> CSRFTestResponse:
        """HTTPリクエストを送信"""
        if headers is None:
            headers = {}

        # クッキーの設定
        if include_cookies and self.session_cookies:
            cookie_parts = []
            for name, value in self.session_cookies.items():
                cookie_parts.append(f"{name}={value}")
            if cookie_parts:
                headers["Cookie"] = "; ".join(cookie_parts)

        # CSRFトークンの設定
        if include_csrf:
            csrf_token = custom_csrf if custom_csrf is not None else self.csrf_token
            if csrf_token:
                headers["x-csrf-token"] = csrf_token

        # データの準備
        request_data = None
        if data:
            request_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(request_data))

        # リクエストの作成
        req = urllib.request.Request(
            url, data=request_data, headers=headers, method=method
        )

        try:
            with urllib.request.urlopen(req) as response:
                status_code = response.status
                content = response.read()
                response_headers = dict(response.headers)

                # Set-Cookieヘッダーからクッキーを取得
                response_cookies = {}
                # urllib.requestでは、Set-Cookieヘッダーがある場合に取得する方法
                all_headers = []
                if hasattr(response, "headers"):
                    # response.headersから全てのSet-Cookieヘッダーを取得
                    for key, value in response.headers.items():
                        if key.lower() == "set-cookie":
                            all_headers.append(value)

                # デバッグ情報
                print(f"  🔍 Debug - 全ヘッダー: {dict(response.headers)}")
                print(f"  🔍 Debug - Set-Cookieヘッダー数: {len(all_headers)}")

                if all_headers:
                    response_cookies = self.parse_cookies(all_headers)
                    print(f"  🔍 Debug - パース結果: {response_cookies}")

                return CSRFTestResponse(
                    status_code, content, response_headers, response_cookies
                )

        except urllib.error.HTTPError as e:
            content = e.read()
            response_headers = dict(e.headers) if e.headers else {}

            # エラーレスポンスでもクッキーを確認
            response_cookies = {}
            all_headers = []
            if hasattr(e, "headers") and e.headers:
                # e.headersから全てのSet-Cookieヘッダーを取得
                for key, value in e.headers.items():
                    if key.lower() == "set-cookie":
                        all_headers.append(value)

            if all_headers:
                response_cookies = self.parse_cookies(all_headers)

            return CSRFTestResponse(e.code, content, response_headers, response_cookies)

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")
            return CSRFTestResponse(0, b"", {})

    def generate_random_token(self, length: int = 32) -> str:
        """ランダムなトークンを生成"""
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def login_and_get_csrf(
        self, email: str = "user@example.com", password: str = "testuser123456"
    ) -> bool:
        """ログインしてCSRFトークンを取得"""
        print(f"🔐 ログイン開始: {email}")

        # 最初にCSRFトークン専用エンドポイントからトークンを取得
        print("  📝 CSRFトークンを取得中...")
        csrf_response = self.make_request(
            "GET",
            f"{self.frontend_url}/api/auth/csrf",
            include_csrf=False,
            include_cookies=False,
        )

        print(f"  📋 CSRF応答: {csrf_response.status_code}")
        print(f"  📋 レスポンスヘッダー: {dict(csrf_response.headers)}")
        print(f"  📋 レスポンステキスト: {csrf_response.text}")
        print(f"  📋 取得したクッキー: {list(csrf_response.cookies.keys())}")

        if csrf_response.status_code == 200:
            # CSRFトークンクッキーを取得
            if "koiki_csrf_token" in csrf_response.cookies:
                self.csrf_token = csrf_response.cookies["koiki_csrf_token"]
                print(f"  ✅ CSRFトークン取得成功: {self.csrf_token[:8]}...")
            else:
                print(f"  ⚠️ koiki_csrf_token クッキーが見つかりません")
                print(f"  📋 利用可能なクッキー: {csrf_response.cookies}")

            # すべてのクッキーを保存
            for cookie_name, cookie_value in csrf_response.cookies.items():
                self.session_cookies[cookie_name] = cookie_value
        else:
            print(f"  ⚠️ CSRFトークン取得失敗: {csrf_response.status_code}")
            print(f"  📋 レスポンス内容: {csrf_response.text[:200]}")

        if not self.csrf_token:
            print("  ❌ CSRFトークンが取得できませんでした")
            return False

        # CSRFトークン付きでログイン試行
        print("  🔐 CSRFトークン付きでログイン試行...")
        login_data = {"email": email, "password": password}
        response = self.make_request(
            "POST",
            f"{self.frontend_url}/api/auth/login",
            data=login_data,
            include_csrf=True,
        )

        # 新しいクッキーを保存
        for cookie_name, cookie_value in response.cookies.items():
            self.session_cookies[cookie_name] = cookie_value
            # CSRFトークンが更新された場合は更新
            if cookie_name == "koiki_csrf_token":
                self.csrf_token = cookie_value
                print(f"  🔄 CSRFトークンが更新されました: {self.csrf_token[:8]}...")

        if response.status_code == 200:
            print("  ✅ ログイン成功")
            return True
        else:
            print(f"  ❌ ログイン失敗: {response.status_code} - {response.text[:200]}")
            return False

    def test_csrf_protection(
        self,
        endpoint: str,
        method: str = "POST",
        data: Optional[dict] = None,
        description: str = "",
    ) -> Dict[str, any]:
        """CSRF保護をテスト"""
        print(f"\n🔍 CSRFテスト: {description or f'{method} {endpoint}'}")

        results = {
            "endpoint": endpoint,
            "method": method,
            "description": description,
            "tests": {},
        }

        # テスト1: CSRFトークンなし
        print("  1️⃣ CSRFトークンなし")
        response = self.make_request(
            method, f"{self.frontend_url}{endpoint}", data=data, include_csrf=False
        )
        results["tests"]["no_csrf"] = {
            "status_code": response.status_code,
            "expected": 403,
            "passed": response.status_code == 403,
            "response": response.text[:100] if response.text else "",
        }

        status_emoji = "✅" if response.status_code == 403 else "❌"
        print(f"    {status_emoji} ステータス: {response.status_code} (期待値: 403)")

        # テスト2: 正しいCSRFトークン
        print("  2️⃣ 正しいCSRFトークン")
        response = self.make_request(
            method, f"{self.frontend_url}{endpoint}", data=data, include_csrf=True
        )
        expected_success = 200 if method == "GET" else 200  # GET以外も成功を期待
        results["tests"]["valid_csrf"] = {
            "status_code": response.status_code,
            "expected": expected_success,
            "passed": response.status_code == expected_success,
            "response": response.text[:100] if response.text else "",
        }

        status_emoji = "✅" if response.status_code == expected_success else "❌"
        print(
            f"    {status_emoji} ステータス: {response.status_code} (期待値: {expected_success})"
        )

        # テスト3: 不正なCSRFトークン
        print("  3️⃣ 不正なCSRFトークン")
        fake_token = self.generate_random_token()
        response = self.make_request(
            method, f"{self.frontend_url}{endpoint}", data=data, custom_csrf=fake_token
        )
        results["tests"]["invalid_csrf"] = {
            "status_code": response.status_code,
            "expected": 403,
            "passed": response.status_code == 403,
            "response": response.text[:100] if response.text else "",
        }

        status_emoji = "✅" if response.status_code == 403 else "❌"
        print(f"    {status_emoji} ステータス: {response.status_code} (期待値: 403)")

        # テスト4: 空のCSRFトークン
        print("  4️⃣ 空のCSRFトークン")
        response = self.make_request(
            method, f"{self.frontend_url}{endpoint}", data=data, custom_csrf=""
        )
        results["tests"]["empty_csrf"] = {
            "status_code": response.status_code,
            "expected": 403,
            "passed": response.status_code == 403,
            "response": response.text[:100] if response.text else "",
        }

        status_emoji = "✅" if response.status_code == 403 else "❌"
        print(f"    {status_emoji} ステータス: {response.status_code} (期待値: 403)")

        return results


def run_csrf_tests():
    """CSRF検証テストの実行"""
    print("🔐 CSRF検証テスト開始")
    print("=" * 60)

    # フロントエンドが起動しているか確認
    tester = CSRFTester()

    try:
        # 簡単なヘルスチェック
        response = tester.make_request(
            "GET",
            f"{tester.frontend_url}/api/auth/login",
            include_csrf=False,
            include_cookies=False,
        )
        if response.status_code == 0:
            print("❌ フロントエンドサーバーに接続できません")
            print(f"   {tester.frontend_url} が起動していることを確認してください")
            return
    except Exception as e:
        print(f"❌ フロントエンドサーバー接続エラー: {e}")
        return

    # ログインしてセッションとCSRFトークンを取得
    if not tester.login_and_get_csrf():
        print("❌ ログインに失敗しました。テストを中断します。")
        return

    print(
        f"✅ ログイン完了。CSRFトークン: {tester.csrf_token[:8] if tester.csrf_token else 'なし'}..."
    )

    # テスト対象エンドポイント
    test_endpoints = [
        {
            "endpoint": "/api/auth/login",
            "method": "POST",
            "data": {"email": "user@example.com", "password": "testuser123456"},
            "description": "ログインエンドポイント",
        },
        {
            "endpoint": "/api/auth/register",
            "method": "POST",
            "data": {
                "email": f"test{int(time.time())}@example.com",
                "password": "ComplexPass123!",
                "username": f"testuser{int(time.time())}",
            },
            "description": "ユーザー登録エンドポイント",
        },
        {
            "endpoint": "/api/auth/logout",
            "method": "POST",
            "data": {},
            "description": "ログアウトエンドポイント",
        },
        {
            "endpoint": "/api/todos",
            "method": "POST",
            "data": {"title": "CSRFテスト用Todo", "description": "テスト用のTodoです"},
            "description": "Todo作成エンドポイント",
        },
    ]

    # 各エンドポイントのCSRF検証をテスト
    all_results = []

    for test_config in test_endpoints:
        result = tester.test_csrf_protection(
            endpoint=test_config["endpoint"],
            method=test_config["method"],
            data=test_config["data"],
            description=test_config["description"],
        )
        all_results.append(result)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("📋 CSRF検証テスト結果サマリー")
    print("=" * 60)

    total_tests = 0
    passed_tests = 0

    for result in all_results:
        print(f"\n📍 {result['description']} ({result['method']} {result['endpoint']})")

        for test_name, test_result in result["tests"].items():
            total_tests += 1
            if test_result["passed"]:
                passed_tests += 1
                print(f"  ✅ {test_name}: PASS")
            else:
                print(
                    f"  ❌ {test_name}: FAIL ({test_result['status_code']} != {test_result['expected']})"
                )
                if test_result["response"]:
                    print(f"     レスポンス: {test_result['response']}")

    print(f"\n🎯 テスト結果: {passed_tests}/{total_tests} 成功")

    if passed_tests == total_tests:
        print("🎉 全てのCSRF検証テストが成功しました！")
        print("🔒 CSRF保護が正しく動作しています。")
    else:
        print("⚠️ 一部のCSRF検証テストが失敗しました。")
        print("🔧 CSRF保護の実装を確認してください。")

    print("\n💡 推奨事項:")
    print("  - 全てのstate-changing操作（POST, PUT, DELETE）でCSRF検証を有効にする")
    print(
        "  - CSRFトークンはHttpOnlyクッキーとHTTPヘッダーのDouble Submit Cookie方式を使用"
    )
    print("  - トークンは十分な長さ（32文字以上）のランダム文字列を使用")
    print("  - セッション毎、またはリクエスト毎にトークンを更新")


if __name__ == "__main__":
    print("🚀 CSRF検証テストスクリプト")
    print("📝 使用方法:")
    print("  1. フロントエンドサーバーを起動: cd frontend && npm run dev")
    print("  2. バックエンドサーバーを起動: python main.py")
    print("  3. このスクリプトを実行: python ops/tests/test_csrf_validation.py")
    print("")

    # ユーザーに確認
    try:
        input("準備ができたらEnterキーを押してください...")
        run_csrf_tests()
    except KeyboardInterrupt:
        print("\n\n👋 テストを中断しました")
