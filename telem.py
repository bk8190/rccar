import time
import serial;
import re;

cmd_filter  = re.compile('.*\<([a-z]*)\,([a-z0-9\-\.]*)>.*')

def parse_cmd(line):
	m = cmd_filter.match(line);
	cmd = None
	arg = None
	
	if m:
		cmd = m.group(1)
		arg = m.group(2)
		
	return cmd, arg


if __name__ == '__main__':

	ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5);
	print 'Opened port \"' + ser.portstr + '\"'
	x = 1;
	
	while True:
		line = ser.readline();
#		print 'got \'' + line + '\''
		cmd, arg = parse_cmd(line);
		
		if cmd != None and arg != None:
			print 'Got cmd=\'' + cmd + '\', arg=\'' + arg + '\'';
		ser.write('<do,' + str(x) + '>\n')
		x=x+1
		time.sleep(0.500)

	ser.close();
	print 'Goodbye'
