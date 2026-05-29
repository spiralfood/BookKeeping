<script>
// #ifdef APP-PLUS
// 原生插件只能在 APP 环境下引入，必须包在条件编译中
import { startListenPayment, gotoNotificationAccessSettings } from '@/uni_modules/ai-pay-listener';
// #endif

export default {
	onLaunch: function() {
		console.log('App Launch')
		
		// #ifdef APP-PLUS
		// 引导用户去开启通知读取权限
		uni.showModal({
			title: '开启自动记账',
			content: '为实现微信/支付宝付款后自动记账，请允许本应用读取系统通知。',
			confirmText: '去开启',
			success: (res) => {
				if (res.confirm) {
					gotoNotificationAccessSettings();
				}
			}
		});

		// 启动静默监听
		startListenPayment((title, text, pkg) => {
			console.log("拦截到系统存款通告：", title, text);
			
			// 拿到微信或支付宝的推送文本后，直接通过接口丢给 AI 管家入账
			uni.request({
				url: 'http://10.44.214.169:5000/api/chat/text_to_bill',
				method: 'POST',
				data: { text: "这是付款通知：标题是" + title + "，内容是：" + text },
				success: (res) => {
					let resData = res.data;
					if (resData.success && resData.data && resData.data.bills) {
						// 静默追加进账本，大功告成！
						let bills = resData.data.bills;
						let oldBills = uni.getStorageSync('ai_bills') || [];
						uni.setStorageSync('ai_bills', [...bills, ...oldBills]);
						
						// 可以从系统顶端弹个轻提示
						uni.showToast({
							title: `自动记账成功！${bills[0].desc}`,
							icon: 'success'
						});
					}
				}
			});
		});
		// #endif
	},
	onShow: function() {
		console.log('App Show')
	},
	onHide: function() {
		console.log('App Hide')
	}
}
</script>

<style>
	/*每个页面公共css */
</style>
