#!/usr/bin/env python3
"""
WebSocket to OSC Bridge - Flet GUI Application
モダンなWebアプリケーションとしてのGUI実装
"""

import flet as ft
import asyncio
import threading
import logging
from typing import Optional
from bridge import WebSocketOSCBridge

class WebSocketOSCBridgeApp:
    """Flet GUI アプリケーションクラス"""
    
    def __init__(self):
        self.bridge: Optional[WebSocketOSCBridge] = None
        self.bridge_thread: Optional[threading.Thread] = None
        self.bridge_loop: Optional[asyncio.AbstractEventLoop] = None
        self.is_bridge_running = False
        
        # UI コンポーネント
        self.page: Optional[ft.Page] = None
        self.tag_input: Optional[ft.TextField] = None
        self.channel_dropdown: Optional[ft.Dropdown] = None
        self.tag_list: Optional[ft.ListView] = None
        self.osc_ip_input: Optional[ft.TextField] = None
        self.osc_port_input: Optional[ft.TextField] = None
        self.status_text: Optional[ft.Text] = None
        self.ws_status_chip: Optional[ft.Chip] = None
        self.osc_status_chip: Optional[ft.Chip] = None
        self.client_count_text: Optional[ft.Text] = None
        self.log_text: Optional[ft.Text] = None
        self.start_button: Optional[ft.ElevatedButton] = None
        self.stop_button: Optional[ft.ElevatedButton] = None
    
    def main(self, page: ft.Page):
        """メインアプリケーション"""
        self.page = page
        self.page.title = "WebSocket to OSC Bridge"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.window_width = 1200
        self.page.window_height = 800
        self.page.window_resizable = True
        
        # ブリッジ初期化
        self.bridge = WebSocketOSCBridge()
        
        # UI構築
        self.build_ui()
        self.update_display()
        
        # 定期更新タイマー
        self.page.run_task(self.periodic_update)
    
    def build_ui(self):
        """UI構築"""
        # ヘッダー
        header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.SETTINGS_INPUT_ANTENNA, size=40, color=ft.Colors.BLUE_400),
                ft.Text("WebSocket to OSC Bridge", size=28, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                self.create_status_indicators()
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=20,
            # bgcolor=ft.Colors.SURFACE_VARIANT,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=10,
            margin=ft.margin.only(bottom=20)
        )
        
        # メインコンテンツ
        main_content = ft.Row([
            # 左パネル - 設定
            ft.Container(
                content=ft.Column([
                    self.create_tag_mapping_panel(),
                    ft.Divider(height=20),
                    self.create_osc_settings_panel(),
                ], scroll=ft.ScrollMode.AUTO),
                width=400,
                padding=20
            ),
            
            ft.VerticalDivider(width=1),
            
            # 右パネル - 制御とログ
            ft.Container(
                content=ft.Column([
                    self.create_control_panel(),
                    ft.Divider(height=20),
                    self.create_log_panel(),
                ], scroll=ft.ScrollMode.AUTO),
                expand=True,
                padding=20
            )
        ], expand=True)
        
        # ページに追加
        self.page.add(
            header,
            main_content
        )
    
    def create_status_indicators(self):
        """ステータスインジケーター作成"""
        self.ws_status_chip = ft.Chip(
            label=ft.Text("WebSocket: 停止中"),
            bgcolor=ft.Colors.RED_100,
            color=ft.Colors.RED_800
        )
        
        self.osc_status_chip = ft.Chip(
            label=ft.Text("OSC: 未接続"),
            bgcolor=ft.Colors.RED_100,
            color=ft.Colors.RED_800
        )
        
        self.client_count_text = ft.Text("接続数: 0", size=14)
        
        return ft.Column([
            ft.Row([self.ws_status_chip, self.osc_status_chip]),
            self.client_count_text
        ], horizontal_alignment=ft.CrossAxisAlignment.END)
    
    def create_tag_mapping_panel(self):
        """タグマッピングパネル作成"""
        self.tag_input = ft.TextField(
            label="タグ名",
            width=150,
            hint_text="例: tag1"
        )
        
        self.channel_dropdown = ft.Dropdown(
            label="チャンネル",
            width=100,
            options=[ft.dropdown.Option(str(i)) for i in range(16)]
        )
        
        add_button = ft.IconButton(
            icon=ft.Icons.ADD,
            tooltip="タグマッピング追加",
            on_click=self.add_tag_mapping
        )
        
        self.tag_list = ft.ListView(
            height=200,
            spacing=5
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("タグ・チャンネル設定", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.tag_input, self.channel_dropdown, add_button]),
                ft.Text("現在の設定:", size=14, weight=ft.FontWeight.W_500),
                self.tag_list,
                ft.Row([
                    ft.ElevatedButton("設定保存", on_click=self.save_config),
                    ft.ElevatedButton("設定リロード", on_click=self.reload_config)
                ])
            ]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=15,
            border_radius=10
        )
    
    def create_osc_settings_panel(self):
        """OSC設定パネル作成"""
        self.osc_ip_input = ft.TextField(
            label="送信先IP",
            value="127.0.0.1",
            width=200
        )
        
        self.osc_port_input = ft.TextField(
            label="送信先ポート",
            value="8000",
            width=100
        )
        
        update_button = ft.ElevatedButton(
            "OSC設定更新",
            on_click=self.update_osc_settings
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("OSC送信設定", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.osc_ip_input, self.osc_port_input]),
                update_button
            ]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=15,
            border_radius=10
        )
    
    def create_control_panel(self):
        """制御パネル作成"""
        self.start_button = ft.ElevatedButton(
            "ブリッジ開始",
            icon=ft.Icons.PLAY_ARROW,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600,
            on_click=self.start_bridge
        )
        
        self.stop_button = ft.ElevatedButton(
            "ブリッジ停止",
            icon=ft.Icons.STOP,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_600,
            on_click=self.stop_bridge,
            disabled=True
        )
        
        test_button = ft.ElevatedButton(
            "テスト送信",
            icon=ft.Icons.SEND,
            on_click=self.test_send
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("制御", size=18, weight=ft.FontWeight.BOLD),
                ft.Row([self.start_button, self.stop_button, test_button]),
                ft.Divider(),
                ft.Text("WebSocketエンドポイント:", size=14, weight=ft.FontWeight.W_500),
                ft.SelectionArea(content=ft.Text("ws://localhost:3031/haptic", size=12, color=ft.Colors.BLUE_400))
            ]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=15,
            border_radius=10
        )
    
    def create_log_panel(self):
        """ログパネル作成"""
        self.log_text = ft.Text(
            "ログ出力がここに表示されます...",
            size=12,
            selectable=True
        )
        
        log_container = ft.Container(
            content=ft.Column([self.log_text], scroll=ft.ScrollMode.AUTO),
            height=300,
            bgcolor=ft.Colors.BLACK12,
            padding=10,
            border_radius=5
        )
        
        clear_button = ft.TextButton("ログクリア", on_click=self.clear_log)
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("ログ出力", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    clear_button
                ]),
                log_container
            ]),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            padding=15,
            border_radius=10
        )
    
    def add_tag_mapping(self, e):
        """タグマッピング追加"""
        tag = self.tag_input.value
        channel = self.channel_dropdown.value
        
        if not tag or channel is None:
            self.show_snackbar("タグ名とチャンネルを入力してください", ft.colors.RED_400)
            return
        
        try:
            channel_int = int(channel)
            self.bridge.add_tag_mapping(tag, channel_int)
            self.log_message(f"タグマッピング追加: {tag} -> チャンネル {channel_int}")
            self.update_tag_list()
            
            # 入力フィールドクリア
            self.tag_input.value = ""
            self.channel_dropdown.value = None
            self.page.update()
            
        except Exception as ex:
            self.show_snackbar(f"エラー: {ex}", ft.colors.RED_400)
    
    def update_osc_settings(self, e):
        """OSC設定更新"""
        try:
            ip = self.osc_ip_input.value
            port = int(self.osc_port_input.value)
            
            success = self.bridge.update_osc_target(ip, port)
            if success:
                self.log_message(f"OSC送信先更新: {ip}:{port}")
                self.show_snackbar("OSC設定を更新しました", ft.colors.GREEN_400)
            else:
                self.show_snackbar("OSC接続に失敗しました", ft.colors.RED_400)
                
        except Exception as ex:
            self.show_snackbar(f"エラー: {ex}", ft.colors.RED_400)
    
    def start_bridge(self, e):
        """ブリッジ開始"""
        if self.is_bridge_running:
            return
        
        def run_bridge():
            self.bridge_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.bridge_loop)
            try:
                self.bridge_loop.run_until_complete(self.bridge.start())
            except Exception as ex:
                self.log_message(f"ブリッジエラー: {ex}")
            finally:
                self.bridge_loop.close()
        
        self.bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        self.bridge_thread.start()
        self.is_bridge_running = True
        
        # ボタン状態更新
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.page.update()
        
        self.log_message("ブリッジを開始しました")
    
    def stop_bridge(self, e):
        """ブリッジ停止"""
        if not self.is_bridge_running:
            return
        
        if self.bridge_loop:
            asyncio.run_coroutine_threadsafe(self.bridge.stop(), self.bridge_loop)
        
        self.is_bridge_running = False
        
        # ボタン状態更新
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.page.update()
        
        self.log_message("ブリッジを停止しました")
    
    def test_send(self, e):
        """テスト送信"""
        try:
            test_data = {"tag1": 0.5, "tag2": 0.8}
            asyncio.run(self.bridge.handle_websocket_message(test_data))
            self.log_message(f"テストメッセージ送信: {test_data}")
            self.show_snackbar("テストメッセージを送信しました", ft.Colors.GREEN_400)
        except Exception as ex:
            self.show_snackbar(f"テスト送信エラー: {ex}", ft.Colors.RED_400)
    
    def save_config(self, e):
        """設定保存"""
        try:
            self.bridge.save_config()
            self.log_message("設定を保存しました")
            self.show_snackbar("設定を保存しました", ft.Colors.GREEN_400)
        except Exception as ex:
            self.show_snackbar(f"保存エラー: {ex}", ft.Colors.RED_400)
    
    def reload_config(self, e):
        """設定リロード"""
        try:
            self.bridge.config.load_config()
            self.update_display()
            self.log_message("設定をリロードしました")
            self.show_snackbar("設定をリロードしました", ft.Colors.GREEN_400)
        except Exception as ex:
            self.show_snackbar(f"リロードエラー: {ex}", ft.Colors.RED_400)
    
    def clear_log(self, e):
        """ログクリア"""
        self.log_text.value = ""
        self.page.update()
    
    def update_display(self):
        """表示更新"""
        if not self.bridge:
            return
        
        # OSC設定表示更新
        self.osc_ip_input.value = self.bridge.config.osc_ip
        self.osc_port_input.value = str(self.bridge.config.osc_port)
        
        # タグリスト更新
        self.update_tag_list()
        
        # ステータス更新
        self.update_status()
        
        self.page.update()
    
    def update_tag_list(self):
        """タグリスト更新"""
        self.tag_list.controls.clear()
        
        for tag, channel in self.bridge.config.tag_channel_map.items():
            item = ft.ListTile(
                title=ft.Text(f"{tag} → チャンネル {channel}"),
                trailing=ft.IconButton(
                    icon=ft.Icons.DELETE,
                    tooltip="削除",
                    on_click=lambda e, t=tag: self.remove_tag_mapping(t)
                )
            )
            self.tag_list.controls.append(item)
    
    def remove_tag_mapping(self, tag: str):
        """タグマッピング削除"""
        try:
            self.bridge.remove_tag_mapping(tag)
            self.log_message(f"タグマッピング削除: {tag}")
            self.update_tag_list()
            self.page.update()
        except Exception as ex:
            self.show_snackbar(f"削除エラー: {ex}", ft.Colors.RED_400)
    
    def update_status(self):
        """ステータス更新"""
        status = self.bridge.get_status()
        
        # WebSocketステータス
        if status['websocket_running']:
            self.ws_status_chip.label.value = "WebSocket: 動作中"
            self.ws_status_chip.bgcolor = ft.Colors.GREEN_100
            self.ws_status_chip.color = ft.Colors.GREEN_800
        else:
            self.ws_status_chip.label.value = "WebSocket: 停止中"
            self.ws_status_chip.bgcolor = ft.Colors.RED_100
            self.ws_status_chip.color = ft.Colors.RED_800
        
        # OSCステータス
        if status['osc_connected']:
            self.osc_status_chip.label.value = "OSC: 接続中"
            self.osc_status_chip.bgcolor = ft.Colors.GREEN_100
            self.osc_status_chip.color = ft.Colors.GREEN_800
        else:
            self.osc_status_chip.label.value = "OSC: 未接続"
            self.osc_status_chip.bgcolor = ft.Colors.RED_100
            self.osc_status_chip.color = ft.Colors.RED_800
        
        # クライアント数
        self.client_count_text.value = f"接続数: {status['websocket_clients']}"
    
    def log_message(self, message: str):
        """ログメッセージ追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        if self.log_text.value:
            self.log_text.value += f"\n{log_line}"
        else:
            self.log_text.value = log_line
        
        self.page.update()
    
    def show_snackbar(self, message: str, color: str):
        """スナックバー表示"""
        snackbar = ft.SnackBar(
            content=ft.Text(message),
            bgcolor=color
        )
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    async def periodic_update(self):
        """定期更新"""
        while True:
            await asyncio.sleep(2)
            if self.bridge:
                self.update_status()
                self.page.update()

def main():
    """アプリケーション起動"""
    app = WebSocketOSCBridgeApp()
    ft.app(target=app.main, view=ft.AppView.WEB_BROWSER, port=8080)

if __name__ == "__main__":
    main()

