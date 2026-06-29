const { Client, GatewayIntentBits } = require('discord.js');
const axios = require('axios');

const options = {
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
};

const client = new Client(options);
const clientStaging = new Client(options);

const botToken = process.env.DISCORD_BOT_TOKEN;
const botStagingToken = process.env.DISCORD_BOT_STAGING_TOKEN;

async function handleMessage(env, message) {
    if (message.author.bot) return;

    console.log(`[${env}] - Pesan diterima dari ${message.author.username}: ${message.content}`);

    // 1. Balas dulu
    const processingMsg = await message.reply(
        "⏳ Sedang memproses video, mohon tunggu..."
    );

    // 2. Kirim ke n8n TANPA menunggu selesai
    // if (message.mentions.has(client.user) && (message.content.includes('youtube.com') || message.content.includes('youtu.be'))) {

    const n8nEndpoint = env === 'production' ? process.env.N8N_WEBHOOK_URL : process.env.N8N_WEBHOOK_TEST_URL;
    try {
        console.log(`[${env}] - Mengirim data ke n8n URL: ${n8nEndpoint}`);
        await axios.post(n8nEndpoint, {
            author: message.author.username,
            content: message.content,
            channelId: message.channelId,
            replyMessageId: processingMsg.id
        });
        // await message.react('📥'); // Beri tanda centang/emoji masuk antrean
    } catch (err) {
        console.error(`Gagal mengirim data ke Webhook n8n: ${n8nEndpoint} \n`, err.message);
    }
    // }
}

client.on('messageCreate', (message) => handleMessage('production', message));
clientStaging.on('messageCreate', (message) => handleMessage('staging', message));

client.login(botToken);
clientStaging.login(botStagingToken);