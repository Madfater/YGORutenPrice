import json
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import pandas as pd
import aiohttp
import asyncio
import time

headers = {"User-Agent": UserAgent().googlechrome}
prodids = []

def get_result(session:aiohttp.ClientSession, url:str):
    return session.get(url)

async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        start_time=time.perf_counter()
        search = '"RC04-jp001"+亮面'
        url = f"https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod?sort=prc%2Fac&offset=1&limit=5&q={search}&_callback=jsonpcb_CoreProd"
        resp = await get_result(session,url)
        data = re.sub(
            r"try\{jsonpcb_CoreProd\(|\);\}catch\(e\)\{if\(window.console\)\{console.log\(e\);\}\}",
            "",
            await resp.text(),
        )
        for prod in json.loads(data)["Rows"]:
            prodids.append(prod["Id"])

        tasks = [asyncio.create_task(get_result(session, "https://goods.ruten.com.tw/item/show?"+ prodid)) for prodid in prodids]
        df = []
        
        for task in asyncio.as_completed(tasks):
            res=await task
            soup = BeautifulSoup(await res.text(), "html.parser")
            data1 = json.loads(
                soup.findAll("script", {"type": "application/ld+json"})[0].text
            )
            ndf = pd.DataFrame(
                [
                    {
                        "productId": data1["productId"],
                        "price": data1["offers"]["lowPrice"],
                    }
                ]
            )
            df.append(ndf)
        end_time=time.perf_counter()
    print(end_time-start_time)
    df = pd.concat(df, ignore_index=True)
    df.to_excel("./RuTen.xlsx")
    
    
if __name__=="__main__":
    asyncio.run(main())