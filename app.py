import flet as ft
import danbooru_api

from settings import SettingsManager

def main(page: ft.Page):
    # アーティスト名検索
    def search_artistname(e):
        if left_panel.controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("アーティスト名を入れてください。"), duration=3000))
        else:
            api_ret = danbooru_api.getArtistInfobyName(page, left_panel.controls[1].value)
            if api_ret != []:
                right_upper_panel.controls[0].controls[0].controls[0].value = api_ret[0]["id"]
                right_upper_panel.controls[0].controls[0].controls[1].value = api_ret[0]["name"]
                right_upper_panel.controls[0].controls[1].controls[0].value = api_ret[0]["created_at"]
                right_upper_panel.controls[0].controls[1].controls[1].value = api_ret[0]["updated_at"]
                right_upper_panel.controls[0].controls[2].controls[0].value = api_ret[0]["group_name"]
                right_upper_panel.controls[0].controls[2].controls[1].value = api_ret[0]["other_names"]
                right_upper_panel.controls[0].controls[3].controls[0].value = api_ret[0]["is_deleted"]
                right_upper_panel.controls[0].controls[3].controls[1].value = api_ret[0]["is_banned"]
            else:
                page.show_dialog(ft.SnackBar(ft.Text("Not Found."), duration=3000))
    # ダウンロード(後で実装)
    def download_items(e):
        if right_upper_panel.controls[0].controls[0].controls[1].value == "":
            page.show_dialog(ft.SnackBar(ft.Text("先にアーティスト名検索をしてください。"), duration=3000))
        else:
            api_ret = danbooru_api.downloadItems(page, right_upper_panel.controls[0].controls[0].controls[1].value)
            page.show_dialog(ft.SnackBar(ft.Text("download finished."), duration=3000))
    # メインウインドウの設定
    page.title = "danbooru clawler by artist"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.settings = SettingsManager.load()
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
            ft.Text("ダウンロード済みリスト", size=12),
            ft.Divider(),
            #ここにリストアイテムを・・・
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
                    ft.Row(
                        controls=[
                            ft.TextField(label="ID", height=30, text_size=12, disabled=True),
                            ft.TextField(label="アーティスト名", height=30,text_size=12, disabled=True),
                        ],
                        spacing=0,
                    ),
                    ft.Row(
                        controls=[
                            ft.TextField(label="登録日", height=30,text_size=12, disabled=True),
                            ft.TextField(label="更新日", height=30,text_size=12, disabled=True),
                        ],
                        spacing=0,
                    ),
                    ft.Row(
                        controls=[
                            ft.TextField(label="グループ名", height=30,text_size=12, disabled=True),
                            ft.TextField(label="別名", height=30,text_size=12, disabled=True),
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
    page.add(
        ft.Row(
            alignment=ft.MainAxisAlignment.START,
            controls=[
                left_panel,
                ft.Column(
                    controls=[
                        right_upper_panel,
                        right_lower_panel,
                    ],
                    expand=3
                ),
            ],
            expand=True
        )
    )
