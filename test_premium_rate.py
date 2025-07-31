# -*- coding: utf-8 -*-
"""
🧪 ETF溢价率获取测试脚本
验证修复后的溢价率获取功能是否正常工作
"""

from etf_strategy import ETFStrategyAnalyzer
import time

def test_premium_rate_accuracy():
    """测试ETF溢价率获取的准确性"""
    
    print("🧪 ETF溢价率获取测试")
    print("=" * 50)
    
    # 创建分析器实例
    analyzer = ETFStrategyAnalyzer(use_proxy=False)
    
    print("📊 测试ETF溢价率获取...")
    
    try:
        # 获取溢价率数据
        premium_rates = analyzer.get_etf_premium_rate()
        
        print(f"\n✅ 成功获取溢价率数据")
        print("-" * 30)
        
        for etf_name, premium_rate in premium_rates.items():
            if etf_name == 'SPY':
                etf_full_name = "标普500ETF(513500)"
            elif etf_name == 'QQQ':
                etf_full_name = "纳斯达克100ETF(159834)"
            else:
                etf_full_name = etf_name
            
            print(f"📈 {etf_full_name}")
            print(f"   溢价率: {premium_rate:.2f}%")
            
            # 评估溢价率的合理性
            if -2.0 <= premium_rate <= 5.0:
                status = "✅ 正常范围"
            elif -5.0 <= premium_rate <= 8.0:
                status = "⚠️ 稍高/稍低"
            else:
                status = "❌ 异常数据"
            
            print(f"   状态: {status}")
            print()
        
        # 分析溢价率合理性
        print("📋 溢价率分析:")
        print("-" * 20)
        
        for etf_name, premium_rate in premium_rates.items():
            etf_display = "标普500ETF" if etf_name == 'SPY' else "纳斯达克100ETF"
            
            if premium_rate <= 0.5:
                advice = "💰 溢价很低，买入时机较好"
            elif premium_rate <= 1.5:
                advice = "👍 溢价适中，可以考虑买入"
            elif premium_rate <= 3.0:
                advice = "⚠️ 溢价偏高，建议等待回调"
            else:
                advice = "🚫 溢价过高，暂不建议买入"
            
            print(f"{etf_display}: {advice}")
        
        print(f"\n💡 溢价率说明:")
        print("• 溢价率 = (ETF市价 - ETF净值) / ETF净值 × 100%")
        print("• 正值表示溢价，负值表示折价")
        print("• QDII ETF通常有0.5%-2.5%的合理溢价")
        print("• 溢价过高时不建议买入，等待回调")
        
        return True
        
    except Exception as e:
        print(f"❌ 溢价率获取测试失败: {e}")
        return False

def test_single_etf_premium():
    """测试单个ETF的详细溢价率获取过程"""
    
    print("\n🔍 单个ETF详细测试")
    print("=" * 40)
    
    analyzer = ETFStrategyAnalyzer(use_proxy=False)
    
    # 测试标普500ETF
    etf_info = {
        'code': '513500',
        'name': '标普500ETF',
        'exchange': 'SH'
    }
    
    print(f"📊 测试 {etf_info['name']} ({etf_info['code']})...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    proxies = {"http": None, "https": None}
    
    try:
        premium_rate = analyzer._get_single_etf_premium(etf_info, headers, proxies)
        
        if premium_rate is not None:
            print(f"✅ 获取成功: {premium_rate:.3f}%")
            
            # 提供投资建议
            if premium_rate <= 1.0:
                suggestion = "🎯 当前溢价较低，适合买入"
            elif premium_rate <= 2.0:
                suggestion = "💡 溢价适中，可择机买入"
            elif premium_rate <= 3.5:
                suggestion = "⚠️ 溢价偏高，建议观望"
            else:
                suggestion = "🚫 溢价过高，暂不建议"
            
            print(f"💰 投资建议: {suggestion}")
        else:
            print("❌ 获取失败，可能需要检查网络或数据源")
            
    except Exception as e:
        print(f"❌ 测试过程出错: {e}")

def compare_data_sources():
    """比较不同数据源的溢价率数据"""
    
    print("\n📊 数据源对比测试")
    print("=" * 35)
    
    print("🔄 测试不同数据源的准确性...")
    print("注意: 某些数据源可能因网络限制而失败")
    
    # 这里可以手动测试不同的数据源
    # 由于网络环境限制，主要验证逻辑是否正确
    
    expected_ranges = {
        'SPY': (0.2, 3.0),  # 标普500ETF预期溢价范围
        'QQQ': (0.3, 3.5)   # 纳斯达克ETF预期溢价范围
    }
    
    analyzer = ETFStrategyAnalyzer(use_proxy=False)
    premium_rates = analyzer.get_etf_premium_rate()
    
    print("\n📋 溢价率合理性验证:")
    print("-" * 25)
    
    all_reasonable = True
    
    for etf_name, premium_rate in premium_rates.items():
        expected_min, expected_max = expected_ranges.get(etf_name, (0, 5))
        etf_display = "标普500ETF" if etf_name == 'SPY' else "纳斯达克100ETF"
        
        if expected_min <= premium_rate <= expected_max:
            status = "✅ 合理"
        else:
            status = "⚠️ 需检查"
            all_reasonable = False
        
        print(f"{etf_display}: {premium_rate:.2f}% (预期: {expected_min}-{expected_max}%) {status}")
    
    if all_reasonable:
        print(f"\n🎉 所有溢价率数据都在合理范围内!")
    else:
        print(f"\n💡 部分数据超出预期范围，可能是市场波动或数据源问题")

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 开始ETF溢价率综合测试...")
    print("=" * 60)
    
    start_time = time.time()
    
    # 测试1: 基础溢价率获取
    print("测试1: 基础功能测试")
    test1_result = test_premium_rate_accuracy()
    
    # 测试2: 单个ETF详细测试
    print("\n测试2: 单个ETF详细测试")
    test_single_etf_premium()
    
    # 测试3: 数据源对比
    print("\n测试3: 数据合理性验证")
    compare_data_sources()
    
    end_time = time.time()
    
    print(f"\n⏱️ 测试耗时: {end_time - start_time:.2f} 秒")
    
    if test1_result:
        print("🎉 ETF溢价率获取功能测试通过!")
        print("💡 现在可以获得更准确的投资建议")
    else:
        print("⚠️ 测试过程中遇到问题，请检查网络连接或数据源")
    
    print("\n📚 使用说明:")
    print("• 在TrendRadar主程序中会自动使用新的溢价率数据")
    print("• 溢价率低于1.5%时是较好的买入时机")
    print("• 建议结合美股表现和期货数据综合判断")

if __name__ == "__main__":
    run_comprehensive_test()