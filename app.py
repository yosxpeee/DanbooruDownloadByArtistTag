import flet as ft
import danbooru_api
import threading
import os
from settings import SettingsManager

def main(page: ft.Page):
    # outputディレクトリから既存のアーティストタグリストを取得
    def load_artist_list():
        artist_list.controls.clear()
        output_dir = "output"
        if os.path.exists(output_dir) and os.path.isdir(output_dir):
            # outputディレクトリ内のフォルダを取得
            for item in os.listdir(output_dir):
                item_path = os.path.join(output_dir, item)
                if os.path.isdir(item_path):
                    # 各アーティストフォルダをクリック可能で追加
                    artist_btn = ft.TextButton(
                        content=ft.Text(item, size=12),
                        on_click=lambda e, name=item: search_from_list(name),
                    )
                    artist_list.controls.append(artist_btn)
        page.update()
    
    # リストからアーティストを検索
    def search_from_list(artist_name):
        left_panel.controls[1].value = artist_name
        api_ret = danbooru_api.getArtistInfobyName(page, artist_name)
        if api_ret != []:
            right_upper_panel.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
            right_upper_panel.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
            right_upper_panel.controls[0].controls[2].controls[0].value = api_ret[0]["created_at"]
            right_upper_panel.controls[0].controls[2].controls[1].value = api_ret[0]["updated_at"]
            right_upper_panel.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
            right_upper_panel.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
            page.show_dialog(ft.SnackBar(ft.Text(f"「{artist_name}」を表示しました"), duration=2000))
        else:
            page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
        page.update()
    
    # アーティスト名検索
    def search_artistname(e):
        if left_panel.controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("アーティスト名を入れてください。"), duration=3000))
        else:
            api_ret = danbooru_api.getArtistInfobyName(page, left_panel.controls[1].value)
            if api_ret != []:
                right_upper_panel.controls[0].controls[1].controls[0].value = api_ret[0]["id"]
                right_upper_panel.controls[0].controls[1].controls[1].value = api_ret[0]["name"]
                right_upper_panel.controls[0].controls[2].controls[0].value = api_ret[0]["created_at"]
                right_upper_panel.controls[0].controls[2].controls[1].value = api_ret[0]["updated_at"]
                right_upper_panel.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
                right_upper_panel.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
                page.update()
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
    
    # ダウンロード処理を行う関数（別スレッドで実行）
    def run_download(artist_name):
        try:
            # ダウンロード処理を実行
            total = danbooru_api.downloadItems(page, artist_name)
            
            # 完了後のUI更新
            def on_complete():
                overlay.visible = False
                page.show_dialog(ft.SnackBar(ft.Text(f"download finished. {total}枚"), duration=3000))
                # アーティストリストを再読み込み
                load_artist_list()
                page.update()
            
            page.run_thread(on_complete)
            
        except Exception as e:
            def on_error():
                overlay.visible = False
                page.show_dialog(ft.SnackBar(ft.Text(f"Error: {str(e)}"), duration=3000))
                page.update()
            page.run_thread(on_error)
    
    # ダウンロードボタンのクリック処理
    def download_items(e):
        if right_upper_panel.controls[0].controls[0].controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("先にアーティスト名検索をしてください。"), duration=3000))
        else:
            artist_name = right_upper_panel.controls[0].controls[0].controls[1].value
            # オーバーレイを表示
            overlay.visible = True
            page.update()
            
            # 別スレッドでダウンロードを開始
            download_thread = threading.Thread(target=run_download, args=(artist_name,))
            download_thread.daemon = True
            download_thread.start()
    
    # メインウインドウの設定
    page.title = "danbooru clawler by artist"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.settings = SettingsManager.load()
    page.window_width = 1280
    page.window_height = 720
    page.padding = 0
    
    # アーティストリスト用のコンテナ
    artist_list = ft.Column(
        controls=[],
        spacing=2,
        expand=True,
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
    
    # 各パネル
    left_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            ft.Text("アーティストタグ", size=12),
            ft.TextField(label="ArtistTag", hint_text="input artist tag", text_size=12),
            ft.TextButton(
                content="検索",
                icon=ft.Icons.SEARCH,
                icon_color=ft.Colors.BLUE_300,
                on_click=search_artistname,
            ),
            ft.Divider(),
            ft.Text("既存のアーティスト一覧", size=12),
            ft.Container(
                content=artist_list,
                expand=True,
                border=ft.border.all(1, ft.Colors.GREY_400),
                border_radius=8,
                padding=8,
            ),
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
            ft.TextButton(
                content="ダウンロード",
                height=136,
                on_click=download_items,
            ),
        ],
        expand=True,
    )
    right_lower_panel=ft.Column(
        alignment=ft.MainAxisAlignment.START,
        controls=[],
        expand=True,
        spacing=0,
    )
    
    # ページへパネルを追加
    main_content = ft.Row(
        alignment=ft.MainAxisAlignment.START,
        controls=[
            left_panel,
            ft.Column(
                controls=[
                    right_upper_panel,
                    right_lower_panel,
                ],
                expand=3,
            ),
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