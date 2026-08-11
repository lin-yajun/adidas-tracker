import os
import json
import datetime
import requests
import gspread
import pandas as pd

# =========================================================
# 【設定區】請將引號內的文字替換成你在「階段 1」取得的 Google 試算表 ID
# 試算表網址：https://docs.google.com/spreadsheets/d/【這串就是ID】/edit
# =========================================================
SPREADSHEET_ID = "14YvTyrge-ibllkbHQfW9tiwacc2QY5E4Zy98i37Yp-M"


# ---------------------------------------------------------
# 模組一：連線到 Google Sheets API
# ---------------------------------------------------------
def get_google_sheet():
    """
    這個函式的目的是建立與 Google 試算表的安全連線。
    為了讓本地電腦測試與未來 GitHub Actions（自動化雲端）都能運作，
    程式會自動判斷目前是在雲端還是在本地電腦：
    """
    # 嘗試讀取雲端環境變數（給 GitHub Actions 使用）
    creds_json = os.environ.get("GOOGLE_CREDS")
    
    if creds_json:
        # 如果有雲端環境變數，直接讀取文字格式的金鑰
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        # 如果是本地電腦測試，直接讀取同資料夾下的 google_creds.json 檔案
        gc = gspread.service_account(filename="google_creds.json")
    
    # 取得試算表 ID（優先讀取環境變數，若無則用上方設定區的 SPREADSHEET_ID）
    sheet_id = os.environ.get("SPREADSHEET_ID", SPREADSHEET_ID)
    
    # 打開試算表並指定第一個工作表 (sheet1)
    sh = gc.open_by_key(sheet_id)
    return sh.sheet1


# ---------------------------------------------------------
# 模組二：AI / 規則分類 logic（區分 adidas 系列/概念）
# ---------------------------------------------------------
def classify_concept(name):
    """
    根據門市名稱中的關鍵字，自動判定該店屬於哪種概念系列：
    例如：「adidas Home of Sport 忠孝概念店」會被識別為 "Home of Sport"
    """
    name_upper = name.upper() # 轉大寫，避免大小寫比對不到
    
    if "HOME OF SPORT" in name_upper:
        return "Home of Sport"
    elif "COLLECTION" in name_upper or "ORIGINALS" in name_upper:
        return "The Collection / Originals"
    elif "KIDS" in name_upper:
        return "Kids"
    elif "OUTLET" in name_upper or "FACTORY" in name_upper:
        return "Outlet"
    elif "BRAND CENTER" in name_upper:
        return "Brand Center"
    else:
        return "Standard Store" # 如果都沒比對到，預設為一般標準店


# ---------------------------------------------------------
# 模組三：抓取與整理 adidas 店點資料
# ---------------------------------------------------------
def fetch_adidas_stores():
    """
    這個函式負責取得原始資料，並將資料轉換成乾淨的表格格式。
    在實際開發中，這裡會向 adidas Store Locator API 發送請求。
    為了確保你能先測試成功，這裡放置了包含台灣門市的結構化測試資料。
    """
    print("正在抓取與整理店點資料...")
    
    # 模擬抓取到的店點清單（包含名稱、國家、城市、地址、經緯度、圖片網址等）
    raw_stores = [
        {
            "store_id": "TW001",
            "store_name": "adidas Brand Center 信義威秀",
            "country": "TW",
            "city": "Taipei",
            "address": "台北市信義區松壽路 18 號",
            "lat": 25.0354,
            "lng": 121.5668,
            "img_url": "https://example.com/xinyi.jpg"
        },
        {
            "store_id": "TW002",
            "store_name": "adidas Home of Sport 忠孝概念店",
            "country": "TW",
            "city": "Taipei",
            "address": "台北市大安區忠孝東路四段 219 號",
            "lat": 25.0415,
            "lng": 121.5512,
            "img_url": "https://example.com/zhongxiao.jpg"
        },
        {
            "store_id": "TW003",
            "store_name": "adidas Kids 台北新光三越 A8",
            "country": "TW",
            "city": "Taipei",
            "address": "台北市信義區松高路 12 號 5 樓",
            "lat": 25.0385,
            "lng": 121.5670,
            "img_url": "https://example.com/kids.jpg"
        }
    ]
    
    formatted_data = []
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 逐筆清洗並加上分類標籤與更新時間
    for item in raw_stores:
        formatted_data.append({
            "store_id": item["store_id"],
            "store_name": item["store_name"],
            "country": item["country"],
            "city": item["city"],
            "concept": classify_concept(item["store_name"]), # 調用模組二自動分類
            "address": item["address"],
            "lat": item["lat"],
            "lng": item["lng"],
            "img_url": item["img_url"],
            "updated_at": current_time # 記錄這筆資料更新的時間
        })
    
    # 使用 pandas 將 list 轉換成類似 Excel 的 DataFrame 表格結構
    return pd.DataFrame(formatted_data)


# ---------------------------------------------------------
# 模組四：主程式進入點 (Main Process)
# ---------------------------------------------------------
if __name__ == "__main__":
    # 1. 抓取並清理資料
    df = fetch_adidas_stores()
    
    if not df.empty:
        print("正在連線至 Google Sheets...")
        sheet = get_google_sheet()
        
        print("寫入最新資料至 Google 試算表...")
        # 做法：清空舊資料，然後將【表頭欄位】與【資料內容】一起重新寫入
        sheet.clear()
        
        # df.columns.values.tolist() -> 取得標題列 ['store_id', 'store_name', ...]
        # df.values.tolist() -> 取得所有門市資料列
        all_data = [df.columns.values.tolist()] + df.values.tolist()
        
        sheet.update(all_data)
        print("✅ 成功！資料已順利更新至 Google 試算表。")