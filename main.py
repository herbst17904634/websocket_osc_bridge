#!/usr/bin/env python3
"""
WebSocket to OSC Bridge - Flet GUI Application
モダンなWebアプリケーションとしてのGUI実装
"""

import flet as ft
import logging
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
            label="OSC IPアドレス",
            value=self.bridge.config.osc_ip,
            width=200,
            on_submit=self.update_osc_target
        )
        self.osc_port_input = ft.TextField(
            label="OSCポート",
            value=str(self.bridge.config.osc_port),
            width=100,
            on_submit=self.update_osc_target,
            input_filter=ft.InputFilter(r"^\d+$", allow=True)
        )
        
        self.timeout_input = ft.TextField(
            label="タイムアウト (秒)",
            value=str(self.bridge.config.timeout_seconds),
            width=120,
            on_submit=self.update_timeout,
            input_filter=ft.InputFilter(r"^\d+$", allow=True)
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("OSC設定", size=20, weight=ft.FontWeight.BOLD),
                    ft.Row([self.osc_ip_input, self.osc_port_input]),
                    ft.ElevatedButton(
                        "適用",
                        on_click=self.update_osc_target,
                        icon=ft.Icons.SAVE
                    ),
                    ft.Divider(height=20),
                    ft.Text("タイムアウト設定", size=16, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.timeout_input,
                        ft.ElevatedButton(
                            "適用",
                            on_click=self.update_timeout,
                            icon=ft.Icons.TIMER
                        )
                    ], alignment=ft.MainAxisAlignment.START)
                ], spacing=10),
                padding=20
            ),
            elevation=2,
            margin=ft.margin.only(bottom=20)
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
        # ListView に変更して自動スクロールを有効化
        # ログを複数行選択コピーできるよう SelectionArea で包む
        self.log_list = ft.ListView(auto_scroll=True, expand=True, spacing=2)
        log_selection_area = ft.SelectionArea(content=self.log_list)
        # 初期メッセージ
        self.log_list.controls.append(ft.Text("ログ出力がここに表示されます...", size=12, selectable=True))
        
        log_container = ft.Container(
            content=log_selection_area,
            height=300,
            bgcolor=ft.Colors.BLACK12,
            padding=10,
            border_radius=5
        )
        
        clear_button = ft.TextButton("ログクリア", on_click=self.clear_log)
        copy_button = ft.TextButton("全文コピー", on_click=lambda e: self.page.set_clipboard('\n'.join([
            ctrl.value for ctrl in self.log_list.controls if isinstance(ctrl, ft.Text)
        ])))
        clear_button = ft.TextButton("ログクリア", on_click=self.clear_log)
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("ログ出力", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    copy_button,
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
    
    def update_osc_target(self, e=None):
        """OSC送信先を更新"""
        try:
            ip = self.osc_ip_input.value.strip()
            port = int(self.osc_port_input.value)
            if self.bridge.update_osc_target(ip, port):
                self.show_snackbar(f"OSC送信先を更新しました: {ip}:{port}")
                self.update_display()
            else:
                self.show_snackbar("OSC送信先の更新に失敗しました", is_error=True)
        except ValueError:
            self.show_snackbar("無効なポート番号です", is_error=True)
    
    def update_timeout(self, e=None):
        """タイムアウト時間を更新"""
        try:
            timeout = int(self.timeout_input.value)
            if timeout < 1:
                raise ValueError("1以上の値を指定してください")
                
            # ブリッジの設定を更新
            self.bridge.config.set_timeout_seconds(timeout)
            self.bridge.timeout_seconds = timeout
            
            # 設定を保存
            self.bridge.config.save_config()
            
            self.show_snackbar(f"タイムアウトを {timeout}秒 に設定しました")
            self.update_display()
            
        except ValueError as e:
            self.show_snackbar(f"無効なタイムアウト値です: {str(e)}", is_error=True)
    
    def start_bridge(self, e):
        """ブリッジ開始"""
        if self.is_bridge_running:
            return
        
        # 事前にイベントループを作成し参照を保持
        self.bridge_loop = asyncio.new_event_loop()

        def run_bridge():
            loop = self.bridge_loop
            asyncio.set_event_loop(loop)
            try:
                # ブリッジを開始
                self.bridge_loop.run_until_complete(self.bridge.start())
                # 以後はイベントループを走らせ続け、タイムアウトタスクなどを処理
                self.bridge_loop.run_forever()
            except Exception as ex:
                self.log_message(f"ブリッジエラー: {ex}")
            finally:
                # 停止指示で run_forever から抜けてきたらループを閉じる
                self.bridge_loop.close()
        
        self.bridge_thread = threading.Thread(target=run_bridge, daemon=True)
        self.bridge_thread.start()
        self.is_bridge_running = True
        
        # ボタン状態更新
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.page.update()
        # インジケーターを即更新
        self.update_status()
        self.log_message("ブリッジを開始しました")
    
    def stop_bridge(self, e):
        """ブリッジ停止"""
        if not self.is_bridge_running:
            return
        
        if not self.bridge_loop:
            self.log_message("ブリッジ初期化中のため停止できません。数秒後に再度お試しください")
            return

        if self.bridge_loop and not self.bridge_loop.is_closed():
            # ブリッジ停止コルーチンを実行
            fut = asyncio.run_coroutine_threadsafe(self.bridge.stop(), self.bridge_loop)
            # 停止完了後にイベントループを止める
            fut.add_done_callback(lambda _:
                                   self.bridge_loop.call_soon_threadsafe(self.bridge_loop.stop))
        
        self.is_bridge_running = False
        
        # ボタン状態更新
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.page.update()
        
        self.log_message("ブリッジを停止しました")
        # 停止完了後ステータスを更新
        self.update_status()
    
    def test_send(self, e):
        """テスト送信 - タイムアウトも適用されるようにブリッジのイベントループで実行"""
        try:
            test_data = {tag: 0.5 for tag in self.bridge.config.tag_channel_map}
            # ブリッジが動作中かつイベントループが有効な場合はそのループで送信
            if (self.is_bridge_running and self.bridge_loop 
                    and not self.bridge_loop.is_closed() 
                    and self.bridge_loop.is_running()):
                try:
                    fut = asyncio.run_coroutine_threadsafe(
                        self.bridge.handle_websocket_message(test_data),
                        self.bridge_loop
                    )
                    fut.result()  # エラーを拾うために短時間待機して例外を拾う
                except Exception as ex:
                    self.log_message(f"テスト送信エラー: {ex}")
            else:
                # ブリッジが動いていない場合: 非同期ループなしで送信し、タイマーで0送信をスケジュール
                asyncio.run(self.bridge.handle_websocket_message(test_data))

                # 既存のタイマーがあればキャンセル
                if hasattr(self, 'test_timeout_timer') and self.test_timeout_timer and self.test_timeout_timer.is_alive():
                    self.test_timeout_timer.cancel()

                def send_zeros_later():
                    zero_values = {ch: 0.0 for ch in self.bridge.config.tag_channel_map.values()}
                    if zero_values and self.bridge.osc_client.is_connected():
                        self.bridge.osc_client.send_multiple_values(zero_values)
                        logging.info(f"(テスト送信) タイムアウトで0を送信: {zero_values}")
                        # self.log_message(f"(テスト送信) タイムアウトで0を送信: {zero_values}")

                # 新しいタイマーを保持
                self.test_timeout_timer = threading.Timer(self.bridge.timeout_seconds, send_zeros_later)
                self.test_timeout_timer.start()
            logging.info(f"テストメッセージ送信: {test_data}")
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
        self.log_list.controls.clear()
        self.log_list.controls.append(ft.Text("ログ出力がここに表示されます...", size=12, selectable=True))
        self.page.update()
    
    def update_display(self):
        """表示を更新"""
        if not self.bridge:
            return
            
        # ステータス表示を更新
        status = self.bridge.get_status()
        self.ws_status_chip.label = ft.Text(
            "WebSocket: " + ("起動中" if status['websocket_running'] else "停止中"),
            color=ft.Colors.WHITE if status['websocket_running'] else ft.Colors.RED_200
        )
        self.osc_status_chip.label = ft.Text(
            "OSC: " + ("接続済み" if status['osc_connected'] else "未接続"),
            color=ft.Colors.WHITE if status['osc_connected'] else ft.Colors.RED_200
        )
        self.client_count_text.value = f"接続クライアント: {status['websocket_clients']}"

        # UI 更新
        self.page.update()
        
        # ボタンの有効/無効を更新
        is_running = status['websocket_running']
        self.start_button.disabled = is_running
        self.stop_button.disabled = not is_running
        
        # 設定を更新
        self.osc_ip_input.value = status['osc_target'][0]
        self.osc_port_input.value = str(status['osc_target'][1])
        self.timeout_input.value = str(self.bridge.config.timeout_seconds)
        
        # タグマッピングリストを更新
        self.update_tag_list()
        
        if self.page:
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

        # ページ更新
        self.page.update()
    
    def log_message(self, message: str):
        """ログメッセージ追加 (コピー可能)"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        # ListView へ追加し自動スクロール & コピー可能
        self.log_list.controls.append(ft.Text(log_line, size=12, selectable=True))
        self.page.update()
    async def periodic_update(self):
        """定期的にステータスと UI を更新"""
        while True:
            await asyncio.sleep(2)
            if self.bridge:
                self.update_status()
                self.page.update()

    def show_snackbar(self, message: str, color: str = ft.Colors.GREEN_400):
        snackbar = ft.SnackBar(content=ft.Text(message), bgcolor=color)
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()  

class _GuiLogHandler(logging.Handler):
    """Python logging handler that forwards records to the Flet GUI log panel."""
    def __init__(self, app_ref):
        super().__init__()
        self.app_ref: 'WebSocketOSCBridgeApp' = app_ref

    def emit(self, record: logging.LogRecord):
        """Forward log record to GUI thread safely."""
        try:
            msg = self.format(record)
            if self.app_ref.page is not None:
                try:
                    # If called from non-UI thread, schedule on UI thread
                    self.app_ref.page.call_from_thread(lambda: self.app_ref.log_message(msg))
                except Exception:
                    # Fallback: call directly (may already be on UI thread)
                    self.app_ref.log_message(msg)
            else:
                # Page not ready yet; store or ignore (no GUI to show yet)
                pass
        except Exception:
            # Ignore all errors to avoid disrupting logging flow
            pass

def main():
    """アプリケーション起動"""
    # Set up standard logging for console
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    app = WebSocketOSCBridgeApp()
    # Add GUI log handler so bridge logs appear in GUI
    gui_handler = _GuiLogHandler(app)
    gui_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(gui_handler)

    # Using a less common port to avoid conflicts (e.g., OSC default UDP port 8000)
    ft.app(target=app.main, view=ft.AppView.WEB_BROWSER, port=8550)

if __name__ == "__main__":
    main()

