# Agent Skill Smoke Checklist

Use each prompt in an agent-capable runtime and record the selected skills.

## ambiguous-layer-routing

Prompt: ユーザー管理の変更が必要ですが、libkoiki 側に置くべきか app 側に置くべきかまだ判断できません。最初に調査してください。

Expected skills: koiki-project-overview
Forbidden skills: koiki-app-feature-work, koiki-libkoiki-feature-work
Rationale: 変更レイヤが曖昧な依頼は最初に project overview で分類する。

Observed skills: 
Pass/Fail: 
Notes: 

## app-business-feature

Prompt: app の Todo API に承認フロー依存の業務ルールを追加してください。既存の libkoiki 共通機能は再利用したいです。

Expected skills: koiki-app-feature-work
Forbidden skills: koiki-project-overview, koiki-libkoiki-feature-work
Rationale: 業務固有の backend 変更は app feature work が第一候補。

Observed skills: 
Pass/Fail: 
Notes: 

## reusable-framework-capability

Prompt: 複数アプリで使える共通監査ロギング基盤を libkoiki に追加してください。app 固有の判断は入れないでください。

Expected skills: koiki-libkoiki-feature-work
Forbidden skills: koiki-project-overview, koiki-app-feature-work
Rationale: 再利用される共通基盤は libkoiki 側で扱う。

Observed skills: 
Pass/Fail: 
Notes: 

## auth-security-change

Prompt: JWT リフレッシュトークンの失効処理と RBAC の境界を見直したいです。セキュリティ回帰が怖いので確認してください。

Expected skills: koiki-auth-security
Forbidden skills: koiki-project-overview, koiki-app-feature-work, koiki-libkoiki-feature-work
Rationale: auth, token, RBAC を含む依頼は auth security を必ず起動対象にする。

Observed skills: 
Pass/Fail: 
Notes: 

## app-sso-change

Prompt: app の SAML SSO ログインフローを修正してください。必要なら app 層と libkoiki 層の両方を見てください。

Expected skills: koiki-auth-security, koiki-app-feature-work
Forbidden skills: (none)
Rationale: SSO/SAML は auth security を含みつつ、app 固有実装なら app feature も必要。

Observed skills: 
Pass/Fail: 
Notes: 

## framework-auth-change

Prompt: libkoiki のログイン試行制限とセキュリティ監査ログを強化してください。複数プロジェクトで再利用します。

Expected skills: koiki-auth-security, koiki-libkoiki-feature-work
Forbidden skills: (none)
Rationale: framework 層の security 変更は auth security と libkoiki feature の組み合わせ。

Observed skills: 
Pass/Fail: 
Notes: 

## test-scope-question

Prompt: この修正に unit test と integration test のどちらを追加すべきか判断して、そのまま必要なテストを書いてください。

Expected skills: koiki-testing
Forbidden skills: (none)
Rationale: テスト層の選定や追加が主目的なら testing を優先する。

Observed skills: 
Pass/Fail: 
Notes: 

## ci-test-coverage-scope

Prompt: CI でどのテストパスを回すべきか見直したいです。fixture と workflow の現状を踏まえて提案してください。

Expected skills: koiki-testing, koiki-project-overview
Forbidden skills: (none)
Rationale: CI とテストスコープの判断は testing 主導で、全体整理が要るなら project overview も併用。

Observed skills: 
Pass/Fail: 
Notes: 

## frontend-only-change

Prompt: frontend のタブ UI を調整してください。backend の変更は想定していません。

Expected skills: koiki-project-overview
Forbidden skills: koiki-app-feature-work, koiki-libkoiki-feature-work, koiki-auth-security, koiki-testing
Rationale: 現行 skill 集合に frontend 専用 skill はないため、まず overview で分類する。

Observed skills: 
Pass/Fail: 
Notes: 

