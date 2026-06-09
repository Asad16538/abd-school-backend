// backend/whatsapp_bot.js
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const qrcode = require('qrcode-terminal');
const express = require('express');
const pino = require('pino'); // Spacing aur clean coding standard ke liye pino import kiya

const app = express();
app.use(express.json());

let sock;

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState('auth_info_baileys');
    
    sock = makeWASocket({
        auth: state,
        logger: pino({ level: 'silent' }), // Yeh line saare faltu codes aur logs ko silent (gayab) kar degi
        printQRInTerminal: false
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log('\n🔄 [A.B.Digital Work] SCAN THIS QR WITH WHATSAPP TO LINK BOT:');
            qrcode.generate(qr, { small: true });
        }
        if (connection === 'close') {
            const shouldReconnect = lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
            console.log('⚠️ Connection closed, reconnecting: ', shouldReconnect);
            if (shouldReconnect) connectToWhatsApp();
        } else if (connection === 'open') {
            console.log('\n🚀 [A.B.Digital Work] INSTANT WHATSAPP BOT IS LIVE AND CONNECTED!');
        }
    });
}

app.post('/send-message', async (req, res) => {
    const { mobile, message } = req.body;
    try {
        const formattedJid = `${mobile.replace('+', '')}@s.whatsapp.net`;
        await sock.sendMessage(formattedJid, { text: message });
        return res.json({ success: true, message: "Instant Message Delivered!" });
    } catch (error) {
        return res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(6000, () => {
    console.log('⚡ NodeJS Bot Bridge listening on port 6000');
    connectToWhatsApp();
});