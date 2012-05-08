#include <stdio.h>

int BATT_VOLTAGE_PIN = 0;
int RSSI_PIN         = 1;
int LED_PIN          = 12;

static float analog_reference   = 5.03; // Arduino's regulator doesn't produce exactly 5v

void setup()
{
  //pinMode(BATT_VOLTAGE_PIN, INPUT);
  //pinMode(RSSI_PIN        , INPUT);
  
  digitalWrite(LED_PIN, 0);
  pinMode(LED_PIN         , OUTPUT);
  Serial.begin(115200);
  
  sendCommand("hello","there");

}

float readBattVoltage()
{
  static float voltage_div_factor = 4.94; // (R1+R2)/R1, with R1=9.96k and R2=39.24k
  
  float batt_voltage = analogRead(BATT_VOLTAGE_PIN);
  batt_voltage *= analog_reference/1023;
  batt_voltage *= voltage_div_factor;

  return batt_voltage;
}

int readRSSI()
{
  float rssi = analogRead(RSSI_PIN);
  rssi *= analog_reference/1023;

  //rssiDur = pulseIn(digitalPin, LOW, 200);
  
  return rssi;
}



void sendCommand(String cmd, String arg)
{
  Serial.println("<" + cmd + "," + arg + ">");
}

void error(String s)
{
  sendCommand("error", s);
}

void eval_command(String s)
{
  s.replace("<", "");
  s.replace(">", "");
  s.replace("\n", "");
  
  sendCommand("ack",s);
  
  // Parse the command
  int delim = s.indexOf(',');
  if(delim == -1){
    error("no comma");
    return;
  }
  
  String cmd = s.substring(0,delim);
  String arg = s.substring(delim+1);
  
  char scratch[20];
  
  // Turn on/off the LED
  if( cmd == "led"){
    arg.toCharArray(scratch, 20);
    int ledval = atoi(scratch);
    if( ledval == 0 || ledval == 1 ){
      digitalWrite(LED_PIN, ledval);
    } else {
      error("bad led value=" + String(ledval));
    }
  }
  
  // Unknown command
  else {
      error("unknown command - " + cmd);
  }
}

char serial_buffer[500];
int  serial_buffer_pos = 0;
void serialEvent(){
  while( Serial.available() )
  {
    if( serial_buffer_pos < 499 ){
      serial_buffer[serial_buffer_pos++] = Serial.read();
    }
  }
}

String leftover_serial;

void loop()
{
  String serial = leftover_serial;

  // See if anything new came in from serial
  noInterrupts();
  if( serial_buffer_pos > 0 )
  {
    serial_buffer[serial_buffer_pos] = '\0';
    serial += serial_buffer;
    serial_buffer_pos = 0;
  }
  interrupts();

  // Try to parse out commands
  if( serial.length() > 0 )
  {
    int l_delim, r_delim;

    // Grt rid of everything before <
    l_delim = serial.indexOf('<');
    if( l_delim > 0 ){
      serial = serial.substring(l_delim);
    }
    else if( l_delim == -1 ) {
      serial = "";
    }

    l_delim = serial.indexOf('<');
    r_delim = serial.indexOf('>');

    while( l_delim >= 0 && r_delim > 0 )
    {
      // Parse out this command string
      if( r_delim - l_delim > 1 ) {
        String this_command = serial.substring(l_delim+1, r_delim);
        eval_command(this_command);
      }

      // Move to the right of the '>' and to the next command
      if( serial.length() > r_delim ) {
        serial = serial.substring(r_delim+1);
      } 
      else {
        serial = "";
      }

      // Remove everything before the '<'
      l_delim = serial.indexOf('<');
      if( l_delim > 0 ){
        serial = serial.substring(l_delim);
      }

      l_delim = serial.indexOf('<');
      r_delim = serial.indexOf('>');
    }

    // We may have an incomplete command in memory, save it for next time
    leftover_serial = serial;
  }

  float batt = readBattVoltage();
  Serial.print("<batt,");
  Serial.print(batt);
  Serial.println(">");
  //sendCommand("batt", batt);

  float rssi = readRSSI();
  Serial.print("<rssi,");
  Serial.print(rssi);
  Serial.println(">");
  //sendCommand("rssi", rssi);

  delay(300);
}





