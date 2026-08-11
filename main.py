import os
import json
import requests
import pandas as pd
import gspread

# 設定全球主要城市與國家進行覆蓋掃描
SEARCH_TARGETS = [
    # 台灣與亞洲主要區域
    "Taiwan", "Tokyo", "Osaka", "Seoul", "Hong Kong", "Singapore", "Bangkok", "Manila",
    # 美洲主要區域
    "New York", "Los Angeles", "Chicago", "Toronto", "Vancouver", "Sao Paulo",
    # 歐洲與其他區域
    "London", "Paris", "Berlin", "Madrid", "Rome", "Sydney", "Auckland"
]

def fetch_global_adidas_stores():
    all_stores = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    print("正在抓取全球主要城市門市資料...")
    for target in SEARCH_TARGETS:
        # 使用全球通用 API 節點
        url = f"https://www.adidas.com/api/store-finder/v1/stores?query={target}&size=100"
        try:
            res = requests.get(url, headers=headers, timeout=12)
            if res.status_code == 200:
                data = res.json()
                stores = data.get("stores", []) if isinstance(data, dict) else data
                for s in stores:
                    store_id = str(s.get("id", s.get("storeId", "")))
                    if not store_id or store_id in all_stores:
                        continue
                    
                    # 抓取經緯度，如缺乏經緯度則跳過以防地圖報錯
                    lat = s.get("latitude") or s.get("lat")
                    lng = s.get("longitude") or s.get("lng")
                    if not lat or not lng:
                        continue

                    all_stores[store_id] = {
                        "store_id": store_id,
                        "store_name": s.get("name", "adidas Store"),
                        "country": s.get("country", target),
                        "city": s.get("city", ""),
                        "address": s.get("addressLine1", s.get("address", "")),
                        "lat": float(lat),
                        "lng": float(lng),
                        "concept": s.get("storeType", s.get("concept", "Store")),
                        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
                    }
        except Exception as e:
            print(f"抓取目標 {target} 失敗: {e}")

    df = pd.DataFrame(list(all_stores.values()))
    print(f"✅ 成功抓取到 {len(df)} 筆全球門市資料")
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
        sh = gc.open_by_url("https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")

    worksheet = sh.sheet1
    worksheet.clear()
    
    # 寫入欄位與資料
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("✅ 全球資料已成功寫入 Google 試算表！")

if __name__ == "__main__":
    df = fetch_global_adidas_stores()
    if not df.empty:
        update_google_sheet(df)
    else:
        print("未抓取到任何門市資料，請檢查 API 回應狀態。")
