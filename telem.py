import time
import serial;
import re;
import wx;

from wx.lib.wordwrap import wordwrap
cmd_filter  = re.compile('.*\<([a-z]*)\,([a-z0-9\-\.\,]*)>.*')

def parse_cmd(line):
	m = cmd_filter.match(line);
	cmd = None
	arg = None
	
	if m:
		cmd = m.group(1)
		arg = m.group(2)
		
	return cmd, arg

class MyPanel(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		print 'In panel constructor'
		self.quote     = wx.StaticText(self, label="Your quote :", pos=(10,40))
		self.batt_text = wx.StaticText(self, label="Battery: "   , pos=(10,20))
		
		self.textField = wx.TextCtrl(self, value="Enter stuff", pos=(10,60))
		
		self.Bind(wx.EVT_TEXT, self.EvtText, self.textField);
		
		self.button = wx.Button(self, label="Save", pos=(200, 325))
		
	def EvtText(self, evt):
		print 'got event'
		self.batt_text.label = "no"

class MainWindow(wx.Frame):
	def __init__(self, parent):
		wx.Frame.__init__(self, parent, title="my awesome frame", size=(350,200))
		
		# Create a status bar
		self.CreateStatusBar()
		
		# Create a menu bar
		filemenu = wx.Menu()
		menuAbout = filemenu.Append(wx.ID_ABOUT,"&About","Information about this program")
		filemenu.AppendSeparator()
		menuQuit  = filemenu.Append(wx.ID_EXIT ,"E&xit","Terminate the program");
		
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu, "&File")
		self.SetMenuBar(menuBar)
		
		# Menu bar events
		self.Bind(wx.EVT_MENU, self.OnExit , menuQuit)
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		
		# Create a panel
		self.panel = MyPanel(self)
		
		# Create a callback timer
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)
		self.timer.Start(200)
		
		self.open_port()
		
		self.Show(True)
		
	def open_port(self):
		self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5);
		print 'Opened port \"' + self.ser.portstr + '\"'
		self.x = 1;
	
	def update(self, evt):
		print 'Updating'
		line = self.ser.readline();
		raw = ('Raw:' + line).replace('\n','')
		print raw
		cmd, arg = parse_cmd(line);
		
		if cmd != None and arg != None:
			print 'Got cmd=\'' + cmd + '\', arg=\'' + arg + '\'';
		self.ser.write('<do,' + str(self.x) + '>\n')
		self.x = self.x + 1
		
	def OnExit(self, evt=None):
		self.Close(True) # Close the frame
	
	def OnAbout(self, evt):
		info = wx.MessageDialog( self, "Sup bro", "About", wx.OK )
		info.ShowModal()
		info.Destroy()

class myApp(wx.App):
	def __init__(self):
		wx.App.__init__(self)
		self.frame = MainWindow(None)
		self.MainLoop()

if __name__ == '__main__':
	app = myApp()
	
#	ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5);
#	print 'Opened port \"' + ser.portstr + '\"'
#	x = 1;
	
#	while True:
#		line = ser.readline();
#		print 'got \'' + line + '\''
#		cmd, arg = parse_cmd(line);
		
#		if cmd != None and arg != None:
#			print 'Got cmd=\'' + cmd + '\', arg=\'' + arg + '\'';
#		ser.write('<do,' + str(x) + '>\n')
#		x=x+1
#		time.sleep(0.500)

#	ser.close();
	print 'Goodbye'
