"""Browser-session completion endpoints for application-specific identity providers."""

from fastapi import APIRouter, Request, Response

from koiki_ref_app.api.v1.endpoints import saml_auth, sso_auth
from koiki_ref_app.schemas.saml import SAMLLoginTicketRequest
from koiki_ref_app.schemas.sso import SSOLoginRequest
from libkoiki.api.dependencies import DBSessionDep
from libkoiki.core.browser_session import require_browser_csrf, set_auth_cookies, set_csrf_cookie
from libkoiki.schemas.browser_session import BrowserSessionResponse

router = APIRouter(prefix="/browser")


@router.post("/sso/login", response_model=BrowserSessionResponse)
async def browser_sso_login(
    request: Request,
    response: Response,
    payload: SSOLoginRequest,
    sso_service: sso_auth.SSOServiceDep,
    db: DBSessionDep,
) -> BrowserSessionResponse:
    """Exchange an OIDC code without returning internal tokens to JavaScript."""
    require_browser_csrf(request)
    token_pair = await sso_auth.sso_login(
        request=request,
        sso_request=payload,
        sso_service=sso_service,
        db=db,
    )
    set_auth_cookies(
        response,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )
    set_csrf_cookie(response)
    return BrowserSessionResponse(message="SSO login successful", expires_in=token_pair.expires_in)


@router.post("/saml/login", response_model=BrowserSessionResponse)
async def browser_saml_login(
    request: Request,
    response: Response,
    payload: SAMLLoginTicketRequest,
    saml_service: saml_auth.SAMLServiceDep,
    db: DBSessionDep,
) -> BrowserSessionResponse:
    """Exchange a validated SAML ticket without returning internal tokens."""
    require_browser_csrf(request)
    token_pair = await saml_auth.saml_login(
        request=request,
        login_request=payload,
        saml_service=saml_service,
        db=db,
    )
    set_auth_cookies(
        response,
        access_token=token_pair.access_token,
        refresh_token=token_pair.refresh_token,
    )
    set_csrf_cookie(response)
    return BrowserSessionResponse(message="SAML login successful", expires_in=token_pair.expires_in)
