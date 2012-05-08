import time
import serial;
import re;
import wx;
import wx.lib.agw.speedmeter as SM
from math import pi

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
	led_on      = False;
	led_changed = True;
	
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
		
		self.batt_text = wx.StaticText(self, label="Battery: ", size=(120,25))
		self.rssi_text = wx.StaticText(self, label="RSSI   : ", size=(120,25))
		self.led_check = wx.CheckBox  (self, label="LED")
		
		# Create the battery gauge
		self.batt_meter = SM.SpeedMeter(self, agwStyle=SM.SM_DRAW_HAND|SM.SM_DRAW_SECTORS|SM.SM_DRAW_MIDDLE_TEXT|SM.SM_DRAW_SECONDARY_TICKS, size=(200,200))
		self.batt_meter.SetAngleRange(-pi/6, 7*pi/6)
		self.batt_meter.SetSpeedValue(11)
		
		batt_intervals = [11, 11.5, 12, 12.5, 13]
		self.batt_meter.SetIntervals(batt_intervals)
		
		colours = [wx.Colour(200,30,30), wx.Colour(240,240,30), wx.Colour(0,240,0), wx.Colour(0,240,0)]
		self.batt_meter.SetIntervalColours(colours)
		
		ticks = [str(interval) for interval in batt_intervals]
		self.batt_meter.SetTicks(ticks)
		self.batt_meter.SetNumberOfSecondaryTicks(1)
		self.batt_meter.SetTicksColour(wx.BLACK)
		self.batt_meter.SetTicksFont(wx.Font(9, wx.SWISS, wx.NORMAL, wx.NORMAL))
		
		self.batt_meter.SetMiddleText("Voltage")
		self.batt_meter.SetMiddleTextFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.batt_meter.SetMiddleTextColour(wx.BLACK)
		self.batt_meter.SetHandColour(wx.Colour(255, 50, 0))
		self.batt_meter.DrawExternalArc(False)
		
		self.rssi_meter = SM.SpeedMeter(self, agwStyle=SM.SM_DRAW_HAND|SM.SM_DRAW_SECTORS|SM.SM_DRAW_MIDDLE_TEXT|SM.SM_DRAW_SECONDARY_TICKS, size=(200,200))
		#self.rssi_meter.SetAngleRange(-pi/6, 7*pi/6)
		rssi_intervals = range(0,61,20)
		#self.rssi_meter.SetIntervals(rssi_intervals)
		
		
		
		self.Bind(wx.EVT_CHECKBOX, self.EvtLEDCheckBox, self.led_check)
		
		self.button = wx.Button(self, label="Save")
		self.logger = wx.TextCtrl(self, size=(200,300), style=wx.TE_MULTILINE | wx.TE_READONLY)
		
		# Set up the sizers
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		hSizer         = wx.BoxSizer(wx.HORIZONTAL)
		left_col       = wx.BoxSizer(wx.VERTICAL)
		mid_col        = wx.BoxSizer(wx.VERTICAL)
		right_col      = wx.BoxSizer(wx.VERTICAL)
		
		left_col .Add(self.batt_text ,  0, wx.ALL, 3)
		left_col .Add(self.batt_meter,  0, wx.ALL, 3)
		mid_col  .Add(self.rssi_text ,  0, wx.ALL, 3)
		mid_col  .Add(self.rssi_meter,  0, wx.ALL, 3)
		mid_col  .Add(self.led_check ,  0, wx.ALL, 3)
		right_col.Add(self.logger    ,  1, wx.EXPAND|wx.ALL, 3)
		
		hSizer.Add(left_col , 0)
		hSizer.Add(mid_col  , 0)
		hSizer.Add(right_col, 1)
		
		self.mainSizer.Add(hSizer     , 1, wx.EXPAND)
		self.mainSizer.Add(self.button, 0, wx.CENTER)
		
		self.SetSizer(self.mainSizer)
	
	def EvtLEDCheckBox(self, evt):
		self.led_changed = True
		if evt.Checked():
			self.led_on = True
		else:
			self.led_on = False
	
	def logLine(self, s):
		self.logger.AppendText(s + '\n')
	
	def setBattVoltage(self, v):
		self.batt_text.SetLabel('Battery: ' + str(v) + 'v')
		if v<11:
			v = 11.3
		self.batt_meter.SetSpeedValue(v)
		
	def setRSSI(self, rssi):
		self.rssi_text.SetLabel('RSSI: ' + str(rssi) + ' dbm')


class MainWindow(wx.Frame):
	params = dict()

	def __init__(self, parent):
		wx.Frame.__init__(self, parent, title="my awesome frame", size=(800,500))
		
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
		
		self.params['batt'] = 0;
		self.params['rssi']  = 0;
		
		# Start serial communications
		self.open_port()
		
		# Create a callback timer for periodic updates
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, self.update, self.timer)
		self.timer.Start(1000)
		
		# Make the panel visible
		#sizer = wx.BoxSizer(wx.VERTICAL)
		#sizer.Add(self.panel, 0, wx.ALL, 5)
		
		#self.SetSizer(self.panel.mainSizer)
		#self.SetAutoLayout(True)
		#self.panel.mainSizer.Fit(self)
#		self.SetSizerAndFit(self.panel.mainSizer)
		self.Show(True)
		
	def open_port(self):
		self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.10);
		print 'Opened port \"' + self.ser.portstr + '\"'
		self.x = 1;
	
	def update(self, evt):
		# Read lines from the serial connection
		lines = self.ser.readlines();
		
		# Evaluate each line's command
		for line in lines:
			cmd, arg = parse_cmd(line);
			if cmd != None and arg != None:
				self.exec_cmd(cmd, arg);
		
		# Update the GUI
		self.panel.setBattVoltage(self.params['batt'])
		self.panel.setRSSI       (self.params['rssi'])
		
		# Write stuff back to the device
		if self.panel.led_changed:
			print 'LED changed'
			self.panel.led_changed = False
			self.send_cmd("led", int(self.panel.led_on))
			
		
		#self.ser.write('<echo,' + str(self.x) + '>\n')
		self.send_cmd("echo", self.x)
		self.x = self.x + 1
	
	def send_cmd(self, cmd, arg):
		s = "<" + str(cmd) + "," + str(arg) + ">\n";
		print ('Sending: ' + s).replace('\n','')
		self.ser.write(s)
	
	def exec_cmd(self, cmd, arg):
		
		if   cmd == 'batt':
			self.params['batt'] = float(arg)
			#print 'got batt = ' + str(self.params['batt'])
			
		elif cmd == 'rssi':
			self.params['rssi'] = float(arg)
			#print 'got rssi = ' + str(self.params['rssi'])
			
		elif cmd == 'ack':
			self.panel.logLine( 'got ACK for ' + arg )
			
		elif cmd == 'error':
			self.panel.logLine('ERROR: ' + arg)
		
		else:
			self.panel.logLine('Got bad cmd=\'' + cmd + '\', arg=\'' + arg + '\'')
	
	def OnExit(self, evt=None):
		self.ser.close();
		print 'So long and thanks for all the fish'
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
