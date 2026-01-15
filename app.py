import flet as ft
import threading
import os
import datetime

import danbooru_api
from settings import SettingsManager
from downloaded_list import DownloadedListManager

def main(page: ft.Page):
    # ログ表示用の関数
    def append_log(message):
        """ログをTextFieldに追加する"""
        log_text.value += f"{message}\n"
        page.update()
    
    # 日付形式を変換する関数
    def format_date(date_str):
        """ISO 8601形式の日付文字列を YYYY/MM/DD hh:mm:ss 形式に変換"""
        if not date_str:
            return ""
        try:
            dt = datetime.datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except:
            return date_str
    
    # outputディレクトリから既存のアーティストタグリストを取得
    def load_artist_list():
        artist_list.content.controls.clear()
        output_dir = "output"
        
        # downloaded_list.jsonのデータを取得
        downloaded_data = DownloadedListManager.load()
        
        # ヘッダー行（見出し）
        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(content=ft.Text("削除", size=12), width=40, alignment=ft.Alignment.CENTER),  # 削除ボタン列
                    ft.Container(content=ft.Text("アーティスト名", size=12, weight=ft.FontWeight.BOLD), alignment=ft.Alignment.CENTER, expand=True),
                    ft.Container(content=ft.Text("更新日", size=12, weight=ft.FontWeight.BOLD), width=140),
                ],
                spacing=8,
            ),
            padding=ft.Padding(4, 4, 4, 4),
            bgcolor=ft.Colors.GREY_200,
            border_radius=4,
        )
        artist_list.content.controls.append(header_row)
        
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            # outputディレクトリ内のフォルダを取得
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    # ダウンロード日時を取得
                    download_date = downloaded_data.get(item, "")
                    
                    # 削除ボタン
                    delete_btn = ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=20,
                        icon_color=ft.Colors.RED_400,
                        tooltip="削除",
                        on_click=lambda e, name=item: delete_artist(name),
                    )
                    
                    # アーティスト名（クリック可能）
                    artist_name_btn = ft.TextButton(
                        content=ft.Text(item, size=12),
                        on_click=lambda e, name=item: search_from_list(name),
                        style=ft.ButtonStyle(
                            padding=ft.Padding(8, 4, 8, 4),
                        ),
                    )
                    
                    # 更新日表示
                    date_text = ft.Text(download_date if download_date else "-", size=12)
                    
                    # 1行分のRow
                    row = ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(content=delete_btn, width=40),
                                ft.Container(content=artist_name_btn, expand=True),
                                ft.Container(content=date_text, width=140),
                            ],
                            spacing=8,
                        ),
                        padding=ft.Padding(4, 4, 4, 4),
                    )
                    artist_list.content.controls.append(row)
        
        page.update()
    
    # リストからアーティストを検索
    def search_from_list(artist_name):
        left_panel.controls[1].value = artist_name
        api_ret = danbooru_api.getArtistInfobyName(page, artist_name)
        tag_counts = danbooru_api.getTagCounts(page, artist_name.replace(" ", "_"))
        if api_ret != []:
            right_upper_panel.controls[0].content.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
            right_upper_panel.controls[0].content.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
            right_upper_panel.controls[0].content.controls[0].controls[2].controls[0].value = format_date(api_ret[0]["created_at"])
            right_upper_panel.controls[0].content.controls[0].controls[2].controls[1].value = format_date(api_ret[0]["updated_at"])
            right_upper_panel.controls[0].content.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
            right_upper_panel.controls[0].content.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
            right_upper_panel.controls[0].content.controls[0].controls[3].controls[3].value = "Posts："+str(tag_counts["counts"]["posts"])
            page.show_dialog(ft.SnackBar(ft.Text(f"「{artist_name}」を表示しました"), duration=2000))
        else:
            page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
        page.update()
    
    # アーティスト名検索
    def search_artistname(e):
        if left_panel.controls[1].controls[0].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("アーティスト名を入れてください。"), duration=3000))
        else:
            api_ret = danbooru_api.getArtistInfobyName(page, left_panel.controls[1].controls[0].value)
            tag_counts = danbooru_api.getTagCounts(page, left_panel.controls[1].controls[0].value.replace(" ", "_"))
            if api_ret != []:
                right_upper_panel.controls[0].content.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
                right_upper_panel.controls[0].content.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
                right_upper_panel.controls[0].content.controls[0].controls[2].controls[0].value = format_date(api_ret[0]["created_at"])
                right_upper_panel.controls[0].content.controls[0].controls[2].controls[1].value = format_date(api_ret[0]["updated_at"])
                right_upper_panel.controls[0].content.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
                right_upper_panel.controls[0].content.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
                right_upper_panel.controls[0].content.controls[0].controls[3].controls[3].value = "Posts："+str(tag_counts["counts"]["posts"])
                page.update()
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
    
    # アーティストの削除処理
    def delete_artist(artist_name):
        """ダウンロード済みのアーティストを削除する"""
        import shutil
        
        # 確認ダイアログ
        def confirm_delete(e, dialog):
            # ダイアログを閉じる
            dialog.open = False
            page.update()
            
            # ダウンロード済みデータから削除
            DownloadedListManager.remove_artist(artist_name)
            
            # outputディレクトリ内のフォルダを削除
            output_dir = "output"
            artist_path = os.path.join(output_dir, artist_name)
            if os.path.exists(artist_path):
                shutil.rmtree(artist_path)
                append_log(f"削除完了: {artist_name}")
            else:
                append_log(f"フォルダ見つかりず: {artist_name}")
            
            # リストを再読み込み
            load_artist_list()
            page.show_dialog(ft.SnackBar(ft.Text(f"「{artist_name}」を削除しました"), duration=2000))
            page.update()
        
        # 確認求めるダイアログ
        dialog = ft.AlertDialog(
            title=ft.Text("削除確認"),
            content=ft.Text(f"「{artist_name}」のフォルダとデータを削除しますか？\n（元に戻せません）"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("削除", on_click=lambda e: confirm_delete(e, dialog)),
            ],
        )
        page.show_dialog(dialog)
    
    # ダウンロード処理を行う関数（別スレッドで実行）
    def run_download(artist_name, is_banned):
        try:
            if is_banned == True:
                append_log("エラー: 削除されたアーティストタグです")
                page.show_dialog(ft.SnackBar(ft.Text("削除されたアーティストタグなのでダウンロードできません。"), duration=3000))
                overlay.visible = False
                page.update()
                return
            # ダウンロード処理を実行（log_callbackを追加）
            total = danbooru_api.downloadItems(page, artist_name, log_callback=append_log)
            
            # 完了後のUI更新
            def on_complete():
                # 更新日を取得して保存
                api_ret = danbooru_api.getArtistInfobyName(page, artist_name)
                if api_ret != []:
                    updated_date = format_date(api_ret[0]["updated_at"])
                    DownloadedListManager.update_artist(artist_name, updated_date)
                
                overlay.visible = False
                append_log(f"完了: {total}枚ダウンロードしました")
                page.show_dialog(ft.SnackBar(ft.Text(f"download finished. {total}枚"), duration=3000))
                # アーティストリストを再読み込み
                load_artist_list()
                page.update()
            
            page.run_thread(on_complete)
            
        except Exception as e:
            error_msg = str(e)
            def on_error():
                append_log(f"エラー: {error_msg}")
                overlay.visible = False
                page.show_dialog(ft.SnackBar(ft.Text(f"Error: {error_msg}"), duration=3000))
                page.update()
            page.run_thread(on_error)
    
    # ダウンロードボタンのクリック処理
    def download_items(e):
        if right_upper_panel.controls[0].content.controls[0].controls[1].controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("先にアーティスト名検索をしてください。"), duration=3000))
        else:
            artist_name = right_upper_panel.controls[0].content.controls[0].controls[1].controls[1].value
            is_banned = right_upper_panel.controls[0].content.controls[0].controls[3].controls[1].value
            # オーバーレイを表示
            overlay.visible = True
            page.update()
            
            # 別スレッドでダウンロードを開始
            download_thread = threading.Thread(target=run_download, args=(artist_name, is_banned))
            download_thread.daemon = True
            download_thread.start()
    
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
        log_text.value += f"{message}\n"
        page.update()
    
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
    
    # アーティストリスト用のコンテナ
    artist_list = ft.Container(
        content=ft.Column(
            controls=[],
            spacing=2,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            scroll=ft.ScrollMode.AUTO,
        ),
        expand=True,
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=8,
        padding=8,
    )
    
    # オーバーレイUIの作成
    overlay = ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.DOWNLOAD, size=64, color=ft.Colors.WHITE),
                ft.Text("ダウンロード中...", size=16, color=ft.Colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20,
        ),
        bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY),
        visible=False,
        alignment=ft.Alignment.CENTER,
        expand=True,
        margin=0,
        padding=0,
    )
    
    # ログ表示用TextField
    log_text = ft.TextField(
        value="",
        multiline=True,
        min_lines=8,
        expand=True,
        read_only=True,
        bgcolor=ft.Colors.GREY_50,
        text_size=12,
        border_color=ft.Colors.GREY_400,
        content_padding=ft.Padding(8, 8, 8, 8),
    )
    # Containerでラップしてスクロール可能にする
    log_container = ft.Container(
        content=log_text,
        expand=True,
        border=ft.border.all(1, ft.Colors.GREY_400),
        border_radius=8,
        padding=4,
    )
    log_text._container = log_container  # 循環参照を避けるため、weakref的な方法が必要
    
    # 各パネル
    left_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Text("アーティストタグ", size=12),
            ft.Row(
                controls=[
                    ft.TextField(label="Artist Tag", hint_text="input artist tag", text_size=12, expand=True),
                ]  
            ),
            ft.TextButton(
                content="検索",
                icon=ft.Icons.SEARCH,
                icon_color=ft.Colors.BLUE_300,
                on_click=search_artistname,
            ),
            ft.Divider(height=1, radius=0),
            ft.Text("既存のアーティスト一覧", size=12),
            artist_list,
        ],
        width=400,
    )
    right_upper_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.START,
                    vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    controls=[
                        ft.Column(
                            alignment=ft.MainAxisAlignment.START,
                            controls=[
                                ft.Text("アーティスト情報", size=12),
                                ft.Row(
                                    controls=[
                                        ft.TextField(label="ID", height=36, text_size=12, disabled=True),
                                        ft.TextField(label="アーティスト名", height=36,text_size=12, disabled=True),
                                    ],
                                    spacing=0,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.TextField(label="登録日", height=36,text_size=12, disabled=True),
                                        ft.TextField(label="更新日", height=36,text_size=12, disabled=True),
                                    ],
                                    spacing=0,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Checkbox(label="is deleted", value=False, disabled=True),
                                        ft.Checkbox(label="is banned", value=False, disabled=True),
                                        ft.Text(" | "),
                                        ft.Text("Posts："),
                                    ],
                                    spacing=0,
                                ),
                                ft.Row(
                                    controls=[
                                        ft.Text("※Postsと実際のダウンロード数は使用するアカウントの権限により一致しないことがあります。"),
                                    ],
                                    spacing=0,
                                ),
                            ],
                            expand=False,
                            spacing=6,
                        ),
                        ft.Container(
                            content=ft.FilledButton(
                                content=ft.Text("ダウンロード", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                                icon=ft.Icons.DOWNLOAD,
                                on_click=download_items,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE,
                                    shape=ft.RoundedRectangleBorder(radius=8),
                                    padding=20,
                                ),
                                expand=True,
                            ),
                            expand=True,
                        ),
                    ],
                ),
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=8,
                padding=2,
                height=200,
            )
        ],
        expand=False,
        spacing=0,
    )
    right_middle_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Container(
                content=None,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=8,
                padding=2,
            )
        ],
        expand=5,
        spacing=0,
    )
    right_lower_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Container(
                content=log_text,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=8,
                padding=2,
            )
        ],
        expand=1,
        spacing=0,
    )
    
    # 右側パネル全体をColumnで管理（上部、中央、下部）
    right_panel_column = ft.Column(
        controls=[
            right_upper_panel,
            right_middle_panel,
            right_lower_panel,
        ],
        expand=3,
    )
    
    # ページへパネルを追加
    main_content = ft.Column(
        controls=[
            menu_bar,
            ft.Divider(),
            ft.Row(
                alignment=ft.MainAxisAlignment.START,
                controls=[
                    left_panel,
                    right_panel_column,
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
    load_artist_list()