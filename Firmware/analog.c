//This code handles the measuring of the two/three analog inputs we have
//#define nofilter
//stores the analog input currently being measured.
//0: current; 1: voltage
byte current_channel; 

//Calibration numbers
int offset;
// int voltage_scale defined in main.c
float watt_scale;
byte voltage_delay; //size of the voltage ring buffer
float filter_weight_inv;

int buffer[50];
byte buffer_pos;

void read_eeprom_calibration()
{
   if (read_eeprom(0)==0xCA)
   {
      filter_weight_inv=(float)1/read_eeprom(1);

      offset=(read_eeprom(2)<<8)|read_eeprom(3);
   
      current_scale=(read_eeprom(4)<<8)|read_eeprom(5);
      voltage_scale=(read_eeprom(6)<<8)|read_eeprom(7);
      
      voltage_delay=read_eeprom(8);
      
      watt_scale=10000.0/((float)current_scale*voltage_scale);
   }
}
//Handles initialization of analog to digital hardware, ADC interrupts, 
// and other stuff needed to start measuring things
void setup_adc()
{
   //Set up the calibration variables
   if (read_eeprom(0)!=0xCA)//magic flag
   {
      //uncalibrated; set up sane defaults
      write_eeprom(1,100); //filter strength
      write_eeprom(2,0b10); //DC offset high
      write_eeprom(3,0); //DC offset low
      //2770
      write_eeprom(4,10); //current scaling factor high
      write_eeprom(5,210); //current scaling factor low
      //145
      write_eeprom(6,0); //voltage scaling factor high
      write_eeprom(7,145); //voltage scaling factor low
      write_eeprom(8,0); //phase delay
      //set the magic flag
      write_eeprom(0,0xCA);
   }

   read_eeprom_calibration();
   
   current_channel=0;
   
   //Set the reference for analog conversions to the supply voltage (3.3V)
   //Open the AREF pin to use the stabilizing capacitor on that pin.
   //Right align the ADC output
   //Select the first analog input (ADC0)
   ADMUX=0b01000000;
   
   //Disable the digital circuitry on all analog input pins
   DIDR0=0b00111111;
   
   //Disable weird analog comparator stuff
   //Set the trigger mode to "free running" mode
   //This means that the completion of an ADC measurement will immediately trigger another
   ADCSRB=0;
   
   //Enable the analog to digital converter
   //Trigger the first conversion (the rest will be trigged by the end of the previous conversion)
   //Enable the auto trigger system (used for free running mode)
   //Enable the ADC interrupt (see ISR(ADC_vect))
   //Set up a /64 clock divider on the CPU clock speed of 8MHz for an ADC clock speed of 125kHz (max is 200kHz)
   ADCSRA=0b11101110;

   
   //at this point all the ADC hardware is configured and is ready to start sending interrupts

   //time to set the scene for the next conversion, but first a wait is required to give the ADC unit time to sample the current signal
   _delay_loop_2(216); //delay for 864 clock cycles (13.5 ADC cycles)
   ADMUX=(ADMUX&~(0b111))|0b1; //fancy way to select the second ADC channel
   current_channel=1;
   
   //enable interrupts
   sei();
}

//This variable is used to decide whether to switch to high precision, low current mode
byte recal_countdown;

//This is an Interrupt Service Routine (ISR)
// When an interrupt is triggered, the code is paused, and then this code is run.
//This code needs to be pretty fast - This entire method must be under 800 clock cycles because that's the delay between ADC results.
// This interrupt handles the interrupt that gets triggered when the microcontroller has
// finished measuring an analog input
ISR(ADC_vect)
{
   byte this_channel=current_channel;
   
   //Change to the next channel
   current_channel=!current_channel;
   ADMUX=(ADMUX&~(0b111))|current_channel;
   
   //Get the conversion result
   //You must read ADCL first and then ADCH, 
   //because reading ADCL locks these registers until ADCH is read.
   //This prevents the result being updated between reading the registers.
   byte l=ADCL;
   byte h=ADCH;
   int result=(h<<8)|l;
   
   //The reading is stored in result
   //The corresponding channel is stored in this_channel
   
   if (this_channel==1)
   {
      last_current_mode=current_mode;
      //correct for current mode
      if (current_mode==0)
         last_current=result*2;
      else
         last_current=result;
      //test for over/undercurrent
      if (result>max_sense)
         max_sense=result;

      //Advance or reset the low current mode fuse
      if (max_sense<700 && current_mode==0)
         recal_countdown++;
      else
         recal_countdown=0;

      //Switch to low current sense if the "fuse" has triggered
      if (recal_countdown==255)
      {
         multiplex(1);
         current_mode=1;
         max_sense=0;
         recal_countdown=0;
      }
      //Switch to high current sense if needed
      if (max_sense==1023)
      {
         multiplex(0);
         current_mode=0;
         max_sense=0;
         recal_countdown=0;
      }
   }
   else
   {
      voltage_range_reset++;
      //Time to reset the voltage range
      if (voltage_range_reset==255)
      {
         //reset the no voltage indicator because we have a full buffer of measurements to base this on
         no_voltage=((float)100*(max_voltage-min_voltage)/voltage_scale) < 50;
         max_voltage=0;
         min_voltage=1023;
         voltage_range_reset=0;
      }

      //Keep track of the range of voltage readings for no-volt detection
      if (result > max_voltage)
         max_voltage=result;
      if (result < min_voltage)
         min_voltage=result;

      //Keep a ring buffer of voltages if voltage delay is on
      if (voltage_delay!=0)
      {
         buffer[(buffer_pos++)%voltage_delay]=result;
         last_voltage=buffer[buffer_pos%voltage_delay];
      } else
         last_voltage=result;
      
      int shifted_current;
      if (last_current_mode==0)
         shifted_current=last_current-(offset*2);
      else
         shifted_current=last_current-offset;
      
      int shifted_voltage=last_voltage-offset;
      
      filter_watts=(int)(watt_scale*shifted_voltage*shifted_current);
   }
}
