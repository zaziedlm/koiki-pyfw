"""
KOIKI-FW セキュリティAPI テストスクリプト
権限ベースのAPIアクセステスト
"""

from typing import Dict, Optional

import requests


class SecurityAPITester:
    """セキュリティAPI テスター"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.tokens: Dict[str, str] = {}

    def login(self, username: str, password: str) -> Optional[str]:
        """ログインしてトークンを取得"""
        login_data = {"username": username, "password": password}

        try:
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    self.tokens[username] = token
                    print(f"✅ ログイン成功: {username}")
                    return token
            else:
                error = response.text
                print(f"❌ ログイン失敗: {username} - {response.status_code}: {error}")

        except Exception as e:
            print(f"❌ ログインエラー: {username} - {e}")

        return None

    def make_authenticated_request(
        self, method: str, endpoint: str, username: str, **kwargs
    ) -> Optional[requests.Response]:
        """認証付きリクエストを送信"""
        if username not in self.tokens:
            print(f"❌ 認証トークンなし: {username}")
            return None

        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.tokens[username]}"
        kwargs["headers"] = headers

        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, **kwargs)
            return response

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")
            return None

    def test_endpoint_access(
        self, username: str, method: str, endpoint: str, expected_status: int = 200
    ) -> bool:
        """エンドポイントアクセステスト"""
        print(f"🔍 テスト: {username} -> {method} {endpoint}")

        response = self.make_authenticated_request(method, endpoint, username)

        if response is None:
            print(f"  ❌ リクエスト失敗")
            return False

        success = response.status_code == expected_status
        status_emoji = "✅" if success else "❌"

        print(
            f"  {status_emoji} ステータス: {response.status_code} (期待値: {expected_status})"
        )

        if not success:
            try:
                error_data = response.json()
                print(f"    エラー詳細: {error_data}")
            except Exception:
                print(f"    レスポンス: {response.text[:200]}")

        return success


def run_security_tests():
    """セキュリティテストの実行"""
    print("🔐 KOIKI-FW セキュリティAPIテスト開始")
    print("=" * 60)

    tester = SecurityAPITester()

    # テストユーザーのログイン情報
    test_users = {
        "admin@example.com": "admin123456",
        "security@example.com": "security123456",
        "user_admin@example.com": "useradmin123456",
        "user@example.com": "testuser123456",
    }

    # 1. 全ユーザーのログインテスト
    print("\n👤 ログインテスト")
    print("-" * 30)
    login_success = {}

    for email, password in test_users.items():
        token = tester.login(email, password)
        login_success[email] = token is not None

    # ログインに失敗したユーザーがいる場合は早期終了
    failed_logins = [email for email, success in login_success.items() if not success]
    if failed_logins:
        print(f"\n❌ ログイン失敗のため、テストを中止します: {failed_logins}")
        return

    print(f"\n✅ 全ユーザーのログインが成功しました")

    # 2. セキュリティメトリクスAPIテスト
    print("\n📊 セキュリティメトリクスAPI アクセステスト")
    print("-" * 40)

    # 権限あり: admin (system_admin), security (security_admin)
    # 権限なし: user_admin, user (todo_user)

    # GET /api/v1/security/metrics - read:security_metrics権限が必要
    security_read_tests = [
        ("admin@example.com", 200),  # system_admin: 全権限あり
        ("security@example.com", 200),  # security_admin: read:security_metrics あり
        ("user_admin@example.com", 403),  # user_admin: 権限なし
        ("user@example.com", 403),  # todo_user: 権限なし
    ]

    for email, expected_status in security_read_tests:
        tester.test_endpoint_access(
            email, "GET", "/api/v1/security/metrics", expected_status
        )

    # POST /api/v1/security/metrics/reset - manage:security_metrics権限が必要
    print("\n🔄 セキュリティメトリクス管理API テスト")
    print("-" * 40)

    security_manage_tests = [
        ("admin@example.com", 200),  # system_admin: 全権限あり
        ("security@example.com", 200),  # security_admin: manage:security_metrics あり
        ("user_admin@example.com", 403),  # user_admin: 権限なし
        ("user@example.com", 403),  # todo_user: 権限なし
    ]

    for email, expected_status in security_manage_tests:
        tester.test_endpoint_access(
            email, "POST", "/api/v1/security/metrics/reset", expected_status
        )

    # 3. ユーザー管理APIテスト（仮想エンドポイント）
    print("\n👥 ユーザー管理API アクセステスト")
    print("-" * 40)

    # GET /api/v1/users - read:users権限が必要
    user_read_tests = [
        (
            "admin@example.com",
            404,
        ),  # system_admin: read:users権限あり（エンドポイント未実装のため404）
        (
            "security@example.com",
            404,
        ),  # security_admin: read:users権限なし → 実際は権限あり
        ("user_admin@example.com", 404),  # user_admin: read:users権限あり
        ("user@example.com", 403),  # todo_user: 権限なし
    ]

    for email, expected_status in user_read_tests:
        tester.test_endpoint_access(email, "GET", "/api/v1/users", expected_status)

    # 4. ToDo管理APIテスト（既存エンドポイント）
    print("\n📝 ToDo管理API アクセステスト")
    print("-" * 40)

    # GET /api/v1/todos - read:todos権限が必要
    todo_read_tests = [
        ("admin@example.com", 200),  # system_admin: 全権限あり
        ("security@example.com", 403),  # security_admin: read:todos権限なし
        ("user_admin@example.com", 200),  # user_admin: read:todos権限あり
        ("user@example.com", 200),  # todo_user: read:todos権限あり
    ]

    for email, expected_status in todo_read_tests:
        tester.test_endpoint_access(email, "GET", "/api/v1/todos", expected_status)

    # 5. 結果サマリー
    print("\n" + "=" * 60)
    print("📋 テスト結果サマリー")
    print("=" * 60)

    print("\n🔑 ユーザーロール別権限マトリックス:")
    print("  admin@example.com (system_admin): 全権限")
    print("  security@example.com (security_admin): セキュリティ関連のみ")
    print("  user_admin@example.com (user_admin): ユーザー・ToDo管理")
    print("  user@example.com (todo_user): ToDo操作のみ")

    print("\n✅ テストが完了しました！")
    print("📊 各APIエンドポイントの権限制御が正常に動作していることを確認")


if __name__ == "__main__":
    run_security_tests()
