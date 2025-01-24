import datetime
import subprocess
import time
import webbrowser

import PySimpleGUI as sg
from pip._vendor import requests

# ありがとう
# https://qiita.com/dario_okazaki/items/656de21cab5c81cabe59
# https://note.com/hideharu092/n/n9dc1c1075a7b

sg.theme('SystemDefault1')

API = URL = RTM = ""

try:
    with open('settings', mode='r') as f:
        API = f.readline()
        URL = f.readline()
        RTM = f.readline()
except FileNotFoundError:
    pass
# レイアウトの定義
layout = [
    [sg.Text('Please Input Steam Data', key="output")],
    [sg.Text('API Key', size=(15, 1)), sg.InputText(API.strip(), key="API"), sg.Button(button_text='Start')],
    [sg.Text('Custom URL', size=(15, 1)), sg.InputText(URL.strip(), key="URL"), sg.Button(button_text='Get API Key')],
    [sg.Text('Required Time (m)', size=(15, 1)), sg.InputText(RTM.strip(),size=(5,1), key="RTM")],
    [sg.Text('https://steamcommunity.com/id/XXXXX(Custom URL)')]
]

# ウィンドウの生成
window = sg.Window('SteamSaleInTheLibrary', layout)

# イベントループ
while True:
    event, values = window.read()

    if event is None:
        print('exit')
        break

    if event == 'Start':
        apikey = values["API"]
        rtm = values["RTM"]
        if not rtm.isdecimal():
            rtm = 0
        else:
            rtm = int(rtm)

        with open('settings', mode='w') as f:
            f.write(apikey + "\n")
            f.write(values["URL"] + "\n")
            f.write(str(rtm))

        # SteamID の取得（Vanity URL か数字の ID か判定）
        if not values["URL"].isdecimal():
            idurl = (
                "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
                f"?key={apikey}&vanityurl={values['URL']}"
            )
            response = requests.get(idurl)
            json_data = response.json()
            steamID = json_data["response"]["steamid"]
        else:
            steamID = values["URL"]

        # ユーザの所有ゲーム一覧を取得
        ownedurl = (
            "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
            f"?key={apikey}&steamid={steamID}&format=json"
        )
        response = requests.get(ownedurl)
        json_data = response.json()

        # 指定プレイ時間以上のゲームの appid を抽出
        appList = []
        for g in json_data["response"]["games"]:
            if g["playtime_forever"] >= rtm:
                appList.append(g["appid"])

        today = datetime.datetime.today()
        filename = (
            "SteamSaleInTheLibrary-"
            + today.strftime("%Y%m%d%H%M%S")
        )

        appLength = len(appList)
        itemCount = 0

        with open(filename, mode='x', encoding='UTF-8') as f:
            for appid in appList:
                itemCount += 1
                print(f"in process... {itemCount} / {appLength}")
                window["output"].update(f"in process... {itemCount} / {appLength}")

                try:
                    # store API による価格・割引情報の取得
                    # 例: https://store.steampowered.com/api/appdetails?appids=1091500&cc=jp&l=japanese
                    store_url = (
                        "https://store.steampowered.com/api/appdetails"
                        f"?appids={appid}&cc=jp&l=japanese"
                    )
                    store_res = requests.get(store_url)
                    store_json = store_res.json()

                    if str(appid) not in store_json:
                        print(f"Invalid response for appid={appid}")
                        continue

                    app_info = store_json[str(appid)]
                    if not app_info.get('success'):
                        print(f"Failed to get data for appid={appid}")
                        continue

                    data = app_info.get('data', {})
                    appName = data.get('name', '')
                    
                    # 価格情報
                    price_info = data.get('price_overview')
                    if not price_info:
                        continue

                    discount = price_info.get('discount_percent', 0)
                    initial_price = price_info.get('initial_formatted', '')
                    final_price = price_info.get('final_formatted', '')

                    if discount > 0:
                        f.write(
                            f"{appName} : [-{discount}%] "
                            f"{initial_price} -> {final_price}\n"
                        )
                        print(f"{appName} : [-{discount}%] {initial_price} -> {final_price}")

                except Exception as e:
                    print(f"ERROR - appid={appid} ex:{e}")
                    continue

        # 処理終了後にファイルをメモ帳で開く
        subprocess.Popen(['notepad.exe', filename])
        print(f"Done! {filename}")
        window["output"].update(f"Done! {filename}")

    if event == 'Get API Key':
        webbrowser.open("https://steamcommunity.com/dev/apikey")

# ウィンドウの破棄と終了
window.close()
