from urllib import response

import scrapy


class MeetSpiderSpider(scrapy.Spider):
    name = "meet_spider"
    allowed_domains = ["secure.meetcontrol.com"]
    start_urls = [ 
        "https://secure.meetcontrol.com/divemeets/system/meets.php?show=past&association=National%20Collegiate%20Athletic%20Association%20(NCAA)&ye=2026"
    ]
    custom_settings ={
        "ROBOTSTXT_OBEY": False,
        #let 403 errors go into parse instead of ignored
        "HTTPERROR_ALLOWED_CODES": [403],
        
        #limits download speeds to be nice
        "DOWNLOAD_DELAY": 1.0,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 2.0,
        "AUTOTHROTTLE_MAX_DELAY": 5.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0,
        "RETRY_TIMES": 2,

        #look like a browser
        "USER_AGENT":(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0 Safari/537.36"
        ),
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://secure.meetcontrol.com/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    }
    
    def parse(self, response):
        rows = response.xpath('//tr[@bgcolor]')
        
        for row in rows:
            yield {
                "meet_name": row.xpath('.//div[@style="font-size: 9px"]/text()').get(),
                "results_url": row.xpath('.//a[contains(@href, "meetresultsext.php")]/@href').get(),
                "start_date": row.xpath('.//td[@valign="top"][@style="font-size: 9px"][1]/text()').get(),
                "location": row.xpath('.//td[@valign="top"][@style="font-size: 9px"][3]/text()').get(),
            }

        next_page = response.xpath('//a[contains(text(), "Next 200 Meets")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

