const { Client, GatewayIntentBits } = require('discord.js');
const axios = require('axios');

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

const token = process.env.DISCORD_TOKEN;
const n8nUrl = process.env.N8N_WEBHOOK_URL;

client.on('messageCreate', async (message) => {
    if (message.author.bot) return;

    console.log(`Pesan diterima dari ${message.author.username}: ${message.content}`);

    //     // Cek apakah bot di-mention DAN pesan mengandung link youtube
    // if (message.mentions.has(client.user) && (message.content.includes('youtube.com') || message.content.includes('youtu.be'))) {
    try {
        await axios.post(n8nUrl, {
            author: message.author.username,
            content: message.content,
            channelId: message.channelId
        });
        // await message.react('📥'); // Beri tanda centang/emoji masuk antrean
    } catch (err) {
        console.error('Gagal mengirim data ke Webhook n8n:', err.message);
    }
    // }
});

client.login(token);