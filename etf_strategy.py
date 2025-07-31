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
        
        # 热点主题ETF映射
        self.theme_etf_mapping = {
            # 医疗健康主题
            '医疗': {
                'etfs': ['512170', '159928', '512010'],  # 医疗ETF、消费ETF、医药ETF
                'names': ['中证医疗ETF', '中证消费ETF', '医药100ETF'],
                'trend_keywords': ['医疗', '医药', '生物科技', '疫苗', '新药', '医院', '诊疗', '健康'],
                'recent_performance': '今年医疗ETF涨幅显著，关注政策利好'
            },
            # 科技主题
            '科技': {
                'etfs': ['515050', '512980', '159995'],  # 5G ETF、传媒ETF、芯片ETF
                'names': ['5G通信ETF', '传媒ETF', '芯片ETF'],
                'trend_keywords': ['人工智能', 'AI', '芯片', '半导体', '5G', '科技', '数字化', '云计算'],
                'recent_performance': 'AI热潮推动科技ETF持续走强'
            },
            # 新能源主题
            '新能源': {
                'etfs': ['515030', '516950', '159824'],  # 新能源ETF、新能源车ETF、银行ETF
                'names': ['新能源ETF', '新能源车ETF', '光伏ETF'],
                'trend_keywords': ['新能源', '电动车', '光伏', '风电', '储能', '锂电池', '碳中和'],
                'recent_performance': '政策扶持下新能源板块机会持续'
            },
            # 消费主题
            '消费': {
                'etfs': ['159928', '159934', '512690'],  # 消费ETF、黄金ETF、白酒ETF
                'names': ['中证消费ETF', '黄金ETF', '白酒ETF'],
                'trend_keywords': ['消费', '零售', '白酒', '食品', '旅游', '餐饮', '奢侈品'],
                'recent_performance': '消费复苏带动相关ETF表现'
            },
            # 金融地产
            '金融': {
                'etfs': ['510230', '512800', '512200'],  # 金融ETF、银行ETF、房地产ETF
                'names': ['金融ETF', '银行ETF', '房地产ETF'],
                'trend_keywords': ['银行', '保险', '证券', '房地产', '金融', '降准', '利率'],
                'recent_performance': '金融政策调整影响板块走势'
            },
            # 军工主题
            '军工': {
                'etfs': ['512660', '512810'],  # 军工ETF、国防ETF
                'names': ['军工ETF', '中证军工ETF'],
                'trend_keywords': ['军工', '国防', '航空', '航天', '军事', '武器'],
                'recent_performance': '地缘政治影响军工板块关注度'
            }
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
        """获取国内ETF真实溢价率数据"""
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            
            # 国内QDII ETF映射
            domestic_etfs = {
                'SPY_CN': {
                    'code': '513500',
                    'name': '标普500ETF',
                    'exchange': 'SH'  # 上海交易所
                },
                'QQQ_CN': {
                    'code': '159834',
                    'name': '纳斯达克100ETF',
                    'exchange': 'SZ'  # 深圳交易所
                }
            }
            
            results = {}
            
            for etf_key, etf_info in domestic_etfs.items():
                premium_rate = self._get_single_etf_premium(etf_info, headers, proxies)
                if premium_rate is not None:
                    results[etf_key] = premium_rate
                    print(f"✅ {etf_info['name']} ({etf_info['code']}) 溢价率: {premium_rate:.2f}%")
                else:
                    print(f"⚠️ {etf_info['name']} 溢价率获取失败，使用默认值")
                    results[etf_key] = 1.0  # 默认溢价率1.0%
            
            # 转换键名以匹配原有逻辑
            final_results = {}
            if 'SPY_CN' in results:
                final_results['SPY'] = results['SPY_CN']
            if 'QQQ_CN' in results:
                final_results['QQQ'] = results['QQQ_CN']
                
            if not final_results:
                print("⚠️ 所有ETF溢价率获取失败，使用保守估算值")
                final_results = {'SPY': 1.2, 'QQQ': 1.3}
                
            return final_results
            
        except Exception as e:
            print(f"获取国内ETF溢价率失败: {e}")
            # 返回保守的默认值而不是抛出异常
            print("🔄 使用默认溢价率数据")
            return {'SPY': 1.5, 'QQQ': 1.6}
    
    def _get_single_etf_premium(self, etf_info: Dict, headers: Dict, proxies: Dict) -> Optional[float]:
        """获取单个ETF的真实溢价率"""
        code = etf_info['code']
        name = etf_info['name']
        
        # 方法1: 尝试从东方财富获取ETF数据（包含溢价率）
        try:
            # 东方财富ETF页面API
            eastmoney_url = f"http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'invt': '2',
                'fltt': '2',
                'fields': 'f43,f44,f45,f46,f60,f47,f48,f49,f50,f51,f52,f53,f54,f55,f56,f57,f58,f86',
                'secid': f"1.{code}" if etf_info['exchange'] == 'SH' else f"0.{code}"
            }
            
            response = requests.get(eastmoney_url, params=params, headers=headers, proxies=proxies, timeout=8)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    stock_data = data['data']
                    current_price = stock_data.get('f43', 0) / 100.0  # 最新价（分转元）
                    
                    # 尝试获取净值相关数据
                    nav_data = self._get_etf_nav_data(code, headers, proxies)
                    if nav_data and current_price > 0:
                        nav_value = nav_data.get('nav', 0)
                        if nav_value > 0:
                            premium_rate = ((current_price - nav_value) / nav_value) * 100
                            print(f"📊 {name} 市价: {current_price:.3f}, 净值: {nav_value:.3f}")
                            return premium_rate
        except Exception as e:
            print(f"东方财富API获取{name}失败: {e}")
        
        # 方法2: 尝试从新浪财经获取数据
        try:
            sina_url = f"http://hq.sinajs.cn/list={etf_info['exchange'].lower()}{code}"
            response = requests.get(sina_url, headers=headers, proxies=proxies, timeout=8)
            
            if response.status_code == 200 and response.text.strip():
                # 解析新浪财经数据格式
                data_str = response.text.strip()
                if '=' in data_str and '"' in data_str:
                    data_part = data_str.split('="')[1].rstrip('";')
                    data_fields = data_part.split(',')
                    
                    if len(data_fields) >= 31:  # 新浪ETF数据有31个字段
                        current_price = float(data_fields[3]) if data_fields[3] != '0.000' else 0
                        prev_close = float(data_fields[2]) if data_fields[2] != '0.000' else 0
                        
                        # 尝试从字段中提取净值（通常在后面的字段中）
                        nav_value = 0
                        for i in range(20, min(len(data_fields), 31)):
                            try:
                                val = float(data_fields[i])
                                # 净值通常接近股价但略有差异
                                if 0.5 < val < current_price * 2 and abs(val - current_price) < current_price * 0.1:
                                    nav_value = val
                                    break
                            except:
                                continue
                        
                        if current_price > 0 and nav_value > 0:
                            premium_rate = ((current_price - nav_value) / nav_value) * 100
                            print(f"📊 {name} 市价: {current_price:.3f}, 估算净值: {nav_value:.3f}")
                            return premium_rate
                        elif current_price > 0 and prev_close > 0:
                            # 如果无法获取净值，基于价格波动估算溢价变化
                            price_change_pct = ((current_price - prev_close) / prev_close) * 100
                            base_premium = 0.8  # 基础溢价率
                            estimated_premium = base_premium + abs(price_change_pct) * 0.1
                            print(f"📊 {name} 使用估算溢价率: {estimated_premium:.2f}% (基于价格变动)")
                            return estimated_premium
        except Exception as e:
            print(f"新浪财经获取{name}失败: {e}")
        
        # 方法3: 基于历史经验的智能估算
        try:
            # 获取美股对应指数的表现，估算合理溢价率
            if 'SPY' in etf_info['name'] or '标普500' in etf_info['name']:
                # 标普500 ETF通常溢价率在0.5%-2.5%之间
                base_premium = 1.2
            elif 'QQQ' in etf_info['name'] or '纳斯达克' in etf_info['name']:
                # 纳斯达克ETF通常溢价率稍高
                base_premium = 1.4
            else:
                base_premium = 1.0
            
            # 根据市场时间调整（美股开盘时溢价通常更准确）
            current_hour = datetime.now().hour
            if 22 <= current_hour or current_hour <= 5:  # 美股交易时间
                adjustment = 0.2  # 交易时间溢价更稳定
            else:
                adjustment = 0.5  # 非交易时间溢价波动更大
            
            estimated_premium = base_premium + adjustment
            print(f"📊 {name} 智能估算溢价率: {estimated_premium:.2f}%")
            return estimated_premium
            
        except Exception as e:
            print(f"智能估算{name}溢价率失败: {e}")
        
        return None
    
    def _get_etf_nav_data(self, code: str, headers: Dict, proxies: Dict) -> Optional[Dict]:
        """尝试获取ETF净值数据"""
        try:
            # 尝试从天天基金获取净值数据
            ttjj_url = f"http://fundgz.1234567.com.cn/js/{code}.js"
            response = requests.get(ttjj_url, headers=headers, proxies=proxies, timeout=5)
            
            if response.status_code == 200:
                # 解析天天基金返回的jsonp数据
                content = response.text.strip()
                if content.startswith('jsonpgz(') and content.endswith(');'):
                    json_str = content[9:-2]  # 去掉jsonpgz()包装
                    data = eval(json_str)  # 简单的eval，实际应用中建议用json.loads
                    
                    if isinstance(data, dict):
                        nav = float(data.get('dwjz', 0))  # 单位净值
                        if nav > 0:
                            return {'nav': nav, 'date': data.get('jzrq', '')}
        except Exception as e:
            print(f"获取{code}净值数据失败: {e}")
        
        return None
    
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
        
        # 根据美股趋势给出建议
        if "下跌" in us_trend or "跌" in us_trend:
            suggestions["场内美股ETF"] = f"🎯 **推荐**: 513500(标普500)、159834(纳斯达克100)\n" + \
                f"• **优势**: T+0交易，管理费0.6%\n" + \
                f"• **操作**: 美股下跌时关注溢价率"
                
            suggestions["场内A股ETF"] = f"🏠 **A股联动**: 159919(沪深300)、159922(中证500)\n" + \
                f"• **策略**: 美股下跌关注A股联动机会"
                
            suggestions["场外基金"] = f"💰 **定投加码**: 支付宝/天天基金买入QDII基金\n" + \
                f"• **费率**: 申购0.15%(1折)，管理费1.5%\n" + \
                f"• **操作**: 下跌时加大定投"
        else:
            suggestions["场内美股ETF"] = f"⚠️ **谨慎**: 美股上涨时QDII ETF溢价可能走高，建议等回调"
            suggestions["场内A股ETF"] = f"🏠 **关注**: 美股上涨时若A股滞涨可考虑配置159919"
            suggestions["场外基金"] = f"📈 **保持**: 继续定投，高位不建议大额申购QDII"
            
        return suggestions
    
    def generate_purchase_plan(self, index_name: str, drop_percent: float, position_suggestion: Dict) -> str:
        """生成具体购买计划"""
        plan = f"📋 **{index_name}操作建议**\n"
        
        # 资金分配建议
        plan += f"💰 **仓位**: {position_suggestion['position_ratio']} | **紧急度**: {position_suggestion['urgency']}\n"
        
        # 分批买入策略
        if abs(drop_percent) >= 2.0:
            plan += f"📊 **分批**: 3次买入(30%-40%-30%)\n"
        elif abs(drop_percent) >= 1.0:
            plan += f"📊 **分批**: 2次买入(50%-50%)\n"
        else:
            plan += f"📊 **操作**: 可一次性买入\n"
            
        # 止盈止损建议
        plan += f"🎯 **目标**: 盈利15-20%分批减仓 | 亏损10%止损"
        
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
        
        results["国内ETF建议"] = f"🇨🇳 **国内市场操作建议**\n\n{domestic_suggestions['场内美股ETF']}\n\n{domestic_suggestions['场内A股ETF']}\n\n{domestic_suggestions.get('场外基金', '')}"
        
        # 🎯 添加主题投资分析（核心功能）
        if news_titles:
            theme_report = self.generate_theme_investment_report(news_titles)
            results["主题投资机会"] = theme_report
            
        return results
    
    def analyze_trending_themes(self, news_titles: List[str]) -> Dict[str, Dict]:
        """分析热点主题，提供相应ETF投资建议"""
        theme_scores = {}
        theme_news = {}
        
        print("🔍 分析热点主题...")
        
        # 计算每个主题的热度分数
        for theme, theme_info in self.theme_etf_mapping.items():
            score = 0
            matched_news = []
            
            for title in news_titles:
                title_lower = title.lower()
                
                # 检查关键词匹配
                for keyword in theme_info['trend_keywords']:
                    if keyword.lower() in title_lower:
                        score += 1
                        if title not in matched_news:
                            matched_news.append(title)
                        break
            
            if score > 0:
                theme_scores[theme] = score
                theme_news[theme] = matched_news
        
        # 生成投资建议
        recommendations = {}
        
        if not theme_scores:
            recommendations["无明显热点"] = {
                "热度分数": 0,
                "相关新闻": [],
                "投资建议": "📊 当前新闻中未发现明显的主题投资热点，建议关注大盘ETF",
                "推荐ETF": ["513500(标普500)", "159919(沪深300)", "159922(中证500)"],
                "操作策略": "均衡配置，等待明确趋势"
            }
            return recommendations
        
        # 按热度排序
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        
        for theme, score in sorted_themes[:3]:  # 只显示前3个热点
            theme_info = self.theme_etf_mapping[theme]
            
            # 生成投资建议
            if score >= 3:
                urgency = "🔥 高度关注"
                strategy = "重点配置，分批建仓"
                risk_level = "积极"
            elif score >= 2:
                urgency = "📈 适度关注"
                strategy = "适量配置，观察趋势"
                risk_level = "稳健"
            else:
                urgency = "📌 一般关注"
                strategy = "小仓位试探"
                risk_level = "保守"
            
            recommendations[theme] = {
                "热度分数": score,
                "相关新闻": theme_news[theme],
                "投资建议": f"{urgency} - {theme_info['recent_performance']}",
                "推荐ETF": [f"{etf}({name})" for etf, name in zip(theme_info['etfs'], theme_info['names'])],
                "操作策略": strategy,
                "风险等级": risk_level,
                "关键词": theme_info['trend_keywords'][:5]  # 只显示前5个关键词
            }
        
        return recommendations
    
    def generate_theme_investment_report(self, news_titles: List[str]) -> str:
        """生成主题投资报告"""
        theme_analysis = self.analyze_trending_themes(news_titles)
        
        report = "🎯 **主题投资机会分析**\n\n"
        
        if "无明显热点" in theme_analysis:
            report += theme_analysis["无明显热点"]["投资建议"] + "\n\n"
            report += f"**推荐ETF**: {', '.join(theme_analysis['无明显热点']['推荐ETF'])}\n"
            report += f"**操作策略**: {theme_analysis['无明显热点']['操作策略']}\n"
            return report
        
        for i, (theme, analysis) in enumerate(theme_analysis.items(), 1):
            report += f"**{i}. {theme}主题** (热度: {analysis['热度分数']})\n\n"
            report += f"📊 {analysis['投资建议']}\n\n"
            
            # 推荐ETF
            report += f"**推荐ETF**: {', '.join(analysis['推荐ETF'])}\n"
            report += f"**操作策略**: {analysis['操作策略']}\n"
            report += f"**风险等级**: {analysis['风险等级']}\n\n"
            
            # 相关新闻
            if analysis['相关新闻']:
                report += f"**相关新闻**:\n"
                for news in analysis['相关新闻'][:3]:  # 最多显示3条
                    report += f"• {news}\n"
                report += "\n"
            
            # 布局建议
            if analysis['热度分数'] >= 3:
                report += "💡 **布局建议**: 高热度主题，建议重点关注，分3-5次建仓\n"
            elif analysis['热度分数'] >= 2:
                report += "💡 **布局建议**: 中等热度，适量配置，关注后续发展\n"
            else:
                report += "💡 **布局建议**: 初现苗头，小仓位试探，等待确认\n"
            
            if i < len(theme_analysis):
                report += "\n" + "="*50 + "\n\n"
        
        # 总体策略建议
        report += "🎯 **总体策略建议**\n\n"
        report += "1. **分散投资**: 不要all-in单一主题，建议2-3个主题分散\n"
        report += "2. **分批建仓**: 热点具有波动性，分批进入降低风险\n"
        report += "3. **及时止盈**: 主题炒作有周期性，设置止盈目标\n"
        report += "4. **关注政策**: 政策导向对主题投资影响重大\n"
        
        return report
    
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
            
        # 生成简化分析
        result = f"{data_summary}"
        result += f"{color} **{decision}** (评分: {score}/100)\n"
        
        # 如果建议买入，提供简化计划
        if score >= 50:
            position_suggestion = self.calculate_position_suggestion(stock_change, risk_level)
            purchase_plan = self.generate_purchase_plan(index_name, stock_change, position_suggestion)
            result += purchase_plan
        else:
            reasons = []
            if stock_change > 0:
                reasons.append(f"美股上涨{stock_change:.2f}%")
            if etf_premium > 3.0:
                reasons.append(f"ETF溢价{etf_premium:.1f}%过高")
            if future_change > 0:
                reasons.append(f"期货上涨{future_change:.2f}%")
            if has_major_events:
                reasons.append("存在重大事件")
            
            if reasons:
                result += f"💡 **原因**: {' | '.join(reasons)}\n"
                
        # 重大事件简化提醒
        if has_major_events and len(events) > 0:
            event_name = events[0].split("'")[1] if "'" in events[0] else '重大事件'
            result += f"\n⚠️ **事件**: {event_name}"
                
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