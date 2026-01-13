import flet as ft
import danbooru_api
import threading
import os
import datetime
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
        
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            # outputディレクトリ内のフォルダを取得
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    # ダウンロード日時を取得
                    download_date = downloaded_data.get(item, "")
                    if download_date:
                        display_text = f"{item}\n({download_date})"
                    else:
                        display_text = item
                    
                    # 各アーティストフォルダをクリック可能で追加
                    artist_btn = ft.TextButton(
                        content=ft.Text(display_text, size=11, text_align=ft.TextAlign.LEFT),
                        on_click=lambda e, name=item: search_from_list(name),
                        style=ft.ButtonStyle(
                            padding=ft.Padding(8, 4, 8, 4),
                        ),
                    )
                    artist_list.content.controls.append(artist_btn)
        page.update()
    
    # リストからアーティストを検索
    def search_from_list(artist_name):
        left_panel.controls[1].value = artist_name
        api_ret = danbooru_api.getArtistInfobyName(page, artist_name)
        if api_ret != []:
            right_upper_panel.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
            right_upper_panel.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
            right_upper_panel.controls[0].controls[2].controls[0].value = format_date(api_ret[0]["created_at"])
            right_upper_panel.controls[0].controls[2].controls[1].value = format_date(api_ret[0]["updated_at"])
            right_upper_panel.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
            right_upper_panel.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
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
            if api_ret != []:
                right_upper_panel.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
                right_upper_panel.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
                right_upper_panel.controls[0].controls[2].controls[0].value = format_date(api_ret[0]["created_at"])
                right_upper_panel.controls[0].controls[2].controls[1].value = format_date(api_ret[0]["updated_at"])
                right_upper_panel.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
                right_upper_panel.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
                page.update()
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
    
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
        if right_upper_panel.controls[0].controls[1].controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("先にアーティスト名検索をしてください。"), duration=3000))
        else:
            artist_name = right_upper_panel.controls[0].controls[1].controls[1].value
            is_banned = right_upper_panel.controls[0].controls[3].controls[1].value
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
    page.window.min_width = 1024
    page.window.min_height = 576
    page.padding = 0
    
    # アーティストリスト用のコンテナ
    artist_list = ft.Container(
        content=ft.Column(
            controls=[],
            spacing=2,
            expand=True,
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
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
        expand=1
    )
    right_upper_panel=ft.Row(
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.START,
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
                    height=136,
                    on_click=download_items,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.BLUE,
                        shape=ft.RoundedRectangleBorder(radius=8),
                        padding=20,
                    ),
                ),
                expand=True,
            ),
        ],
        expand=1,
    )
    right_middle_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Container(
                content=None,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=8,
                padding=4,
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
                padding=4,
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
    main_content = ft.Row(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            left_panel,
            right_panel_column,
        ],
        expand=True,
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