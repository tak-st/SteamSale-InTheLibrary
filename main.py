import datetime
import subprocess
import time
import webbrowser

import PySimpleGUI as sg
from bs4 import BeautifulSoup
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
        with open('settings', mode='w') as f:
            f.write(apikey + "\n")
            f.write(values["URL"] + "\n")
            f.write(values["RTM"])
            if not values["URL"].isdecimal():
                idurl = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key=" + apikey + "&vanityurl=" + \
                        values["URL"]
                response = requests.get(idurl)
                jsonData = response.json()
                steamID = jsonData["response"]["steamid"]
            else:
                steamID = values["URL"]
            ownedurl = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key=" + apikey + "&steamid=" + steamID + "&format=json"
            response = requests.get(ownedurl)
            jsonData = response.json()
            appList = list(range(0))
            for jsonObj in jsonData["response"]["games"]:
                if int(jsonObj["playtime_forever"]) >= int(rtm):
                    appList.append(jsonObj["appid"])
            today = datetime.datetime.today()
            appLength = len(appList)
            itemCount = 0
            filename = "SteamSaleInTheLibrary-" + str(today.year) + str(today.month) + str(today.day) + str(
                today.hour) + str(today.minute) + str(today.second)
            with open(filename, mode='x', encoding='UTF-8') as f:
                for appid in appList:
                    try:
                        itemCount += 1
                        print("in process... " + str(itemCount) + " / " + str(appLength))
                        window["output"].update("in process... " + str(itemCount) + " / " + str(appLength))
                        appurl = "https://store.steampowered.com/app/" + str(appid) + "?l=japanese"
                        html = requests.get(appurl)
                        soup = BeautifulSoup(html.content, "html.parser")
                        elems = soup.find_all("div")
                        appName = discPct = origPri = finalPri = ""
                        for elem in elems:
                            try:
                                string = elem.get("class").pop(0)
                                if string in "bundle_base_discount":
                                    break
                                if string in "apphub_AppName":
                                    if appName == "":
                                        appName = elem.string
                                if string in "discount_pct":
                                    if discPct == "":
                                        discPct = elem.string
                                if string in "discount_original_price":
                                    if origPri == "":
                                        origPri = elem.string
                                if string in "discount_final_price":
                                    if finalPri == "":
                                        finalPri = elem.string
                            except:
                                pass
                        if appName == "":
                            print("InAccessible Game ID:" + str(appid))
                        else:
                            if discPct != "":
                                f.write(appName + " : [" + discPct + "] " + origPri + " -> " + finalPri + "\n")
                                print(appName + " : [" + discPct + "] " + origPri + " -> " + finalPri)
                        time.sleep(1)
                    except Exception as e:
                        print("ERROR - " + appName + " (" + str(appid) + ") ex:" + str(e))
                        pass
                subprocess.Popen([r'notepad.exe', filename])

    if event == 'Get API Key':
        webbrowser.open("https://steamcommunity.com/dev/apikey")

# ウィンドウの破棄と終了
window.close()
