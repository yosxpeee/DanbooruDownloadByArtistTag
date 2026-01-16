import flet as ft

from settings import SettingsManager
from left_panel import LeftPanel
from right_panel import RightPanel

def main(page: ft.Page):
    """Danbooru crawler by artist tag - メインエントリーポイント"""
    # メインウインドウの設定
    page.title = "Danbooru crawler by artist tag"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.settings = SettingsManager.load()
    page.window.width = 1280
    page.window.height = 720
    page.window.min_width = 1280
    page.window.min_height = 720
    page.padding = 0
    
    # ログ表示用の関数
    def append_log(message):
        """ログをTextFieldに追加する"""
        right_panel.log_panel.value += f"{message}\n"
        page.update()
    
    # ダウンロード完了後のコールバック
    def on_download_complete():
        """ダウンロード完了時に選护状態をクリア"""
        left_pane.clear_selection()
    
    # 右パネルのコールバックを設定
    right_panel = RightPanel(page)
    right_panel.set_log_callback(append_log)
    right_panel.set_download_complete_callback(on_download_complete)
    
    # 左パネルのコールバックを設定
    left_pane = LeftPanel(page, right_panel)
    left_pane.set_log_callback(append_log)
    
    # 右パネルのオーバーレイを取得
    overlay = right_panel.get_overlay()
    
    # 設定をGUIで管理
    username_text = ft.TextField(
        value=page.settings["account"]["username"],
        label="ユーザー名",
        hint_text="Danbooruユーザー名",
        text_size=12,
        expand=True,
    )
    api_key_text = ft.TextField(
        value=page.settings["account"]["api_key"],
        label="APIキー",
        hint_text="Danbooru APIキー",
        text_size=12,
        password=True,
        can_reveal_password=True,
        expand=True,
    )
    
    # 設定ダイアログ
    def show_settings_dialog():
        """
        show_settings_dialog の Docstring
        """
        dialog = ft.AlertDialog(
            title=ft.Text("設定"),
            content=ft.Column(
                controls=[
                    ft.Text("アカウント", size=14, weight=ft.FontWeight.BOLD),
                    username_text,
                    api_key_text,
                ],
                spacing=16,
                height=200,
            ),
            actions=[
                ft.TextButton(
                    "キャンセル",
                    on_click=lambda e: (setattr(dialog, 'open', False), page.update()),
                ),
                ft.TextButton(
                    "保存",
                    on_click=lambda e: save_settings(e, dialog),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True,
        )
        page.show_dialog(dialog)
    
    # 設定保存
    def save_settings(e, dialog):
        page.settings["account"]["username"] = username_text.value
        page.settings["account"]["api_key"] = api_key_text.value
        SettingsManager.save(page.settings)
        dialog.open = False
        page.show_dialog(ft.SnackBar(ft.Text("設定を保存しました"), duration=2000))
        page.update()
    
    # メニューバー作成
    menu_bar = ft.Row(
        controls=[
            ft.MenuBar(
                expand=True,
                controls=[
                    ft.SubmenuButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SETTINGS, size=20, color=ft.Colors.BLACK),
                            ft.Text("設定", weight=ft.FontWeight.W_600, size=14),
                        ]),
                        key="submenubutton",
                        controls=[
                            ft.MenuItemButton(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.ACCOUNT_BOX, size=18, color=ft.Colors.BLACK),
                                    ft.Text("アカウント", weight=ft.FontWeight.W_400, size=12),
                                ]),
                                on_click=lambda e: show_settings_dialog(),
                            ),
                        ],
                        menu_style=ft.MenuStyle(
                            bgcolor=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=0),
                            padding=0,
                        ),
                    ),
                ],
                style=ft.MenuStyle(
                    alignment=ft.Alignment.TOP_LEFT,
                    bgcolor=ft.Colors.WHITE,
                    mouse_cursor=ft.MouseCursor.CLICK,
                    shape=ft.RoundedRectangleBorder(radius=0),
                    padding=0,
                ),
            )
        ]
    )
    
    # ページへパネルを追加
    main_content = ft.Column(
        controls=[
            menu_bar,
            ft.Divider(),
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    left_pane.get_control(),
                    right_panel.get_control(),
                ],
                expand=True,
            ),
        ],
        expand=True,
        spacing=0,
    )
    
    # オーバーレイを含むStack
    page.add(
        ft.Stack(
            controls=[
                main_content,
                overlay,
            ],
            expand=True,
        )
    )
    
    # 起動時にアーティスト一覧を読み込み
    left_pane.load_artist_list()


if __name__ == "__main__":
    ft.app(target=main)