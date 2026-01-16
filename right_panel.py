import flet as ft
import os
import threading
from datetime import datetime

import danbooru_api
from downloaded_list import DownloadedListManager

####################
# 右パネルの管理クラス
####################
class RightPanel:
    # パネルの初期化
    def __init__(self, page: ft.Page):
        self.page = page
        self.selected_file_name = None
        self.log_callback = None
        self.on_download_complete = None
        # UIコンコンポーネント
        self.artist_info_panel = None
        self.file_viewer_panel = None
        self.log_panel = None
        self.overlay = None
        # 右パネルの各パネル
        self.right_upper_panel = None
        self.right_middle_panel = None
        self.right_lower_panel = None
        # UIの初期化
        self._init_ui()
    # UIコンポーネントの初期化
    def _init_ui(self):
        # 上部パネル：アーティスト情報 + ダウンロードボタン
        self.artist_info_panel = ft.Container(
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
                                    ft.TextField(label="アーティスト名", height=36, text_size=12, disabled=True),
                                ],
                                spacing=0,
                            ),
                            ft.Row(
                                controls=[
                                    ft.TextField(label="登録日", height=36, text_size=12, disabled=True),
                                    ft.TextField(label="更新日", height=36, text_size=12, disabled=True),
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
                            on_click=self.download_items,
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
        self.right_upper_panel = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            controls=[self.artist_info_panel],
            expand=False,
            spacing=0,
        )
        # 中央パネル：ファイルビューワー
        self.right_middle_panel = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            controls=[],
            expand=5,
            spacing=0,
        )
        # 下部パネル：ログ
        self.log_panel = ft.TextField(
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
            content=self.log_panel,
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=8,
            padding=4,
        )
        self.log_panel._container = log_container  # 循環参照を避けるため
        self.right_lower_panel = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            controls=[log_container],
            expand=1,
            spacing=0,
        )
        # オーバーレイUIの作成
        self.overlay = ft.Container(
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
    # 右パネルのコントロールを返す
    def get_control(self):
        return ft.Column(
            controls=[
                self.right_upper_panel,
                self.right_middle_panel,
                self.right_lower_panel,
            ],
            expand=3,
        )
    # オーバーレイを返す
    def get_overlay(self):
        return self.overlay
    # ログ表示用のコールバックを設定
    def set_log_callback(self, callback):
        self.log_callback = callback
    # ダウンロード完了コールバックを設定
    def set_download_complete_callback(self, callback):
        self.on_download_complete = callback
    # ログを追加
    def append_log(self, message):
        if self.log_callback:
            self.log_callback(message)
        else:
            self.log_panel.value += f"{message}\n"
            self.page.update()
    # アーティスト情報を設定
    def set_artist_info(self, id, name, created_at, updated_at, is_deleted, is_banned, posts):
        controls = self.artist_info_panel.content.controls[0].controls
        controls[1].controls[0].value = id
        controls[1].controls[1].value = name
        controls[2].controls[0].value = created_at
        controls[2].controls[1].value = updated_at
        controls[3].controls[0].value = is_deleted
        controls[3].controls[1].value = is_banned
        controls[3].controls[3].value = f"Posts：{posts}"
        self.page.update()
    # ファイルビューワーを表示
    def show_file_viewer(self, artist_name):
        self.selected_file_name = None
        artist_dir = os.path.join("output", artist_name)
        # ビューワークリア
        self.right_middle_panel.controls.clear()
        if not os.path.exists(artist_dir):
            self.right_middle_panel.controls.append(
                ft.Container(
                    content=ft.Text("ダウンロードフォルダが見つかりません"),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            )
            return
        # ファイル一覧を取得（.txtを除外）
        files = []
        for item in sorted(os.listdir(artist_dir)):
            item_path = os.path.join(artist_dir, item)
            if os.path.isfile(item_path) and not item.lower().endswith(".txt"):
                files.append(item)
        if not files:
            self.right_middle_panel.controls.append(
                ft.Container(
                    content=ft.Text("ファイルがありません"),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                )
            )
            return
        # 左ペイン: ファイル一覧
        file_list_container = ft.Container(
            content=ft.Column(
                controls=[],
                scroll=ft.ScrollMode.AUTO,
                spacing=2,
            ),
            width=200,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=4,
            padding=4,
        )
        # 右ペイン: プレビュー
        preview_container = ft.Container(
            content=ft.Text("ファイルを選択してください"),
            expand=True,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=4,
            alignment=ft.Alignment.CENTER,
        )
        # 右ペイン: タグ情報（ContainerにTextFieldを入れる）
        tag_text_field = ft.TextField(
            value="",
            multiline=True,
            expand=True,
            read_only=True,
            bgcolor=ft.Colors.GREY_50,
            text_size=11,
            min_lines=20,
            border_color=ft.Colors.GREY_400,
            content_padding=ft.Padding(8, 8, 8, 8),
            hint_text="タグ情報",
        )
        # ファイル一覧を作成
        for file_name in files:
            # ファイル名ボタン - 選択状態なら黄色背景
            bgcolor = ft.Colors.YELLOW_200 if self.selected_file_name == file_name else None
            btn = ft.Container(
                content=ft.TextButton(
                    content=ft.Text(file_name, size=11, text_align=ft.TextAlign.LEFT),
                    on_click=lambda e, fn=self.show_file_preview, fp=os.path.join(artist_dir, file_name), tt=tag_text_field, pc=preview_container, fl=file_list_container.content.controls: self.open_file_preview(fn, fp, tt, pc, fl),
                    style=ft.ButtonStyle(
                        padding=ft.Padding(4, 2, 4, 2),
                    ),
                ),
                bgcolor=bgcolor,
                border_radius=4,
            )
            file_list_container.content.controls.append(btn)
        # タグ情報を含むContainer
        tag_container = ft.Container(
            content=tag_text_field,
            height=100,
            border=ft.border.all(1, ft.Colors.GREY_400),
            border_radius=4,
            padding=4,
        )
        # 2ペインレイアウト
        self.right_middle_panel.controls.append(
            ft.Row(
                controls=[
                    file_list_container,
                    ft.Column(
                        controls=[
                            preview_container,
                            tag_container,
                        ],
                        expand=1,
                        spacing=4,
                    ),
                ],
                expand=1,
                spacing=4,
            )
        )
        self.page.update()
    # 選択されたファイルのプレビューを表示
    def show_file_preview(self, file_path, tag_text_control=None):
        ext = os.path.splitext(file_path)[1].lower()
        # タグを読み込む
        if tag_text_control:
            tag_file_path = os.path.splitext(file_path)[0] + ".txt"
            if os.path.exists(tag_file_path):
                try:
                    with open(tag_file_path, 'r', encoding='utf-8') as f:
                        tag_content = f.read()
                        tag_text_control.value = tag_content
                except Exception as e:
                    tag_text_control.value = f"タグファイルを読み込めませんでした: {e}"
            else:
                tag_text_control.value = "タグファイルがありません"
        if ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            # 画像ファイル
            preview = ft.Image(
                src=file_path,
                fit=ft.BoxFit.CONTAIN,
                expand=True,
            )
            return preview
        elif ext in [".mp4", ".webm"]:
            # 動画ファイル - プレビュー不可のためアイコン表示にとどめる
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.VIDEO_LIBRARY, size=48, color=ft.Colors.BLUE),
                        ft.Text("動画ファイル", size=12),
                        ft.Text(os.path.basename(file_path), size=10),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
        else:
            # 画像・動画以外は×アイコン表示
            return ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon(ft.Icons.CLOSE, size=64, color=ft.Colors.GREY_400),
                        ft.Text(os.path.basename(file_path), size=10),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
                alignment=ft.Alignment.CENTER,
                expand=True,
            )
    # 選択されたファイルのプレビューとタグを表示する
    def open_file_preview(self, show_file_preview_func, file_path, tag_text, preview_container, file_list_controls):
        # ファイル名を抽出して選択状態を更新
        self.selected_file_name = os.path.basename(file_path)
        # プレビューを更新（タグも同時に読み込む）
        preview = show_file_preview_func(file_path, tag_text)
        preview_container.content = preview
        # ファイル一覧のハイライトを更新
        for control in file_list_controls:
            if isinstance(control, ft.Container) and control.content is not None:
                # コンテナの中のTextButtonの内容を取得
                if hasattr(control.content, 'content') and hasattr(control.content.content, 'value'):
                    file_name = control.content.content.value
                    if file_name == self.selected_file_name:
                        control.bgcolor = ft.Colors.YELLOW_200
                    else:
                        control.bgcolor = None
        # 画面更新（タグの更新も含める）
        self.page.update()
    # ダウンロードボタンのクリック処理
    def download_items(self, e):
        artist_name = self.artist_info_panel.content.controls[0].controls[1].controls[1].value
        is_banned = self.artist_info_panel.content.controls[0].controls[3].controls[1].value
        if not artist_name:
            self.page.show_dialog(
                ft.SnackBar(ft.Text("先にアーティスト名検索をしてください。"), duration=3000, bgcolor=ft.Colors.RED)
            )
            return
        # ダウンロード開始時に選択状態をクリア
        if self.on_download_complete:
            self.on_download_complete()
        # オーバーレイを表示
        self.overlay.visible = True
        self.page.update()
        # 別スレッドでダウンロードを開始
        download_thread = threading.Thread(target=self.run_download, args=(artist_name, is_banned))
        download_thread.daemon = True
        download_thread.start()
    # ダウンロード処理を実行
    def run_download(self, artist_name, is_banned):
        try:
            if is_banned == True:
                self.append_log("エラー: 削除されたアーティストタグです")
                self.page.show_dialog(
                    ft.SnackBar(ft.Text("削除されたアーティストタグなのでダウンロードできません。"), duration=3000, bgcolor=ft.Colors.RED)
                )
                self.overlay.visible = False
                self.page.update()
                return
            # ダウンロード処理を実行（log_callbackを追加）
            total = danbooru_api.downloadItems(self.page, artist_name, log_callback=self.append_log)
            # 完了後のUI更新
            def on_complete():
                # 更新日を取得して保存
                api_ret = danbooru_api.getArtistInfobyName(self.page, artist_name)
                if api_ret != []:
                    updated_date = datetime.fromisoformat(api_ret[0]["updated_at"].replace('Z', '+00:00')).strftime("%Y/%m/%d %H:%M:%S")
                    DownloadedListManager.update_artist(artist_name, updated_date)
                self.overlay.visible = False
                self.page.show_dialog(
                    ft.SnackBar(ft.Text(f"ダウンロード完了: {total}枚"), duration=3000, bgcolor=ft.Colors.LIGHT_GREEN_900)
                )
                # ダウンロード完了コールバックを呼び出し
                if self.on_download_complete:
                    self.on_download_complete()
                # ファイルビューワーをクリア
                self.right_middle_panel.controls.clear()
                self.page.update()
            self.page.run_thread(on_complete)
        except Exception as e:
            error_msg = str(e)
            def on_error():
                self.append_log(f"エラー: {error_msg}")
                self.overlay.visible = False
                self.page.show_dialog(
                    ft.SnackBar(ft.Text(f"エラー: {error_msg}"), duration=3000, bgcolor=ft.Colors.RED)
                )
                self.page.update()
            self.page.run_thread(on_error)
    # ファイル選択状態をクリア
    def clear_file_selection(self):
        self.selected_file_name = None
        self.right_middle_panel.controls.clear()
        self.page.update()
    # 選択状態をクリア
    def clear_selection(self):
        self.selected_file_name = None
        self.right_middle_panel.controls.clear()
        self.page.update()