export function formatOpenAIError(e: unknown): string {
	if (e && typeof e === 'object' && 'message' in e) {
		const msg = String((e as { message: unknown }).message);
		if (msg.includes('Insufficient funds') || msg.includes('402')) {
			return 'Hết credit AI Gateway. Nạp thêm tại Vercel → Project → AI hoặc đổi OPENAI_BASE_URL sang OpenAI trực tiếp.';
		}
		if (msg.includes('Invalid input') || msg.includes('400')) {
			return 'Request AI không hợp lệ. Kiểm tra OPENAI_CHAT_MODEL (vd. openai/gpt-4o-mini) khi dùng AI Gateway.';
		}
		return msg;
	}
	return String(e);
}
