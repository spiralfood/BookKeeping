<template>
  <view class="container">
    <!-- 顶部导航 -->
    <view class="nav-bar">
      <view class="nav-left">
        <text class="nav-title">收支报表</text>
      </view>
      <view style="display: flex; align-items: center;">
        <text class="nav-right" @tap="clearAllBills" style="color: #F44336; margin-right: 30rpx; font-size: 28rpx;">清空账单</text>
        <text class="nav-right">订阅设置</text>
      </view>
    </view>

    <!-- 顶部 Tab -->
    <view class="tab-list">
      <text class="tab-item" :class="{ active: currentTab === 'week' }" @tap="currentTab = 'week'">周报</text>
      <text class="tab-item" :class="{ active: currentTab === 'month' }" @tap="currentTab = 'month'">月报</text>
      <text class="tab-item" :class="{ active: currentTab === 'year' }" @tap="currentTab = 'year'">年报</text>
      <text class="tab-item" :class="{ active: currentTab === 'custom' }" @tap="currentTab = 'custom'">自定义</text>
    </view>

    <!-- 日期及类型切换 -->
    <view class="filter-bar">
      <view class="date-selector">
        <text class="arrow">‹</text>
        <text class="date-text">{{ dateText }}</text>
        <text class="arrow">›</text>
      </view>
      <view class="type-toggle">
        <text class="type-btn" :class="{ active: billType === 'expense' }" @tap="billType = 'expense'">支出</text>
        <text class="type-btn" :class="{ active: billType === 'income' }" @tap="billType = 'income'">收入</text>
      </view>
    </view>

    <scroll-view scroll-y class="scroll-content">
      
      <!-- AI 总结卡片 -->
      <view class="ai-card">
        <view class="ai-header">
          <text class="ai-icon">🤖</text>
          <text class="ai-title">AI {{ currentTab === 'week' ? '本周' : currentTab === 'year' ? '年度' : '月度' }}小结</text>
        </view>
        <view class="ai-desc">
          <text>{{ dateText }}以<text class="highlight">{{ aiTopCategory }}</text>为主，合计 <text class="highlight">{{ aiTopAmount }}</text> 元，专属优化清单已生成！</text>
          <text class="ai-link" @tap="jumpToAIAnalysis">查看 AI 账单分析 ></text>
        </view>
        
        <view class="ai-stats">
          <view class="stat-item">
            <text class="stat-label">{{ dateText }}{{ billType === 'expense' ? '支出' : '收入' }}(元)</text>
            <text class="stat-value highlight-num">{{ totalAmount }}</text>
          </view>
          <view class="stat-item">
            <text class="stat-label">日均{{ billType === 'expense' ? '支出' : '收入' }}(元)</text>
            <text class="stat-value">{{ dailyAvg }}</text>
          </view>
          <view class="stat-item mt-10">
            <text class="stat-label">比上期{{ billType === 'expense' ? '支出' : '收入' }}(元)</text>
            <text class="stat-value">{{ totalAmount === '0.00' ? '0.00' : (billType === 'expense' ? '-374.88' : '-1,513.54') }}</text>
          </view>
          <view class="stat-item mt-10">
            <text class="stat-label">收支结余(元)</text>
            <text class="stat-value">{{ balance }}</text>
          </view>
        </view>
      </view>

      <!-- 构成卡片 -->
      <view class="chart-card">
        <view class="card-header">
          <text class="card-title">{{ dateText }}{{ billType === 'expense' ? '支出' : '收入' }}分类构成</text>
          <view class="sub-tabs">
            <text class="sub-tab active">主分类</text>
            <text class="sub-tab">子分类</text>
          </view>
        </view>
        
        <view class="donut-chart-container">
          <view class="donut-chart" :class="billType">
            <view class="donut-hole">
              <text class="donut-amount">{{ totalAmount }}</text>
              <text class="donut-label">{{ aiTopCategory }}(元)</text>
            </view>
          </view>
        </view>

        <!-- 分类列表 -->
        <view class="category-list">
          <view class="cat-item" v-for="(item, index) in categoryList" :key="index">
            <view class="cat-rank">{{ index + 1 }}</view>
            <view class="cat-icon-box">
              <text class="cat-icon">{{ item.icon }}</text>
            </view>
            <view class="cat-info">
              <view class="cat-name-count">
                <view style="display: flex; align-items: center;">
                  <text class="cat-name">{{ item.name }}</text>
                  <text class="cat-count">{{ item.count }}笔</text>
                </view>
                <text class="cat-amount">{{ billType === 'expense' ? '-' : '+' }}{{ item.amount }} <text class="cat-arrow">></text></text>
              </view>
              <view class="cat-progress-bg">
                <view class="cat-progress-bar" :style="{ width: item.percent + '%', backgroundColor: item.color }"></view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { ref, watch, computed } from 'vue';
import { onShow } from '@dcloudio/uni-app';

export default {
  setup() {
    const currentTab = ref('month');
    const billType = ref('expense');
    
    const totalAmount = ref('0.00');
    const dailyAvg = ref('0.00');
    const balance = ref('0.00');
    
    const aiTopCategory = ref('暂无');
    const aiTopAmount = ref('0.00');
    
    const categoryList = ref([]);

    const now = new Date();
    
    // 动态生成日期范围文案
    const dateText = computed(() => {
        if (currentTab.value === 'week') return "本周";
        if (currentTab.value === 'month') return `${now.getFullYear()}年${now.getMonth() + 1}月`;
        if (currentTab.value === 'year') return `${now.getFullYear()}年`;
        return "全部";
    });

    const isDateInRange = (dateStrFull, tab) => {
        if (!dateStrFull) return false;
        
        let dateStr = dateStrFull.split(' ')[0];
        let parts;
        if(dateStr.includes('-')) parts = dateStr.split('-');
        else if (dateStr.includes('/')) parts = dateStr.split('/');
        else return false;
        
        const y = parseInt(parts[0]);
        const m = parseInt(parts[1]) - 1;
        const d = parseInt(parts[2]);
        const dateObj = new Date(y, m, d);
        
        if (tab === 'year') {
            return y === now.getFullYear();
        } else if (tab === 'month') {
            return y === now.getFullYear() && m === now.getMonth();
        } else if (tab === 'week') {
            const day = now.getDay() || 7;
            const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - day + 1);
            monday.setHours(0,0,0,0);
            const sunday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - day + 7);
            sunday.setHours(23,59,59,999);
            return dateObj >= monday && dateObj <= sunday;
        } else {
            return true;
        }
    };

    const getCategoryStyle = (category) => {
      if (category.includes('餐') || category.includes('吃') || category.includes('饭') || category.includes('外卖')) return { icon: '🍽️', color: '#FF9800' };
      if (category.includes('交') || category.includes('车') || category.includes('滴') || category.includes('地铁')) return { icon: '🚗', color: '#03A9F4' };
      if (category.includes('百') || category.includes('购') || category.includes('超') || category.includes('淘宝')) return { icon: '🛒', color: '#3B82F6' };
      if (category.includes('红') || category.includes('资') || category.includes('收') || category.includes('转')) return { icon: '🧧', color: '#F44336' };
      if (category.includes('教') || category.includes('学') || category.includes('课')) return { icon: '📚', color: '#3F51B5' };
      if (category.includes('医') || category.includes('药') || category.includes('健')) return { icon: '💊', color: '#E91E63' };
      return { icon: '💰', color: '#9C27B0' };
    };

    const loadData = () => {
      const aiBills = uni.getStorageSync('ai_bills') || [];
      if (aiBills.length === 0) {
        balance.value = '0.00';
        totalAmount.value = '0.00';
        dailyAvg.value = '0.00';
        aiTopCategory.value = '暂无';
        aiTopAmount.value = '0.00';
        categoryList.value = [];
        return;
      }
      
      let expenseTotal = 0;
      let incomeTotal = 0;
      
      const catMap = {};

      aiBills.forEach(bill => {
        let isIncome = false;
        const rawAmount = parseFloat(bill.amount) || 0;
        
        if (bill.type === 'income' || bill.type === '收入') {
          isIncome = true;
        } else if (bill.type === 'expense' || bill.type === '支出') {
          isIncome = false;
        } else {
          isIncome = rawAmount > 0;
        }
        
        const timeStrFull = bill.time || '';
        
        // 使用新的过滤逻辑，按 周/月/年/自定义 过滤数据
        if (!isDateInRange(timeStrFull, currentTab.value)) return;
        
        const amountNum = Math.abs(rawAmount);
        
        if (isIncome) incomeTotal += amountNum;
        else expenseTotal += amountNum;
        
        if ((billType.value === 'income' && isIncome) || (billType.value === 'expense' && !isIncome)) {
            const cat = bill.category || '其它记录';
            if (!catMap[cat]) {
              catMap[cat] = { amount: 0, count: 0, name: cat };
            }
            catMap[cat].amount += amountNum;
            catMap[cat].count += 1;
        }
      });
      
      balance.value = (incomeTotal - expenseTotal).toFixed(2);
      const targetTotal = billType.value === 'income' ? incomeTotal : expenseTotal;
      totalAmount.value = targetTotal.toFixed(2);
      
      // 动态计算日均值所需的天数
      let days = 30;
      if (currentTab.value === 'week') days = 7;
      else if (currentTab.value === 'year') {
          const isLeap = (now.getFullYear() % 4 === 0 && now.getFullYear() % 100 !== 0) || (now.getFullYear() % 400 === 0);
          days = isLeap ? 366 : 365;
      }
      else days = 30;
      
      dailyAvg.value = (targetTotal / days).toFixed(2);
      
      const list = Object.values(catMap).sort((a, b) => b.amount - a.amount);
      if (list.length > 0) {
          aiTopCategory.value = list[0].name;
          aiTopAmount.value = list[0].amount.toFixed(2);
      } else {
          aiTopCategory.value = '无开销/收入';
          aiTopAmount.value = '0.00';
      }
      
      categoryList.value = list.map(item => {
        const style = getCategoryStyle(item.name);
        return {
          name: item.name,
          count: item.count,
          amount: item.amount.toFixed(2),
          percent: targetTotal > 0 ? ((item.amount / targetTotal) * 100).toFixed(1) : 0,
          icon: style.icon,
          color: style.color
        };
      });
    };

    onShow(() => {
      loadData();
    });

    watch(billType, () => {
      loadData();
    });
    
    watch(currentTab, () => {
      loadData();
    });

    const jumpToAIAnalysis = () => {
      uni.setStorageSync('auto_analyze_bills', 'true');
      uni.setStorageSync('analyze_date_text', dateText.value);
      uni.setStorageSync('analyze_tab', currentTab.value);
      
      uni.switchTab({
        url: '/pages/chat/chat'
      });
    };

    const clearAllBills = () => {
      uni.showModal({
        title: '温馨提示',
        content: '确定要清空所有已记录的账单吗？清空后方便您重新测试。',
        confirmColor: '#F44336',
        success: function(res) {
          if (res.confirm) {
            uni.removeStorageSync('ai_bills');
            uni.showToast({ title: '已清空', icon: 'success' });
            loadData(); // 重新加载（会自动变0）
          }
        }
      });
    };

    return {
      currentTab,
      billType,
      dateText,
      totalAmount,
      dailyAvg,
      balance,
      categoryList,
      aiTopCategory,
      aiTopAmount,
      jumpToAIAnalysis,
      clearAllBills
    };
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F7F8FA;
  display: flex;
  flex-direction: column;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: calc(20rpx + var(--status-bar-height)) 30rpx 20rpx;
  background-color: #FFFFFF;
}

.nav-left {
  display: flex;
  align-items: center;
}

.nav-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.nav-right {
  font-size: 26rpx;
  color: #3B82F6;
  font-weight: bold;
}

.tab-list {
  display: flex;
  justify-content: space-around;
  background-color: #FFFFFF;
  padding: 10rpx 40rpx 0;
}

.tab-item {
  font-size: 28rpx;
  color: #999;
  padding-bottom: 20rpx;
  position: relative;
}

.tab-item.active {
  color: #3B82F6;
  font-weight: bold;
}

.tab-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 6rpx;
  background-color: #3B82F6;
  border-radius: 6rpx;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30rpx;
  background-color: #F7F8FA;
}

.date-selector {
  display: flex;
  align-items: center;
  background-color: #FFFFFF;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
}

.date-text {
  font-size: 28rpx;
  color: #333;
  margin: 0 20rpx;
  font-weight: bold;
}

.arrow {
  color: #999;
  font-size: 28rpx;
}

.type-toggle {
  display: flex;
  background-color: #FFFFFF;
  border-radius: 30rpx;
  padding: 6rpx;
}

.type-btn {
  font-size: 24rpx;
  padding: 10rpx 36rpx;
  border-radius: 26rpx;
  color: #666;
}

.type-btn.active {
  background-color: #EEF2FF;
  color: #3B82F6;
  font-weight: bold;
}

.scroll-content {
  flex: 1;
}

.ai-card {
  background: linear-gradient(135deg, #EEF2FF 0%, #E3F2FD 100%);
  border-radius: 32rpx;
  padding: 40rpx 30rpx;
  margin: 0 30rpx 30rpx;
}

.ai-header {
  display: flex;
  align-items: center;
  margin-bottom: 20rpx;
}

.ai-icon {
  font-size: 40rpx;
  margin-right: 12rpx;
}

.ai-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #111;
}

.ai-desc {
  font-size: 26rpx;
  color: #444;
  line-height: 1.6;
  margin-bottom: 30rpx;
}

.highlight {
  font-weight: bold;
  color: #111;
}

.ai-link {
  color: #3B82F6;
  font-weight: bold;
  margin-left: 10rpx;
}

.ai-stats {
  display: flex;
  flex-wrap: wrap;
  background-color: rgba(255, 255, 255, 0.6);
  border-radius: 20rpx;
  padding: 30rpx;
}

.stat-item {
  width: 50%;
  display: flex;
  flex-direction: column;
}

.mt-10 {
  margin-top: 30rpx;
}

.stat-label {
  font-size: 24rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.stat-value {
  font-size: 32rpx;
  font-weight: bold;
  color: #111;
}

.highlight-num {
  font-size: 40rpx;
}

.chart-card {
  background-color: #FFFFFF;
  border-radius: 32rpx;
  padding: 40rpx 30rpx;
  margin: 0 30rpx 40rpx;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 40rpx;
}

.card-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333;
}

.sub-tabs {
  display: flex;
  background-color: #F5F7FA;
  border-radius: 30rpx;
  padding: 6rpx;
}

.sub-tab {
  font-size: 24rpx;
  padding: 8rpx 24rpx;
  border-radius: 26rpx;
  color: #666;
}

.sub-tab.active {
  background-color: #FFFFFF;
  color: #333;
  font-weight: bold;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}

.donut-chart-container {
  display: flex;
  justify-content: center;
  margin-top: 20rpx;
  margin-bottom: 60rpx;
}

.donut-chart {
  width: 320rpx;
  height: 320rpx;
  border-radius: 50%;
  background: conic-gradient(#3B82F6 0% 64%, #38BDF8 64% 82%, #818CF8 82% 95%, #E2E8F0 95% 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.donut-chart.income {
  background: conic-gradient(#3B82F6 0% 88%, #93C5FD 88% 95%, #E2E8F0 95% 100%);
}

.donut-hole {
  width: 220rpx;
  height: 220rpx;
  background-color: #FFFFFF;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2rpx 10rpx rgba(0,0,0,0.05);
}

.donut-amount {
  font-size: 36rpx;
  font-weight: bold;
  color: #333;
}

.donut-label {
  font-size: 24rpx;
  color: #999;
  margin-top: 6rpx;
}

.cat-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 45rpx;
}

.cat-rank {
  font-size: 28rpx;
  color: #999;
  width: 50rpx;
  padding-top: 6rpx;
}

.cat-icon-box {
  margin-right: 20rpx;
}

.cat-icon {
  font-size: 44rpx;
}

.cat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.cat-name-count {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12rpx;
}

.cat-name {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
  margin-right: 12rpx;
}

.cat-count {
  font-size: 22rpx;
  color: #999;
}

.cat-amount {
  font-size: 30rpx;
  font-weight: bold;
  color: #333;
}

.cat-arrow {
  color: #CCC;
  font-size: 24rpx;
  margin-left: 10rpx;
  font-weight: normal;
}

.cat-progress-bg {
  width: 100%;
  height: 8rpx;
  background-color: #F0F2F5;
  border-radius: 4rpx;
}

.cat-progress-bar {
  height: 100%;
  border-radius: 4rpx;
}
</style>