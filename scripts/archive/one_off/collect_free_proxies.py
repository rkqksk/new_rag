#!/usr/bin/env python3
"""
무료 프록시 수집 및 검증 스크립트
- 여러 소스에서 무료 프록시 수집
- 동작하는 프록시만 필터링
- 한국 접근 가능한 프록시 우선
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import re


class FreeProxyCollector:
    """무료 프록시 수집기"""

    def __init__(self, output_file: str = "data/freemold/free_proxies.json"):
        self.output_file = Path(output_file)
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.proxies = []

    async def collect_from_api(self):
        """공개 API에서 프록시 수집"""
        apis = [
            "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        ]

        async with aiohttp.ClientSession() as session:
            for api_url in apis:
                try:
                    print(f"📥 Fetching from: {api_url[:50]}...")
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            text = await response.text()
                            # IP:Port 형식 파싱
                            proxy_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{2,5})'
                            matches = re.findall(proxy_pattern, text)

                            for ip, port in matches:
                                proxy_url = f"http://{ip}:{port}"
                                if proxy_url not in [p['url'] for p in self.proxies]:
                                    self.proxies.append({
                                        'url': proxy_url,
                                        'ip': ip,
                                        'port': port,
                                        'source': api_url[:30],
                                        'tested': False,
                                        'working': False
                                    })

                            print(f"  ✅ Found {len(matches)} proxies")
                except Exception as e:
                    print(f"  ❌ Failed: {e}")

        print(f"\n📊 Total proxies collected: {len(self.proxies)}")

    async def test_proxy(self, proxy: Dict, timeout: int = 3) -> bool:
        """프록시 동작 테스트"""
        proxy_url = proxy['url']
        test_urls = [
            "http://httpbin.org/ip",
            "http://ip-api.com/json",
        ]

        try:
            async with aiohttp.ClientSession() as session:
                for test_url in test_urls:
                    try:
                        async with session.get(
                            test_url,
                            proxy=proxy_url,
                            timeout=aiohttp.ClientTimeout(total=timeout)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                proxy['tested'] = True
                                proxy['working'] = True
                                proxy['response_time'] = response.headers.get('X-Response-Time', 'unknown')
                                proxy['test_url'] = test_url
                                proxy['tested_at'] = datetime.now().isoformat()
                                return True
                    except:
                        continue
        except Exception as e:
            pass

        proxy['tested'] = True
        proxy['working'] = False
        return False

    async def validate_proxies(self, max_concurrent: int = 50):
        """수집한 프록시 검증"""
        print(f"\n🔍 Testing {len(self.proxies)} proxies (max {max_concurrent} concurrent)...")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def test_with_semaphore(proxy):
            async with semaphore:
                return await self.test_proxy(proxy)

        tasks = [test_with_semaphore(proxy) for proxy in self.proxies]
        results = await asyncio.gather(*tasks)

        working_count = sum(results)
        print(f"\n✅ Working proxies: {working_count}/{len(self.proxies)} ({working_count/len(self.proxies)*100:.1f}%)")

    def save_proxies(self):
        """프록시 리스트 저장"""
        # 동작하는 프록시만 필터링
        working_proxies = [p for p in self.proxies if p.get('working', False)]

        output_data = {
            'total_collected': len(self.proxies),
            'working': len(working_proxies),
            'collected_at': datetime.now().isoformat(),
            'proxies': working_proxies
        }

        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n💾 Saved {len(working_proxies)} working proxies to: {self.output_file}")

        # 간단한 텍스트 파일로도 저장
        txt_file = self.output_file.with_suffix('.txt')
        with open(txt_file, 'w') as f:
            for proxy in working_proxies:
                f.write(f"{proxy['url']}\n")

        print(f"💾 Also saved to: {txt_file}")

    async def run(self):
        """전체 프로세스 실행"""
        print("=" * 60)
        print("🌐 Free Proxy Collector")
        print("=" * 60)

        # 1. 프록시 수집
        await self.collect_from_api()

        # 2. 프록시 검증
        if self.proxies:
            await self.validate_proxies()

            # 3. 저장
            self.save_proxies()

            # 4. 통계
            working = [p for p in self.proxies if p.get('working')]
            if working:
                print("\n📊 Statistics:")
                print(f"  Total collected: {len(self.proxies)}")
                print(f"  Working: {len(working)}")
                print(f"  Success rate: {len(working)/len(self.proxies)*100:.1f}%")
                print(f"\n🎯 Ready for crawling!")
            else:
                print("\n⚠️ No working proxies found. Try again later.")
        else:
            print("\n❌ No proxies collected. Check network connection.")

        print("=" * 60)


async def main():
    collector = FreeProxyCollector()
    await collector.run()


if __name__ == "__main__":
    asyncio.run(main())
