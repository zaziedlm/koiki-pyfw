"""認証系API統合テスト"""
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestAuthAPI:
    """認証系API統合テスト"""
    
    def test_user_registration_success(self, test_client: TestClient):
        """正常なユーザー登録テスト"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "TestPass123@",
                "full_name": "Test User"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["is_active"] is True
        assert "id" in data["user"]
        assert "created_at" in data["user"]
    
    def test_user_registration_duplicate_email(self, test_client: TestClient):
        """重複メールアドレスでの登録テスト"""
        # 最初の登録
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPass123@",
                "full_name": "First User"
            }
        )
        
        # 重複登録を試行
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "duplicate@example.com",
                "password": "TestPass123@",
                "full_name": "Second User"
            }
        )
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]
    
    def test_user_registration_weak_password(self, test_client: TestClient):
        """弱いパスワードでの登録テスト"""
        response = test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "full_name": "Weak User"
            }
        )
        
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "at least 8 characters" in str(data["detail"])
    
    def test_login_success(self, test_client: TestClient):
        """正常なログインテスト"""
        # ユーザー登録
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "TestPass123@",
                "full_name": "Login User"
            }
        )
        
        # ログインテスト
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "login@example.com",
                "password": "TestPass123@"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0
    
    def test_login_invalid_credentials(self, test_client: TestClient):
        """無効な認証情報でのログインテスト"""
        # ユーザー登録
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid@example.com",
                "password": "TestPass123@",
                "full_name": "Invalid User"
            }
        )
        
        # 無効なパスワードでログイン
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "invalid@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, test_client: TestClient):
        """存在しないユーザーでのログインテスト"""
        response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "TestPass123@"
            }
        )
        
        assert response.status_code == 500
        assert "login failed" in response.json()["detail"]
    
    def test_get_current_user_success(self, test_client: TestClient):
        """認証済みユーザー情報取得テスト"""
        # ユーザー登録
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "current@example.com",
                "password": "TestPass123@",
                "full_name": "Current User"
            }
        )
        
        # ログインしてトークン取得
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "current@example.com",
                "password": "TestPass123@"
            }
        )
        token = login_response.json()["access_token"]
        
        # 認証済みユーザー情報取得
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "current@example.com"
        assert data["full_name"] == "Current User"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_get_current_user_invalid_token(self, test_client: TestClient):
        """無効なトークンでの認証テスト"""
        response = test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]
    
    def test_get_current_user_no_token(self, test_client: TestClient):
        """トークンなしでの認証テスト"""
        response = test_client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_logout_success(self, test_client: TestClient):
        """正常なログアウトテスト"""
        # ユーザー登録
        test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "TestPass123@",
                "full_name": "Logout User"
            }
        )
        
        # ログインしてトークン取得
        login_response = test_client.post(
            "/api/v1/auth/login",
            data={
                "username": "logout@example.com",
                "password": "TestPass123@"
            }
        )
        token = login_response.json()["access_token"]
        
        # ログアウト
        response = test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"
    
    def test_logout_invalid_token(self, test_client: TestClient):
        """無効なトークンでのログアウトテスト"""
        response = test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]