const cron = require('node-cron');
const { Subscription } = require('./db');
const { checkAppointments } = require('./scraper');

const ICP_URL = 'https://icp.administracionelectronica.gob.es/icpplus/index.html';

// How often to check (minutes) - set in .env or default 5
const CHECK_INTERVAL = process.env.CHECK_INTERVAL_MINUTES || '5';

let botInstance = null;
let isRunning = false;

function startScheduler(bot) {
  botInstance = bot;
  
  console.log(`⏰ Scheduler started - checking every ${CHECK_INTERVAL} minutes`);

  // Run every N minutes
  cron.schedule(`*/${CHECK_INTERVAL} * * * *`, async () => {
    if (isRunning) {
      console.log('⚠️ Previous check still running, skipping...');
      return;
    }
    await runCheck();
  });

  // Also run once immediately on startup (after 10 sec delay)
  setTimeout(runCheck, 10000);
}

async function runCheck() {
  isRunning = true;
  console.log(`\n🔍 [${new Date().toISOString()}] Checking all subscriptions...`);

  try {
    const subs = await Subscription.find({ active: true });
    console.log(`📋 Found ${subs.length} active subscriptions`);

    for (const sub of subs) {
      try {
        await checkSingleSubscription(sub);
        // Small delay between checks to avoid getting blocked
        await sleep(3000);
      } catch (err) {
        console.error(`Error checking sub ${sub._id}:`, err.message);
      }
    }
  } catch (err) {
    console.error('Scheduler error:', err);
  }

  isRunning = false;
  console.log('✅ Check cycle complete\n');
}

async function checkSingleSubscription(sub) {
  console.log(`  Checking: ${sub.provincia} / ${sub.tramite.substring(0, 40)}...`);

  const result = await checkAppointments(
    sub.provinciaCode,
    sub.tramiteCode,
    sub.oficinaCode
  );

  if (result.error === 'BLOCKED') {
    console.log(`  ⚠️ Blocked for ${sub.provincia}`);
    return;
  }

  if (result.available) {
    console.log(`  🎉 APPOINTMENT FOUND for ${sub.provincia}!`);
    await sendNotification(sub, result.oficinas);
    
    // Update last notified
    await Subscription.findByIdAndUpdate(sub._id, {
      lastNotified: new Date()
    });
  } else {
    console.log(`  ❌ No appointments for ${sub.provincia}`);
  }
}

async function sendNotification(sub, oficinas) {
  if (!botInstance) return;

  const oficinasText = oficinas.length > 0
    ? oficinas.slice(0, 5).map(o => `🏢 ${o}`).join('\n')
    : '🏢 Oficina disponible';

  const msg = `🔔*Cita encontrada*🔔\n\n` +
    `✅ *Provincia:* ${sub.provincia}\n` +
    `✅ *Trámite:* ${sub.tramite.substring(0, 80)}\n` +
    `✅ *Oficina:* ${sub.oficina}\n\n` +
    `${oficinasText}\n\n` +
    `[👉 Haz clic aquí para reservar](${ICP_URL})\n\n` +
    `⚡ ¡Date prisa, las citas se agotan rápido!`;

  try {
    await botInstance.telegram.sendMessage(sub.chatId, msg, {
      parse_mode: 'Markdown',
      disable_web_page_preview: true
    });
  } catch (err) {
    console.error(`Failed to send notification to ${sub.chatId}:`, err.message);
    // If user blocked bot, deactivate subscription
    if (err.message.includes('blocked') || err.message.includes('chat not found')) {
      await Subscription.findByIdAndUpdate(sub._id, { active: false });
    }
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = { startScheduler };
