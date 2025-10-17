# ホスト初期設定メモ

1. Python 仮想環境を作成
   ```bash
   cd agent
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt  # or poetry install
   ```

2. パッチ用ディレクトリ・hook を設定
   ```bash
   ./host-tools/configure-hooks.sh
   source .patch_env
   ```

3. runtime を起動
   ```bash
   ./host-tools/run_runtime.sh
   ```

4. ブラウザで http://127.0.0.1:8080/ui を開き、ステータスやパッチ操作を確認できる。

5. `PATCH_WORKSPACE` 配下に git worktree 用の一時ディレクトリが作成される（既定 `$HOME/.yamada6`）。

6. Docker を使う場合も `.patch_env` を読み込んでから `./host-tools/start.sh` を実行する。

7. staging からは `PATCH_APPLY_MODE` を `noop` または `fail` に設定して挙動をテストできる。
