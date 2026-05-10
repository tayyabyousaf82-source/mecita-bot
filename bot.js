require('dotenv').config();
const { Telegraf, Markup } = require('telegraf');
const { connectDB, Subscription, User } = require('./db');
const { startScheduler } = require('./scheduler');
const { PROVINCIAS, TRAMITES_COMUNES, OFICINAS_POR_PROVINCIA } = require('./data');
const { fetchTramites } = require('./scraper');

const bot = new Telegraf(process.env.BOT_TOKEN);

// ─── Admin helpers ────────────────────────────────────────
function getAdminIds() {
  return (process.env.ADMIN_IDS || '').split(',').map(id => id.trim()).filter(Boolean);
}
function isAdmin(userId) {
  return getAdminIds().includes(userId.toString());
}

// ─── Session state ────────────────────────────────────────
const userState = {};
function getState(chatId) {
  if (!userState[chatId]) userState[chatId] = {};
  return userState[chatId];
}
function clearState(chatId) {
  userState[chatId] = {};
}

// ─── Core approval check ──────────────────────────────────
// Returns: 'admin' | 'approved' | 'pending' | 'rejected' | 'new'
async function getUserStatus(userId) {
  if (isAdmin(userId)) return 'admin';
  const user = await User.findOne({ userId: userId.toString() });
  if (!user) return 'new';
  if (user.rejected) return 'rejected';
  if (user.approved) return 'approved';
  return 'pending';
}

// ─── Middleware: block all commands until approved ─────────
// Applied to every command except /start
async function requireApproval(ctx, next) {
  const status = await getUserStatus(ctx.from.id);
  if (status === 'admin' || status === 'approved') return next();

  if (status === 'new') {
    return ctx.reply(
      '⛔ No tienes acceso.\n\nEnvía /start para solicitar acceso al administrador.'
    );
  }
  if (status === 'pending') {
    return ctx.reply('⏳ Tu solicitud está pendiente de aprobación. Por favor espera.');
  }
  if (status === 'rejected') {
    return ctx.reply('❌ Tu solicitud fue rechazada. Contacta al administrador.');
  }
}

// ─── /start — ONLY entry point ────────────────────────────
bot.start(async (ctx) => {
  clearState(ctx.chat.id);
  const userId = ctx.from.id.toString();
  const status = await getUserStatus(ctx.from.id);

  // Admin
  if (status === 'admin') {
    return ctx.reply(
      `👋 *Bienvenido Admin!*\n\n` +
      `Comandos usuario:\n` +
      `📌 /agregar\\_aviso\n📋 /mis\\_avisos\n❌ /borrar\\_aviso\n\n` +
      `Comandos admin:\n` +
      `👥 /usuarios — Panel usuarios\n📊 /estado — Estado del bot`,
      { parse_mode: 'Markdown' }
    );
  }

  // Already approved
  if (status === 'approved') {
    return ctx.reply(
      `👋 *¡Ya tienes acceso!*\n\n` +
      `📌 /agregar\\_aviso — Nueva alerta\n` +
      `📋 /mis\\_avisos — Ver alertas\n` +
      `❌ /borrar\\_aviso — Borrar alerta`,
      { parse_mode: 'Markdown' }
    );
  }

  // Already rejected
  if (status === 'rejected') {
    return ctx.reply('❌ Tu solicitud fue rechazada anteriormente. Contacta al administrador.');
  }

  // Already pending
  if (status === 'pending') {
    return ctx.reply(
      '⏳ Tu solicitud ya fue enviada y está pendiente de aprobación.\n\nTe notificaremos cuando el administrador te apruebe.'
    );
  }

  // NEW USER — send join request to admin, don't give any access
  await sendJoinRequest(ctx);
});

// ─── Send join request to admin ───────────────────────────
async function sendJoinRequest(ctx) {
  const userId = ctx.from.id.toString();
  const chatId = ctx.chat.id.toString();
  const username = ctx.from.username ? `@${ctx.from.username}` : (ctx.from.first_name || 'Sin nombre');

  // Save as pending in DB
  await User.findOneAndUpdate(
    { userId },
    {
      userId,
      chatId,
      username: ctx.from.username || '',
      firstName: ctx.from.first_name || '',
      lastName: ctx.from.last_name || '',
      approved: false,
      rejected: false,
      requestedAt: new Date()
    },
    { upsert: true, new: true }
  );

  // Tell user: request sent, wait
  await ctx.reply(
    `📨 *Solicitud de acceso enviada*\n\n` +
    `Tu solicitud ha sido enviada al administrador.\n` +
    `Te notificaremos cuando sea aprobada o rechazada. ⏳\n\n` +
    `_Hasta entonces no podrás usar el bot._`,
    { parse_mode: 'Markdown' }
  );

  // Notify all admins with Approve/Reject buttons
  const adminIds = getAdminIds();
  for (const adminId of adminIds) {
    try {
      await bot.telegram.sendMessage(
        adminId,
        `🔔 *Nueva solicitud de acceso*\n\n` +
        `👤 Usuario: ${username}\n` +
        `🆔 ID: \`${userId}\`\n` +
        `📛 Nombre: ${ctx.from.first_name || ''} ${ctx.from.last_name || ''}\n` +
        `📅 Fecha: ${new Date().toLocaleString('es-ES')}`,
        {
          parse_mode: 'Markdown',
          ...Markup.inlineKeyboard([
            [
              Markup.button.callback('✅ Aprobar', `approve_${userId}`),
              Markup.button.callback('❌ Rechazar', `reject_${userId}`)
            ]
          ])
        }
      );
    } catch (err) {
      console.error(`Failed to notify admin ${adminId}:`, err.message);
    }
  }
}

// ─── Admin: Approve ───────────────────────────────────────
bot.action(/^approve_(.+)$/, async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.answerCbQuery('⛔ No autorizado');

  const targetUserId = ctx.match[1];
  const user = await User.findOneAndUpdate(
    { userId: targetUserId },
    { approved: true, rejected: false, approvedAt: new Date(), approvedBy: ctx.from.id.toString() },
    { new: true }
  );

  if (!user) return ctx.editMessageText('❌ Usuario no encontrado.');

  const displayName = user.username ? `@${user.username}` : user.firstName;
  await ctx.editMessageText(
    `✅ *Usuario aprobado*\n\n👤 ${displayName}\n🆔 \`${targetUserId}\``,
    { parse_mode: 'Markdown' }
  );

  // Notify the approved user — NOW they can use bot
  try {
    await bot.telegram.sendMessage(
      user.chatId,
      `🎉 *¡Tu acceso ha sido aprobado!*\n\n` +
      `Ya puedes usar el bot:\n\n` +
      `📌 /agregar\\_aviso — Añadir alerta\n` +
      `📋 /mis\\_avisos — Ver alertas\n` +
      `❌ /borrar\\_aviso — Borrar alerta`,
      { parse_mode: 'Markdown' }
    );
  } catch (err) {
    console.error('Failed to notify approved user:', err.message);
  }
});

// ─── Admin: Reject ────────────────────────────────────────
bot.action(/^reject_(.+)$/, async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.answerCbQuery('⛔ No autorizado');

  const targetUserId = ctx.match[1];
  const user = await User.findOneAndUpdate(
    { userId: targetUserId },
    { approved: false, rejected: true },
    { new: true }
  );

  if (!user) return ctx.editMessageText('❌ Usuario no encontrado.');

  const displayName = user.username ? `@${user.username}` : user.firstName;
  await ctx.editMessageText(
    `❌ *Usuario rechazado*\n\n👤 ${displayName}\n🆔 \`${targetUserId}\``,
    { parse_mode: 'Markdown' }
  );

  try {
    await bot.telegram.sendMessage(
      user.chatId,
      `❌ Tu solicitud de acceso ha sido rechazada.\n\nContacta al administrador si crees que es un error.`
    );
  } catch (err) {
    console.error('Failed to notify rejected user:', err.message);
  }
});

// ─── Admin: /usuarios ─────────────────────────────────────
bot.command('usuarios', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.reply('⛔ No autorizado.');

  const approved = await User.countDocuments({ approved: true });
  const pending = await User.countDocuments({ approved: false, rejected: false });
  const rejected = await User.countDocuments({ rejected: true });
  const pendingList = await User.find({ approved: false, rejected: false }).limit(10);

  let msg = `👥 *Panel de Usuarios*\n\n` +
    `✅ Aprobados: ${approved}\n` +
    `⏳ Pendientes: ${pending}\n` +
    `❌ Rechazados: ${rejected}\n`;

  const buttons = [];
  if (pendingList.length > 0) {
    msg += `\n*Solicitudes pendientes:*\n`;
    pendingList.forEach(u => {
      const name = u.username ? `@${u.username}` : u.firstName;
      msg += `• ${name} (\`${u.userId}\`)\n`;
    });
    buttons.push([Markup.button.callback('📋 Gestionar pendientes', 'admin_pending')]);
  }

  await ctx.reply(msg, {
    parse_mode: 'Markdown',
    ...(buttons.length > 0 ? Markup.inlineKeyboard(buttons) : {})
  });
});

bot.action('admin_pending', async (ctx) => {
  if (!isAdmin(ctx.from.id)) return ctx.answerCbQuery('⛔ No autorizado');

  const pendingList = await User.find({ approved: false, rejected: false }).limit(20);
  if (pendingList.length === 0) return ctx.editMessageText('✅ No hay solicitudes pendientes.');

  const buttons = pendingList.map(u => {
    const name = u.username ? `@${u.username}` : u.firstName;
    return [
      Markup.button.callback(`✅ ${name}`, `approve_${u.userId}`),
      Markup.button.callback(`❌ ${name}`, `reject_${u.userId}`)
    ];
  });

  await ctx.editMessageText(
    `⏳ *Pendientes (${pendingList.length}):*\n_Selecciona acción:_`,
    { parse_mode: 'Markdown', ...Markup.inlineKeyboard(buttons) }
  );
});

// ─── /ayuda ───────────────────────────────────────────────
bot.command('ayuda', requireApproval, async (ctx) => {
  await ctx.reply(
    `❓ *Ayuda - MiCitaBot*\n\n` +
    `Monitoriza citas de extranjería y te avisa cuando hay disponibilidad.\n\n` +
    `*Cómo funciona:*\n` +
    `1. /agregar\\_aviso → elige provincia + trámite\n` +
    `2. El bot comprueba cada ${process.env.CHECK_INTERVAL_MINUTES || 5} min\n` +
    `3. Recibes notificación cuando hay cita\n\n` +
    `*Límite:* ${process.env.MAX_SUBS_PER_USER || 100} avisos por usuario`,
    { parse_mode: 'Markdown' }
  );
});

// ─── /agregar_aviso ───────────────────────────────────────
bot.command(['agregar_aviso', 'agregar'], requireApproval, async (ctx) => {
  const chatId = ctx.chat.id;
  const userId = ctx.from.id.toString();

  const count = await Subscription.countDocuments({ userId, active: true });
  const maxSubs = parseInt(process.env.MAX_SUBS_PER_USER || '100');

  if (count >= maxSubs) {
    return ctx.reply(
      `⚠️ Límite de ${maxSubs} avisos alcanzado.\nUsa /borrar\\_aviso para eliminar uno.`,
      { parse_mode: 'Markdown' }
    );
  }

  clearState(chatId);
  getState(chatId).step = 'provincia';

  const provinceButtons = PROVINCIAS.map(p =>
    Markup.button.callback(p.name, `prov_${p.code}_${p.name}`)
  );
  const rows = [];
  for (let i = 0; i < provinceButtons.length; i += 3) {
    rows.push(provinceButtons.slice(i, i + 3));
  }

  await ctx.reply(
    '📍 *Selecciona la provincia:*',
    { parse_mode: 'Markdown', ...Markup.inlineKeyboard(rows) }
  );
});

// ─── Tramite pagination helper ───────────────────────────
const TRAM_PAGE_SIZE = 10;
function buildTramiteButtons(tramites, page) {
  const start = page * TRAM_PAGE_SIZE;
  const end = Math.min(start + TRAM_PAGE_SIZE, tramites.length);
  const totalPages = Math.ceil(tramites.length / TRAM_PAGE_SIZE);

  const buttons = [];
  for (let i = start; i < end; i++) {
    buttons.push([Markup.button.callback(tramites[i].name.substring(0, 60), `tram_${i}`)]);
  }

  const nav = [];
  if (page > 0) nav.push(Markup.button.callback('⬅️ Anterior', `tram_page_${page - 1}`));
  if (page < totalPages - 1) nav.push(Markup.button.callback('Siguiente ➡️', `tram_page_${page + 1}`));
  if (nav.length > 0) buttons.push(nav);

  return buttons;
}

// ─── Province selected ────────────────────────────────────
bot.action(/^prov_(\d+)_(.+)$/, async (ctx) => {
  const chatId = ctx.chat.id;
  const code = ctx.match[1];
  const name = ctx.match[2];
  const state = getState(chatId);
  state.provinciaCode = code;
  state.provincia = name;
  state.step = 'tramite';

  await ctx.editMessageText(`✅ Provincia: *${name}*\n\n⏳ Cargando trámites...`, { parse_mode: 'Markdown' });

  let tramites = await fetchTramites(code);
  if (!tramites || tramites.length === 0) tramites = TRAMITES_COMUNES;
  state.tramitesList = tramites;
  state.tramitesPage = 0;

  await ctx.reply('📋 *Selecciona el trámite:*', {
    parse_mode: 'Markdown',
    ...Markup.inlineKeyboard(buildTramiteButtons(tramites, 0))
  });
});


// ─── Tramite page navigation ──────────────────────────────
bot.action(/^tram_page_(\d+)$/, async (ctx) => {
  const state = getState(ctx.chat.id);
  const page = parseInt(ctx.match[1]);
  state.tramitesPage = page;
  const tramites = state.tramitesList || [];

  await ctx.editMessageReplyMarkup(
    Markup.inlineKeyboard(buildTramiteButtons(tramites, page)).reply_markup
  );
  await ctx.answerCbQuery();
});

// ─── Tramite selected ─────────────────────────────────────
bot.action(/^tram_(\d+)$/, async (ctx) => {
  const chatId = ctx.chat.id;
  const idx = parseInt(ctx.match[1]);
  const state = getState(chatId);

  if (!state.tramitesList || !state.tramitesList[idx]) {
    return ctx.reply('❌ Error, empieza de nuevo con /agregar_aviso');
  }

  const tramite = state.tramitesList[idx];
  state.tramiteCode = tramite.name; // use name as unique key
  state.tramite = tramite.name;
  state.step = 'oficina';

  await ctx.editMessageText(
    `✅ Trámite:\n_${tramite.name.substring(0, 80)}_`,
    { parse_mode: 'Markdown' }
  );

  // Show oficinas for this province (paginated)
  const provOficinas = OFICINAS_POR_PROVINCIA[state.provinciaCode] || [];
  state.oficinasList = provOficinas;
  state.oficinasPage = 0;

  await ctx.reply('🏢 *Selecciona la oficina:*', {
    parse_mode: 'Markdown',
    ...Markup.inlineKeyboard(buildOficinaButtons(provOficinas, 0))
  });
});


// ─── Oficina pagination helper ────────────────────────────
const OFIC_PAGE_SIZE = 12;
function buildOficinaButtons(oficinas, page) {
  const start = page * OFIC_PAGE_SIZE;
  const end = Math.min(start + OFIC_PAGE_SIZE, oficinas.length);
  const totalPages = Math.ceil(oficinas.length / OFIC_PAGE_SIZE);

  const buttons = [[Markup.button.callback('🔍 Cualquiera (todas)', 'ofic_any')]];
  for (let i = start; i < end; i++) {
    buttons.push([Markup.button.callback(oficinas[i].substring(0, 64), `ofic_${i}`)]);
  }

  const nav = [];
  if (page > 0) nav.push(Markup.button.callback('⬅️ Anterior', `ofic_page_${page - 1}`));
  if (page < totalPages - 1) nav.push(Markup.button.callback('Siguiente ➡️', `ofic_page_${page + 1}`));
  if (nav.length > 0) buttons.push(nav);

  return buttons;
}


// ─── Oficina page navigation ──────────────────────────────
bot.action(/^ofic_page_(\d+)$/, async (ctx) => {
  const state = getState(ctx.chat.id);
  const page = parseInt(ctx.match[1]);
  state.oficinasPage = page;
  const oficinas = state.oficinasList || [];

  await ctx.editMessageReplyMarkup(
    Markup.inlineKeyboard(buildOficinaButtons(oficinas, page)).reply_markup
  );
  await ctx.answerCbQuery();
});

// ─── Oficina selected ─────────────────────────────────────
bot.action('ofic_any', async (ctx) => {
  await ctx.answerCbQuery();
  const state = getState(ctx.chat.id);
  if (!state.tramite) return ctx.reply('❌ Sesión expirada. Empieza de nuevo con /agregar_aviso');
  state.oficina = 'Cualquiera';
  state.oficinaCode = '';
  await saveSubscription(ctx, state);
});

bot.action(/^ofic_(\d+)$/, async (ctx) => {
  await ctx.answerCbQuery();
  const state = getState(ctx.chat.id);
  if (!state.tramite) return ctx.reply('❌ Sesión expirada. Empieza de nuevo con /agregar_aviso');
  const idx = parseInt(ctx.match[1]);
  const oficinas = state.oficinasList || [];
  
  if (oficinas[idx]) {
    state.oficina = oficinas[idx];
    state.oficinaCode = idx.toString();
  } else {
    state.oficina = 'Cualquiera';
    state.oficinaCode = '';
  }
  await saveSubscription(ctx, state);
});

// ─── Save subscription ────────────────────────────────────
async function saveSubscription(ctx, state) {
  const chatId = ctx.chat.id.toString();
  const userId = ctx.from.id.toString();

  try {
    const existing = await Subscription.findOne({
      userId, provinciaCode: state.provinciaCode, tramite: state.tramite, active: true
    });

    if (existing) {
      clearState(ctx.chat.id);
      return ctx.reply('⚠️ Ya tienes un aviso activo para esta provincia y trámite.');
    }

    await Subscription.create({
      chatId, userId,
      username: ctx.from.username || ctx.from.first_name,
      provincia: state.provincia, provinciaCode: state.provinciaCode,
      tramite: state.tramite, tramiteCode: state.tramiteCode,
      oficina: state.oficina, oficinaCode: state.oficinaCode || ''
    });

    clearState(ctx.chat.id);

    await ctx.reply(
      `✅ *¡Aviso creado!*\n\n` +
      `📍 *${state.provincia}*\n` +
      `📋 _${state.tramite.substring(0, 80)}_\n` +
      `🏢 ${state.oficina}\n\n` +
      `🔔 Te avisaré cuando haya cita disponible.`,
      { parse_mode: 'Markdown' }
    );
  } catch (err) {
    console.error('saveSubscription error:', err);
    await ctx.reply('❌ Error al guardar. Inténtalo de nuevo.');
  }
}

// ─── /mis_avisos ──────────────────────────────────────────
bot.command(['mis_avisos', 'mis'], requireApproval, async (ctx) => {
  const userId = ctx.from.id.toString();
  const subs = await Subscription.find({ userId, active: true });

  if (subs.length === 0) {
    return ctx.reply('📭 No tienes avisos activos.\n\nUsa /agregar\\_aviso para crear uno.', { parse_mode: 'Markdown' });
  }

  let msg = `📋 *Tus avisos activos (${subs.length}):*\n\n`;
  subs.forEach((sub, i) => {
    const last = sub.lastNotified ? `\n   _Último aviso: ${sub.lastNotified.toLocaleDateString('es-ES')}_` : '';
    msg += `*${i + 1}.* 📍 ${sub.provincia}\n   📋 ${sub.tramite.substring(0, 55)}...\n   🏢 ${sub.oficina}${last}\n\n`;
  });

  await ctx.reply(msg, { parse_mode: 'Markdown' });
});

// ─── /borrar_aviso ────────────────────────────────────────
bot.command(['borrar_aviso', 'borrar'], requireApproval, async (ctx) => {
  const userId = ctx.from.id.toString();
  const subs = await Subscription.find({ userId, active: true });

  if (subs.length === 0) return ctx.reply('📭 No tienes avisos activos para borrar.');

  const buttons = subs.map(sub => [
    Markup.button.callback(`🗑 ${sub.provincia} - ${sub.tramite.substring(0, 35)}...`, `del_${sub._id}`)
  ]);
  buttons.push([Markup.button.callback('❌ Cancelar', 'del_cancel')]);

  await ctx.reply('🗑 *¿Qué aviso quieres borrar?*', {
    parse_mode: 'Markdown', ...Markup.inlineKeyboard(buttons)
  });
});

bot.action(/^del_(.+)$/, async (ctx) => {
  const id = ctx.match[1];
  if (id === 'cancel') return ctx.editMessageText('❌ Cancelado.');

  try {
    const sub = await Subscription.findByIdAndUpdate(id, { active: false });
    if (sub) {
      await ctx.editMessageText(`✅ Aviso eliminado:\n📍 ${sub.provincia} - ${sub.tramite.substring(0, 50)}...`);
    } else {
      await ctx.editMessageText('❌ Aviso no encontrado.');
    }
  } catch (err) {
    await ctx.editMessageText('❌ Error al borrar.');
  }
});

// ─── /estado ──────────────────────────────────────────────
bot.command('estado', async (ctx) => {
  const total = await Subscription.countDocuments({ active: true });
  const users = await Subscription.distinct('userId', { active: true });
  const pending = await User.countDocuments({ approved: false, rejected: false });

  await ctx.reply(
    `📊 *Estado del Bot*\n\n` +
    `✅ Bot activo\n` +
    `👥 Usuarios aprobados: ${users.length}\n` +
    `⏳ Solicitudes pendientes: ${pending}\n` +
    `🔔 Avisos activos: ${total}\n` +
    `⏰ Cada ${process.env.CHECK_INTERVAL_MINUTES || 5} min`,
    { parse_mode: 'Markdown' }
  );
});

// ─── Block everything else for non-approved users ─────────
bot.on('message', async (ctx) => {
  const status = await getUserStatus(ctx.from.id);
  if (status === 'admin' || status === 'approved') return;

  if (status === 'new') {
    return ctx.reply('Envía /start para solicitar acceso.');
  }
  if (status === 'pending') {
    return ctx.reply('⏳ Tu solicitud está pendiente. Espera la aprobación del administrador.');
  }
  if (status === 'rejected') {
    return ctx.reply('❌ Tu solicitud fue rechazada.');
  }
});

// ─── Error handler ────────────────────────────────────────
bot.catch((err, ctx) => {
  console.error('Bot error:', err);
  ctx.reply('❌ Error interno.').catch(() => {});
});

// ─── Start ────────────────────────────────────────────────
async function main() {
  await connectDB();
  startScheduler(bot);

  await bot.telegram.setMyCommands([
    { command: 'start', description: 'Iniciar / Solicitar acceso' },
    { command: 'agregar_aviso', description: 'Añadir nuevo aviso de cita' },
    { command: 'mis_avisos', description: 'Ver tus avisos activos' },
    { command: 'borrar_aviso', description: 'Borrar un aviso' },
    { command: 'estado', description: 'Estado del bot' }
  ]);

  console.log('🤖 MiCitaBot started!');
  bot.launch();

  process.once('SIGINT', () => bot.stop('SIGINT'));
  process.once('SIGTERM', () => bot.stop('SIGTERM'));
}

main().catch(console.error);
