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
        "DOWNLOAD_DELAY": 2.0,
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
            tds = row.xpath('./td')
            if len(tds) < 5:
                continue

            meet_name = tds[1].xpath('.//div[contains(@style, "font-size: 9px")]/text()').get()
            results_link = tds[1].xpath('.//a/@href').get()
            start_date = tds[2].xpath('string(.)').get(default='').strip()
            location = tds[4].xpath('string(.)').get(default='').strip()

            if results_link:
                yield response.follow(
                    results_link,
                    callback=self.parse_meet,
                    meta={
                        "meet_name": meet_name,
                        "start_date": start_date,
                        "location": location,
                    }
                )

        next_page = response.xpath('//a[contains(text(), "Next 200 Meets")]/@href').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_meet(self, response):
        meet_name = response.meta.get("meet_name")
        start_date = response.meta.get("start_date")
        location = response.meta.get("location")

        rows = response.xpath('//tr[@bgcolor="DDDDDD"]')
        for row in rows:
            tds = row.xpath('./td')
            if len(tds) < 1:
                continue

           
            event_link = tds[0].xpath('.//a/@href').get()
            event_name = tds[0].xpath('.//a/text()').get()
            event_round = tds[0].xpath('.//a/following-sibling::text()').get(default='').strip()
            full_event_name = f"{event_name} {event_round}".strip() if event_name else None
            
            if event_link:
                self.logger.info(f"OPENING EVENT: {event_name} - {event_link}")
                yield response.follow(
                    event_link,
                    callback=self.parse_event,
                    meta={
                        "meet_name": meet_name,
                        "start_date": start_date,
                        "location": location,
                        "event_name": full_event_name,
                    }
                )

    def parse_event(self, response):
        pass