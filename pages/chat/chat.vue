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
import { onShow } from '@dcloudio/uni-app';

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
  chatList.value.push({ role: 'ai', content: '思考中...' });
  scrollToBottom();

  uni.request({
    url: 'http://10.44.214.169:5000/api/chat/text_to_bill',
    method: 'POST',
    data: { text: text },
    success: (res) => {
      const resData = res.data;
      if (resData.success && resData.code === 200) {
        const aiResult = resData.data;
        
        if (aiResult.type === 'bill' && aiResult.bills && aiResult.bills.length > 0) {
          const bills = aiResult.bills;
          const oldBills = uni.getStorageSync('ai_bills') || [];
          uni.setStorageSync('ai_bills', [...bills, ...oldBills]);
          
          let reply = `✅ ${aiResult.message || `已经为您记下 ${bills.length} 笔账单：`}`;
          bills.forEach(item => {
             reply += `\n【${item.category}】${item.desc} ${item.type === 'expense' || item.type === '支出' ? '-' : '+'}${item.amount}元`;
          });
          chatList.value[chatList.value.length - 1].content = reply;
        } else {
          // 普通聊天或者查询，使用打字机效果输出
          chatList.value[chatList.value.length - 1].content = '';
          const fullText = aiResult.message || '不好意思，我没有听清您的需求。';
          let index = 0;
          const typeWriter = setInterval(() => {
            if (index < fullText.length) {
              chatList.value[chatList.value.length - 1].content += fullText.charAt(index);
              index++;
              scrollToBottom();
            } else {
              clearInterval(typeWriter);
            }
          }, 30);
        }
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

const triggerAIAnalyze = (dateText, tab) => {
  const allBills = uni.getStorageSync('ai_bills') || [];
  
  if (allBills.length === 0) {
    chatList.value.push({ role: 'user', content: `帮我分析一下${dateText}的账单` });
    scrollToBottom();
    setTimeout(() => {
      chatList.value.push({ role: 'ai', content: `${dateText}暂时还没有记账数据哦，快去记录一笔吧！` });
      scrollToBottom();
    }, 500);
    return;
  }

  // 计算过滤逻辑：和报表里保持一致，不过为了方便，我们在后端重新做统计，这里只把所有的对应阶段的账单找出来
  const now = new Date();
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

  const filteredBills = allBills.filter(bill => isDateInRange(bill.time, tab));
  
  chatList.value.push({ role: 'user', content: `帮我分析一下${dateText}的账单并给出优化建议` });
  scrollToBottom();
  
  isWaiting.value = true;
  chatList.value.push({ role: 'ai', content: '让我看一下您的账单...' });
  scrollToBottom();

  uni.request({
    url: 'http://10.44.214.169:5000/api/chat/analyze_bills',
    method: 'POST',
    data: { bills: filteredBills, dateText: dateText },
    success: (res) => {
      const resData = res.data;
      if (resData.success && resData.code === 200) {
        // 实现打字机效果
        chatList.value[chatList.value.length - 1].content = '';
        const fullText = resData.data;
        let index = 0;
        
        const typeWriter = setInterval(() => {
          if (index < fullText.length) {
            chatList.value[chatList.value.length - 1].content += fullText.charAt(index);
            index++;
            scrollToBottom();
          } else {
            clearInterval(typeWriter);
          }
        }, 50); // 每字符 50 毫秒

      } else {
        chatList.value[chatList.value.length - 1].content = '账单分析失败了，请稍后再试。';
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

onShow(() => {
  const autoAnalyze = uni.getStorageSync('auto_analyze_bills');
  if (autoAnalyze === 'true') {
    const dateText = uni.getStorageSync('analyze_date_text') || '这段时间';
    const tab = uni.getStorageSync('analyze_tab') || 'month';
    
    uni.removeStorageSync('auto_analyze_bills');
    uni.removeStorageSync('analyze_date_text');
    uni.removeStorageSync('analyze_tab');
    
    triggerAIAnalyze(dateText, tab);
  }
});

const startVoice = () => {
  isRecording.value = true;
  // #ifdef APP-PLUS
  plus.speech.startRecognize({
    engine: 'baidu', // 引擎改为 baidu
    continue: false
  }, (result) => {
    isRecording.value = false;
    if (result) {
      processMessage(result);
    }
  }, (err) => {
    isRecording.value = false;
    // 捕获真正的错误信息，而不仅仅是写死"未听到声音"
    const errMsg = err.message || '未听到声音';
    if (errMsg.includes('cancel') || errMsg.includes('取消')) {
      // 用户过快松手或取消
      uni.showToast({ title: '说话时间太短', icon: 'none' });
    } else {
      uni.showToast({ title: errMsg, icon: 'none' });
      console.error("语音识别错误:", err);
    }
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