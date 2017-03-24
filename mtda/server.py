import zerorpc

class Server(object):
   def __init__(self, mtda):
       self.mtda = mtda

   def target_off(self):
       self.mtda.target_off()

   def target_on(self):
       self.mtda.target_on()

   def run(self, uri):
       s = zerorpc.Server(self)
       s.bind(uri)
       s.run()

