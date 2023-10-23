# Summary

This is a POC of webscraping the Pr0perty9uru - PG (don't want this to be insta-blocked) website for listings. It scrapes all 50,000 listings on the site in ~ 1 hour and requires 3-4 interventions to reset cookies when Cloudflare detects bot activity. This means we can scrape 900+ pages before getting bot detected, which is much better than the 10 page limit that was possible with Selenium. It also can be run on a single IP rather than requiring rotating IPs.

The scraper needs to be run in conjunction with Burpsuite as without it we instantly get bot detected.

# How to use

## Sample

The `sample` folder contains examples of the raw HTML files.

## Dependencies

Install [Burpsuite](https://portswigger.net/burp) according to official instructions.

## Setup

    git clone xxx

`pip install` the required libraries if you don't already have them:

    pandas
    bs4
    requests
    urllib3
    numpy
    tqdm

## Scraping

1. Start a new Burpsuite project and open the browser

![Burpsuite UI](/assets/imgs/1-burpsuite-install.png)

2. Go to `www.propertyguru.com.sg/`, solve CAPTCHAs if needed, then go to the `Buy` page and turn on `Show Map`

![Main page](/assets/imgs/2-browser-pg.png)

![Search listings page](/assets/imgs/3-browser-search.png)

![Map Search mode](/assets/imgs/3-browser-map.png)

3. In Burpsuite proxy HTTP history, look for the latest instance of this URL

        https://www.propertyguru.com.sg/property-for-sale?market=residential&listing_type=sale&zoom=12&center=1.32941534...

![Check HTTP History](/assets/imgs/4-bs-cookie.png)

4. Copy over the entire cookie string from the `Request` into the `by-page.py COOKIES_BURPSUITE` variable.

5. Also check how many total pages there are at the current moment. This should be close to 2,500. Enter this into the `TOTAL_PAGES` variable.

![User input for script](/assets/imgs/5-py-cookie.png)

6. Run the entire `by-page.py` file. If bot detection is triggered, it will automatically stop scraping. 

7. To continue, solve the CAPTCHA on the browser, then repeat from (2). You may have to clear the Burpsuite history to find the latest request. You should have a **new** set of cookies.

8. Repeat until all pages are scraped.

# Background

## PG website infrastructure

PG hosts all their content on Cloudflare. Listings data including images, are delivered by Cloudflare CDNs which make it difficult to find an exposed endpoint where we can directly access the data. Thus, we are limited to scraping the data that is presented in HTML.

### Attempting other methods of getting data

I have attempted to find the specific endpoint that delivers listing data that is used to generate the listings in the front-end Javascript, but Cloudflare code obfuscation makes it impossible to reverse engineer. I believe the actual script retrieving the data sits on either of these particular files:

    https://cdn1.pgimgs.com/1697806357/sf2-search/assets/165.js
    https://cdn.pgimgs.com/hive-ui/widgets/v2.25.1/iife/bundle.min.js 

![165.js](/assets/imgs/6-165js.png)


If we look at the various scripts used to load the main page, `bundle.min.js` gets called right at the start of page load along with some other page tracking services, before the GuruApp variable containing all the listings even gets defined. It is likely that the listing data in GuruApp gets populated dynamically by some other script as the page is being built.

    ```javascript
    <script type="text/javascript" src="https://cdn.pgimgs.com/hive-ui/widgets/v2.25.1/iife/bundle.min.js"></script>
    <script type="text/javascript">
        (function(i, s, o, g, r, a, m) {
            i['GoogleAnalyticsObject'] = r;
            i[r] = i[r] || function() {
                (i[r].q = i[r].q || []).push(arguments)
            }
            ,
            i[r].l = 1 * new Date();
            a = s.createElement(o),
            m = s.getElementsByTagName(o)[0];
            a.async = 1;
            a.src = g;
            m.parentNode.insertBefore(a, m)
        }
        )(window, document, 'script', 'https://www.google-analytics.com/analytics.js', 'ga');
    </script>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-0HGK3QZS7D"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag() {
            dataLayer.push(arguments);
        }
        gtag('js', new Date());
    </script>
    <script type="text/javascript">        
        var guruApp = {...}                      <------ THIS IS WHERE ALL THE LISTING DATA IS HELD
        ...
        ...
        ...
    </script>
    ```

If you monitor the network traffic when any listing data is loaded, you will see this `165.js` being called. The file itself is also obfuscated, with the path name containing a UNIX timestamp `1697806357` (GMT: Friday, 20 October 2023 12:52:37), so maybe the file name is some form of versioning.

To make things even more difficult, the listing data is pre-loaded as a JS variable in the page source `/property-for-sale.html`, before being used in subsequent JS scripts to render and display the content. This protects the source from override, modifications, and re-running. Hence, we are left with scraping using either HTTP requests or Selenium.

Selenium gets CAPTCHA blocked instantly, and if not, after scrolling for 10 pages, because Cloudflare doesnt trust the browser as human. Selenium also requires the browser to load the entire web content, which contains a massive amount of 3rd-party activity tracking services. 

![Third-party services](/assets/imgs/7-thirdparty.png)

To minimise excessive loading, we use HTTP requests directly. 

## The Map Search function

Instead of using the regular search filters in `/property-for-sale`, I noticed that the Map Search function in PG simply calls `/property-for-sale` with a latitude and longitude. The listings are loaded by the sidebar like the main search page. More importantly, if the user navigates through the page selector at the bottom while in map-search mode, Cloudflare doesn't trigger bot detection, at least for the next 50 pages that I tried.

So, we can look at the exact HTTP request that is being sent during this usage pattern and reuse the request headers and cookies to trick Cloudflare into thinking our script is just the same browser clicking through each page.

## Burpsuite

Since we need to capture the HTTP request, sent by the specific action and from a specific browser, we need to use Burpsuite. We will start a browser directly in Burpsuite, and then continue using that same browser and all its credentials for any subsequent Python requests.

As of current testing, requests only work when passing through the BurpSuite proxy `127.0.0.1:8080`, although I am not sure why. Technically, the requests are exactly the same and coming from the same IP - perhaps it has something to do with the cookies being created with the original Burpsuite CA Cert. Either ways, since we are already running Burpsuite to pass the cookies, we can just leave it on as a proxy.

Cloudflare checks the cookies to know if a request is coming from a human source. Hence, we need to pass the same cookies used by Burpsuite, that has already been verified. They look something like:

    isRedirectFromMapSearch=false; 
    PHPSESSID2=25a2c7fc3c1dd0149c340c3f9dd44f09; 
    sixpack_client_id=631E5C85-5CEC-54D1-9EAA-8E8055CE3FB8; 
    Visitor=2365e540-ab25-4399-bae5-42620888a46c; 
    _gid=GA1.3.1942453048.1697959549; 
    _ga4_ga=GA1.3.758351161.1697959549; 
    pgutid=653fd2bd-6732-4720-b274-d60f14c1ec92; 
    ajs_anonymous_id=653fd2bd-6732-4720-b274-d60f14c1ec92; 
    _fbp=fb.2.1697959550127.1207524503; 
    isRedirectFromMapSearch=false; 
    pgutid=653fd2bd-6732-4720-b274-d60f14c1ec92; 
    _hjSessionUser_2468245=eyJpZCI6ImZiMTEyYmE5LWU3NTQtNWUyNS04MmI4LTIzZWU3YzU3MDdmZCIsImNyZWF0ZWQiOjE2OTc5ODU4NDU0NzgsImV4aXN0aW5nIjp0cnVlfQ==; 
    ab.storage.deviceId.598492ca-0323-4cd6-a8dd-62e8595da78f=%7B%22g%22%3A%220876e2c7-ab89-f981-48a8-a5d6356ab5ac%22%2C%22c%22%3A1697959550033%2C%22l%22%3A1698035148893%7D; 
    _clck=zo5dxu|2|fg3|0|1390;
    _clsk=vr6tl5|1698035153003|1|1|x.clarity.ms/collect; 
    ldpv=24337113.1697983846445%2C24727917.1697985842699%2C24759940.1698035170006; 
    _ga=GA1.3.758351161.1697959549; 
    _ga_0HGK3QZS7D=GS1.1.1698035135.3.1.1698035170.0.0.0; 
    __cf_bm=m5vaWkxYn_lfASoeMWuNl3te_BWvxedynr977JYrU.Q-1698038748-0-AdDDyOHrKmpIWB/+W5Ak6twHQezj2sKeo1EdikkIFXqXptmulo0SY0JddrQQtD8o2qprMtu/5CtertlXp/FfTifl3OySmNKugn3NZzLRjLhG; 
    __gads=ID=bd7a8b377451dbef-229a99ec01e500e2:T=1697959550:RT=1698038776:S=ALNI_MaJtqg1Td_nRDMKdzLbd60P41rLnA; 
    __gpi=UID=00000c6d1dc95e56:T=1697959550:RT=1698038776:S=ALNI_MZb1OmbC4j6_HA0Te290e_UkmToHQ; _ga_7RWB0F6NS6=GS1.3.1698035177.6.1.1698038788.34.0.0; 
    ab.storage.sessionId598492ca-0323-4cd6-a8dd-62e8595da78f=%7B%22g%22%3A%222e7a72d8-8579-941d-440c-8bdea04c32c2%22%2C%22e%22%3A1698040588369%2C%22c%22%3A1698035148892%2C%22l%22%3A1698038788369%7D; cf_clearance=qlVgclIrqRq4e2spVH55qUdxKfNZRi9Fk4W1yGBXra0-1698038802-0-1-a4cacce6.c1a9d99a.f3cb9306-250.0.0; 
    _ga4_ga_0HGK3QZS7D=GS1.3.1698035177.7.1.1698038862.0.0.0; 
    _gat=1; 
    _gat_regionalTracker=1

Since we are copy-pasting the entire cookie string, I didn't bother to check if the specific combination of cookies mattered, or only the Cloudflare `cf` related ones are.

## Scraping

This is a basic HTTP GET/ request to the following URL:

    https://www.propertyguru.com.sg/property-for-sale/{PAGE_NUMBER}?center=1.3520476038161642%2C103.83908448315377&max_latitude=1.5270868766303571&max_longitude=104.07323060131783&min_latitude=1.1769957089687204&min_longitude=103.6049383649897&search=true&zoom=12"

The only variable we need to change is `PAGE_NUMBER`. All other search filters remain the same. The hard-coded coordinates covers the entire Singapore map, hence we will get all 50,000 results, loaded 20 at a time. Giving us about 2,500 pages to loop through.

* At first, I did explore the option of walking the coordinates across the map in a 100m x 100m grid to mimic the movement of a user panning across the map, but that turned out to be way less efficient once I realised you can loop through pages unblocked in map mode.

## The data

Data loading is done separately from processing to minimise disruption from CAPTCHA events. 

Once each page's HTML has been received, it gets saved directly into your local folder. 

Repeat until all pages are done

## CAPTCHA events

Despite the cookies, Cloudflare can still detect bot activity after ~ 900 requests. Since we only have 2,500 requests to go through, this is not a major issue. 

Upon such events:
1. We solve the CAPTCHA on Burpsuite browser
2. Do a refresh on Burpsuite back to the map-search page
3. Copy over the new set of cookies from the latest request from Burpsuite to the script.
4. Re-run the script.

The script automatically checks the page of the latest saved `.html` in `html-files` and continues numbering from there. 

## Processing

`process-html` provides an example of how the HTML data may be processed, although that only considers very basic details for each listing. 

|    id     |                                               name                                               |   price   |     category     |              brand              | variant |     list      | position | dimension19 |      dimension22      |      dimension23      | dimension24 | dimension25 |            district             |            region             | regionCode | districtCode | bedrooms | bathrooms | area | areaCode |  floorArea  | project |     dimension40     |
|-----------|--------------------------------------------------------------------------------------------------|-----------|-----------------|----------------------------------|---------|---------------|----------|-------------|-----------------------|-----------------------|------------|------------|----------------------------------|-------------------------------|------------|--------------|----------|-----------|------|----------|-------------|---------|--------------------|
| 23561643  | Freehold, Well Renovated Greenery and Quiet Facing! Move in condition!                          | 3700000   | Condominium     |                                  | Sale    | Map Search    | 1        | 575982      | {"page":1,"limit":20,"rankInPage":1} | {"Product":["Turbo"]} | ACT        | 575982     | Tanglin / Holland / Bukit Timah |                               |            | D10          | 3        | 3         |      |          | 1572 sqft   |         |                    |
| 23875898  | OUE Twin Peaks                                                                                  | 1500000   | Condominium     | Cove Development Pte Ltd         | Sale    | Map Search    | 2        | 575982      | {"page":1,"limit":20,"rankInPage":2} | {"Product":["Turbo"]} | ACT        | 575982     | Orchard / River Valley            | Orchard / Holland (D09-10)  | B          | D09          | 1        | 1         |      |          | 570 sqft    | 2655    |
| 24596834  | The Springside                                                                                 | 4750000   | Terraced House  | Kallang Development Pte Ltd      | Sale    | Map Search    | 3        | 575982      | {"page":1,"limit":20,"rankInPage":3} | {"Product":["Turbo"]} | ACT        | 575982     | Mandai / Upper Thomson           | North (D25-28)               | I          | D26          | 5        | 5         |      |          | 4155 sqft   | 319     |
| 24090161  | One Bernam                                                                                    | 2340000   | Condominium     | HY-MCC (Bernam) Pte Ltd           | Sale    | Map Search    | 4        | 575982      | {"page":1,"limit":20,"rankInPage":4} | {"Product":["Turbo"]} | ACT        | 575982     | Chinatown / Tanjong Pagar        | City & South West (D01-08)   | A          | D02          | 2        | 2         |      |          | 807 sqft    | 24610   | newProject=1         |
| 24560155  | Genuine Listing for Sale! Detached at Coronation Road West For Sale! Selling Vacant!       | 23000000  | Bungalow House  |                                  | Sale    | Map Search    | 5        | 575982      | {"page":1,"limit":20,"rankInPage":5} | {"Product":["Turbo"]} | ACT        | 575982     | Tanglin / Holland / Bukit Timah |                               |            | D10          | 4        | 4         |      |          | 5500 sqft   |         |                    |
| 24128714  | Waterbank at Dakota                                                                            | 2580000   | Condominium     | UOL Group Limited                | Sale    | Map Search    | 6        | 13905226    | {"page":1,"limit":20,"rankInPage":6} | {"Product":["Turbo"]} | ACT        | 13905226   | Eunos / Geylang / Paya Lebar     | Balestier / Geylang (D12-14) | D          | D14          | 3        | 2         |      |          | 1432 sqft   | 2642    |


The raw HTML files contain much richer data such as image links, links to the actual listing, agent info, and more description:

    ```javascript
    <div class="col-xs-12 col-sm-5  image-container">
        <div class="gallery-wrapper">
            <div class="gallery-container">
                <a class="nav-link" href="https://www.propertyguru.com.sg/listing/for-sale-freehold-well-renovated-greenery-and-quiet-facing-move-in-condition-23561643" title="For Sale - Freehold, Well Renovated Greenery and Quiet Facing! Move in condition!">
                    <ul>
                        <li itemscope itemtype="https://schema.org/Photograph">
                            <img src="https://sg1-cdn.pgimgs.com/listing/23561643/UPHO.129863845.R400X300/Freehold-Well-Renovated-Greenery-and-Quiet-Facing%21-Move-in-condition%21-Tanglin-Holland-Bukit-Timah-Singapore.jpg" alt="For Sale - Freehold, Well Renovated Greenery and Quiet Facing! Move in condition!" itemprop="thumbnailUrl" onerror="this.src='https://cdn1.pgimgs.com/1697806357/sf2-search/bundles/guruweblayout/img/desktop/missing/nophoto_property_400x300.png';" />
                        </li>
                    </ul>
                </a>
            </div>
        </div>

        <span class="listing-viewed badge-label badge-label--viewed" data-id="23561643">Viewed</span>

        <a class="listing-card-img-footer" title="For Sale - Freehold, Well Renovated Greenery and Quiet Facing! Move in condition!" href=https://www.propertyguru.com.sg/listing/for-sale-freehold-well-renovated-greenery-and-quiet-facing-move-in-condition-23561643>
            <span class="media-bar-bg"></span>
            <div class="gallery-information" data-automation-id="listing-card-media-gallery-img-lnk">7 
                <span class="icons pgicon-photo"></span>1 
                <span class="icons pgicon-floorplan"></span>
                <span class="badge">LiveTour</span>
            </div>
        </a>
    </div>
    ...
    ...
    ```

## Future Automation

As this still requires manual intervention to transfer cookies from Burpsuite to the python script. I am looking for a solution that can do this automatically.

For example, the new version would run with a max 700 request limit.
1. Upon hitting the limit, close the current Burpsuite browser and pause for X minutes. 
2. Then open a new Burpsuite browser
3. Make the first map-search request (can this be done automatically without triggering bot protection?)
4. Pass the cookies to the script and continue scraping.

