import requests
from collections import OrderedDict
import urllib3
import numpy as np
import time 
from tqdm import tqdm
from datetime import datetime

####### USER INPUT ########

TOTAL_PAGES = 2492 # Check how many pages there are when you are in your actual browser.

# COOKIES
# Copy over the ENTIRE STRING that is in your Burpsuite request 'Cookies' header.
# After you visit the site and make the first map search as a human, this combination of cookies will be marked by Cloudflare as valid, hence you can use for the next ~900 requests or so, or 30 mins.

COOKIES_BURPSUITE = "isRedirectFromMapSearch=false; PHPSESSID2=25a2c7fc3c1dd0149c340c3f9dd44f09; sixpack_client_id=631E5C85-5CEC-54D1-9EAA-8E8055CE3FB8; Visitor=2365e540-ab25-4399-bae5-42620888a46c; _gid=GA1.3.1942453048.1697959549; _ga4_ga=GA1.3.758351161.1697959549; pgutid=653fd2bd-6732-4720-b274-d60f14c1ec92; ajs_anonymous_id=653fd2bd-6732-4720-b274-d60f14c1ec92; _fbp=fb.2.1697959550127.1207524503; isRedirectFromMapSearch=false; pgutid=653fd2bd-6732-4720-b274-d60f14c1ec92; _hjSessionUser_2468245=eyJpZCI6ImZiMTEyYmE5LWU3NTQtNWUyNS04MmI4LTIzZWU3YzU3MDdmZCIsImNyZWF0ZWQiOjE2OTc5ODU4NDU0NzgsImV4aXN0aW5nIjp0cnVlfQ==; ab.storage.deviceId.598492ca-0323-4cd6-a8dd-62e8595da78f=%7B%22g%22%3A%220876e2c7-ab89-f981-48a8-a5d6356ab5ac%22%2C%22c%22%3A1697959550033%2C%22l%22%3A1698035148893%7D; _clck=zo5dxu|2|fg3|0|1390; _clsk=vr6tl5|1698035153003|1|1|x.clarity.ms/collect; ldpv=24337113.1697983846445%2C24727917.1697985842699%2C24759940.1698035170006; _ga=GA1.3.758351161.1697959549; _ga_0HGK3QZS7D=GS1.1.1698035135.3.1.1698035170.0.0.0; __cf_bm=m5vaWkxYn_lfASoeMWuNl3te_BWvxedynr977JYrU.Q-1698038748-0-AdDDyOHrKmpIWB/+W5Ak6twHQezj2sKeo1EdikkIFXqXptmulo0SY0JddrQQtD8o2qprMtu/5CtertlXp/FfTifl3OySmNKugn3NZzLRjLhG; __gads=ID=bd7a8b377451dbef-229a99ec01e500e2:T=1697959550:RT=1698038776:S=ALNI_MaJtqg1Td_nRDMKdzLbd60P41rLnA; __gpi=UID=00000c6d1dc95e56:T=1697959550:RT=1698038776:S=ALNI_MZb1OmbC4j6_HA0Te290e_UkmToHQ; _ga_7RWB0F6NS6=GS1.3.1698035177.6.1.1698038788.34.0.0; ab.storage.sessionId.598492ca-0323-4cd6-a8dd-62e8595da78f=%7B%22g%22%3A%222e7a72d8-8579-941d-440c-8bdea04c32c2%22%2C%22e%22%3A1698040588369%2C%22c%22%3A1698035148892%2C%22l%22%3A1698038788369%7D; cf_clearance=qlVgclIrqRq4e2spVH55qUdxKfNZRi9Fk4W1yGBXra0-1698038802-0-1-a4cacce6.c1a9d99a.f3cb9306-250.0.0; _ga4_ga_0HGK3QZS7D=GS1.3.1698035177.7.1.1698038862.0.0.0; _gat=1; _gat_regionalTracker=1"

######### END USER INPUT ########

# So we don't get SSL warnings when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# This is the default setting to view the entire SG map
zoom='20'
center='1.3294153461484386%2C103.83883754108852'
min_lat=1.1543619385843042
min_lon=103.60469142292446
max_lat=1.504456342809669
max_lon=104.07298365925259

# I use POINT_... which makes it easier if you want to structure a loop around this that incorporates breaking the SG map into smaller squares. I tested it and it is not as efficient as just taking the entire SG map.

point_center = center
point_min_lat = min_lat
point_min_lon = min_lon
point_max_lat = max_lat
point_max_lon = max_lon

# Keep track of the latest file in your scrape
latest_page = 0
for filename in os.listdir('html-files'):
    if filename.endswith('.html'):
        number = int(filename.split('_')[1].split('.')[0])
        if number > latest_page:
            latest_page = number
start_from = latest_page+1

# Start scraping
page_data_ls = []
start_t = datetime.now().strftime('%Y%m%dT%H%M%S') 
for n  in tqdm(range(start_from,TOTAL_PAGES+1,1)):
    session = requests.session()    
    time.sleep(2*np.random.random())
    url = f"https://www.propertyguru.com.sg/property-for-sale/{str(n)}?center=1.3520476038161642%2C103.83908448315377&max_latitude=1.5270868766303571&max_longitude=104.07323060131783&min_latitude=1.1769957089687204&min_longitude=103.6049383649897&search=true&zoom=12"
    headers = OrderedDict({"Host": "www.propertyguru.com.sg",
                        "Cookie": f"{COOKIES_BURPSUITE}",
                        "Sec-Ch-Ua": "\"Not=A?Brand\";v=\"99\", \"Chromium\";v=\"118\"",
                        "Sec-Ch-Ua-Mobile": "?0",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36",
                        "X-Map-Search": "true",
                        "Accept": "*/*",
                        "X-Requested-With": "XMLHttpRequest",
                        "X-Ajax-Search": "true",
                        "Sec-Ch-Ua-Platform": "\"Windows\"",
                        "Sec-Fetch-Site": "same-origin",
                        "Sec-Fetch-Mode": "cors",
                        "Sec-Fetch-Dest": "empty",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"
    })

    # Pass the request through Burpsuite proxy, for some reason this keeps Cloudflare from instantly blocking you as a bot.
    proxies = {"http": "http://127.0.0.1:8080", "https": "http://127.0.0.1:8080"}

    html = session.get(url,headers=headers, proxies=proxies, verify=False).text

    # Immediately stop the scrape when we get blocked. We need to get a new set of cookies in Burpsuite to continue.
    if 'We just want to make sure you are a human' in html:
        break
    
    # Save file and keep track of the page count
    with open(f'html-files/{start_t}_{n}.html', 'w', encoding='utf-8') as file:
        file.write(html)


