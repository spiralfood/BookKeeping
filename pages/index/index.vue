<template>
  <view class="container">
    <view class="header-card">
      <view class="header-top">
        <text class="header-label">今日支出(元)</text>
        <text class="header-amount-huge">{{ todayExpense }}</text>
      </view>
      <view class="header-bottom">
        <view class="header-col">
          <text class="header-sub-label">本月支出</text>
          <text class="header-sub-val">{{ monthExpense }}</text>
        </view>
        <view class="header-col">
          <text class="header-sub-label">本月收入</text>
          <text class="header-sub-val">{{ monthIncome }}</text>
        </view>
      </view>
    </view>

    <scroll-view class="bill-list" scroll-y>
      <view class="bill-group" v-for="(group, gIndex) in billGroups" :key="gIndex">
        <view class="group-header">
          <text class="group-date">{{ group.date }}</text>
          <text class="group-summary">支 {{ group.expenseSum }} · 收 {{ group.incomeSum }}</text>
        </view>

        <view class="bill-item" v-for="item in group.items" :key="item.id">
          <view class="item-left">
            <view class="icon-circle" :style="{ backgroundColor: item.color }">
              <text class="icon-text">{{ item.iconText }}</text>
            </view>
          </view>
          <view class="item-middle">
            <text class="item-category">{{ item.category }}</text>
            <text class="item-time-note">{{ item.time }} {{ item.note ? '| ' + item.note : '' }}</text>
          </view>
          <view class="item-right">
            <text class="item-amount" :class="{'income-text': item.isIncome}">{{ item.amount }}</text>
          </view>
        </view>
      </view>
      
      <view class="safe-bottom-space"></view>
    </scroll-view>

    <view class="bottom-action">
      <view class="record-btn" @click="openAddPopup" hover-class="record-btn-active">
        <text class="record-icon">+</text>
      </view>
    </view>

    <view class="mask" v-if="showPopup" @click="closeAddPopup"></view>
    
    <view class="popup-panel" :class="{'popup-show': showPopup}">
      <view class="popup-header">
        <view class="tab-group">
          <view class="tab-item" :class="{'tab-active': billType === 'expense'}" @click="billType = 'expense'">支出</view>
          <view class="tab-item" :class="{'tab-active': billType === 'income'}" @click="billType = 'income'">收入</view>
        </view>
        <view class="close-icon" @click="closeAddPopup">×</view>
      </view>

      <view class="amount-display">
        <text class="currency-symbol">¥</text>
        <text class="amount-text">{{ currentAmount }}</text>
      </view>

      <scroll-view class="category-scroll" scroll-x :show-scrollbar="false">
        <view class="category-list">
          <view 
            class="category-item" 
            v-for="(cat, index) in currentCategories" 
            :key="index"
            @click="selectedCategory = cat"
          >
            <view class="cat-icon-wrap" :class="{'cat-active': selectedCategory.name === cat.name}">
              <view class="cat-icon" :style="{ backgroundColor: selectedCategory.name === cat.name ? cat.color : '#F1F5F9' }">
                <text class="cat-icon-text" :style="{ color: selectedCategory.name === cat.name ? '#FFF' : '#64748B' }">{{ cat.iconText }}</text>
              </view>
            </view>
            <text class="cat-name">{{ cat.name }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="remark-input-area">
        <input class="remark-input" v-model="remark" placeholder="点击填写备注..." placeholder-style="color:#CBD5E1;"/>
      </view>

      <view class="keyboard">
        <view class="kb-left">
          <view class="kb-row">
            <view class="key-btn" @click="handleKey('7')">7</view>
            <view class="key-btn" @click="handleKey('8')">8</view>
            <view class="key-btn" @click="handleKey('9')">9</view>
          </view>
          <view class="kb-row">
            <view class="key-btn" @click="handleKey('4')">4</view>
            <view class="key-btn" @click="handleKey('5')">5</view>
            <view class="key-btn" @click="handleKey('6')">6</view>
          </view>
          <view class="kb-row">
            <view class="key-btn" @click="handleKey('1')">1</view>
            <view class="key-btn" @click="handleKey('2')">2</view>
            <view class="key-btn" @click="handleKey('3')">3</view>
          </view>
          <view class="kb-row">
            <view class="key-btn key-zero" @click="handleKey('0')">0</view>
            <view class="key-btn" @click="handleKey('.')">.</view>
          </view>
        </view>
        <view class="kb-right">
          <view class="key-btn key-action" @click="handleKey('del')">⌫</view>
          <view class="key-btn key-save" @click="saveBill">保存</view>
        </view>
      </view>

    </view>
  </view>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { onShow } from '@dcloudio/uni-app';

// 页面数据展示
const todayExpense = ref('0.00');
const monthExpense = ref('0.00');
const monthIncome = ref('0.00');
const billGroups = ref([]);

// 弹窗状态管理
const showPopup = ref(false);
const billType = ref('expense');
const currentAmount = ref('0');
const remark = ref('');

// 预设分类数据
const expenseCategories = [
  { name: '餐饮美食', iconText: '餐', color: '#FF9800' },
  { name: '交通出行', iconText: '车', color: '#03A9F4' },
  { name: '购物百货', iconText: '购', color: '#8BC34A' },
  { name: '休闲娱乐', iconText: '娱', color: '#E91E63' },
  { name: '日常缴费', iconText: '费', color: '#9C27B0' },
  { name: '医疗健康', iconText: '医', color: '#F44336' },
  { name: '其他支出', iconText: '账', color: '#78909C' }
];

const incomeCategories = [
  { name: '工资收入', iconText: '薪', color: '#4CAF50' },
  { name: '理财收益', iconText: '理', color: '#F44336' },
  { name: '收红包', iconText: '红', color: '#FF5722' },
  { name: '其他收入', iconText: '收', color: '#78909C' }
];

const currentCategories = computed(() => billType.value === 'expense' ? expenseCategories : incomeCategories);
const selectedCategory = ref(expenseCategories[0]);

// 监听弹窗类型切换，自动重置选中的分类
watch(billType, (newVal) => {
  selectedCategory.value = newVal === 'expense' ? expenseCategories[0] : incomeCategories[0];
});

// 打开/关闭弹窗
const openAddPopup = () => {
  currentAmount.value = '0';
  remark.value = '';
  billType.value = 'expense';
  showPopup.value = true;
};
const closeAddPopup = () => showPopup.value = false;

// 自定义键盘逻辑
const handleKey = (key) => {
  if (key === 'del') {
    if (currentAmount.value.length > 1) {
      currentAmount.value = currentAmount.value.slice(0, -1);
    } else {
      currentAmount.value = '0';
    }
    return;
  }

  if (key === '.') {
    if (!currentAmount.value.includes('.')) {
      currentAmount.value += '.';
    }
    return;
  }

  // 限制两位小数
  if (currentAmount.value.includes('.')) {
    const parts = currentAmount.value.split('.');
    if (parts[1].length >= 2) return; 
  }

  if (currentAmount.value === '0') {
    currentAmount.value = key;
  } else {
    // 限制最大金额长度
    if (currentAmount.value.length < 9) {
      currentAmount.value += key;
    }
  }
};

// 保存账单并瞬间渲染
const saveBill = () => {
  if (currentAmount.value === '0' || currentAmount.value === '0.') {
    uni.showToast({ title: '请输入金额', icon: 'none' });
    return;
  }

  const now = new Date();
  const dateStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
  const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  
  const newBill = {
    time: `${dateStr} ${timeStr}`,
    desc: remark.value.trim() || selectedCategory.value.name,
    category: selectedCategory.value.name,
    type: billType.value,
    amount: parseFloat(currentAmount.value).toFixed(2)
  };

  // 插入缓存
  const oldBills = uni.getStorageSync('ai_bills') || [];
  uni.setStorageSync('ai_bills', [newBill, ...oldBills]);

  // 关闭弹窗并重新加载列表
  closeAddPopup();
  uni.showToast({ title: '记账成功', icon: 'success' });
  loadBills();
};

// 工具函数：获取图标颜色
const getCategoryStyle = (category) => {
  if (!category) return { iconText: '账', color: '#9C27B0' };
  if (category.includes('餐') || category.includes('吃')) return { iconText: '餐', color: '#FF9800' };
  if (category.includes('交') || category.includes('车') || category.includes('滴')) return { iconText: '车', color: '#03A9F4' };
  if (category.includes('百') || category.includes('购') || category.includes('超')) return { iconText: '购', color: '#8BC34A' };
  if (category.includes('资') || category.includes('收') || category.includes('红包')) return { iconText: '收', color: '#4CAF50' };
  if (category.includes('医')) return { iconText: '医', color: '#F44336' };
  if (category.includes('娱')) return { iconText: '娱', color: '#E91E63' };
  if (category.includes('费')) return { iconText: '费', color: '#9C27B0' };
  return { iconText: category.charAt(0), color: '#78909C' };
};

// 核心加载函数（从 onShow 抽离出来，方便随存随刷）
const loadBills = () => {
  const aiBills = uni.getStorageSync('ai_bills');
  if (aiBills && aiBills.length > 0) {
    const groupMap = {};
    let tExpense = 0, mExpense = 0, mIncome = 0;
    
    const now = new Date();
    const currentMonthPrefix1 = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
    const currentMonthPrefix2 = `${now.getFullYear()}/${String(now.getMonth() + 1).padStart(2, '0')}`;
    const todayPrefix1 = `${currentMonthPrefix1}-${String(now.getDate()).padStart(2, '0')}`;
    const todayPrefix2 = `${currentMonthPrefix2}/${String(now.getDate()).padStart(2, '0')}`;
    
    aiBills.forEach((bill, index) => {
      const timeStrFull = bill.time || '';
      const timeParts = timeStrFull.split(' ');
      const dateStr = timeParts[0] || '未知日期';
      const timeStr = timeParts[1] || '';
      
      if (!groupMap[dateStr]) {
        groupMap[dateStr] = { date: dateStr, expenseSum: 0, incomeSum: 0, items: [] };
      }
      
      let isIncome = false;
      const rawAmount = parseFloat(bill.amount) || 0;
      if (bill.type === 'income' || bill.type === '收入') {
        isIncome = true;
      } else if (bill.type === 'expense' || bill.type === '支出') {
        isIncome = false;
      } else {
        isIncome = rawAmount > 0;
      }

      const amountNum = Math.abs(rawAmount);
      if (isIncome) {
        groupMap[dateStr].incomeSum += amountNum;
        if (dateStr.startsWith(currentMonthPrefix1) || dateStr.startsWith(currentMonthPrefix2)) mIncome += amountNum;
      } else {
        groupMap[dateStr].expenseSum += amountNum;
        if (dateStr.startsWith(currentMonthPrefix1) || dateStr.startsWith(currentMonthPrefix2)) mExpense += amountNum;
        if (dateStr === todayPrefix1 || dateStr === todayPrefix2) tExpense += amountNum;
      }
      
      const style = getCategoryStyle(bill.category);
      groupMap[dateStr].items.push({
        id: 'ai_' + index,
        category: bill.category || '未分类',
        iconText: style.iconText,
        color: style.color,
        time: timeStr,
        note: bill.desc || '',
        amount: (isIncome ? '+' : '-') + amountNum.toFixed(2),
        isIncome: isIncome
      });
    });
    
    const newGroups = Object.values(groupMap).sort((a, b) => b.date.localeCompare(a.date));
    newGroups.forEach(g => {
      g.expenseSum = g.expenseSum.toFixed(2);
      g.incomeSum = g.incomeSum.toFixed(2);
    });
    
    billGroups.value = newGroups;
    todayExpense.value = tExpense.toFixed(2);
    monthExpense.value = mExpense.toFixed(2);
    monthIncome.value = mIncome.toFixed(2);
  } else {
    todayExpense.value = '0.00';
    monthExpense.value = '0.00';
    monthIncome.value = '0.00';
    billGroups.value = [];
  }
};

onShow(() => {
  loadBills();
});
</script>

<style scoped>
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #F7F8FA;
  box-sizing: border-box;
  position: relative;
  padding-top: var(--status-bar-height);
}

/* 顶部统计卡片 */
.header-card {
  margin: 30rpx 30rpx 10rpx 30rpx;
  padding: 40rpx;
  background: linear-gradient(135deg, #FFF5D1, #FFE599);
  border-radius: 30rpx;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8rpx 20rpx rgba(255, 215, 120, 0.2);
}

.header-top { display: flex; flex-direction: column; margin-bottom: 40rpx; }
.header-label { font-size: 26rpx; color: #554A2E; margin-bottom: 12rpx; }
.header-amount-huge { font-size: 80rpx; font-weight: 900; color: #1A1A1A; line-height: 1; }
.header-bottom { display: flex; flex-direction: row; }
.header-col { flex: 1; display: flex; flex-direction: column; }
.header-sub-label { font-size: 24rpx; color: #7A6F50; margin-bottom: 8rpx; }
.header-sub-val { font-size: 36rpx; font-weight: bold; color: #1A1A1A; }

/* 账单列表区 */
.bill-list { flex: 1; width: 100%; height: 0; }
.safe-bottom-space { height: 220rpx; }
.bill-group { margin: 20rpx 30rpx; }
.group-header { display: flex; justify-content: space-between; padding: 20rpx 10rpx; }
.group-date, .group-summary { font-size: 24rpx; color: #999999; }
.bill-item { background-color: #FFFFFF; border-radius: 20rpx; padding: 24rpx; margin-bottom: 20rpx; display: flex; flex-direction: row; align-items: center; }
.item-left { margin-right: 24rpx; }
.icon-circle { width: 80rpx; height: 80rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.icon-text { color: #FFFFFF; font-size: 32rpx; font-weight: bold; }
.item-middle { flex: 1; display: flex; flex-direction: column; }
.item-category { font-size: 30rpx; color: #333333; margin-bottom: 8rpx; font-weight: 500; }
.item-time-note { font-size: 24rpx; color: #AAAAAA; }
.item-right { margin-left: 20rpx; }
.item-amount { font-size: 34rpx; font-weight: bold; color: #1A1A1A; }
.income-text { color: #F44336; }

/* 底部交互按钮 */
.bottom-action {
  position: absolute;
  bottom: 60rpx;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}
.record-btn {
  width: 120rpx;
  height: 120rpx;
  background-color: #3B82F6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 16rpx 40rpx rgba(59, 130, 246, 0.4);
  pointer-events: auto;
  transition: all 0.15s;
}
.record-btn-active {
  transform: scale(0.9);
  box-shadow: 0 8rpx 20rpx rgba(59, 130, 246, 0.3);
}
.record-icon { font-size: 70rpx; font-weight: 300; color: #fff; margin-top: -6rpx;}

/* 弹窗及遮罩 */
.mask {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.4); z-index: 99;
}
.popup-panel {
  position: fixed; bottom: 0; left: 0; width: 100%;
  background-color: #F8FAFC;
  border-radius: 40rpx 40rpx 0 0;
  z-index: 100;
  transform: translateY(100%);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
  padding-bottom: env(safe-area-inset-bottom);
}
.popup-show {
  transform: translateY(0);
}

/* 弹窗 Header */
.popup-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 30rpx 40rpx 10rpx;
}
.tab-group {
  display: flex; background: #EEF2F6; border-radius: 40rpx; padding: 6rpx;
}
.tab-item {
  padding: 10rpx 40rpx; font-size: 28rpx; color: #64748B; border-radius: 34rpx;
}
.tab-active {
  background: #FFFFFF; color: #3B82F6; font-weight: bold; box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.05);
}
.close-icon {
  font-size: 50rpx; color: #94A3B8; line-height: 1; padding: 0 10rpx;
}

/* 金额显示 */
.amount-display {
  padding: 20rpx 40rpx 10rpx; display: flex; align-items: baseline; border-bottom: 2rpx solid #E2E8F0; margin: 0 40rpx;
}
.currency-symbol { font-size: 40rpx; font-weight: bold; margin-right: 10rpx; color: #1E293B; }
.amount-text { font-size: 70rpx; font-weight: bold; color: #1E293B; }

/* 分类滚动区 */
.category-scroll {
  width: 100%; white-space: nowrap; padding: 30rpx 0;
}
.category-list {
  display: inline-flex; padding: 0 20rpx;
}
.category-item {
  display: flex; flex-direction: column; align-items: center; width: 120rpx; margin: 0 10rpx;
}
.cat-icon-wrap {
  width: 90rpx; height: 90rpx; border-radius: 50%; display: flex; justify-content: center; align-items: center;
  transition: all 0.2s;
}
.cat-active {
  transform: scale(1.15); box-shadow: 0 10rpx 20rpx rgba(0,0,0,0.1);
}
.cat-icon {
  width: 100%; height: 100%; border-radius: 50%; display: flex; justify-content: center; align-items: center;
}
.cat-icon-text { font-size: 36rpx; font-weight: bold; }
.cat-name { font-size: 22rpx; color: #64748B; margin-top: 16rpx; }

/* 备注 */
.remark-input-area {
  padding: 0 40rpx 20rpx;
}
.remark-input {
  background: #FFFFFF; height: 70rpx; border-radius: 35rpx; padding: 0 30rpx; font-size: 26rpx;
}

/* 键盘重构：Flexbox 方案 (100% 兼容所有 WebView) */
.keyboard {
  display: flex;
  flex-direction: row;
  padding: 20rpx 40rpx 40rpx;
  background: #FFFFFF;
}

.kb-left {
  width: 74%;
  display: flex;
  flex-direction: column;
}

.kb-right {
  width: 23%;
  margin-left: 3%;
  display: flex;
  flex-direction: column;
}

.kb-row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.kb-row:last-child {
  margin-bottom: 0;
}

.key-btn {
  width: 31%;
  height: 100rpx;
  background: #F1F5F9;
  border-radius: 16rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 44rpx;
  font-weight: 500;
  color: #1E293B;
}

.key-btn:active {
  background: #E2E8F0;
}

.key-zero {
  width: 65.5%; /* 两个普通按键宽度 + 间距 */
}

.kb-right .key-btn {
  width: 100%;
}

.key-action {
  margin-bottom: 16rpx;
  font-size: 40rpx;
  color: #64748B;
}

.key-save {
  flex: 1; /* 自动填满右侧剩余高度 */
  background: #3B82F6;
  color: #FFF;
  font-size: 32rpx;
}

.key-save:active {
  background: #2563EB;
}
</style>