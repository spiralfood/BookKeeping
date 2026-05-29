<template>
  <view class="container">
    <!-- 顶部 Header -->
    <view class="header-bg">
      <view class="user-info">
        <view class="avatar-wrap">
          <view class="avatar"></view>
        </view>
        <text class="username">赵宏斌</text>
        <view class="badge">
          <text class="badge-text">已连续记账 128 天</text>
        </view>
      </view>
    </view>

    <!-- 原有数据卡片 (悬浮叠层) -->
    <view class="data-card">
      <view class="data-item">
        <text class="data-label">总资产(元)</text>
        <text class="data-value">0.00</text>
      </view>
      <view class="data-divider"></view>
      <view class="data-item">
        <text class="data-label">本月预算(元)</text>
        <text class="data-value">1000.00</text>
      </view>
    </view>

    <!-- 【新增】账单同步卡片 -->
    <view class="sync-card">
      <view class="sync-left">
        <text class="sync-icon">📊</text>
        <view class="sync-text-box">
          <text class="sync-title">导入历史账单</text>
          <text class="sync-sub">支持 CSV / Excel 格式，AI 自动分类</text>
        </view>
      </view>
      <view class="sync-btn" hover-class="sync-btn-active" @click="csvPicker.openPicker">
        <text class="sync-btn-text">立即导入</text>
      </view>
    </view>

    <!-- 原有菜单列表 -->
    <view class="menu-card">
      <view class="menu-item" v-for="(menu, index) in menuList" :key="index">
        <view class="menu-left">
          <text class="menu-icon">{{ menu.icon }}</text>
          <text class="menu-text">{{ menu.text }}</text>
        </view>
        <text class="menu-arrow">></text>
      </view>
    </view>
    
    <!-- 进度条蒙层 -->
    <view class="progress-overlay" v-if="isUploading">
      <view class="progress-box">
        <text class="progress-title">AI 引擎正在分析账单</text>
        <view class="progress-bar-container">
          <view class="progress-bar-inner" :style="{ width: uploadProgress + '%' }"></view>
        </view>
        <text class="progress-text">{{ uploadProgress }}%</text>
        <text class="progress-sub">这可能需要几十秒的时间</text>
      </view>
    </view>
  </view>
</template>

<script>
import { ref } from 'vue';

export default {
  setup() {
    const menuList = ref([
      { text: '我的资产', icon: '💰' },
      { text: '成就勋章', icon: '🎖️' },
      { text: '隐私安全', icon: '🛡️' },
      { text: '系统设置', icon: '⚙️' }
    ]);

    const isUploading = ref(false);
    const uploadProgress = ref(0);

    return {
      menuList,
      isUploading,
      uploadProgress,
      progressTimer: null
    };
  },
  methods: {
    // 这个函数专门用来接收 RenderJS 穿透传上来的文件数据
    receiveFile(fileData) {
      console.log('【前端穿透】成功接收底层文件数据，文件名:', fileData.name);
      console.log('【前端穿透】Base64 数据长度:', fileData.base64 ? fileData.base64.length : 0);

      const isValidFormat = fileData.name.endsWith('.csv') || fileData.name.endsWith('.xlsx') || fileData.name.endsWith('.xls');
      if (!isValidFormat) {
        uni.showToast({ title: '请选择 CSV 或 Excel 格式的账单', icon: 'none' })
        return;
      }
      
      this.isUploading = true;
      this.uploadProgress = 0;
      
      // 模拟一个美观的进度，最高跑到 90% 等待后端返回
      this.progressTimer = setInterval(() => {
        if (this.uploadProgress < 90) {
          this.uploadProgress += Math.floor(Math.random() * 8) + 2;
          if (this.uploadProgress > 90) this.uploadProgress = 90;
        }
      }, 300);
      
      console.log('【网络请求】准备发送到后端解析...');
      // 此时 fileData.base64 就是文件的核心内容，我们可以直接发给后端
      uni.request({
        url: 'http://10.44.214.169:5000/api/bill/import_base64', // 
        method: 'POST',
        data: {
          fileName: fileData.name,
          fileData: fileData.base64
        },
        success: (res) => {
          console.log('【后端响应】请求成功:', res.data);
          this.uploadProgress = 100;
          
          setTimeout(() => {
            this.isUploading = false;
            clearInterval(this.progressTimer);
            
            try {
              const resData = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
              if (resData.success && resData.code === 200) {
                // 拿到真正的解析数据了！直接存到本地缓存 ai_bills 里
                const oldBills = uni.getStorageSync('ai_bills') || [];
                uni.setStorageSync('ai_bills', [...resData.data, ...oldBills]);
                uni.showToast({ title: `导入成功，新增 ${resData.count} 条记录`, icon: 'success' })
              } else {
                uni.showToast({ title: resData.message || 'AI 提取失败', icon: 'none' })
              }
            } catch (e) {
              console.error('【解析异常】:', e);
              uni.showToast({ title: '服务器返回异常', icon: 'none' })
            }
          }, 500);
        },
        fail: (err) => {
          console.error('【网络请求】失败:', err);
          this.isUploading = false;
          clearInterval(this.progressTimer);
          uni.showToast({ title: '网络连接失败', icon: 'error' })
        }
      })
    }
  }
}
</script>

<style scoped>
.container {
  min-height: 100vh;
  background-color: #F7F8FA;
}

/* 顶部 Header */
.header-bg {
  background-color: #3B82F6;
  height: 440rpx;
  border-bottom-left-radius: 60rpx;
  border-bottom-right-radius: 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: calc(100rpx + var(--status-bar-height)); /* 适配顶部状态栏防止重叠 */
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.avatar-wrap {
  width: 130rpx;
  height: 130rpx;
  background-color: #FFFFFF;
  border-radius: 50%;
  padding: 6rpx;
  margin-bottom: 20rpx;
}

.avatar {
  width: 100%;
  height: 100%;
  background-color: #EEEEEE;
  border-radius: 50%;
}

.username {
  font-size: 36rpx;
  font-weight: bold;
  color: #FFFFFF;
  margin-bottom: 16rpx;
}

.badge {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 6rpx 20rpx;
  border-radius: 30rpx;
}

.badge-text {
  font-size: 24rpx;
  color: #FFFFFF;
}

/* 头像下方数据卡片 */
.data-card {
  background-color: #FFFFFF;
  border-radius: 24rpx;
  margin: -60rpx 30rpx 30rpx 30rpx; /* Negative margin to overlap */
  padding: 40rpx 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.04);
}

.data-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.data-label {
  font-size: 26rpx;
  color: #666666;
  margin-bottom: 12rpx;
}

.data-value {
  font-size: 34rpx;
  font-weight: bold;
  color: #333333;
}

.data-divider {
  width: 2rpx;
  height: 60rpx;
  background-color: #EEEEEE;
}

/* 【新增】账单同步卡片 */
.sync-card {
  background-color: #FFFFFF;
  border-radius: 24rpx;
  margin: 0 30rpx 30rpx 30rpx;
  padding: 30rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.02);
}

.sync-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.sync-icon {
  font-size: 56rpx;
  margin-right: 20rpx;
}

.sync-text-box {
  display: flex;
  flex-direction: column;
}

.sync-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 8rpx;
}

.sync-sub {
  font-size: 22rpx;
  color: #999999;
}

.sync-btn {
  height: 60rpx;
  padding: 0 30rpx;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 20rpx;
  transition: all 0.15s ease-in-out;
}

/* 按钮点击缩放反馈动画 */
.sync-btn-active {
  transform: scale(0.92);
  background-color: rgba(59, 130, 246, 0.2);
}

.sync-btn-text {
  font-size: 24rpx;
  font-weight: bold;
  color: #3B82F6;
}

/* 底部菜单列表 */
.menu-card {
  background-color: #FFFFFF;
  border-radius: 24rpx;
  margin: 0 30rpx 30rpx 30rpx;
  padding: 0 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.02);
}

.menu-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 36rpx 0;
  border-bottom: 1rpx solid #F5F7FA;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-left {
  display: flex;
  align-items: center;
}

.menu-icon {
  font-size: 36rpx;
  margin-right: 20rpx;
}

.menu-text {
  font-size: 30rpx;
  color: #333333;
}

.menu-arrow {
  font-size: 30rpx;
  color: #CCCCCC;
}

/* 进度条蒙层 */
.progress-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
  backdrop-filter: blur(4px);
}

.progress-box {
  width: 600rpx;
  background-color: #FFFFFF;
  border-radius: 32rpx;
  padding: 50rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 16rpx 48rpx rgba(0, 0, 0, 0.1);
}

.progress-title {
  font-size: 34rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 40rpx;
}

.progress-bar-container {
  width: 100%;
  height: 16rpx;
  background-color: #F0F2F5;
  border-radius: 8rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
}

.progress-bar-inner {
  height: 100%;
  background: linear-gradient(90deg, #60A5FA, #3B82F6);
  border-radius: 8rpx;
  transition: width 0.3s ease-out;
}

.progress-text {
  font-size: 40rpx;
  font-weight: bold;
  color: #3B82F6;
  margin-bottom: 12rpx;
}

.progress-sub {
  font-size: 24rpx;
  color: #999999;
}
</style>

<script module="csvPicker" lang="renderjs">
export default {
  methods: {
    openPicker(e, ownerInstance) {
      // 动态创建一个隐藏的 H5 文件选择器
      let input = document.createElement('input');
      input.type = 'file';
      // 【关键修改】：Android WebView 对 .csv 后缀的 Intent 解析有问题，会导致只出现相机。
      // 改为 */* 强制系统弹出全能文件管理器，具体格式通过 JS 校验
      input.accept = '*/*'; 
      
      input.onchange = (event) => {
        let file = event.target.files[0];
        if (!file) return;

        // 利用 FileReader 将文件转码为 Base64
        let reader = new FileReader();
        reader.onload = (e) => {
          let base64Data = e.target.result;
          // 【核心穿透】把拿到的文件数据强制塞回给上面的 Vue 逻辑层！
          ownerInstance.callMethod('receiveFile', {
            name: file.name,
            base64: base64Data
          });
        };
        reader.readAsDataURL(file); // 读取文件
      };
      
      // 模拟点击，瞬间唤起系统自带的文件管理器！
      input.click();
    }
  }
}
</script>