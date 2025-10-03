# tests/unit/app/services/test_saml_service.py
"""
SAMLServiceクラスの基本的なユニットテスト

SAML認証フローの主要機能をテスト
OIDCのテストパターンに合わせて設計
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from app.services.saml_service import SAMLService, ValidationException
from app.core.saml_config import SAMLSettings
from app.schemas.saml import SAMLUserInfo
from libkoiki.models.user import UserModel


class TestSAMLService:
    """SAMLServiceクラスのテストケース"""

    @pytest.fixture
    def mock_saml_settings(self):
        """モックSAML設定"""
        settings = Mock(spec=SAMLSettings)
        settings.SAML_SP_ENTITY_ID = "https://app.example.com/saml/metadata"
        settings.SAML_IDP_ENTITY_ID = "https://idp.example.com"
        settings.SAML_IDP_SSO_URL = "https://idp.example.com/saml/sso"
        settings.SAML_IDP_X509_CERT = "test-cert"
        settings.SAML_SP_ACS_URL = "https://app.example.com/saml/acs"
        settings.SAML_RELAY_STATE_SIGNING_KEY = "test-signing-key"
        settings.SAML_RELAY_STATE_TTL_SECONDS = 600
        settings.SAML_LOGIN_TICKET_TTL_SECONDS = 120
        settings.SAML_DEFAULT_REDIRECT_URI = "https://frontend.example.com/saml/callback"
        settings.SAML_ALLOWED_REDIRECT_URIS = "https://frontend.example.com/saml/callback"
        settings.SAML_AUTO_CREATE_USERS = True
        settings.SAML_DEFAULT_PROVIDER = "saml"

        # メソッドをモック
        settings.validate_required_settings.return_value = True
        settings.is_domain_allowed.return_value = True
        settings.get_attribute_mapping.return_value = {
            "email": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "name": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        }
        settings.get_saml_sp_settings.return_value = {"entityId": "test-sp"}
        settings.get_saml_idp_settings.return_value = {"entityId": "test-idp"}
        settings.get_saml_security_settings.return_value = {"wantAssertionsSigned": True}
        settings.resolve_redirect_uri.side_effect = lambda uri=None: uri or "https://frontend.example.com/saml/callback"

        return settings

    @pytest.fixture
    def mock_user_service(self):
        """モックユーザーサービス"""
        return Mock()

    @pytest.fixture
    def mock_auth_service(self):
        """モック認証サービス"""
        service = Mock()
        service.create_token_pair = AsyncMock(return_value=("access_token", "refresh_token", 3600))
        return service

    @pytest.fixture
    def saml_service(self, mock_user_service, mock_auth_service, mock_saml_settings):
        """SAMLServiceインスタンス"""
        with patch('app.services.saml_service.PYTHON3_SAML_AVAILABLE', True):
            service = SAMLService(
                user_service=mock_user_service,
                auth_service=mock_auth_service,
                saml_settings=mock_saml_settings,
            )
            # リポジトリもモック化
            service.user_sso_repository = Mock()
            from app.services import saml_service as saml_module
            saml_module._LOGIN_TICKET_CACHE.clear()
            return service

    def test_init_success(self, mock_user_service, mock_auth_service, mock_saml_settings):
        """SAMLService初期化成功テスト"""
        with patch('app.services.saml_service.PYTHON3_SAML_AVAILABLE', True):
            service = SAMLService(
                user_service=mock_user_service,
                auth_service=mock_auth_service,
                saml_settings=mock_saml_settings,
            )

            assert service.user_service == mock_user_service
            assert service.auth_service == mock_auth_service
            assert service.saml_settings == mock_saml_settings

    def test_init_missing_signing_key(self, mock_user_service, mock_auth_service):
        """署名キー未設定時の初期化失敗テスト"""
        settings = Mock(spec=SAMLSettings)
        settings.SAML_RELAY_STATE_SIGNING_KEY = ""

        with patch('app.services.saml_service.PYTHON3_SAML_AVAILABLE', True):
            with pytest.raises(RuntimeError, match="SAML RelayState signing key is required"):
                SAMLService(
                    user_service=mock_user_service,
                    auth_service=mock_auth_service,
                    saml_settings=settings,
                )

    def test_generate_authn_request_library_unavailable(self, saml_service):
        """ライブラリ未導入時のAuthnRequest生成失敗テスト"""
        with patch('app.services.saml_service.PYTHON3_SAML_AVAILABLE', False):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                saml_service.generate_authn_request()

            assert exc_info.value.status_code == 500
            assert "python3-saml is not available" in exc_info.value.detail

    def test_generate_authn_request_invalid_settings(self, saml_service):
        """設定不正時のAuthnRequest生成失敗テスト"""
        saml_service.saml_settings.validate_required_settings.return_value = False

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            saml_service.generate_authn_request()

        assert exc_info.value.status_code == 500
        assert "SAML configuration is incomplete" in exc_info.value.detail

    @patch('app.services.saml_service.OneLogin_Saml2_Settings')
    @patch('app.services.saml_service.OneLogin_Saml2_Auth')
    def test_generate_authn_request_success(self, mock_auth_class, mock_settings_class, saml_service):
        """AuthnRequest生成成功テスト"""
        # OneLogin_Saml2_Authのモック設定
        mock_auth = Mock()
        mock_auth.login.return_value = "https://idp.example.com/saml/sso?SAMLRequest=..."
        mock_auth.get_last_request_id.return_value = "REQ123"
        mock_auth.get_last_request_xml.return_value = "<samlp:AuthnRequest>...</samlp:AuthnRequest>"
        mock_auth_class.return_value = mock_auth
        mock_settings_class.return_value = Mock()

        result = saml_service.generate_authn_request(
            acs_url="https://app.example.com/saml/acs",
            redirect_uri="https://frontend.example.com/saml/callback",
        )

        assert "sso_url" in result
        assert "saml_request" in result
        assert "relay_state" in result
        assert "expires_at" in result
        assert result["sso_binding"] == "HTTP-Redirect"
        assert result["redirect_url"].startswith("https://idp.example.com/saml/sso")

    def test_validate_relay_state_token_invalid_format(self, saml_service):
        """RelayStateトークン形式不正テスト"""
        with pytest.raises(ValidationException, match="Invalid RelayState token format"):
            saml_service._validate_relay_state_token("invalid-token")

    def test_validate_relay_state_token_invalid_signature(self, saml_service):
        """RelayStateトークン署名不正テスト"""
        payload = {"nonce": "test-nonce", "req": "REQ123"}
        token, _ = saml_service._create_relay_state_token(payload)
        payload_part, _ = token.split(".")
        invalid_token = f"{payload_part}.invalid-signature"

        with pytest.raises(ValidationException, match="Invalid RelayState token signature"):
            saml_service._validate_relay_state_token(invalid_token)

    def test_create_relay_state_token_and_validate(self, saml_service):
        """RelayStateトークン作成と検証のラウンドトリップテスト"""
        payload = {"nonce": "test-nonce", "req": "REQ123", "return_to": "https://frontend.example.com/saml/callback"}
        token, expires_at = saml_service._create_relay_state_token(payload)

        validated_payload = saml_service._validate_relay_state_token(token)
        assert validated_payload["nonce"] == "test-nonce"
        assert validated_payload["req"] == "REQ123"

    def test_build_login_redirect_url(self, saml_service):
        base_url = "https://frontend.example.com/saml/callback"
        ticket = "ticket123"
        redirect_url = saml_service.build_login_redirect_url(base_url, ticket)

        assert redirect_url.startswith(base_url)
        assert "saml_ticket=ticket123" in redirect_url

    @pytest.mark.asyncio
    async def test_create_internal_token_pair_success(self, saml_service):
        """内部トークンペア作成成功テスト"""
        mock_user = Mock(spec=UserModel)
        mock_user.id = 123
        mock_db = Mock()

        access_token, refresh_token, expires_in = await saml_service.create_internal_token_pair(
            user=mock_user,
            db=mock_db,
            device_info="test-device"
        )

        assert access_token == "access_token"
        assert refresh_token == "refresh_token"
        assert expires_in == 3600

        # AuthServiceのcreate_token_pairが呼ばれたことを確認
        saml_service.auth_service.create_token_pair.assert_called_once_with(
            user=mock_user,
            db=mock_db,
            device_info="test-device"
        )

    @pytest.mark.asyncio
    async def test_create_internal_token_pair_failure(self, saml_service):
        """内部トークンペア作成失敗テスト"""
        mock_user = Mock(spec=UserModel)
        mock_user.id = 123
        mock_db = Mock()

        # AuthServiceでエラーが発生するようにモック
        saml_service.auth_service.create_token_pair.side_effect = Exception("Token creation failed")

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await saml_service.create_internal_token_pair(
                user=mock_user,
                db=mock_db
            )

        assert exc_info.value.status_code == 500
        assert "Token generation failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_exchange_login_ticket_success(self, saml_service):
        mock_db = Mock()
        mock_user = Mock(spec=UserModel)
        mock_user.id = 42
        mock_user.is_active = True

        saml_service.user_service.get_user_by_id = AsyncMock(return_value=mock_user)

        from fastapi import HTTPException

        relay_payload = {"nonce": "relay-nonce"}
        user_info = SAMLUserInfo(
            subject_id="user@example.com",
            email="user@example.com",
            email_verified=True,
        )
        login_ticket, expires_at, ticket_id = saml_service._create_login_ticket(
            user=mock_user,
            relay_state_payload=relay_payload,
            user_info=user_info,
        )

        user, access_token, refresh_token, expires_in = await saml_service.exchange_login_ticket(
            login_ticket=login_ticket,
            db=mock_db,
            device_info="test-device",
        )

        assert user == mock_user
        assert access_token == "access_token"
        assert refresh_token == "refresh_token"
        assert expires_in == 3600

        with pytest.raises(HTTPException) as exc_info:
            await saml_service.exchange_login_ticket(
                login_ticket=login_ticket,
                db=mock_db,
                device_info="test-device",
            )

        assert exc_info.value.status_code == 400
        assert "already used" in exc_info.value.detail

    def test_extract_attribute_value(self, saml_service):
        """SAML属性値抽出テスト"""
        attributes = {
            "email": ["user@example.com"],
            "name": ["Test User"],
            "empty": [],
            "multiple": ["value1", "value2"]
        }

        # 正常な属性抽出
        assert saml_service._extract_attribute_value(attributes, "email") == "user@example.com"
        assert saml_service._extract_attribute_value(attributes, "name") == "Test User"

        # 複数値の場合は最初の値
        assert saml_service._extract_attribute_value(attributes, "multiple") == "value1"

        # 存在しない属性
        assert saml_service._extract_attribute_value(attributes, "nonexistent") is None
        assert saml_service._extract_attribute_value(attributes, "nonexistent", "default") == "default"

        # 空の属性
        assert saml_service._extract_attribute_value(attributes, "empty") is None
        assert saml_service._extract_attribute_value(attributes, "empty", "default") == "default"

    def test_generate_dummy_password(self, saml_service):
        """ダミーパスワード生成テスト"""
        password = saml_service._generate_dummy_password()

        assert len(password) == 24
        assert isinstance(password, str)

        # 複数回生成して異なることを確認
        password2 = saml_service._generate_dummy_password()
        assert password != password2

    def test_build_saml_config(self, saml_service):
        """SAML設定構築テスト"""
        acs_url = "https://app.example.com/saml/acs"
        config = saml_service._build_saml_config(acs_url)

        assert "sp" in config
        assert "idp" in config
        assert "security" in config
        assert config["sp"]["assertionConsumerService"]["url"] == acs_url

    def test_create_fake_request(self, saml_service):
        """疑似リクエスト作成テスト"""
        # SAML Response無しの場合
        request = saml_service._create_fake_request()
        assert request["https"] == "on"
        assert request["http_host"] == "localhost"
        assert "post_data" in request
        assert "get_data" in request

        # SAML Response有りの場合
        saml_response = "test-saml-response"
        request = saml_service._create_fake_request(saml_response=saml_response)
        assert request["post_data"]["SAMLResponse"] == saml_response

    @pytest.mark.asyncio
    async def test_verify_saml_response_library_unavailable(self, saml_service):
        """ライブラリ未導入時のSAML Response検証失敗テスト"""
        with patch('app.services.saml_service.PYTHON3_SAML_AVAILABLE', False):
            from fastapi import HTTPException

            with pytest.raises(HTTPException) as exc_info:
                await saml_service.verify_saml_response(
                    saml_response="test-response",
                    relay_state="test-relay-state"
                )

            assert exc_info.value.status_code == 500
            assert "python3-saml is not available" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_saml_response_invalid_settings(self, saml_service):
        """設定不正時のSAML Response検証失敗テスト"""
        saml_service.saml_settings.validate_required_settings.return_value = False

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await saml_service.verify_saml_response(
                saml_response="test-response",
                relay_state="test-relay-state"
            )

        assert exc_info.value.status_code == 500
        assert "SAML configuration is incomplete" in exc_info.value.detail
