# Scenarioと証拠の対応

2026-10-27。チェック済みタスクは実施した事実のみ。実測範囲はLinux/amd64。OpenSpecはbackend9件/frontend9件と下表を1対1に対応させ、未確認の適用先を残して全体を完了にしない。PR発行・ドラフト作成・mainへのマージは行わない。

| Backend Scenario | 結果 | 根拠・限界 |
| --- | --- | --- |
| E1 収録証拠 | 確認 | version-selection.md、bootstrap JSON、node-brotli-official.json、built-images.json |
| E2 未収録版の誤完了防止 | 確認 | 3.13.17のpip対応と3.13.18のssl対応を分け、3.13.18実体で比較。未検証CI/CPUを残す |
| E3 OSバックポート | 確認 | bookworm libbrotli1=1.0.9-2+deb12u1、trixie=1.1.0-2+deb13u1、runtime-probes.json。上流版の大小だけで判定しない |
| S1 正規TLS/信頼 | 一部 | TLS200、OS/certifiのG3除去を実測。管理された実IdPのJWKS/SSO/SAML通信は未提供・未実測 |
| S2 不正証明書拒否 | 確認 | tls-results.json。未信頼CA・ホスト名不一致を拒否。侵害鍵実物による試験は行わず、ssl対策は公式配布の収録証拠も使う |
| S3 Brotli非搭載とOS分離 | 確認 | 完成backendのbrotli/brotlicffi/brotlipyはいずれも非搭載。OS部品とNodeのバックポート・定数を別に確認 |
| R1 回帰成功 | 確認（自動検証範囲） | JUnitで旧lock/更新lockとも328成功・1スキップ。wheel単独39パッケージの整合確認。実IdP合同試験の未検証はS1/別残件に保持 |
| R2 回帰検出時の停止 | 確認 | npm解決失敗・Nginx起動失敗・容量不足の段階で止め、原因修正後に該当検査を再実行。バックエンド新規失敗・スキップ増加なし |
| R3 版指定と実体の区別 | 一部 | 通常/unified/Dev Containerの実体・UID・IDを確認。CI実行・実配備CPU/arm64は未確認と記録 |

| Frontend Scenario | 結果 | 根拠・限界 |
| --- | --- | --- |
| F-E1 指摘分類 | 確認 | frontend-triage.jsonで18パッケージの親・勧告・旧新版を保存。消滅したtarは親依存更新で経路除去 |
| F-E2 未確認条件の扱い | 確認 | OS-BE/OS-FE/OS-DEV、VENDOR-PIP/NPMを未解消として明記。開発用という理由だけで除外しない |
| F-E3 RSC非搭載 | 確認 | createRoot/BrowserRouter、@vitejs/plugin-react、最終Nginxはdistのみ。RSC脆弱性の非到達とRouter更新を分ける |
| F-S1 クリーン再現 | 確認 | npm ci/check-types/lint/test/build成功、全依存/omit=dev監査0件。旧lockの別領域再現も成功 |
| F-S2 ロック/解決失敗 | 確認 | npm10.9.9のedgesOut内部エラーは完了扱いせず、npm11で対象指定解決。強制/legacy-peer-deps/overridesなし |
| F-S3 Nodeと最終OSを分離 | 確認 | Node内蔵Brotliの修正cherry-pickと機能定数、npm全体、Nginx最終OSを別検査。内蔵npmコピーは残件 |
| F-R1 認証/画面/SSO/SAML | 一部 | 21件のUI/transport/queryテストとbackend DB認証/CSRF等は成功。実ブラウザと管理された実IdPの合同フローは未実施 |
| F-R2 回帰切り分け | 確認 | Nginx権限失敗を検出し設定0644/資源UID101所有へ修正。再実行した両イメージのHTTPスモーク成功 |
| F-R3 静的配信 | 確認 | 通常/unifiedのhealth、/login、/tasks、/tasks/123の直接アクセス、JS資源配信を実測。Node非搭載も確認 |

## U01〜U08の分類

| 更新前タスク | 今回の判定 | 利用条件・根拠 |
| --- | --- | --- |
| U01 PyJWT/cryptography | 今回修正 | JWT認証とSSO鍵の検証で利用。PyJWKClientは利用せずアプリでJWKSを取得する。許容アルゴリズム/claimsを緩和せず2.15.1/50.0.2へ更新。optionsは呼出し毎のdict、採用版で不変性・期限拒否も確認 |
| U02 Starlette/multipart | 今回修正 | OAuth等のHTTP入口に関係。FastAPI公開依存条件を照合し上限を1.4未満へ変更、実auth/session/todos DB統合と既存拒否系を確認 |
| U03 Python/CA/pip/uv | 今回修正＋内蔵コピー別残件 | Python本体・certifi・OS・uv・pipを別照合。G3除去を実測。pipのCA対策とその他内蔵ライブラリ指摘は分ける |
| U04 anyio等 | 今回修正＋ツール内蔵別残件 | anyioはHTTP/TLSのruntime、urllib3/filelock/msgpackは監査/開発側。外側のlockを修正してもpip内部は変更されないことを記録 |
| U05 frontend18件 | 今回修正 | runtime Router/ZodとdevのVite/Vitest/親依存を別に更新。非RSCの構成根拠を保存し、全18件の更新/経路除去と監査0件を確認 |
| U06 root zod | 今回修正 | OpenSpec1.7.0の間接依存。root lockを別更新・npm ciし、root監査0件。SPAのZodとは別判定 |
| U07 イメージ/Keycloak | 今回検査＋OS/内蔵残件＋テストサービス分離 | 完成5種/Node depsを検査。修正提供のないOSと親ツール未修正内蔵コピーを残す。Keycloakは依頼者がテストIdP代替と明示、サービス更新はしない |
| U08 継続監査 | 別タスク | securityブランチ/main PRでfrontend CIが走るトリガーとnpm/uv版を整理。定期監査/更新通知/組織ポリシー化は別変更で検討。担当者・期限は未定であり本作業で設定を捏造しない |

「判定済み」は脆弱性全件の解消やリスク受容を意味しない。未検証/修正版待ちの追跡はREADMEの残件IDに従う。
