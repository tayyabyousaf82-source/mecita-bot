import os,asyncio,logging
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,CallbackQueryHandler,MessageHandler,filters,ContextTypes,ConversationHandler
from database import Database
logging.basicConfig(level=logging.INFO)
db=Database()

SELECT_TRAMITE,SELECT_PROVINCIA,ENTER_NIE,ENTER_NAME,ENTER_PHONE,ENTER_EMAIL,CONFIRM=range(7)

PROVINCIAS=["Albacete","Alicante","Almería","Barcelona","Cádiz","Ciudad Real","Granada","Huelva","Madrid","Málaga","Murcia","Sevilla","Valencia","Zaragoza"]

TRAMITES=["TOMA DE HUELLAS (NIE)","RENOVACIONES Y PRÓRROGAS","CARTA DE INVITACIÓN","CÉDULA DE INSCRIPCIÓN","PRORROGA CON VISADO","PRORROGA SIN VISADO"]

async def start(u,c):
 await u.message.reply_text("🤖 Bienvenido Robot Cita!\n/nueva_busqueda - Nueva cita\n/mis_busquedas - Ver busquedas\n/ayuda - Ayuda")

async def nueva(u,c):
 c.user_data.clear()
 kb=[[InlineKeyboardButton(t,callback_data=f"t_{i}")] for i,t in enumerate(TRAMITES)]
 await u.message.reply_text("Selecciona tramite:",reply_markup=InlineKeyboardMarkup(kb))
 return SELECT_TRAMITE

async def sel_tramite(u,c):
 q=u.callback_query
 await q.answer()
 c.user_data['tramite']=TRAMITES[int(q.data.split('_')[1])]
 kb=[]
 row=[]
 for i,p in enumerate(PROVINCIAS):
  row.append(InlineKeyboardButton(p,callback_data=f"p_{i}"))
  if len(row)==3:kb.append(row);row=[]
 if row:kb.append(row)
 await q.edit_message_text("Selecciona provincia:",reply_markup=InlineKeyboardMarkup(kb))
 return SELECT_PROVINCIA

async def sel_prov(u,c):
 q=u.callback_query
 await q.answer()
 c.user_data['provincia']=PROVINCIAS[int(q.data.split('_')[1])]
 await q.edit_message_text("Escribe tu NIE o Pasaporte:")
 return ENTER_NIE

async def nie(u,c):
 c.user_data['nie']=u.message.text.upper()
 await u.message.reply_text("Nombre completo:")
 return ENTER_NAME

async def name(u,c):
 c.user_data['nombre']=u.message.text
 await u.message.reply_text("Telefono (+34...):")
 return ENTER_PHONE

async def phone(u,c):
 c.user_data['telefono']=u.message.text
 await u.message.reply_text("Email (o escribe 'skip'):")
 return ENTER_EMAIL

async def email(u,c):
 e=u.message.text
 c.user_data['email']='' if e.lower()=='skip' else e
 d=c.user_data
 kb=[[InlineKeyboardButton("✅ Confirmar",callback_data="yes")],[InlineKeyboardButton("❌ Cancelar",callback_data="no")]]
 await u.message.reply_text(f"Confirma:\nTramite: {d['tramite']}\nProvincia: {d['provincia']}\nNIE: {d['nie']}\nNombre: {d['nombre']}",reply_markup=InlineKeyboardMarkup(kb))
 return CONFIRM

async def confirm(u,c):
 q=u.callback_query
 await q.answer()
 if q.data=='no':
  await q.edit_message_text("Cancelado.")
  return ConversationHandler.END
 db.init()
 sid=db.save_search(u.effective_user.id,c.user_data)
 await q.edit_message_text(f"✅ Busqueda #{sid} iniciada!\nBot monitoreando ICP Clave cada 2-3 min.\n/mis_busquedas para ver estado.")
 return ConversationHandler.END

async def mis(u,c):
 s=db.get_user_searches(u.effective_user.id)
 if not s:await u.message.reply_text("No hay busquedas activas.\n/nueva_busqueda para empezar!");return
 t="Tus busquedas:\n\n"
 kb=[]
 for x in s:
  t+=f"#{x['id']} {x['provincia']} - {x['tramite'][:30]}\n"
  kb.append([InlineKeyboardButton(f"❌ Cancelar #{x['id']}",callback_data=f"cancel_{x['id']}")])
 await u.message.reply_text(t,reply_markup=InlineKeyboardMarkup(kb))

async def cancel_cb(u,c):
 q=u.callback_query
 await q.answer()
 sid=int(q.data.split('_')[1])
 db.cancel_search(sid,u.effective_user.id)
 await q.edit_message_text(f"✅ Busqueda #{sid} cancelada.")

async def ayuda(u,c):
 await u.message.reply_text("/nueva_busqueda - Nueva cita\n/mis_busquedas - Ver busquedas\n/ayuda - Ayuda")

async def cancelar(u,c):
 await u.message.reply_text("Cancelado.")
 return ConversationHandler.END

def main():
 token=os.environ.get('TELEGRAM_BOT_TOKEN')
 if not token:raise ValueError("Token missing!")
 db.init()
 app=Application.builder().token(token).build()
 conv=ConversationHandler(entry_points=[CommandHandler('nueva_busqueda',nueva)],states={SELECT_TRAMITE:[CallbackQueryHandler(sel_tramite,pattern='^t_')],SELECT_PROVINCIA:[CallbackQueryHandler(sel_prov,pattern='^p_')],ENTER_NIE:[MessageHandler(filters.TEXT&~filters.COMMAND,nie)],ENTER_NAME:[MessageHandler(filters.TEXT&~filters.COMMAND,name)],ENTER_PHONE:[MessageHandler(filters.TEXT&~filters.COMM
