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
        "DEPTH_PRIORITY": 1,
        "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
        "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
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
    
    def parse(self, response, meet_count=0):
        rows = response.xpath('//tr[@bgcolor]')
        
        for row in rows:
            if meet_count >= 4:
                return

            tds = row.xpath('./td')
            if len(tds) < 5:
                continue

            meet_name = tds[1].xpath('.//div[contains(@style, "font-size: 9px")]/text()').get()
            results_link = tds[1].xpath('.//a/@href').get()
            start_date = tds[2].xpath('string(.)').get(default='').strip()
            location = tds[4].xpath('string(.)').get(default='').strip()

            if results_link:
                meet_count += 1
                yield response.follow(
                    results_link,
                    callback=self.parse_meet,
                    meta={
                        "meet_name": meet_name,
                        "start_date": start_date,
                        "location": location,
                    }
                )

        if meet_count < 4:
            next_page = response.xpath('//a[contains(text(), "Next 200 Meets")]/@href').get()
            if next_page:
                yield response.follow(
                    next_page,
                    callback=self.parse,
                    cb_kwargs={"meet_count": meet_count}
                )

    def parse_meet(self, response):
        meet_name = response.meta.get("meet_name")
        start_date = response.meta.get("start_date")
        location = response.meta.get("location")

        rows = response.xpath('//tr[.//a[contains(@href, "eventresultsext.php")]]')
        for row in rows:
            tds = row.xpath('./td')
            if len(tds) < 1:
                continue

           
            event_link = tds[0].xpath('.//a/@href').get()
            event_name = tds[0].xpath('.//a/text()').get()
            event_round = tds[0].xpath('.//a/following-sibling::text()').get(default='').strip()
            full_event_name = f"{event_name} {event_round}".strip() if event_name else None
            

            if event_link and 'eventnum=all' not in event_link:
                self.logger.info(f"OPENING EVENT: {full_event_name} - {event_link}")
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
        meet_name = response.meta.get("meet_name")
        start_date = response.meta.get("start_date")
        location = response.meta.get("location")
        event_name = response.meta.get("event_name")

        rows = response.xpath('//tr[td[@valign="top"]]')
        for row in rows:
            tds = row.xpath('./td')
            if len(tds) < 4:
                continue

            diver_link = tds[0].xpath('.//a/@href').get()
            diver_name = tds[0].xpath('.//a/text()').get()
            team = tds[1].xpath('string(.)').get(default='').strip()
            place = tds[2].xpath('string(.)').get(default='').strip()
            score = tds[3].xpath('.//a/text()').get()

            # extract diver_id from profile.php?number=171039
            diver_id = None
            if diver_link and 'number=' in diver_link:
                diver_id = diver_link.split('number=')[1].split('&')[0]

            if diver_name and place:
                yield {
                    "meet_name": meet_name,
                    "start_date": start_date,
                    "location": location,
                    "event_name": event_name,
                    "diver_id": diver_id,
                    "diver_name": diver_name,
                    "team": team,
                    "place": place,
                    "score": score,
                }