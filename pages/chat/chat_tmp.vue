<template>
  <view class="container">
    <scroll-view 
      class="chat-area" 
      scroll-y 
      :scroll-with-animation="true"
      :scroll-top="scrollTop"
    >
      <view 
        class="message" 
        v-for="(msg, index) in chatList" 
        :key="index"
        :class="msg.role === 'ai' ? 'ai-message' : 'user-message'"
        :id="'msg-' + index"
      >
        <view class="bubble" :class="msg.role === 'ai' ? 'ai-bubble' : 'user-bubble'" style="white-space: pre-wrap;">
          {{ msg.content }}
        </view>
      </view>
    </scroll-view>

    <view class="input-area">
      <view class="toggle-mode" @tap="toggleMode">
        <text class="mode-icon">{{ isAudioMode ? '⌨️' : '🎙️' }}</text>
      </view>

      <view v-if="!isAudioMode" class="text-input-wrap">
        <input 
          class="text-input" 
          v-model="inputText" 
          placeholder="给管家发消息..." 
          @confirm="sendText" 
          confirm-type="send"
        />
        <view class="send-btn" v-if="inputText.trim().length > 0" @tap="sendText">发送</view>
      </view>

      <view v-else class="audio-input-wrap">
        <view 
          class="audio-btn" 
          :class="{ 'recording': isRecording }"
          @touchstart="startVoice"
          @touchend="stopVoice"
        >
          {{ isRecording ? '松开 结束' : '按住 说话' }}
        </view>
      </view>
    </view>
    
    <view v-if="isRecording" class="recording-overlay">
      <text class="recording-icon">🎤</text>
      <text class="recording-text">正在聆听...请说话</text>
    </view>
  </view>
</template>

<script setup>
import { ref, nextTick } from 'vue';

const chatList = ref([
  { role: 'ai', content: '您好！我是您的智能账房管家。\n您可以直接对我说：“今天中午吃海底捞花了380”\n我会帮您自动提取记录并入账！' }
]);

const inputText = ref('');
const isAudioMode = ref(true);
const isRecording = ref(false);
const scrollTop = ref(99999);
const isWaiting = ref(false);

const scrollToBottom = () => {
  nextTick(() => {
    scrollTop.value += 1000;
  });
};

const toggleMode = () => {
  isAudioMode.value = !isAudioMode.value;
};

const sendText = () => {
  const text = inputText.value.trim();
  if (!text) return;
  inputText.value = '';
  processMessage(text);
};

const processMessage = (text) => {
  if (isWaiting.value) {
    uni.showToast({ title: '小管家正在处理中...', icon: 'none' });
    return;
  }
  
  chatList.value.push({ role: 'user', content: text });
  scrollToBottom();
  
  isWaiting.value = true;
  chatList.value.push({ role: 'ai', content: '思考中' });
  scrollToBottom();

  uni.request({
    url: 'http://10.44.214.169:5000/api/chat/text_to_bill',
    method: 'POST',
    data: { text: text },
    success: (res) => {
      const resData = res.data;
      if (resData.success && resData.code === 200) {
        const bills = resData.data;
        const oldBills = uni.getStorageSync('ai_bills') || [];
        uni.setStorageSync('ai_bills', [...bills, ...oldBills]);
        
        let reply = `✅ 已经为您记下 ${bills.length} 笔账单：`;
        bills.forEach(item => {
           reply += `\n【${item.category}】${item.desc} ${item.type === 'expense' || item.type === '支出' ? '-' : '+'}${item.amount}元`;
        });
        
        chatList.value[chatList.value.length - 1].content = reply;
      } else {
        chatList.value[chatList.value.length - 1].content = '提取失败了，可能是描述不够清楚，能不能再说详细一点？';
      }
    },
    fail: (err) => {
      chatList.value[chatList.value.length - 1].content = '网络连接失败，管家暂时离线了...';
      console.error(err);
    },
    complete: () => {
      isWaiting.value = false;
      scrollToBottom();
    }
  });
};

const startVoice = () => {
  isRecording.value = true;
  // #ifdef APP-PLUS
  plus.speech.startRecognize({
    engine: 'iFly',
    continue: false
  }, (result) => {
    isRecording.value = false;
    if (result) {
      processMessage(result);
    }
  }, (err) => {
    isRecording.value = false;
    uni.showToast({ title: '未听到声音', icon: 'none' });
  });
  // #endif
  
  // #ifndef APP-PLUS
  uni.showToast({ title: '语音功能主要在APP客户端生效', icon: 'none'});
  // 网页端给予模拟体验
  setTimeout(() => {
    if(isRecording.value) {
      isRecording.value = false;
      processMessage("中午吃海底捞花了380");
    }
  }, 1500);
  // #endif
};

const stopVoice = () => {
  isRecording.value = false;
  // #ifdef APP-PLUS
  plus.speech.stopRecognize();
  // #endif
};
</script>

<style scoped>
.container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #F8FAFC 0%, #E0E7FF 100%);
  box-sizing: border-box;
  padding-top: var(--status-bar-height);
}

.chat-area {
  flex: 1;
  padding: 40rpx 30rpx;
  box-sizing: border-box;
  height: 0; 
}

.message {
  margin-bottom: 40rpx;
  display: flex;
}

.ai-message {
  justify-content: flex-start;
}

.user-message {
  justify-content: flex-end;
}

.bubble {
  max-width: 75%;
  padding: 24rpx 30rpx;
  font-size: 28rpx;
  line-height: 1.6;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.ai-bubble {
  background-color: #FFFFFF;
  color: #333333;
  border-radius: 24rpx 24rpx 24rpx 0;
}

.user-bubble {
  background-color: #3B82F6;
  color: #FFFFFF;
  border-radius: 24rpx 24rpx 0 24rpx;
}

.input-area {
  background-color: #FFFFFF;
  border-top: 1rpx solid #EEEEEE;
  padding: 20rpx 30rpx 60rpx 30rpx;
  display: flex;
  align-items: center;
}

.toggle-mode {
  width: 60rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20rpx;
}

.mode-icon {
  font-size: 40rpx;
}

.text-input-wrap {
  flex: 1;
  display: flex;
  align-items: center;
}

.text-input {
  flex: 1;
  height: 80rpx;
  background-color: #F5F7FA;
  border-radius: 40rpx;
  padding: 0 30rpx;
  font-size: 28rpx;
}

.send-btn {
  margin-left: 20rpx;
  color: #FFFFFF;
  background-color: #3B82F6;
  padding: 10rpx 30rpx;
  border-radius: 30rpx;
  font-size: 26rpx;
}

.audio-input-wrap {
  flex: 1;
}

.audio-btn {
  height: 80rpx;
  background-color: #F5F7FA;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: bold;
  color: #666;
  transition: all 0.2s;
}

.audio-btn.recording {
  background-color: #E2E8F0;
  color: #3B82F6;
}

.recording-overlay {
  position: fixed;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 300rpx;
  height: 300rpx;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.recording-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
  animation: pulse 1s infinite alternate;
}

.recording-text {
  color: #FFFFFF;
  font-size: 28rpx;
}

@keyframes pulse {
  0% { transform: scale(1); opacity: 0.8; }
  100% { transform: scale(1.2); opacity: 1; }
}
</style>