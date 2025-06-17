#!/usr/bin/env python3
"""
設定管理モジュール
タブ名とチャンネル番号のマッピング、OSC送信先IPなどの設定を管理
"""

import json
import os
from typing import Dict, Optional

class Config:
    """設定管理クラス"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.tag_channel_map: Dict[str, int] = {}
        self.osc_ip: str = "127.0.0.1"
        self.osc_port: int = 8080
        self.websocket_port: int = 3031
        self.load_config()
    
    def load_config(self) -> None:
        """設定ファイルから設定を読み込み"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tag_channel_map = data.get('tag_channel_map', {})
                    self.osc_ip = data.get('osc_ip', '127.0.0.1')
                    self.osc_port = data.get('osc_port', 8080)
                    self.websocket_port = data.get('websocket_port', 3031)
                print(f"設定を読み込みました: {self.config_file}")
            except Exception as e:
                print(f"設定ファイル読み込みエラー: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def save_config(self) -> None:
        """設定をファイルに保存"""
        try:
            data = {
                'tag_channel_map': self.tag_channel_map,
                'osc_ip': self.osc_ip,
                'osc_port': self.osc_port,
                'websocket_port': self.websocket_port
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"設定を保存しました: {self.config_file}")
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")
    
    def _create_default_config(self) -> None:
        """デフォルト設定を作成"""
        self.tag_channel_map = {
            "a": 0,
            "b": 1,
            "c": 3
        }
        self.osc_ip = "127.0.0.1"
        self.osc_port = 8080
        self.websocket_port = 3031
        self.save_config()
    
    def add_tag_mapping(self, tag: str, channel: int) -> None:
        """タグとチャンネルのマッピングを追加"""
        if 0 <= channel <= 15:
            self.tag_channel_map[tag] = channel
            print(f"マッピング追加: {tag} -> チャンネル {channel}")
        else:
            raise ValueError("チャンネル番号は0-15の範囲で指定してください")
    
    def remove_tag_mapping(self, tag: str) -> None:
        """タグマッピングを削除"""
        if tag in self.tag_channel_map:
            del self.tag_channel_map[tag]
            print(f"マッピング削除: {tag}")
    
    def get_channel_for_tag(self, tag: str) -> Optional[int]:
        """タグに対応するチャンネル番号を取得"""
        return self.tag_channel_map.get(tag)
    
    def set_osc_target(self, ip: str, port: int = 8080) -> None:
        """OSC送信先を設定"""
        self.osc_ip = ip
        self.osc_port = port
        print(f"OSC送信先設定: {ip}:{port}")
    
    def get_osc_target(self) -> tuple:
        """OSC送信先を取得"""
        return (self.osc_ip, self.osc_port)

if __name__ == "__main__":
    # テスト用コード
    config = Config()
    print("=== 設定テスト ===")
    print(f"タグマッピング: {config.tag_channel_map}")
    print(f"OSC送信先: {config.get_osc_target()}")
    print(f"WebSocketポート: {config.websocket_port}")

