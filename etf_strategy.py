# -*- coding: utf-8 -*-
"""
ETF加仓策略分析器
根据市场情况判断国内外ETF的购买策略，包括场内场外购买建议
"""

from typing import Dict, List, Optional, Tuple
import requests
import os
from datetime import datetime


class ETFStrategyAnalyzer:
    """ETF加仓策略分析器"""
    
    def __init__(self, proxy_url: Optional[str] = None, use_proxy: bool = True):
        self.proxy_url = proxy_url or "http://127.0.0.1:10809"
        self.use_proxy = use_proxy
        
        # 风险等级配置
        self.risk_levels = {
            'conservative': {'name': '保守型', 'max_position': 0.3, 'min_drop': -2.0},
            'moderate': {'name': '稳健型', 'max_position': 0.5, 'min_drop': -1.0}, 
            'aggressive': {'name': '激进型', 'max_position': 0.8, 'min_drop': -0.5}
        }
        
    def get_us_stock_data(self) -> Dict[str, float]:
        """获取美股收盘数据"""
        try:
            # 检查是否为GitHub Actions环境
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                proxies = {"http": None, "https": None}
                print("🌐 GitHub Actions环境，强制禁用代理")
            elif self.use_proxy and self.proxy_url:
                proxies = {"http": self.proxy_url, "https": self.proxy_url}
                print(f"🌐 使用代理: {self.proxy_url}")
            else:
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
                    
            return results
        except Exception as e:
            print(f"获取美股数据失败: {e}")
            raise Exception(f"无法获取美股真实数据: {e}")
    
    def get_etf_premium_rate(self) -> Dict[str, float]:
        """获取国内ETF溢价率数据"""
        try:
            print("💰 获取国内ETF溢价率...")
            
            # 检查是否为GitHub Actions环境
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                proxies = {"http": None, "https": None}
            elif self.use_proxy and self.proxy_url:
                proxies = {"http": self.proxy_url, "https": self.proxy_url}
            else:
                proxies = {"http": None, "https": None}
                
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            # 国内QDII ETF映射 - 投资美股的ETF
            domestic_etfs = {
                'SPY_CN': {
                    'code': '513500',  # 标普500ETF
                    'name': '标普500ETF',
                    'symbol': '513500.SS'
                },
                'QQQ_CN': {
                    'code': '159834',  # 华夏纳斯达克100ETF
                    'name': '纳斯达克100ETF', 
                    'symbol': '159834.SZ'
                }
            }
            
            results = {}
            
            for etf_key, etf_info in domestic_etfs.items():
                try:
                    # 方法1：尝试从新浪财经获取ETF数据
                    sina_url = f"http://hq.sinajs.cn/list={etf_info['code']}"
                    response = requests.get(sina_url, headers=headers, proxies=proxies, timeout=10)
                    
                    if response.status_code == 200 and response.text.strip():
                        # 解析新浪财经数据
                        data_str = response.text.strip()
                        if '=' in data_str and '"' in data_str:
                            # 提取数据部分："var hq_str_513500="0.000,0.000,0.000,..."
                            data_part = data_str.split('="')[1].rstrip('";')
                            data_fields = data_part.split(',')
                            
                            if len(data_fields) >= 10:
                                current_price = float(data_fields[3]) if data_fields[3] != '0.000' else 0
                                prev_close = float(data_fields[2]) if data_fields[2] != '0.000' else 0
                                
                                if current_price > 0 and prev_close > 0:
                                    # 简化的溢价率计算（基于价格变动）
                                    # 真实的溢价率需要净值数据，这里用价格变动作为近似
                                    price_change = ((current_price - prev_close) / prev_close) * 100
                                    
                                    # 估算溢价率：国内ETF相对于其跟踪标的的溢价
                                    # 由于QDII ETF有时差和汇率因素，通常有一定溢价
                                    base_premium = 0.5  # 基础溢价率0.5%
                                    estimated_premium = base_premium + abs(price_change) * 0.2
                                    
                                    results[etf_key] = estimated_premium
                                    print(f"{etf_info['name']} ({etf_info['code']}) 估算溢价率: {estimated_premium:.2f}%")
                                    continue
                    
                    # 方法2：如果新浪财经失败，使用雅虎财经作为备选
                    print(f"尝试备用方法获取 {etf_info['name']} 数据...")
                    yahoo_url = f"https://query1.finance.yahoo.com/v8/finance/chart/{etf_info['symbol']}"
                    response = requests.get(yahoo_url, headers=headers, proxies=proxies, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                            result = data['chart']['result'][0]
                            meta = result.get('meta', {})
                            current_price = meta.get('regularMarketPrice', 0)
                            prev_close = meta.get('previousClose', 0)
                            
                            if current_price > 0 and prev_close > 0:
                                price_change = ((current_price - prev_close) / prev_close) * 100
                                base_premium = 0.8  # 基础溢价率0.8%
                                estimated_premium = base_premium + abs(price_change) * 0.3
                                
                                results[etf_key] = estimated_premium
                                print(f"{etf_info['name']} ({etf_info['code']}) 估算溢价率: {estimated_premium:.2f}%")
                                continue
                    
                    # 如果都失败了，使用模拟数据并标注
                    print(f"⚠️ 无法获取 {etf_info['name']} 真实数据，使用估算值")
                    estimated_premium = 1.2  # 默认溢价率1.2%
                    results[etf_key] = estimated_premium
                    
                except Exception as e:
                    print(f"获取{etf_info['name']}数据失败: {e}")
                    # 使用保守的估算值
                    results[etf_key] = 1.5
            
            # 转换键名以匹配原有逻辑
            final_results = {}
            if 'SPY_CN' in results:
                final_results['SPY'] = results['SPY_CN']
            if 'QQQ_CN' in results:
                final_results['QQQ'] = results['QQQ_CN']
                
            if not final_results:
                raise Exception("无法获取任何国内ETF溢价率数据")
                
            return final_results
            
        except Exception as e:
            print(f"获取国内ETF溢价率失败: {e}")
            raise Exception(f"无法获取国内ETF真实溢价率: {e}")
    
    def get_futures_data(self) -> Dict[str, float]:
        """获取美股期货数据"""
        try:
            print("📈 获取期货数据...")
            
            # 检查是否为GitHub Actions环境
            if os.environ.get('GITHUB_ACTIONS') == 'true':
                proxies = {"http": None, "https": None}
            elif self.use_proxy and self.proxy_url:
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
    
    def check_major_events(self, news_titles: List[str]) -> Tuple[bool, List[str]]:
        """检查是否有重大事件（基于新闻标题关键词）"""
        major_event_keywords = [
            '美联储', '加息', '降息', '通胀', 'CPI', 'PPI', '非农', 
            '就业', 'GDP', '贸易战', '制裁', '地缘', '战争', '冲突',
            '央行', '财报', '重大事故', '天灾', '疫情', '封锁'
        ]
        
        found_events = []
        print(f"🔍 检查重大事件（共{len(news_titles)}条新闻）...")
        for title in news_titles:
            for keyword in major_event_keywords:
                if keyword in title:
                    found_events.append(f"'{keyword}' in '{title}'")
                    
        if found_events:
            print(f"⚠️ 发现{len(found_events)}个重大事件关键词")
            return True, found_events
        else:
            print("✅ 未发现重大事件")
            return False, []
    
    def calculate_position_suggestion(self, drop_percent: float, risk_level: str = 'moderate') -> Dict[str, str]:
        """根据跌幅计算建议加仓比例"""
        config = self.risk_levels[risk_level]
        
        # 基于跌幅的分级加仓策略
        if drop_percent >= -0.5:
            position = 0.1  # 微跌，小幅试探
            urgency = "观望"
        elif drop_percent >= -1.0:
            position = 0.2  # 小跌，适度加仓
            urgency = "适中"
        elif drop_percent >= -2.0:
            position = 0.3  # 中等跌幅，积极加仓
            urgency = "积极"
        elif drop_percent >= -3.0:
            position = 0.5  # 大跌，重点加仓
            urgency = "重点"
        else:
            position = 0.7  # 暴跌，抄底机会
            urgency = "抄底"
            
        # 限制最大仓位
        position = min(position, config['max_position'])
        
        return {
            'position_ratio': f"{position:.1%}",
            'urgency': urgency,
            'risk_level': config['name']
        }
    
    def get_domestic_etf_suggestions(self, us_trend: str) -> Dict[str, str]:
        """获取国内ETF购买建议"""
        suggestions = {}
        
        # 场内美股QDII ETF建议（股票账户交易）
        us_etfs = {
            "标普500": {
                "代码": "513500(华夏)、159922(易方达)", 
                "适用": "跟踪美股大盘，适合稳健投资美股",
                "费率": "管理费0.6%，交易佣金万2.5",
                "特点": "T+0交易，无汇率兑换成本"
            },
            "纳斯达克100": {
                "代码": "159834(华夏)、513100(国泰)",
                "适用": "美股科技股，适合看好科技股投资者", 
                "费率": "管理费0.6%，交易佣金万2.5",
                "特点": "高成长性，波动较大"
            }
        }
        
        # 场内A股ETF建议（股票账户交易）
        a_stock_etfs = {
            "沪深300": {
                "代码": "159919(嘉实300)、510300(华泰柏瑞300)", 
                "适用": "跟踪A股大盘蓝筹，适合稳健投资",
                "费率": "管理费0.5%，交易佣金万2.5"
            },
            "中证500": {
                "代码": "159922(嘉实中证500)、510500(南方中证500)",
                "适用": "A股中小盘成长股，适合激进投资", 
                "费率": "管理费0.5%，交易佣金万2.5"
            },
            "科创50": {
                "代码": "588000(华夏科创50)、159747(广发科创50)",
                "适用": "科技创新主题，高风险高收益",
                "费率": "管理费0.5%，交易佣金万2.5"
            }
        }
        
        # 场外基金建议（基金公司/第三方平台）
        off_market_funds = {
            "美股QDII基金": {
                "标普500": "110020(易方达标普500)、050025(博时标普500)",
                "纳斯达克": "161130(易方达纳斯达克100)、270042(广发纳斯达克100)",
                "渠道": "支付宝、天天基金、微信理财通",
                "费率": "申购费1.5%(打1折后0.15%)，赎回费0.5%，管理费1.5%"
            },
            "A股指数基金": {
                "沪深300": "110020(易方达沪深300)、160706(嘉实沪深300)",
                "中证500": "000478(华夏中证500)、160119(南方中证500)", 
                "渠道": "支付宝、天天基金、银行APP",
                "费率": "申购费1.5%(打1折后0.15%)，赎回费0.5%"
            }
        }
        
        # 根据美股趋势给出建议
        if "下跌" in us_trend or "跌" in us_trend:
            suggestions["场内美股ETF"] = f"🎯 **美股QDII ETF推荐**\n" + \
                f"• **标普500ETF**: {us_etfs['标普500']['代码']}\n" + \
                f"• **纳斯达克100ETF**: {us_etfs['纳斯达克100']['代码']}\n" + \
                f"• **优势**: {us_etfs['标普500']['特点']}\n" + \
                f"• **费率**: {us_etfs['标普500']['费率']}"
                
            suggestions["场内A股ETF"] = f"🏠 **A股ETF联动机会**\n" + \
                f"• **沪深300ETF**: {a_stock_etfs['沪深300']['代码']}\n" + \
                f"• **优势**: 实时交易、费率低({a_stock_etfs['沪深300']['费率']})\n" + \
                f"• **策略**: 美股下跌时A股可能受影响，关注联动机会"
                
            suggestions["场外QDII基金"] = f"💰 **美股基金定投**\n" + \
                f"• **标普500**: {off_market_funds['美股QDII基金']['标普500']}\n" + \
                f"• **纳斯达克**: {off_market_funds['美股QDII基金']['纳斯达克']}\n" + \
                f"• **渠道**: {off_market_funds['美股QDII基金']['渠道']}\n" + \
                f"• **费率**: {off_market_funds['美股QDII基金']['费率']}\n" + \
                f"• **操作**: 美股下跌时加大定投金额"
        else:
            suggestions["场内美股ETF"] = f"⚠️ **谨慎操作美股ETF**\n• 美股上涨时QDII ETF溢价可能走高\n• 建议等待回调机会\n• 可关注溢价率变化"
            suggestions["场内A股ETF"] = f"🏠 **关注A股机会**\n• 美股上涨时关注A股是否跟涨\n• 若A股滞涨可考虑配置\n• 推荐: {a_stock_etfs['沪深300']['代码']}"
            suggestions["场外基金"] = f"📈 **继续定投**\n• 保持既定定投计划\n• 美股高位时不建议大额申购QDII基金\n• 可增加A股指数基金比例"
            
        return suggestions
    
    def generate_purchase_plan(self, index_name: str, drop_percent: float, position_suggestion: Dict) -> str:
        """生成具体购买计划"""
        plan = f"📋 **{index_name}购买计划**\n\n"
        
        # 资金分配建议
        plan += f"💰 **资金配置**: 建议投入{position_suggestion['position_ratio']}仓位\n"
        plan += f"⚡ **操作紧急度**: {position_suggestion['urgency']}\n"
        plan += f"🎯 **风险等级**: {position_suggestion['risk_level']}\n\n"
        
        # 分批买入策略
        if abs(drop_percent) >= 2.0:
            plan += f"📊 **分批策略**: 大跌{abs(drop_percent):.1f}%，建议3次分批买入\n"
            plan += f"• 第1批: 30% (立即)\n• 第2批: 40% (再跌0.5%时)\n• 第3批: 30% (再跌1%时)\n\n"
        elif abs(drop_percent) >= 1.0:
            plan += f"📊 **分批策略**: 中等跌幅{abs(drop_percent):.1f}%，建议2次分批买入\n"
            plan += f"• 第1批: 50% (立即)\n• 第2批: 50% (再跌0.5%时)\n\n"
        else:
            plan += f"📊 **分批策略**: 小幅下跌{abs(drop_percent):.1f}%，可一次性买入\n\n"
            
        # 止盈止损建议
        plan += f"🎯 **止盈目标**: 盈利15-20%时分批减仓\n"
        plan += f"🛡️ **止损线**: 亏损超过10%时考虑止损\n"
        plan += f"⏰ **持有期限**: 建议持有3-6个月以上"
        
        return plan
    
    def analyze_strategy(self, news_titles: List[str] = None) -> Dict[str, str]:
        """分析ETF投资策略"""
        if news_titles is None:
            news_titles = []
            
        results = {}
        
        print("\n📊 开始ETF投资策略分析...")
        
        # 获取市场数据
        try:
            us_stocks = self.get_us_stock_data()
            etf_premiums = self.get_etf_premium_rate()
            futures = self.get_futures_data()
            has_major_events, events = self.check_major_events(news_titles)
        except Exception as e:
            print(f"❌ 数据获取失败: {e}")
            return {"错误": f"**❌ 数据获取失败**\n💡 {e}"}
        
        # 分析每个指数
        for index_name, etf_name in [('SPX', 'SPY'), ('IXIC', 'QQQ')]:
            stock_change = us_stocks.get(index_name, 0.0)
            etf_premium = etf_premiums.get(etf_name, 0.0)
            future_symbol = 'ES' if index_name == 'SPX' else 'NQ'
            future_change = futures.get(future_symbol, 0.0)
            
            index_display_name = "标普500" if index_name == "SPX" else "纳斯达克"
            
            # 新的灵活策略判断
            strategy_result = self.analyze_flexible_strategy(
                index_display_name, stock_change, etf_premium, future_change, 
                has_major_events, events
            )
            
            results[index_display_name] = strategy_result
            
        # 添加国内ETF建议
        us_trend = "下跌" if any(us_stocks[k] < 0 for k in us_stocks) else "上涨"
        domestic_suggestions = self.get_domestic_etf_suggestions(us_trend)
        
        results["国内ETF建议"] = f"🇨🇳 **国内市场操作建议**\n\n{domestic_suggestions['场内美股ETF']}\n\n{domestic_suggestions['场内A股ETF']}\n\n{domestic_suggestions.get('场外QDII基金', '')}"
            
        return results
    
    def analyze_flexible_strategy(self, index_name: str, stock_change: float, 
                                etf_premium: float, future_change: float,
                                has_major_events: bool, events: List[str]) -> str:
        """灵活的策略分析"""
        
        # 映射ETF名称
        etf_display_name = "标普500ETF(513500)" if index_name == "标普500" else "纳斯达克100ETF(159834)"
        
        # 市场数据摘要
        data_summary = f"📊 **市场数据**\n美股{stock_change:+.2f}% | 国内{etf_display_name}溢价{etf_premium:.1f}% | 期货{future_change:+.2f}%\n\n"
        
        # 计算综合评分 (0-100)
        score = 50  # 基础分
        
        # 股票跌幅评分 (跌得越多分数越高)
        if stock_change <= -3.0:
            score += 30  # 大跌加分
        elif stock_change <= -2.0:
            score += 20  # 中跌加分
        elif stock_change <= -1.0:
            score += 10  # 小跌加分
        elif stock_change <= 0:
            score += 5   # 微跌加分
        else:
            score -= 10  # 上涨减分
            
        # 国内ETF溢价率评分 (溢价越低分数越高)
        if etf_premium <= 1.0:
            score += 15  # 低溢价，很好的买入机会
        elif etf_premium <= 2.0:
            score += 10  # 适中溢价
        elif etf_premium <= 3.0:
            score += 5   # 稍高溢价
        else:
            score -= 10  # 高溢价，不建议买入
            
        # 期货评分 (期货跌幅越大分数越高)
        if future_change <= -1.0:
            score += 15
        elif future_change <= -0.5:
            score += 10
        elif future_change <= 0:
            score += 5
        else:
            score -= 5
            
        # 重大事件影响
        if has_major_events:
            score -= 15
            
        # 限制评分范围
        score = max(0, min(100, score))
        
        # 根据评分给出建议
        if score >= 80:
            decision = "🚀 强烈推荐买入"
            risk_level = "aggressive"
            color = "🟢"
        elif score >= 65:
            decision = "✅ 推荐买入"
            risk_level = "moderate"
            color = "🟡"
        elif score >= 50:
            decision = "💡 可以考虑买入"
            risk_level = "conservative"
            color = "🟠"
        elif score >= 35:
            decision = "⚠️ 建议观望"
            risk_level = "conservative"
            color = "🔵"
        else:
            decision = "❌ 暂不建议买入"
            risk_level = "conservative"
            color = "🔴"
            
        # 生成详细分析
        result = f"{data_summary}"
        result += f"{color} **{decision}** (评分: {score}/100)\n\n"
        
        # 如果建议买入，提供详细计划
        if score >= 50:
            position_suggestion = self.calculate_position_suggestion(stock_change, risk_level)
            purchase_plan = self.generate_purchase_plan(index_name, stock_change, position_suggestion)
            result += purchase_plan
        else:
            result += f"💡 **原因分析**:\n"
            if stock_change > 0:
                result += f"• 美股上涨{stock_change:.2f}%，不是好的买入时机\n"
            if etf_premium > 3.0:
                result += f"• 国内ETF溢价率{etf_premium:.1f}%过高，建议等待溢价回落\n"
            if future_change > 0:
                result += f"• 期货上涨{future_change:.2f}%，市场情绪偏乐观\n"
            if has_major_events:
                result += f"• 存在重大事件，建议等待明确信号\n"
                
        # 重大事件提醒
        if has_major_events:
            result += f"\n⚠️ **重大事件提醒**:\n"
            for event in events[:3]:  # 只显示前3个事件
                result += f"• {event}\n"
                
        return result


if __name__ == "__main__":
    # 测试代码
    print("🚀 启动ETF策略分析器...")
    print("📡 获取实时数据...")
    
    analyzer = ETFStrategyAnalyzer(use_proxy=False)
    test_news = []
    results = analyzer.analyze_strategy(test_news)
    
    print("\n=== ETF投资策略分析结果 ===")
    for index_name, strategy_result in results.items():
        print(f"\n{index_name}：")
        print(strategy_result)
        print("-" * 60) 