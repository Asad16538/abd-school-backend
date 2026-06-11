// backend/telegram_bot.js
const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

// ✅ APNA TOKEN YAHAN DAALO
const TELEGRAM_TOKEN = "8793915550:AAGK3RIR9PDQXkawoxaSp-69sfB5jge87A0";
const TELEGRAM_API = `https://api.telegram.org/bot${TELEGRAM_TOKEN}`;

// 📨 Send Message Function
async function sendTelegramMessage(chatId, message) {
    try {
        const response = await axios.post(`${TELEGRAM_API}/sendMessage`, {
            chat_id: chatId,
            text: message,
            parse_mode: "HTML"
        });
        return response.data.ok;
    } catch (error) {
        console.error('Telegram Error:', error.response?.data || error.message);
        return false;
    }
}

// 🤖 Webhook - Messages receive karne ke liye
app.post(`/webhook/${TELEGRAM_TOKEN}`, async (req, res) => {
    const { message } = req.body;
    
    if (message && message.text) {
        const chatId = message.chat.id;
        const text = message.text.toLowerCase();
        
        if (text === "/start") {
            await sendTelegramMessage(chatId, 
                "🎉 *Welcome to A.B.Digital Work ERP Bot!*\n\n" +
                "I can help you with:\n" +
                "• 📚 Child's Attendance\n" +
                "• 💰 Fee Status\n" +
                "• 📅 School Holidays\n" +
                "• 📞 Contact Information\n\n" +
                "Type /help for available commands.",
                { parse_mode: "Markdown" }
            );
        } else if (text === "/help") {
            await sendTelegramMessage(chatId,
                "📋 *Available Commands:*\n\n" +
                "/start - Start the bot\n" +
                "/help - Show this help\n" +
                "/attendance - Check attendance\n" +
                "/fee - Check fee status\n" +
                "/contact - School contact info",
                { parse_mode: "Markdown" }
            );
        } else if (text === "/attendance") {
            await sendTelegramMessage(chatId, "📊 Please send your child's Admission Number to check attendance.");
        } else if (text === "/fee") {
            await sendTelegramMessage(chatId, "💰 Please send your child's Admission Number to check fee status.");
        } else if (text === "/contact") {
            await sendTelegramMessage(chatId, "📞 *Contact School*\n\nPhone: +91 9893260067\nEmail: admin@school.com", { parse_mode: "Markdown" });
        } else {
            await sendTelegramMessage(chatId, "❓ Command not recognized. Type /help for available commands.");
        }
    }
    
    res.sendStatus(200);
});

// 🌐 Webhook set karo (ek baar)
async function setWebhook() {
    const webhookUrl = `https://abd-school-backend-production.up.railway.app/webhook/${TELEGRAM_TOKEN}`;
    try {
        await axios.post(`${TELEGRAM_API}/setWebhook`, { url: webhookUrl });
        console.log('✅ Telegram webhook set successfully!');
        console.log(`📡 Webhook URL: ${webhookUrl}`);
    } catch (error) {
        console.error('❌ Webhook error:', error.message);
    }
}

// 📤 API endpoint for backend to send messages
app.post('/api/send-telegram', async (req, res) => {
    const { chatId, message } = req.body;
    const result = await sendTelegramMessage(chatId, message);
    res.json({ success: result });
});

// 🚀 Start server
const PORT = process.env.TELEGRAM_PORT || 6001;
app.listen(PORT, () => {
    console.log(`🤖 Telegram Bot running on port ${PORT}`);
    setWebhook();
});