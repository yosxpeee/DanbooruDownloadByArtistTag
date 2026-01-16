import flet as ft
import os
import shutil
from datetime import datetime

import danbooru_api
from downloaded_list import DownloadedListManager

class LeftPanel:
    """左パネルの処理を管理するクラス"""
    
    def __init__(self, page: ft.Page, right_panel):
        self.page = page
        self.right_panel = right_panel
        self.selected_artist_name = None
        self.log_callback = None
        
        # UIコンポーネント
        self.artist_list = None
        self.search_field = None
        
        # UIの初期化
        self._init_ui()
    
    def _init_ui(self):
        """UIコンポーネントの初期化"""
        self.artist_list = ft.Container(
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
        
        self.search_field = ft.TextField(
            label="Artist Tag",
            hint_text="input artist tag",
            text_size=12,
            expand=True,
        )
    
    def get_control(self):
        """左パネルのコントロールを返す"""
        return ft.Column(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                ft.Text("アーティストタグ", size=12),
                ft.Row(
                    controls=[self.search_field],
                ),
                ft.TextButton(
                    content="検索",
                    icon=ft.Icons.SEARCH,
                    icon_color=ft.Colors.BLUE_300,
                    on_click=self.search_artistname,
                ),
                ft.Divider(height=1, radius=0),
                ft.Text("既存のアーティスト一覧", size=12),
                self.artist_list,
            ],
            width=400,
        )
    
    def set_log_callback(self, callback):
        """ログ表示用のコールバックを設定"""
        self.log_callback = callback
    
    def append_log(self, message):
        """ログを追加"""
        if self.log_callback:
            self.log_callback(message)
    
    def format_date(self, date_str):
        """ISO 8601形式の日付文字列を YYYY/MM/DD hh:mm:ss 形式に変換"""
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except:
            return date_str
    
    def load_artist_list(self):
        """アーティスト一覧をロード"""
        self.artist_list.content.controls.clear()
        output_dir = "output"
        
        # downloaded_list.jsonのデータを取得
        downloaded_data = DownloadedListManager.load()
        
        # ヘッダー行（見出し）
        header_row = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Text("削除", size=12),
                        width=40,
                        alignment=ft.Alignment.CENTER
                    ),
                    ft.Container(
                        content=ft.Text("アーティスト名", size=12, weight=ft.FontWeight.BOLD),
                        alignment=ft.Alignment.CENTER,
                        bgcolor=ft.Colors.BLUE_100,
                        expand=True,
                    ),
                    ft.Container(
                        content=ft.Text("更新日", size=12, weight=ft.FontWeight.BOLD),
                        width=140,
                        alignment=ft.Alignment.CENTER
                    ),
                ],
                spacing=8,
            ),
            padding=ft.Padding(0, 0, 0, 0),
            bgcolor=ft.Colors.GREY_200,
            border_radius=4,
        )
        self.artist_list.content.controls.append(header_row)
        
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
                        on_click=lambda e, name=item: self.delete_artist(name),
                    )
                    
                    # アーティスト名（クリック可能）
                    artist_name_btn = ft.TextButton(
                        content=ft.Text(item, size=12),
                        on_click=lambda e, name=item: self.search_from_list(name),
                        style=ft.ButtonStyle(
                            padding=ft.Padding(8, 4, 8, 4),
                        ),
                    )
                    
                    # 更新日表示
                    date_text = ft.Text(
                        download_date if download_date else "-",
                        size=12,
                        text_align=ft.TextAlign.CENTER
                    )
                    
                    # 1行分のRow - 選択状態なら黄色背景
                    bgcolor = ft.Colors.YELLOW_200 if self.selected_artist_name == item else None
                    row = ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Container(content=delete_btn, width=40),
                                ft.Container(content=artist_name_btn, expand=True),
                                ft.Container(content=date_text, width=140),
                            ],
                            spacing=8,
                        ),
                        padding=ft.Padding(0, 0, 0, 0),
                        bgcolor=bgcolor,
                    )
                    self.artist_list.content.controls.append(row)
        
        self.page.update()
    
    def search_from_list(self, artist_name):
        """リストからアーティストを検索"""
        self.selected_artist_name = artist_name
        self.search_field.value = artist_name
        
        # APIからデータを取得
        api_ret = danbooru_api.getArtistInfobyName(self.page, artist_name)
        tag_counts = danbooru_api.getTagCounts(self.page, artist_name.replace(" ", "_"))
        
        if api_ret != []:
            # 右パネルにアーティスト情報を表示
            self.right_panel.set_artist_info(
                api_ret[0]["id"],
                api_ret[0]["name"],
                self.format_date(api_ret[0]["created_at"]),
                self.format_date(api_ret[0]["updated_at"]),
                api_ret[0]["is_deleted"],
                api_ret[0]["is_banned"],
                str(tag_counts["counts"]["posts"])
            )
            
            # 右パネルにファイルビューワーを表示
            self.right_panel.show_file_viewer(artist_name)
            
            # リストを再読み込みしてハイライトを更新
            self.load_artist_list()
            
            self.page.show_dialog(
                ft.SnackBar(ft.Text(f"「{artist_name}」を表示しました"), duration=2000)
            )
        else:
            self.page.show_dialog(
                ft.SnackBar(ft.Text("Not Found."), duration=3000)
            )
        
        self.page.update()
    
    def search_artistname(self, e):
        """アーティスト名を検索"""
        if self.search_field.value == "":
            self.page.show_dialog(
                ft.SnackBar(ft.Text("アーティスト名を入れてください。"), duration=3000)
            )
            return
        
        api_ret = danbooru_api.getArtistInfobyName(self.page, self.search_field.value)
        tag_counts = danbooru_api.getTagCounts(self.page, self.search_field.value.replace(" ", "_"))
        
        if api_ret != []:
            self.right_panel.set_artist_info(
                api_ret[0]["id"],
                api_ret[0]["name"],
                self.format_date(api_ret[0]["created_at"]),
                self.format_date(api_ret[0]["updated_at"]),
                api_ret[0]["is_deleted"],
                api_ret[0]["is_banned"],
                str(tag_counts["counts"]["posts"])
            )
            self.page.update()
        else:
            self.page.show_dialog(
                ft.SnackBar(ft.Text("Not Found."), duration=3000)
            )
    
    def delete_artist(self, artist_name):
        """ダウンロード済みのアーティストを削除"""
        
        # 確認ダイアログ
        def confirm_delete(e, dialog):
            # ダイアログを閉じる
            dialog.open = False
            self.page.update()
            
            # ダウンロード済みデータから削除
            DownloadedListManager.remove_artist(artist_name)
            
            # outputディレクトリ内のフォルダを削除
            output_dir = "output"
            artist_path = os.path.join(output_dir, artist_name)
            if os.path.exists(artist_path):
                shutil.rmtree(artist_path)
                self.append_log(f"削除完了: {artist_name}")
            else:
                self.append_log(f"フォルダ見つかりず: {artist_name}")
            
            # リストを再読み込み
            self.load_artist_list()
            self.page.show_dialog(
                ft.SnackBar(ft.Text(f"「{artist_name}」を削除しました"), duration=2000)
            )
            self.page.update()
        
        # 確認求めるダイアログ
        dialog = ft.AlertDialog(
            title=ft.Text("削除確認"),
            content=ft.Text(f"「{artist_name}」のフォルダとデータを削除しますか？\n（元に戻せません）"),
            actions=[
                ft.TextButton("キャンセル", on_click=lambda e: (setattr(dialog, 'open', False), self.page.update())),
                ft.TextButton("削除", on_click=lambda e: confirm_delete(e, dialog)),
            ],
        )
        self.page.show_dialog(dialog)
    
    def get_selected_artist_name(self):
        """選択されたアーティスト名を取得"""
        return self.selected_artist_name
    
    def clear_selection(self):
        """選択状態をクリア"""
        self.selected_artist_name = None
        self.load_artist_list()
    
    def clear_file_selection(self):
        """ファイル選択状態をクリア（右パネルに委譲）"""
        self.right_panel.clear_file_selection()