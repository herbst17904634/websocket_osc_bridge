#!/usr/bin/env python3
"""
WebSocket to OSC ブリッジモジュール
WebSocketで受信したメッセージをOSCで送信する
"""

import asyncio
import logging
from typing import Dict
from config import Config
from osc_client import OSCClient
from websocket_server import WebSocketServer

class WebSocketOSCBridge:
    """WebSocket to OSC ブリッジクラス"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = Config(config_file)
        self.osc_client = OSCClient(self.config.osc_ip, self.config.osc_port)
        self.websocket_server = WebSocketServer(self.config.websocket_port, self.handle_websocket_message)
        self.is_running = False
        self.last_message_time = 0
        self.timeout_seconds = self.config.timeout_seconds
        self.timeout_task = None
        self.loop = None
        self.last_values = {}  # 最後に送信した値を保持
    
    async def _reset_timeout(self) -> None:
        """タイムアウトをリセット"""
        if self.timeout_task:
            self.timeout_task.cancel()
        self.timeout_task = asyncio.create_task(self._check_timeout())
    
    async def _check_timeout(self) -> None:
        """タイムアウトチェック"""
        try:
            await asyncio.sleep(self.timeout_seconds)
            # タイムアウト発生時に0を送信
            if self.last_values:
                logging.info(f"{self.timeout_seconds}秒間の入力がなかったため、0を送信します")
                zero_values = {channel: 0.0 for channel in self.last_values}
                if self.osc_client.is_connected():
                    # 現在の値を0に更新してから送信
                    for channel in self.last_values:
                        self.last_values[channel] = 0.0
                    self.osc_client.send_multiple_values(zero_values)
                    logging.debug(f"タイムアウト: 0を送信: {zero_values}")
                self.last_values.clear()
        except asyncio.CancelledError:
            # タスクがキャンセルされた場合は何もしない
            logging.debug("タイムアウトタスクがキャンセルされました")
            raise
        except Exception as e:
            logging.error(f"タイムアウト処理中にエラーが発生しました: {e}")
            raise
    
    async def handle_websocket_message(self, data: Dict[str, float]) -> None:
        """
        WebSocketメッセージを処理してOSCで送信
        
        Args:
            data: {tag: strength} の辞書
        """
        logging.debug(f"WebSocketメッセージ受信: {data}")
        
        # タグをチャンネルにマッピングしてOSC送信
        channel_values = {}
        has_non_zero = False
        
        for tag, strength in data.items():
            channel = self.config.get_channel_for_tag(tag)
            if channel is not None:
                channel_values[channel] = strength
                self.last_values[channel] = strength  # 最後の値を記録
                if strength > 0:
                    has_non_zero = True
                logging.debug(f"マッピング: {tag} -> チャンネル {channel} = {strength}")
            else:
                logging.warning(f"未設定のタグ: {tag}")
        
        # 0以外の値があればタイマーをリセット
        if has_non_zero:
            if self.timeout_task and not self.timeout_task.done():
                self.timeout_task.cancel()
            self.timeout_task = asyncio.create_task(self._check_timeout())
        
        # OSCで送信
        if channel_values and self.osc_client.is_connected():
            success = self.osc_client.send_multiple_values(channel_values)
            if success:
                logging.debug(f"OSC送信成功: {channel_values}")
            else:
                logging.error("OSC送信失敗")
        elif not self.osc_client.is_connected():
            logging.warning("OSCクライアントが接続されていません")
    
    def update_osc_target(self, ip: str, port: int = 8000) -> bool:
        """OSC送信先を更新"""
        self.config.set_osc_target(ip, port)
        return self.osc_client.update_target(ip, port)
    
    def add_tag_mapping(self, tag: str, channel: int) -> None:
        """タグマッピングを追加"""
        self.config.add_tag_mapping(tag, channel)
    
    def remove_tag_mapping(self, tag: str) -> None:
        """タグマッピングを削除"""
        self.config.remove_tag_mapping(tag)
    
    def save_config(self) -> None:
        """設定を保存"""
        self.config.save_config()
    
    def get_status(self) -> dict:
        """ブリッジの状態を取得"""
        return {
            'websocket_running': self.is_running,
            'websocket_clients': self.websocket_server.get_client_count(),
            'osc_connected': self.osc_client.is_connected(),
            'osc_target': self.config.get_osc_target(),
            'tag_mappings': self.config.tag_channel_map.copy(),
            'timeout_seconds': self.timeout_seconds
        }
    
    async def start(self) -> None:
        """ブリッジを開始"""
        logging.info("WebSocket to OSC ブリッジを開始します...")
        self.loop = asyncio.get_event_loop()
        self.is_running = True
        
        # OSC接続確認
        if not self.osc_client.is_connected():
            logging.info("OSCクライアントが未接続のため再接続を試行します…")
            if self.osc_client.connect():
                logging.info("OSCクライアント再接続成功")
            else:
                logging.warning("OSCクライアントの接続に失敗しました")
        
        # 既存のタイムアウトタスクをクリア
        if self.timeout_task and not self.timeout_task.done():
            self.timeout_task.cancel()
        
        # WebSocketサーバー開始
        try:
            await self.websocket_server.start_server()
            # 初期タイムアウトタスクを開始
            self.timeout_task = asyncio.create_task(self._check_timeout())
            logging.info("タイムアウト監視を開始しました")
        except Exception as e:
            logging.error(f"WebSocketサーバーエラー: {e}")
            self.is_running = False
            raise
    
    async def stop(self) -> None:
        """ブリッジを停止"""
        logging.info("WebSocket to OSC ブリッジを停止します...")
        try:
            # タイムアウトタスクをキャンセル
            if self.timeout_task:
                self.timeout_task.cancel()
                try:
                    await self.timeout_task
                except asyncio.CancelledError:
                    pass
                self.timeout_task = None
                
            # WebSocketサーバーを停止
            if hasattr(self, 'websocket_server') and self.websocket_server:
                await self.websocket_server.stop_server()
                
            # 最後に0を送信
            if self.last_values and self.osc_client.is_connected():
                zero_values = {channel: 0.0 for channel in self.last_values}
                self.osc_client.send_multiple_values(zero_values)
                logging.debug(f"停止時に0を送信: {zero_values}")
                
        except Exception as e:
            logging.error(f"ブリッジ停止中にエラーが発生しました: {e}")
        finally:
            self.osc_client.disconnect()
            self.is_running = False
            self.last_values.clear()

if __name__ == "__main__":
    # テスト用コード
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=== WebSocket to OSC ブリッジテスト ===")
    print("ブリッジを開始します...")
    print("WebSocket: ws://localhost:3031/haptic")
    print("OSC送信先: 127.0.0.1:8000")
    print("Ctrl+C で停止")
    
    # ブリッジ作成
    bridge = WebSocketOSCBridge()
    
    # 状態表示
    status = bridge.get_status()
    print(f"設定状況:")
    print(f"  OSC送信先: {status['osc_target']}")
    print(f"  タグマッピング: {status['tag_mappings']}")
    
    try:
        # ブリッジ開始
        asyncio.run(bridge.start())
    except KeyboardInterrupt:
        print("\nブリッジを停止します...")
        asyncio.run(bridge.stop())
    except Exception as e:
        print(f"エラー: {e}")

