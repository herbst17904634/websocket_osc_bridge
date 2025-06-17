# WebSocket to OSC Bridge - プロジェクト概要

## 開発完了日
2025年6月15日

## プロジェクト概要
buttplug-lite互換のWebSocketサーバーでモーター強度を受け取り、OSCプロトコルでデバイスに送信するPythonアプリケーションです。

## 主要機能
✓ WebSocketサーバー（ポート3031）でモーター強度受信
✓ OSCクライアントでハプティック値送信
✓ PySimpleGUI使用のGUI設定画面
✓ タグ・チャンネルマッピング設定
✓ OSC送信先IP/ポート設定
✓ 設定の保存・読み込み機能
✓ リアルタイム状態表示

## ファイル構成

### 主要ファイル
- `main.py` - メインアプリケーション（GUI/CLIモード対応）
- `bridge.py` - WebSocket-OSCブリッジ機能
- `gui.py` - GUI設定画面
- `config.py` - 設定管理
- `websocket_server.py` - WebSocketサーバー
- `osc_client.py` - OSCクライアント

### 設定・ドキュメント
- `requirements.txt` - 依存ライブラリ
- `config.json` - 設定ファイル（自動生成）
- `README.md` - 使用方法説明書
- `PROJECT_OVERVIEW.md` - このファイル

### テスト・開発用
- `test_libraries.py` - ライブラリ動作確認
- `test_client.py` - WebSocketクライアントテスト
- `final_test.py` - 最終動作確認
- `integration_test.py` - 統合テスト
- `library_analysis.md` - ライブラリ調査結果

## 使用方法

### 基本起動
```bash
python main.py
```

### CLIモード
```bash
python main.py --cli
```

### 詳細ログ
```bash
python main.py --verbose
```

## WebSocket API
- エンドポイント: `ws://localhost:3031`
- メッセージ形式: `tag:strength` または `tag1:strength1;tag2:strength2`
- strength範囲: 0.0-1.0

## OSC出力
- メッセージ形式: `/avatar/parameters/haptira/channel/XX/value,f`
- XX: チャンネル番号（00-15）
- f: float32値（0.0-1.0）

## 動作確認済み
✓ 設定管理機能
✓ WebSocket受信機能
✓ OSC送信機能
✓ GUI操作機能
✓ メッセージ変換機能
✓ エラーハンドリング

## 技術仕様
- Python 3.11以上
- websockets 15.0.1
- python-osc 1.9.3
- PySimpleGUI 5.0.8.3
- 非同期処理対応
- クロスプラットフォーム対応

## 開発者
Manus AI Agent

