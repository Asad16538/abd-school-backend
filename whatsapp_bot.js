// backend/whatsapp_bot.js
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const express = require('express');
const pino = require('pino');

const app = express();
app.use(express.json());

let sock;

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }),
        printQRInTerminal: true,  // ✅ QR code terminal mein dikhega
        browser: ['Chrome (Linux)', '', '']
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log('📱 Scan QR code with WhatsApp');
        }
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('⚠️ Connection closed, reconnecting:', shouldReconnect);
            if (shouldReconnect) connectToWhatsApp();
        } else if (connection === 'open') {
            console.log('🚀 WHATSAPP BOT IS LIVE AND CONNECTED! ✅');
        }
    });
}

app.post('/send-message', async (req, res) => {
    const { mobile, message } = req.body;
    try {
        if (!sock) {
            return res.status(500).json({ success: false, error: "Bot not connected yet" });
        }
        const formattedJid = `${mobile.replace('+', '')}@s.whatsapp.net`;
        await sock.sendMessage(formattedJid, { text: message });
        return res.json({ success: true, message: "Message sent!" });
    } catch (error) {
        return res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(6000, () => {
    console.log('⚡ Bot Bridge listening on port 6000');
    connectToWhatsApp();
});