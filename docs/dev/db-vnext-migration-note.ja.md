# vNext DB baseline 移行ノート

記録日: 2026-07-15

## pre-vNextスキーマの保存先

- Git tag: `db-schema-pre-vnext-202607`
- tag種別: annotated tag
- remote: `origin`
- tag object: `5c25179be2d8dbe3118cf10260f7406814af0bb2`
- 対象commit: `382920e4559150059f38160250aa04544c331101`
- 旧Alembic head: `20260709001`
- 保存revision数: 19

`origin`上のタグとローカルのannotated tag objectが一致し、タグのpeeled commitが対象commitを指すことをDB-00で確認した。タグ対象commitの`components/koiki_ref_app/alembic/versions/`に旧revision 19本が保存されている。

## 互換性の境界

- vNextは空のPostgreSQL DBから再作成する。
- 旧revisionからvNext baselineへのupgrade経路は提供しない。
- vNextから旧スキーマへのdowngrade経路は提供しない。
- vNext baselineのdowngradeは空DBへ戻す用途だけを保証する。
- 旧DBの再現や調査が必要な場合は、このタグから旧revision一式を参照する。

## 確認コマンド

```powershell
git fetch origin tag db-schema-pre-vnext-202607
git rev-parse db-schema-pre-vnext-202607
git rev-parse 'db-schema-pre-vnext-202607^{}'
git ls-tree -r --name-only 'db-schema-pre-vnext-202607^{}' -- components/koiki_ref_app/alembic/versions
git show 'db-schema-pre-vnext-202607^{}:components/koiki_ref_app/alembic/versions/20260709001_add_version_to_todos_table.py'
```

旧履歴を実行する必要がある場合は、作業中のvNext treeへ旧revisionを混在させず、タグから分離したworktreeまたは一時branchを作成して扱う。
