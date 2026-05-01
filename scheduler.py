import logging
logger = logging.getLogger(__name__)

class AppointmentScheduler:
 def __init__(self):
  self.active_searches={}
  self.bot=None
 def add_search(self,sid,uid,data,bot):
  self.bot=bot
  logger.info(f"Search {sid} added")
 def remove_search(self,sid):
  if sid in self.active_searches:
   del self.active_searches[sid]
