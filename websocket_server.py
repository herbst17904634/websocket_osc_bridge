#!/usr/bin/env python3
"""
WebSocketサーバーモジュール
buttplug-lite互換のWebSocketサーバーを提供
"""

import asyncio
import logging
import websockets
from websockets.server import WebSocketServerProtocol
from typing import Set, Callable, Optional
import re

class WebSocketServer:
    """WebSocketサーバークラス"""
    
    def __init__(self, port: int = 3031, message_handler: Optional[Callable] = None):
        self.port = port
        self.message_handler = message_handler
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.server = None
        self.is_running = False
    
    def set_message_handler(self, handler: Callable) -> None:
        """メッセージハンドラーを設定"""
        self.message_handler = handler
    
    async def register_client(self, websocket: WebSocketServerProtocol) -> None:
        """クライアント接続を登録"""
        self.connected_clients.add(websocket)
        logging.info(f"クライアント接続: {websocket.remote_address}")
    
    async def unregister_client(self, websocket: WebSocketServerProtocol) -> None:
        """クライアント接続を解除"""
        self.connected_clients.discard(websocket)
        logging.info(f"クライアント切断: {websocket.remote_address}")
    
    def parse_message(self, message: str) -> dict:
        """
        受信メッセージを解析
        
        Args:
            message: "tag:strength" または "tag1:strength1;tag2:strength2" 形式
        
        Returns:
            {tag: strength} の辞書
        """
        result = {}
        
        # セミコロンで分割して複数のコマンドを処理
        commands = message.strip().split(';')
        
        for command in commands:
            command = command.strip()
            if not command:
                continue
            
            # "tag:strength" 形式をパース
            parts = command.split(':')
            if len(parts) == 2:
                tag = parts[0].strip()
                try:
                    strength = float(parts[1].strip())
                    # 0.0-1.0の範囲にクランプ
                    strength = max(0.0, min(1.0, strength))
                    result[tag] = strength
                except ValueError:
                    logging.warning(f"無効な強度値: {parts[1]}")
            else:
                logging.warning(f"無効なコマンド形式: {command}")
        
        return result
    
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str = "/haptic") -> None:
        """クライアント接続を処理"""
        # Check if the path is /haptic
        if path != "/haptic":
            logging.warning(f"Invalid path: {path}")
            await websocket.close()
            return
            
        await self.register_client(websocket)
        
        try:
            async for message in websocket:
                logging.debug(f"受信メッセージ: {message}")
                
                # メッセージを解析
                parsed_data = self.parse_message(message)
                
                if parsed_data and self.message_handler:
                    # メッセージハンドラーを呼び出し
                    try:
                        await self.message_handler(parsed_data)
                    except Exception as e:
                        logging.error(f"メッセージハンドラーエラー: {e}")
                
        except websockets.exceptions.ConnectionClosed as e:
            logging.info(f"クライアント接続が閉じられました: {e}")
            # 自動再接続処理
            if e.code == 1006:  # アブノーマルな切断
                await asyncio.sleep(5)  # 5秒待機
                try:
                    await websocket.close()
                except Exception as reconnect_error:
                    logging.error(f"再接続エラー: {reconnect_error}")
        except Exception as e:
            logging.error(f"クライアント処理エラー: {e}")
            # エラー時は5秒待機して再試行
            await asyncio.sleep(5)
        finally:
            await self.unregister_client(websocket)
    
    async def start_server(self) -> None:
        """サーバーを開始"""
        try:
            # サーバー設定: 長いタイムアウトと自動再接続
            self.server = await websockets.serve(
                self.handle_client,
                "0.0.0.0",  # すべてのインターフェースでリッスン
                self.port,
                ping_interval=60,  # 1分ごとにping
                ping_timeout=30,   # 30秒のタイムアウト
                close_timeout=30,  # 30秒のクローズタイムアウト
                max_size=2**20,    # 1MBの最大メッセージサイズ
                max_queue=1000,    # 1000メッセージのキュー
                read_limit=2**20,  # 1MBの読み取り制限
                write_limit=2**20   # 1MBの書き込み制限
            )
            self.is_running = True
            logging.info(f"WebSocketサーバー開始: ポート {self.port}")
            
            # サーバーが終了するまで待機
            try:
                await self.server.wait_closed()
            except Exception as e:
                logging.error(f"サーバー終了エラー: {e}")
                # エラー時は5秒待機して再試行
                await asyncio.sleep(5)
                # サーバーを再起動
                await self.start_server()
            
        except Exception as e:
            logging.error(f"サーバー開始エラー: {e}")
            self.is_running = False
    
    async def stop_server(self) -> None:
        """サーバーを停止"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.is_running = False
            logging.info("WebSocketサーバー停止")
    
    def get_client_count(self) -> int:
        """接続中のクライアント数を取得"""
        return len(self.connected_clients)

# テスト用のメッセージハンドラー
async def test_message_handler(data: dict) -> None:
    """テスト用メッセージハンドラー"""
    print(f"受信データ: {data}")
    for tag, strength in data.items():
        print(f"  {tag}: {strength}")

if __name__ == "__main__":
    # テスト用コード
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== WebSocketサーバーテスト ===")
    print("サーバーを開始します...")
    print("テスト用クライアントで ws://localhost:3031/haptic に接続してください")
    print("メッセージ例: tag1:0.5 または tag1:0.5;tag2:0.8")
    print("Ctrl+C で停止")
    
    # サーバー作成
    server = WebSocketServer(3031, test_message_handler)
    
    try:
        # サーバー開始
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("\nサーバーを停止します...")
    except Exception as e:
        print(f"エラー: {e}")

