import os
import json
import requests
import pandas as pd
import gspread

# 1. 欲抓取的全球主要國家/地區代碼 (可自行增減 ISO 代碼)
COUNTRY_CODES = [
    "TW", "JP", "KR", "US", "GB", "DE", "FR", "IT", "CA", "AU", 
    "CN", "HK", "SG", "MY", "TH", "VN", "PH", "IN", "BR", "MX"
]

def fetch_global_adidas_stores():
    all_stores = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("正在抓取全球門市資料...")
    for code in COUNTRY_CODES:
        url = f"https://www.adidas.com/api/store-finder/v1/stores?country={code}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                stores = data.get("stores", data) if isinstance(data, dict) else data
                for s in stores:
                    all_stores.append({
                        "store_id": s.get("id", ""),
                        "store_name": s.get("name", ""),
                        "country": s.get("country", code),
                        "city": s.get("city", ""),
                        "address": s.get("addressLine1", ""),
                        "lat": s.get("latitude", 0),
                        "lng": s.get("longitude", 0),
                        "concept": s.get("storeType", "Store"),
                        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    })
        except Exception as e:
            print(f"抓取國家 {code} 失敗: {e}")

    df = pd.DataFrame(all_stores)
    print(f"累計抓取到 {len(df)} 筆全球門市資料")
    return df

def update_google_sheet(df):
    print("正在更新至 Google 試算表...")
    creds_json = os.environ.get("GOOGLE_CREDS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        gc = gspread.service_account(filename="google_creds.json")

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if spreadsheet_id:
        sh = gc.open_by_key(spreadsheet_id)
    else:
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit") # 本地備用

    worksheet = sh.sheet1
    worksheet.clear()
    
    # 寫入欄位與資料
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("✅ 全球資料已成功寫入 Google 試算表！")

if __name__ == "__main__":
    df = fetch_global_adidas_stores()
    if not df.empty:
        update_google_sheet(df)
