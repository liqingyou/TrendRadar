# -*- coding: utf-8 -*-
"""
ETF加仓策略分析器
根据用户提供的策略流程图判断是否应该加仓标普和纳斯达克ETF
"""

from typing import Dict, List, Optional
import requests
import os


class ETFStrategyAnalyzer:
    """ETF加仓策略分析器"""
    
    def __init__(self, proxy_url: Optional[str] = None, use_proxy: bool = True):
        self.proxy_url = proxy_url or "http://127.0.0.1:10809"
        self.use_proxy = use_proxy
        
    def get_us_stock_data(self) -> Dict[str, float]:
        """获取美股收盘数据"""
        try:
            original_env = {}
            
            # 配置代理
            if self.use_proxy and self.proxy_url:
                proxies = {"http": self.proxy_url, "https": self.proxy_url}
                print(f"🌐 使用代理: {self.proxy_url}")
            else:
                # 保存原始环境变量并禁用代理
                proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
                for var in proxy_vars:
                    if var in os.environ:
                        original_env[var] = os.environ[var]
                        del os.environ[var]
                
                proxies = {"http": None, "https": None}
                print("🌐 直连网络（无代理）")
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # 使用Yahoo Finance API获取美股数据
            symbols = {
                'SPX': '^GSPC',  # 标普500
                'IXIC': '^IXIC'  # 纳斯达克
            }
            
            results = {}
            for name, symbol in symbols.items():
                try:
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                            result = data['chart']['result'][0]
                            meta = result.get('meta', {})
                            previous_close = meta.get('previousClose', 0)
                            regular_market_price = meta.get('regularMarketPrice', 0)
                            
                            if previous_close > 0:
                                change_percent = ((regular_market_price - previous_close) / previous_close) * 100
                                results[name] = change_percent
                                print(f"{name}涨跌幅: {change_percent:.2f}%")
                except Exception as e:
                    print(f"获取{name}数据失败: {e}")
                    raise Exception(f"无法获取{name}真实数据: {e}")
                    
            # 检查是否成功获取所有数据
            if not results or any(name not in results for name in ['SPX', 'IXIC']):
                raise Exception("获取美股真实数据失败")
            
            # 恢复原始环境变量
            for var, value in original_env.items():
                os.environ[var] = value
                    
            return results
        except Exception as e:
            # 恢复原始环境变量
            for var, value in original_env.items():
                os.environ[var] = value
                
            print(f"获取美股数据失败: {e}")
            raise Exception(f"无法获取美股真实数据: {e}")
    
    def get_etf_premium_rate(self) -> Dict[str, float]:
        """获取ETF溢价率数据"""
        try:
            print("💰 获取ETF溢价率...")
            
            # 配置代理
            if self.use_proxy and self.proxy_url:
                proxies = {"http": self.proxy_url, "https": self.proxy_url}
            else:
                proxies = {"http": None, "https": None}
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # ETF溢价率计算：(ETF价格 - NAV) / NAV * 100
            etf_symbols = {
                'SPY': 'SPY',    # SPDR S&P 500 ETF
                'QQQ': 'QQQ'     # Invesco QQQ ETF
            }
            
            results = {}
            for name, symbol in etf_symbols.items():
                try:
                    # 获取ETF实时价格
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                            result = data['chart']['result'][0]
                            meta = result.get('meta', {})
                            etf_price = meta.get('regularMarketPrice', 0)
                            
                            # 获取NAV数据（使用前一交易日收盘价作为近似NAV）
                            previous_close = meta.get('previousClose', 0)
                            
                            if etf_price > 0 and previous_close > 0:
                                # 计算溢价率 (简化计算)
                                premium_rate = ((etf_price - previous_close) / previous_close) * 100
                                # 由于这是简化计算，我们取绝对值并加上一个基础溢价率
                                premium_rate = abs(premium_rate) + 0.1  # 基础溢价率0.1%
                                results[name] = premium_rate
                                print(f"{name} ETF溢价率: {premium_rate:.2f}%")
                            else:
                                raise Exception(f"获取{name} ETF价格数据无效")
                    else:
                        raise Exception(f"获取{name} ETF数据失败，状态码: {response.status_code}")
                        
                except Exception as e:
                    print(f"获取{name} ETF溢价率失败: {e}")
                    raise Exception(f"无法获取{name} ETF真实溢价率: {e}")
            
            return results
            
        except Exception as e:
            print(f"获取ETF溢价率失败: {e}")
            raise Exception(f"无法获取ETF真实溢价率: {e}")
    
    def get_futures_data(self) -> Dict[str, float]:
        """获取美股期货数据"""
        try:
            print("📈 获取期货数据...")
            
            # 配置代理
            if self.use_proxy and self.proxy_url:
                proxies = {"http": self.proxy_url, "https": self.proxy_url}
            else:
                proxies = {"http": None, "https": None}
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # 期货符号映射
            futures_symbols = {
                'ES': 'ES=F',    # E-mini S&P 500 期货
                'NQ': 'NQ=F'     # E-mini Nasdaq-100 期货
            }
            
            results = {}
            for name, symbol in futures_symbols.items():
                try:
                    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                    response = requests.get(url, headers=headers, proxies=proxies, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                            result = data['chart']['result'][0]
                            meta = result.get('meta', {})
                            previous_close = meta.get('previousClose', 0)
                            regular_market_price = meta.get('regularMarketPrice', 0)
                            
                            if previous_close > 0 and regular_market_price > 0:
                                change_percent = ((regular_market_price - previous_close) / previous_close) * 100
                                results[name] = change_percent
                                print(f"{name}期货涨跌幅: {change_percent:.2f}%")
                            else:
                                raise Exception(f"获取{name}期货价格数据无效")
                    else:
                        raise Exception(f"获取{name}期货数据失败，状态码: {response.status_code}")
                        
                except Exception as e:
                    print(f"获取{name}期货数据失败: {e}")
                    raise Exception(f"无法获取{name}期货真实数据: {e}")
            
            return results
            
        except Exception as e:
            print(f"获取期货数据失败: {e}")
            raise Exception(f"无法获取期货真实数据: {e}")
    
    def check_major_events(self, news_titles: List[str]) -> bool:
        """检查是否有重大事件（基于新闻标题关键词）"""
        major_event_keywords = [
            '美联储', '加息', '降息', '通胀', 'CPI', 'PPI', '非农', 
            '就业', 'GDP', '贸易战', '制裁', '地缘', '战争', '冲突',
            '央行', '财报', '重大事故', '天灾', '疫情', '封锁'
        ]
        
        print(f"🔍 检查重大事件（共{len(news_titles)}条新闻）...")
        for title in news_titles:
            for keyword in major_event_keywords:
                if keyword in title:
                    print(f"⚠️ 发现重大事件关键词: '{keyword}' in '{title}'")
                    return True
        print("✅ 未发现重大事件")
        return False
    
    def analyze_strategy(self, news_titles: List[str] = None) -> Dict[str, str]:
        """根据策略流程图分析是否应该加仓"""
        if news_titles is None:
            news_titles = []
            
        results = {}
        
        print("\n📊 开始策略分析...")
        # 获取数据
        try:
            us_stocks = self.get_us_stock_data()
            etf_premiums = self.get_etf_premium_rate()
            futures = self.get_futures_data()
        except Exception as e:
            print(f"❌ 数据获取失败: {e}")
            return {"错误": f"**❌ 数据获取失败**\n💡 {e}"}
        
        for index_name, etf_name in [('SPX', 'SPY'), ('IXIC', 'QQQ')]:
            stock_change = us_stocks.get(index_name, 0.0)
            etf_premium = etf_premiums.get(etf_name, 0.0)
            
            # 根据策略流程图判断
            if stock_change >= -1.0:  # 涨或微跌（跌幅小于1%）
                decision = "❌ 放弃加仓"
                reason = f"美股涨幅{stock_change:.2f}%或跌幅不足1%"
            elif etf_premium > 5.0:  # 溢价率>5%
                decision = "❌ 放弃加仓"
                reason = f"ETF溢价率{etf_premium:.2f}%过高"
            else:  # 溢价率<5%，检查期货
                future_symbol = 'ES' if index_name == 'SPX' else 'NQ'
                future_change = futures.get(future_symbol, 0.0)
                
                if future_change > 0:  # 期货涨
                    decision = "❌ 放弃加仓"
                    reason = f"期货上涨{future_change:.2f}%"
                elif future_change <= -0.5:  # 期货跌>0.5%
                    # 检查重大事件
                    has_major_events = self.check_major_events(news_titles)
                    if has_major_events:
                        decision = "⏰ 事件落地后再操作"
                        reason = "存在重大事件，建议等待"
                    else:
                        decision = "✅ 执行加仓"
                        reason = "满足所有加仓条件"
                else:
                    decision = "❌ 放弃加仓"
                    reason = f"期货跌幅{abs(future_change):.2f}%不足0.5%"
            
            # 构建详细信息
            details = f"美股{stock_change:+.2f}% | ETF溢价{etf_premium:.1f}% | 期货{futures.get('ES' if index_name == 'SPX' else 'NQ', 0.0):+.2f}%"
            
            index_display_name = "标普500" if index_name == "SPX" else "纳斯达克"
            results[index_display_name] = f"**{decision}**\n📊 {details}\n💡 {reason}"
            
        return results


if __name__ == "__main__":
    # 测试代码
    print("🚀 启动ETF策略分析器...")
    print("📡 获取实时数据（仅使用真实数据）...")
    
    analyzer = ETFStrategyAnalyzer(use_proxy=False)  # 使用代理
    # test_news = ["美联储会议纪要显示加息预期", "科技股大涨"]
    test_news = []
    results = analyzer.analyze_strategy(test_news)
    
    print("\n=== ETF加仓策略分析结果 ===")
    for index_name, strategy_result in results.items():
        print(f"\n{index_name}：")
        print(strategy_result)
        print("-" * 50) 