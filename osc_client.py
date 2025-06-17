#!/usr/bin/env python3
"""
OSCクライアントモジュール
OSCメッセージを送信する機能を提供
"""

import logging
from pythonosc import udp_client
from pythonosc.osc_message_builder import OscMessageBuilder
from typing import Optional

class OSCClient:
    """OSCクライアントクラス"""
    
    def __init__(self, ip: str = "127.0.0.1", port: int = 8000):
        self.ip = ip
        self.port = port
        self.client: Optional[udp_client.SimpleUDPClient] = None
        self.connect()
    
    def connect(self) -> bool:
        """OSCクライアントに接続"""
        try:
            self.client = udp_client.SimpleUDPClient(self.ip, self.port)
            logging.info(f"OSCクライアント接続: {self.ip}:{self.port}")
            return True
        except Exception as e:
            logging.error(f"OSCクライアント接続エラー: {e}")
            self.client = None
            return False
    
    def disconnect(self) -> None:
        """OSCクライアントを切断"""
        if self.client:
            self.client = None
            logging.info("OSCクライアント切断")
    
    def update_target(self, ip: str, port: int) -> bool:
        """送信先を更新"""
        self.ip = ip
        self.port = port
        self.disconnect()
        return self.connect()
    
    def send_haptic_value(self, channel: int, value: float) -> bool:
        """
        ハプティック値をOSCで送信
        
        Args:
            channel: チャンネル番号 (0-15)
            value: 強度値 (0.0-1.0)
        
        Returns:
            送信成功の場合True
        """
        if not self.client:
            logging.warning("OSCクライアントが接続されていません")
            return False
        
        if not (0 <= channel <= 15):
            logging.error(f"無効なチャンネル番号: {channel}")
            return False
        
        if not (0.0 <= value <= 1.0):
            logging.warning(f"値を0.0-1.0の範囲にクランプ: {value}")
            value = max(0.0, min(1.0, value))
        
        try:
            # OSCアドレス形式: /avatar/parameters/haptira/channel/XX/value
            channel_str = f"{channel:02d}"  # 2桁ゼロパディング
            osc_address = f"/avatar/parameters/haptira/channel/{channel_str}/value"
            
            # float32値として送信
            self.client.send_message(osc_address, value)
            logging.debug(f"OSC送信: {osc_address} = {value}")
            return True
            
        except Exception as e:
            logging.error(f"OSC送信エラー: {e}")
            return False
    
    def send_multiple_values(self, channel_values: dict) -> bool:
        """
        複数のチャンネルに値を一括送信
        
        Args:
            channel_values: {channel: value} の辞書
        
        Returns:
            すべて送信成功の場合True
        """
        success = True
        for channel, value in channel_values.items():
            if not self.send_haptic_value(channel, value):
                success = False
        return success
    
    def is_connected(self) -> bool:
        """接続状態を確認"""
        return self.client is not None

if __name__ == "__main__":
    # テスト用コード
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== OSCクライアントテスト ===")
    
    # OSCクライアント作成
    osc_client = OSCClient("127.0.0.1", 8000)
    
    if osc_client.is_connected():
        print("✓ OSCクライアント接続成功")
        
        # テスト送信
        print("テスト送信中...")
        osc_client.send_haptic_value(0, 0.5)
        osc_client.send_haptic_value(1, 0.8)
        osc_client.send_haptic_value(15, 0.2)
        
        # 複数値送信テスト
        test_values = {0: 0.1, 1: 0.3, 3: 0.7}
        osc_client.send_multiple_values(test_values)
        
        print("✓ テスト送信完了")
    else:
        print("✗ OSCクライアント接続失敗")
    
    osc_client.disconnect()

