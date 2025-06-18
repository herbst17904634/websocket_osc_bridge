# WebSocket to OSC Bridge

## 概要
buttplug-lite互換のWebSocketサーバーでモーター強度を受け取り、OSCプロトコルでデバイスに送信するPythonアプリケーションです。FletフレームワークによりモダンなWebアプリケーションとして実装されています。

## 特徴
- ✅ **モダンなWebUI**: Fletによるレスポンシブなダークテーマ
- ✅ **クロスプラットフォーム**: デスクトップ・Web両対応
- ✅ **リアルタイム制御**: WebSocket経由でのハプティック制御
- ✅ **OSC送信**: VRChat等への標準OSCプロトコル対応
- ✅ **設定管理**: タグ・チャンネルマッピングの柔軟な設定
- ✅ **永続デプロイ**: Webアプリケーションとして公開可能

## 公開URL
🌐 **ライブデモ**: https://8080-i1zri7kx70ag5vxv2dr5t-a0c48409.manusvm.computer

## ファイル構成

### 主要ファイル
- `main.py` - メインFletアプリケーション
- `test_app.py` - シンプルなテストアプリケーション
- `bridge.py` - WebSocket-OSCブリッジ機能
- `config.py` - 設定管理
- `websocket_server.py` - WebSocketサーバー
- `osc_client.py` - OSCクライアント

### 設定・ドキュメント
- `requirements.txt` - 依存ライブラリ
- `config.json` - 設定ファイル（自動生成）
- `README.md` - このファイル

## インストール・起動

### 依存関係インストール
```bash
pip install -r requirements.txt
```

### アプリケーション起動
```bash
# Webアプリケーションとして起動
python main.py

# テストアプリケーション起動
python test_app.py
```

### デスクトップアプリとして起動
```python
# main.py内で以下に変更
ft.app(target=main, view=ft.AppView.FLET_APP, port=8080)
```

## WebSocket API

### エンドポイント
- **URL**: `ws://localhost:3031`
- **プロトコル**: WebSocket

### メッセージ形式
```
# 単一タグ
tag1:0.5

# 複数タグ
tag1:0.5;tag2:0.8;tag3:0.2
```

### パラメーター
- **strength**: 0.0-1.0の範囲のfloat値

## OSC出力

### メッセージ形式
```
/avatar/parameters/haptira/channel/XX/value,f
```

### パラメーター
- **XX**: チャンネル番号（00-15）
- **f**: float32値（0.0-1.0）

## GUI機能

### 設定パネル
- タグ・チャンネルマッピング設定
- OSC送信先IP/ポート設定
- 設定の保存・読み込み

### 制御パネル
- ブリッジ開始/停止
- テスト送信
- リアルタイム状態表示

### ログパネル
- 動作ログのリアルタイム表示
- ログクリア機能

## 技術仕様

### フレームワーク
- **Flet**: 0.28.3以上
- **Python**: 3.11以上

### 依存ライブラリ
- `flet>=0.28.3` - Webアプリケーションフレームワーク
- `websockets>=15.0.1` - WebSocketサーバー
- `python-osc>=1.9.3` - OSCクライアント

### デプロイメント
- **ローカル**: `python main.py`
- **Web**: ポート8080で自動起動
- **永続化**: クラウドサービスでの継続運用可能

## 使用例

### VRChatでの使用
1. アプリケーションを起動
2. OSC送信先をVRChatのIPに設定
3. タグとチャンネルをマッピング
4. ブリッジを開始
5. WebSocketクライアントから制御

### 開発・テスト
1. テストアプリケーションで基本動作確認
2. WebSocketクライアントでAPI確認
3. OSC受信側でメッセージ確認

## ライセンス
MIT License

## 開発者
herbst17904634
このプログラムは主にManus AI Agentを用いて作成しました。

