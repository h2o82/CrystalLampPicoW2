# **Pico 2 W Simple Web Controlled addressable LED Ring**

Upon seeing Sevro's Crystal Lamp on Printables.com I knew I had to have it and do something with it!

Link to 3D model: https://www.printables.com/model/995490-crystal-lamp


So first of all my thoughts were, I want colours and I want it to be accessible over a web interface.

I ordered some 60 LED per Meter ARGB WS2812B led's from Aliexpress (£6)
Bought some transparent PETG from Amazon.

## **Wiring:**

Its very important that you have a supply that will happily run the 36 LED's and extremely important that you power the LED's off that supply.
Also on the note of importance, Its probably not a good Idea to run the LED's on white at full brightness, this will use approx 2.16 A (36 LED's x 60 mA = 2.16A)
Unless ofcourse you have a decent supply!
And lastly regardless of Power supply DO NOT power the LED's off your Pico, it most likely wont last long!

My wiring is as follows:

+5v wiring:

            ---------- +5v LEDS
5v + -------
            ---------- +5v PICO W2 VSYS


Ground wiring:

            ----------- Gnd LEDs			
GND --------
            ----------- GND PICO W2


LED Data channel wiring:
			
PICO GPIO 0 ----------- Data LEDs


## **Code:**

Update the main.py with your wifi details, and start it up. Also, depending on your country you might want to update the NTP address.
When connected an IP will be listed in the shell for you to use a web browser to interact with the Crystal Lamp.

## **Functions:**

Off = turn the LED's off
Red = Red Crystals
Green = Green Crystals
Blue = Blue Crystals
Chase= Red and Green LED's chasing eachother!
Purple/Green = like Ying & Yang, they go up and down, meeting eachother at the top and bottom.
Sync NTP = Syncs the time to the Pico for the clock function
Clock = Shows the Time as synced above, Hour = red, Minute = Green, second = Blue - It seems a bit iffy but still works ok! (note the second hand may pause slightly, it is cramming 60 seconds into 36 led's)
Heartbeat = Beats red like a heart beat (double bump)
rainbow = this one can be quite iffy, the rainbow slowly rotates around the Lamp. Sometimes this can flicker, may be due to a previous function not clearing properly - may look at it later!
Stars = randomly light an LED with a random colours
Matrix = basically a rain simulation where the "code" runs down the sides of the lamp.
