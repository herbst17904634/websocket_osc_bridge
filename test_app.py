#!/usr/bin/env python3
"""
Flet テストアプリケーション
基本的なUIコンポーネントのテスト
"""

import flet as ft

def main(page: ft.Page):
    page.title = "WebSocket to OSC Bridge"
    page.theme_mode = ft.ThemeMode.DARK
    
    # シンプルなテストUI
    page.add(
        ft.AppBar(title=ft.Text("WebSocket to OSC Bridge")),
        ft.Text("Hello, Flet!", size=30),
        ft.ElevatedButton("テストボタン", on_click=lambda e: print("クリックされました"))
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8000)

